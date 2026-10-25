"""Meong, kucing maskot gembul: menyapa setelah login, berkeliaran dengan animasi halus, minta makan, dan bisa ditanya.
Pompom (abu-abu) menemani pelanggan; di halaman admin Oyen (oranye) ikut hadir. Gambar ada di static/, mesin animasi di assets/kucing.js."""
from __future__ import annotations

import json
import re
from pathlib import Path

import logic
import orders

_JS = Path(__file__).parent / "assets" / "kucing.js"
_META = Path(__file__).parent / "assets" / "pompom_meta.json"
_STAT = Path(__file__).parent / "static"


def css() -> str:
    return """
.uj-cat{position:fixed;left:0;top:0;z-index:90;pointer-events:none;perspective:720px;will-change:transform,opacity;user-select:none;-webkit-user-select:none;}
.uj-cat.sembunyi{display:none!important;}
.uj-cat .tilt{position:absolute;inset:0;transform-origin:50% 96%;transform-style:preserve-3d;will-change:transform;
 filter:drop-shadow(0 3px 2px rgba(90,45,20,.25));}
.uj-cat .spr{position:absolute;left:0;top:0;background-repeat:no-repeat;pointer-events:none;will-change:opacity;}
.uj-cat .bayang{position:absolute;left:50%;bottom:0;width:78px;height:12px;border-radius:50%;transform:translateX(-50%);
 background:radial-gradient(ellipse at center,rgba(90,45,20,.38),rgba(90,45,20,0) 70%);pointer-events:none;}
.uj-cat .hit{position:absolute;left:50%;bottom:0;width:84px;height:92px;transform:translateX(-50%);pointer-events:auto;cursor:pointer;
 -webkit-tap-highlight-color:transparent;touch-action:manipulation;}
.uj-gelembung{position:fixed;z-index:95;max-width:220px;background:#FFFAF0;color:#4A2410;border:2px solid #F0CC9C;border-radius:16px;
 padding:.45rem .7rem;font:700 .8rem/1.3 'Nunito',system-ui,sans-serif;box-shadow:0 4px 0 rgba(224,160,90,.5),0 6px 14px rgba(120,60,20,.2);
 opacity:0;transform:translateY(-6px);transition:opacity .25s;pointer-events:none;left:0;top:0;min-width:96px;}
.uj-gelembung.tampil{opacity:1;}
.uj-gelembung.menu{pointer-events:auto;}
.uj-gelembung::after{content:"";position:absolute;left:var(--ekor,24px);top:-8px;width:12px;height:12px;background:#FFFAF0;border-left:2px solid #F0CC9C;border-top:2px solid #F0CC9C;transform:rotate(45deg);}
.uj-gelembung.atas::after{top:auto;bottom:-8px;border:0;border-right:2px solid #F0CC9C;border-bottom:2px solid #F0CC9C;}
.uj-gelembung .mkn{display:flex;gap:.3rem;margin-top:.4rem;flex-wrap:wrap}
.uj-gelembung .mkn button{font-size:1.25rem;line-height:1;border:2px solid #F0CC9C;background:#FFF1DB;border-radius:12px;padding:.25rem .4rem;cursor:pointer;transition:transform .12s}
.uj-gelembung .mkn button:active{transform:scale(.88)}
.uj-fx{position:fixed;z-index:96;pointer-events:none;left:0;top:0;will-change:transform,opacity;}
@media (prefers-reduced-motion:reduce){.uj-cat,.uj-gelembung{display:none}}
"""


def _url(nama: str) -> str:
    f = _STAT / nama
    return f"/app/static/{nama}?v={int(f.stat().st_mtime) if f.exists() else 0}"


def js(mode: str = "user", sapa: str = "", nama: str = "", kabar: str = "", lengkap: bool = True) -> str:
    """Skrip pemasang kucing (iframe kecil yang memasang kode ke jendela induk).
    lengkap=False: mesin sudah terpasang di sesi ini, cukup kirim mode/sapaan/kabar."""
    cfg = {"mode": mode, "sapa": sapa, "nama": nama, "kabar": kabar}
    if not lengkap:
        return ("<script>(function(P,C){var K=P.__ujKucing;if(K&&K.mode)K.mode(C.mode,C);})(window.parent,"
                + json.dumps(cfg, ensure_ascii=False) + ");</script>")
    cfg.update({"css": css(), "meta": json.loads(_META.read_text()), "urls": {"pompom": _url("pompom.webp"), "oyen": _url("oyen.webp")}})
    # kode dijalankan di jendela induk (bukan di iframe) supaya animasi tetap hidup walau iframe diganti saat halaman dimuat ulang
    kode = "(function(P,CFG){" + _JS.read_text() + "})(window,%s);" % json.dumps(cfg, ensure_ascii=False)
    muat = json.dumps(kode, ensure_ascii=False).replace("</", "<\\/")
    return ("<script>(function(P){var s=P.document.createElement('script');s.textContent=" + muat +
            ";P.document.head.appendChild(s);s.remove();})(window.parent);</script>")


FRASA = ["Sudah pesan hari ini? 🍗", "Pesan sebelum jam 10:45 ya!", "Kasbon dibayar tanggal 10 ya 😸",
         "Ketuk aku kalau mau tanya-tanya 🐾", "Es teh dulu, biar segar 🧋", "Ayam gepreknya kriuk lho! 😋"]


# ------------------------------------------------------------------ obrolan (tanya-jawab berbasis aturan)
SARAN = ["Menu hari ini", "Pesanan saya", "Tagihan saya", "Cara bayar", "Batas jam", "Cara pesan"]


def _rp(x: float) -> str:
    return logic.rupiah(x)


def _kata(t: str) -> str:
    return " " + re.sub(r"[^a-z0-9 ]+", " ", t.lower()) + " "


def _ada(t: str, *kunci: str) -> bool:
    return any(k in t for k in kunci)


def _menu(store) -> str:
    tgl = orders.tanggal_aktif(store)
    if not tgl:
        return "Menu berikutnya belum diunggah admin. Biasanya setelah jam 13:00 untuk besok. Sabar ya, meong 🐾"
    m = orders.menu_hari(store, tgl)
    if m.empty:
        return "Menu hari ini masih kosong."
    baris = [f"**Menu {logic.tanggal_panjang(tgl)}**"]
    for kat in orders.KATEGORI:
        sub = m[m["kategori"] == kat]
        if sub.empty:
            continue
        isi = ", ".join(f"{r.nama} ({_rp(r.harga)})" for r in sub.itertuples())
        baris.append(f"- **{kat}**: {isi}")
    if orders.is_tutup(store, tgl):
        baris.append("\n🔒 Order hari ini sudah ditutup admin.")
    return "\n".join(baris)


def _pesanan_saya(store, nama: str | None) -> str:
    if not nama:
        return "Masuk dulu ya, supaya aku bisa lihat pesananmu 😺"
    tgl = orders.tanggal_aktif(store)
    if not tgl:
        return "Belum ada menu yang dibuka."
    its = orders.items_pesanan(store, tgl, nama)
    if not its:
        return f"Kamu belum memesan untuk {logic.tanggal_panjang(tgl)}. Ketuk tombol **PESAN** di tabel ya!"
    daftar = "\n".join(f"- {i['item']} ×{i['qty']} ({_rp(i['qty'] * i['harga'])})" for i in its)
    rev = orders.revisi_menunggu(store, tgl, nama)
    extra = "\n\n⏳ Ada perubahan yang menunggu konfirmasi admin." if rev else ""
    return f"**Pesananmu {logic.tanggal_panjang(tgl)}**\n{daftar}\n\nTotal **{_rp(sum(i['qty'] * i['harga'] for i in its))}**.{extra}"


def _tagihan(store, nama: str | None) -> str:
    if not nama:
        return "Masuk dulu ya, supaya aku bisa cek kasbonmu 😺"
    import payments
    a, b = logic.periode_untuk(logic.today_wib())
    t = payments.tagihan(store, nama, logic.kode_periode(a))
    if t["total"] <= 0:
        return "Periode ini kamu belum punya kasbon. Aman! 🎉"
    if t["lunas"]:
        return f"Semua kasbonmu periode {logic.label_periode(a, b)} sudah **lunas** ✅"
    return (f"Kasbonmu yang belum dibayar: **{_rp(t['sisa'])}** (total belanja {_rp(t['total'])}).\n"
            f"Jatuh tempo tanggal {logic.CUTOFF_HARI} {logic.BULAN[b.month]} {b.year}. Ketuk angka di kolom **TOTAL** untuk membayar.")


def _bayar() -> str:
    import ui_pesanan as ui
    r = ui.rekening()
    return (f"Cara bayar kasbon:\n1. Ketuk angka di kolom **TOTAL** (atau di tanggal tertentu) lalu **Bayar sekarang**.\n"
            f"2. Centang yang mau dibayar, transfer ke **{r['bank']} {r['nomor']}** a.n. **{r['nama']}**.\n"
            "3. Unggah foto bukti. Kalau nominalnya pas, langsung lunas otomatis; kalau beda, admin yang cek.")


def _libur(store) -> str:
    hari = logic.today_wib()
    lib = {t: k for t, k in orders.libur_map(store).items() if t >= hari}
    if not lib:
        return "Belum ada jadwal libur yang tercatat. Warung buka terus! 🍛"
    return "Jadwal libur: " + ", ".join(f"{logic.tanggal_pendek(t)}" + (f" ({k})" if k else "") for t, k in sorted(lib.items()))


def jawab(store, nama: str | None, teks: str) -> str:
    t = _kata(teks)
    if _ada(t, " menu ", " makan ", " masak ", " lauk "):
        return _menu(store)
    if _ada(t, " pesanan saya", " pesananku", " aku pesan", " saya pesan", " orderan"):
        return _pesanan_saya(store, nama)
    if _ada(t, " tagihan", " kasbon", " utang", " hutang", " sisa ", " berapa bayar", " total saya"):
        return _tagihan(store, nama)
    if _ada(t, " bayar", " transfer", " rekening", " bni ", " lunas"):
        return _bayar()
    if _ada(t, " jam ", " batas", " kapan ", " telat", " terlambat", " tutup"):
        return (f"Pesanan bisa dibuat atau diubah sampai **jam {logic.BATAS_TEKS} WIB** di hari yang sama, atau sampai admin menekan **Close order**. "
                f"Menu yang diunggah sebelum jam {logic.UNGGAH_BATAS_JAM}:00 berlaku hari itu, setelahnya untuk besok. Setelah lewat batas, perubahan harus lewat admin.")
    if _ada(t, " libur"):
        return _libur(store)
    if _ada(t, " teman", " temen", " kawan"):
        return "Mau memesankan temanmu? Buka bagian **Pesankan untuk teman** di bawah tabel, pilih namanya, lalu isi pesanannya. Tercatat \"dipesan oleh\" kamu ya 😸"
    if _ada(t, " ubah", " revisi", " ganti", " batal", " edit"):
        return ("Mengubah pesanan: ketuk angka pesananmu di tabel lalu **Ubah / batalkan pesanan** (sebelum "
                f"jam {logic.BATAS_TEKS}). Perubahan menunggu konfirmasi admin dan sel berwarna kuning ⏳.")
    if _ada(t, " cara pesan", " pesan ", " order ", " memesan", " mesen", " beli "):
        return ("Cara pesan: 1) Masuk dulu. 2) Ketuk tombol **PESAN** di tanggal yang aktif. 3) Isi nasi, lauk, minuman, lalu **Pesan sekarang**. "
                "Tombol PESAN aktif setelah admin mengunggah menu.")
    if _ada(t, " sandi", " password", " lupa", " login", " masuk "):
        return "Lupa sandi? Di halaman masuk ketuk **Lupa sandi? Tanya admin**, nanti admin mengembalikan sandimu ke sandi awal."
    if _ada(t, " terima kasih", " makasih", " thanks", " thx", " tengkyu"):
        return "Sama-sama! Meong~ 🧡"
    if _ada(t, " halo", " hai", " hi ", " pagi", " siang", " sore", " malam", " assalam"):
        return f"Halo{', ' + nama if nama else ''}! Aku **Meong**, penjaga warung 😺 Mau tanya apa?"
    if _ada(t, " siapa", " nama kamu", " kamu itu"):
        return "Aku **Meong**, kucing penjaga warung Ungkep Jowo. Aku bisa bantu soal menu, pesanan, kasbon, dan cara bayar 🐾"
    import tanya
    return tanya.teruskan(store, nama, teks)
