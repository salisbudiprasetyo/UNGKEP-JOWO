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


def tabel_html(df: pd.DataFrame, nama_semua: list[str], hari: list[date], me: str | None, admin: bool,
               bisa_pesan: set[date], ada_menu: set[date], rev: set[tuple[str, date]], kode: str) -> str:
    """Tabel kasbon. Sel yang boleh diklik diberi data-c (dibaca skrip kecil di bawah)."""
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
            boleh = mine or admin
            klik = boleh and bool(v or (d in ada_menu if admin else d in bisa_pesan))
            pending = (n, d) in rev
            cls = ("me " if mine else "") + ("ada" if v else "kosong") + (" hari-ini" if d == hari_ini else "") \
                + (" klik" if klik else "") + (" rev" if pending else "")
            if v:
                isi = ("⏳" if pending else "") + f"{int(v):,}".replace(",", ".")
            elif klik:
                isi = '<span class="pill-pesan">PESAN</span>'
            else:
                isi = "·"
            attr = f' data-c="d|{d.isoformat()}|{html.escape(n, quote=True)}"' if klik else ""
            h.append(f'<td class="{cls}"{attr}>{isi}</td>')
        chip = ' <span class="chip-lunas">✓</span>' if total and lunas.get(n) else ""
        tklik = (mine or admin) and total
        attr = f' data-c="t|{kode}|{html.escape(n, quote=True)}"' if tklik else ""
        h.append(f'<td class="tot{" klik" if tklik else ""}"{attr}>{logic.rupiah(total) if total else "-"}{chip}</td></tr>')
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
    if total_saya > 0 and st.button("Lihat tagihan / Bayar sekarang", key="btn_tagihan", width="stretch"):
        st.session_state["_open"] = ("tagihan", logic.kode_periode(start), me)

# tanggal yang masih bisa dipesan: menu sudah ada dan belum lewat batas jam
ada_menu = set(orders.tanggal_menu(store))
tgl_buka = [d for d in sorted(ada_menu) if d >= hari_ini and logic.bisa_edit(d)][:3]
kode = logic.kode_periode(start)
_rv = store.all("Revisi")
rev_set = {(r.pelanggan, pd.to_datetime(r.tanggal).date()) for r in _rv[_rv["status"] == "Menunggu"].itertuples()} if not _rv.empty else set()

_akun = store.all("Pelanggan")
nama_semua = sorted(_akun[(_akun["aktif"] != "0") & (_akun["role"] != "admin")]["nama"].tolist(), key=str.lower)
cari = st.text_input("Cari nama", placeholder="Cari nama di tabel…", label_visibility="collapsed") if len(nama_semua) > 12 else ""
if cari:
    nama_semua = [n for n in nama_semua if cari.lower() in n.lower() or n == me]

# kotak tersembunyi: skrip kecil mengisinya saat sel tabel diketuk (kuncinya berganti tiap dipakai)
n_klik = st.session_state.setdefault("_n_klik", 0)
klik = st.text_input("sel", key=f"cellsel_{n_klik}", label_visibility="collapsed")
if klik:
    st.session_state["_n_klik"] += 1
    jenis, a1, a2 = (klik.split("#")[0].split("|", 2) + ["", "", ""])[:3]
    if me and (a2 == me or admin) and jenis in ("d", "t"):
        if jenis == "t":
            st.session_state["_open"] = ("tagihan", a1, a2)
        else:
            tg = date.fromisoformat(a1)
            ada = bool(orders.items_pesanan(store, tg, a2))
            if admin:
                st.session_state["_open"] = ("rincian", a1, a2) if ada else ("pesan", a1, a2, True)
            elif ada and logic.bisa_edit(tg):
                st.session_state["_open"] = ("pesan", a1, a2, False)
            elif ada:
                st.session_state["_open"] = ("rincian", a1, a2)
            elif orders.bisa_pesan(store, tg):
                st.session_state["_open"] = ("pesan", a1, a2, False)

st.markdown(tabel_html(df, nama_semua, hari, me, admin, set(tgl_buka), ada_menu, rev_set, kode), unsafe_allow_html=True)
st.caption("Ketuk **PESAN** untuk memesan · ketuk angka untuk melihat rincian · ketuk TOTAL untuk tagihan · ⏳ menunggu admin · ✓ lunas")
_js = ("""<script>
(function(){
 var P=window.parent,D=P.document;
 if(!P.__ujKlik){
  var s=D.createElement('script');
  s.textContent="(function(){document.addEventListener('click',function(e){var td=e.target.closest&&e.target.closest('[data-c]');if(!td)return;"+
  "var b=document.querySelector('[class*=st-key-cellsel] input');if(!b)return;"+
  "var st=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;b.focus({preventScroll:true});"+
  "st.call(b,td.getAttribute('data-c')+'#'+Date.now());b.dispatchEvent(new Event('input',{bubbles:true}));b.blur();},true);})();";
  D.head.appendChild(s); P.__ujKlik=true;
 }
 var n=0,t=setInterval(function(){try{var w=D.querySelector('.rekap-wrap'),h=D.querySelector('th.hari-ini');
 if(w&&h){w.scrollLeft=Math.max(0,h.offsetLeft-215);clearInterval(t);}}catch(e){clearInterval(t);} if(++n>20)clearInterval(t);},150);
})();
</script>""")
if hasattr(st, "iframe"):          # components.html dihapus di Streamlit baru
    st.iframe(_js, height=1)
else:
    components.html(_js, height=0)

# buka jendela yang diminta (dari ketukan sel atau dari tombol di dalam jendela lain)
if (spec := st.session_state.pop("_open", None)) and me:
    jenis = spec[0]
    if jenis == "pesan":
        ui.dialog_pesan(spec[1], spec[2], langsung=bool(spec[3]) and admin)
    elif jenis == "rincian":
        ui.dialog_rincian(spec[1], spec[2], admin=admin)
    elif jenis == "tagihan":
        ui.dialog_tagihan(spec[1], spec[2], admin=admin)
    elif jenis == "bayar" and (spec[2] == me and not admin):
        ui.dialog_bayar(spec[1], spec[2])

# ---- cadangan: tombol biasa bila sel tabel tidak merespons di perangkatmu
if me and not admin and tgl_buka:
    with st.expander("Tombol cadangan"):
        for d in tgl_buka:
            ada = bool(orders.items_pesanan(store, d, me))
            if st.button(("Lihat / ubah pesanan " if ada else "PESAN ") + ui.label_tgl(d), key=f"pesan_{d}", width="stretch"):
                ui.dialog_pesan(d.isoformat(), me)
if me and not admin and not tgl_buka:
    st.markdown('<div class="kartu"><small>Menu berikutnya belum diunggah admin. Pemesanan terbuka setelah menu tersedia.</small></div>',
                unsafe_allow_html=True)

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

# ---- akun
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
