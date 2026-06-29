import streamlit as st
import pandas as pd
import math
from datetime import datetime

st.set_page_config(
    page_title="Laporan JFK",
    layout="wide"
)

# =====================================================
# CONFIG
# =====================================================

MASTER_FILE = "master_sku.csv"
BUNDLING_FILE = "bundling.xlsx"

SPECIAL_BUNDLES = [
    "BUNDLING TAS 150K",
    "BUNDLING TAS ANAK 250K",
    "BUNDLING TAS REMAJA 250K"
]

# =====================================================
# HELPERS
# =====================================================

def rupiah(x):
    return f"Rp. {int(round(x)):,.0f}".replace(",", ".")

def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)

# =====================================================
# LOAD MASTER
# =====================================================

@st.cache_data
def load_master():
    return pd.read_csv(MASTER_FILE)

@st.cache_data
def load_bundle():
    return pd.read_excel(BUNDLING_FILE)

# =====================================================
# APP
# =====================================================

st.title("📚 Generator Laporan JFK")

trx_file = st.file_uploader(
    "Upload CSV Transaksi",
    type=["csv"]
)

if trx_file:

    master = load_master()
    bundle_master = load_bundle()

    trx = pd.read_csv(trx_file)

    # 1. Hitung TOTAL dasar (Net Sales + Tax) per baris item
    trx["TOTAL_NET"] = safe_numeric(trx["Net Sales"]) + safe_numeric(trx["Tax"])
    
    # ==========================================
    # VOUCHER MASUK KE OMZET BRAND
    # ==========================================

    trx["Voucher_Allocated"] = 0.0

    for receipt, grp in trx.groupby("Receipt Number"):

        voucher_receipt = 0

        discount_text = " ".join(
            grp["Discount Applied"]
            .fillna("")
            .astype(str)
            .tolist()
        )

        # Voucher ERL selalu 100.000
        if "Voucher ERL 100K".lower() in discount_text.lower():
            voucher_receipt += 100000

        # Voucher KOL selalu 500.000
        if "Voucher KOL 500K JAKFAIR 2026".lower() in discount_text.lower():
            voucher_receipt += 500000

        # DISKON CUSTOM
        custom_rows = grp[
            grp["Discount Applied"]
            .astype(str)
            .str.contains(
                "DISKON CUSTOM",
                case=False,
                na=False
            )
        ]

        if len(custom_rows) > 0:

            custom_discount = abs(
                safe_numeric(
                    custom_rows["Discounts"]
                ).sum()
            )

            custom_voucher = (
                round(custom_discount / 100000)
                * 100000
            )

            voucher_receipt += custom_voucher

        if voucher_receipt > 0:

            total_sales = (
                safe_numeric(grp["Net Sales"]) +
                safe_numeric(grp["Tax"])
            ).sum()

            if total_sales > 0:

                proporsi = (
                    (
                        safe_numeric(grp["Net Sales"]) +
                        safe_numeric(grp["Tax"])
                    )
                    / total_sales
                )

                trx.loc[
                    grp.index,
                    "Voucher_Allocated"
                ] = proporsi * voucher_receipt

    trx["TOTAL"] = (
        trx["TOTAL_NET"] +
        trx["Voucher_Allocated"]
    )

    # ==========================================
    # PAYMENT (Tetap menggunakan TOTAL_NET karena uang asli yang masuk)
    # ==========================================

    payment = trx["Payment Method"].astype(str).str.lower()

    cash = trx.loc[payment == "cash", "TOTAL_NET"].sum()
    card = trx.loc[payment != "cash", "TOTAL_NET"].sum()

    # ==========================================
    # VOUCHER SUMMARY (Untuk tampilan Summary WA)
    # ==========================================
    
    voucher_total = trx["Voucher_Allocated"].sum()

    # ==========================================
    # MERGE MASTER
    # ==========================================

    trx = trx.merge(
        master[["SKU", "Brand Name", "Category", "Basic - Price"]],
        on="SKU",
        how="left",
        suffixes=("", "_MASTER")
    )

    # ==========================================
    # CATEGORY SPLITTING
    # ==========================================

    merchandise = trx[
        trx["Category_MASTER"]
        .astype(str)
        .str.contains("1702 MERCHANDISE EDISI ERLANGGA", case=False, na=False)
    ]

    suma = trx[
        trx["Brand Name"]
        .astype(str)
        .str.contains("SUMA", case=False, na=False)
    ]

    erlass = trx[
        trx["Brand Name"]
        .astype(str)
        .str.contains("ERLASS", case=False, na=False)
    ]

    madison = trx[
        trx["Brand Name"]
        .astype(str)
        .str.contains("2MADISON", case=False, na=False)
    ]

    excluded_idx = (
        merchandise.index
        .union(suma.index)
        .union(erlass.index)
        .union(madison.index)
    )

    erlangga = trx.drop(
        excluded_idx,
        errors="ignore"
    )

    # ==========================================
    # SUMMARY FUNCTION
    # ==========================================

    def get_summary(df):
        qty = safe_numeric(df["Quantity"]).sum()
        total = safe_numeric(df["TOTAL"]).sum()
        return qty, total

    qty_erlangga, total_erlangga = get_summary(erlangga)
    qty_suma, total_suma = get_summary(suma)
    qty_merch, total_merch = get_summary(merchandise)
    qty_erlass, total_erlass = get_summary(erlass)
    qty_madison, total_madison = get_summary(madison)

    # ==========================================
    # SPECIAL BUNDLE REPORT
    # ==========================================

    bundle_report = []

    for bundle_name in SPECIAL_BUNDLES:
        b = trx[trx["Items"].astype(str).str.upper() == bundle_name.upper()]
        if len(b) > 0:
            qty = safe_numeric(b["Quantity"]).sum()
            total = safe_numeric(b["TOTAL"]).sum()
            bundle_report.append({
                "name": bundle_name,
                "qty": qty,
                "total": total
            })

    # ==========================================
    # TRANSAKSI
    # ==========================================

    transaksi = trx["Receipt Number"].nunique()
    customer = math.ceil(transaksi * 1.2)

    # ==========================================
    # DATE
    # ==========================================

    try:
        tgl = pd.to_datetime(trx["Date"].iloc[0])
        tanggal_text = tgl.strftime("%d %B %Y")
    except:
        tanggal_text = "-"

    # ==========================================
    # TOTAL PENJUALAN
    # ==========================================

    # Penjumlahan langsung dari total masing-masing brand yang sudah menyerap nominal voucher
    total_penjualan = (
    total_erlangga +
    total_suma +
    total_merch +
    total_erlass +
    total_madison
)

    # ==========================================
    # OUTPUT WA
    # ==========================================

    laporan = f"""Semangat pagi
Bapak Willy ysh,
Bapak Adriansyah ysh,
Bapak Sigit ysh,

Berikut kami sampaikan closing Pameran Jakarta Fair Kemayoran hari {tanggal_text} dengan total penjualan sebagai berikut:

Cash : {rupiah(cash)}
Card : {rupiah(card)}
Voucher : {rupiah(voucher_total)}

Qty Buku Erlangga : {int(qty_erlangga)} exp
Total : {rupiah(total_erlangga)}

Qty Suma : {int(qty_suma)} pcs
Total : {rupiah(total_suma)}

Qty Merchandise Erlangga : {int(qty_merch)} pcs
Total : {rupiah(total_merch)}

Qty Erlass : {int(qty_erlass)} pcs
Total : {rupiah(total_erlass)}
"""
Qty 2MADISON : {int(qty_madison)} pcs
Total : {rupiah(total_madison)}
    if len(bundle_report) > 0:
        laporan += "\nPenjualan Bundling:\n"
        for item in bundle_report:
            laporan += f"""
{item['name']}
Qty : {int(item['qty'])} Paket
Total : {rupiah(item['total'])}
"""

    laporan += f"""
Total penjualan Erlangga, Suma, Merchandise, Erlass, 2MADISON :
{rupiah(total_penjualan)}

Transaksi : {transaksi}
Customer : {customer}

Demikian
Terima kasih
"""

    st.text_area(
        "Hasil Siap Copy WhatsApp",
        laporan,
        height=600
    )
