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
    page_title="Matches & Results | WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

style_path = Path(APP_PATH) / "style.css"
if style_path.exists():
    st.markdown(f"<style>{style_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

render_navigation("Matches")
st.html(Path(APP_PATH) / "match_experience.css")

render_photo_story(
    "MATCH CALENDAR / 2026",
    "TOURNAMENT",
    "MATCHES.",
    "All 104 fixtures and results, arranged as one continuous match programme.",
    index="104 FIXTURES",
    page="matches",
)

all_matches = get_matches()
if all_matches.empty:
    st.markdown('<div class="match-experience match-calendar-mode"></div>', unsafe_allow_html=True)
    st.error("Match data is unavailable. Rebuild the database and reload this page.")
    st.stop()

match_count = len(all_matches)
score_columns = all_matches[["Home_Score", "Away_Score"]].apply(pd.to_numeric, errors="coerce")
goals = int(score_columns.fillna(0).sum().sum())
attendance = int(all_matches["Attendance"].fillna(0).sum())
goal_average = goals / max(match_count, 1)

st.markdown(render_calendar_hero(match_count), unsafe_allow_html=True)
st.markdown(render_stat_strip(match_count, goals, goal_average, attendance), unsafe_allow_html=True)

st.markdown(
    '<div class="match-filter-title"><div><span>CALENDAR CONTROL</span>'
    '<h2>FILTER MATCHES</h2></div><span>FIND A FIXTURE / ENTER ITS STORY</span></div>',
    unsafe_allow_html=True,
)

stages = ["All Stages"] + sorted(all_matches["Stage"].dropna().astype(str).unique().tolist())
teams = ["All Teams"] + sorted(
    set(all_matches["Home_Team"].dropna()) | set(all_matches["Away_Team"].dropna())
)

filter_stage, filter_team, filter_tag, filter_search = st.columns([1, 1, 1, 1.35])
with filter_stage:
    selected_stage = st.selectbox("Stage", stages)
with filter_team:
    selected_team = st.selectbox("Team", teams)
with filter_tag:
    selected_tag = st.selectbox("Match Tag", ["All Matches", "Anomalous Only", "Regular Only"])
with filter_search:
    search_term = st.text_input("Search", placeholder="Search team, city or stadium")

anomalous_ids = get_anomaly_ids()
st.markdown('<div class="match-filter-foot"></div>', unsafe_allow_html=True)

filtered = all_matches.copy()
if selected_stage != "All Stages":
    filtered = filtered[filtered["Stage"] == selected_stage]
if selected_team != "All Teams":
    filtered = filtered[
        (filtered["Home_Team"] == selected_team) | (filtered["Away_Team"] == selected_team)
    ]
if search_term.strip():
    searchable = filtered[["Home_Team", "Away_Team", "City", "Stadium"]].fillna("").astype(str)
    mask = searchable.agg(" ".join, axis=1).str.contains(search_term.strip(), case=False, regex=False)
    filtered = filtered[mask]
is_anomalous = filtered["ID"].astype(int).isin(anomalous_ids)
if selected_tag == "Anomalous Only":
    filtered = filtered[is_anomalous]
elif selected_tag == "Regular Only":
    filtered = filtered[~is_anomalous]

st.markdown(
    '<div class="match-results-header"><div><span>FIXTURE INDEX</span><h2>MATCH CALENDAR</h2></div>'
    f'<span>{len(filtered):03d} OF {match_count:03d} MATCHES</span></div>',
    unsafe_allow_html=True,
)

if filtered.empty:
    st.markdown(
        '<div class="match-empty-state">No matches meet the current filters. Adjust the stage, team, tag, or search selection.</div>',
        unsafe_allow_html=True,
    )
else:
    cards = "".join(
        render_match_card(match, int(match["ID"]) in anomalous_ids)
        for _, match in filtered.iterrows()
    )
    st.markdown(f'<div class="match-card-grid">{cards}</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="match-results-header"><div><span>TECHNICAL INDEX</span><h2>ALL FIXTURES</h2></div>'
    '<span>SELECT A ROW TO OPEN ITS MATCH PROGRAMME</span></div>',
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
    fixture_table = fixture_table[["ID", "Date", "Stage", "Home_Team", "Score", "Away_Team", "Stadium", "City", "Attendance"]]
    fixture_table.columns = ["ID", "Date", "Stage", "Home Team", "Score", "Away Team", "Stadium", "City", "Attendance"]
    selection = data_table(
        fixture_table,
        width="stretch",
        height=420,
        label="Filtered fixture index",
        on_select="rerun",
        selection_mode="single-row",
        key="match_fixture_table",
    )
    selected_rows = getattr(getattr(selection, "selection", None), "rows", [])
    if selected_rows:
        selected_match_id = int(fixture_table.iloc[selected_rows[0]]["ID"])
        st.switch_page("pages/7_match_detail.py", query_params={"match_id": selected_match_id})

st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#686865;font-size:10px;letter-spacing:.08em;padding:24px 0;border-top:1px solid #292929'>"
    "WORLDCUP STATS '26 &nbsp;·&nbsp; MATCH CALENDAR &nbsp;·&nbsp; FIFA 2026 DATA ARCHIVE"
    "</div>",
    unsafe_allow_html=True,
)
