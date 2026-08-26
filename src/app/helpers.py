# -*- coding: utf-8 -*-
"""Ket noi DB dung chung cho cac trang Streamlit."""
import glob
import html as html_lib
import json
import os
import sqlite3

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "data", "db", "wc2026_full.db")
ANALYTICS = os.path.join(ROOT, "data", "processed", "analytics")
FIFA_RAW = os.path.join(ROOT, "data", "raw", "fifa")
FIFA_ID_MAP = os.path.join(ROOT, "data", "processed", "wc2026_player_match", "id_mapping_fifa_to_csv.json")


@st.cache_resource
def get_conn():
    if not os.path.exists(DB):
        st.error("Chưa có database! Chạy lệnh: python src/db/build_db.py")
        return None
    return sqlite3.connect(DB, check_same_thread=False)


def q(sql, params=None):
    con = get_conn()
    if con is None:
        return pd.DataFrame()
    return pd.read_sql(sql, con, params=params or [])


def load_analytics_csv(filename):
    """Doc output cua Nhóm B tu data/processed/analytics/. Tra None neu thieu."""
    path = os.path.join(ANALYTICS, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


# ── Ảnh đội tuyển (flag) từ FIFA CDN ──────────────────────────────────────────
# Ten team theo DB (teams.team_name) -> ma 3 chu cai FIFA (api.fifa.com).
FIFA_TEAM_CODES = {
    "Algeria": "ALG", "Argentina": "ARG", "Australia": "AUS", "Austria": "AUT",
    "Belgium": "BEL", "Bosnia and Herzegovina": "BIH", "Brazil": "BRA",
    "Cabo Verde": "CPV", "Canada": "CAN", "Colombia": "COL", "Congo DR": "COD",
    "Croatia": "CRO", "Curaçao": "CUW", "Curacao": "CUW", "Czechia": "CZE",
    "Côte d'Ivoire": "CIV", "Ecuador": "ECU", "Egypt": "EGY", "England": "ENG",
    "France": "FRA", "Germany": "GER", "Ghana": "GHA", "Haiti": "HAI",
    "IR Iran": "IRN", "Iraq": "IRQ", "Japan": "JPN", "Jordan": "JOR",
    "Korea Republic": "KOR", "South Korea": "KOR", "Mexico": "MEX",
    "Morocco": "MAR", "Netherlands": "NED", "New Zealand": "NZL", "Norway": "NOR",
    "Panama": "PAN", "Paraguay": "PAR", "Portugal": "POR", "Qatar": "QAT",
    "Saudi Arabia": "KSA", "Scotland": "SCO", "Senegal": "SEN",
    "South Africa": "RSA", "Spain": "ESP", "Sweden": "SWE", "Switzerland": "SUI",
    "Tunisia": "TUN", "Türkiye": "TUR", "Turkiye": "TUR", "USA": "USA",
    "Uruguay": "URU", "Uzbekistan": "UZB",
}


def flag_url(team_name):
    """URL anh flag cua quoc gia (FIFA CDN). Tra None neu khong ro ten."""
    if not isinstance(team_name, str):
        return None
    code = FIFA_TEAM_CODES.get(team_name.strip())
    if not code:
        return None
    return f"https://api.fifa.com/api/v3/picture/flags-sq-4/{code}"


def flag_img(team_name, height=18, fallback_emoji="⚽"):
    """The <img> flag inline de nhung vao HTML (fallback emoji khi khong co ma)."""
    url = flag_url(team_name)
    if not url:
        return fallback_emoji
    return (
        f'<img src="{url}" alt="" loading="lazy" '
        f'style="height:{height}px;width:auto;vertical-align:-{round(height * 0.15)}px;'
        f'border-radius:2px;box-shadow:0 1px 4px rgba(0,0,0,0.5);display:inline-block" />'
    )


# ── Ảnh cầu thủ (mặt cầu thủ) từ dữ liệu FIFA thô ────────────────────────────
@st.cache_data(show_spinner=False)
def load_player_photos():
    """Quet JSON FIFA thô + ban do id -> {player_id (str): anh dai dien URL}.

    Nguon: data/raw/fifa/match_*.json (PlayerPicture.PictureUrl)
    Ban do id: data/processed/wc2026_player_match/id_mapping_fifa_to_csv.json
    """
    fifa_to_local = {}
    if os.path.exists(FIFA_ID_MAP):
        try:
            with open(FIFA_ID_MAP, encoding="utf-8") as f:
                fifa_to_local = json.load(f)
        except Exception:
            fifa_to_local = {}

    url_by_fifa_id = {}
    for fp in glob.glob(os.path.join(FIFA_RAW, "match_*.json")):
        try:
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        for side in ("HomeTeam", "AwayTeam"):
            players = (d.get(side) or {}).get("Players") or []
            for p in players:
                fid = p.get("IdPlayer")
                pic = (p.get("PlayerPicture") or {}).get("PictureUrl")
                if fid and pic:
                    url_by_fifa_id[str(fid)] = pic

    photos = {}
    for fid, url in url_by_fifa_id.items():
        lid = fifa_to_local.get(fid)
        if lid:
            photos[str(lid)] = url
    return photos


def player_avatar_html(player_id, player_name, size=120):
    """Anh mat cau thu (crop vung mat tu anh toàn than FIFA - khung anh chuan).

    Fallback: avatar chu cai dau. player_id co the None.
    """
    url = None
    if player_id is not None:
        url = load_player_photos().get(str(player_id))
    initials = "".join(w[0] for w in str(player_name or "?").split()[:2]).upper() or "?"
    border = "border:2px solid rgba(204,255,0,0.45);box-shadow:0 6px 18px rgba(0,0,0,0.55)"
    # Anh FIFA la anh toan than khung chuan (dau nam ~8-20% chieu cao anh).
    # Crop bang CSS: cua so = 25% phia tren anh, phong to 2.7x -> dau chiem ~48% khung.
    img_style = (
        "position:absolute;inset:0;width:100%;height:100%;"
        "object-fit:cover;object-position:50% 0%;"
        "transform:scale(2.7);transform-origin:50% 0%;"
    )
    html_img = (
        f'<div class="player-avatar" style="width:{size}px;height:{size}px;{border}">'
        f'<span class="avatar-fallback" style="font-size:{round(size * 0.34)}px">{html_lib.escape(initials)}</span>'
        + (f'<img src="{url}" alt="" loading="lazy" style="{img_style}" />' if url else "")
        + "</div>"
    )
    return html_img


# ── Ảnh mặt cầu thủ dạng data URI (cho sân pitch Plotly) ──────────────────────
@st.cache_data(show_spinner=False)
def _fetch_face_bytes(url):
    """Tai anh nho (~240px) tu FIFA CDN de giam dung luong. Tra None neu loi."""
    try:
        import urllib.request

        req = urllib.request.Request(
            url + "?io=transform:fill,width:240",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read()
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def player_face_data_uri(player_id, player_name, px=128):
    """Anh MAT cau thu (crop vung dau, giong crop CSS o avatar) thanh data URI.

    Dung cho layout_image cua Plotly (san Best XI). Fallback: avatar chu cai dau
    ve bang PIL. Tra None neu may khong co PIL.
    """
    try:
        import base64
        import io

        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    url = None
    if player_id is not None:
        url = load_player_photos().get(str(player_id))

    img = None
    if url:
        raw = _fetch_face_bytes(url)
        if raw:
            try:
                src = Image.open(io.BytesIO(raw)).convert("RGBA")
                # Anh 240px cua FIFA co nen trong suot -> ghep len nen toi cua app
                bg = Image.new("RGBA", src.size, (17, 22, 18, 255))
                src = Image.alpha_composite(bg, src).convert("RGB")
                w, _h = src.size  # ~240 x ~360
                # Vung mat: hinh vuong 864/2333 = 37.1% be ngang, canh giua, tu dinh
                side = round(w * 0.371)
                x0 = round(w * 0.315)
                img = src.crop((x0, 0, x0 + side, min(side, src.size[1])))
            except Exception:
                img = None

    if img is not None:
        img = img.resize((px, px))
    else:
        # Fallback: avatar chu cai dau
        initials = "".join(w[0] for w in str(player_name or "?").split()[:2]).upper() or "?"
        img = Image.new("RGB", (px, px), (17, 22, 18))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 4, px - 5, px - 5], outline=(204, 255, 0), width=3)
        try:
            fnt = ImageFont.load_default(size=max(12, round(px * 0.32)))
        except Exception:
            fnt = ImageFont.load_default()
        tb = d.textbbox((0, 0), initials, font=fnt)
        d.text(
            ((px - (tb[2] - tb[0])) / 2, (px - (tb[3] - tb[1])) / 2 - tb[1]),
            initials,
            fill=(204, 255, 0),
            font=fnt,
        )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── Bộ icon SVG dung chung (line icons, mau lime, khung vuon bo goc) ─────────
_SVG_ICONS = {
    "ball": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7l4.5 3.3-1.7 5.2H9.2L7.5 10.3 12 7z"/>'
            '<path d="M12 3.5V7M20 10l-3.5.3M17.8 18l-3-2.5M6.2 18l3-2.5M4 10l3.5.3"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/>',
    "arrows": '<path d="M17 4l4 4-4 4"/><path d="M21 8H8"/><path d="M7 20l-4-4 4-4"/><path d="M3 16h13"/>',
    "shield": '<path d="M12 3l7 3v5c0 4.6-3 8.2-7 10-4-1.8-7-5.4-7-10V6l7-3z"/>',
    "glove": '<path d="M7 11V5.5a1.5 1.5 0 0 1 3 0V10M10 10V4.5a1.5 1.5 0 0 1 3 0V10'
             'M13 10V5.5a1.5 1.5 0 0 1 3 0V12"/><path d="M16 12v-1.5a1.5 1.5 0 0 1 3 0V14'
             'a7 7 0 0 1-7 7h-1a7 7 0 0 1-7-7v-3a1.5 1.5 0 0 1 3 0v1"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0V4z"/>'
              '<path d="M7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4"/>',
    "medal": '<circle cx="12" cy="9" r="5"/><path d="M9.5 13.6L8 21l4-2.2L16 21l-1.5-7.4"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.8-4.5 4.3 1.1 6.1L12 16.9 6.6 19.8l1.1-6.1L3.2 9.4l6.1-.8L12 3z"/>',
    "chart": '<path d="M4 20h16"/><path d="M7 16v-5"/><path d="M12 16V6"/><path d="M17 16v-8"/>',
    "cpu": '<rect x="8" y="8" width="8" height="8" rx="1"/><path d="M9 2v3M15 2v3M9 19v3'
           'M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "bolt": '<path d="M13 2L4.5 13.5H11L9.5 22 19 10h-6.5L13 2z"/>',
    "radar": '<circle cx="12" cy="12" r="2"/><circle cx="12" cy="12" r="7"/>'
             '<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/>',
    "money": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v10"/>'
             '<path d="M15 9.5c0-1.4-1.3-2.2-3-2.2s-3 .8-3 2.1c0 2.8 6 1.6 6 4.4 0 1.3-1.3 2.2-3 2.2s-3-.9-3-2.2"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.5-4.5"/>',
    "clipboard": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 2.5h6v3H9z"/>'
                 '<path d="M9 11h6M9 15h6"/>',
    "calendar": '<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M8 3v4M16 3v4M4 11h16"/>',
    "stadium": '<path d="M5 21V9.5L12 5l7 4.5V21"/><path d="M3 21h18M9.5 21v-5h5v5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.2 3.4-5 6.5-5s5.7 1.8 6.5 5"/>'
             '<circle cx="17" cy="9" r="2.5"/><path d="M16 15.2c2.6.3 4.6 1.9 5.3 4.8"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/>'
             '<path d="M12 3.5c2.5 2.3 3.8 5.2 3.8 8.5s-1.3 6.2-3.8 8.5c-2.5-2.3-3.8-5.2-3.8-8.5s1.3-6.2 3.8-8.5z"/>',
    "scale": '<path d="M12 4v16M8 21h8"/><path d="M6 6l-2.8 6a3 3 0 0 0 5.6 0L6 6zM18 8l-2.8 6a3 3 0 0 0 5.6 0L18 8z"/>',
    "spark": '<path d="M12 4l1.5 4L18 9.5 13.5 11 12 15l-1.5-4L6 9.5 10.5 8 12 4z"/>'
             '<path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/>',
    "rocket": '<path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2"/>'
             '<path d="M12 15l-3-3c1.5-4.5 5-8 12-9-1 7-4.5 10.5-9 12z"/><circle cx="14.5" cy="9.5" r="1.5"/>',
    "flame": '<path d="M12 3c1 3-3 4.5-3 8a3 3 0 0 0 6 .2C15 9 18 10 18 13.5A6 6 0 0 1 6 13c0-4 5-6 6-10z"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1'
            'a7 7 0 0 0-2-.9L14 3h-4l-.5 2.9a7 7 0 0 0-2 .9l-2.4-1-2 3.4 2 1.6a7 7 0 0 0 0 2.4'
            'l-2 1.6 2 3.4 2.4-1a7 7 0 0 0 2-.9l2.4 1 2-3.4-2-1.6'
            'a7 7 0 0 0 .1-1.2z"/>',
    "goal": '<path d="M4 19V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v11"/><path d="M4 19h16"/>'
            '<path d="M8 19v-4M12 19v-4M16 19v-4M6 11h12M6 15h12"/>',
    "map": '<path d="M9 4L4 6v14l5-2 6 2 5-2V4l-5 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>',
    "pin": '<path d="M12 21s-6-5.2-6-10a6 6 0 1 1 12 0c0 4.8-6 10-6 10z"/><circle cx="12" cy="11" r="2"/>',
}


def icon_svg(name, size=16):
    """SVG line icon (stroke currentColor) de nhung inline trong HTML."""
    path = _SVG_ICONS.get(name)
    if path is None:
        return ""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


def icon_badge(name, size=34, icon_size=18):
    """Icon trong khung vuon bo goc nen lime mo (style giong FIFA 2026)."""
    svg = icon_svg(name, icon_size)
    if not svg:
        return ""
    return (
        f'<span class="icon-badge" style="width:{size}px;height:{size}px">{svg}</span>'
    )

# ── Column config cho st.dataframe (bang hien dai dong nhat) ──
def cfg_progress(label, vmax=100, vmin=0):
    """Cot diem hien thi thanh tien trinh (0..vmax)."""
    return st.column_config.ProgressColumn(label, min_value=vmin, max_value=vmax,
                                           format="%.1f")

def cfg_money(label):
    """Cot gia tri dinh dang trieu Euro."""
    return st.column_config.NumberColumn(label, format="%.1f")

def cfg_num(label, fmt="%.2f"):
    """Cot so thap phan/nguyen dong nhat."""
    return st.column_config.NumberColumn(label, format=fmt)
