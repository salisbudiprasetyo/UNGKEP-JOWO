# UNGKEP JOWO - Rekap Pembelian (tahap 1-2)

## Jalankan lokal (uji coba, data di folder data/)
1. pip install -r requirements.txt
2. Salin .streamlit/secrets.toml.example menjadi .streamlit/secrets.toml, ubah backend = "local", isi admin_password.
3. (Opsional) python seed_demo.py untuk data contoh.
4. streamlit run app.py

## Pakai Google Sheets
1. Buat Spreadsheet kosong di Google Sheets, salin ID dari URL (/d/<ID>/edit).
2. Google Cloud Console: buat project, aktifkan Google Sheets API dan Google Drive API, buat Service Account, buat key JSON.
3. Bagikan Spreadsheet ke client_email service account (peran Editor).
4. Isi secrets.toml: backend = "sheets", spreadsheet_id, dan blok [gcp_service_account] dari file JSON.
5. Saat pertama jalan, aplikasi membuat sendiri sheet: Pelanggan, Permintaan, Menu, MenuHarian, Kasbon, RecordHarian.

## Sheet
- Kasbon: satu baris per item (tanggal, periode, pelanggan, item, qty, harga, subtotal, status_bayar).
- RecordHarian: backup Pesanan Hari Ini per periode (diisi di tahap 3).
