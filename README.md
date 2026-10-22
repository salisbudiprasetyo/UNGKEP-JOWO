# UNGKEP JOWO - Rekap Pembelian (tahap 1-3 + data awal)

## Jalankan lokal (uji coba, data di folder data/)
1. pip install -r requirements.txt
2. Salin .streamlit/secrets.toml.example menjadi .streamlit/secrets.toml, ubah backend = "local", isi admin_password.
3. (Opsional) python seed_demo.py untuk data contoh (menu + pesanan untuk besok).
4. streamlit run app.py

## Pakai Google Sheets
1. Buat Spreadsheet kosong di Google Sheets, salin ID dari URL (/d/<ID>/edit).
2. Google Cloud Console: buat project, aktifkan Google Sheets API dan Google Drive API, buat Service Account, buat key JSON.
3. Bagikan Spreadsheet ke client_email service account (peran Editor).
4. Isi secrets.toml: backend = "sheets", spreadsheet_id, dan blok [gcp_service_account] dari file JSON.
5. Saat pertama jalan, aplikasi membuat sendiri semua sheet.

## Sheet
- Kasbon: satu baris per item (tanggal, periode, pelanggan, item, qty, harga, subtotal, status_pesanan, status_bayar).
- RecordHarian: backup Pesanan Hari Ini per tanggal dan periode, diperbarui otomatis setiap ada perubahan.
- Revisi: permintaan ubah/batal dari pelanggan yang menunggu konfirmasi admin.
- Pelanggan, Permintaan, Menu, MenuHarian.

## Aturan penting
- Periode kasbon: tanggal 11 s/d 10 bulan berikutnya.
- Pelanggan bisa pesan/ubah/batal sampai 10:45 WIB pada hari H; admin bisa kapan saja.
- Perubahan dari pelanggan baru berlaku setelah admin konfirmasi; sampai itu pesanan lama yang dihitung.

## Data awal (sekali saja)
Admin > tab **Data awal** > centang > **Muat data awal**. Mengisi 36 pelanggan, riwayat pesanan 20 dan 21 Okt (Rp561.000), menu master, daftar minuman (centang Ready), dan menu 20-22 Okt (22 Okt: Sate Komo + sayur bening, harga Rp7.000 - cek lagi). Aman diulang; pesanan 20-21 Okt ditimpa sesuai file, menu 22 Okt tidak menimpa menu yang sudah diunggah admin.


## Cara kerja tabel & pembayaran (versi terbaru)
- **Tabel kasbon**: ketuk **PESAN** di kolom tanggal untuk membuka jendela pesan (Nasi, Lauk, Minuman, Lain-lain: pilihan, jumlah, harga, lalu total). Ketuk angka untuk melihat rincian; ketuk **TOTAL** untuk tagihan. Sel kuning ⏳ = perubahan menunggu konfirmasi admin.
- **Batas ubah pesanan**: 10:45 WIB hari H (ubah di `logic.py`, baris `EDIT_BATAS_JAM`). Setelah itu rincian hanya bisa dilihat.
- **Bayar sekarang**: menampilkan rekening (bawaan BNI 0258578828 a.n. NUR HABIBAH; ganti lewat secrets `rekening_bank`, `rekening_nomor`, `rekening_nama`), kolom jumlah transfer, dan unggah foto bukti. Jumlah sama dengan tagihan = lunas otomatis; berbeda = tersimpan dan dicek admin di tab **Pembayaran**.
- **Logo bank**: taruh file `assets/bni.png` (logo resmi) agar tampil di jendela pembayaran. Tanpa file itu tampil lencana teks.

## Aturan tombol PESAN, libur, dan pembayaran per hari
- Tombol PESAN hanya muncul di satu tanggal: menu terdekat yang sudah diunggah admin (hari ini; besok baru aktif setelah menu besok diunggah). Tanggal yang sudah lewat tidak punya tombol PESAN, juga untuk admin.
- Admin: tab **Libur** untuk menjadikan tanggal libur pemesanan (pilih tanggal, konfirmasi). Kolom tanggal itu bertanda “libur”.
- Ketuk angka di sel mana pun untuk melihat rincian pesanan dan pembayaran hari itu: admin ada **Konfirmasi lunas**, pelanggan ada **Bayar sekarang**. Ketuk TOTAL untuk tagihan satu periode.

## Pesan atas nama teman & data awal otomatis
- Pelanggan bisa memesankan untuk teman (kotak **Pesankan untuk teman** di bawah tabel). Kolom `dipesan_oleh` di sheet Kasbon mencatat siapa yang memasukkan pesanan. Pesanan teman yang sudah memesan sendiri tidak bisa diubah orang lain.
- Saat database masih kosong (hanya akun admin), aplikasi memuat `data_awal.json` otomatis. Tombol “Muat data awal” di tab Data awal tetap ada dan tidak menghapus status lunas.

## Kecepatan & pembaruan otomatis
- Semua sesi memakai satu cache di memori server. Membaca tidak memanggil Google; menulis memperbarui cache seketika (satu panggilan API per tulisan). Cache disegarkan diam-diam di latar belakang tiap ±60 detik agar suntingan manual di Google Sheet ikut terbaca.
- Tabel kasbon, kartu total, dan “Pesanan Hari Ini” menyegarkan diri otomatis: tiap 2 detik di akun admin, tiap 8 detik di akun pelanggan. Pesanan baru langsung muncul tanpa muat ulang.
- Cadangan RecordHarian ditulis di latar belakang supaya tombol “Pesan sekarang” tidak menunggu.
