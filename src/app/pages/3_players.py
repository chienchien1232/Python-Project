# -*- coding: utf-8 -*-
"""TAB PLAYERS - Master table Per-90 + ho so + AI Similarity + Market Value."""
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, "..")
from helpers import q, load_analytics_csv  # noqa: E402

st.title("👤 Cầu thủ")

# ---------- master per-90 ----------
df = q("SELECT * FROM v_player_season ORDER BY minutes DESC")
if df.empty:
    st.error("Chưa có DB. Chạy python src/db/build_db.py")
    st.stop()

clusters = load_analytics_csv("player_clusters.csv")
mv = load_analytics_csv("market_value_estimates.csv")

min_apps = st.slider("Tối thiểu số trận", 0, int(df["matches_played"].max()), 3)
search = st.text_input("🔍 Tìm tên:")
view = df[df["matches_played"] >= min_apps].copy()
if search:
    view = view[view["player_name"].str.contains(search, case=False,
                                                 na=False)]
if clusters is not None:
    view = view.merge(clusters[["player_id", "cluster_label"]],
                      on="player_id", how="left")
    view = view.rename(columns={"cluster_label": "🤖 Vai trò AI"})

show_cols = ["player_name", "position", "team", "matches_played", "minutes",
             "goals_p90", "assists_p90", "shots_p90", "passes_p90",
             "pass_accuracy_pct", "tackles_p90", "interceptions_p90",
             "clearances_p90"]
show_cols = [c for c in show_cols if c in view.columns]
st.dataframe(view[show_cols], use_container_width=True, hide_index=True)

# ---------- profile ----------
st.subheader("🔎 Hồ sơ cầu thủ")
pname = st.selectbox("Chọn cầu thủ:", df["player_name"].sort_values().tolist())
p = df[df["player_name"] == pname].iloc[0]
pid = str(p["player_id"])

c1, c2, c3 = st.columns(3)
c1.metric("Vị trí", p["position"])
c2.metric("Phút thi đấu", int(p["minutes"]))
c3.metric("Trận (đá chính)", f"{int(p['matches_played'])} ({int(p.get('appearances', 0))})")

# thong tin ca nhan tu players + squads
info = q("""SELECT p.club_team, s.date_of_birth, s.height_cm, s.caps,
                   s.market_value_eur
            FROM players p LEFT JOIN squads_and_players s
              ON s.player_id = p.player_id WHERE p.player_id = ?""", (pid,))
club, foot_note = "", ""
if not info.empty:
    r = info.iloc[0]
    club = r["club_team"] or "-"
    mv_meur = (float(r["market_value_eur"]) / 1e6) if pd.notna(r["market_value_eur"]) else None

c1.write(f"**CLB:** {club}")
if mv_meur is not None:
    c2.write(f"**Giá trị hiện tại:** {mv_meur:.1f}M €")

# ML cluster label
label = None
if clusters is not None:
    hit = clusters[clusters["player_id"] == pid]
    if not hit.empty:
        label = hit.iloc[0].get("cluster_label")
        st.success(f"🤖 ML Cluster: **{label}**")

# radar percentile cung vi tri
radar_axes = [("goals_p90", "Bàn/90"), ("assists_p90", "Kiến tạo/90"),
              ("shots_p90", "Sút/90"), ("passes_p90", "Chuyền/90"),
              ("tackles_p90", "Tắc/90"), ("interceptions_p90", "Cắt/90"),
              ("clearances_p90", "Phá/90"), ("recoveries_p90", "Thu hồi/90")]
peers = df[(df["position"] == p["position"]) & (df["minutes"] >= 90)]
fig = go.Figure()
r_vals, labels_r = [], []
for col, vn in radar_axes:
    if col in peers.columns:
        pctv = round(100 * (peers[col] < p[col]).mean(), 1)
        r_vals.append(pctv)
        labels_r.append(vn)
fig.add_trace(go.Scatterpolar(r=r_vals + [r_vals[0]],
                              theta=labels_r + [labels_r[0]],
                              fill="toself", name=pname,
                              line=dict(color="#00E676")))
fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                  title=f"Percentile so với {p['position']} cùng vị trí",
                  height=420)
st.plotly_chart(fig, use_container_width=True)

# AI similarity top5
sim_path = os.path.join("..", "..", "data", "processed", "analytics",
                        "similarity_matrix.parquet")
if os.path.exists(os.path.abspath(sim_path)):
    sim = pd.read_parquet(sim_path)
    target = next((x for x in sim.index if f"#{pid}" in x), None)
    if target:
        top5 = sim.loc[target].drop(target).sort_values(ascending=False).head(5)
        st.subheader("🤖 AI Player Similarity — Top 5")
        for nm, sval in top5.items():
            st.progress(min(sval, 1.0),
                        text=f"**{nm.split(' #')[0]}** — {sval*100:.1f}% tương đồng")
else:
    st.caption("Chạy src/analytics/player_similarity.py để có Similarity.")

# market value regression row
if mv is not None:
    mrow = mv[mv["player_id"] == pid]
    if not mrow.empty:
        r = mrow.iloc[0]
        st.subheader("💰 Market Value Regression (AI)")
        a, b, c_ = st.columns(3)
        a.metric("Trước giải", f"{r['current_value']/1e6:.1f}M €")
        b.metric("Dự đoán sau giải", f"{r['predicted_post_value']/1e6:.1f}M €")
        d_pct = r["change_pct"]
        c_.metric("Chênh lệch", f"{d_pct:+.1f}%", delta=d_pct)
        st.caption("⚠️ Estimate — thiếu ground-truth giá trị sau giải.")
