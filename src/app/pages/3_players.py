# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Player Statistics & Profiles."""
import os
import sys
import datetime as dt
import html as html_lib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys_path = os.path.join(ROOT, "src")
app_path = os.path.join(ROOT, "src", "app")
for p in [app_path, sys_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers import q, load_analytics_csv, load_similarity_matrix  # noqa: E402
from media_ui import country_palette, flag_image, player_portrait, render_photo_story, static_url  # noqa: E402

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Players & Statistics | WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

# ── Inject custom CSS ──────────────────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def clean_name(val):
    if not isinstance(val, str):
        return str(val) if val is not None else ""
    return (
        val.replace("Adrin", "Adrian")
           .replace("Andrs", "Andres")
           .replace("Damin", "Damian")
           .replace("Curaao", "Curacao")
           .replace("Cte d'Ivoire", "Côte d'Ivoire")
           .replace("Trkiye", "Türkiye")
           .replace("Lionel Andrs Messi", "Lionel Messi")
           .replace("Rodrigo Rodri", "Rodri")
           .replace("Kylian Mbappe", "Kylian Mbappé")
    )


# ── Top Navigation Bar ────────────────────────────────────────────────────────
from navigation import render_navigation
from table_ui import data_table
render_navigation('Players')

render_photo_story(
    "PLAYER PERFORMANCE ARCHIVE / 2026",
    "THE PLAYERS.",
    "BEHIND DATA.",
    "Profiles, roles and the performances that shaped the tournament.",
    index="1,248 PLAYERS",
    page="players",
)

st.markdown(
    '<div class="vc-subnav-anchor" aria-hidden="true">players-subnav</div>'
    '<style>'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div [data-testid="stHorizontalBlock"]{'
    'max-width:1100px;margin:6px auto 26px !important;padding:10px 34px;'
    'border:1px solid rgba(255,255,255,.14);border-radius:999px;'
    'background:rgba(8,8,10,.72);backdrop-filter:blur(18px) saturate(130%);'
    '-webkit-backdrop-filter:blur(18px) saturate(130%);'
    'box-shadow:0 14px 44px rgba(0,0,0,.45);'
    'display:flex !important;align-items:center;gap:6px;}'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div [data-testid="stHorizontalBlock"] [data-testid="column"]{'
    'display:flex !important;align-items:center;justify-content:center;}'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div [data-testid="stPageLink-NavLink"]{'
    'border:0 !important;background:none !important;box-shadow:none !important;'
    'color:#cfcfc9 !important;font-size:11px;font-weight:700;letter-spacing:.9px;'
    'padding:10px 12px !important;text-align:center;border-radius:999px;white-space:nowrap;}'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div [data-testid="stPageLink-NavLink"]:hover{'
    'background:none !important;color:#fff !important;}'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div [data-testid="stPageLink-NavLink"][aria-disabled="true"]{'
    'color:#fff !important;}'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div .wc-nav-fallback{'
    'display:block;padding:8px 2px;color:#aaa !important;font-size:11px;font-weight:500;'
    'letter-spacing:.7px;text-transform:uppercase;text-decoration:none !important;text-align:center;}'
    '@media(max-width:750px){'
    'div[data-testid="stElementContainer"]:has(.vc-subnav-anchor) + div [data-testid="stHorizontalBlock"]{'
    'margin:0 10px 20px !important;border-radius:20px;overflow-x:auto;}}'
    '</style>',
    unsafe_allow_html=True,
)
ws_dir, ws_cmp = st.columns(2, gap="small")
with ws_dir:
    st.markdown('<a class="wc-nav-fallback" href="#player-directory" target="_self">PLAYER DIRECTORY</a>', unsafe_allow_html=True)
with ws_cmp:
    st.markdown('<a class="wc-nav-fallback" href="#player-compare" target="_self">COMPARE PLAYERS + TEAMS</a>', unsafe_allow_html=True)

st.markdown('<div id="player-directory"></div>', unsafe_allow_html=True)


# ── Load Dataset ──────────────────────────────────────────────────────────────
df = q("SELECT * FROM v_player_season ORDER BY minutes DESC")
if df.empty:
    st.error("Player season database view not found.")
    st.stop()

df["player_name"] = df["player_name"].apply(clean_name)
df["team"] = df["team"].apply(clean_name)

clusters = load_analytics_csv("player_clusters.csv")
mv = load_analytics_csv("market_value_estimates.csv")
if clusters is not None:
    clusters["player_id"] = clusters["player_id"].astype(str)
if mv is not None:
    mv["player_id"] = mv["player_id"].astype(str)


# ── Hero & KPI Summary ────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span>PLAYER DIRECTORY</div>'
    '<div class="wc-hero-dates">1,248 SQUAD MEMBERS · COMPREHENSIVE PER-90 RATINGS</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">PLAYER</span>'
    '<span class="title-lime">STATISTICS.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Browse in-depth player statistics normalized per 90 minutes. Inspect positional percentile radar charts, '
    'AI-calculated player similarity profiles, and post-tournament market value estimations.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)
tot_p = len(df)
top_scorer = "Kylian Mbappé (10G)"
top_assists = "Lionel Messi (5A)"

st.markdown(
    '<div class="kpi-row-container" style="margin-bottom:28px">'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{tot_p:,}</div><div class="kpi-sport-label">PLAYERS LOGGED</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">Mbappé</div><div class="kpi-sport-label">GOLDEN BOOT (10 GOALS)</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num"> Rodri</div><div class="kpi-sport-label">GOLDEN BALL (MVP)</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">48</div><div class="kpi-sport-label">NATIONAL SQUADS</div></div>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Master Per-90 Table & Filters ─────────────────────────────────────────────
st.markdown("<div class='section-header'>Master Player Per-90 Statistics</div>", unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 1.6])
with col_f1:
    pos_options = ["All Positions"] + sorted(df["position"].dropna().unique().tolist())
    sel_pos = st.selectbox("Position", pos_options)
with col_f2:
    team_options = ["All Teams"] + sorted(df["team"].dropna().unique().tolist())
    sel_team = st.selectbox("National Team", team_options)
with col_f3:
    search_q = st.text_input(" Search Player Name:")

min_apps = st.slider("Minimum Matches Played", 0, int(df["matches_played"].max()), 2)

view = df[df["matches_played"] >= min_apps].copy()
if sel_pos != "All Positions":
    view = view[view["position"] == sel_pos]
if sel_team != "All Teams":
    view = view[view["team"] == sel_team]
if search_q:
    view = view[view["player_name"].str.contains(search_q, case=False, na=False)]

if clusters is not None and "cluster_label" in clusters.columns:
    view = view.merge(clusters[["player_id", "cluster_label"]], on="player_id", how="left")
    view = view.rename(columns={"cluster_label": "AI Tactical Role"})

show_cols = [
    "player_name", "position", "team", "matches_played", "minutes",
    "goals_p90", "assists_p90", "shots_p90", "passes_p90",
    "pass_accuracy_pct", "tackles_p90", "interceptions_p90", "clearances_p90"
]
if "AI Tactical Role" in view.columns:
    show_cols.append("AI Tactical Role")

show_cols = [c for c in show_cols if c in view.columns]
display_view = view[show_cols].copy()
display_view.columns = [c.replace("_p90", "/90").replace("_", " ").title() for c in display_view.columns]

data_table(display_view, width="stretch", height=320, label="Player performance index")


# ── Detailed Player Dossier Profile ───────────────────────────────────────────
st.markdown("<div class='section-header'>Detailed Player Profile &amp; Radar</div>", unsafe_allow_html=True)

player_list = sorted(df["player_name"].unique().tolist())
default_idx = player_list.index("Kylian Mbappé") if "Kylian Mbappé" in player_list else 0

sel_pname = st.selectbox("Select Player to inspect complete profile:", player_list, index=default_idx)

if sel_pname:
    p = df[df["player_name"] == sel_pname].iloc[0]
    pid = str(p["player_id"])
    p_team = p["team"]
    p_pos = str(p["position"])
    p_flag_img = flag_image(p_team, class_name="team-flag-photo")

    # Detailed metadata from players table
    info = q("SELECT club_team, date_of_birth, height_cm, caps, market_value_eur FROM players WHERE CAST(player_id AS TEXT) = ?", (pid,))
    club = "-"
    mv_meur = 0.0
    caps = "-"
    height = "-"
    dob_txt, age_txt, h_m = "-", "", "-"
    if not info.empty:
        r_info = info.iloc[0]
        club = clean_name(r_info["club_team"]) if pd.notna(r_info["club_team"]) else "-"
        caps = str(int(float(r_info["caps"]))) if pd.notna(r_info["caps"]) else "-"
        height = f"{int(r_info['height_cm'])} cm" if pd.notna(r_info["height_cm"]) else "-"
        mv_meur = (float(r_info["market_value_eur"]) / 1e6) if pd.notna(r_info["market_value_eur"]) else 0.0
        if pd.notna(r_info.get("date_of_birth")):
            try:
                dob = dt.date.fromisoformat(str(r_info["date_of_birth"])[:10])
                dob_txt = dob.strftime("%d %b %Y")
                age_txt = f"({int((dt.date.today() - dob).days // 365.25)} years)"
            except ValueError:
                dob_txt = str(r_info["date_of_birth"])
        if pd.notna(r_info.get("height_cm")):
            h_m = f"{float(r_info['height_cm']) / 100:.2f} m"

    cluster_badge = "Standard Profile"
    if clusters is not None:
        hit = clusters[clusters["player_id"] == pid]
        if not hit.empty:
            cluster_badge = hit.iloc[0].get("cluster_label", "Standard Profile")

    POS_FULL = {"FWD": "FORWARD (FW)", "MID": "MIDFIELDER (MF)", "DEF": "DEFENDER (DF)", "GK": "GOALKEEPER (GK)"}
    POS_SHORT = {"FWD": "FW", "MID": "MF", "DEF": "DF", "GK": "GK"}
    pos_full = POS_FULL.get(p_pos, p_pos)
    pos_short = POS_SHORT.get(p_pos, p_pos)
    TAGLINES = {
        "FWD": "CLINICAL. DECISIVE. ALWAYS A THREAT.",
        "MID": "CONTROL. VISION. RELENTLESS ENGINE.",
        "DEF": "COMMANDING. RELENTLESS. IMPENETRABLE.",
        "GK": "COMMANDING. FEARLESS. THE LAST LINE.",
    }
    tagline = TAGLINES.get(p_pos, "DISCIPLINE. PRECISION. BIG-MOMENT PLAYER.")
    palette_code, palette_primary, palette_secondary, palette_primary_rgb, palette_secondary_rgb = country_palette(p_team)
    stadium_src = html_lib.escape(static_url("hero-players-v1.png"), quote=True)
    profile_vars = (
        f'--pp-primary:{palette_primary};--pp-secondary:{palette_secondary};'
        f'--pp-primary-rgb:{palette_primary_rgb};--pp-secondary-rgb:{palette_secondary_rgb};'
    )

    # ── Player Hero Showcase Card (editorial profile, FIFA portrait reused) ──
    st.markdown(
        '<style>'
        '.pp-hero{display:grid;grid-template-columns:minmax(0,48fr) minmax(0,52fr);gap:0;'
        'min-height:clamp(620px,78vh,820px);background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);'
        'border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;overflow:hidden;margin-bottom:22px;isolation:isolate;'
        'opacity:0;animation:pp-profile-in .8s cubic-bezier(.22,.61,.36,1) .04s both;}'
        '.pp-photo{position:relative;min-height:clamp(620px,78vh,820px);background:#080b10;overflow:hidden;isolation:isolate;}'
        '.pp-photo-stadium{position:absolute;inset:-3%;width:106%;height:106%;object-fit:cover;object-position:center;filter:brightness(.24) saturate(.5) blur(3px);opacity:.9;z-index:0;transform:scale(1.03);}'
        '.pp-photo-glow{position:absolute;inset:-10%;z-index:1;pointer-events:none;'
        'background:radial-gradient(circle at 48% 34%,rgba(var(--pp-primary-rgb),.24) 0%,rgba(var(--pp-primary-rgb),.14) 23%,transparent 62%),'
        'radial-gradient(circle at 45% 88%,rgba(var(--pp-secondary-rgb),.11),transparent 66%);'
        'animation:pp-glow-drift 14s ease-in-out infinite alternate;}'
        '.pp-photo::before{content:"";position:absolute;inset:0;z-index:2;pointer-events:none;'
        'background:linear-gradient(90deg,rgba(0,0,0,.10),transparent 54%,rgba(4,6,9,.68)),linear-gradient(180deg,rgba(4,6,9,.16),transparent 34%,rgba(4,6,9,.76));}'
        '.pp-photo .player-portrait{position:absolute;left:2%;right:2%;top:0;bottom:0;width:auto !important;height:auto !important;'
        'border:none !important;display:block;overflow:visible;background:transparent;z-index:3;animation:pp-photo-in .78s cubic-bezier(.22,.61,.36,1) .10s both;}'
        '.pp-photo .player-portrait img{width:100%;height:100%;object-fit:cover;object-position:center top;transform:scale(1.35);'
        'transform-origin:center top;filter:none !important;image-rendering:auto;-webkit-backface-visibility:hidden;backface-visibility:hidden;'
        'transition:opacity .6s ease,transform .7s cubic-bezier(.22,.61,.36,1);}'
        '.pp-photo-num{position:absolute;top:6px;left:14px;font-size:120px;font-weight:900;line-height:1;'
        'color:rgba(255,255,255,0.13);letter-spacing:-4px;pointer-events:none;z-index:4;}'
        '.pp-photo-name{position:absolute;left:16px;bottom:120px;writing-mode:vertical-rl;transform:rotate(180deg);'
        'font-size:11px;font-weight:700;letter-spacing:5px;color:rgba(255,255,255,0.68);text-transform:uppercase;z-index:4;}'
        '.pp-photo-motto{position:absolute;left:36px;bottom:44px;font-size:10px;font-weight:600;letter-spacing:3px;'
        'color:rgba(255,255,255,0.48);text-transform:uppercase;line-height:2;z-index:4;}'
        '.pp-info{padding:clamp(30px,4vw,54px) clamp(24px,3.2vw,48px) 30px;display:flex;flex-direction:column;justify-content:center;'
        'background:linear-gradient(90deg,rgba(var(--pp-primary-rgb),.10),#0e0e0e 42%,#0e0e0e 100%);animation:pp-info-in .78s cubic-bezier(.22,.61,.36,1) .20s both;}'
        '.pp-flag .team-flag-photo{position:relative;width:46px;height:32px;display:inline-block;overflow:hidden;border-radius:3px;}'
        '.pp-name{font-size:clamp(38px,4.2vw,64px);font-weight:900;color:#fff;line-height:1.02;margin:12px 0 10px;letter-spacing:-1.2px;overflow-wrap:anywhere;}'
        '.pp-sub{font-size:12px;font-weight:700;letter-spacing:3.5px;color:#a7abb3;text-transform:uppercase;}'
        '.pp-sub .pp-sep{color:#fff;margin:0 10px;}'
        '.pp-quote{margin:18px 0;padding:14px 0;border-top:1px solid rgba(255,255,255,0.09);'
        'border-bottom:1px solid rgba(255,255,255,0.09);font-size:11px;letter-spacing:2.5px;color:#8a8f98;}'
        '.pp-stats{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:18px;}'
        '.pp-stat{text-align:center;padding:6px 4px;border-left:1px solid rgba(255,255,255,0.08);}'
        '.pp-stat:first-child{border-left:none;}'
        '.pp-stat-lbl{font-size:10px;font-weight:700;letter-spacing:1.2px;color:#8a8f98;text-transform:uppercase;margin-bottom:6px;}'
        '.pp-stat-val{font-size:26px;font-weight:900;color:#fff;}'
        '.pp-stat-sub{font-size:11px;color:#8a8f98;margin-top:2px;}'
        '.pp-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}'
        '.pp-meta-cell{padding:6px 12px 2px;border-left:1px solid rgba(255,255,255,0.08);}'
        '.pp-meta-cell:first-child{border-left:none;padding-left:0;}'
        '.pp-meta-lbl{font-size:10px;font-weight:700;letter-spacing:1.2px;color:#8a8f98;text-transform:uppercase;margin-bottom:6px;}'
        '.pp-meta-val{font-size:16px;font-weight:700;color:#fff;}'
        '.pp-meta-sub{font-size:11px;color:#8a8f98;}'
        '@keyframes pp-profile-in{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}'
        '@keyframes pp-photo-in{from{opacity:0;transform:translateX(-24px)}to{opacity:1;transform:translateX(0)}}'
        '@keyframes pp-info-in{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}'
        '@keyframes pp-glow-drift{from{transform:translate3d(-4px,-2px,0)}to{transform:translate3d(4px,6px,0)}}'
        '@media (max-width:900px){.pp-hero{grid-template-columns:1fr;min-height:0;}.pp-photo{min-height:460px;}.pp-info{padding:28px 22px 26px;}.pp-name{font-size:clamp(34px,8vw,48px);}.pp-photo .player-portrait img{transform:scale(1.24);}}'
        '@media (max-width:560px){.pp-photo{min-height:380px;}.pp-photo .player-portrait img{transform:scale(1.15);}.pp-photo-num{font-size:92px;}.pp-photo-name{left:12px;bottom:102px;font-size:9px;}.pp-photo-motto{left:24px;bottom:28px;font-size:9px;}.pp-stats{grid-template-columns:repeat(2,1fr);gap:6px;}.pp-stat{border-left:0;border-top:1px solid rgba(255,255,255,.08);padding-top:10px;}.pp-meta{grid-template-columns:repeat(2,1fr);gap:12px 6px;}.pp-meta-cell{border-left:0;padding-left:0;}.pp-meta-cell:first-child{padding-left:0;}}'
        '@media (prefers-reduced-motion:reduce){.pp-hero,.pp-photo .player-portrait,.pp-info,.pp-photo-glow{animation:none !important;opacity:1 !important;transform:none !important;}.pp-photo .player-portrait img{transition:none !important;}}'
        '</style>'
        f'<section class="pp-hero" data-player-id="{html_lib.escape(pid, quote=True)}" data-team-code="{html_lib.escape(palette_code, quote=True)}" style="{profile_vars}">'
        f'<div class="pp-photo"><img class="pp-photo-stadium" src="{stadium_src}" alt="" aria-hidden="true" loading="eager">'
        '<span class="pp-photo-glow" aria-hidden="true"></span>'
        f'<div class="pp-photo-num">{html_lib.escape(pos_short)}</div>'
        + player_portrait(sel_pname, "player-portrait pp-profile-portrait")
        + f'<div class="pp-photo-name">{html_lib.escape(sel_pname)}</div>'
        f'<div class="pp-photo-motto">PLUS<br>VITE<br>TOUJOURS<br>PLUS LOIN</div></div>'
        f'<div class="pp-info">'
        f'<div class="pp-flag">{p_flag_img}</div>'
        f'<div class="pp-name">{html_lib.escape(sel_pname)}</div>'
        f'<div class="pp-sub">{html_lib.escape(p_team.upper())}<span class="pp-sep">•</span>{html_lib.escape(pos_full)}</div>'
        f'<div class="pp-quote">&ldquo;{tagline}&rdquo;</div>'
        f'<div class="pp-stats">'
        f'<div class="pp-stat"><div class="pp-stat-lbl">Matches</div><div class="pp-stat-val">{int(p["matches_played"])}</div></div>'
        f'<div class="pp-stat"><div class="pp-stat-lbl">Minutes</div><div class="pp-stat-val">{int(p["minutes"])}</div></div>'
        f'<div class="pp-stat"><div class="pp-stat-lbl">Goals / 90</div><div class="pp-stat-val">{float(p.get("goals_p90", 0)):.2f}</div></div>'
        f'<div class="pp-stat"><div class="pp-stat-lbl">Assists / 90</div><div class="pp-stat-val">{float(p.get("assists_p90", 0)):.2f}</div></div>'
        f'<div class="pp-stat"><div class="pp-stat-lbl">Market Valuation</div><div class="pp-stat-val">€{mv_meur:.1f}M</div><div class="pp-stat-sub">Pre-Tournament Value</div></div>'
        f'</div>'
        f'<div class="pp-meta">'
        f'<div class="pp-meta-cell"><div class="pp-meta-lbl">Date of Birth</div><div class="pp-meta-val">{html_lib.escape(dob_txt)}</div><div class="pp-meta-sub">{html_lib.escape(age_txt)}</div></div>'
        f'<div class="pp-meta-cell"><div class="pp-meta-lbl">Height</div><div class="pp-meta-val">{html_lib.escape(h_m)}</div></div>'
        f'<div class="pp-meta-cell"><div class="pp-meta-lbl">Caps</div><div class="pp-meta-val">{html_lib.escape(str(caps))}</div></div>'
        f'<div class="pp-meta-cell"><div class="pp-meta-lbl">Club</div><div class="pp-meta-val" style="font-size:14px">{html_lib.escape(club)}</div></div>'
        f'</div>'
        f'</div>'
        f'</section>',
        unsafe_allow_html=True
    )
    st.markdown('<a class="wc-nav-fallback" href="#player-compare" target="_self">⇄ OPEN PLAYER COMPARISON</a>', unsafe_allow_html=True)
    col_p_left, col_p_right = st.columns([1.15, 1.0], gap="large")

    with col_p_left:
        # Radar Percentile vs Positional Peers (computations unchanged)
        radar_axes = [
            ("shots_p90", "Shots/90", False),
            ("assists_p90", "Assists/90", False),
            ("goals_p90", "Goals/90", False),
            ("dribbles_p90", "Dribbles/90", True),
            ("tackles_p90", "Tackles/90", False),
            ("passes_p90", "Passes/90", False),
        ]

        peers = df[(df["position"] == p["position"]) & (df["minutes"] >= 90)].copy()
        if "dribbles_p90" not in peers.columns and "dribbles_attempted" in peers.columns:
            peers["dribbles_p90"] = (
                peers["dribbles_attempted"].fillna(0) / peers["minutes"].replace(0, pd.NA)
            ) * 90
        p_minutes = float(p["minutes"]) if pd.notna(p["minutes"]) and float(p["minutes"]) > 0 else 0.0
        p_drib = (float(p.get("dribbles_attempted") or 0) / p_minutes * 90) if p_minutes > 0 else 0.0

        r_vals = []
        labels_r = []

        for col_k, lbl, derived in radar_axes:
            if col_k in peers.columns:
                if derived:
                    p_val = p_drib
                elif col_k in p and pd.notna(p[col_k]):
                    p_val = float(p[col_k])
                else:
                    continue
                pctv = round(100.0 * (peers[col_k].fillna(0) <= p_val).mean(), 1)
                r_vals.append(pctv)
                labels_r.append(lbl)

        with st.container(border=True):
            st.markdown(
                f'<div class="pp-panel-head"><span class="pp-dot"></span>'
                f'PERCENTILE VS {html_lib.escape(p_pos)} PEERS (MIN 90 MINS)'
                f'<span class="pp-year">/ 2026</span></div>',
                unsafe_allow_html=True,
            )
            if r_vals:
                fig_p_radar = go.Figure()
                fig_p_radar.add_trace(go.Scatterpolar(
                    r=r_vals + [r_vals[0]],
                    theta=labels_r + [labels_r[0]],
                    fill="toself",
                    # Use the same muted aqua/sand pair as the team radar so
                    # the analytical views remain visually consistent.
                    fillcolor="rgba(168, 218, 220, 0.22)",
                    name=sel_pname,
                    line=dict(color="#a8dadc", width=2.5),
                    marker=dict(color="#a8dadc", size=5),
                ))
                fig_p_radar.add_trace(go.Scatterpolar(
                    r=[50] * (len(labels_r) + 1),
                    theta=labels_r + [labels_r[0]],
                    name=f"{p_pos} Peer Average",
                    line=dict(color="#d7c3a3", dash="dash", width=1.5),
                ))
                fig_p_radar.update_layout(
                    paper_bgcolor="#000000",
                    plot_bgcolor="#000000",
                    font=dict(family="Inter, sans-serif", color="#a7abb3", size=11),
                    polar=dict(
                        bgcolor="#000000",
                        radialaxis=dict(visible=True, range=[0, 100],
                                        gridcolor="rgba(255,255,255,0.10)",
                                        linecolor="rgba(255,255,255,0.12)",
                                        tickfont=dict(color="#6b7280", size=9)),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.10)",
                                         linecolor="rgba(255,255,255,0.12)"),
                    ),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.22,
                                xanchor="center", x=0.5, font=dict(size=10)),
                    margin=dict(l=35, r=35, t=20, b=50),
                    height=350,
                )
                st.plotly_chart(fig_p_radar, width="stretch")
            else:
                st.info("Not enough peer data for radar.")

    with col_p_right:
        # AI Player Similarity Top 5 (computations unchanged, editorial rows)
        with st.container(border=True):
            st.markdown(
                '<div class="pp-panel-head"><span class="pp-dot"></span>'
                'AI PLAYER SIMILARITY (TOP 5 MATCHES)'
                '<span class="pp-year">/ 2026</span></div>',
                unsafe_allow_html=True,
            )
            sim = load_similarity_matrix()
            if sim is not None:
                try:
                    target = next((x for x in sim.index if f"#{pid}" in x or x == sel_pname), None)
                    if target:
                        top5 = sim.loc[target].drop(target, errors="ignore").sort_values(ascending=False).head(5)
                        sim_rows = ""
                        for nm, sval in top5.items():
                            clean_target_name = clean_name(nm.split(" #")[0])
                            pct_sim = round(min(max(float(sval), 0.0), 1.0) * 100, 1)
                            bar_w = min(max(float(sval), 0.0), 1.0) * 100
                            sim_rows += (
                                '<div class="pp-sim-row">'
                                '<span class="pp-sim-avatar">'
                                + player_portrait(clean_target_name, "player-portrait")
                                + '</span>'
                                f'<span class="pp-sim-name">{html_lib.escape(clean_target_name)}</span>'
                                f'<span class="pp-sim-pct">{pct_sim:.1f}%</span>'
                                '<span class="pp-sim-lbl">similarity</span>'
                                f'<span class="pp-sim-bar"><i style="width:{bar_w:.1f}%"></i></span>'
                                '</div>'
                            )
                        st.markdown(
                            '<style>'
                            '.pp-panel-head{display:flex;align-items:center;gap:9px;'
                            'font-size:13px;font-weight:800;letter-spacing:1.6px;color:#f3f2ed;'
                            'text-transform:uppercase;margin-bottom:14px;}'
                            '.pp-dot{width:8px;height:8px;border-radius:50%;background:#fff;flex:0 0 auto;}'
                            '.pp-year{margin-left:auto;font-size:10px;font-weight:600;letter-spacing:1px;color:#6b7280;}'
                            '.pp-sim-row{display:grid;grid-template-columns:36px minmax(0,1fr) auto auto minmax(0,130px);'
                            'align-items:center;gap:10px;padding:9px 2px;border-bottom:1px solid rgba(255,255,255,0.06);}'
                            '.pp-sim-row:last-child{border-bottom:none;}'
                            '.pp-sim-avatar .player-portrait{width:36px !important;height:36px !important;'
                            'border-radius:50% !important;border:1px solid rgba(255,255,255,0.15) !important;'
                            'display:block;font-size:11px;}'
                            '.pp-sim-name{font-size:13.5px;font-weight:600;color:#e8e8e3;'
                            'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
                            '.pp-sim-pct{font-size:13.5px;font-weight:800;color:#fff;}'
                            '.pp-sim-lbl{font-size:11.5px;color:#8a8f98;}'
                            '.pp-sim-bar{display:block;height:5px;background:rgba(255,255,255,0.09);border-radius:3px;overflow:hidden;}'
                            '.pp-sim-bar i{display:block;height:100%;background:#fff;border-radius:3px;}'
                            '</style>' + sim_rows,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("No direct similarity vector found for this player.")
                except Exception:
                    st.info("Similarity matrix loading error.")
            else:
                st.info("Run `python src/analytics/player_similarity.py` to generate similarity vectors.")

        # Post-Tournament Market Value Estimation
        if mv is not None:
            mrow = mv[mv["player_id"] == pid]
            if not mrow.empty:
                r_mv = mrow.iloc[0]
                st.markdown("<div class='section-header' style='font-size:20px'>Market Value AI Regression</div>", unsafe_allow_html=True)
                v_pre = float(r_mv["current_value"]) / 1e6
                v_post = float(r_mv["predicted_post_value"]) / 1e6
                chg = float(r_mv["change_pct"])

                st.markdown(
                    f'<div style="background:#141414;border:0;border-top:1px solid rgba(255,255,255,0.18);border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:18px">'
                    f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;text-align:center">'
                    f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">PRE-TOURNAMENT</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#FFFFFF">€{v_pre:.1f}M</div></div>'
                    f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">PREDICTED POST</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#e8e8e3">€{v_post:.1f}M</div></div>'
                    f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">NET CHANGE</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:{"#00e676" if chg>=0 else "#ff5252"}">{chg:+.1f}%</div></div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )


# ── Player & Team Comparison (always visible on this page) ────────────────────
st.markdown('<div id="player-compare"></div>', unsafe_allow_html=True)
st.markdown("<div class='section-header'>Player & Team Comparison</div>", unsafe_allow_html=True)
from compare_ui import render_compare_workspace

render_compare_workspace()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
