"""Logika pesanan (tanpa UI): simpan pesanan, revisi, stok, pengelompokan 3 tabel, backup harian."""
from __future__ import annotations

import json
from collections import OrderedDict
from datetime import date

import pandas as pd

import logic

KATEGORI = ["Nasi", "Ayam Sayur", "Lauk", "Minuman", "Lain-lain"]
UTAMA = {"Nasi", "Ayam Sayur", "Lauk"}
KELOMPOK = {
    1: "NASI + LAUK",
    2: "LAUK SAJA (TANPA NASI)",
    3: "MINUMAN & LAINNYA SAJA",
}
LAUK = {"Ayam Sayur", "Lauk"}  # kategori yang dihitung sebagai lauk utama


def _num(x, d=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def order_id(tgl: date, nama: str) -> str:
    return f"{tgl.isoformat()}|{nama}"


# ------------------------------------------------------------------ menu & stok
def menu_hari(store, tgl: date) -> pd.DataFrame:
    df = store.all("MenuHarian")
    df = df[df["tanggal"] == tgl.isoformat()].drop_duplicates("nama", keep="last").copy()   # nama ganda tidak boleh membuat pesanan rusak
    for c in ("harga", "hpp", "batas_stok", "stok"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["_k"] = df["kategori"].map(lambda k: KATEGORI.index(k) if k in KATEGORI else 99)
    return df.sort_values("_k", kind="stable").reset_index(drop=True)


def libur_map(store) -> dict[date, str]:
    """Tanggal libur pemesanan -> keterangan."""
    df = store.all("Libur")
    return {pd.to_datetime(r.tanggal).date(): r.keterangan for r in df.itertuples() if r.tanggal}


def is_libur(store, tgl: date) -> bool:
    return tgl in libur_map(store)


def set_libur(store, tgl: date, ket: str = "") -> None:
    store.replace_where("Libur", "tanggal", tgl.isoformat(),
                        [{"tanggal": tgl.isoformat(), "keterangan": ket, "dibuat": logic.now_wib().isoformat(timespec="seconds")}])


def hapus_libur(store, tgl: date) -> None:
    store.replace_where("Libur", "tanggal", tgl.isoformat(), [])


def tanggal_menu(store) -> list[date]:
    """Tanggal yang menunya sudah diunggah dan tidak libur."""
    libur = libur_map(store)
    ds = {pd.to_datetime(t).date() for t in store.all("MenuHarian")["tanggal"] if t}
    return sorted(d for d in ds if d not in libur)


def tanggal_aktif(store) -> date | None:
    """Tanggal yang ditampilkan di 'Pesanan Hari Ini' = menu terbaru yang sudah diunggah admin."""
    ds = tanggal_menu(store)
    return ds[-1] if ds else None


def bisa_pesan(store, tgl: date, sekarang=None) -> bool:
    """Tombol PESAN aktif bila menu tanggal itu sudah ada dan belum lewat batas jam pada hari H."""
    return tgl in set(tanggal_menu(store)) and logic.bisa_edit(tgl, sekarang)


def tanggal_pesan_pelanggan(store, sekarang=None) -> date | None:
    """Satu-satunya tanggal yang tombol PESAN-nya aktif untuk pelanggan: menu terdekat (hari ini atau
    yang berikutnya) yang sudah diunggah dan belum lewat batas jam."""
    hari = (sekarang or logic.now_wib()).date()
    for d in tanggal_menu(store):
        if d >= hari and logic.bisa_edit(d, sekarang):
            return d
    return None


def tanggal_pesan_admin(store, sekarang=None) -> date | None:
    """Tanggal tempat admin bisa menambah pesanan atas nama pelanggan: menu terdekat mulai hari ini (tanpa batas jam)."""
    hari = (sekarang or logic.now_wib()).date()
    return next((d for d in tanggal_menu(store) if d >= hari), None)


def _kasbon(store) -> pd.DataFrame:
    df = store.all("Kasbon")
    for c in ("qty", "harga", "hpp", "subtotal"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def pesanan_tgl(store, tgl: date) -> pd.DataFrame:
    df = _kasbon(store)
    return df[(df["tanggal"] == tgl.isoformat()) & (df["status_pesanan"] != "Batal")]


def batas_stok(store, tgl: date, nama_pelanggan: str | None = None) -> dict[str, int | None]:
    """Sisa stok per menu untuk pelanggan tertentu (stok total - pesanan orang lain). None = tanpa batas."""
    menu = menu_hari(store, tgl)
    dipesan = pesanan_tgl(store, tgl)
    if nama_pelanggan:
        dipesan = dipesan[dipesan["pelanggan"] != nama_pelanggan]
    hasil: dict[str, int | None] = {}
    for r in menu.itertuples():
        if r.batas_stok == 1:
            terpakai = dipesan.loc[dipesan["item"] == r.nama, "qty"].sum()
            hasil[r.nama] = max(0, int(_num(r.stok) - terpakai))
        else:
            hasil[r.nama] = None
    return hasil


# ------------------------------------------------------------------ baca pesanan
def items_pesanan(store, tgl: date, nama: str) -> list[dict]:
    df = pesanan_tgl(store, tgl)
    df = df[df["pelanggan"] == nama]
    return [{"kategori": r.kategori, "item": r.item, "qty": int(r.qty), "harga": float(r.harga), "hpp": float(r.hpp)}
            for r in df.itertuples()]


def catatan_pesanan(store, tgl: date, nama: str) -> str:
    df = pesanan_tgl(store, tgl)
    df = df[df["pelanggan"] == nama]
    return str(df.iloc[0]["catatan"]) if not df.empty else ""


def revisi_menunggu(store, tgl: date, nama: str) -> dict | None:
    df = store.all("Revisi")
    df = df[(df["tanggal"] == tgl.isoformat()) & (df["pelanggan"] == nama) & (df["status"] == "Menunggu")]
    if df.empty:
        return None
    r = df.iloc[-1]
    return {"jenis": r["jenis"], "items": json.loads(r["items"] or "[]"), "catatan": r["catatan"], "waktu": r["waktu"]}


# ------------------------------------------------------------------ tulis pesanan
def _baris(tgl: date, nama: str, items: list[dict], catatan: str, status: str, dibuat: str, oleh: str = "") -> list[dict]:
    kode = logic.kode_periode(logic.periode_untuk(tgl)[0])
    return [{
        "order_id": order_id(tgl, nama), "tanggal": tgl.isoformat(), "periode": kode, "pelanggan": nama,
        "kategori": it["kategori"], "item": it["item"], "qty": it["qty"], "harga": int(it["harga"]),
        "hpp": int(it.get("hpp", 0)), "subtotal": int(it["qty"] * it["harga"]), "catatan": catatan,
        "status_pesanan": status, "status_bayar": "Belum", "dibuat": dibuat, "dipesan_oleh": oleh,
    } for it in items]


def _susun_items(store, tgl: date, nama: str, pilihan: dict[str, int]) -> tuple[list[dict], str | None]:
    """Ubah {nama_menu: qty} menjadi daftar item berharga; validasi menu dan stok."""
    menu = menu_hari(store, tgl).set_index("nama")
    lama = {i["item"]: i for i in items_pesanan(store, tgl, nama)}
    sisa = batas_stok(store, tgl, nama)
    items = []
    for item, qty in pilihan.items():
        qty = int(qty or 0)
        if qty <= 0:
            continue
        if item not in menu.index:
            return [], f"Menu “{item}” tidak tersedia."
        cap = sisa.get(item)
        if cap is not None and qty > cap:
            return [], f"Stok {item} tinggal {cap}."
        harga = lama[item]["harga"] if item in lama else _num(menu.loc[item, "harga"])
        hpp = lama[item]["hpp"] if item in lama else _num(menu.loc[item, "hpp"])
        items.append({"kategori": menu.loc[item, "kategori"], "item": item, "qty": qty, "harga": harga, "hpp": hpp})
    return items, None


def pemesan(store, tgl: date, nama: str) -> str:
    """Siapa yang memasukkan pesanan ini (kosong pada data lama = pemilik akun sendiri)."""
    df = pesanan_tgl(store, tgl)
    df = df[df["pelanggan"] == nama]
    return (str(df.iloc[0]["dipesan_oleh"]) or nama) if not df.empty else ""


def simpan_pesanan(store, tgl: date, nama: str, pilihan: dict[str, int], catatan: str = "",
                   langsung: bool = False, sekarang=None, oleh: str | None = None) -> tuple[str | None, str]:
    """Kembalikan (galat, jenis). jenis: 'baru' | 'revisi' | 'langsung'."""
    if is_libur(store, tgl):
        return "Tanggal ini libur pemesanan.", ""
    if not langsung and not bisa_pesan(store, tgl, sekarang):
        return f"Waktu pemesanan untuk tanggal ini sudah ditutup (batas {logic.BATAS_TEKS} WIB).", ""
    items, err = _susun_items(store, tgl, nama, pilihan)
    if err:
        return err, ""
    if not items:
        return "Pilih minimal satu item.", ""
    wkt = (sekarang or logic.now_wib()).isoformat(timespec="seconds")
    ada = bool(items_pesanan(store, tgl, nama))
    oid = order_id(tgl, nama)
    oleh = oleh or nama
    if ada and not langsung and oleh != nama and pemesan(store, tgl, nama) != oleh:
        return f"{nama} sudah memesan sendiri. Minta dia mengubahnya lewat akunnya.", ""
    if not ada:
        store.replace_where("Kasbon", "order_id", oid, _baris(tgl, nama, items, catatan, "Dipesan", wkt, oleh))
        kind = "baru"
    elif langsung:
        lama = pesanan_tgl(store, tgl)
        lama = lama[lama["pelanggan"] == nama]
        rows = _baris(tgl, nama, items, catatan, "Disetujui", wkt, pemesan(store, tgl, nama) if not lama.empty else oleh)
        for r in rows:
            r["status_bayar"] = lama.iloc[0]["status_bayar"] if not lama.empty else "Belum"
        store.replace_where("Kasbon", "order_id", oid, rows)
        _tutup_revisi(store, tgl, nama, "Diganti admin")
        kind = "langsung"
    else:
        _tutup_revisi(store, tgl, nama, "Diganti")
        store.append("Revisi", [{"tanggal": tgl.isoformat(), "pelanggan": nama, "jenis": "ubah",
                                 "items": json.dumps(items), "catatan": catatan, "waktu": wkt, "status": "Menunggu"}])
        kind = "revisi"
    simpan_record(store, tgl)
    return None, kind


def batalkan_pesanan(store, tgl: date, nama: str, langsung: bool = False, sekarang=None) -> str | None:
    if not items_pesanan(store, tgl, nama):
        return "Pesanan tidak ditemukan."
    if not langsung and not logic.bisa_edit(tgl, sekarang):
        return f"Waktu pembatalan sudah lewat (batas {logic.BATAS_TEKS} WIB)."
    wkt = (sekarang or logic.now_wib()).isoformat(timespec="seconds")
    if langsung:
        store.update_where("Kasbon", {"order_id": order_id(tgl, nama)}, {"status_pesanan": "Batal"})
        _tutup_revisi(store, tgl, nama, "Diganti admin")
    else:
        _tutup_revisi(store, tgl, nama, "Diganti")
        store.append("Revisi", [{"tanggal": tgl.isoformat(), "pelanggan": nama, "jenis": "batal",
                                 "items": "[]", "catatan": "", "waktu": wkt, "status": "Menunggu"}])
    simpan_record(store, tgl)
    return None


def _tutup_revisi(store, tgl: date, nama: str, status: str) -> None:
    store.update_where("Revisi", {"tanggal": tgl.isoformat(), "pelanggan": nama, "status": "Menunggu"}, {"status": status})


def konfirmasi_revisi(store, tgl: date, nama: str) -> None:
    rev = revisi_menunggu(store, tgl, nama)
    if not rev:
        return
    oid = order_id(tgl, nama)
    if rev["jenis"] == "batal":
        store.update_where("Kasbon", {"order_id": oid}, {"status_pesanan": "Batal"})
    else:
        bayar = pesanan_tgl(store, tgl)
        bayar = bayar[bayar["pelanggan"] == nama]
        status_bayar = bayar.iloc[0]["status_bayar"] if not bayar.empty else "Belum"
        rows = _baris(tgl, nama, rev["items"], rev["catatan"], "Disetujui", rev["waktu"], pemesan(store, tgl, nama))
        for r in rows:
            r["status_bayar"] = status_bayar
        store.replace_where("Kasbon", "order_id", oid, rows)
    store.update_where("Revisi", {"tanggal": tgl.isoformat(), "pelanggan": nama, "status": "Menunggu"}, {"status": "Disetujui"})
    simpan_record(store, tgl)


def tolak_revisi(store, tgl: date, nama: str) -> None:
    _tutup_revisi(store, tgl, nama, "Ditolak")
    simpan_record(store, tgl)


def set_dibungkus(store, tgl: date, nama: str, ya: bool) -> None:
    store.update_where("Kasbon", {"order_id": order_id(tgl, nama)}, {"status_pesanan": "Dibungkus" if ya else "Dipesan"})
    simpan_record(store, tgl)


# ------------------------------------------------------------------ tampilan: kelompok & rekap
def teks_pesanan(items: list[dict]) -> tuple[str, int, str]:
    """(baris utama, jumlah, baris tambahan). Jika semua item utama sama qty: 'Nasi + Ayam sayur lengkap' × q."""
    utama = [i for i in items if i["kategori"] in UTAMA]
    extra = [i for i in items if i["kategori"] not in UTAMA]
    ekstra_txt = " · ".join(f"{i['item']} ×{i['qty']}" for i in extra)
    if not utama:
        return "", sum(i["qty"] for i in extra), ekstra_txt
    qs = {i["qty"] for i in utama}
    if len(qs) == 1:
        return " + ".join(i["item"] for i in utama), qs.pop(), ekstra_txt
    return " · ".join(f"{i['item']} ×{i['qty']}" for i in utama), sum(i["qty"] for i in utama), ekstra_txt


def kelompok_dari(items: list[dict]) -> int:
    kat = {i["kategori"] for i in items}
    if "Nasi" in kat:
        return 1
    if kat & LAUK:
        return 2
    return 3


def daftar_pesanan(store, tgl: date) -> list[dict]:
    """Semua pesanan aktif pada tanggal tsb (memakai versi LAMA sampai admin konfirmasi)."""
    df = pesanan_tgl(store, tgl)
    hasil = []
    for nama, g in df.groupby("pelanggan", sort=False):
        items = [{"kategori": r.kategori, "item": r.item, "qty": int(r.qty), "harga": float(r.harga), "hpp": float(r.hpp)}
                 for r in g.itertuples()]
        rev = revisi_menunggu(store, tgl, nama)
        stat = set(g["status_pesanan"])
        if rev:
            status = "Minta batal" if rev["jenis"] == "batal" else "Revisi"
        elif "Dibungkus" in stat:
            status = "Dibungkus"
        elif "Disetujui" in stat:
            status = "Disetujui"
        else:
            status = "Dipesan"
        baris_utama, jumlah, ekstra = teks_pesanan(items)
        hasil.append({
            "nama": nama, "items": items, "catatan": str(g.iloc[0]["catatan"]), "status": status, "revisi": rev,
            "kelompok": kelompok_dari(items), "utama": baris_utama, "jumlah": jumlah, "ekstra": ekstra,
            "seragam": bool(baris_utama) and len({i["qty"] for i in items if i["kategori"] in UTAMA}) == 1,
            "total": float(g["subtotal"].sum()), "dibuat": str(g.iloc[0]["dibuat"]),
            "oleh": (str(g.iloc[0]["dipesan_oleh"]) if str(g.iloc[0]["dipesan_oleh"]) not in ("", nama) else ""),
        })
    hasil.sort(key=lambda o: (o["dibuat"], o["nama"].lower()))
    return hasil


def rekap(orders: list[dict]) -> "OrderedDict[str, int]":
    """Jumlah per item (urut kategori) untuk sekumpulan pesanan."""
    jumlah: dict[tuple[int, str], int] = {}
    for o in orders:
        for i in o["items"]:
            k = (KATEGORI.index(i["kategori"]) if i["kategori"] in KATEGORI else 99, i["item"])
            jumlah[k] = jumlah.get(k, 0) + i["qty"]
    return OrderedDict((nm, q) for (_, nm), q in sorted(jumlah.items()))


def selisih(lama: list[dict], baru: list[dict]) -> list[tuple[str, str, int]]:
    """Perubahan lama → baru: [(simbol, item, selisih)] dengan simbol '+', '−', '='."""
    a = {i["item"]: i["qty"] for i in lama}
    b = {i["item"]: i["qty"] for i in baru}
    out = []
    for nm in list(dict.fromkeys(list(a) + list(b))):
        d = b.get(nm, 0) - a.get(nm, 0)
        out.append(("+" if d > 0 else "−" if d < 0 else "=", nm, abs(d)))
    return out


# ------------------------------------------------------------------ backup harian
import threading as _th

_REC_LOCK = _th.Lock()


def simpan_record(store, tgl: date, tunggu: bool = False) -> None:
    """Tulis ulang snapshot 'Pesanan Hari Ini' untuk tanggal tsb ke sheet RecordHarian (backup, satu sheet per periode)."""
    if not tunggu:   # cadangan tidak perlu ditunggu pelanggan: tulis di latar belakang
        import threading
        threading.Thread(target=simpan_record, args=(store, tgl, True), daemon=True).start()
        return
    with _REC_LOCK:   # satu per satu; gambaran dibuat setelah giliran tiba sehingga selalu yang terbaru
        _tulis_record(store, tgl)


def _tulis_record(store, tgl: date) -> None:
    kode = logic.kode_periode(logic.periode_untuk(tgl)[0])
    wkt = logic.now_wib().isoformat(timespec="seconds")
    rows = []
    for o in sorted(daftar_pesanan(store, tgl), key=lambda x: (x["kelompok"], x["dibuat"])):
        teks = " + ".join(filter(None, [o["utama"], o["ekstra"]]))
        rows.append({"tanggal": tgl.isoformat(), "periode": kode, "kelompok": KELOMPOK[o["kelompok"]],
                     "pelanggan": o["nama"], "pesanan": teks + (f" ({o['catatan']})" if o["catatan"] else ""),
                     "jumlah": o["jumlah"], "status": o["status"], "dicatat": wkt})
    store.replace_where("RecordHarian", "tanggal", tgl.isoformat(), rows)
