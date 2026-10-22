"""Pembayaran kasbon (tanpa UI): tagihan per periode, kirim bukti transfer, konfirmasi lunas."""
from __future__ import annotations

import base64
import io
from datetime import date

import pandas as pd

import logic

# status pembayaran
LUNAS_OTO = "Lunas (otomatis)"
LUNAS = "Lunas"
CEK = "Perlu dicek admin"
DITOLAK = "Ditolak"
STATUS_LUNAS = {LUNAS, LUNAS_OTO}


def _kasbon(store) -> pd.DataFrame:
    df = store.all("Kasbon")
    df["subtotal"] = pd.to_numeric(df["subtotal"], errors="coerce").fillna(0)
    return df[df["status_pesanan"] != "Batal"]


def tagihan(store, nama: str, kode: str) -> dict:
    """Ringkasan kasbon satu pelanggan pada satu periode: total, sisa (belum lunas), dan rincian per tanggal."""
    df = _kasbon(store)
    df = df[(df["pelanggan"] == nama) & (df["periode"] == kode)]
    total = float(df["subtotal"].sum())
    sisa = float(df.loc[df["status_bayar"] != "Lunas", "subtotal"].sum())
    per_hari = df.groupby("tanggal")["subtotal"].sum().sort_index().to_dict()
    return {"total": total, "sisa": sisa, "lunas": total > 0 and sisa == 0, "per_hari": per_hari}


def daftar(store, nama: str | None = None, kode: str | None = None) -> pd.DataFrame:
    df = store.all("Pembayaran")
    if nama:
        df = df[df["pelanggan"] == nama]
    if kode:
        df = df[df["periode"] == kode]
    return df


def menunggu_cek(store, nama: str, kode: str) -> pd.DataFrame:
    df = daftar(store, nama, kode)
    return df[df["status"] == CEK]


def kompres_bukti(data: bytes, batas: int = 44000) -> str:
    """Perkecil foto bukti jadi JPEG kecil (base64) agar muat di satu sel Google Sheets (maks 50.000 karakter)."""
    from PIL import Image, ImageOps

    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    for sisi, mutu in ((520, 55), (420, 50), (340, 45), (280, 40), (220, 35)):
        im = img.copy()
        im.thumbnail((sisi, sisi * 3))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=mutu, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        if len(b64) <= batas:
            return b64
    return b64[:0]


def _id() -> str:
    return logic.now_wib().strftime("%Y%m%d%H%M%S%f")


def _tandai_lunas(store, nama: str, kode: str) -> None:
    store.update_where("Kasbon", {"pelanggan": nama, "periode": kode}, {"status_bayar": "Lunas"})


def kirim_pembayaran(store, nama: str, kode: str, jumlah: float, foto: bytes | None) -> tuple[str | None, str]:
    """Pelanggan mengirim bukti transfer. Bila nominal sama dengan sisa tagihan -> lunas otomatis,
    selain itu tetap disimpan dan menunggu pengecekan admin. Kembalikan (galat, status)."""
    t = tagihan(store, nama, kode)
    if t["sisa"] <= 0:
        return "Tidak ada tagihan yang tersisa pada periode ini.", ""
    if jumlah <= 0:
        return "Isi jumlah yang kamu transfer.", ""
    if not foto:
        return "Unggah foto bukti pembayaran dulu.", ""
    try:
        bukti = kompres_bukti(foto)
    except Exception:
        return "Foto tidak bisa dibaca. Coba foto lain (JPG/PNG).", ""
    if not bukti:
        return "Foto terlalu besar untuk disimpan. Coba foto lain.", ""
    status = LUNAS_OTO if int(round(jumlah)) == int(round(t["sisa"])) else CEK
    store.append("Pembayaran", [{
        "id": _id(), "waktu": logic.now_wib().isoformat(timespec="seconds"), "pelanggan": nama, "periode": kode,
        "jumlah": int(round(jumlah)), "tagihan": int(round(t["sisa"])), "metode": "Transfer BNI",
        "status": status, "bukti": bukti, "catatan": "",
    }])
    if status == LUNAS_OTO:
        _tandai_lunas(store, nama, kode)
    return None, status


def konfirmasi_lunas(store, nama: str, kode: str, metode: str = "Tunai") -> None:
    """Admin menandai kasbon periode ini lunas. Pembayaran yang menunggu cek ikut disetujui."""
    t = tagihan(store, nama, kode)
    ada = store.update_where("Pembayaran", {"pelanggan": nama, "periode": kode, "status": CEK}, {"status": LUNAS})
    if not ada and t["sisa"] > 0:
        store.append("Pembayaran", [{
            "id": _id(), "waktu": logic.now_wib().isoformat(timespec="seconds"), "pelanggan": nama, "periode": kode,
            "jumlah": int(round(t["sisa"])), "tagihan": int(round(t["sisa"])), "metode": metode,
            "status": LUNAS, "bukti": "", "catatan": "Dikonfirmasi admin",
        }])
    _tandai_lunas(store, nama, kode)


def tolak_pembayaran(store, nama: str, kode: str) -> None:
    store.update_where("Pembayaran", {"pelanggan": nama, "periode": kode, "status": CEK}, {"status": DITOLAK})


def batalkan_lunas(store, nama: str, kode: str) -> None:
    """Admin salah menandai lunas: kembalikan ke belum lunas."""
    store.update_where("Kasbon", {"pelanggan": nama, "periode": kode}, {"status_bayar": "Belum"})
    store.update_where("Pembayaran", {"pelanggan": nama, "periode": kode, "status": LUNAS}, {"status": DITOLAK})
    store.update_where("Pembayaran", {"pelanggan": nama, "periode": kode, "status": LUNAS_OTO}, {"status": DITOLAK})


def status_periode(store, nama: str, kode: str) -> str:
    t = tagihan(store, nama, kode)
    if t["total"] <= 0:
        return "—"
    if t["lunas"]:
        return "Lunas"
    if not menunggu_cek(store, nama, kode).empty:
        return "Menunggu cek"
    return "Belum bayar"
