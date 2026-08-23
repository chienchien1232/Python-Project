# -*- coding: utf-8 -*-
"""Trang chu - Tong quan giai dau. Chay: streamlit run src/app/app.py"""
import os
import sqlite3

import plotly.express as px
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "data", "db", "wc2026_full.db")


@st.cache_resource
def get_conn():
    if not os.path.exists(DB):
        st.error("Chưa có database! Chạy lệnh: python src/db/build_db.py")
        return None
    return sqlite3.connect(DB, check_same_thread=False)


def q(sql, params=None):
    con = get_conn()
    return pd.read_sql(sql, con, params=params or []) if con else pd.DataFrame()


st.title("⚽ FIFA World Cup 2026 — Tổng quan")

n_matches = q("SELECT COUNT(*) c FROM matches").iloc[0]["c"]
goals = q("SELECT COALESCE(SUM(home_score)+SUM(away_score),0) g FROM matches").iloc[0]["g"]
n_players = q("SELECT COUNT(*) c FROM players").iloc[0]["c"]
attendance = q("SELECT SUM(attendance) a FROM matches_detailed").iloc[0]["a"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trận đấu", n_matches)
c2.metric("Bàn thắng", goals)
c3.metric("Cầu thủ", n_players)
c4.metric("Tổng khán giả", f"{int(attendance):,}" if attendance else "-")

top = q("""SELECT player_name AS Cầu_thủ, player_team AS Đội,
                  COUNT(*) AS Trận, SUM(goals) AS Bàn,
                  SUM(assists) AS Kiến_tạo, SUM(minutes_played) AS Phút
           FROM player_match_stats WHERE goals > 0
           GROUP BY player_id ORDER BY Bàn DESC LIMIT 10""")
if not top.empty:
    st.subheader("Vua phá lưới")
    st.dataframe(top, use_container_width=True)

daily = q("""SELECT date AS Ngày, SUM(home_score+away_score) AS Bàn
             FROM matches GROUP BY date ORDER BY date""")
if not daily.empty:
    fig = px.bar(daily, x="Ngày", y="Bàn", title="Số bàn theo ngày")
    st.plotly_chart(fig, use_container_width=True)
