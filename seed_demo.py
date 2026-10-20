"""Isi data contoh ke folder data/ (hanya untuk uji coba lokal)."""
import logic
from store import LocalStore

s = LocalStore()
now = logic.now_wib().isoformat(timespec="seconds")
for n in ["Budi QC", "Erry QC", "Erix Kama", "Sari Admin"]:
    s.append("Pelanggan", [{"nama": n, "sandi_hash": logic.hash_sandi("ungkep123"), "role": "pelanggan", "aktif": "1", "dibuat": now}])
rows = []
for tgl, items in {"2026-10-12": [("Nasi", "Nasi", 1, 4000), ("Ayam Sayur", "Ayam sayur lengkap", 1, 11000)],
                   "2026-10-13": [("Nasi", "Nasi", 1, 4000), ("Ayam Sayur", "Ayam sayur lengkap", 1, 11000), ("Minuman", "Es teh", 1, 3000)]}.items():
    for k, it, q, h in items:
        rows.append({"order_id": f"o-{tgl}-Budi", "tanggal": tgl, "periode": "2026-10", "pelanggan": "Budi QC", "kategori": k, "item": it,
                     "qty": q, "harga": h, "hpp": 0, "subtotal": q * h, "catatan": "", "status_pesanan": "Dipesan", "status_bayar": "Belum", "dibuat": now})
rows.append({"order_id": "o-2026-10-13-Erry", "tanggal": "2026-10-13", "periode": "2026-10", "pelanggan": "Erry QC", "kategori": "Nasi", "item": "Nasi",
             "qty": 2, "harga": 4000, "hpp": 0, "subtotal": 8000, "catatan": "", "status_pesanan": "Dipesan", "status_bayar": "Belum", "dibuat": now})
s.append("Kasbon", rows)
s.append("Menu", [{"id": "m001", "kategori": "Nasi", "nama": "Nasi", "harga": 4000, "hpp": 2000, "aktif": "1"},
                  {"id": "m002", "kategori": "Ayam Sayur", "nama": "Ayam sayur lengkap", "harga": 11000, "hpp": 7000, "aktif": "1"},
                  {"id": "m003", "kategori": "Minuman", "nama": "Es teh", "harga": 3000, "hpp": 1000, "aktif": "1"}])
