# SPESIFIKASI APLIKASI LAPORAN JFK V2.0

## INPUT USER

User hanya perlu:

1. Upload CSV Transaksi
2. Klik Generate

Tidak perlu upload:

* Master SKU
* Bundling

karena keduanya tersimpan permanen di repository GitHub.

---

## FILE REPOSITORY

```text
laporan-jfk/
│
├── app_laporan_jfk_streamlit.py
├── requirements.txt
├── master_sku.csv
├── bundling.xlsx
```

---

## LOGIKA PAYMENT

### Cash

Payment Method = Cash

```python
cash = total(Net Sales + Tax)
```

### Card

Selain Cash

```python
card = total(Net Sales + Tax)
```

---

## LOGIKA VOUCHER

Voucher dihitung otomatis.

### Voucher ERL 100K

Discount Applied:

```text
Voucher ERL 100K
```

Nilai voucher:

```text
100.000
```

per Receipt Number unik.

---

### Voucher KOL 500K JAKFAIR 2026

Discount Applied:

```text
Voucher KOL 500K JAKFAIR 2026
```

Nilai voucher:

```text
500.000
```

per Receipt Number unik.

---

### DISKON CUSTOM Rp.

Discount Applied:

```text
DISKON CUSTOM Rp.
```

Kelompokkan berdasarkan Receipt Number.

Jumlahkan kolom Discounts.

Lalu bulatkan ke kelipatan 100.000 terdekat.

Contoh:

```text
99.999  -> 100.000
100.001 -> 100.000
199.999 -> 200.000
200.001 -> 200.000
299.999 -> 300.000
```

Total voucher:

```text
Voucher ERL
+
Voucher KOL
+
Voucher Custom
```

---

## LOGIKA KATEGORI

### Merchandise Erlangga

Category:

```text
1702 MERCHANDISE EDISI ERLANGGA
```

---

### Suma

Brand mengandung:

```text
SUMA
```

---

### Erlass

Brand mengandung:

```text
ERLASS
```

---

### Erlangga

Semua item selain:

* Suma
* Erlass
* Merchandise Erlangga

---

## LOGIKA BUNDLING

Category:

```text
Bundle_Package
```

Lookup ke:

```text
bundling.xlsx
```

Kolom:

```text
Items
```

dipisah dengan:

```text
,
```

Setiap item dicocokkan ke:

```text
master_sku.csv
```

kemudian dimasukkan ke kategori:

* Erlangga
* Suma
* Merchandise
* Erlass

---

## LAPORAN BUNDLING KHUSUS

Tampilkan hanya jika terjual.

### BUNDLING TAS 150K

Hitung:

```text
Qty Paket
Total Rupiah
```

---

### BUNDLING TAS ANAK 250K

Hitung:

```text
Qty Paket
Total Rupiah
```

---

### BUNDLING TAS REMAJA 250K

Hitung:

```text
Qty Paket
Total Rupiah
```

---

Jika qty = 0

JANGAN DITAMPILKAN.

---

## TOTAL PENJUALAN

```text
Erlangga
+
Suma
+
Merchandise
+
Erlass
+
Voucher
```

---

## TRANSAKSI

Unique:

```text
Receipt Number
```

---

## CUSTOMER

```text
Customer = CEILING(Transaksi x 1.2)
```

---

# FORMAT OUTPUT WHATSAPP

Semangat pagi

Bapak Willy ysh,
Bapak Adriansyah ysh,
Bapak Sigit ysh,

Berikut kami sampaikan closing Pameran Jakarta Fair Kemayoran hari {tanggal} dengan total penjualan sebagai berikut:

Cash : Rp. xxx
Card : Rp. xxx
Voucher : Rp. xxx

Qty Buku Erlangga : xxx exp
Total : Rp. xxx

Qty Suma : xxx pcs
Total : Rp. xxx

Qty Merchandise Erlangga : xxx pcs
Total : Rp. xxx

Qty Erlass : xxx pcs
Total : Rp. xxx

{TAMPILKAN HANYA JIKA ADA PENJUALAN BUNDLING}

Penjualan Bundling:

BUNDLING TAS 150K
Qty : xxx Paket
Total : Rp. xxx

BUNDLING TAS ANAK 250K
Qty : xxx Paket
Total : Rp. xxx

BUNDLING TAS REMAJA 250K
Qty : xxx Paket
Total : Rp. xxx

Total penjualan Erlangga, Suma, Merchandise, Erlass, Voucher :
Rp. xxx

Transaksi : xxx
Customer : xxx

Demikian
Terima kasih
