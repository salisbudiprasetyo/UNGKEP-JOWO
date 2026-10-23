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


def tagihan(store, nama: str, kode: str, tanggal: str | None = None, pilih: list[str] | None = None) -> dict:
    """Ringkasan kasbon satu pelanggan pada satu periode (atau satu tanggal bila `tanggal` diisi):
    total, sisa (belum lunas), dan rincian per tanggal dengan status lunas."""
    df = _kasbon(store)
    df = df[(df["pelanggan"] == nama) & (df["periode"] == kode)]
    if tanggal:
        df = df[df["tanggal"] == tanggal]
    if pilih is not None:   # hanya item yang dicentang
        df = df[df["item"].isin(pilih)]
    total = float(df["subtotal"].sum())
    sisa = float(df.loc[df["status_bayar"] != "Lunas", "subtotal"].sum())
    per_hari = {}
    for tgl, g in df.groupby("tanggal"):
        per_hari[tgl] = {"total": float(g["subtotal"].sum()), "lunas": bool((g["status_bayar"] == "Lunas").all()),
                         "sisa": float(g.loc[g["status_bayar"] != "Lunas", "subtotal"].sum())}
    return {"total": total, "sisa": sisa, "lunas": total > 0 and sisa == 0, "per_hari": dict(sorted(per_hari.items()))}


def daftar(store, nama: str | None = None, kode: str | None = None) -> pd.DataFrame:
    df = store.all("Pembayaran")
    if nama:
        df = df[df["pelanggan"] == nama]
    if kode:
        df = df[df["periode"] == kode]
    return df


def menunggu_cek(store, nama: str, kode: str, tanggal: str | None = None) -> pd.DataFrame:
    df = daftar(store, nama, kode)
    df = df[df["status"] == CEK]
    if tanggal:  # bukti khusus tanggal itu, atau bukti satu periode penuh
        df = df[(df["tanggal"] == tanggal) | (df["tanggal"] == "")]
    return df


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


def _cocok(nama: str, kode: str, tgl: str | None) -> dict:
    m = {"pelanggan": nama, "periode": kode}
    if tgl:
        m["tanggal"] = tgl
    return m


def item_belum_lunas(store, nama: str, kode: str, tgl: str) -> list[dict]:
    """Item pada satu tanggal beserta status lunasnya: [{item, qty, subtotal, lunas}]."""
    df = _kasbon(store)
    df = df[(df["pelanggan"] == nama) & (df["periode"] == kode) & (df["tanggal"] == tgl)]
    return [{"item": r.item, "qty": int(float(r.qty or 0)), "subtotal": float(r.subtotal), "lunas": r.status_bayar == "Lunas"}
            for r in df.itertuples()]


def _tandai_lunas(store, nama: str, kode: str, tgl: str | None = None, pilih: list[str] | None = None) -> None:
    if pilih is None:
        store.update_where("Kasbon", _cocok(nama, kode, tgl), {"status_bayar": "Lunas"})
        return
    for it in pilih:
        store.update_where("Kasbon", {**_cocok(nama, kode, tgl), "item": it}, {"status_bayar": "Lunas"})


_PFX = "ITEM:"


def _catat_item(pilih: list[str] | None) -> str:
    return _PFX + "|".join(pilih) if pilih is not None else ""


def _item_dari_cek(store, nama: str, kode: str, tgl: str | None) -> list[str] | None:
    """Item yang tercatat pada bukti transfer yang menunggu cek (None = seluruh tagihan)."""
    df = daftar(store, nama, kode)
    df = df[(df["status"] == CEK) & (df["tanggal"] == (tgl or ""))]
    hasil: list[str] = []
    for c in df["catatan"]:
        if not str(c).startswith(_PFX):
            return None
        hasil += [x for x in str(c)[len(_PFX):].split("|") if x]
    return hasil if len(df) else None


def kirim_pembayaran(store, nama: str, kode: str, jumlah: float, foto: bytes | None,
                     tgl: str | None = None, pilih: list[str] | None = None) -> tuple[str | None, str]:
    """Pelanggan mengirim bukti transfer. Bila nominal sama dengan sisa tagihan -> lunas otomatis,
    selain itu tetap disimpan dan menunggu pengecekan admin. Kembalikan (galat, status)."""
    t = tagihan(store, nama, kode, tgl, pilih)
    if t["sisa"] <= 0:
        return "Tidak ada tagihan yang tersisa pada periode ini.", ""
    if pilih is not None:   # hanya item yang masih belum lunas
        pilih = [i["item"] for i in item_belum_lunas(store, nama, kode, tgl or "") if not i["lunas"] and i["item"] in pilih]
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
        "status": status, "bukti": bukti, "catatan": _catat_item(pilih), "tanggal": tgl or "",
    }])
    if status == LUNAS_OTO:
        _tandai_lunas(store, nama, kode, tgl, pilih)
    return None, status


def konfirmasi_lunas(store, nama: str, kode: str, tgl: str | None = None, metode: str = "Tunai",
                     pilih: list[str] | None = None) -> None:
    """Admin menandai kasbon (satu tanggal, atau satu periode penuh) lunas. Bukti yang menunggu cek ikut disetujui.
    `pilih` = hanya item itu yang lunas; bila kosong dan bukti transfer mencatat item tertentu, item itulah yang lunas."""
    if pilih is None:
        pilih = _item_dari_cek(store, nama, kode, tgl)
    t = tagihan(store, nama, kode, tgl, pilih)
    ada = store.update_where("Pembayaran", {"pelanggan": nama, "periode": kode, "status": CEK, "tanggal": tgl or ""},
                             {"status": LUNAS})
    if not ada and t["sisa"] > 0:
        store.append("Pembayaran", [{
            "id": _id(), "waktu": logic.now_wib().isoformat(timespec="seconds"), "pelanggan": nama, "periode": kode,
            "jumlah": int(round(t["sisa"])), "tagihan": int(round(t["sisa"])), "metode": metode,
            "status": LUNAS, "bukti": "", "catatan": _catat_item(pilih) if pilih is not None else "Dikonfirmasi admin",
            "tanggal": tgl or "",
        }])
    _tandai_lunas(store, nama, kode, tgl, pilih)


def tolak_pembayaran(store, nama: str, kode: str, tgl: str | None = None) -> None:
    m = {"pelanggan": nama, "periode": kode, "status": CEK}
    if tgl is not None:
        m["tanggal"] = tgl
    store.update_where("Pembayaran", m, {"status": DITOLAK})


def batalkan_lunas(store, nama: str, kode: str, tgl: str | None = None) -> None:
    """Admin salah menandai lunas: kembalikan ke belum lunas."""
    store.update_where("Kasbon", _cocok(nama, kode, tgl), {"status_bayar": "Belum"})
    for st_ in (LUNAS, LUNAS_OTO):
        m = {"pelanggan": nama, "periode": kode, "status": st_}
        if tgl:
            m["tanggal"] = tgl
        store.update_where("Pembayaran", m, {"status": DITOLAK})


def status_periode(store, nama: str, kode: str) -> str:
    t = tagihan(store, nama, kode)
    if t["total"] <= 0:
        return "—"
    if t["lunas"]:
        return "Lunas"
    if not menunggu_cek(store, nama, kode).empty:
        return "Menunggu cek"
    return "Belum bayar"
