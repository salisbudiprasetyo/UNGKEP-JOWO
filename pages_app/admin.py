from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

import logic
import services

store = services.get_store()

if not services.is_admin():
    st.error("Halaman ini khusus admin.")
    if st.button("Kembali ke beranda", width="stretch"):
        st.switch_page("pages_app/beranda.py")
    st.stop()

if st.button("← Beranda", key="kembali"):
    st.switch_page("pages_app/beranda.py")
st.markdown('<h1 class="judul">ADMIN</h1><p class="subjudul">UNGKEP JOWO</p>', unsafe_allow_html=True)

KATEGORI = ["Nasi", "Ayam Sayur", "Lauk", "Minuman", "Lain-lain"]

tab_harian, tab_master, tab_sandi, tab_pelanggan = st.tabs(["Menu harian", "Menu master", "Sandi", "Pelanggan"])


def _angka(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- menu master
with tab_master:
    st.caption("Daftar semua menu beserta harga bawaan dan modal (HPP). Harga bisa kamu ubah lagi tiap hari di tab Menu harian.")
    master = store.all("Menu")
    ed = pd.DataFrame({
        "kategori": master["kategori"].replace("", KATEGORI[0]) if not master.empty else pd.Series(dtype=str),
        "nama": master["nama"] if not master.empty else pd.Series(dtype=str),
        "harga": master["harga"].map(_angka) if not master.empty else pd.Series(dtype=float),
        "hpp": master["hpp"].map(_angka) if not master.empty else pd.Series(dtype=float),
        "aktif": (master["aktif"] != "0") if not master.empty else pd.Series(dtype=bool),
    })
    hasil = st.data_editor(
        ed, num_rows="dynamic", width="stretch", hide_index=True, key="ed_master",
        column_config={
            "kategori": st.column_config.SelectboxColumn("Jenis", options=KATEGORI, required=True),
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
            rows.append({"id": f"m{i:03d}", "kategori": r.kategori or KATEGORI[0], "nama": nm,
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
            # isi awal: salin menu terakhir yang pernah diunggah, bila ada
            terakhir = harian.sort_values("tanggal").tail(1)
            sudah_ref = harian[harian["tanggal"] == terakhir.iloc[0]["tanggal"]] if not terakhir.empty else harian.iloc[0:0]
            if not sudah_ref.empty:
                st.caption(f"Terisi otomatis dari menu {sudah_ref.iloc[0]['tanggal']}. Ubah seperlunya lalu unggah.")
            sudah = sudah_ref

        terpilih = {r.nama: r for r in sudah.itertuples()}
        baris = []
        for m in master.itertuples():
            t = terpilih.get(m.nama)
            baris.append({
                "pakai": t is not None,
                "jenis": m.kategori,
                "nama": m.nama,
                "harga": _angka(t.harga) if t else _angka(m.harga),
                "hpp": _angka(t.hpp) if t else _angka(m.hpp),
                "batasi": bool(t and _angka(t.batas_stok) == 1),
                "stok": int(_angka(t.stok)) if t else 0,
                "alternatif": (t.alternatif if t else ""),
            })
        nama_opsi = [""] + master["nama"].tolist()
        st.caption("Centang menu yang tersedia. Harga boleh diubah khusus hari ini. Aktifkan “Batasi stok” bila jumlahnya terbatas, "
                   "lalu pilih menu pengganti kalau habis.")
        ed = st.data_editor(
            pd.DataFrame(baris), hide_index=True, width="stretch", key=f"ed_harian_{tgl}",
            disabled=["jenis", "nama", "hpp"],
            column_config={
                "pakai": st.column_config.CheckboxColumn("Ada"),
                "jenis": st.column_config.TextColumn("Jenis"),
                "nama": st.column_config.TextColumn("Menu"),
                "harga": st.column_config.NumberColumn("Harga", min_value=0, step=500, format="%d"),
                "hpp": st.column_config.NumberColumn("Modal", format="%d"),
                "batasi": st.column_config.CheckboxColumn("Batasi stok"),
                "stok": st.column_config.NumberColumn("Stok", min_value=0, step=1),
                "alternatif": st.column_config.SelectboxColumn("Pengganti bila habis", options=nama_opsi),
            })
        if st.button("Unggah menu", type="primary", width="stretch"):
            pilih = ed[ed["pakai"]]
            if pilih.empty:
                st.error("Pilih minimal satu menu.")
            else:
                id_by_name = dict(zip(master["nama"], master["id"]))
                rows = [{
                    "tanggal": tgl.isoformat(), "menu_id": id_by_name.get(r.nama, ""), "kategori": r.jenis,
                    "nama": r.nama, "harga": int(r.harga), "hpp": int(r.hpp),
                    "batas_stok": 1 if r.batasi else 0, "stok": int(r.stok) if r.batasi else "",
                    "alternatif": r.alternatif if r.batasi else "",
                } for r in pilih.itertuples()]
                store.replace_where("MenuHarian", "tanggal", tgl.isoformat(), rows)
                st.success(f"Menu {tgl.strftime('%d/%m/%Y')} terunggah ({len(rows)} item). Halaman pelanggan ikut berganti.")

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
