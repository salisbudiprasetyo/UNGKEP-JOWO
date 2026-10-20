import streamlit as st

import services

st.set_page_config(page_title="UNGKEP JOWO", page_icon="🍛", layout="centered",
                   initial_sidebar_state="collapsed")

CSS = """
<style>
#MainMenu, footer, [data-testid="stToolbar"] {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding: 2.6rem 0.8rem 5rem 0.8rem; max-width: 720px;}
h1.judul {text-align:center; font-weight:800; letter-spacing:.04em; margin:0; padding:0; font-size:1.9rem;}
p.subjudul {text-align:center; font-weight:700; margin:.1rem 0 1rem 0; opacity:.85;}
.st-key-btn_admin {position: fixed; top: .55rem; right: .7rem; z-index: 2147483000; width:auto;}
.st-key-btn_admin button {border-radius: 999px; min-height: 2.4rem; padding: 0 .8rem;}
.stButton > button, .stFormSubmitButton > button {min-height: 2.8rem; border-radius: .6rem;}
.kartu {border:1px solid rgba(128,128,128,.35); border-radius:.8rem; padding:.7rem .9rem; margin:.4rem 0;}
.kartu .besar {font-size:1.5rem; font-weight:800;}
.rekap-wrap {overflow-x:auto; border:1px solid rgba(128,128,128,.4); border-radius:.5rem;}
table.rekap {border-collapse: separate; border-spacing:0; font-size:.78rem; width:max-content; min-width:100%;}
table.rekap th, table.rekap td {border-right:1px solid rgba(128,128,128,.35); border-bottom:1px solid rgba(128,128,128,.35);
  padding:.35rem .45rem; text-align:center; white-space:nowrap; background: var(--background-color, #fff);}
table.rekap th {font-weight:700; background: rgba(128,128,128,.14);}
table.rekap .nama {position:sticky; left:0; text-align:left; z-index:2; min-width:6.2rem; max-width:7.5rem;
  overflow:hidden; text-overflow:ellipsis; font-weight:600; background: var(--secondary-background-color, #f4f4f4);}
table.rekap thead .nama {z-index:3;}
table.rekap .tot {font-weight:700; position:sticky; right:0; z-index:2; background: var(--secondary-background-color, #f4f4f4);}
table.rekap td.me {background: rgba(255,200,0,.22);}
table.rekap td.ada {font-weight:600;}
table.rekap td.hari-ini, table.rekap th.hari-ini {box-shadow: inset 0 -3px 0 #1f77b4;}
table.rekap td.kosong {opacity:.35;}
.chip-lunas {color:#1a7f37; font-weight:700;} .chip-belum {color:#c0392b; font-weight:700;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

beranda = st.Page("pages_app/beranda.py", title="Beranda", icon="🍛", default=True)
admin = st.Page("pages_app/admin.py", title="Admin", icon=":material/admin_panel_settings:")

# Halaman admin tidak muncul di menu; hanya bisa dibuka lewat ikon admin (khusus admin).
pages = [beranda] + ([admin] if services.is_admin() else [])
st.navigation(pages, position="hidden").run()
