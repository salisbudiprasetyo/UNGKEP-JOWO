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

## Unggah rekap Excel (tab Data awal)
Unggah `.xlsx` berformat REKAP_PEMBELIAN (A1 "TANGGAL", baris 2 tanggal, kolom NAMA/PESANAN). Pilih bulan & tahun, cocokkan item/nama yang tak dikenali, lalu "Impor & timpa". Tanggal yang sudah ada **ditimpa**, bukan ditambah. Perlu `openpyxl`.

## Tampilan lunas
Sel tanggal yang sudah lunas berwarna hijau muda bertuliskan LUNAS (tetap bisa diklik). Kolom total hijau hanya bila semua tagihan periode lunas.

## Bayar sebagian (per item)
Di jendela rincian harian, centang item yang dibayar (admin: "Konfirmasi lunas", pelanggan: "Bayar sekarang"). Item yang tidak dicentang tetap kasbon. Hari yang baru sebagian lunas tampil hijau pucat dengan tulisan "sisa".

## Menu master vs menu harian
Mengubah Menu master tidak mengubah menu harian yang sudah diunggah. Setelah mengubah, buka tab Menu harian dan tekan "Unggah menu".

## Jam unggah menu & Close order
Tanggal bawaan di tab Menu harian: diunggah sebelum 13:00 WIB = menu hari ini, setelahnya = menu besok (tanggal tetap bisa diganti). Menu tanggal yang belum ada pesanan bisa dihapus. Tombol **Close order** di bawah rekap Pesanan Hari Ini menutup order: pelanggan tidak bisa memesan/mengubah/membatalkan; admin bisa **Buka kembali order**.

## Pesanan Hari Ini (rekap & revisi)
- Tampil untuk menu terdekat yang belum lewat. Menu hari ini hilang mulai jam 13:00 WIB (dan tidak tampil bila hari libur/belum ada menu berikutnya).
- Kartu hanya muncul untuk **permintaan revisi** (sebelum/sesudah, perubahan disorot, catatan otomatis; admin: Konfirmasi revisi / Tolak revisi).
- **Rekap pesanan** bisa diketuk per baris (paket, lauk saja, tiap menu) untuk melihat siapa yang memesan; admin menandai "Bungkus" per orang atau "Bungkus semua".
- Kolom TOTAL di tabel dan "TOTAL KASBON" di jendela tagihan = kasbon yang **belum dibayar**.

## Meong, kucing maskot
Kucing animasi menyapa setelah masuk, berjalan/berlari/duduk/tidur/melompat di bagian bawah halaman, lari ke tempat yang diketuk, dan bisa diketuk untuk ngobrol (menu hari ini, pesanan saya, tagihan, cara bayar, jam batas, libur). Jawaban dibuat dari data aplikasi dengan aturan sederhana (bukan AI luar). Kode: `kucing.py`. Kucing disembunyikan di halaman admin.


## Meong v2 (kucing gembul) & Tanya admin
- Karakter **Pompom** memakai pose dari ilustrasi karakter (`assets/pompom.json`), digerakkan mesin animasi 60 fps (`assets/kucing.js`) dengan efek 3D semu: perspektif, putar badan, miring, squash & stretch, bayangan, dan kedalaman.
- Diam di **kanan atas**; tiap **5 detik** melakukan aktivitas acak (25 macam, durasi beragam). Setelah login: tersenyum, melompat dari kiri ke kanan, lalu melambai.
- **Memberi makan**: saat Meong bilang "Aku lapar", pilih 🍗🍤🐟🥩🥛🍚 di gelembung.
- **Tanya**: pertanyaan di luar kemampuan Meong disimpan di sheet `Tanya`, pelanggan diminta menunggu. Admin menjawab di tab **Tanya**; jawaban muncul di obrolan dan gelembung kucing (setelah halaman dimuat ulang).
- Admin tidak bisa mengubah/membatalkan pesanan tanggal yang sudah lewat.
