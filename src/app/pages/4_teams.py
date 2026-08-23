# -*- coding: utf-8 -*-
"""Trang 4 — Đội tuyển: thành tích + thống kê + cụm phong cách (ML)."""
import os
import sys

import streamlit as st

sys.path.insert(0, "..")
from helpers import q

st.title("🌍 Đội tuyển")

team = st.selectbox("Chọn đội", q(
    "SELECT team_name FROM teams ORDER BY team_name")["team_name"].tolist())
tid = q("SELECT team_id FROM teams WHERE team_name = ?", (team,)).iloc[0]["team_id"]

matches_df = q("""SELECT date AS Ngày, home_team_id, away_team_id,
                         home_score, away_score, result_type AS Kết_quả
                  FROM matches WHERE home_team_id = ? OR away_team_id = ?
                  ORDER BY date""", (tid, tid))


def ketqua(row):
    is_home = row["home_team_id"] == int(tid)
    my, opp = (row["home_score"], row["away_score"]) if is_home \
        else (row["away_score"], row["home_score"])
    return "T" if my > opp else ("H" if my == opp else "B")


if not matches_df.empty:
    matches_df["KQ"] = matches_df.apply(ketqua, axis=1)
    st.dataframe(matches_df[["Ngày", "home_score", "away_score", "KQ", "Kết_quả"]],
                 use_container_width=True, hide_index=True)
    w = (matches_df["KQ"] == "T").sum()
    d = (matches_df["KQ"] == "H").sum()
    l = (matches_df["KQ"] == "B").sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Thắng", w)
    c2.metric("Hòa", d)
    c3.metric("Thua", l)

st.subheader("Thống kê đội")
stats = q("""SELECT ROUND(SUM(possession_pct)/COUNT(*),1) AS Possession_TB,
                    SUM(total_shots) AS Sút, SUM(shots_on_target) AS Trúng_đích,
                    SUM(corners) AS Phạt_góc, SUM(fouls) AS Phạm_lỗi,
                    SUM(offsides) AS Việt_vị, SUM(saves) AS Cứu_thủ_GK
             FROM match_team_stats WHERE team_id = ?""", (tid,))
st.dataframe(stats, use_container_width=True, hide_index=True)

cluster_p = os.path.join("..", "..", "data", "processed", "analytics",
                         "team_clusters.csv")
if os.path.exists(os.path.abspath(cluster_p)):
    import pandas as pd
    tc = pd.read_csv(cluster_p)
    row = tc[tc["team_name"] == team]
    if not row.empty:
        st.success(f"Nhóm phong cách (Machine Learning): "
                   f"Cluster {row.iloc[0]['cluster']}")
