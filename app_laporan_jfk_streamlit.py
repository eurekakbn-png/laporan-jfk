
import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title='Laporan JFK', layout='wide')
st.title('📚 Generator Laporan JFK')

voucher = st.number_input('Voucher Manual', min_value=0, step=1000, value=0)

trx_file = st.file_uploader('Upload CSV Transaksi', type=['csv'])
master_file = st.file_uploader('Upload Master SKU Vendor', type=['csv'])

def rupiah(x):
    return f"Rp. {int(math.ceil(x)):,.0f}".replace(',', '.')

if trx_file and master_file:
    trx = pd.read_csv(trx_file)
    master = pd.read_csv(master_file)

    sku_col = next((c for c in master.columns if 'sku' in c.lower()), None)
    trx_sku = next((c for c in trx.columns if 'sku' in c.lower()), None)

    df = trx.copy()
    if sku_col and trx_sku:
        df = trx.merge(master, left_on=trx_sku, right_on=sku_col, how='left')

    df['TOTAL'] = pd.to_numeric(df['Net Sales'], errors='coerce').fillna(0) + pd.to_numeric(df['Tax'], errors='coerce').fillna(0)

    payment = df['Payment Method'].astype(str).str.lower()
    cash = df.loc[payment == 'cash', 'TOTAL'].sum()
    card = df.loc[payment != 'cash', 'TOTAL'].sum()

    brand_col = next((c for c in df.columns if 'brand' in c.lower()), None)
    category_col = next((c for c in df.columns if 'category' in c.lower()), None)

    brand = df[brand_col].astype(str) if brand_col else pd.Series('', index=df.index)
    category = df[category_col].astype(str) if category_col else pd.Series('', index=df.index)

    merchandise = df[category.str.contains('1702 MERCHANDISE EDISI ERLANGGA', case=False, na=False)]
    suma = df[brand.str.contains('suma', case=False, na=False)]
    erlass = df[brand.str.contains('erlass', case=False, na=False)]
    erlangga = df.drop(merchandise.index.union(suma.index).union(erlass.index), errors='ignore')

    def calc(x):
        qty = math.ceil(pd.to_numeric(x['Quantity'], errors='coerce').fillna(0).sum())
        total = math.ceil(x['TOTAL'].sum())
        return qty, total

    qty_erlangga, total_erlangga = calc(erlangga)
    qty_suma, total_suma = calc(suma)
    qty_merch, total_merch = calc(merchandise)
    qty_erlass, total_erlass = calc(erlass)

    transaksi = df['Receipt Number'].nunique()
    customer = math.ceil(transaksi * 1.2)

    total_penjualan = total_erlangga + total_suma + total_merch + total_erlass + voucher

    laporan = f'''Semangat pagi
Bapak Willy ysh,
Bapak Adriansyah ysh,
Bapak Sigit ysh,

Berikut kami sampaikan closing Pameran Jakarta Fair Kemayoran dengan total penjualan sebagai berikut:

Cash : {rupiah(cash)}
Card : {rupiah(card)}
Voucher : {rupiah(voucher)}

Qty Buku Erlangga : {qty_erlangga} exp
Total : {rupiah(total_erlangga)}

Qty Suma : {qty_suma} pcs
Total : {rupiah(total_suma)}

Qty Merchandise Erlangga : {qty_merch} pcs
Total : {rupiah(total_merch)}

Qty Erlass : {qty_erlass} pcs
Total : {rupiah(total_erlass)}

Qty Voucher : {rupiah(voucher)}

Total penjualan Erlangga, Suma, Merchandise, Erlass, Voucher :
{rupiah(total_penjualan)}

Transaksi : {transaksi}
Customer : {customer}

Demikian
Terima kasih'''

    st.text_area('Hasil Siap Copy ke WA', laporan, height=500)
