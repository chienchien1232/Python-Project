# -*- coding: utf-8 -*-
"""WorldCup Stats '26 — dedicated digital match programme."""
from __future__ import annotations

import os
import sys
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
APP_PATH = os.path.join(ROOT, "src", "app")
SRC_PATH = os.path.join(ROOT, "src")
for path in (APP_PATH, SRC_PATH):
    if path not in sys.path:
        sys.path.insert(0, path)

from match_data import (  # noqa: E402
    get_anomaly_ids,
    get_match,
    get_match_anomaly_details,
    get_match_events,
    get_match_lineups,
    get_match_stats,
    get_matches,
    get_player_match_stats,
    team_code,
)
from match_ui import (  # noqa: E402
    render_anomaly_panel,
    render_comparison_stats,
    render_detail_hero,
    render_fixture_navigation,
    render_match_facts,
    render_timeline,
    render_venue,
    safe,
    safe_number,
    section_heading,
)
from media_ui import flag_url, player_portrait, render_photo_story  # noqa: E402
from navigation import nav_link, render_navigation  # noqa: E402
from table_ui import data_table  # noqa: E402


st.set_page_config(
    page_title="Chi tiết Trận đấu | WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

style_path = Path(APP_PATH) / "style.css"
if style_path.exists():
    st.markdown(f"<style>{style_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

render_navigation("Trận đấu")
st.html(Path(APP_PATH) / "match_experience.css")


def render_not_found(message: str) -> None:
    st.markdown('<div class="match-experience match-detail-mode"></div>', unsafe_allow_html=True)
    nav_link("pages/1_matches.py", "← TOÀN BỘ TRẬN ĐẤU")
    st.markdown(section_heading("404", "KHÔNG TÌM THẤY TRẬN ĐẤU", "not-found"), unsafe_allow_html=True)
    st.markdown(f'<div class="match-empty-state">{escape(message)}</div>', unsafe_allow_html=True)


raw_match_id = st.query_params.get("match_id")
try:
    match_id = int(raw_match_id)
except (TypeError, ValueError):
    render_not_found("Đường dẫn không chứa mã trận đấu hợp lệ.")
    st.stop()

match = get_match(match_id)
if match is None:
    render_not_found(f"Trận đấu {match_id} không tồn tại trong kho lưu trữ dữ liệu.")
    st.stop()

render_photo_story(
    "BẢNG TIN TRẬN ĐẤU / 2026",
    "TRẬN ĐẤU.",
    "TÁI HIỆN.",
    f'{match["Home_Team"]} đối đầu {match["Away_Team"]}, từ tiếng còi khai cuộc đến những con số cuối cùng.',
    index=f'TRẬN {match_id:02d}',
    page="match-detail",
)

events = get_match_events(match_id)
stats = get_match_stats(match_id)
lineups = get_match_lineups(match_id)
players = get_player_match_stats(match_id)
all_matches = get_matches().reset_index(drop=True)

nav_link("pages/1_matches.py", "← TOÀN BỘ TRẬN ĐẤU")
st.markdown(render_detail_hero(match), unsafe_allow_html=True)
if int(match["ID"]) in get_anomaly_ids():
    st.markdown(render_anomaly_panel(get_match_anomaly_details(int(match["ID"]))), unsafe_allow_html=True)
st.markdown(
    '<nav class="detail-subnav" aria-label="Match programme sections">'
    '<a href="#stats">THỐNG KÊ</a>'
    '<a href="#timeline">DIỄN BIẾN</a><a href="#lineups">ĐỘI HÌNH</a>'
    '<a href="#players">CẦU THỦ</a><a href="#facts">ĐIỂM TIN</a><a href="#venue">SÂN THI ĐẤU</a>'
    '</nav>',
    unsafe_allow_html=True,
)

st.markdown(section_heading("01", "THỐNG KÊ TRẬN ĐẤU", "stats"), unsafe_allow_html=True)
st.markdown(render_comparison_stats(match, stats), unsafe_allow_html=True)

st.markdown(section_heading("02", "DIỄN BIẾN TRẬN ĐẤU", "timeline"), unsafe_allow_html=True)
st.markdown(render_timeline(match, events), unsafe_allow_html=True)

st.markdown(section_heading("03", "ĐỘI HÌNH CHIẾN THUẬT", "lineups"), unsafe_allow_html=True)
home_name = str(match["Home_Team"])
away_name = str(match["Away_Team"])
home_code = team_code(home_name, match.get("Home_Code"))
away_code = team_code(away_name, match.get("Away_Code"))
home_flag_url = flag_url(home_name, match.get("Home_Code"))
away_flag_url = flag_url(away_name, match.get("Away_Code"))
flag_col_config = {"Flag": st.column_config.ImageColumn("Cờ", help="Quốc kỳ", width="small")}
if lineups.empty:
    st.markdown('<div class="match-empty-state">Chưa có dữ liệu đội hình cho trận đấu này.</div>', unsafe_allow_html=True)
else:
    home_tab, away_tab = st.tabs([f"{home_code} {home_name}", f"{away_code} {away_name}"])

    def render_team_lineup(team_name: str, team_flag: str) -> None:
        team_rows = lineups[lineups["team_name"] == team_name]
        starters = team_rows[team_rows["is_starting_xi"] == 1][
            ["shirt_number", "player_name", "tactical_position", "minutes_played"]
        ].copy()
        bench = team_rows[team_rows["is_starting_xi"] == 0][
            ["shirt_number", "player_name", "tactical_position", "minutes_played"]
        ].copy()
        starters.columns = ["#", "Cầu thủ", "Vị trí", "Số phút"]
        bench.columns = ["#", "Dự bị", "Vị trí", "Số phút"]
        starters.insert(0, "Flag", team_flag)
        bench.insert(0, "Flag", team_flag)
        data_table(starters, width="stretch", label=f"{team_name} / Đội hình xuất phát",
                   column_config=flag_col_config)
        data_table(bench, width="stretch", label=f"{team_name} / Cầu thủ dự bị",
                   column_config=flag_col_config)

    with home_tab:
        render_team_lineup(home_name, home_flag_url)
    with away_tab:
        render_team_lineup(away_name, away_flag_url)

st.markdown(section_heading("04", "HIỆU SUẤT CẦU THỦ", "players"), unsafe_allow_html=True)
motm = str(match.get("MOTM", "")).strip()
if motm:
    motm_rows = players[players["Player"].str.casefold() == motm.casefold()] if not players.empty else pd.DataFrame()
    details = []
    if not motm_rows.empty:
        motm_stats = motm_rows.iloc[0]
        for column, label in (("Goals", "BÀN THẮNG"), ("Shots", "CÚ SÚT"), ("Passes", "ĐƯỜNG CHUYỀN")):
            if pd.notna(motm_stats.get(column)):
                value = float(motm_stats[column])
                details.append(f'{safe_number(value)} {label}')
        motm_team = safe(motm_stats.get("Team"))
    else:
        motm_team = ""
    st.markdown(
        '<div class="motm-programme"><span>CẦU THỦ XUẤT SẮC NHẤT TRẬN</span><div>'
        f'{player_portrait(motm, "player-portrait is-medium")}<h3>{safe(motm).upper()}</h3><p>{motm_team.upper()}'
        f'{" &nbsp;·&nbsp; " if motm_team and details else ""}{" &nbsp;·&nbsp; ".join(details)}</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )
if players.empty:
    st.markdown('<div class="match-empty-state">Chưa có dữ liệu hiệu suất cầu thủ cho trận đấu này.</div>', unsafe_allow_html=True)
else:
    players = players.copy()
    players.insert(
        0, "Flag",
        players["Team"].map(lambda t: home_flag_url if t == home_name else away_flag_url),
    )
    data_table(players, width="stretch", height=520, label="Bảng chỉ số hiệu suất cầu thủ trong trận",
               column_config=flag_col_config)

st.markdown(section_heading("05", "ĐIỂM TIN TRẬN ĐẤU", "facts"), unsafe_allow_html=True)
st.markdown(render_match_facts(match, stats, players), unsafe_allow_html=True)

st.markdown(section_heading("06", "SÂN THI ĐẤU", "venue"), unsafe_allow_html=True)
st.markdown(render_venue(match), unsafe_allow_html=True)

match_positions = all_matches.index[all_matches["ID"].astype(int) == match_id].tolist()
if match_positions:
    position = match_positions[0]
    previous = all_matches.iloc[position - 1] if position > 0 else None
    following = all_matches.iloc[position + 1] if position + 1 < len(all_matches) else None
    st.markdown(render_fixture_navigation(previous, following), unsafe_allow_html=True)

nav_link("pages/1_matches.py", f"← XEM TOÀN BỘ {len(all_matches)} TRẬN ĐẤU")
st.markdown(
    "<div style='text-align:center;color:#686865;font-size:10px;letter-spacing:.08em;padding:24px 0;border-top:1px solid #292929'>"
    "WORLDCUP STATS '26 &nbsp;·&nbsp; BẢNG TIN TRẬN ĐẤU KỸ THUẬT SỐ"
    "</div>",
    unsafe_allow_html=True,
)
