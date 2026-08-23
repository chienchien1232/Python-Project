# -*- coding: utf-8 -*-
"""TAB MATCHES - Trung tam tran dau + chi tiet."""

import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import q  # noqa: E402

st.title("🗓️ Match Center")

stages = ["Tất cả"] + [r[0] for r in q(
    "SELECT DISTINCT stage_name FROM matches_detailed ORDER BY stage_name").values.tolist()]
dates = ["Tất cả"] + [r[0] for r in q(
    "SELECT DISTINCT date FROM matches ORDER BY date").values.tolist()]

c1, c2 = st.columns(2)
stage = c1.selectbox("Vòng đấu", stages)
date = c2.selectbox("Ngày thi đấu", dates)

sql = """SELECT m.match_id AS ID, d.date AS Ngày, d.stage_name AS Vòng,
                d.home_team_name AS Đội_nhà, d.home_score AS SN,
                d.away_score AS SX, d.away_team_name AS Đội_khách,
                d.attendance AS Khán_giả,
                h.team_name AS HLV_nhà, a.team_name AS HLV_khách,
                d.stadium_name AS Sân_vận_động, d.city AS Thành_phố
         FROM matches_detailed d
         JOIN matches m ON m.match_id = d.match_id
         LEFT JOIN teams h ON h.team_name LIKE (
             SELECT manager_name FROM teams WHERE team_name = d.home_team_name)
         LEFT JOIN teams a ON a.team_name LIKE (
             SELECT manager_name FROM teams WHERE team_name = d.away_team_name)
         WHERE 1=1"""
# HLV doc tu bang teams (cot manager_name)
sql = """SELECT m.match_id AS ID, d.date AS Ngày, d.stage_name AS Vòng,
                d.home_team_name AS Đội_nhà, d.home_score AS SN,
                d.away_score AS SX, d.away_team_name AS Đội_khách,
                m.attendance AS Khán_giả,
                th.manager_name AS HLV_nhà, ta.manager_name AS HLV_khách,
                d.stadium_name AS Sân_vận_động, d.city AS Thành_phố
         FROM matches_detailed d
         JOIN matches m ON m.match_id = d.match_id
         JOIN teams th ON th.team_id = m.home_team_id
         JOIN teams ta ON ta.team_id = m.away_team_id
         WHERE 1=1"""
params = []
if stage != "Tất cả":
    sql += " AND d.stage_name = ?"
    params.append(stage)
if date != "Tất cả":
    sql += " AND d.date = ?"
    params.append(date)

df = q(sql + " ORDER BY d.date", params)

# nhan anomalous match: lech possession/shots qua lon so voi toan giai
mts = q("SELECT match_id, team_id, possession_pct, total_shots FROM match_team_stats")
if not mts.empty:
    z_poss = (mts["possession_pct"] - mts["possession_pct"].mean()) \
        / max(mts["possession_pct"].std(), 1e-9)
    anomaly_ids = set(mts.loc[z_poss.abs() > 2.3, "match_id"])
    df["Ghi_chú"] = df["ID"].apply(
        lambda x: "⚡ ANOMALOUS MATCH" if x in anomaly_ids else "")
else:
    df["Ghi_chú"] = ""

st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Match Detail ----------
mid = st.selectbox("🔍 Chọn trận để xem chi tiết:",
                   df["ID"].tolist() if not df.empty else [])
if mid:
    info = df[df["ID"] == mid].iloc[0]
    badge = " <span class='badge-anomaly'>⚡ ANOMALOUS PERFORMANCE</span>" \
        if info.get("Ghi_chú") else ""
    st.markdown(
        f"### {info['Đội_nhà']} {info['SN']} — {info['SX']} {info['Đội_khách']}"
        f"{badge}",
        unsafe_allow_html=True)
    st.caption(f"{info['Vòng']} · {info['Sân_vận_động']}, {info['Thành_phố']} · "
               f"HLV: {info['HLV_nhà']} vs {info['HLV_khách']} · "
               f"Khán giả: {int(info['Khán_giả']):,}" if info['Khán_giả'] else "")

    # team stats side-by-side
    ts = q("""SELECT team_id, possession_pct, total_shots, shots_on_target,
                     corners, fouls, offsides, saves
              FROM match_team_stats WHERE match_id = ?""", (str(mid),))
    if len(ts) == 2:
        labels = ["Kiểm soát bóng %", "Sút", "Sút trúng đích", "Phạt góc",
                  "Phạm lỗi", "Việt vị", "Cứu thủ"]
        home_row = ts.iloc[0]
        away_row = ts.iloc[1]
        for i, lb in enumerate(labels):
            col = ts.columns[i + 1]
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.write(f"**{home_row[col]}**")
            c3.write(f"**{away_row[col]}**")
            c2.write(lb)

    # lineups theo doi
    lu = q("""SELECT l.team_id, l.is_starting_xi, pm.shirt_number,
                     p.player_name, l.tactical_position, l.minutes_played,
                     p.position
              FROM match_lineups l
              LEFT JOIN players p ON p.player_id = l.player_id
              LEFT JOIN player_match_stats pm
                     ON pm.match_id = l.match_id AND pm.player_id = l.player_id
              WHERE l.match_id = ?
              ORDER BY l.team_id, l.is_starting_xi DESC, l.lineup_id""",
            (str(mid),))
    if not lu.empty and "player_name" in lu.columns:
        for tid_val in lu["team_id"].unique():
            sub = lu[lu["team_id"] == tid_val]
            formation = q("""SELECT DISTINCT formation FROM player_match_stats
                             WHERE match_id = ? AND player_team IN (
                                 SELECT team_name FROM teams WHERE team_id = ?)""",
                          (str(mid), str(tid_val)))
            f_str = formation.iloc[0][0] if not formation.empty else "?"
            st.markdown(f"#### Đội hình ({f_str})")
            starters = sub[sub["is_starting_xi"] == 1]
            bench = sub[sub["is_starting_xi"] == 0]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Đá chính**")
                st.dataframe(
                    starters[["shirt_number", "player_name",
                              "tactical_position", "minutes_played"]],
                    use_container_width=True, hide_index=True)
            with c2:
                st.markdown("**Dự bị**")
                st.dataframe(
                    bench[["shirt_number", "player_name",
                           "tactical_position"]],
                    use_container_width=True, hide_index=True)

    # per-player stats
    pm = q("""SELECT player_team AS Đội, shirt_number AS Sốáo,
                     player_name AS Cầu_thủ, position AS VT,
                     minutes_played AS Phút, goals AS Bàn, assists AS KT,
                     shots AS Sút, passes AS Chuyền, accurate_passes AS `Chuyền_xác`,
                     tackles AS Tắc, interceptions AS Cắt, clearances AS Phá,
                     fouls_committed AS Phạm, yellow_cards AS Thẻv, red_cards AS Thẻđ
              FROM player_match_stats WHERE match_id = ?
              ORDER BY minutes_played DESC""", (str(mid),))
    if not pm.empty:
        st.markdown("**Thống kê cầu thủ trong trận**")
        st.dataframe(pm, use_container_width=True, hide_index=True)
