from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

import base64

import logic
import payments
import services

store = services.get_store()

if not services.is_admin():
    st.error("Halaman ini khusus admin.")
    if st.button("Kembali ke beranda", width="stretch"):
        st.switch_page("pages_app/beranda.py")
    st.stop()

if st.button("← Beranda", key="kembali"):
    st.switch_page("pages_app/beranda.py")
st.markdown('<div class="hero"><h1>ADMIN</h1><div class="sub">UNGKEP JOWO</div></div>', unsafe_allow_html=True)

KAT_MASTER = ["Nasi", "Lauk", "Lain-lain"]                 # menu master: makanan saja
KAT_MAKANAN = ["Nasi", "Ayam Sayur", "Lauk", "Lain-lain"]  # urutan tampil (Ayam Sayur = data lama)

tab_harian, tab_libur, tab_bayar, tab_master, tab_minuman, tab_sandi, tab_pelanggan, tab_awal = st.tabs(
    ["Menu harian", "Libur", "Pembayaran", "Menu master", "Minuman", "Sandi", "Pelanggan", "Data awal"])


def _angka(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- menu master
with tab_master:
    st.caption("Makanan saja: nasi, lauk, dan lain-lain (kerupuk). Harga bawaan bisa kamu ubah lagi tiap hari di tab Menu harian. "
               "Minuman diatur di tab Minuman.")
    master = store.all("Menu")
    master = master[master["kategori"] != "Minuman"] if not master.empty else master
    ed = pd.DataFrame({
        "kategori": master["kategori"].replace("", KAT_MASTER[0]) if not master.empty else pd.Series(dtype=str),
        "nama": master["nama"] if not master.empty else pd.Series(dtype=str),
        "harga": master["harga"].map(_angka) if not master.empty else pd.Series(dtype=float),
        "hpp": master["hpp"].map(_angka) if not master.empty else pd.Series(dtype=float),
        "aktif": (master["aktif"] != "0") if not master.empty else pd.Series(dtype=bool),
    })
    hasil = st.data_editor(
        ed, num_rows="dynamic", width="stretch", hide_index=True, key="ed_master",
        column_config={
            "kategori": st.column_config.SelectboxColumn("Jenis", options=KAT_MASTER + [k for k in sorted(set(ed["kategori"])) if k not in KAT_MASTER], required=True),
            "nama": st.column_config.TextColumn("Nama menu", required=True),
            "harga": st.column_config.NumberColumn("Harga jual", min_value=0, step=500, format="%d"),
            "hpp": st.column_config.NumberColumn("Modal (HPP)", min_value=0, step=500, format="%d"),
            "aktif": st.column_config.CheckboxColumn("Aktif"),
        })
    if st.button("Simpan menu master", type="primary", width="stretch"):
        rows, ada = [], set()
        for i, r in enumerate(hasil.dropna(subset=["nama"]).itertuples(), start=1):
            nm = str(r.nama).strip()
            if not nm or nm.lower() in ada:
                continue
            ada.add(nm.lower())
            rows.append({"id": f"m{i:03d}", "kategori": r.kategori or KAT_MASTER[0], "nama": nm,
                         "harga": int(_angka(r.harga)), "hpp": int(_angka(r.hpp)), "aktif": "1" if r.aktif else "0"})
        store.replace_all("Menu", rows)
        st.success(f"{len(rows)} menu tersimpan.")
        st.rerun()

# ---------------------------------------------------------------- menu harian
with tab_harian:
    master = store.all("Menu")
    master = master[master["aktif"] != "0"] if not master.empty else master
    if master.empty:
        st.info("Isi dulu daftar menu di tab “Menu master”.")
    else:
        besok = logic.today_wib() + timedelta(days=1)
        tgl = st.date_input("Tanggal menu", value=besok, format="DD/MM/YYYY")
        harian = store.all("MenuHarian")
        sudah = harian[harian["tanggal"] == tgl.isoformat()]
        if not sudah.empty:
            st.success(f"Menu {tgl.strftime('%d/%m/%Y')} sudah diunggah ({len(sudah)} item). Kamu bisa mengubahnya lagi.")
        else:
            terakhir = harian.sort_values("tanggal").tail(1)
            sudah = harian[harian["tanggal"] == terakhir.iloc[0]["tanggal"]] if not terakhir.empty else harian.iloc[0:0]
            if not sudah.empty:
                st.caption(f"Terisi otomatis dari menu {sudah.iloc[0]['tanggal']}. Ubah seperlunya lalu unggah.")
        terpilih = {r.nama: r for r in sudah.itertuples()}
        semua_nama = master["nama"].tolist()

        pilihan_harian = []
        for kat in KAT_MAKANAN:
            sub = master[master["kategori"] == kat]
            if sub.empty:
                continue
            st.markdown(f"**{kat.upper()}**")
            for m in sub.itertuples():
                t = terpilih.get(m.nama)
                k = f"{tgl.isoformat()}_{m.id}"
                with st.container(border=True):
                    pakai = st.toggle(m.nama, value=t is not None, key=f"hp_{k}")
                    if not pakai:
                        continue
                    harga = st.number_input("Harga hari ini (Rp)", min_value=0, step=500, key=f"hh_{k}",
                                            value=int(_angka(t.harga) if t else _angka(m.harga)))
                    batasi = st.toggle("Batasi stok", value=bool(t and _angka(t.batas_stok) == 1), key=f"hb_{k}")
                    stok, alt = 0, ""
                    if batasi:
                        stok = st.number_input("Jumlah stok", min_value=1, step=1, key=f"hs_{k}",
                                               value=max(1, int(_angka(t.stok, 10))) if t else 10)
                        pilih_alt = [""] + [n for n in semua_nama if n != m.nama]
                        awal = t.alternatif if t and t.alternatif in pilih_alt else ""
                        alt = st.selectbox("Pengganti bila habis (opsional)", pilih_alt, index=pilih_alt.index(awal),
                                           format_func=lambda x: x or "— tidak ada —", key=f"ha_{k}")
                    pilihan_harian.append({
                        "tanggal": tgl.isoformat(), "menu_id": m.id, "kategori": m.kategori, "nama": m.nama,
                        "harga": int(harga), "hpp": int(_angka(t.hpp) if t else _angka(m.hpp)),
                        "batas_stok": 1 if batasi else 0, "stok": int(stok) if batasi else "", "alternatif": alt})
        # minuman: otomatis semua yang dicentang "ready" di tab Minuman
        drinks = store.all("Minuman")
        drinks = drinks[drinks["ready"] == "1"] if not drinks.empty else drinks
        st.markdown("**MINUMAN READY**")
        if drinks.empty:
            st.warning("Belum ada minuman yang dicentang ready. Atur dulu di tab Minuman.")
        else:
            with st.container(border=True):
                st.caption(f"{len(drinks)} minuman ikut otomatis (ubah di tab Minuman):")
                st.write(" · ".join(f"{(r.nama + ' ' + r.varian).strip()} ({logic.rupiah(_angka(r.harga))})" for r in drinks.itertuples()))
            for r in drinks.itertuples():
                nm = (r.nama + " " + r.varian).strip()
                pilihan_harian.append({"tanggal": tgl.isoformat(), "menu_id": "", "kategori": "Minuman", "nama": nm,
                                       "harga": int(_angka(r.harga)), "hpp": int(_angka(r.hpp)),
                                       "batas_stok": 0, "stok": "", "alternatif": ""})
        st.caption(f"{len(pilihan_harian)} menu dipilih.")
        if st.button("Unggah menu", type="primary", width="stretch"):
            if not pilihan_harian:
                st.error("Pilih minimal satu menu.")
            else:
                store.replace_where("MenuHarian", "tanggal", tgl.isoformat(), pilihan_harian)
                st.success(f"Menu {tgl.strftime('%d/%m/%Y')} terunggah ({len(pilihan_harian)} item). "
                           "Tabel Pesanan Hari Ini di beranda ikut berganti.")

# ---------------------------------------------------------------- minuman
with tab_minuman:
    st.caption("Centang **Ready** untuk minuman/varian yang tersedia. Yang dicentang otomatis masuk menu harian. "
               "Tambah baris baru di bagian bawah tabel untuk varian lain.")
    dr = store.all("Minuman")
    tabel = pd.DataFrame({
        "ready": (dr["ready"] == "1") if not dr.empty else pd.Series(dtype=bool),
        "nama": dr["nama"] if not dr.empty else pd.Series(dtype=str),
        "varian": dr["varian"] if not dr.empty else pd.Series(dtype=str),
        "harga": dr["harga"].map(_angka) if not dr.empty else pd.Series(dtype=float),
        "hpp": dr["hpp"].map(_angka) if not dr.empty else pd.Series(dtype=float),
    })
    c1, c2 = st.columns(2)
    if c1.button("Semua ready", width="stretch") and not dr.empty:
        store.replace_all("Minuman", [{**r._asdict(), "ready": "1"} for r in dr.itertuples(index=False)])
        st.rerun()
    if c2.button("Kosongkan", width="stretch") and not dr.empty:
        store.replace_all("Minuman", [{**r._asdict(), "ready": "0"} for r in dr.itertuples(index=False)])
        st.rerun()
    hasil_m = st.data_editor(
        tabel, num_rows="dynamic", width="stretch", hide_index=True, key="ed_minuman",
        column_config={
            "ready": st.column_config.CheckboxColumn("Ready"),
            "nama": st.column_config.TextColumn("Minuman", required=True),
            "varian": st.column_config.TextColumn("Varian"),
            "harga": st.column_config.NumberColumn("Harga", min_value=0, step=500, format="%d"),
            "hpp": st.column_config.NumberColumn("Modal", min_value=0, step=500, format="%d"),
        })
    st.caption(f"{int(hasil_m['ready'].sum())} dari {len(hasil_m)} minuman ready.")
    if st.button("Simpan minuman", type="primary", width="stretch"):
        rows, ada = [], set()
        for r in hasil_m.dropna(subset=["nama"]).itertuples():
            nm, vr = str(r.nama).strip(), str(r.varian or "").strip()
            if not nm or (nm.lower(), vr.lower()) in ada:
                continue
            ada.add((nm.lower(), vr.lower()))
            rows.append({"nama": nm, "varian": vr, "harga": int(_angka(r.harga)), "hpp": int(_angka(r.hpp)),
                         "ready": "1" if r.ready else "0"})
        store.replace_all("Minuman", rows)
        st.success(f"{len(rows)} minuman tersimpan. Unggah ulang menu harian agar perubahan ikut masuk.")
        st.rerun()

# ---------------------------------------------------------------- data awal
with tab_awal:
    import data_awal
    ring = data_awal.ringkasan()
    st.markdown("**Muat data awal dari REKAP_PEMBELIAN.xlsx**")
    st.caption("Dipakai sekali di awal. Berisi daftar pelanggan, riwayat pesanan 20–21 Okt, menu master (nasi, lauk, kerupuk), "
               "daftar minuman, dan menu 20–22 Okt (22 Okt: Sate Komo + sayur bening).")
    with st.container(border=True):
        st.markdown(f"- **{ring['pelanggan']}** pelanggan (sandi awal)\n- **{ring['riwayat']}** pesanan riwayat, total **{logic.rupiah(ring['total'])}**\n"
                    f"- **{ring['menu']}** menu master dan **{ring['minuman']}** minuman")
    st.warning("Menu master, daftar minuman, dan **semua pesanan tanggal 20–21 Okt** yang ada sekarang akan **diganti**. "
               "Pelanggan yang sudah terdaftar tidak diubah. Menu 22 Okt hanya diisi bila belum kamu unggah. Aman dijalankan ulang.")
    ok = st.checkbox("Saya mengerti, lanjutkan")
    if st.button("Muat data awal", type="primary", disabled=not ok, width="stretch"):
        hasil = data_awal.muat(store, services.sandi_awal())
        st.session_state["_awal_ok"] = (f"Selesai: {hasil['pelanggan_baru']} pelanggan baru, {hasil['pesanan']} pesanan riwayat "
                                        f"({', '.join(hasil['tanggal'])}). Menu master, minuman, dan menu 20–22 Okt sudah terisi.")
        st.rerun()
    if (pesan_ok := st.session_state.pop("_awal_ok", None)):
        st.success(pesan_ok)

    st.divider()
    st.markdown("**Unggah rekap pesanan (Excel)**")
    st.caption("Format sama seperti REKAP_PEMBELIAN: sel A1 \"TANGGAL\", baris 2 berisi tanggal, lalu kolom NAMA dan PESANAN. "
               "Tanggal yang sudah ada di aplikasi **ditimpa seluruhnya** (tidak ditambah), jadi data tidak dobel.")
    import rekap_excel
    from datetime import date as _d
    _hari = logic.now_wib().date()
    c1, c2 = st.columns(2)
    _bln = c1.selectbox("Bulan", list(range(1, 13)), index=_hari.month - 1, key="xl_bln")
    _thn = c2.number_input("Tahun", 2024, 2100, _hari.year, key="xl_thn")
    _fx = st.file_uploader("Berkas Excel (.xlsx)", type=["xlsx"], key="xl_file")
    if _fx is not None:
        try:
            _data, _info = rekap_excel.baca(_fx.getvalue(), int(_bln), int(_thn))
        except Exception as e:
            st.error(f"Berkas tidak bisa dibaca: {e}")
            _data = None
        if _data:
            _rc0 = rekap_excel.rencana(store, _data)
            _akun = [n for n in store.all("Pelanggan")["nama"]]
            _menu = sorted(rekap_excel.katalog(store, max(_data)))
            peta_i, peta_n = {}, {}
            if _rc0["tak_dikenal"]:
                st.warning("Item berikut tidak dikenali. Pilih padanannya atau biarkan untuk dilewati.")
                for k, n in _rc0["tak_dikenal"].items():
                    v = st.selectbox(f"{k} ({n}x)", ["(lewati)"] + _menu, key=f"xl_i_{k}")
                    peta_i[k] = None if v == "(lewati)" else v
            if _rc0["nama_baru"]:
                st.info("Nama berikut belum punya akun. Pilih akun yang sudah ada, atau biarkan untuk dibuatkan akun baru.")
                for k, n in _rc0["nama_baru"].items():
                    v = st.selectbox(f"{k} ({n} baris)", ["(buat akun baru)"] + _akun, key=f"xl_n_{k}")
                    peta_n[k] = None if v == "(buat akun baru)" else v
            _rc = rekap_excel.rencana(store, _data, peta_i, peta_n)
            _rows = rekap_excel.ringkas(store, _rc)
            st.dataframe(pd.DataFrame([{"Tanggal": r["tanggal"].strftime("%d %b %Y"), "Pelanggan": r["pelanggan"],
                                        "Total": logic.rupiah(r["total"]),
                                        "Keterangan": (f"Sudah ada {r['ada_sekarang']} pesanan → akan ditimpa" if r["ada_sekarang"] else "Baru")}
                                       for r in _rows]), hide_index=True, width="stretch")
            _ok = st.checkbox("Saya mengerti, pesanan pada tanggal di atas akan diganti", key="xl_ok")
            if st.button("Impor & timpa", type="primary", disabled=not _ok, width="stretch", key="xl_go"):
                h = rekap_excel.impor(store, _rc, True, services.sandi_awal())
                st.session_state["_xl_ok"] = (f"Selesai: {h['pesanan']} pesanan pada {', '.join(h['tanggal'])}; {h['akun_baru']} akun baru.")
                st.rerun()
    if (_m := st.session_state.pop("_xl_ok", None)):
        st.success(_m)

# ---------------------------------------------------------------- sandi
with tab_sandi:
    minta = store.all("Permintaan")
    minta = minta[(minta["jenis"] == "reset_sandi") & (minta["status"] == "Menunggu")]
    st.subheader("Permintaan reset sandi")
    if minta.empty:
        st.caption("Tidak ada permintaan.")
    for r in minta.itertuples():
        c = st.container(border=True)
        c.markdown(f"**{r.nama}** · {r.waktu.replace('T', ' ')[:16]}")
        if c.button(f"Reset {r.nama} ke sandi awal", key=f"rs_{r.nama}_{r.waktu}", width="stretch"):
            services.reset_sandi(store, r.nama)
            st.rerun()
    st.subheader("Reset manual")
    nama_list = services.daftar_nama(store)
    n = st.selectbox("Pelanggan", nama_list, index=None, placeholder="Ketik nama")
    if st.button("Reset ke sandi awal", disabled=not n, width="stretch"):
        services.reset_sandi(store, n)
        st.success(f"Sandi {n} dikembalikan ke sandi awal.")
    st.caption("Sandi pelanggan disimpan terenkripsi (hash), jadi tidak bisa dibaca siapa pun, termasuk admin. "
               "Jika lupa, cukup di-reset ke sandi awal.")

# ---------------------------------------------------------------- pelanggan
with tab_pelanggan:
    df = store.all("Pelanggan")
    df = df[df["role"] != "admin"]
    st.metric("Jumlah pelanggan aktif", int((df["aktif"] != "0").sum()))
    st.subheader("Impor daftar pelanggan lama")
    st.caption("Tempel satu nama per baris (atau unggah CSV dengan kolom “nama”). Semua mendapat sandi awal.")
    teks = st.text_area("Daftar nama", height=140, placeholder="Budi QC\nErry QC\nErix Kama")
    file = st.file_uploader("…atau CSV", type=["csv"])
    nama_baru = [logic.bersih_nama(x) for x in teks.splitlines() if x.strip()]
    if file is not None:
        try:
            nama_baru += [logic.bersih_nama(str(x)) for x in pd.read_csv(file)["nama"].dropna()]
        except Exception:
            st.error("CSV harus punya kolom “nama”.")
    if st.button("Impor", disabled=not nama_baru, type="primary", width="stretch"):
        ada = {n.lower() for n in store.all("Pelanggan")["nama"]}
        tambah, lewati = [], 0
        for nm in dict.fromkeys(nama_baru):
            if nm.lower() in ada or len(nm) < 2:
                lewati += 1
                continue
            ada.add(nm.lower())
            tambah.append({"nama": nm, "sandi_hash": logic.hash_sandi(services.sandi_awal()), "role": "pelanggan",
                           "aktif": "1", "dibuat": logic.now_wib().isoformat(timespec="seconds")})
        store.append("Pelanggan", tambah)
        st.success(f"{len(tambah)} pelanggan diimpor, {lewati} dilewati (sudah ada).")
    st.subheader("Daftar")
    st.dataframe(df[["nama", "aktif", "dibuat"]], hide_index=True, width="stretch")


# ---------------------------------------------------------------- pembayaran kasbon
with tab_bayar:
    hari_ini = logic.today_wib()
    p0, _ = logic.periode_untuk(hari_ini)
    opsi = [logic.geser_periode(p0, -i) for i in range(0, 6)]
    lab = [logic.label_periode(a, b) + (" (berjalan)" if i == 0 else "") for i, (a, b) in enumerate(opsi)]
    pil = st.selectbox("Periode kasbon", lab, key="bayar_periode")
    mulai, akhir = opsi[lab.index(pil)]
    kode = logic.kode_periode(mulai)
    akun = store.all("Pelanggan")
    nama_pel = sorted(akun[(akun["role"] != "admin") & (akun["aktif"] != "0")]["nama"].tolist(), key=str.lower)
    baris = []
    for n in nama_pel:
        t = payments.tagihan(store, n, kode)
        if t["total"] > 0:
            baris.append({"Nama": n, "Total": t["total"], "Sisa": t["sisa"], "Status": payments.status_periode(store, n, kode)})
    total_semua = sum(b["Total"] for b in baris)
    total_sisa = sum(b["Sisa"] for b in baris)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total kasbon", logic.rupiah(total_semua))
    c2.metric("Sudah lunas", logic.rupiah(total_semua - total_sisa))
    c3.metric("Belum lunas", logic.rupiah(total_sisa))
    st.caption(f"Jatuh tempo {logic.CUTOFF_HARI} {logic.BULAN[akhir.month]} {akhir.year}. Pelanggan membayar lewat tombol “Bayar sekarang”; "
               "bila nominal sama dengan tagihan, otomatis lunas.")

    cek = payments.daftar(store, kode=kode)
    cek = cek[cek["status"] == payments.CEK]
    if not cek.empty:
        st.markdown("#### Perlu dicek")
        for p in cek.itertuples():
            with st.container(border=True):
                st.markdown((f"Pesanan {p.tanggal} · " if p.tanggal else "") + f"**{p.pelanggan}** transfer **{logic.rupiah(float(p.jumlah))}** · tagihan {logic.rupiah(float(p.tagihan))}")
                if p.bukti:
                    st.image(base64.b64decode(p.bukti), width=220)
                a, b = st.columns(2)
                if a.button("Konfirmasi lunas", key=f"kl_{p.id}", type="primary", width="stretch"):
                    payments.konfirmasi_lunas(store, p.pelanggan, kode, tgl=p.tanggal or None)
                    st.rerun()
                if b.button("Tolak", key=f"tl_{p.id}", width="stretch"):
                    payments.tolak_pembayaran(store, p.pelanggan, kode, tgl=p.tanggal or None)
                    st.rerun()

    st.markdown("#### Rekap per pelanggan")
    if baris:
        tbl = pd.DataFrame(baris)
        tbl["Total"] = tbl["Total"].map(logic.rupiah)
        tbl["Sisa"] = tbl["Sisa"].map(logic.rupiah)
        st.dataframe(tbl, hide_index=True, width="stretch")
    else:
        st.info("Belum ada kasbon pada periode ini.")

    st.markdown("#### Tandai lunas (tunai / lainnya)")
    belum = [b["Nama"] for b in baris if b["Sisa"] > 0]
    n_lunas = st.selectbox("Pelanggan", belum, index=None, placeholder="Pilih pelanggan yang belum lunas", key="bayar_pilih")
    if st.button("Konfirmasi lunas", disabled=not n_lunas, key="bayar_tunai", width="stretch"):
        payments.konfirmasi_lunas(store, n_lunas, kode)
        st.rerun()
    sudah = [b["Nama"] for b in baris if b["Sisa"] == 0]
    if sudah:
        n_batal = st.selectbox("Salah tandai? Pilih pelanggan", sudah, index=None, placeholder="Batalkan status lunas", key="bayar_batal")
        if st.button("Batalkan status lunas", disabled=not n_batal, key="bayar_batal_btn", width="stretch"):
            payments.batalkan_lunas(store, n_batal, kode)
            st.rerun()

    riwayat = payments.daftar(store, kode=kode)
    if not riwayat.empty:
        st.markdown("#### Riwayat pembayaran")
        r = riwayat.drop(columns=["bukti", "id", "periode"]).rename(columns={
            "waktu": "Waktu", "pelanggan": "Nama", "jumlah": "Dibayar", "tagihan": "Tagihan", "metode": "Metode",
            "status": "Status", "catatan": "Catatan"})
        st.dataframe(r.iloc[::-1], hide_index=True, width="stretch")


# ---------------------------------------------------------------- libur pemesanan
import orders

with tab_libur:
    st.caption("Pilih tanggal yang libur lalu konfirmasi. Di tanggal itu tombol PESAN tidak muncul dan kolomnya bertanda “libur”.")
    hari_ini_l = logic.today_wib()
    tgl_l = st.date_input("Tanggal libur", value=hari_ini_l, min_value=hari_ini_l, key="libur_tgl", format="DD/MM/YYYY")
    ket_l = st.text_input("Keterangan (opsional)", placeholder="mis. libur nasional, warung tutup", key="libur_ket")
    sudah_libur = orders.libur_map(store)
    if tgl_l in sudah_libur:
        st.info("Tanggal ini sudah libur.")
    elif st.button("Jadikan libur", type="primary", width="stretch", key="libur_btn"):
        st.session_state["_libur_konfirm"] = (tgl_l.isoformat(), ket_l.strip())
    pend = st.session_state.get("_libur_konfirm")
    if pend and pend[0] == tgl_l.isoformat() and tgl_l not in sudah_libur:
        n_psn = len(orders.pesanan_tgl(store, tgl_l)["pelanggan"].unique())
        st.warning(f"Yakin **{logic.tanggal_panjang(tgl_l)}** libur pemesanan?"
                   + (f" Sudah ada {n_psn} pelanggan yang memesan; pesanan mereka tidak dihapus otomatis." if n_psn else ""))
        c1, c2 = st.columns(2)
        if c1.button("Ya, libur", type="primary", width="stretch", key="libur_ya"):
            orders.set_libur(store, tgl_l, pend[1])
            st.session_state.pop("_libur_konfirm", None)
            st.rerun()
        if c2.button("Batal", width="stretch", key="libur_batal"):
            st.session_state.pop("_libur_konfirm", None)
            st.rerun()
    mendatang = {d: k for d, k in sudah_libur.items() if d >= hari_ini_l}
    st.markdown("#### Libur yang akan datang")
    if not mendatang:
        st.caption("Belum ada.")
    for d, k in sorted(mendatang.items()):
        with st.container(border=True):
            st.markdown(f"**{logic.tanggal_panjang(d)}**" + (f" · {k}" if k else ""))
            if st.button("Batalkan libur", key=f"hl_{d}", width="stretch"):
                orders.hapus_libur(store, d)
                st.rerun()
