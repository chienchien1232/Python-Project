# -*- coding: utf-8 -*-
"""TAB TEAMS - 48 doi tuyen + ho so + radar phong cach + AI cluster."""
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, "..")
from helpers import q, load_analytics_csv  # noqa: E402

st.title("🌍 Đội tuyển")

# ---------- bang 48 doi tong hop ----------
df = q("""SELECT t.team_id, t.team_name AS Đội_tuyển,
                 t.manager_name AS HLV,
                 t.fifa_ranking_pre_tournament AS `Hạng_FIFA`,
                 t.confederation AS Liên_đoàn,
                 COALESCE(SUM(CASE WHEN m.home_team_id=t.team_id THEN m.home_score
                                   WHEN m.away_team_id=t.team_id THEN m.away_score END),0) AS Bàn_thắng,
                 COALESCE(SUM(CASE WHEN m.home_team_id=t.team_id THEN m.away_score
                                   WHEN m.away_team_id=t.team_id THEN m.home_score END),0) AS Bàn_thua
          FROM teams t
          LEFT JOIN matches m ON m.home_team_id=t.team_id OR m.away_team_id=t.team_id
          GROUP BY t.team_id""")
df["HS_bàn"] = df["Bàn_thắng"] - df["Bàn_thua"]

cluster_p = os.path.join("..", "..", "data", "processed", "analytics",
                         "team_clusters.csv")
tc = load_analytics_csv("team_clusters.csv") or (
    pd.read_csv(cluster_p) if os.path.exists(os.path.abspath(cluster_p)) else None)
if tc is not None and "team_name" in tc.columns:
    df = df.merge(tc[["team_name", "cluster_label"]], left_on="Đội_tuyển",
                  right_on="team_name", how="left")
    df = df.rename(columns={"cluster_label": "🤖 Nhóm AI"})
    df = df.drop(columns=["team_name"], errors="ignore")

st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- team profile ----------
st.subheader("🔎 Hồ sơ đội tuyển")
team = st.selectbox("Chọn đội", df["Đội_tuyển"].sort_values().tolist())
row = df[df["Đội_tuyển"] == team].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Hạng FIFA", row["Hạng_FIFA"])
c2.metric("Bàn thắng / thủng lưới", f"{row['Bàn_thắng']}–{row['Bàn_thua']}")
c3.metric("Hiệu số", f"{row['HS_bàn']:+d}")
if "🤖 Nhóm AI" in row and pd.notna(row["🤖 Nhóm AI"]):
    c4.success(f"AI: {row['🤖 Nhóm AI']}")

info = q("""SELECT manager_name AS HLV FROM teams WHERE team_name = ?""", (team,))
if not info.empty:
    st.caption(f"Head Coach: {info.iloc[0]['HLV']}")

squad_value = q("""SELECT ROUND(SUM(s.market_value_eur)/1e6,1) v, COUNT(*) n
                   FROM squads_and_players s JOIN teams t ON t.team_id=s.team_id
                   WHERE t.team_name = ?""", (team,))
if not squad_value.empty:
    v = squad_value.iloc[0]
    st.metric("Tổng giá trị đội hình", f"{v['v']:.0f}M € ({v['n']} cầu thủ)")

squad_list = q("""SELECT s.player_name AS Cầu_thủ, s.position AS VT,
                         s.club_team AS CLB, s.caps AS Lượt_trận_DT,
                         s.height_cm AS `Cao(cm)`
                  FROM squads_and_players s JOIN teams t ON t.team_id=s.team_id
                  WHERE t.team_name = ? ORDER BY s.position""", (team,))
with st.expander("📋 Danh sách cầu thủ"):
    st.dataframe(squad_list, use_container_width=True, hide_index=True)

# ---------- radar phong cach ----------
per_match = q("""SELECT AVG(x.possession_pct) possession,
                        AVG(x.total_shots) shots,
                        AVG(x.shots_on_target) sot,
                        AVG(x.corners) corners,
                        AVG(x.saves) saves,
                        AVG(x.fouls) fouls
                 FROM match_team_stats x
                 WHERE x.team_id IN (SELECT team_id FROM teams WHERE team_name=?)
                   AND x.match_id IN (
                       SELECT match_id FROM matches
                       WHERE home_team_id=x.team_id OR away_team_id=x.team_id)""",
              (team,))
league_avg = q("""SELECT AVG(possession_pct) possession, AVG(total_shots) shots,
                         AVG(shots_on_target) sot, AVG(corners) corners,
                         AVG(saves) saves, AVG(fouls) fouls
                  FROM match_team_stats""")
if not per_match.empty:
    axes = ["Kiểm soát bóng", "Sút", "Trúng đích", "Phạt góc", "Cứu thủ", "Phạm lỗi"]
    vals = [float(per_match.iloc[0][c]) for c in
            ("possession", "shots", "sot", "corners", "saves", "fouls")]
    lavg = [float(league_avg.iloc[0][c]) for c in
            ("possession", "shots", "sot", "corners", "saves", "fouls")]
    pct = [round(100 * min(v / max(l, 1e-9), 2.5) / 2.5, 1)
           for v, l in zip(vals, lavg)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pct + [pct[0]], theta=axes + [axes[0]],
                                  fill="toself", name=team,
                                  line=dict(color="#00E676")))
    fig.add_trace(go.Scatterpolar(r=[50] * (len(axes) + 1),
                                  theta=axes + [axes[0]], name="TB giải",
                                  line=dict(color="#888", dash="dot")))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                      title="Radar phong cách chơi (so với TB giải)")
    st.plotly_chart(fig, use_container_width=True)

# ---------- so sanh cum ----------
if tc is not None and "cluster_label" in tc.columns:
    st.subheader("🤖 So sánh đặc trưng các cụm đội tuyển (AI)")
    zcols = [c for c in tc.columns if c not in
             ("team_id", "match_id", "team_name", "home_away", "score",
              "source_page", "cluster", "cluster_label", "topic")]
    if zcols:
        cm = tc.groupby("cluster_label")[zcols[:6]].mean().round(2)
        st.dataframe(cm, use_container_width=True)

import plotly.graph_objects as go  # noqa: E402
