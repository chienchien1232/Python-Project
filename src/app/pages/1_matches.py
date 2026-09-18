# -*- coding: utf-8 -*-
"""WorldCup Stats '26 — editorial match calendar."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
APP_PATH = os.path.join(ROOT, "src", "app")
SRC_PATH = os.path.join(ROOT, "src")
for path in (APP_PATH, SRC_PATH):
    if path not in sys.path:
        sys.path.insert(0, path)

from match_data import get_anomaly_ids, get_matches  # noqa: E402
from match_ui import render_calendar_hero, render_match_card, render_stat_strip  # noqa: E402
from media_ui import render_photo_story  # noqa: E402
from navigation import render_navigation  # noqa: E402
from table_ui import data_table  # noqa: E402


st.set_page_config(
    page_title="Trận đấu & Kết quả | WorldCup Stats '26",
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

render_photo_story(
    "LỊCH THI ĐẤU / 2026",
    "TOÀN BỘ",
    "TRẬN ĐẤU.",
    "Tất cả 104 trận đấu và kết quả, được sắp xếp theo trình tự giải đấu.",
    index="104 TRẬN ĐẤU",
    page="matches",
)

all_matches = get_matches()
if all_matches.empty:
    st.markdown('<div class="match-experience match-calendar-mode"></div>', unsafe_allow_html=True)
    st.error("Dữ liệu trận đấu không khả dụng. Vui lòng kiểm tra lại cơ sở dữ liệu và tải lại trang.")
    st.stop()

match_count = len(all_matches)
score_columns = all_matches[["Home_Score", "Away_Score"]].apply(pd.to_numeric, errors="coerce")
goals = int(score_columns.fillna(0).sum().sum())
attendance = int(all_matches["Attendance"].fillna(0).sum())
goal_average = goals / max(match_count, 1)

st.markdown(render_calendar_hero(match_count), unsafe_allow_html=True)
st.markdown(render_stat_strip(match_count, goals, goal_average, attendance), unsafe_allow_html=True)

st.markdown(
    '<div class="match-filter-title"><div><span>BỘ ĐIỀU KHIỂN LỊCH</span>'
    '<h2>LỌC TRẬN ĐẤU</h2></div><span>TÌM KIẾM TRẬN ĐẤU / XEM DIỄN BIẾN CHI TIẾT</span></div>',
    unsafe_allow_html=True,
)

stage_names_vn = {
    "Group Stage": "Vòng bảng",
    "Round of 32": "Vòng 32 đội",
    "Round of 16": "Vòng 16 đội",
    "Quarter-finals": "Tứ kết",
    "Semi-finals": "Bán kết",
    "Third place play-off": "Tranh hạng ba",
    "Final": "Chung kết",
}
raw_stages = sorted(all_matches["Stage"].dropna().astype(str).unique().tolist())
stages = ["Tất cả vòng đấu"] + raw_stages
teams = ["Tất cả đội tuyển"] + sorted(
    set(all_matches["Home_Team"].dropna()) | set(all_matches["Away_Team"].dropna())
)

filter_stage, filter_team, filter_tag, filter_search = st.columns([1, 1, 1, 1.35])
with filter_stage:
    selected_stage = st.selectbox("Vòng đấu", stages, format_func=lambda s: stage_names_vn.get(s, s))
with filter_team:
    selected_team = st.selectbox("Đội tuyển", teams)
with filter_tag:
    selected_tag = st.selectbox("Phân loại", ["Tất cả trận đấu", "Chỉ trận bất thường", "Chỉ trận thông thường"])
with filter_search:
    search_term = st.text_input("Tìm kiếm", placeholder="Tìm đội tuyển, thành phố hoặc sân vận động")

anomalous_ids = get_anomaly_ids()
st.markdown('<div class="match-filter-foot"></div>', unsafe_allow_html=True)

filtered = all_matches.copy()
if selected_stage != "Tất cả vòng đấu":
    filtered = filtered[filtered["Stage"] == selected_stage]
if selected_team != "Tất cả đội tuyển":
    filtered = filtered[
        (filtered["Home_Team"] == selected_team) | (filtered["Away_Team"] == selected_team)
    ]
if search_term.strip():
    searchable = filtered[["Home_Team", "Away_Team", "City", "Stadium"]].fillna("").astype(str)
    mask = searchable.agg(" ".join, axis=1).str.contains(search_term.strip(), case=False, regex=False)
    filtered = filtered[mask]
is_anomalous = filtered["ID"].astype(int).isin(anomalous_ids)
if selected_tag == "Chỉ trận bất thường":
    filtered = filtered[is_anomalous]
elif selected_tag == "Chỉ trận thông thường":
    filtered = filtered[~is_anomalous]

st.markdown(
    '<div class="match-results-header"><div><span>DANH MỤC TRẬN ĐẤU</span><h2>LỊCH THI ĐẤU</h2></div>'
    f'<span>{len(filtered):03d} TRÊN {match_count:03d} TRẬN ĐẤU</span></div>',
    unsafe_allow_html=True,
)

if filtered.empty:
    st.markdown(
        '<div class="match-empty-state">Không có trận đấu nào thỏa mãn bộ lọc hiện tại. Vui lòng điều chỉnh vòng đấu, đội tuyển hoặc từ khóa tìm kiếm.</div>',
        unsafe_allow_html=True,
    )
else:
    cards = "".join(
        render_match_card(match, int(match["ID"]) in anomalous_ids)
        for _, match in filtered.iterrows()
    )
    st.markdown(f'<div class="match-card-grid">{cards}</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="match-results-header"><div><span>BẢNG KỸ THUẬT</span><h2>TOÀN BỘ TRẬN ĐẤU</h2></div>'
    '<span>CHỌN MỘT HÀNG ĐỂ MỞ TRANG DIỄN BIẾN CHI TIẾT</span></div>',
    unsafe_allow_html=True,
)

if not filtered.empty:
    fixture_table = filtered[["ID", "Date", "Stage", "Home_Team", "Home_Score", "Away_Score", "Away_Team", "Stadium", "City", "Attendance"]].copy()
    fixture_table["Score"] = fixture_table.apply(
        lambda row: (
            f'{int(row["Home_Score"])} — {int(row["Away_Score"])}'
            if pd.notna(row["Home_Score"]) and pd.notna(row["Away_Score"]) else "VS"
        ),
        axis=1,
    )
    fixture_table["Stage"] = fixture_table["Stage"].map(lambda s: stage_names_vn.get(s, s))
    fixture_table = fixture_table[["ID", "Date", "Stage", "Home_Team", "Score", "Away_Team", "Stadium", "City", "Attendance"]]
    fixture_table.columns = ["Mã trận", "Ngày", "Vòng đấu", "Đội nhà", "Tỷ số", "Đội khách", "Sân vận động", "Thành phố", "Khán giả"]
    selection = data_table(
        fixture_table,
        width="stretch",
        height=420,
        label="Danh mục trận đấu theo bộ lọc",
        on_select="rerun",
        selection_mode="single-row",
        key="match_fixture_table",
    )
    selected_rows = getattr(getattr(selection, "selection", None), "rows", [])
    if selected_rows:
        selected_match_id = int(fixture_table.iloc[selected_rows[0]]["Mã trận"])
        st.switch_page("pages/7_match_detail.py", query_params={"match_id": selected_match_id})

st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#686865;font-size:10px;letter-spacing:.08em;padding:24px 0;border-top:1px solid #292929'>"
    "WORLDCUP STATS '26 &nbsp;·&nbsp; LỊCH THI ĐẤU &nbsp;·&nbsp; KHO DỮ LIỆU FIFA 2026"
    "</div>",
    unsafe_allow_html=True,
)
