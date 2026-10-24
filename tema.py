"""Tampilan umum: kepala halaman bergaya warung dengan logo."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

_LOGO = Path(__file__).parent / "assets" / "logo.png"


@lru_cache(maxsize=1)
def _logo_uri() -> str:
    if not _LOGO.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(_LOGO.read_bytes()).decode()


@lru_cache(maxsize=8)
def hero(judul: str, sub: str, tagline: str = "") -> str:
    uri = _logo_uri()
    logo = f'<div class="logo"><img alt="Logo Ungkep Jowo" src="{uri}"></div>' if uri else ""
    tag = f'<div class="sub2">{tagline}</div>' if tagline else ""
    return f'<div class="hero">{logo}<div class="tt"><h1>{judul}</h1><div class="sub">{sub}</div>{tag}</div></div>'
