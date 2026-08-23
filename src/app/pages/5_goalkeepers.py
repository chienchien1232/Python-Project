# -*- coding: utf-8 -*-
"""Trang 5 — Thủ môn."""
import sys

import streamlit as st

sys.path.insert(0, "..")
from helpers import q

st.title("🧤 Thủ môn")

df = q("""SELECT player_name AS Thủ_môn, team AS Đội,
                 SUM(minutes_played) AS Phút,
                 SUM(saves) AS Cứu_thủ,
                 SUM(shots_faced) AS Sút_hướng_khung_thành,
                 SUM(goals_conceded_on_pitch) AS Thủng_lưới,
                 SUM(clean_sheet) AS Trắng_lưới_trận
          FROM goalkeeper_match_stats
          GROUP BY player_id
          ORDER BY Cứu_thủ DESC""")
if df.empty:
    st.info("Chưa có dữ liệu GK.")
else:
    df["% cứu thủ"] = (100 * df["Cứu_thủ"] /
                       (df["Cứu_thủ"] + df["Thủng_lưới"]).replace(0, 1)).round(1)
    top = df.head(20)
    c1, c2 = st.columns(2)
    c1.metric("GK có pha cứu thủ cao nhất",
              f"{top.iloc[0]['Cứu_thủ']} — {top.iloc[0]['Thủ_môn']}")
    if len(df) > 1:
        best_cs = df.sort_values(["Trắng_lưới_trận", "% cứu thủ"],
                                 ascending=False).iloc[0]
        c2.metric("Trắng lưới nhiều nhất",
                  f"{int(best_cs['Trắng_lưới_trận'])} — {best_cs['Thủ_môn']}")
    st.dataframe(df, use_container_width=True, hide_index=True)
