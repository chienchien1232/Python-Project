# -*- coding: utf-8 -*-
"""TAB COMPARE - Cau thu vs Cau thu & Doi tuyen vs Doi tuyen."""

import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import q, load_analytics_csv  # noqa: E402

st.title("⚔️ So sánh")

tab_pvp, tab_tvt = st.tabs(["👤 Cầu thủ vs Cầu thủ", "🌍 Đội vs Đội"])

# ================= PLAYER VS PLAYER =================
with tab_pvp:
    df = q("SELECT * FROM v_player_season WHERE minutes >= 90")
    if df.empty:
        st.error("Chưa có DB.")
    else:
        names = df["player_name"].sort_values().tolist()
        c1, c2 = st.columns(2)
        pA = c1.selectbox("Cầu thủ A", names, index=names.index(
            "Lionel Andrés Messi") if "Lionel Andrés Messi" in names else 0)
        pB = c2.selectbox("Cầu thủ B", names,
                          index=names.index("Kylian Mbappé")
                          if "Kylian Mbappé" in names else 1)

        rA = df[df["player_name"] == pA].iloc[0]
        rB = df[df["player_name"] == pB].iloc[0]

        axes = [("goals_p90", "Bàn/90"), ("assists_p90", "Kiến tạo/90"),
                ("shots_p90", "Sút/90"), ("passes_p90", "Chuyền/90"),
                ("tackles_p90", "Tắc/90"), ("interceptions_p90", "Cắt/90"),
                ("clearances_p90", "Phá/90"), ("recoveries_p90", "Thu hồi/90")]

        fig = go.Figure()
        for r, nm, color in ((rA, pA, "#00E676"), (rB, pB, "#2196F3")):
            vals = [round(float(r.get(col, 0) or 0), 2) for col, _ in axes]
            maxes = [max(df[c].fillna(0).max(), 1e-9) for c, _ in axes]
            pct = [round(100 * v / mx, 1) for v, mx in zip(vals, maxes)]
            fig.add_trace(go.Scatterpolar(
                r=pct + [pct[0]], theta=[vn for _, vn in axes] + [axes[0][1]],
                fill="toself", name=nm, line=dict(color=color)))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                          title="So sánh percentile Per-90", height=460)
        st.plotly_chart(fig, use_container_width=True)

        rows = []
        for col, vn in axes:
            va = float(rA.get(col, 0) or 0)
            vb = float(rB.get(col, 0) or 0)
            rows.append({"Chỉ số": vn, pA: round(va, 2), pB: round(vb, 2),
                         "Lệch": round(va - vb, 2)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True,
                     hide_index=True)

        sim_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "data", "processed", "analytics",
            "similarity_matrix.parquet")
        if os.path.exists(os.path.abspath(sim_path)):
            sim = pd.read_parquet(sim_path)
            key_a = next((x for x in sim.index
                          if x.split(" #")[-1] == str(rA["player_id"])), None)
            key_b = next((x for x in sim.index
                          if x.split(" #")[-1] == str(rB["player_id"])), None)
            if key_a and key_b and key_a in sim.columns and key_b in sim.index:
                val = float(sim.loc[key_b, key_a]) * 100
                st.success(f"🤖 Độ tương đồng: **{val:.1f}%**")

# ================= TEAM VS TEAM =================
with tab_tvt:
    teams_list = q("SELECT team_name FROM teams ORDER BY team_name")[
        "team_name"].tolist()
    c1, c2 = st.columns(2)
    tA = c1.selectbox("Đội A", teams_list, index=teams_list.index("Argentina")
                      if "Argentina" in teams_list else 0)
    tB = c2.selectbox("Đội B", teams_list,
                      index=teams_list.index("France")
                      if "France" in teams_list else 1)

    ids = q("""SELECT team_id, team_name FROM teams
               WHERE team_name IN (?, ?)""", (tA, tB))
    id_map = dict(zip(ids["team_name"], ids["team_id"]))

    h2h = q("""SELECT d.date AS Ngày, d.home_team_name AS Đội_nhà,
                      d.home_score AS SN, d.away_score AS SX,
                      d.away_team_name AS Đội_khách, d.stage_name AS Vòng
               FROM matches_detailed d
               WHERE d.home_team_name IN (?, ?) AND d.away_team_name IN (?, ?)
               ORDER BY d.date""", (tA, tB, tA, tB))
    st.subheader("Đối đầu trực tiếp tại giải")
    st.dataframe(h2h, use_container_width=True, hide_index=True)

    st.subheader("Thống kê tập thể cả giải")
    stat = q("""SELECT team_id,
                       ROUND(AVG(possession_pct),1) AS `Kiểm soát %`,
                       ROUND(AVG(total_shots),1) AS `Sút/TB`,
                       ROUND(AVG(shots_on_target),1) AS `Trúng đích/TB`,
                       ROUND(AVG(corners),1) AS `Phạt góc/TB`,
                       SUM(fouls) AS Phạm_lỗi
                FROM match_team_stats WHERE team_id IN (?, ?)
                GROUP BY team_id""", (id_map.get(tA), id_map.get(tB)))
    if not stat.empty:
        stat.insert(0, "Đội", [tA, tB])
        st.dataframe(stat.set_index("Đội").T, use_container_width=True)
