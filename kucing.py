"""Meong, kucing maskot gembul: menyapa setelah login, berkeliaran dengan animasi halus, minta makan, dan bisa ditanya.
Gambar dibuat sendiri (SVG berlapis gradasi) dan digerakkan skrip kerangka (assets/kucing.js), tanpa berkas gambar."""
from __future__ import annotations

import json
import re
from pathlib import Path

import logic
import orders

_JS = Path(__file__).parent / "assets" / "kucing.js"
OUT = "#7B5B5B"


def svg() -> str:
    """Kucing abu-abu belang yang gembul, duduk, tampak 3/4. Bagian-bagiannya bernama (k-*) agar bisa digerakkan satu per satu."""
    o = f'stroke="{OUT}" stroke-width="1.5" stroke-linejoin="round"'
    return f"""<svg class="uj-svg" viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<defs>
 <radialGradient id="kF" cx=".38" cy=".3" r=".85"><stop offset="0" stop-color="#F6F6F9"/><stop offset=".6" stop-color="#DCDCE3"/><stop offset="1" stop-color="#B9B9C6"/></radialGradient>
 <radialGradient id="kB" cx=".5" cy=".25" r=".9"><stop offset="0" stop-color="#F4F4F8"/><stop offset=".65" stop-color="#D9D9E1"/><stop offset="1" stop-color="#B5B5C3"/></radialGradient>
 <radialGradient id="kP" cx=".5" cy=".4" r=".7"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#E9E9F0"/></radialGradient>
 <radialGradient id="kE" cx=".5" cy=".62" r=".7"><stop offset="0" stop-color="#7FB2F2"/><stop offset=".55" stop-color="#3E67B8"/><stop offset="1" stop-color="#1B2447"/></radialGradient>
 <linearGradient id="kT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7DB0F0"/><stop offset="1" stop-color="#5588D4"/></linearGradient>
 <radialGradient id="kBell" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#B9BEC9"/></radialGradient>
</defs>
<ellipse class="k-shadow" cx="60" cy="134" rx="38" ry="5.5" fill="rgba(80,45,25,.22)"/>
<g class="k-tail"><path d="M88 118 C108 120 116 100 110 82" fill="none" stroke="{OUT}" stroke-width="16.5" stroke-linecap="round"/>
 <path d="M88 118 C108 120 116 100 110 82" fill="none" stroke="url(#kB)" stroke-width="13.5" stroke-linecap="round"/>
 <path d="M96 119 q4 -5 0 -11 M106 114 q4 -5 0 -11 M111 100 q4 -4 -1 -10" stroke="#A9A9B8" stroke-width="3.6" fill="none" stroke-linecap="round" opacity=".85"/>
 <g class="k-tail2"><path d="M110 82 C108 72 108 66 112 58" fill="none" stroke="{OUT}" stroke-width="15" stroke-linecap="round"/>
  <path d="M110 82 C108 72 108 66 112 58" fill="none" stroke="url(#kB)" stroke-width="12" stroke-linecap="round"/>
  <path d="M105 74 q5 -2 9 1 M106 65 q4 -2 8 0" stroke="#A9A9B8" stroke-width="3.2" fill="none" stroke-linecap="round" opacity=".85"/></g></g>
<g class="k-body">
 <path d="M26 114 C20 84 38 68 60 68 C82 68 100 84 94 114 C92 132 28 132 26 114 Z" fill="url(#kB)" {o}/>
 <ellipse cx="60" cy="108" rx="19" ry="22" fill="url(#kP)" opacity=".95"/>
 <path d="M30 92 q9 3 13 14 M28 104 q9 3 13 12 M90 92 q-9 3 -13 14 M92 104 q-9 3 -13 12" stroke="#A9A9B8" stroke-width="3.4" fill="none" stroke-linecap="round" opacity=".85"/>
 <ellipse cx="44" cy="82" rx="14" ry="8" fill="#fff" opacity=".28"/>
</g>
<g class="k-fl"><ellipse cx="36" cy="127" rx="13" ry="7.5" fill="url(#kP)" {o}/><path d="M32 125 v4 M37 124 v5 M42 125 v4" stroke="#C6C6D2" stroke-width="1" stroke-linecap="round"/></g>
<g class="k-fr"><ellipse cx="84" cy="127" rx="13" ry="7.5" fill="url(#kP)" {o}/><path d="M78 125 v4 M83 124 v5 M88 125 v4" stroke="#C6C6D2" stroke-width="1" stroke-linecap="round"/></g>
<g class="k-pl"><path d="M45 92 C38 98 38 116 42 124 C44 130 56 130 57 124 C58 114 56 98 53 92 Z" fill="url(#kP)" {o}/>
 <path d="M43 112 q5 2 10 0" stroke="#C6C6D2" stroke-width="1" fill="none"/><path d="M45 124 v4 M50 124 v4" stroke="#C6C6D2" stroke-width="1" stroke-linecap="round"/></g>
<g class="k-pr"><path d="M75 92 C82 98 82 116 78 124 C76 130 64 130 63 124 C62 114 64 98 67 92 Z" fill="url(#kP)" {o}/>
 <path d="M77 112 q-5 2 -10 0" stroke="#C6C6D2" stroke-width="1" fill="none"/><path d="M75 124 v4 M70 124 v4" stroke="#C6C6D2" stroke-width="1" stroke-linecap="round"/></g>
<g class="k-collar"><path d="M34 80 Q60 98 86 80" fill="none" stroke="{OUT}" stroke-width="8" stroke-linecap="round"/>
 <path d="M34 80 Q60 98 86 80" fill="none" stroke="url(#kT)" stroke-width="6" stroke-linecap="round"/>
 <path d="M40 84 q3 1 5 -1 M52 89 q3 1 5 0 M64 89 q3 0 5 -1 M75 85 q3 0 5 -2" stroke="#fff" stroke-width="1" fill="none" opacity=".6" stroke-linecap="round"/>
 <g class="k-bell"><path d="M60 92 v3" stroke="#8C8C98" stroke-width="2.4" stroke-linecap="round"/><circle cx="60" cy="100" r="5.6" fill="url(#kBell)" stroke="#8C8C98" stroke-width="1.2"/><path d="M56 101 h8" stroke="#8C8C98" stroke-width="1"/></g></g>
<g class="k-head">
 <g class="k-ears">
  <path d="M26 46 C20 26 24 10 30 8 C38 10 50 18 56 26 Z" fill="url(#kF)" {o}/><path d="M30 40 C27 28 29 18 32 15 C37 18 44 24 48 29 Z" fill="#F7B1BB"/>
  <path d="M94 46 C100 26 96 10 90 8 C82 10 70 18 64 26 Z" fill="url(#kF)" {o}/><path d="M90 40 C93 28 91 18 88 15 C83 18 76 24 72 29 Z" fill="#F7B1BB"/>
 </g>
 <path d="M60 18 C36 18 20 34 21 54 C22 76 40 84 60 84 C80 84 98 76 99 54 C100 34 84 18 60 18 Z" fill="url(#kF)" {o}/>
 <ellipse cx="26" cy="64" rx="8" ry="7" fill="url(#kF)"/><ellipse cx="94" cy="64" rx="8" ry="7" fill="url(#kF)"/>
 <path d="M60 20 v11 M50 21 q3 8 -1 14 M70 21 q-3 8 1 14 M31 44 q6 2 9 6 M89 44 q-6 2 -9 6" stroke="#A9A9B8" stroke-width="3.4" fill="none" stroke-linecap="round" opacity=".9"/>
 <ellipse cx="44" cy="34" rx="15" ry="8" fill="#fff" opacity=".32"/>
 <g class="k-face">
  <ellipse class="k-bl" cx="35" cy="66" rx="7.5" ry="4.6" fill="#FF9CA0" opacity=".25"/><ellipse class="k-br" cx="85" cy="66" rx="7.5" ry="4.6" fill="#FF9CA0" opacity=".25"/>
  <g class="k-eyes">
   <g class="k-eye"><ellipse cx="42" cy="54" rx="9.6" ry="11.6" fill="#1C2342" stroke="#141A33" stroke-width="1"/>
    <ellipse cx="42" cy="57" rx="7.6" ry="8.6" fill="url(#kE)"/><circle class="k-pup" cx="42" cy="55" r="3.6" fill="#0E1226"/>
    <circle cx="39" cy="50" r="3.4" fill="#fff"/><circle cx="46" cy="60" r="1.7" fill="#fff" opacity=".9"/></g>
   <g class="k-eye"><ellipse cx="78" cy="54" rx="9.6" ry="11.6" fill="#1C2342" stroke="#141A33" stroke-width="1"/>
    <ellipse cx="78" cy="57" rx="7.6" ry="8.6" fill="url(#kE)"/><circle class="k-pup" cx="78" cy="55" r="3.6" fill="#0E1226"/>
    <circle cx="75" cy="50" r="3.4" fill="#fff"/><circle cx="82" cy="60" r="1.7" fill="#fff" opacity=".9"/></g>
  </g>
  <g class="k-eyes-h"><path d="M32 57 q10 -13 20 0" fill="none" stroke="#2A2230" stroke-width="3.4" stroke-linecap="round"/><path d="M68 57 q10 -13 20 0" fill="none" stroke="#2A2230" stroke-width="3.4" stroke-linecap="round"/></g>
  <path d="M55.5 64 q4.5 -2.2 9 0 q-1 5.4 -4.5 6 q-3.5 -.6 -4.5 -6 Z" fill="#F29AAE" stroke="#C97A8C" stroke-width=".8"/>
  <g class="k-mt"><path d="M60 70 v2.5 M60 72.5 q-4 4.2 -8.5 1.6 M60 72.5 q4 4.2 8.5 1.6" fill="none" stroke="#8C6B6B" stroke-width="1.5" stroke-linecap="round"/></g>
  <path class="k-smile" d="M49 71 q11 14 22 0" fill="#8B2E3A" stroke="#8C6B6B" stroke-width="1.5" stroke-linejoin="round" opacity="0"/>
  <g class="k-mo"><path d="M51 72 q9 -2 18 0 q-1 13 -9 13 q-8 0 -9 -13 Z" fill="#8B2E3A" stroke="#6E2530" stroke-width="1.2"/><ellipse cx="60" cy="81" rx="5" ry="3" fill="#F28A9A"/></g>
  <path d="M22 62 l-14 -3 M22 66 l-14 3 M24 70 l-12 7 M98 62 l14 -3 M98 66 l14 3 M96 70 l12 7" stroke="#8E8EA0" stroke-width="1" stroke-linecap="round" opacity=".75"/>
 </g>
</g>
</svg>"""


def css() -> str:
    return """
#uj-kucing{position:fixed;left:0;top:0;width:84px;height:98px;z-index:90;cursor:pointer;user-select:none;-webkit-user-select:none;
 -webkit-tap-highlight-color:transparent;touch-action:manipulation;perspective:520px;will-change:transform;}
#uj-kucing.sembunyi{display:none;}
#uj-kucing .dalam{width:100%;height:100%;transform-style:preserve-3d;will-change:transform;filter:drop-shadow(0 5px 3px rgba(90,45,20,.22));}
#uj-kucing svg{width:100%;height:100%;overflow:visible;display:block;}
#uj-kucing svg *{transform-box:view-box;}
#uj-kucing .k-body{transform-origin:60px 130px}#uj-kucing .k-head{transform-origin:60px 80px}
#uj-kucing .k-tail{transform-origin:90px 116px}#uj-kucing .k-tail2{transform-origin:110px 82px}
#uj-kucing .k-pl{transform-origin:47px 92px}#uj-kucing .k-pr{transform-origin:73px 92px}
#uj-kucing .k-fl,#uj-kucing .k-fr{transform-origin:60px 128px}
#uj-kucing .k-shadow{transform-origin:60px 134px}
#uj-kucing .k-eye{transform-origin:60px 54px}
#uj-kucing .k-mo{transform-origin:60px 72px;opacity:0}
#uj-kucing .k-eyes-h{opacity:0}
#uj-gelembung{position:fixed;z-index:91;max-width:220px;background:#FFFAF0;color:#4A2410;border:2px solid #F0CC9C;border-radius:16px;
 padding:.45rem .7rem;font:700 .8rem/1.3 'Nunito',system-ui,sans-serif;box-shadow:0 4px 0 rgba(224,160,90,.5),0 6px 14px rgba(120,60,20,.2);
 opacity:0;transform:translateY(-6px) scale(.96);transition:opacity .25s,transform .25s;pointer-events:none;left:0;top:0;}
#uj-gelembung.tampil{opacity:1;transform:none;}
#uj-gelembung.menu{pointer-events:auto;}
#uj-gelembung::after{content:"";position:absolute;left:var(--ekor,24px);top:-8px;width:12px;height:12px;background:#FFFAF0;border-left:2px solid #F0CC9C;border-top:2px solid #F0CC9C;transform:rotate(45deg);}
#uj-gelembung.atas::after{top:auto;bottom:-8px;border:0;border-right:2px solid #F0CC9C;border-bottom:2px solid #F0CC9C;}
#uj-gelembung .mkn{display:flex;gap:.3rem;margin-top:.4rem;flex-wrap:wrap}
#uj-gelembung .mkn button{font-size:1.25rem;line-height:1;border:2px solid #F0CC9C;background:#FFF1DB;border-radius:12px;padding:.25rem .4rem;cursor:pointer;transition:transform .12s}
#uj-gelembung .mkn button:active{transform:scale(.88)}
.uj-fx{position:fixed;z-index:92;pointer-events:none;left:0;top:0;will-change:transform,opacity;}
@media (prefers-reduced-motion:reduce){#uj-kucing{display:none}}
"""


def js(sapa: str = "", nama: str = "", kabar: str = "", sembunyi: bool = False) -> str:
    """Skrip pemasang kucing (dijalankan di iframe kecil, memasang elemen ke halaman induk)."""
    if sembunyi:
        return "<script>(function(P){if(P.__ujKucing)P.__ujKucing.hide();})(window.parent);</script>"
    cfg = {"sapa": sapa, "nama": nama, "kabar": kabar, "frasa": FRASA, "css": css(), "svg": svg()}
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
