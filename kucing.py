"""Meong, kucing maskot: berjalan-jalan di halaman, menyapa setelah login, dan bisa diajak ngobrol (tanya-jawab berbasis aturan).
Gambar dan animasi dibuat sendiri (SVG + CSS), tanpa berkas gambar dan tanpa layanan luar."""
from __future__ import annotations

import json
import re
from datetime import date

import logic
import orders

# ------------------------------------------------------------------ gambar kucing (menghadap kanan)
_SVG = """
<svg class="uj-svg" viewBox="0 0 110 86" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
 <g class="zz"><text x="78" y="14" font-size="11" fill="#9A6F4E" font-weight="800">z</text><text x="88" y="6" font-size="9" fill="#9A6F4E" font-weight="800">z</text></g>
 <ellipse class="bayang" cx="52" cy="82" rx="30" ry="3.6" fill="rgba(90,42,20,.18)"/>
 <g class="badan">
  <path class="ekor" d="M20 48 C4 46 0 28 10 20" fill="none" stroke="#F29A2E" stroke-width="8" stroke-linecap="round"/>
  <path class="ekor-ujung" d="M10 20 C8 18 8 16 10 14" fill="none" stroke="#B9601A" stroke-width="8" stroke-linecap="round" opacity="0"/>
  <rect class="kaki kb1" x="26" y="56" width="9" height="24" rx="4.5" fill="#E8851E"/>
  <rect class="kaki kb2" x="40" y="56" width="9" height="24" rx="4.5" fill="#F29A2E"/>
  <ellipse cx="46" cy="50" rx="31" ry="19" fill="#F29A2E"/>
  <ellipse cx="50" cy="58" rx="22" ry="11" fill="#FFE2B0"/>
  <path d="M32 34 q3 6 0 11 M42 32 q3 6 0 12 M52 33 q3 6 0 11" stroke="#C9701A" stroke-width="3" fill="none" stroke-linecap="round" opacity=".7"/>
  <rect class="kaki kf1" x="62" y="56" width="9" height="24" rx="4.5" fill="#E8851E"/>
  <rect class="kaki kf2" x="73" y="56" width="9" height="24" rx="4.5" fill="#F29A2E"/>
  <g class="pal"><ellipse cx="66.5" cy="80" rx="6" ry="3.2" fill="#FFF1DB"/><ellipse cx="77.5" cy="80" rx="6" ry="3.2" fill="#FFF1DB"/>
   <ellipse cx="30.5" cy="80" rx="6" ry="3.2" fill="#FFF1DB"/><ellipse cx="44.5" cy="80" rx="6" ry="3.2" fill="#FFF1DB"/></g>
 </g>
 <g class="kepala">
  <path d="M66 26 L67 6 L82 20 Z" fill="#F29A2E"/><path d="M69 22 L69.5 11 L78 19.5 Z" fill="#FFB3A0"/>
  <path d="M94 20 L103 6 L104 28 Z" fill="#F29A2E"/><path d="M96 22 L101 12 L101.5 25 Z" fill="#FFB3A0"/>
  <ellipse cx="85" cy="38" rx="21" ry="18" fill="#F29A2E"/>
  <path d="M85 21 v8 M79 22 l2 7 M91 22 l-2 7" stroke="#C9701A" stroke-width="2.6" stroke-linecap="round" opacity=".75"/>
  <ellipse cx="85" cy="46" rx="11" ry="8" fill="#FFE2B0"/>
  <g class="mata"><ellipse cx="77" cy="37" rx="3.6" ry="4.6" fill="#4A2410"/><ellipse cx="93" cy="37" rx="3.6" ry="4.6" fill="#4A2410"/>
   <circle cx="78.2" cy="35.4" r="1.4" fill="#fff"/><circle cx="94.2" cy="35.4" r="1.4" fill="#fff"/></g>
  <g class="mata-tidur"><path d="M73 38 q4 4 8 0 M89 38 q4 4 8 0" stroke="#4A2410" stroke-width="2" fill="none" stroke-linecap="round"/></g>
  <path d="M82.5 43 h5 l-2.5 3 Z" fill="#E8403A"/>
  <path d="M85 46 v2 M85 48 q-3 3 -6 1 M85 48 q3 3 6 1" stroke="#4A2410" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <circle cx="71" cy="45" r="3.4" fill="#FF9A6B" opacity=".7"/><circle cx="99" cy="45" r="3.4" fill="#FF9A6B" opacity=".7"/>
  <path d="M64 44 l-9 -2 M64 47 l-9 2 M106 44 l9 -2 M106 47 l9 2" stroke="#8A5A3A" stroke-width="1.1" stroke-linecap="round" opacity=".7"/>
 </g>
</svg>
"""


def css() -> str:
    return """
#uj-kucing{position:fixed;left:10px;bottom:8px;width:84px;height:68px;z-index:90;cursor:pointer;user-select:none;-webkit-user-select:none;
 -webkit-tap-highlight-color:transparent;touch-action:manipulation;transition:opacity .3s;}
#uj-kucing.sembunyi{display:none;}
#uj-kucing .flip{width:100%;height:100%;transform-origin:50% 100%;}
#uj-kucing.kiri .flip{transform:scaleX(-1);}
#uj-kucing .lompat{width:100%;height:100%;}
#uj-kucing svg{width:100%;height:100%;overflow:visible;display:block;}
#uj-kucing .kaki,#uj-kucing .ekor{transform-box:fill-box;}
#uj-kucing .kaki{transform-origin:50% 8%;}
#uj-kucing .ekor{transform-origin:100% 100%;animation:ujEkor 2.6s ease-in-out infinite;}
#uj-kucing .mata{transform-box:fill-box;transform-origin:50% 50%;animation:ujKedip 4.2s infinite;}
#uj-kucing .mata-tidur,#uj-kucing .zz{opacity:0;}
#uj-kucing .kepala{transform-box:fill-box;transform-origin:50% 90%;}
#uj-kucing .badan{transform-box:fill-box;transform-origin:50% 100%;}
@keyframes ujEkor{0%,100%{transform:rotate(-10deg)}50%{transform:rotate(14deg)}}
@keyframes ujKedip{0%,94%,100%{transform:scaleY(1)}97%{transform:scaleY(.1)}}
@keyframes ujAyun{0%{transform:rotate(34deg)}100%{transform:rotate(-34deg)}}
@keyframes ujAyun2{0%{transform:rotate(-34deg)}100%{transform:rotate(34deg)}}
@keyframes ujGoyang{0%,100%{transform:translateY(0)}50%{transform:translateY(-2.5px)}}
@keyframes ujLompat{0%{transform:translateY(0) scale(1.08,.9)}18%{transform:translateY(-8px) scale(.95,1.08)}50%{transform:translateY(-58px)}82%{transform:translateY(-6px) scale(.97,1.05)}92%{transform:translateY(0) scale(1.1,.88)}100%{transform:translateY(0) scale(1)}}
@keyframes ujZz{0%{opacity:0;transform:translate(0,6px)}30%{opacity:1}100%{opacity:0;transform:translate(6px,-12px)}}
@keyframes ujSapa{0%,100%{transform:rotate(0)}50%{transform:rotate(-150deg)}}
@keyframes ujNapas{0%,100%{transform:scale(1,1)}50%{transform:scale(1.03,1.06)}}
@keyframes ujAngguk{0%,100%{transform:rotate(0)}50%{transform:rotate(9deg)}}
#uj-kucing.jalan .kb1,#uj-kucing.jalan .kf2{animation:ujAyun .5s ease-in-out infinite alternate}
#uj-kucing.jalan .kb2,#uj-kucing.jalan .kf1{animation:ujAyun2 .5s ease-in-out infinite alternate}
#uj-kucing.jalan .badan{animation:ujGoyang .5s ease-in-out infinite}
#uj-kucing.lari .kb1,#uj-kucing.lari .kf2{animation:ujAyun .22s ease-in-out infinite alternate}
#uj-kucing.lari .kb2,#uj-kucing.lari .kf1{animation:ujAyun2 .22s ease-in-out infinite alternate}
#uj-kucing.lari .badan{animation:ujGoyang .22s ease-in-out infinite}
#uj-kucing.lari .ekor{animation-duration:.5s}
#uj-kucing.lompat-aksi .lompat{animation:ujLompat .8s ease-in-out}
#uj-kucing.lompat-aksi .kaki{transform:rotate(18deg)}
#uj-kucing.duduk .kb1,#uj-kucing.duduk .kb2{transform:rotate(-70deg) translate(6px,-6px)}
#uj-kucing.duduk .badan{transform:rotate(-16deg) translateY(2px)}
#uj-kucing.duduk .kepala{transform:translateY(-3px)}
#uj-kucing.tidur .kaki{transform:rotate(90deg) translate(0,-2px);}
#uj-kucing.tidur .badan{transform:scaleY(.72) translateY(6px);animation:ujNapas 3s ease-in-out infinite}
#uj-kucing.tidur .kepala{transform:translate(-6px,14px) rotate(14deg)}
#uj-kucing.tidur .mata{display:none}
#uj-kucing.tidur .mata-tidur{opacity:1}
#uj-kucing.tidur .zz{opacity:1;animation:ujZz 2.4s ease-out infinite}
#uj-kucing.tidur .ekor{animation-duration:6s}
#uj-kucing.sapa .kf2{transform-origin:50% 10%;animation:ujSapa .6s ease-in-out 3}
#uj-kucing.sapa .kepala{animation:ujAngguk .6s ease-in-out 3}
#uj-gelembung{position:fixed;z-index:91;max-width:210px;background:#FFFAF0;color:#4A2410;border:2px solid #F0CC9C;border-radius:16px;
 padding:.45rem .7rem;font:700 .8rem/1.3 'Nunito',system-ui,sans-serif;box-shadow:0 4px 0 rgba(224,160,90,.5),0 6px 14px rgba(120,60,20,.2);
 opacity:0;transform:translateY(6px) scale(.96);transition:opacity .25s,transform .25s;pointer-events:none;}
#uj-gelembung.tampil{opacity:1;transform:none;}
#uj-gelembung::after{content:"";position:absolute;left:var(--ekor,24px);bottom:-8px;width:12px;height:12px;background:#FFFAF0;border-right:2px solid #F0CC9C;border-bottom:2px solid #F0CC9C;transform:rotate(45deg);}
.uj-hati{position:fixed;z-index:92;font-size:18px;pointer-events:none;animation:ujHati 1.2s ease-out forwards;}
@keyframes ujHati{0%{opacity:0;transform:translateY(0) scale(.6)}20%{opacity:1}100%{opacity:0;transform:translateY(-46px) scale(1.2)}}
@media (prefers-reduced-motion:reduce){#uj-kucing *{animation:none!important}}
"""


_JS = r"""
(function(P){
 var D=P.document;
 if(!P.__ujKucing){
  var st=D.createElement('style'); st.id='uj-kucing-css'; st.textContent=%CSS%; D.head.appendChild(st);
  var el=D.createElement('div'); el.id='uj-kucing'; el.setAttribute('data-c','k|chat'); el.setAttribute('role','button'); el.setAttribute('aria-label','Tanya Meong');
  el.innerHTML='<div class="flip"><div class="lompat">'+%SVG%+'</div></div>';
  D.body.appendChild(el);
  var gl=D.createElement('div'); gl.id='uj-gelembung'; D.body.appendChild(gl);
  var K={el:el,gl:gl,x:10,dir:1,target:null,mode:'duduk',until:0,bicara:0,lompat:0,sembunyi:false,frasa:%FRASA%};
  var W=function(){return Math.max(160,(P.innerWidth||360)-90)};
  function kelas(m){K.mode=m; el.classList.remove('jalan','lari','duduk','tidur','sapa'); if(m!=='diam') el.classList.add(m);}
  function pos(){el.style.left=Math.round(K.x)+'px'; el.classList.toggle('kiri',K.dir<0);
   if(gl.classList.contains('tampil')){var gw=gl.offsetWidth; var gx=Math.min(Math.max(6,K.x+40-gw/2),(P.innerWidth||360)-gw-6); gl.style.left=gx+'px'; gl.style.bottom=(80)+'px'; gl.style.setProperty('--ekor',Math.max(12,K.x+40-gx-6)+'px');}}
  K.bilang=function(t,ms){gl.textContent=t; gl.classList.add('tampil'); pos(); clearTimeout(K._bt); K._bt=setTimeout(function(){gl.classList.remove('tampil')},ms||4200);};
  K.hati=function(){var h=D.createElement('div'); h.className='uj-hati'; h.textContent='❤️'; h.style.left=(K.x+34)+'px'; h.style.bottom='74px'; D.body.appendChild(h); setTimeout(function(){h.remove()},1300);};
  K.lompat=function(){el.classList.add('lompat-aksi'); setTimeout(function(){el.classList.remove('lompat-aksi')},850);};
  K.sapa=function(t){K.show(); el.classList.remove('jalan','lari','duduk','tidur'); kelas('sapa'); K.target=null; K.until=Date.now()+3800; K.bilang(t,5200); K.lompat(); K.hati();};
  K.hide=function(){K.sembunyi=true; el.classList.add('sembunyi'); gl.classList.remove('tampil');};
  K.show=function(){K.sembunyi=false; el.classList.remove('sembunyi');};
  function pilih(){
   var r=Math.random(), now=Date.now();
   if(K.mode==='tidur'&&r<.7){K.until=now+3000; return;}
   if(r<.38){kelas('jalan'); K.dir=Math.random()<.5?-1:1; K.target=Math.random()*W(); K.until=now+4000+Math.random()*4000;}
   else if(r<.52){kelas('lari'); K.target=Math.random()*W(); K.until=now+3500;}
   else if(r<.68){kelas('duduk'); K.target=null; K.until=now+3000+Math.random()*3000;}
   else if(r<.78){kelas('tidur'); K.target=null; K.until=now+7000+Math.random()*5000; K.bilang('Zzz...',2200);}
   else if(r<.9){kelas('duduk'); K.target=null; K.until=now+2200; K.lompat();}
   else {kelas('jalan'); K.target=K.x<W()/2?W():0; K.until=now+6000;}
  }
  function tick(){
   if(K.sembunyi) return;
   var now=Date.now();
   if(K.target!=null){
    var d=K.target-K.x, v=(K.mode==='lari'?4.2:1.5);
    if(Math.abs(d)<=v){K.target=null; if(K.mode==='jalan'||K.mode==='lari'){kelas('duduk'); K.until=now+1800;}}
    else {K.dir=d>0?1:-1; K.x+=K.dir*v;}
   }
   K.x=Math.max(0,Math.min(W(),K.x));
   if(now>K.until) pilih();
   if(now>K.bicara && K.mode!=='tidur' && !K.diam){K.bicara=now+22000+Math.random()*18000; K.bilang(K.frasa[Math.floor(Math.random()*K.frasa.length)],4000);}
   pos();
  }
  var reduce=P.matchMedia&&P.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(!reduce) setInterval(tick,40); else {kelas('duduk');}
  K.bicara=Date.now()+15000; K.until=Date.now()+1500; kelas('duduk'); pos();
  // ketuk kucing: melompat + hati (jendela obrolan dibuka oleh pengendali ketukan halaman)
  el.addEventListener('click',function(){K.lompat(); K.hati(); K.bilang('Meong! Mau tanya apa?',2600); if(K.mode==='tidur'){kelas('duduk');K.until=Date.now()+2500;}},true);
  // ketuk bagian kosong halaman: kucing lari ke situ
  D.addEventListener('pointerdown',function(e){
   if(K.sembunyi||reduce) return;
   var t=e.target; if(!t||!t.closest) return;
   if(t.closest('button,a,input,select,textarea,label,table,[data-c],[role=dialog],[data-testid=stDialog],[data-baseweb],[data-testid=stExpander],iframe,svg')) return;
   K.target=Math.max(0,Math.min(W(),e.clientX-40)); kelas('lari'); K.until=Date.now()+5000;
  },true);
  P.__ujKucing=K;
 }
 var K2=P.__ujKucing; K2.show();
 var s=%SAPA%; if(s) K2.sapa(s);
})(window.parent);
"""

FRASA = ["Sudah pesan hari ini? 🍗", "Pesan sebelum jam 10:45 ya!", "Meong~ kasbon jangan lupa dibayar tgl 10 😸",
         "Mau tahu menu hari ini? Ketuk aku!", "Es teh dulu, biar segar 🧋", "Aku jagain warung, tenang aja~",
         "Ayam gepreknya kriuk lho! 😋", "Ketuk aku kalau mau tanya-tanya ya 🐾"]


def js(sapa: str = "", sembunyi: bool = False) -> str:
    """Skrip pemasang kucing (dijalankan di iframe kecil, memasang elemen ke halaman induk)."""
    if sembunyi:
        return "<script>(function(P){if(P.__ujKucing)P.__ujKucing.hide();})(window.parent);</script>"
    kode = (_JS.replace("%CSS%", json.dumps(css())).replace("%SVG%", json.dumps(_SVG.strip()))
            .replace("%FRASA%", json.dumps(FRASA, ensure_ascii=False)).replace("%SAPA%", json.dumps(sapa, ensure_ascii=False)))
    return f"<script>{kode}</script>"


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
    return "Meong? Aku belum paham 🙀 Coba tanya soal **menu**, **pesanan saya**, **tagihan**, **cara bayar**, atau **jam batas pesan**."
