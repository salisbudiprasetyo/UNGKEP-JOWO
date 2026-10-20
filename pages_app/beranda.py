from __future__ import annotations

import html
from datetime import date

import pandas as pd
import streamlit as st

import logic
import services

store = services.get_store()

# ikon admin: hanya tampil bila admin yang login
if services.is_admin():
    if st.button("", icon=":material/admin_panel_settings:", key="btn_admin", help="Halaman admin"):
        st.switch_page("pages_app/admin.py")

st.markdown('<h1 class="judul">UNGKEP JOWO</h1><p class="subjudul">REKAP PEMBELIAN</p>', unsafe_allow_html=True)


# ------------------------------------------------------------------ login
def tampil_login():
    tab_masuk, tab_daftar = st.tabs(["Masuk", "Daftar pelanggan"])
    with tab_masuk:
        nama_list = services.daftar_nama(store)
        with st.form("form_masuk"):
            nama = st.selectbox("Nama (ketik untuk mencari)", nama_list, index=None,
                                placeholder="Ketik nama, mis. “er”…")
            sandi = st.text_input("Sandi", type="password")
            kirim = st.form_submit_button("Masuk", type="primary", width="stretch")
        if kirim:
            if not nama:
                st.error("Pilih nama dulu.")
            elif (err := services.masuk(store, nama, sandi)):
                st.error(err)
            else:
                st.rerun()
        if st.button("Lupa sandi? Tanya admin", width="stretch"):
            st.session_state["_lupa_buka"] = True
        if st.session_state.get("_lupa_buka"):
            n2 = st.selectbox("Nama kamu", nama_list, index=None, placeholder="Pilih nama", key="lupa_nama_pilih")
            if st.button("Kirim permintaan ke admin", disabled=not n2, width="stretch"):
                services.tanya_admin(store, n2)
                st.session_state["_lupa_buka"] = False
                st.success("Permintaan terkirim. Hubungi admin; setelah dikonfirmasi, sandimu kembali ke sandi awal.")
    with tab_daftar:
        with st.form("form_daftar"):
            baru = st.text_input("Nama kamu", placeholder="mis. Budi QC")
            st.caption("Sandi awal sama dengan pelanggan lain (tanya admin). Bisa kamu ganti setelah masuk.")
            kirim = st.form_submit_button("Daftar", type="primary", width="stretch")
        if kirim:
            if (err := services.daftar_baru(store, baru)):
                st.error(err)
            else:
                st.success("Terdaftar! Silakan masuk di tab “Masuk” dengan sandi awal.")


# ------------------------------------------------------------------ data kasbon
def data_periode(start: date, end: date) -> pd.DataFrame:
    df = store.all("Kasbon")
    if df.empty:
        return df
    df = df[df["status_pesanan"] != "Batal"].copy()
    df["tgl"] = pd.to_datetime(df["tanggal"], errors="coerce").dt.date
    df["subtotal"] = pd.to_numeric(df["subtotal"], errors="coerce").fillna(0)
    return df[(df["tgl"] >= start) & (df["tgl"] <= end)]


def tabel_html(df: pd.DataFrame, nama_semua: list[str], hari: list[date], me: str | None) -> str:
    hari_ini = logic.today_wib()
    pivot = df.groupby(["pelanggan", "tgl"])["subtotal"].sum().to_dict() if not df.empty else {}
    lunas = {}
    if not df.empty:
        for p, g in df.groupby("pelanggan"):
            lunas[p] = bool((g["status_bayar"] == "Lunas").all())

    urut = sorted(nama_semua, key=lambda n: (n != me, n.lower()))
    # header bulan (colspan)
    bulan_runs: list[tuple[str, int]] = []
    for d in hari:
        lab = f"{logic.BULAN[d.month].upper()} {d.year}"
        if bulan_runs and bulan_runs[-1][0] == lab:
            bulan_runs[-1] = (lab, bulan_runs[-1][1] + 1)
        else:
            bulan_runs.append((lab, 1))
    h = ['<div class="rekap-wrap"><table class="rekap"><thead><tr><th class="nama" rowspan="2">NAMA</th>']
    for lab, n in bulan_runs:
        h.append(f'<th colspan="{n}" style="text-align:left"><span style="position:sticky;left:7.6rem;padding-left:.2rem">{lab}</span></th>')
    h.append('<th class="tot" rowspan="2">TOTAL</th></tr><tr>')
    for d in hari:
        h.append(f'<th class="{"hari-ini" if d == hari_ini else ""}">{d.day}</th>')
    h.append("</tr></thead><tbody>")
    for n in urut:
        mine = n == me
        h.append(f'<tr><td class="nama">{html.escape(n)}</td>')
        total = 0
        for d in hari:
            v = pivot.get((n, d), 0)
            total += v
            cls = ("me " if mine else "") + ("ada" if v else "kosong") + (" hari-ini" if d == hari_ini else "")
            h.append(f'<td class="{cls}">{f"{int(v):,}".replace(",", ".") if v else "·"}</td>')
        chip = ""
        if total:
            chip = ' <span class="chip-lunas">✓</span>' if lunas.get(n) else ""
        h.append(f'<td class="tot">{logic.rupiah(total) if total else "-"}{chip}</td></tr>')
    h.append("</tbody></table></div>")
    return "".join(h)


# ------------------------------------------------------------------ tampilan utama
me = services.user()
if not me:
    tampil_login()
    st.divider()

# pemilih periode
hari_ini = logic.today_wib()
p_start, _ = logic.periode_untuk(hari_ini)
opsi = [logic.geser_periode(p_start, -i) for i in range(0, 6)]
labels = [logic.label_periode(a, b) + (" (berjalan)" if i == 0 else "") for i, (a, b) in enumerate(opsi)]
pilih = st.selectbox("Periode", labels, index=0, label_visibility="collapsed")
start, end = opsi[labels.index(pilih)]
hari = logic.daftar_hari(start, end)

df = data_periode(start, end)

if me and not services.is_admin():
    total_saya = float(df.loc[df["pelanggan"] == me, "subtotal"].sum()) if not df.empty else 0.0
    st.markdown(
        f'<div class="kartu">Halo, <b>{html.escape(me)}</b><div class="besar">{logic.rupiah(total_saya)}</div>'
        f'<small>Kasbon periode ini · dibayar tgl {logic.CUTOFF_HARI} {logic.BULAN[end.month]} {end.year}</small></div>',
        unsafe_allow_html=True)

_akun = store.all("Pelanggan")
nama_semua = sorted(_akun[(_akun["aktif"] != "0") & (_akun["role"] != "admin")]["nama"].tolist(), key=str.lower)
cari = st.text_input("Cari nama", placeholder="Cari nama di tabel…", label_visibility="collapsed") if len(nama_semua) > 12 else ""
if cari:
    nama_semua = [n for n in nama_semua if cari.lower() in n.lower() or n == me]
st.markdown(tabel_html(df, nama_semua, hari, me), unsafe_allow_html=True)
st.caption("Angka = total belanja per hari (Rp). Geser tabel ke samping untuk melihat tanggal lain. ✓ = lunas.")

# ---- riwayat & pesan milik sendiri
if me and services.is_admin():
    if st.button("Keluar", width="stretch"):
        services.keluar()
        st.rerun()
elif me:
    st.subheader("Riwayat saya")
    mine = df[df["pelanggan"] == me] if not df.empty else df
    per_hari = mine.groupby("tgl")["subtotal"].sum().to_dict() if not mine.empty else {}
    menu_tersedia = store.all("MenuHarian")
    tgl_menu = {pd.to_datetime(t).date() for t in menu_tersedia["tanggal"] if t}
    kandidat = sorted(set(per_hari) | {d for d in tgl_menu if d in hari})
    if not kandidat:
        st.info("Belum ada pembelian di periode ini.")
    else:
        label = {d: f"{d.day} {logic.BULAN[d.month][:3]} · " + (logic.rupiah(per_hari[d]) if d in per_hari else "PESAN")
                 for d in kandidat}
        pilihan = st.pills("Pilih tanggal", kandidat, format_func=lambda d: label[d], key="pill_tgl",
                           label_visibility="collapsed")
        if pilihan:
            if pilihan in per_hari:
                rows = mine[mine["tgl"] == pilihan]
                st.markdown(f"**{pilihan.day} {logic.BULAN[pilihan.month]} {pilihan.year}**")
                tbl = rows[["kategori", "item", "qty", "harga", "subtotal", "catatan"]].rename(columns={
                    "kategori": "Jenis", "item": "Item", "qty": "Jml", "harga": "Harga", "subtotal": "Subtotal", "catatan": "Catatan"})
                st.dataframe(tbl, hide_index=True, width="stretch")
                st.markdown(f"**Total: {logic.rupiah(per_hari[pilihan])}**")
                if logic.bisa_edit(pilihan):
                    st.info("Pesanan ini masih bisa diubah sampai pukul 10:15 WIB. (Fitur ubah/batal menyusul di tahap 3.)")
            else:
                st.info("Form pemesanan menyusul di tahap 3.")

    with st.expander("Akun saya"):
        with st.form("form_sandi", clear_on_submit=True):
            lama = st.text_input("Sandi lama", type="password")
            baru = st.text_input("Sandi baru", type="password")
            if st.form_submit_button("Ganti sandi", width="stretch"):
                if (err := services.ganti_sandi(store, me, lama, baru)):
                    st.error(err)
                else:
                    st.success("Sandi diganti.")
        if st.button("Keluar", width="stretch"):
            services.keluar()
            st.rerun()
