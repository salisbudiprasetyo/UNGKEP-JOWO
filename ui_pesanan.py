"""Komponen tampilan pesanan: form pesan (dialog), terima kasih, revisi admin, tabel Pesanan Hari Ini."""
from __future__ import annotations

import html
from datetime import date

import streamlit as st

import logic
import orders
import services
from orders import KATEGORI, KELOMPOK

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
KELAS = {"Dipesan": "s-baru", "Revisi": "s-rev", "Minta batal": "s-rev", "Disetujui": "s-ok", "Dibungkus": "s-pack"}


def label_tgl(d: date) -> str:
    return f"{HARI[d.weekday()]}, {d.day} {logic.BULAN[d.month][:3]}"


def _esc(x) -> str:
    return html.escape(str(x))


# ===================================================================== form pesan
@st.dialog("Pesan makanan")
def dialog_pesan(tgl_iso: str, nama: str, langsung: bool = False):
    store = services.get_store()
    tgl = date.fromisoformat(tgl_iso)
    menu = orders.menu_hari(store, tgl)
    lama = {i["item"]: i for i in orders.items_pesanan(store, tgl, nama)}
    ada = bool(lama)
    rev = orders.revisi_menunggu(store, tgl, nama)

    st.markdown(f"**{label_tgl(tgl)}** · atas nama **{_esc(nama)}**")
    if ada and not langsung:
        st.info("Mengubah pesanan perlu persetujuan admin. Sebelum disetujui, pesanan lama yang berlaku.")
    if rev:
        st.warning("Ada permintaan perubahan yang masih menunggu admin. Mengirim lagi akan menggantikannya.")

    sisa = orders.batas_stok(store, tgl, nama)
    pilihan: dict[str, int] = {}
    harga: dict[str, float] = {}
    for kat in KATEGORI:
        sub = menu[menu["kategori"] == kat]
        if sub.empty:
            continue
        st.markdown(f'<div class="kat">{kat}</div>', unsafe_allow_html=True)
        for r in sub.itertuples():
            cap = sisa.get(r.nama)
            harga[r.nama] = lama[r.nama]["harga"] if r.nama in lama else float(r.harga)
            if cap is not None and cap == 0:
                alt = f" Coba: <b>{_esc(r.alternatif)}</b>." if r.alternatif else ""
                st.markdown(f'<div class="habis"><b>{_esc(r.nama)}</b> sedang habis.{alt}</div>', unsafe_allow_html=True)
                pilihan[r.nama] = 0
                continue
            ada_qty = lama[r.nama]["qty"] if r.nama in lama else 0
            maks = max(5, ada_qty) if cap is None else cap
            opsi = list(range(0, maks + 1))
            label = f"{r.nama} · {logic.rupiah(harga[r.nama])}" + (f"  (sisa {cap})" if cap is not None else "")
            q = st.segmented_control(label, opsi, default=min(ada_qty, maks), selection_mode="single",
                                     format_func=lambda n: "–" if n == 0 else str(n), width="stretch",
                                     key=f"q_{tgl_iso}_{nama}_{r.nama}")
            pilihan[r.nama] = int(q or 0)

    catatan = st.text_input("Catatan (opsional)", value=orders.catatan_pesanan(store, tgl, nama),
                            placeholder="mis. sambal dipisah, nasi sedikit", key=f"cat_{tgl_iso}_{nama}")
    total = sum(q * harga[n] for n, q in pilihan.items())

    with st.container(key="bar_total"):
        st.markdown(f'<div class="total-bar"><span>Total</span><b>{logic.rupiah(total)}</b></div>', unsafe_allow_html=True)
        if st.session_state.get("_konfirm_batal"):
            st.warning("Yakin batalkan seluruh pesanan ini?")
            if st.button("Ya, batalkan pesanan", type="primary", width="stretch"):
                err = orders.batalkan_pesanan(store, tgl, nama, langsung=langsung)
                st.session_state.pop("_konfirm_batal", None)
                if err:
                    st.error(err)
                else:
                    st.session_state["_sukses"] = {"kind": "batal-langsung" if langsung else "batal", "tgl": tgl_iso, "total": 0}
                    st.rerun()
            if st.button("Tidak jadi", width="stretch"):
                st.session_state.pop("_konfirm_batal", None)
                st.rerun(scope="fragment")
        else:
            label = ("Simpan perubahan" if langsung else "Kirim revisi") if ada else "Pesan sekarang"
            if st.button(label, type="primary", width="stretch", disabled=total <= 0):
                err, kind = orders.simpan_pesanan(store, tgl, nama, pilihan, catatan.strip(), langsung=langsung)
                if err:
                    st.error(err)
                else:
                    st.session_state["_sukses"] = {"kind": kind, "tgl": tgl_iso, "total": total}
                    st.rerun()
            if ada and st.button("Batalkan pesanan", width="stretch"):
                st.session_state["_konfirm_batal"] = True
                st.rerun(scope="fragment")


@st.dialog("Terima kasih 🙏")
def dialog_sukses(info: dict):
    tgl = date.fromisoformat(info["tgl"])
    kind = info["kind"]
    if kind == "baru":
        st.markdown(f"### Terima kasih atas pembeliannya!")
        st.markdown(f"Pesanan **{label_tgl(tgl)}** sebesar **{logic.rupiah(info['total'])}** sudah tercatat sebagai kasbon.")
        st.caption("Masih bisa diubah atau dibatalkan sampai pukul 10:15 WIB hari itu.")
    elif kind == "revisi":
        st.markdown("### Perubahan terkirim")
        st.markdown("Admin akan mengecek. Sampai disetujui, **pesanan lama** yang berlaku dan tertagih.")
    elif kind == "batal":
        st.markdown("### Permintaan batal terkirim")
        st.markdown("Pesanan baru benar-benar batal setelah admin mengonfirmasi.")
    elif kind == "batal-langsung":
        st.markdown("### Pesanan dibatalkan")
    else:
        st.markdown("### Tersimpan")
    if st.button("Tutup", type="primary", width="stretch"):
        st.rerun()


# ===================================================================== revisi (admin)
def _tabel_mini(items: list[dict]) -> str:
    if not items:
        return '<div class="kosong-info">— kosong (dibatalkan) —</div>'
    rows = "".join(f"<tr><td>{_esc(i['item'])}</td><td>{i['qty']}</td></tr>" for i in items)
    return f'<table class="mini"><tr><th>Item</th><th>Jml</th></tr>{rows}</table>'


@st.dialog("Perubahan pesanan")
def dialog_revisi(tgl_iso: str, nama: str):
    store = services.get_store()
    tgl = date.fromisoformat(tgl_iso)
    rev = orders.revisi_menunggu(store, tgl, nama)
    if not rev:
        st.info("Tidak ada perubahan yang menunggu.")
        if st.button("Tutup", width="stretch"):
            st.rerun()
        return
    lama = orders.items_pesanan(store, tgl, nama)
    st.markdown(f"**{_esc(nama)}** · {label_tgl(tgl)}")
    diff = "".join(
        f'<span class="diff {"tambah" if s == "+" else "kurang"}">{s}{n} {_esc(i)}</span>'
        for s, i, n in orders.selisih(lama, rev["items"]) if s != "=")
    st.markdown(f"**Yang berubah:** {diff or '—'}", unsafe_allow_html=True)
    st.markdown("**Pesanan lama**")
    st.markdown(_tabel_mini(lama), unsafe_allow_html=True)
    st.markdown("**Pesanan baru**")
    st.markdown(_tabel_mini(rev["items"]), unsafe_allow_html=True)
    if rev["catatan"]:
        st.caption(f"Catatan baru: {rev['catatan']}")
    if st.button("Konfirmasi", type="primary", width="stretch"):
        orders.konfirmasi_revisi(store, tgl, nama)
        st.rerun()
    if st.button("Tolak (tetap pesanan lama)", width="stretch"):
        orders.tolak_revisi(store, tgl, nama)
        st.rerun()


# ===================================================================== tabel Pesanan Hari Ini
def _kartu_html(o: dict, no: int, me: str | None) -> str:
    kelas = KELAS.get(o["status"], "s-baru")
    utama = o["utama"] or o["ekstra"]
    ekstra = o["ekstra"] if o["utama"] else ""
    jml = f'×{o["jumlah"]}' if o["seragam"] else ""
    info = ""
    if o["revisi"]:
        info = ('<div class="info">Minta dibatalkan · menunggu admin</div>' if o["revisi"]["jenis"] == "batal"
                else '<div class="info">Minta ubah pesanan · menunggu admin</div>')
    aku = " me" if o["nama"] == me else ""
    return (f'<div class="psn {kelas}{aku}"><div class="r1"><span class="no">{no}.</span>'
            f'<span class="nm">{_esc(o["nama"]).upper()}</span><span class="jml">{jml}</span>'
            f'<span class="chip {kelas}">{_esc(o["status"]).upper()}</span></div>'
            f'<div class="isi">{_esc(utama)}</div>'
            + (f'<div class="ekstra">{_esc(ekstra)}</div>' if ekstra else "")
            + (f'<div class="cat">📝 {_esc(o["catatan"])}</div>' if o["catatan"] else "")
            + info + "</div>")


def _rekap_html(orders_: list[dict]) -> str:
    if not orders_:
        return ""
    chips = "".join(f"<span>{_esc(n)} <b>{q}</b></span>" for n, q in orders.rekap(orders_).items())
    return f'<div class="rk">{chips}</div>'


def _rekap_akhir_html(semua: list[dict], admin: bool) -> str:
    paket = ayam_saja = nasi_saja = 0
    for o in semua:
        q = {"Nasi": 0, "Ayam Sayur": 0}
        for i in o["items"]:
            if i["kategori"] in q:
                q[i["kategori"]] += i["qty"]
        p = min(q["Nasi"], q["Ayam Sayur"])
        paket += p
        ayam_saja += q["Ayam Sayur"] - p
        nasi_saja += q["Nasi"] - p
    rek = orders.rekap(semua)
    per_kat: dict[str, list[tuple[str, int]]] = {}
    kat_item = {i["item"]: i["kategori"] for o in semua for i in o["items"]}
    for nm, q in rek.items():
        per_kat.setdefault(kat_item[nm], []).append((nm, q))
    rows = ['<tr class="sec"><td colspan="2">PORSI</td></tr>',
            f"<tr><td>Nasi + Ayam sayur lengkap</td><td>{paket}</td></tr>",
            f"<tr><td>Ayam sayur lengkap (tanpa nasi)</td><td>{ayam_saja}</td></tr>"]
    if nasi_saja:
        rows.append(f"<tr><td>Nasi saja (tanpa ayam)</td><td>{nasi_saja}</td></tr>")
    for kat in KATEGORI:
        if kat in per_kat:
            rows.append(f'<tr class="sec"><td colspan="2">{kat.upper()}</td></tr>')
            rows += [f"<tr><td>{_esc(n)}</td><td>{q}</td></tr>" for n, q in per_kat[kat]]
    rows.append(f'<tr class="tot"><td>Pelanggan</td><td>{len(semua)} orang</td></tr>')
    if admin:
        rows.append(f'<tr class="tot"><td>Total tagihan</td><td>{logic.rupiah(sum(o["total"] for o in semua))}</td></tr>')
    return f'<div class="rk-akhir"><h4>REKAP TOTAL HARI INI</h4><table>{"".join(rows)}</table></div>'


def render_hari_ini(store, tgl: date, me: str | None, admin: bool):
    semua = orders.daftar_pesanan(store, tgl)
    tahun = f"{tgl.day} {logic.BULAN[tgl.month]} {tgl.year}"
    st.markdown(f'<div class="judul-sec"><h3>PESANAN HARI INI</h3><span class="tg">{HARI[tgl.weekday()]}, {tahun}</span></div>',
                unsafe_allow_html=True)
    if not semua:
        st.markdown('<div class="kartu"><small>Belum ada yang memesan untuk menu ini.</small></div>', unsafe_allow_html=True)
        return
    for k in (1, 2, 3):
        grup = [o for o in semua if o["kelompok"] == k]
        st.markdown(f'<div class="grp-h">{k}. {KELOMPOK[k]}<span>{len(grup)} orang</span></div>', unsafe_allow_html=True)
        if not grup:
            st.markdown('<div class="kosong-info">Belum ada pesanan.</div>', unsafe_allow_html=True)
            continue
        for no, o in enumerate(grup, 1):
            if admin:
                with st.container():
                    st.markdown(_kartu_html(o, no, me), unsafe_allow_html=True)
                    _aksi_admin(store, tgl, o, f"{k}_{no}")
            else:
                st.markdown(_kartu_html(o, no, me), unsafe_allow_html=True)
                if me and o["nama"] == me and logic.bisa_edit(tgl):
                    if st.button("Ubah / batalkan pesanan saya", key=f"ubahku_{k}_{no}", width="stretch"):
                        dialog_pesan(tgl.isoformat(), me)
        st.markdown(_rekap_html(grup), unsafe_allow_html=True)
    st.markdown(_rekap_akhir_html(semua, admin), unsafe_allow_html=True)


def _aksi_admin(store, tgl: date, o: dict, kunci: str):
    nama = o["nama"]
    with st.container(key=f"aksi_{kunci}"):
        if o["revisi"]:
            c1, c2 = st.columns(2)
            if c1.button("Konfirmasi", key=f"kf_{kunci}", type="primary", width="stretch"):
                orders.konfirmasi_revisi(store, tgl, nama)
                st.rerun()
            if c2.button("Lihat pesanan sebelumnya", key=f"lh_{kunci}", width="stretch"):
                dialog_revisi(tgl.isoformat(), nama)
        else:
            c1, c2 = st.columns(2)
            bungkus = o["status"] == "Dibungkus"
            if c1.button("✓ Dibungkus" if bungkus else "Bungkus", key=f"bk_{kunci}", width="stretch",
                         type="secondary"):
                orders.set_dibungkus(store, tgl, nama, not bungkus)
                st.rerun()
            if c2.button("Ubah", key=f"ub_{kunci}", width="stretch"):
                dialog_pesan(tgl.isoformat(), nama, langsung=True)
