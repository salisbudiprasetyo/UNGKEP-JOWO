"""Tampilan umum: warung manis (hangat, pastel, imut) — logo, kepala halaman, dan pola latar vektor.
Semua gambar dibuat dari SVG sederhana buatan sendiri (tanpa berkas gambar), jadi ringan dan tajam di layar HP."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote


# ----------------------------------------------------------------- motif (koordinat lokal ± 0..64)
def _wajah(x: float, y: float, s: float = 1.0) -> str:
    return (f'<circle cx="{x-5*s}" cy="{y}" r="{1.7*s}" fill="#5A2A22"/><circle cx="{x+5*s}" cy="{y}" r="{1.7*s}" fill="#5A2A22"/>'
            f'<path d="M{x-2.2*s} {y+3*s} q{2.2*s} {2.4*s} {4.4*s} 0" stroke="#5A2A22" stroke-width="{1.3*s}" fill="none" stroke-linecap="round"/>'
            f'<circle cx="{x-9*s}" cy="{y+3*s}" r="{2.3*s}" fill="#FF8FA8" opacity=".7"/><circle cx="{x+9*s}" cy="{y+3*s}" r="{2.3*s}" fill="#FF8FA8" opacity=".7"/>')


def udang() -> str:
    """Udang rebus yang gemuk: badan melengkung berisi, garis ruas, ekor mengembang, mata besar."""
    badan = ("M6 22 C8 6 30 -2 48 10 C62 20 62 40 50 52 C54 40 52 30 44 24 C34 17 24 20 20 30 C16 36 6 34 6 22 Z")
    return ('<path d="M50 52 C41 54 36 62 39 67 C45 66 50 61 50 52 Z" fill="#FF6F4F"/>'
            '<path d="M50 52 C53 61 58 65 64 63 C63 57 58 53 50 52 Z" fill="#FF6F4F"/>'
            '<path d="M50 52 C46 60 49 68 53 68 C55 63 53 58 50 52 Z" fill="#FF8C69"/>'
            '<path d="M8 22 C2 22 -2 18 -4 12 C3 12 8 14 10 17 Z" fill="#F0644A"/>'
            f'<path d="{badan}" fill="#FF9570" stroke="#EE6B4D" stroke-width="1.6" stroke-linejoin="round"/>'
            '<path d="M20 4 L25 19 M31 1.5 L34 17 M42 6 L43 22 M52 14 L48 27 M58 26 L52 36" stroke="#FFD1BF" stroke-width="2.2" stroke-linecap="round"/>'
            '<path d="M12 8 C20 -1 34 -2 44 6" stroke="#FFC4AE" stroke-width="2.6" fill="none" stroke-linecap="round" opacity=".8"/>'
            '<path d="M18 31 l-3 7 M25 27 l-2 8 M32 24 l1 8" stroke="#F0644A" stroke-width="2" stroke-linecap="round"/>'
            '<path d="M7 28 C0 32 -3 40 0 48" stroke="#F0644A" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
            '<circle cx="15" cy="19" r="3.6" fill="#fff"/><circle cx="15.6" cy="19.4" r="2.1" fill="#5A2A22"/>'
            '<circle cx="21" cy="26" r="3" fill="#FF8FA8" opacity=".7"/>')


def ikan() -> str:
    return ('<path d="M50 22 L69 8 Q64 22 69 36 Z" fill="#6EC6DA"/>'
            '<path d="M20 9 Q30 -3 42 9 Z" fill="#6EC6DA"/>'
            '<ellipse cx="28" cy="22" rx="25" ry="16" fill="#92DAE8"/>'
            '<ellipse cx="28" cy="29" rx="19" ry="8" fill="#D6F3F7" opacity=".85"/>'
            '<path d="M30 14 q6 4 0 9 M38 14 q6 4 0 9 M46 16 q4 3 0 7" stroke="#fff" stroke-width="1.4" fill="none" opacity=".8" stroke-linecap="round"/>'
            '<circle cx="14" cy="18" r="4.2" fill="#fff"/><circle cx="14.6" cy="18.4" r="2.2" fill="#5A2A22"/>'
            '<path d="M7 25 q4 4 8 0" stroke="#5A2A22" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
            '<circle cx="19" cy="27" r="3" fill="#FF8FA8" opacity=".7"/>')


def paha_ayam() -> str:
    return ('<g transform="rotate(-30 30 30)">'
            '<path d="M36 36 L58 54" stroke="#FFF3DC" stroke-width="7" stroke-linecap="round"/>'
            '<circle cx="60" cy="50" r="4.4" fill="#FFF3DC"/><circle cx="55" cy="58" r="4.4" fill="#FFF3DC"/>'
            '<path d="M8 28 C-2 10 22 -4 40 6 C56 15 52 36 34 41 C22 44 13 38 8 28 Z" fill="#F6B23D"/>'
            '<circle cx="18" cy="14" r="2.2" fill="#E8901A"/><circle cx="32" cy="10" r="2" fill="#E8901A"/><circle cx="40" cy="24" r="2.4" fill="#E8901A"/>'
            '<circle cx="24" cy="28" r="2" fill="#E8901A"/><ellipse cx="20" cy="18" rx="7" ry="3.2" fill="#fff" opacity=".45" transform="rotate(-25 20 18)"/>'
            '</g>')


def telur() -> str:
    return ('<path d="M8 26 C3 11 20 2 32 6 C46 -3 63 10 56 27 C62 41 44 51 32 46 C18 54 2 41 8 26 Z" fill="#FFFDF6" stroke="#F4E4C6" stroke-width="2"/>'
            '<circle cx="32" cy="26" r="12" fill="#FFC83D"/><circle cx="27.5" cy="21.5" r="3.4" fill="#fff" opacity=".7"/>' + _wajah(32, 28, .8))


def mangkok() -> str:
    return ('<path d="M-4 10 C-2 -4 6 -4 8 4 M62 8 C64 -4 72 -2 70 8" stroke="#FFC9BC" stroke-width="2.2" fill="none" stroke-linecap="round" opacity="0"/>'
            '<path d="M18 -2 c-4 -5 4 -8 0 -13 M32 0 c-4 -5 4 -8 0 -13 M46 -2 c-4 -5 4 -8 0 -13" stroke="#FFC9BC" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
            '<path d="M5 26 C5 6 59 6 59 26 Z" fill="#fff" stroke="#F4E4C6" stroke-width="2"/>'
            '<circle cx="20" cy="17" r="1.6" fill="#EBDCC0"/><circle cx="32" cy="12" r="1.6" fill="#EBDCC0"/><circle cx="43" cy="18" r="1.6" fill="#EBDCC0"/>'
            '<path d="M2 26 H62 C62 46 48 58 32 58 C16 58 2 46 2 26 Z" fill="#FF8E7A"/>'
            '<path d="M5 33 H59" stroke="#FFC4B6" stroke-width="3" stroke-linecap="round"/>' + _wajah(32, 43, .85))


def gelas_teh() -> str:
    return ('<path d="M36 40 L44 -6" stroke="#FF8FB1" stroke-width="4.5" stroke-linecap="round"/>'
            '<path d="M12 8 H52 L47 60 H17 Z" fill="#FFD9A0" stroke="#F6B766" stroke-width="2"/>'
            '<path d="M13.5 22 H50.5 L47 60 H17 Z" fill="#F7B55E" opacity=".75"/>'
            '<rect x="22" y="26" width="10" height="10" rx="2.5" fill="#fff" opacity=".7" transform="rotate(14 27 31)"/>'
            '<rect x="33" y="36" width="9" height="9" rx="2.5" fill="#fff" opacity=".65" transform="rotate(-12 37 40)"/>'
            '<circle cx="52" cy="8" r="9.5" fill="#FFE680" stroke="#F7C948" stroke-width="2"/>'
            '<path d="M52 8 L52 -1.5 M52 8 L60 3 M52 8 L60 13 M52 8 L52 17.5 M52 8 L44 13 M52 8 L44 3" stroke="#F7C948" stroke-width="1.3"/>'
            + _wajah(32, 48, .7))


def cabai() -> str:
    j = "M8 10 C34 6 54 24 56 54"
    return (f'<path d="{j}" fill="none" stroke="#F4574C" stroke-width="11" stroke-linecap="round"/>'
            f'<path d="M12 5 C32 2 48 14 52 30" fill="none" stroke="#FF9488" stroke-width="3" stroke-linecap="round" opacity=".7"/>'
            '<path d="M6 8 C0 4 -2 -2 2 -8" stroke="#58B968" stroke-width="5" fill="none" stroke-linecap="round"/>')


def tomat() -> str:
    return ('<circle cx="22" cy="26" r="17" fill="#FF6F61"/><ellipse cx="15" cy="19" rx="5" ry="3" fill="#fff" opacity=".45" transform="rotate(-30 15 19)"/>'
            '<path d="M22 10 L17 3 L22 6 L27 2 L26 10 L33 11 L25 14 Z" fill="#5BB86A"/>' + _wajah(22, 28, .65))


def bunga() -> str:
    p = "".join(f'<circle cx="{20+11*__import__("math").cos(a*1.2566):.1f}" cy="{20+11*__import__("math").sin(a*1.2566):.1f}" r="8" fill="#FFB3C6"/>' for a in range(5))
    return p + '<circle cx="20" cy="20" r="6" fill="#FFD25E"/>'


def hati() -> str:
    return '<path d="M16 30 C-8 12 6 -6 16 8 C26 -6 40 12 16 30 Z" fill="#FF9FB8"/><ellipse cx="9" cy="8" rx="3" ry="2" fill="#fff" opacity=".5"/>'


def kilau() -> str:
    return '<path d="M12 0 C13 8 16 11 24 12 C16 13 13 16 12 24 C11 16 8 13 0 12 C8 11 11 8 12 0 Z" fill="#FFD25E"/>'


def daun() -> str:
    return '<path d="M2 28 C0 8 16 0 32 2 C34 18 24 32 2 28 Z" fill="#A8DCB0"/><path d="M4 26 C12 18 20 12 30 4" stroke="#fff" stroke-width="1.6" fill="none" opacity=".7"/>'


def _g(motif: str, x: float, y: float, rot: float = 0, s: float = 1.0) -> str:
    return f'<g transform="translate({x} {y}) rotate({rot}) scale({s})">{motif}</g>'


# ----------------------------------------------------------------- pola latar & logo
@lru_cache(maxsize=1)
def pola_uri() -> str:
    """Ubin latar 400×400: lauk, minuman, dan hiasan imut berwarna pastel."""
    isi = "".join([
        _g(udang(), 24, 30, -12, .95), _g(ikan(), 190, 24, 8, .9), _g(paha_ayam(), 312, 34, 10, .95),
        _g(telur(), 120, 108, -8, .9), _g(mangkok(), 262, 120, 6, .95), _g(gelas_teh(), 24, 150, -6, .9),
        _g(cabai(), 350, 150, 14, .8), _g(tomat(), 176, 200, 0, .95), _g(bunga(), 98, 205, 0, .9),
        _g(ikan(), 28, 290, -14, .85), _g(telur(), 232, 258, 10, .8), _g(udang(), 318, 262, 16, .9),
        _g(mangkok(), 120, 305, -4, .85), _g(paha_ayam(), 230, 345, -8, .85), _g(gelas_teh(), 340, 350, 8, .8),
        _g(hati(), 90, 22, 0, .9), _g(hati(), 168, 128, 12, .7), _g(hati(), 372, 80, -10, .7),
        _g(kilau(), 70, 100, 0, .9), _g(kilau(), 300, 214, 0, .8), _g(kilau(), 20, 232, 0, .7), _g(kilau(), 190, 292, 0, .8),
        _g(daun(), 368, 224, 20, .8), _g(daun(), 70, 262, -30, .8), _g(bunga(), 362, 304, 0, .75), _g(bunga(), 214, 78, 0, .6),
        _g(hati(), 20, 360, 0, .6), _g(kilau(), 126, 372, 0, .7), _g(daun(), 280, 70, -40, .6),
    ])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">'
           f'<g opacity=".55">{isi}</g></svg>')
    return "data:image/svg+xml;utf8," + quote(svg, safe="")


@lru_cache(maxsize=1)
def logo_svg() -> str:
    """Logo buatan sendiri: mangkok kuah gurih berisi ayam goreng kriuk, sayur segar, dan nasi. Tanpa tulisan & tanpa latar."""
    ayam = ('<g transform="translate(31 51) rotate(165) scale(.78) translate(-24 -22)">'
            '<path d="M30 38 L50 58" stroke="#FFF3DC" stroke-width="7" stroke-linecap="round"/>'
            '<circle cx="53" cy="55" r="4.4" fill="#FFF3DC"/><circle cx="47" cy="62" r="4.4" fill="#FFF3DC"/>'
            '<g fill="#F7B53A" stroke="#E08A1C" stroke-width="1.4"><circle cx="43.0" cy="20.0" r="4.2"/><circle cx="38.6" cy="29.6" r="4.2"/><circle cx="27.3" cy="34.8" r="4.2"/><circle cx="14.5" cy="33.0" r="4.2"/><circle cx="6.1" cy="25.1" r="4.2"/><circle cx="6.1" cy="14.9" r="4.2"/><circle cx="14.5" cy="7.0" r="4.2"/><circle cx="27.3" cy="5.2" r="4.2"/><circle cx="38.6" cy="10.4" r="4.2"/></g>'
            '<ellipse cx="24" cy="20" rx="20" ry="15.5" fill="#F7B53A"/>'
            '<path d="M9 13 C14 5 26 3 34 6" stroke="#FFE08A" stroke-width="3" fill="none" stroke-linecap="round"/>'
            '<g fill="#E0881A"><circle cx="13" cy="19" r="1.8"/><circle cx="22" cy="12" r="1.6"/><circle cx="32" cy="17" r="1.8"/><circle cx="20" cy="26" r="1.7"/>'
            '<circle cx="30" cy="27" r="1.6"/><circle cx="38" cy="22" r="1.4"/></g>'
            '<g fill="#FFD66B"><circle cx="24" cy="19" r="1.4"/><circle cx="16" cy="25" r="1.2"/><circle cx="35" cy="12" r="1.2"/></g>'
            '</g>')
    daun = ('<path d="M34 54 C22 44 24 28 36 22 C46 30 44 46 34 54 Z" fill="#5DBB63"/><path d="M34 52 C34 42 36 32 36 24" stroke="#BFE9B8" stroke-width="1.6" fill="none"/>'
            '<path d="M44 54 C38 40 46 26 60 24 C64 38 56 50 44 54 Z" fill="#7BCB6F"/><path d="M46 52 C50 42 56 34 60 26" stroke="#CFF0C4" stroke-width="1.6" fill="none"/>'
            '<path d="M54 56 C54 46 66 40 76 44 C74 54 66 58 54 56 Z" fill="#4FAE5B"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<path d="M32 24 c-4 -5 4 -8 0 -13 M50 20 c-4 -5 4 -8 0 -13 M68 24 c-4 -5 4 -8 0 -13" stroke="#FFB07A" stroke-width="3" fill="none" stroke-linecap="round"/>'
            '<g transform="translate(78 2) scale(.45)">' + hati() + '</g>'
            '<g transform="translate(2 24) scale(.62)">' + kilau() + '</g>'
            '<g transform="translate(84 58) scale(.5)">' + kilau() + '</g>'
            '<ellipse cx="50" cy="55" rx="42" ry="10" fill="#FFD27A"/>'
            '<ellipse cx="50" cy="55" rx="37" ry="7.5" fill="#F39B2E"/>'
            '<ellipse cx="50" cy="54" rx="30" ry="4" fill="#FFB84D" opacity=".7"/>'
            + daun +
            '<path d="M60 58 C60 47 85 47 85 58 Z" fill="#FFFDF6" stroke="#F1E2C4" stroke-width="1.5"/>'
            '<circle cx="67" cy="54" r="1.2" fill="#E6D6B6"/><circle cx="74" cy="52" r="1.2" fill="#E6D6B6"/><circle cx="79" cy="56" r="1.2" fill="#E6D6B6"/>'
            + ayam +
            '<circle cx="26" cy="57" r="4.2" fill="#FF9A3C" stroke="#E57E1E" stroke-width="1"/><circle cx="26" cy="57" r="1.4" fill="#FFD9A0"/>'
            '<circle cx="52" cy="59" r="2.6" fill="#E8403A"/><circle cx="52" cy="59" r=".9" fill="#FFB3A8"/>'
            '<circle cx="44" cy="58.5" r="1.2" fill="#FFE9A0"/><circle cx="60" cy="59" r="1.1" fill="#FFE9A0"/><circle cx="34" cy="59" r="1" fill="#FFE9A0"/>'
            '<path d="M9 54 Q50 72 91 54 C91 80 73 96 50 96 C27 96 9 80 9 54 Z" fill="#FF8E7A"/>'
            '<path d="M9 54 Q50 72 91 54 C91 57 90.6 60 90 63 Q50 80 10 63 C9.4 60 9 57 9 54 Z" fill="#FFD27A"/>'
            '<path d="M18 76 q5 -4 10 0 t10 0 t10 0 t10 0 t10 0 t10 0" stroke="#fff" stroke-width="2" fill="none" opacity=".6" stroke-linecap="round"/>'
            + _wajah(50, 85, 1.0) + '</svg>')


@lru_cache(maxsize=1)
def logo_uri() -> str:
    return "data:image/svg+xml;utf8," + quote(logo_svg(), safe="")


@lru_cache(maxsize=1)
def _stiker_svg() -> str:
    isi = "".join([_g(udang(), 6, 4, 10, .55), _g(ikan(), 88, 44, -8, .5), _g(paha_ayam(), 150, 6, 6, .5),
                   _g(hati(), 70, 10, 0, .5), _g(kilau(), 130, 54, 0, .6), _g(kilau(), 2, 56, 0, .5), _g(daun(), 190, 54, 20, .5)])
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 230 90" aria-hidden="true">{isi}</svg>'


@lru_cache(maxsize=8)
def hero(judul: str, sub: str, tagline: str = "") -> str:
    tag = f'<div class="sub2">{tagline}</div>' if tagline else ""
    return (f'<div class="hero"><div class="stiker"><img alt="" src="data:image/svg+xml;utf8,{quote(_stiker_svg(), safe="")}"></div>'
            f'<div class="logo"><img alt="Logo Ungkep Jowo" src="{logo_uri()}"></div>'
            f'<div class="tt"><h1>{judul}</h1><div class="sub">{sub}</div>{tag}</div></div>')


def css() -> str:
    """Gaya tema (dimuat setelah style.css supaya menimpa gaya lama)."""
    return _CSS.replace("%POLA%", pola_uri())


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;600;700;800&display=swap');
:root{--brand:#E4574B;--brand-d:#7B3220;--rose:#F59AB1;--rose-l:#FFE3EA;--butter:#FFE08A;--mint:#CBEBD7;--peach:#FFE4CE;
--cream:#FFF6EA;--cream2:#FFEBD6;--line:#F6D5BC;--ink:#4A2A1E;--muted:#9A7A68;--bg:#FFF6EA;--gold:#F6B23D;}
html,body,.stApp,[data-testid="stAppViewContainer"]{font-family:'Nunito',system-ui,sans-serif;color:var(--ink);}
h1,h2,h3,h4,.kartu .besar,.hero h1,.grp-h,.pill-pesan{font-family:'Fredoka','Nunito',sans-serif;}
.stApp{background-color:#FFF6EA;background-image:url("%POLA%");background-size:400px 400px;}
[data-testid="stHeader"]{background:transparent;}
.block-container{background:rgba(255,246,234,.55);border-radius:0 0 28px 28px;}
h2,h3{color:var(--brand-d);}

/* kepala halaman: tenda warung pastel + logo + stiker lauk */
.hero{position:relative;display:flex;align-items:center;gap:.9rem;text-align:left;padding:1.7rem 1rem 1.05rem;margin:.2rem 0 1.1rem;overflow:hidden;
 background:radial-gradient(circle at 12% 30%,rgba(255,255,255,.75),transparent 45%),linear-gradient(135deg,#FFD9B5 0%,#FFC9B0 48%,#FFB5BF 100%);
 border-radius:26px;border:3px solid #fff;box-shadow:0 8px 22px rgba(228,87,75,.22),0 0 0 2px #FFC7A8;}
.hero::before{content:"";position:absolute;left:0;right:0;top:0;height:.7rem;
 background:repeating-linear-gradient(90deg,#FF8E7A 0 1.2rem,#FFF6EA 1.2rem 2.4rem);}
.hero::after{content:"";position:absolute;left:0;right:0;top:.7rem;height:.6rem;
 background:radial-gradient(circle at 1.2rem 0,#FF8E7A .6rem,transparent .62rem) 0 0/2.4rem .6rem repeat-x,
            radial-gradient(circle at 2.4rem 0,#FFF6EA .6rem,transparent .62rem) 0 0/2.4rem .6rem repeat-x;}
.hero .stiker{position:absolute;right:-.2rem;top:1.5rem;width:42%;opacity:.9;pointer-events:none;}
.hero .stiker img{display:block;width:100%;height:auto;}
.hero .logo{position:relative;flex:0 0 auto;width:5.4rem;margin-top:.5rem;filter:drop-shadow(0 4px 5px rgba(160,60,40,.25));}
.hero .logo img{display:block;width:100%;height:auto;}
.hero .tt{position:relative;flex:1;margin-top:.5rem;}
.hero h1{margin:0;padding:0;font-size:1.65rem;font-weight:700;letter-spacing:.05em;color:#fff;line-height:1.1;
 text-shadow:0 2px 0 #E4574B,0 0 12px rgba(228,87,75,.35);-webkit-text-stroke:.5px #E4574B;}
.hero .sub{display:inline-block;margin-top:.45rem;padding:.14rem .8rem;border-radius:999px;background:#fff;color:var(--brand);
 font-weight:800;font-size:.72rem;letter-spacing:.14em;box-shadow:0 2px 0 #FFC7A8;}
.hero .sub2{margin-top:.4rem;font-size:.76rem;color:var(--brand-d);font-weight:700;}

/* kartu & komponen */
.kartu,.rekap-wrap,.rk-akhir,.psn{background:#FFFDF8;border:2px solid var(--line);border-radius:20px;box-shadow:0 4px 0 rgba(246,213,188,.7);}
.kartu .besar{color:var(--brand);}
.kartu small,.cap,.rk-akhir .cap2{color:var(--muted);}
.judul-sec{flex-wrap:wrap;gap:.1rem .6rem;} .judul-sec h3{white-space:nowrap;font-size:1.05rem!important;}
.judul-sec h3::before{content:"🍤 ";}
.grp-h{background:linear-gradient(135deg,#FF8E7A,#F59AB1);color:#fff;border-radius:999px;padding:.45rem 1rem;box-shadow:0 3px 0 #F6B8A6;}
.grp-h span{background:rgba(255,255,255,.35);}
.stButton>button,.stFormSubmitButton>button{border-radius:999px;border:2px solid var(--line);background:#FFFDF8;color:var(--brand-d);font-weight:800;}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:linear-gradient(180deg,#FF7A68,#E4574B);
 border-color:#C8453A;color:#fff;box-shadow:0 3px 0 #C8453A;}
.stButton>button:active{transform:translateY(2px);}
.stTextInput input,div[data-baseweb="select"]>div,.stNumberInput input,[data-baseweb="input"]{background:#FFF9F0!important;border-radius:16px!important;}
.stTextInput input{border:2px solid var(--line)!important;}
.stTabs [data-baseweb="tab-highlight"]{background:var(--brand)!important;}
.stTabs [aria-selected="true"]{color:var(--brand)!important;}
[data-testid="stDialog"]>div,div[role="dialog"]{border-radius:26px!important;background:#FFFAF2!important;}
.stCheckbox [data-baseweb="checkbox"] span:first-child{border-radius:7px;}

/* tabel kasbon */
table.rekap th{background:var(--peach);color:var(--brand-d);}
table.rekap .nama,table.rekap .tot{background:#FFEEDC;color:var(--ink);}
table.rekap td,table.rekap th{border-color:var(--line);}
table.rekap td.me{background:#FFF3C4;}
table.rekap th.hari-ini{box-shadow:inset 0 -3px 0 var(--brand);}
.pill-pesan{background:linear-gradient(180deg,#FF7A68,#E4574B);box-shadow:0 2px 0 #C8453A;border-radius:999px;}
table.rekap td.lunas-sel{background:#D8F3E2!important;color:#1E7F4B;}
table.rekap td.tot.lunas-tot{background:#BDEBD0!important;color:#17653B;}
/* libur: kolom merah muda, tulisan merah menyala */
table.rekap th.libur{background:#FFC2D1!important;color:#E0002B!important;}
table.rekap td.libur{background:#FFE3EA!important;color:#E0002B!important;font-weight:800;font-style:normal;font-size:.66rem;letter-spacing:.03em;}
.libur-info{background:#FFE3EA;border-color:#F8A9BE;color:#B0102A;}
.rk-akhir tr.tot td{border-top:2px dashed var(--line);}
.rk-akhir td.q{color:var(--brand);}
.psn.s-rev{background:#FFF4C9;border-color:#F6D77A;}
"""
