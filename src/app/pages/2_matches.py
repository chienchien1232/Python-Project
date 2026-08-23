# -*- coding: utf-8 -*-
"""Trang 2 — Trận đấu: lọc + danh sách + timeline."""
import sys

import streamlit as st

sys.path.insert(0, "..")
from helpers import q

st.title("🗓️ Trận đấu")

teams = q("SELECT team_name FROM teams ORDER BY team_name")["team_name"].tolist()
sel = st.multiselect("Lọc đội", teams)
stage = st.selectbox("Vòng đấu", ["Tất cả"] +
                     [r[0] for r in q(
                         "SELECT DISTINCT stage_name FROM matches_detailed").values.tolist()])

sql = """SELECT match_id, date AS Ngày, home_team_name AS Đội_nhà,
                home_score, away_score, away_team_name AS Đội_khách,
                stage_name AS Vòng, result_type AS Kết_quả, attendance AS Khán_giả
         FROM matches_detailed WHERE 1=1"""
params = []
if sel:
    marks = ",".join("?" * len(sel))
    sql += f" AND (home_team_name IN ({marks}) OR away_team_name IN ({marks}))"
    params += sel
if stage != "Tất cả":
    sql += " AND stage_name = ?"
    params.append(stage)

df = q(sql + " ORDER BY date", params)
st.dataframe(df, use_container_width=True, hide_index=True)

mid = st.selectbox("Xem timeline trận:", df["match_id"].tolist() if not df.empty else [])
if mid:
    ev = q("""SELECT minute AS Phút, event_type AS Loại, team AS Đội,
                     player_name AS Cầu_thủ
              FROM match_events WHERE match_id = ? ORDER BY minute""", (str(mid),))
    if ev.empty:
        st.info("Trận này không có sự kiện được ghi nhận.")
    else:
        st.dataframe(ev, use_container_width=True, hide_index=True)
