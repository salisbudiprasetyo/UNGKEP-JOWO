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


# ===================================================================== form pesan (bentuk tabel)
GRUP = [("Lauk", "Lauk", ["Ayam Sayur", "Lauk"]), ("Minuman", "Minuman", ["Minuman"]), ("Lain-lain", "Lain-lain", ["Lain-lain"])]


def _hrg(n: float, aktif: bool = True) -> None:
    st.markdown(f'<div class="hrg">{logic.rupiah(n) if aktif and n else "—"}</div>', unsafe_allow_html=True)


@st.dialog("Pesan makanan")
def dialog_pesan(tgl_iso: str, nama: str, langsung: bool = False):
    store = services.get_store()
    tgl = date.fromisoformat(tgl_iso)
    menu = orders.menu_hari(store, tgl)
    lama = {i["item"]: i for i in orders.items_pesanan(store, tgl, nama)}
    ada = bool(lama)
    rev = orders.revisi_menunggu(store, tgl, nama)
    awal = {i["item"]: i for i in rev["items"]} if rev and rev["jenis"] == "ubah" else lama  # isian awal form

    st.markdown(f"**{label_tgl(tgl)}** · atas nama **{_esc(nama)}**")
    pengguna = services.user() or nama
    if pengguna != nama:
        st.caption(f"Kamu memesankan untuk {nama}. Tercatat dipesan oleh {pengguna}.")
    if ada and not langsung:
        st.info(f"Mengubah pesanan perlu persetujuan admin. Sebelum disetujui, pesanan lama yang berlaku. Batas ubah: {logic.BATAS_TEKS} WIB.")
    if rev:
        st.warning("Perubahan sebelumnya masih menunggu admin. Mengirim lagi akan menggantikannya.")

    sisa = orders.batas_stok(store, tgl, nama)
    k = f"{tgl_iso}_{nama}"
    pilihan: dict[str, int] = {}
    harga: dict[str, float] = {}
    habis: list[str] = []

    def info(r):
        harga[r.nama] = lama[r.nama]["harga"] if r.nama in lama else float(r.harga)
        cap = sisa.get(r.nama)
        if cap is not None and cap == 0:
            habis.append(f"<b>{_esc(r.nama)}</b>" + (f" (coba: {_esc(r.alternatif)})" if r.alternatif else ""))
            return None
        return cap

    with st.container(key="tabel_psn"):
        h = st.columns([5.2, 3.1, 3.3], gap="small")
        h[0].markdown('<div class="th">Menu</div>', unsafe_allow_html=True)
        h[1].markdown('<div class="th c">Jumlah</div>', unsafe_allow_html=True)
        h[2].markdown('<div class="th r">Harga</div>', unsafe_allow_html=True)

        # --- Nasi: centang (otomatis tercentang untuk pesanan baru) + jumlah + harga
        nasi = menu[menu["kategori"] == "Nasi"]
        if not nasi.empty:
            r = next(nasi.itertuples())
            cap = info(r)
            c = st.columns([5.2, 3.1, 3.3], gap="small", vertical_alignment="center")
            pakai = c[0].checkbox(f"**{r.nama}**", value=(r.nama in awal) if ada else True, key=f"nasi_on_{k}")
            q = c[1].number_input("Jumlah nasi", 1, cap if cap else 99, int(awal[r.nama]["qty"]) if r.nama in awal else 1,
                                  key=f"nasi_q_{k}", disabled=not pakai, label_visibility="collapsed")
            if pakai:
                pilihan[r.nama] = int(q)
            with c[2]:
                _hrg(q * harga[r.nama], pakai)

        # --- Lauk / Minuman / Lain-lain: pilih menu (sejajar dengan Nasi) + jumlah + harga
        for judul, kunci, kats in GRUP:
            sub = menu[menu["kategori"].isin(kats)]
            if sub.empty:
                continue
            ada_item = [i for i in awal.values() if i["kategori"] in kats]
            nbaris = max(1, len(ada_item)) + st.session_state.get(f"ex_{kunci}_{k}", 0)
            tersedia = []
            for r in sub.itertuples():
                if info(r) is not None or sisa.get(r.nama) is None:
                    tersedia.append(r)
            nama_opsi = [r.nama for r in tersedia]
            st.markdown(f'<div class="kat">{judul}</div>', unsafe_allow_html=True)
            for b in range(nbaris):
                aw = ada_item[b] if b < len(ada_item) else None
                idx = nama_opsi.index(aw["item"]) if aw and aw["item"] in nama_opsi else None
                c = st.columns([5.2, 3.1, 3.3], gap="small", vertical_alignment="center")
                pil = c[0].selectbox(f"Pilih {judul.lower()}", nama_opsi, index=idx, placeholder=f"Pilih {judul.lower()}",
                                     key=f"sel_{kunci}_{b}_{k}", label_visibility="collapsed")
                cap = sisa.get(pil) if pil else None
                q = c[1].number_input(f"Jumlah {judul.lower()}", 1, cap if cap else 99, int(aw["qty"]) if aw else 1,
                                      key=f"qty_{kunci}_{b}_{k}", disabled=not pil, label_visibility="collapsed")
                if pil:
                    pilihan[pil] = pilihan.get(pil, 0) + int(q)
                with c[2]:
                    _hrg(q * harga[pil] if pil else 0, bool(pil))
            if st.button(f"＋ Tambah {judul.lower()}", key=f"tambah_{kunci}_{k}", type="tertiary"):
                st.session_state[f"ex_{kunci}_{k}"] = st.session_state.get(f"ex_{kunci}_{k}", 0) + 1
                st.rerun(scope="fragment")

    if habis:
        st.markdown('<div class="habis">Sedang habis: ' + ", ".join(habis) + "</div>", unsafe_allow_html=True)

    catatan = st.text_input("Catatan (opsional)", value=orders.catatan_pesanan(store, tgl, nama),
                            placeholder="mis. sambal dipisah, nasi sedikit", key=f"cat_{k}")
    total = sum(q * harga[n] for n, q in pilihan.items())

    with st.container(key="bar_total"):
        st.markdown(f'<div class="total-bar"><span>TOTAL PESANAN</span><b>{logic.rupiah(total)}</b></div>', unsafe_allow_html=True)
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
                err, kind = orders.simpan_pesanan(store, tgl, nama, pilihan, catatan.strip(), langsung=langsung, oleh=pengguna)
                if err:
                    st.error(err)
                else:
                    st.session_state["_sukses"] = {"kind": kind, "tgl": tgl_iso, "total": total}
                    st.rerun()
            if ada and st.button("Batalkan pesanan", width="stretch"):
                st.session_state["_konfirm_batal"] = True
                st.rerun(scope="fragment")


# ===================================================================== rincian pesanan (riwayat, hanya baca)
def _rincian_tabel(items: list[dict]) -> str:
    if not items:
        return '<div class="kosong-info">— kosong (dibatalkan) —</div>'
    rows = "".join(f"<tr><td>{_esc(i['item'])}</td><td class='c'>{i['qty']}</td><td>{logic.rupiah(i['harga'])}</td>"
                   f"<td>{logic.rupiah(i['qty'] * i['harga'])}</td></tr>" for i in items)
    tot = sum(i["qty"] * i["harga"] for i in items)
    return (f'<table class="mini rinci"><tr><th>Menu</th><th class="c">Jml</th><th>Harga</th><th>Total</th></tr>{rows}'
            f'<tr class="gt"><td colspan="3">TOTAL</td><td>{logic.rupiah(tot)}</td></tr></table>')


def _muat_ulang(iso: str, nama: str) -> None:
    """Segarkan seluruh halaman (tabel ikut berubah) lalu buka lagi rincian yang sama."""
    st.session_state["_open"] = ("rincian", iso, nama)
    st.rerun()


def _blok_bayar(store, tgl: date, nama: str, admin: bool) -> None:
    """Baris pembayaran tepat di bawah TOTAL: status + tombol (pelanggan: Bayar sekarang, admin: Konfirmasi lunas)."""
    import payments
    kode = logic.kode_periode(logic.periode_untuk(tgl)[0])
    iso = tgl.isoformat()
    t = payments.tagihan(store, nama, kode, iso)
    cek = payments.menunggu_cek(store, nama, kode, iso)
    if t["lunas"]:
        stat, kls = "✓ LUNAS", "ok"
    elif not cek.empty:
        stat, kls = "⏳ MENUNGGU CEK ADMIN", "cek"
    else:
        stat, kls = "BELUM DIBAYAR", "belum"
    with st.container(key="bar_bayar"):
        c = st.columns([1.15, 1], gap="small", vertical_alignment="center")
        c[0].markdown(f'<div class="bayar-stat {kls}"><small>Pembayaran</small><b>{stat}</b></div>', unsafe_allow_html=True)
        if admin:
            if t["lunas"]:
                if c[1].button("Batalkan lunas", key=f"bl_{iso}_{nama}", width="stretch"):
                    payments.batalkan_lunas(store, nama, kode, iso)
                    _muat_ulang(iso, nama)
            elif c[1].button("Konfirmasi lunas", key=f"kl_{iso}_{nama}", type="primary", width="stretch"):
                payments.konfirmasi_lunas(store, nama, kode, tgl=iso)
                _muat_ulang(iso, nama)
        elif not t["lunas"] and cek.empty and nama == services.user():
            if c[1].button("Bayar sekarang", key=f"by_{iso}_{nama}", type="primary", width="stretch"):
                st.session_state["_open"] = ("bayar", kode, nama, iso)
                st.rerun()
    if admin:
        for p in cek.itertuples():
            st.warning(f"Bukti transfer {logic.rupiah(float(p.jumlah))} dari pelanggan, tagihan {logic.rupiah(float(p.tagihan))}.")
            _bukti_img(p.bukti)
            if st.button("Tolak bukti transfer", key=f"tb_{iso}_{nama}", width="stretch"):
                payments.tolak_pembayaran(store, nama, kode, iso)
                _muat_ulang(iso, nama)


@st.dialog("Rincian pesanan")
def dialog_rincian(tgl_iso: str, nama: str, admin: bool = False):
    store = services.get_store()
    tgl = date.fromisoformat(tgl_iso)
    items = orders.items_pesanan(store, tgl, nama)
    rev = orders.revisi_menunggu(store, tgl, nama)
    st.markdown(f"**{label_tgl(tgl)} {tgl.year}** · **{_esc(nama)}**")
    if not items:
        st.info("Tidak ada pesanan pada tanggal ini.")
    else:
        st.markdown(_rincian_tabel(items), unsafe_allow_html=True)
        oleh = orders.pemesan(store, tgl, nama)
        if oleh and oleh != nama:
            st.caption(f"🧾 Dipesan oleh {oleh}")
        cat = orders.catatan_pesanan(store, tgl, nama)
        if cat:
            st.caption(f"📝 {cat}")
    if items:
        _blok_bayar(store, tgl, nama, admin)
    if rev:
        st.markdown('<div class="psn s-rev"><b>Menunggu konfirmasi admin</b> — perubahan yang diajukan:</div>', unsafe_allow_html=True)
        st.markdown(_rincian_tabel(rev["items"]) if rev["jenis"] != "batal" else '<div class="kosong-info">Permintaan batal pesanan</div>',
                    unsafe_allow_html=True)
        if admin:
            c1, c2 = st.columns(2)
            if c1.button("Konfirmasi", type="primary", width="stretch"):
                orders.konfirmasi_revisi(store, tgl, nama)
                st.rerun()
            if c2.button("Tolak", width="stretch"):
                orders.tolak_revisi(store, tgl, nama)
                st.rerun()
    if admin:
        if st.button("Ubah pesanan (admin)" if items else "Buat pesanan", width="stretch"):
            st.session_state["_open"] = ("pesan", tgl_iso, nama, True)
            st.rerun()
    elif items and logic.bisa_edit(tgl):
        if st.button("Ubah / batalkan pesanan", type="primary", width="stretch"):
            st.session_state["_open"] = ("pesan", tgl_iso, nama, False)
            st.rerun()
    elif items:
        st.caption(f"🔒 Sudah lewat batas {logic.BATAS_TEKS} WIB, pesanan ini tidak bisa diubah lagi.")


# ===================================================================== tagihan & pembayaran
def rekening() -> dict:
    return {"bank": services.secret("rekening_bank", "BNI"), "nomor": services.secret("rekening_nomor", "0258578828"),
            "nama": services.secret("rekening_nama", "NUR HABIBAH")}


def _bukti_img(b64: str) -> None:
    import base64
    if b64:
        st.image(base64.b64decode(b64), width=220)


@st.dialog("Tagihan kasbon")
def dialog_tagihan(kode: str, nama: str, admin: bool = False):
    import payments
    store = services.get_store()
    th, bl = (int(x) for x in kode.split("-"))
    start = date(th, bl, logic.CUTOFF_HARI + 1)
    a, b = logic.periode_untuk(start)
    t = payments.tagihan(store, nama, kode)
    st.markdown(f"**{_esc(nama)}** · periode {logic.label_periode(a, b)}")
    if not t["per_hari"]:
        st.info("Belum ada pembelian pada periode ini.")
        return
    rows = "".join(f"<tr><td>{label_tgl(date.fromisoformat(d))}</td><td>{logic.rupiah(v['total'])}{' ✓' if v['lunas'] else ''}</td></tr>"
                   for d, v in t["per_hari"].items())
    st.markdown(f'<table class="mini rinci"><tr><th>Tanggal</th><th>Total</th></tr>{rows}'
                f'<tr class="gt"><td>TOTAL KASBON</td><td>{logic.rupiah(t["total"])}</td></tr></table>', unsafe_allow_html=True)
    stat = payments.status_periode(store, nama, kode)
    if t["lunas"]:
        st.success("✓ LUNAS")
    else:
        st.markdown(f'<div class="kartu"><small>Belum dibayar</small><div class="besar">{logic.rupiah(t["sisa"])}</div>'
                    f'<small>Jatuh tempo {logic.CUTOFF_HARI} {logic.BULAN[b.month]} {b.year} · status: {stat}</small></div>', unsafe_allow_html=True)
    cek = payments.menunggu_cek(store, nama, kode)
    for p in cek.itertuples():
        st.warning(f"Bukti transfer {logic.rupiah(float(p.jumlah))} menunggu dicek admin.")
        if admin:
            _bukti_img(p.bukti)
    if admin:
        if not t["lunas"]:
            if st.button("Konfirmasi lunas", type="primary", width="stretch"):
                payments.konfirmasi_lunas(store, nama, kode)
                st.rerun()
            if not cek.empty and st.button("Tolak bukti transfer", width="stretch"):
                payments.tolak_pembayaran(store, nama, kode)
                st.rerun()
        elif st.button("Batalkan status lunas", width="stretch"):
            payments.batalkan_lunas(store, nama, kode)
            st.rerun()
    elif not t["lunas"]:
        if st.button("Bayar sekarang", type="primary", width="stretch"):
            st.session_state["_open"] = ("bayar", kode, nama)
            st.rerun()


@st.dialog("Bayar kasbon")
def dialog_bayar(kode: str, nama: str, tgl_iso: str | None = None):
    import payments
    from pathlib import Path
    store = services.get_store()
    t = payments.tagihan(store, nama, kode, tgl_iso)
    if t["sisa"] <= 0:
        st.success("Tidak ada tagihan yang tersisa. Terima kasih!")
        return
    rek = rekening()
    st.markdown(f'<div class="kartu"><small>Yang harus dibayar{" · pesanan " + label_tgl(date.fromisoformat(tgl_iso)) if tgl_iso else ""}</small><div class="besar">{logic.rupiah(t["sisa"])}</div></div>',
                unsafe_allow_html=True)
    st.markdown("**Transfer ke rekening:**")
    logo = Path(__file__).parent / "assets" / "bni.png"
    if logo.exists():
        import base64
        lg = f'<img class="bank-logo" src="data:image/png;base64,{base64.b64encode(logo.read_bytes()).decode()}">'
    else:
        lg = f'<span class="bank-badge">{_esc(rek["bank"])}</span>'
    st.markdown(f'<div class="bank-row">{lg}<span class="bank-nama">Bank {_esc(rek["bank"])}</span></div>', unsafe_allow_html=True)
    with st.container(key="rek"):
        st.code(rek["nomor"], language=None)  # ikon salin ada di pojok kanan kotak
    st.markdown(f'<div class="bank-an">a.n. <b>{_esc(rek["nama"])}</b></div>', unsafe_allow_html=True)
    st.divider()
    jumlah = st.number_input("Jumlah yang kamu transfer (Rp)", min_value=0, value=int(t["sisa"]), step=1000, key=f"bayar_jml_{kode}_{tgl_iso}")
    foto = st.file_uploader("Unggah foto bukti pembayaran", type=["jpg", "jpeg", "png", "webp"], key=f"bayar_foto_{kode}_{tgl_iso}")
    if foto:
        st.image(foto, width=200)
    st.caption("Jika jumlahnya sama dengan tagihan, kasbon langsung berstatus lunas. Jika berbeda, bukti tetap tersimpan dan dicek admin.")
    if st.button("Kirim bukti pembayaran", type="primary", width="stretch"):
        err, status = payments.kirim_pembayaran(store, nama, kode, float(jumlah), foto.getvalue() if foto else None, tgl_iso)
        if err:
            st.error(err)
        else:
            st.session_state["_sukses"] = {"kind": "bayar-oto" if status == payments.LUNAS_OTO else "bayar-cek",
                                           "tgl": logic.today_wib().isoformat(), "total": float(jumlah)}
            st.rerun()


@st.dialog("Terima kasih 🙏")
def dialog_sukses(info: dict):
    tgl = date.fromisoformat(info["tgl"])
    kind = info["kind"]
    if kind == "baru":
        st.markdown(f"### Terima kasih atas pembeliannya!")
        st.markdown(f"Pesanan **{label_tgl(tgl)}** sebesar **{logic.rupiah(info['total'])}** sudah tercatat sebagai kasbon.")
        st.caption(f"Masih bisa diubah atau dibatalkan sampai pukul {logic.BATAS_TEKS} WIB hari itu.")
    elif kind == "revisi":
        st.markdown("### Perubahan terkirim")
        st.markdown("Admin akan mengecek. Sampai disetujui, **pesanan lama** yang berlaku dan tertagih.")
    elif kind == "batal":
        st.markdown("### Permintaan batal terkirim")
        st.markdown("Pesanan baru benar-benar batal setelah admin mengonfirmasi.")
    elif kind == "bayar-oto":
        st.markdown("### Pembayaran diterima ✓")
        st.markdown(f"Nominal **{logic.rupiah(info['total'])}** sesuai tagihan. Kasbon periode ini berstatus **LUNAS**.")
    elif kind == "bayar-cek":
        st.markdown("### Bukti pembayaran tersimpan")
        st.markdown(f"Nominal **{logic.rupiah(info['total'])}** belum sama dengan tagihan, jadi admin akan mengeceknya dulu.")
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
            + (f'<div class="oleh">🧾 dipesan oleh {_esc(o["oleh"])}</div>' if o.get("oleh") else "")
            + info + "</div>")


def _rekap_html(orders_: list[dict]) -> str:
    if not orders_:
        return ""
    chips = "".join(f"<span>{_esc(n)} <b>{q}</b></span>" for n, q in orders.rekap(orders_).items())
    return f'<div class="rk">{chips}</div>'


def _rekap_akhir_html(semua: list[dict], admin: bool) -> str:
    paket = lauk_saja = nasi_saja = 0
    for o in semua:
        nasi = sum(i["qty"] for i in o["items"] if i["kategori"] == "Nasi")
        lauk = sum(i["qty"] for i in o["items"] if i["kategori"] in orders.LAUK)
        p = min(nasi, lauk)
        paket += p
        lauk_saja += lauk - p
        nasi_saja += nasi - p
    rek = orders.rekap(semua)
    per_kat: dict[str, list[tuple[str, int]]] = {}
    kat_item = {i["item"]: i["kategori"] for o in semua for i in o["items"]}
    for nm, q in rek.items():
        per_kat.setdefault(kat_item[nm], []).append((nm, q))
    rows = ['<tr class="sec"><td colspan="2">PORSI</td></tr>',
            f"<tr><td>Nasi + Lauk (paket)</td><td>{paket}</td></tr>",
            f"<tr><td>Lauk saja (tanpa nasi)</td><td>{lauk_saja}</td></tr>"]
    if nasi_saja:
        rows.append(f"<tr><td>Nasi saja (tanpa lauk)</td><td>{nasi_saja}</td></tr>")
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
