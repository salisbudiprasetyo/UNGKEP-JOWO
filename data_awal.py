"""Muat data awal (pelanggan, riwayat, menu, minuman) dari data_awal.json ke database yang sedang dipakai."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import logic
import orders

BERKAS = Path(__file__).parent / "data_awal.json"


def ringkasan() -> dict:
    d = json.loads(BERKAS.read_text(encoding="utf-8"))
    return {"pelanggan": len(d["pelanggan"]), "minuman": len(d["minuman"]), "menu": len(d["menu"]),
            "riwayat": len({(r["tanggal"], r["pelanggan"]) for r in d["riwayat"]}),
            "total": sum(r["qty"] * r["harga"] for r in d["riwayat"])}


def muat(store, sandi_awal: str) -> dict:
    """Aman diulang: pelanggan yang sudah ada tidak diubah, riwayat diganti per pesanan, menu master/minuman ditimpa."""
    d = json.loads(BERKAS.read_text(encoding="utf-8"))
    sekarang = logic.now_wib().isoformat(timespec="seconds")

    ada = {n.lower() for n in store.all("Pelanggan")["nama"]}
    baru = []
    for nm in d["pelanggan"]:
        if nm.lower() not in ada:
            ada.add(nm.lower())
            baru.append({"nama": nm, "sandi_hash": logic.hash_sandi(sandi_awal), "role": "pelanggan", "aktif": "1", "dibuat": sekarang})
    store.append("Pelanggan", baru)

    store.replace_all("Menu", d["menu"])
    store.replace_all("Minuman", d["minuman"])

    id_menu = {m["nama"]: m["id"] for m in d["menu"]}
    per_tgl: dict[str, list[dict]] = {}
    for r in d["menu_harian"]:
        r = dict(r)
        r["menu_id"] = id_menu.get(r["nama"], "")
        per_tgl.setdefault(r["tanggal"], []).append(r)
    for tgl, rows in per_tgl.items():
        store.replace_where("MenuHarian", "tanggal", tgl, rows)

    pesanan: dict[tuple[str, str], list[dict]] = {}
    for r in d["riwayat"]:
        pesanan.setdefault((r["tanggal"], r["pelanggan"]), []).append(r)
    for (tgl_iso, nama), items in pesanan.items():
        tgl = date.fromisoformat(tgl_iso)
        rows = orders._baris(tgl, nama, [{"kategori": i["kategori"], "item": i["item"], "qty": i["qty"],
                                           "harga": i["harga"], "hpp": 0} for i in items], "", "Disetujui", f"{tgl_iso}T08:00:00+07:00")
        store.replace_where("Kasbon", "order_id", orders.order_id(tgl, nama), rows)
    for tgl_iso in sorted({t for t, _ in pesanan}):
        orders.simpan_record(store, date.fromisoformat(tgl_iso))
    return {"pelanggan_baru": len(baru), "pesanan": len(pesanan), "tanggal": sorted({t for t, _ in pesanan})}
