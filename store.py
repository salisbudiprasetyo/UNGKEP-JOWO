"""Lapisan data. Dua backend dengan antarmuka sama: Google Sheets (produksi) dan CSV lokal (uji coba)."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pandas as pd

def _locked(fn):
    """Serialkan operasi baca-ubah-tulis dalam satu proses server."""
    def wrapper(self, *a, **k):
        with self.lock:
            return fn(self, *a, **k)
    wrapper.__name__ = fn.__name__
    return wrapper


SCHEMA: dict[str, list[str]] = {
    # akun pelanggan + admin (sandi disimpan sebagai hash)
    "Pelanggan": ["nama", "sandi_hash", "role", "aktif", "dibuat"],
    # permintaan reset sandi ("Tanya admin")
    "Permintaan": ["waktu", "nama", "jenis", "status"],
    # daftar menu master (harga bawaan + modal/HPP)
    "Menu": ["id", "kategori", "nama", "harga", "hpp", "aktif"],
    # daftar minuman + varian; kolom ready dicentang admin (otomatis masuk menu harian)
    "Minuman": ["nama", "varian", "harga", "hpp", "ready"],
    # menu yang diunggah admin untuk tanggal tertentu (harga bisa beda dari master)
    "MenuHarian": ["tanggal", "menu_id", "kategori", "nama", "harga", "hpp", "batas_stok", "stok", "alternatif"],
    # REKAP KASBON: satu baris per item yang dipesan (siapa, apa, harga, tanggal, status bayar)
    "Kasbon": ["order_id", "tanggal", "periode", "pelanggan", "kategori", "item", "qty", "harga", "hpp",
               "subtotal", "catatan", "status_pesanan", "status_bayar", "dibuat"],
    # revisi pesanan dari pelanggan yang menunggu konfirmasi admin (items = JSON daftar item baru)
    "Revisi": ["tanggal", "pelanggan", "jenis", "items", "catatan", "waktu", "status"],
    # pembayaran kasbon: bukti transfer disimpan sebagai foto kecil (base64) di kolom bukti
    "Pembayaran": ["id", "waktu", "pelanggan", "periode", "jumlah", "tagihan", "metode", "status", "bukti", "catatan", "tanggal"],
    # tanggal libur pemesanan (diatur admin)
    "Libur": ["tanggal", "keterangan", "dibuat"],
    # backup tabel "Pesanan Hari Ini" (satu baris per pelanggan per hari)
    "RecordHarian": ["tanggal", "periode", "kelompok", "pelanggan", "pesanan", "jumlah", "status", "dicatat"],
}


class LocalStore:
    """Menyimpan tiap sheet sebagai CSV di folder data/ (untuk uji coba tanpa Google)."""

    def __init__(self, folder: str = "data"):
        self.dir = Path(folder)
        self.dir.mkdir(exist_ok=True)
        self.lock = threading.RLock()

    def _path(self, sheet: str) -> Path:
        return self.dir / f"{sheet}.csv"

    def all(self, sheet: str) -> pd.DataFrame:
        p = self._path(sheet)
        if not p.exists():
            return pd.DataFrame(columns=SCHEMA[sheet])
        return pd.read_csv(p, dtype=str, keep_default_na=False)

    def _save(self, sheet: str, df: pd.DataFrame) -> None:
        df.reindex(columns=SCHEMA[sheet]).to_csv(self._path(sheet), index=False)

    @_locked
    def append(self, sheet: str, rows: list[dict]) -> None:
        if not rows:
            return
        df = pd.concat([self.all(sheet), pd.DataFrame(rows).astype(str)], ignore_index=True)
        self._save(sheet, df)

    @_locked
    def replace_where(self, sheet: str, col: str, value: str, rows: list[dict]) -> None:
        df = self.all(sheet)
        df = df[df[col] != str(value)]
        if rows:
            df = pd.concat([df, pd.DataFrame(rows).astype(str)], ignore_index=True)
        self._save(sheet, df)

    @_locked
    def replace_all(self, sheet: str, rows: list[dict]) -> None:
        self._save(sheet, pd.DataFrame(rows, columns=SCHEMA[sheet]).astype(str))

    @_locked
    def update_where(self, sheet: str, match: dict, updates: dict) -> int:
        df = self.all(sheet)
        mask = pd.Series(True, index=df.index)
        for k, v in match.items():
            mask &= df[k] == str(v)
        for k, v in updates.items():
            df.loc[mask, k] = str(v)
        self._save(sheet, df)
        return int(mask.sum())


class SheetsStore:
    """Google Sheets lewat gspread. Pembacaan di-cache singkat agar tidak kena batas kuota API."""

    TTL = 15  # detik

    def __init__(self, spreadsheet_id: str, creds: dict):
        import gspread

        self.gc = gspread.service_account_from_dict(creds)
        self.sh = self.gc.open_by_key(spreadsheet_id)
        self._cache: dict[str, tuple[float, pd.DataFrame]] = {}
        self._ws: dict[str, object] = {}
        self.lock = threading.RLock()
        for name in SCHEMA:
            self._worksheet(name)

    def _worksheet(self, sheet: str):
        if sheet in self._ws:
            return self._ws[sheet]
        import gspread

        try:
            ws = self.sh.worksheet(sheet)
        except gspread.WorksheetNotFound:
            ws = self.sh.add_worksheet(title=sheet, rows=500, cols=len(SCHEMA[sheet]) + 2)
            ws.update([SCHEMA[sheet]], "A1")
        else:
            try:  # samakan judul kolom bila skema bertambah kolom baru
                if ws.row_values(1) != SCHEMA[sheet]:
                    ws.update([SCHEMA[sheet]], "A1")
            except Exception:
                pass
        self._ws[sheet] = ws
        return ws

    def all(self, sheet: str) -> pd.DataFrame:
        hit = self._cache.get(sheet)
        if hit and time.time() - hit[0] < self.TTL:
            return hit[1].copy()
        values = self._worksheet(sheet).get_all_values()
        cols = SCHEMA[sheet]
        rows = [r + [""] * (len(cols) - len(r)) for r in values[1:] if any(c != "" for c in r)]
        df = pd.DataFrame([r[: len(cols)] for r in rows], columns=cols, dtype=str)
        self._cache[sheet] = (time.time(), df)
        return df.copy()

    def _invalidate(self, sheet: str) -> None:
        self._cache.pop(sheet, None)

    @_locked
    def append(self, sheet: str, rows: list[dict]) -> None:
        if not rows:
            return
        cols = SCHEMA[sheet]
        self._worksheet(sheet).append_rows([[str(r.get(c, "")) for c in cols] for r in rows],
                                           value_input_option="USER_ENTERED")
        self._invalidate(sheet)

    def _rewrite(self, sheet: str, df: pd.DataFrame) -> None:
        ws = self._worksheet(sheet)
        cols = SCHEMA[sheet]
        data = [cols] + df.reindex(columns=cols).fillna("").astype(str).values.tolist()
        ws.clear()
        ws.update(data, "A1", value_input_option="USER_ENTERED")
        self._invalidate(sheet)

    @_locked
    def replace_where(self, sheet: str, col: str, value: str, rows: list[dict]) -> None:
        self._invalidate(sheet)
        df = self.all(sheet)
        df = df[df[col] != str(value)]
        if rows:
            df = pd.concat([df, pd.DataFrame(rows).astype(str)], ignore_index=True)
        self._rewrite(sheet, df)

    @_locked
    def replace_all(self, sheet: str, rows: list[dict]) -> None:
        self._rewrite(sheet, pd.DataFrame(rows, columns=SCHEMA[sheet]).astype(str))

    @_locked
    def update_where(self, sheet: str, match: dict, updates: dict) -> int:
        self._invalidate(sheet)
        df = self.all(sheet)
        mask = pd.Series(True, index=df.index)
        for k, v in match.items():
            mask &= df[k] == str(v)
        for k, v in updates.items():
            df.loc[mask, k] = str(v)
        self._rewrite(sheet, df)
        return int(mask.sum())


def make_store(secrets) -> LocalStore | SheetsStore:
    backend = secrets.get("backend", os.environ.get("KASIR_BACKEND", "local"))
    if backend == "sheets":
        return SheetsStore(secrets["spreadsheet_id"], dict(secrets["gcp_service_account"]))
    return LocalStore()
