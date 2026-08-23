# -*- coding: utf-8 -*-
"""TAB HOME - Tong quan giai dau."""
import os

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys_path = os.path.join(ROOT, "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from helpers import q, load_analytics_csv  # noqa: E402

st.set_page_config(page_title="WC2026 Analytics", page_icon="⚽", layout="wide")

css = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
if os.path.exists(css):
    st.markdown(f"<style>{open(css, encoding='utf-8').read()}</style>",
                unsafe_allow_html=True)

st.title("🏆 FIFA World Cup 2026 — Tổng quan giải đấu")

# ---------- KPI ----------
kpi = q("""
    SELECT COUNT(*) AS n_matches,
           COALESCE(SUM(home_score+away_score),0) AS goals,
           SUM(CASE WHEN home_score=0 OR away_score=0 THEN 1 ELSE 0 END) AS clean_sheet_matches,
           0 AS yellow, 0 AS red
    FROM matches""").iloc[0]
cards = q("""SELECT
        SUM(CASE WHEN event_type='Yellow Card' THEN 1 ELSE 0 END) AS y,
        SUM(CASE WHEN event_type='Red Card' THEN 1 ELSE 0 END) AS r
     FROM match_events""").iloc[0]
n_players = q("SELECT COUNT(*) c FROM players").iloc[0]["c"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Trận đấu", kpi["n_matches"])
c2.metric("Tổng bàn thắng", kpi["goals"])
c3.metric("Bàn / trận", round(kpi["goals"] / max(kpi["n_matches"], 1), 2))
c4.metric("🟨 Thẻ vàng", int(cards["y"] or 0))
c5.metric("🟥 Thẻ đỏ", int(cards["r"] or 0))
c6.metric("🧤 Lượt sạch lưới", int(kpi["clean_sheet_matches"]))
st.caption(f"Ngôi sao giải: {n_players} cầu thủ · Dữ liệu nguồn: FIFA API + ESPN + FIFA Training Centre")

# ---------- Top 5 rankings ----------
st.subheader("🏅 Bảng xếp hạng nhanh (Top 5)")
rank_sqls = {
    "⚽ Ghi bàn": """SELECT player_name nm, player_team tm, SUM(goals) v
                     FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5""",
    "🎯 Kiến tạo": """SELECT player_name nm, player_team tm, SUM(assists) v
                      FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5""",
    "🔁 Chuyền nhiều nhất": """SELECT player_name nm, player_team tm,
                     SUM(passes) v FROM player_match_stats
                     GROUP BY player_id ORDER BY v DESC LIMIT 5""",
    "🛡️ Tắc + Cắt bóng": """SELECT player_name nm, player_team tm,
                     SUM(tackles)+SUM(interceptions) v
                     FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5""",
}
r1, r2, r3, r4 = st.columns(4)
for col, (title, sql) in zip((r1, r2, r3, r4), rank_sqls.items()):
    d = q(sql)
    d.columns = ["Cầu thủ", "Đội", "Giá trị"]
    col.markdown(f"**{title}**")
    col.dataframe(d, use_container_width=True, hide_index=True)

gks = q("""SELECT g.player_name nm, g.team tm, SUM(g.saves) v
           FROM goalkeeper_match_stats g GROUP BY g.player_id
           ORDER BY v DESC LIMIT 5""")
r5.markdown("**🧤 Cứu thua**")
gk_show = gks.copy()
gk_show.columns = ["Thủ môn", "Đội", "Saves"]
r5.dataframe(gk_show, use_container_width=True, hide_index=True)

# ---------- Charts ----------
st.subheader("📈 Biểu đồ tổng quan")

by_stage = q("""SELECT s.stage_name AS Vòng,
                       SUM(m.home_score+m.away_score) AS Bàn
                FROM matches m JOIN tournament_stages s ON s.stage_id=m.stage_id
                GROUP BY s.stage_id ORDER BY m.match_number""")
fig1 = px.bar(by_stage, x="Vòng", y="Bàn", color="Bàn",
              color_continuous_scale=["#123c25", "#00E676"],
              title="Bàn thắng theo vòng đấu")
fig1.update_layout(showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

ages = q("""SELECT CAST(2026 - CAST(substr(date_of_birth,1,4) AS INT) AS INT) AS Tuổi
            FROM players WHERE date_of_birth IS NOT NULL""")
ages = ages.dropna()
fig2 = px.histogram(ages, x="Tuổi", nbins=15,
                    title="Phân bố độ tuổi cầu thủ dự giải",
                    color_discrete_sequence=["#2196F3"])
st.plotly_chart(fig2, use_container_width=True)

shots_goals = q("""SELECT player_name AS Cầu_thủ, team AS Đội,
                          SUM(shots) AS Sút, SUM(goals) AS Bàn
                   FROM player_match_stats GROUP BY player_id
                   HAVING SUM(shots) >= 3""")
fig3 = px.scatter(shots_goals, x="Sút", y="Bàn", hover_data=["Cầu_thủ"],
                  title="Bàn thắng thực tế vs Số cú sút (thay cho xG — nguồn không công bố)",
                  color_discrete_sequence=["#00E676"])
st.plotly_chart(fig3, use_container_width=True)

# ---------- Best XI preview ----------
st.subheader("⭐ Đội hình tiêu biểu")
xi_p = os.path.join(ROOT, "data", "processed", "analytics", "best_xi.csv")
if os.path.exists(xi_p):
    xi = pd.read_csv(xi_p)
    st.dataframe(xi, use_container_width=True, hide_index=True)
    st.page_link("pages/6_best_xi.py", label="→ Mở Best XI Builder đầy đủ "
                 "(4 chế độ: AI Official · ML Balanced · U23 · Value-for-Money)")
else:
    st.info("Chạy analytics suite (Nhóm B) để tạo đội hình tiêu biểu.")
