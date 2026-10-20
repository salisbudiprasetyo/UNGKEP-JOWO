"""Layanan aplikasi: akun, sesi, dan pembacaan data bersama untuk semua halaman."""
from __future__ import annotations

import streamlit as st

import logic
from store import make_store


@st.cache_resource(show_spinner="Menghubungkan ke database…")
def get_store():
    store = make_store(st.secrets)
    _pastikan_admin(store)
    return store


def _pastikan_admin(store) -> None:
    df = store.all("Pelanggan")
    if (df["role"] == "admin").any():
        return
    nama = st.secrets.get("admin_name", "ADMIN")
    sandi = st.secrets.get("admin_password", "admin123")
    store.append("Pelanggan", [{
        "nama": nama, "sandi_hash": logic.hash_sandi(sandi), "role": "admin",
        "aktif": "1", "dibuat": logic.now_wib().isoformat(timespec="seconds"),
    }])


def sandi_awal() -> str:
    return st.secrets.get("default_password", "ungkep123")


# ---- sesi ----
def user() -> str | None:
    return st.session_state.get("user")


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def keluar() -> None:
    for k in ("user", "role"):
        st.session_state.pop(k, None)


# ---- akun ----
def daftar_nama(store) -> list[str]:
    df = store.all("Pelanggan")
    df = df[df["aktif"] != "0"]
    return sorted(df["nama"].tolist(), key=str.lower)


def masuk(store, nama: str, sandi: str) -> str | None:
    """Kembalikan None bila sukses, atau pesan galat."""
    df = store.all("Pelanggan")
    row = df[df["nama"] == nama]
    if row.empty or row.iloc[0]["aktif"] == "0":
        return "Nama tidak ditemukan."
    if not logic.cek_sandi(sandi, row.iloc[0]["sandi_hash"]):
        return "Sandi salah. Lupa sandi? Tekan 'Tanya admin'."
    st.session_state["user"] = nama
    st.session_state["role"] = row.iloc[0]["role"]
    return None


def daftar_baru(store, nama: str) -> str | None:
    nama = logic.bersih_nama(nama)
    if len(nama) < 3:
        return "Nama minimal 3 huruf."
    ada = {n.lower() for n in store.all("Pelanggan")["nama"]}
    if nama.lower() in ada:
        return "Nama sudah terdaftar. Silakan masuk, atau pakai nama lain (mis. tambah inisial/bagian)."
    store.append("Pelanggan", [{
        "nama": nama, "sandi_hash": logic.hash_sandi(sandi_awal()), "role": "pelanggan",
        "aktif": "1", "dibuat": logic.now_wib().isoformat(timespec="seconds"),
    }])
    return None


def ganti_sandi(store, nama: str, lama: str, baru: str) -> str | None:
    row = store.all("Pelanggan").query("nama == @nama")
    if row.empty or not logic.cek_sandi(lama, row.iloc[0]["sandi_hash"]):
        return "Sandi lama salah."
    if len(baru) < 4:
        return "Sandi baru minimal 4 karakter."
    store.update_where("Pelanggan", {"nama": nama}, {"sandi_hash": logic.hash_sandi(baru)})
    return None


def tanya_admin(store, nama: str) -> None:
    store.append("Permintaan", [{
        "waktu": logic.now_wib().isoformat(timespec="seconds"), "nama": nama,
        "jenis": "reset_sandi", "status": "Menunggu",
    }])


def reset_sandi(store, nama: str) -> None:
    store.update_where("Pelanggan", {"nama": nama}, {"sandi_hash": logic.hash_sandi(sandi_awal())})
    store.update_where("Permintaan", {"nama": nama, "status": "Menunggu"}, {"status": "Selesai"})
