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
    
    # 2. Identifikasi baris yang mengandung Voucher/Diskon Custom spesifik
    discount_col = trx["Discount Applied"].astype(str)
    
    is_voucher_erl = discount_col.str.contains("Voucher ERL 100K", case=False, na=False)
    is_voucher_kol = discount_col.str.contains("Voucher KOL 500K JAKFAIR 2026", case=False, na=False)
    is_diskon_custom = discount_col.str.contains("DISKON CUSTOM", case=False, na=False)
    
    # Filter hanya diskon target pameran ini
    is_target_discount = is_voucher_erl | is_voucher_kol | is_diskon_custom
    
    # Ambil nilai diskon positifnya (jika di laporan bernilai minus, kita mutlakkan dengan abs())
    trx["Voucher_Allocated"] = 0.0
    trx.loc[is_target_discount, "Voucher_Allocated"] = safe_numeric(trx.loc[is_target_discount, "Discounts"]).abs()

    # 3. TOTAL baru = Net + Tax + Nilai Voucher (Mengembalikan omset asli ke item/brand)
    trx["TOTAL"] = trx["TOTAL_NET"] + trx["Voucher_Allocated"]

    # ==========================================
    # PAYMENT (Tetap menggunakan TOTAL_NET karena uang kas/kartu yang masuk adalah nilai net)
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

    excluded_idx = merchandise.index.union(suma.index).union(erlass.index)
    erlangga = trx.drop(excluded_idx, errors="ignore")

    # ==========================================
    # SUMMARY FUNCTION
    # ==========================================

    def get_summary(df):
        qty = safe_numeric(df["Quantity"]).sum()
        total = safe_numeric(df["TOTAL"]).sum()  # Sudah termasuk alokasi voucher di atas
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

    # Total penjualan gabungan adalah penjumlahan langsung dari brand yang sudah include voucher
    total_penjualan = total_erlangga + total_suma + total_merch + total_erlass

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

    if len(bundle_report) > 0:
        laporan += "\nPenjualan Bundling:\n"
        for item in bundle_report:
            laporan += f"""
{item['name']}
Qty : {int(item['qty'])} Paket
Total : {rupiah(item['total'])}
"""

    laporan += f"""
Total penjualan Erlangga, Suma, Merchandise, Erlass :
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
