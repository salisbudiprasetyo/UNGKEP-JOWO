from __future__ import annotations

import html
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import logic
import orders
import services
import ui_pesanan as ui

store = services.get_store()

# ikon admin: hanya tampil bila admin yang login
if services.is_admin():
    if st.button("", icon=":material/admin_panel_settings:", key="btn_admin", help="Halaman admin"):
        st.switch_page("pages_app/admin.py")

st.markdown('<div class="hero"><h1>UNGKEP JOWO</h1><div class="sub">REKAP PEMBELIAN</div></div>', unsafe_allow_html=True)

# pop up terima kasih (setelah form pesan ditutup)
if (info := st.session_state.pop("_sukses", None)):
    ui.dialog_sukses(info)


# ------------------------------------------------------------------ login
def tampil_login():
    tab_masuk, tab_daftar = st.tabs(["Masuk", "Daftar pelanggan"])
    with tab_masuk:
        nama_list = services.daftar_nama(store)
        with st.form("form_masuk"):
            nama = st.selectbox("Nama (ketik untuk mencari)", nama_list, index=None, placeholder="Ketik nama, mis. “er”…")
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


def tabel_html(df: pd.DataFrame, nama_semua: list[str], hari: list[date], me: str | None, bisa_pesan: set[date]) -> str:
    hari_ini = logic.today_wib()
    pivot = df.groupby(["pelanggan", "tgl"])["subtotal"].sum().to_dict() if not df.empty else {}
    lunas = {}
    if not df.empty:
        for p, g in df.groupby("pelanggan"):
            lunas[p] = bool((g["status_bayar"] == "Lunas").all())

    urut = sorted(nama_semua, key=lambda n: (n != me, n.lower()))
    bulan_runs: list[tuple[str, int]] = []
    for d in hari:
        lab = f"{logic.BULAN[d.month].upper()} {d.year}"
        if bulan_runs and bulan_runs[-1][0] == lab:
            bulan_runs[-1] = (lab, bulan_runs[-1][1] + 1)
        else:
            bulan_runs.append((lab, 1))
    h = ['<div class="rekap-wrap"><table class="rekap"><thead><tr><th class="nama" rowspan="2">NAMA</th>']
    for lab, n in bulan_runs:
        h.append(f'<th colspan="{n}" style="text-align:left"><span style="position:sticky;left:7.6rem;display:inline-block;padding-left:.2rem">{lab}</span></th>')
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
            if v:
                isi = f"{int(v):,}".replace(",", ".")
            elif mine and d in bisa_pesan:
                isi = '<span class="pill-pesan">PESAN</span>'
            else:
                isi = "·"
            h.append(f'<td class="{cls}">{isi}</td>')
        chip = ' <span class="chip-lunas">✓</span>' if total and lunas.get(n) else ""
        h.append(f'<td class="tot">{logic.rupiah(total) if total else "-"}{chip}</td></tr>')
    h.append("</tbody></table></div>")
    return "".join(h)


# ------------------------------------------------------------------ tampilan utama
me = services.user()
admin = services.is_admin()
if not me:
    tampil_login()
    st.divider()

hari_ini = logic.today_wib()
p_start, _ = logic.periode_untuk(hari_ini)
opsi = [logic.geser_periode(p_start, -i) for i in range(0, 6)]
labels = [logic.label_periode(a, b) + (" (berjalan)" if i == 0 else "") for i, (a, b) in enumerate(opsi)]
pilih = st.selectbox("Periode", labels, index=0, label_visibility="collapsed")
start, end = opsi[labels.index(pilih)]
hari = logic.daftar_hari(start, end)
df = data_periode(start, end)

if me and not admin:
    total_saya = float(df.loc[df["pelanggan"] == me, "subtotal"].sum()) if not df.empty else 0.0
    st.markdown(
        f'<div class="kartu"><small>Halo, <b>{html.escape(me)}</b> · kasbon periode ini</small>'
        f'<div class="besar">{logic.rupiah(total_saya)}</div>'
        f'<small>Dibayar tanggal {logic.CUTOFF_HARI} {logic.BULAN[end.month]} {end.year}</small></div>', unsafe_allow_html=True)

# tanggal yang masih bisa dipesan: menu sudah ada dan belum lewat 10:15
tgl_buka = [d for d in orders.tanggal_menu(store) if d >= hari_ini and logic.bisa_edit(d)][:3]

_akun = store.all("Pelanggan")
nama_semua = sorted(_akun[(_akun["aktif"] != "0") & (_akun["role"] != "admin")]["nama"].tolist(), key=str.lower)
cari = st.text_input("Cari nama", placeholder="Cari nama di tabel…", label_visibility="collapsed") if len(nama_semua) > 12 else ""
if cari:
    nama_semua = [n for n in nama_semua if cari.lower() in n.lower() or n == me]
st.markdown(tabel_html(df, nama_semua, hari, me, set(tgl_buka) if me and not admin else set()), unsafe_allow_html=True)
st.caption("Angka = belanja per hari (Rp) · geser tabel untuk melihat tanggal lain · ✓ lunas")
# geser tabel otomatis ke tanggal hari ini (bila skrip diizinkan browser; kalau tidak, tabel tetap bisa digeser manual)
components.html("""<script>
(function(){var n=0,t=setInterval(function(){try{var d=window.parent.document,w=d.querySelector('.rekap-wrap'),h=d.querySelector('th.hari-ini');
if(w&&h){w.scrollLeft=Math.max(0,h.offsetLeft-215);clearInterval(t);}}catch(e){clearInterval(t);} if(++n>20)clearInterval(t);},150);})();
</script>""", height=0)

# ---- tombol pesan (pelanggan)
if me and not admin:
    if not tgl_buka:
        st.markdown('<div class="kartu"><small>Menu berikutnya belum diunggah admin. Pemesanan terbuka setelah menu tersedia.</small></div>',
                    unsafe_allow_html=True)
    for d in tgl_buka:
        mine = orders.items_pesanan(store, d, me)
        rev = orders.revisi_menunggu(store, d, me)
        if mine:
            tot = sum(i["qty"] * i["harga"] for i in mine)
            ket = f"Sudah dipesan · {logic.rupiah(tot)}" + (" · perubahan menunggu admin" if rev else "")
            st.markdown(f'<div class="aksi-card sudah"><div><div class="tgl">{ui.label_tgl(d)}</div><div class="ket">{ket}</div></div></div>',
                        unsafe_allow_html=True)
            if st.button("Lihat / ubah pesanan", key=f"pesan_{d}", width="stretch"):
                ui.dialog_pesan(d.isoformat(), me)
        else:
            st.markdown(f'<div class="aksi-card"><div><div class="tgl">{ui.label_tgl(d)}</div><div class="ket">Menu sudah tersedia · pesan sebelum 10:15</div></div></div>',
                        unsafe_allow_html=True)
            if st.button(f"PESAN {ui.label_tgl(d)}", key=f"pesan_{d}", type="primary", width="stretch"):
                ui.dialog_pesan(d.isoformat(), me)

# ---- Pesanan Hari Ini (semua orang bisa melihat; kontrol hanya untuk admin)
tgl_aktif = orders.tanggal_aktif(store)
if tgl_aktif:
    ui.render_hari_ini(store, tgl_aktif, me, admin)
    if admin:
        with st.expander("Tambah pesanan atas nama pelanggan"):
            n = st.selectbox("Pelanggan", nama_semua, index=None, placeholder="Ketik nama", key="admin_tambah_nama")
            if st.button("Buka form pesan", disabled=not n, width="stretch"):
                ui.dialog_pesan(tgl_aktif.isoformat(), n, langsung=True)
else:
    st.markdown('<div class="kartu"><small>Belum ada menu. Admin belum mengunggah menu.</small></div>', unsafe_allow_html=True)

# ---- riwayat & akun
if me and not admin:
    st.markdown("### Riwayat saya")
    mine_df = df[df["pelanggan"] == me] if not df.empty else df
    per_hari = mine_df.groupby("tgl")["subtotal"].sum().to_dict() if not mine_df.empty else {}
    if not per_hari:
        st.info("Belum ada pembelian di periode ini.")
    else:
        kandidat = sorted(per_hari)
        label = {d: f"{d.day} {logic.BULAN[d.month][:3]} · {logic.rupiah(per_hari[d])}" for d in kandidat}
        pilihan = st.pills("Pilih tanggal", kandidat, format_func=lambda d: label[d], key="pill_tgl", label_visibility="collapsed")
        if pilihan:
            rows = mine_df[mine_df["tgl"] == pilihan]
            st.markdown(f"**{ui.label_tgl(pilihan)}**")
            tbl = rows[["item", "qty", "harga", "subtotal", "catatan"]].rename(columns={
                "item": "Item", "qty": "Jml", "harga": "Harga", "subtotal": "Subtotal", "catatan": "Catatan"})
            st.dataframe(tbl, hide_index=True, width="stretch")
            st.markdown(f"**Total: {logic.rupiah(per_hari[pilihan])}**")

if me:
    with st.expander("Akun saya" if not admin else "Akun admin"):
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
