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

def bundle_round(discount):
    return round(discount / 100000) * 100000

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

    # ==========================================
    # TOTAL
    # ==========================================

    trx["TOTAL"] = (
        safe_numeric(trx["Net Sales"]) +
        safe_numeric(trx["Tax"])
    )

    # ==========================================
    # PAYMENT
    # ==========================================

    payment = trx["Payment Method"].astype(str).str.lower()

    cash = trx.loc[
        payment == "cash",
        "TOTAL"
    ].sum()

    card = trx.loc[
        payment != "cash",
        "TOTAL"
    ].sum()

    # ==========================================
    # VOUCHER ERL
    # ==========================================

    voucher_erl = (
        trx[
            trx["Discount Applied"]
            .astype(str)
            .str.contains(
                "Voucher ERL 100K",
                case=False,
                na=False
            )
        ]["Receipt Number"]
        .nunique()
        * 100000
    )

    # ==========================================
    # VOUCHER KOL
    # ==========================================

    voucher_kol = (
        trx[
            trx["Discount Applied"]
            .astype(str)
            .str.contains(
                "Voucher KOL 500K",
                case=False,
                na=False
            )
        ]["Receipt Number"]
        .nunique()
        * 500000
    )

    # ==========================================
    # DISKON CUSTOM
    # ==========================================

    custom_df = trx[
        trx["Discount Applied"]
        .astype(str)
        .str.contains(
            "DISKON CUSTOM",
            case=False,
            na=False
        )
    ].copy()

    voucher_custom = 0

    if len(custom_df) > 0:

        grouped = (
            custom_df
            .groupby("Receipt Number")["Discounts"]
            .sum()
        )

        voucher_custom = grouped.apply(
            bundle_round
        ).sum()

    voucher_total = (
        voucher_erl +
        voucher_kol +
        voucher_custom
    )

    # ==========================================
    # MERGE MASTER
    # ==========================================

    trx = trx.merge(
        master[
            [
                "SKU",
                "Brand Name",
                "Category",
                "Basic - Price"
            ]
        ],
        on="SKU",
        how="left",
        suffixes=("", "_MASTER")
    )

    # ==========================================
    # CATEGORY
    # ==========================================

    merchandise = trx[
        trx["Category_MASTER"]
        .astype(str)
        .str.contains(
            "1702 MERCHANDISE EDISI ERLANGGA",
            case=False,
            na=False
        )
    ]

    suma = trx[
        trx["Brand Name"]
        .astype(str)
        .str.contains(
            "SUMA",
            case=False,
            na=False
        )
    ]

    erlass = trx[
        trx["Brand Name"]
        .astype(str)
        .str.contains(
            "ERLASS",
            case=False,
            na=False
        )
    ]

    excluded_idx = (
        merchandise.index
        .union(suma.index)
        .union(erlass.index)
    )

    erlangga = trx.drop(
        excluded_idx,
        errors="ignore"
    )

    # ==========================================
    # SUMMARY FUNCTION
    # ==========================================

    def get_summary(df):

        qty = safe_numeric(
            df["Quantity"]
        ).sum()

        total = safe_numeric(
            df["TOTAL"]
        ).sum()

        return qty, total

    qty_erlangga, total_erlangga = get_summary(erlangga)
    qty_suma, total_suma = get_summary(suma)
    qty_merch, total_merch = get_summary(merchandise)
    qty_erlass, total_erlass = get_summary(erlass)

    # ==========================================
    # SPECIAL BUNDLE REPORT
    # ==========================================

    bundle_report = []

    for bundle_name in SPECIAL_BUNDLES:

        b = trx[
            trx["Items"]
            .astype(str)
            .str.upper()
            .eq(bundle_name.upper())
        ]

        if len(b) > 0:

            qty = safe_numeric(
                b["Quantity"]
            ).sum()

            total = safe_numeric(
                b["TOTAL"]
            ).sum()

            bundle_report.append({
                "name": bundle_name,
                "qty": qty,
                "total": total
            })

    # ==========================================
    # TRANSAKSI
    # ==========================================

    transaksi = trx[
        "Receipt Number"
    ].nunique()

    customer = math.ceil(
        transaksi * 1.2
    )

    # ==========================================
    # DATE
    # ==========================================

    try:

        tgl = pd.to_datetime(
            trx["Date"].iloc[0]
        )

        tanggal_text = tgl.strftime(
            "%d %B %Y"
        )

    except:

        tanggal_text = "-"

    # ==========================================
    # TOTAL PENJUALAN
    # ==========================================

    total_penjualan = (
        total_erlangga +
        total_suma +
        total_merch +
        total_erlass +
        voucher_total
    )

    # ==========================================
    # OUTPUT WA
    # ==========================================

    laporan = f"""
Semangat pagi
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

    if len(bundle_report) > 0:

        laporan += "\nPenjualan Bundling:\n"

        for item in bundle_report:

            laporan += f"""

{item['name']}
Qty : {int(item['qty'])} Paket
Total : {rupiah(item['total'])}
"""

    laporan += f"""

Total penjualan Erlangga, Suma, Merchandise, Erlass, Voucher :
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
