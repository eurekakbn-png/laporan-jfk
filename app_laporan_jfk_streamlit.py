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

    # --- TAMBAHAN UNTUK BRAND 2MEDISON ---
    twomedison = trx[
        trx["Brand Name"]
        .astype(str)
        .str.contains("2MEDISON", case=False, na=False)
    ]

    # Masukkan twomedison.index ke dalam pengecualian agar tidak ikut terhitung di Buku Erlangga
    excluded_idx = merchandise.index.union(suma.index).union(erlass.index).union(twomedison.index)
    erlangga = trx.drop(excluded_idx, errors="ignore")

    # ==========================================
    # SUMMARY FUNCTION
    # ==========================================

    def get_summary(df):
        qty = safe_numeric(df["Quantity"]).sum()
        total = safe_numeric(df["TOTAL"]).sum()  # Menggunakan TOTAL yang sudah include proporsi voucher
        return qty, total

    qty_erlangga, total_erlangga = get_summary(erlangga)
    qty_suma, total_suma = get_summary(suma)
    qty_merch, total_merch = get_summary(merchandise)
    qty_erlass, total_erlass = get_summary(erlass)
    
    # --- TAMBAHAN QUANTITY & TOTAL FOR 2MEDISON ---
    qty_twomedison, total_twomedison = get_summary(twomedison)

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

    # Tambahkan total_twomedison ke akumulasi total penjualan
    total_penjualan = total_erlangga + total_suma + total_merch + total_erlass + total_twomedison

    # ==========================================
    # OUTPUT WA
    # ==========================================

    # Perbarui template pesan dengan menambahkan baris 2medison
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

Qty 2medison : {int(qty_twomedison)} pcs
Total : {rupiah(total_twomedison)}
"""

    if len(bundle_report) > 0:
        laporan += "\nPenjualan Bundling:\n"
        for item in bundle_report:
            laporan += f"""
{item['name']}
Qty : {int(item['qty'])} Paket
Total : {rupiah(item['total'])}
"""

    # Update label deskripsi total penjualan agar mencakup seluruh brand
    laporan += f"""
Total penjualan Erlangga, Suma, Merchandise, Erlass, 2medison :
{rupiah(total_penjualan)}

Transaksi : {transaksi}
Customer : {customer}

Demikian
Terima kasih
"""
