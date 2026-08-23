# -*- coding: utf-8 -*-
"""TAB BEST XI - Sa ban 4 che do (AI Official / ML Balanced / U23 / Value).

LP PuLP: max tong Overall Score
Rang buoc: formation (GK/DEF/MID/FWD), tong = 11,
           budget (trieu EUR, che do VFM), max-per-nation.
"""
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import pulp
except ImportError:
    st.error("Cần thư viện PuLP: pip install pulp")
    st.stop()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANALYTICS = os.path.join(ROOT, "data", "processed", "analytics")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

st.title("⭐ Optimal Best XI Builder")

FORMATIONS = {
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
}

scores_path = os.path.join(ANALYTICS, "analytics_scores.csv")
if not os.path.exists(scores_path):
    st.error("Chưa có analytics_scores.csv — chạy: "
             "`python src/analytics/analytics_score.py`")
    st.stop()

MIN_MIN = 90
df = pd.read_csv(scores_path, dtype={"player_id": str})
df = df[df["minutes"].astype(float) >= MIN_MIN].copy()

# gia tri chuyen nhuong (trieu EUR) tu squads
sq_path = os.path.join(ROOT, "data", "processed", "csv",
                       "squads_and_players.csv")
sq = pd.read_csv(sq_path, dtype={"player_id": str})[
    ["player_id", "market_value_eur"]]
df = df.merge(sq, on="player_id", how="left")
df["value_meur"] = (pd.to_numeric(df["market_value_eur"],
                                  errors="coerce") / 1e6).round(1)
# tuoi cho mode U23
dob_col = "date_of_birth" if "date_of_birth" in df.columns else None

# ---------- Control panel ----------
c1, c2 = st.columns(2)
formation = c1.selectbox("Sơ đồ chiến thuật", list(FORMATIONS.keys()))
mode = c2.radio("Chế độ đội hình", [
    "🤖 AI Official (Performance)",
    "⚖️ ML Cluster Balanced XI",
    "🌱 Under-23 Young Stars XI",
    "💵 Value-for-Money XI"])

budget = st.slider("Ngân sách (triệu €) — áp dụng chế độ 💵 VFM",
                   50, 1500, 300, step=25) if mode.startswith("💵") else None
max_nation = st.slider("Tối đa cầu thủ cùng 1 đội tuyển", 1, 8, 8)

pool = df.copy()
pool["value_meur"] = pool["value_meur"].fillna(
    pool["value_meur"].median() if pool["value_meur"].notna().any() else 10.0)

if mode == "🌱 Under-23 Young Stars XI":
    if dob_col and dob_col in pool.columns:
        pool = pool[pd.to_numeric(
            pool[dob_col].str[:4], errors="coerce") >= 2004]
    else:
        pool = pool[pool.get("age", pd.Series(99, index=pool.index)) < 23]
elif mode == "💵 Value-for-Money XI":
    budget = min(budget, 150)

has_cluster = "cluster_label" in pool.columns
if mode == "⚖️ ML Cluster Balanced XI" and not has_cluster:
    st.warning("Thiếu cluster_label — chuyển về AI Official.")
    mode = "🤖 AI Official (Performance)"

# ---------- LP ----------
prob = pulp.LpProblem("BestXI", pulp.LpMaximize)
x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in pool.index}

if mode == "💵 Value-for-Money XI":
    obj = pool["overall_score"] / pool["value_meur"].clip(lower=0.5)
else:
    obj = pool["overall_score"]
prob += pulp.lpSum(obj[i] * x[i] for i in pool.index)

prob += pulp.lpSum(x.values()) == 11, "total_11"
for pos, need in FORMATIONS[formation].items():
    idx = pool.index[pool["position"] == pos]
    prob += pulp.lpSum(x[i] for i in idx) == need, f"pos_{pos}"
if budget is not None and mode == "💵 Value-for-Money XI":
    prob += pulp.lpSum(pool.loc[i, "value_meur"] * x[i]
                       for i in pool.index) <= budget, "budget"
if max_nation:
    for nat, grp in pool.groupby("team"):
        prob += pulp.lpSum(x[i] for i in grp.index) <= max_nation, \
            f"nat_{nat}"
if mode == "⚖️ ML Cluster Balanced XI":
    half = 11 // 2
    for lbl in ("Finisher / Goal Scorer", "Playmaker / Chance Creator",
                "Defensive Player"):
        idx = pool.index[pool["cluster_label"] == lbl]
        if len(idx):
            prob += pulp.lpSum(x[i] for i in idx) >= 1, f"min_{lbl[:12]}"

status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
if pulp.LpStatus[status] != "Optimal":
    st.error(f"Không tìm được phương án tối ưu ({pulp.LpStatus[status]}). "
             "Hãy nới lỏng ngân sách/ràng buộc.")
    st.stop()

xi = pool[[x[i].value() == 1 for i in pool.index]].copy()
order = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
xi["_o"] = xi["position"].map(order)
xi = xi.sort_values("_o")

total_score = xi["overall_score"].sum().round(1)
total_val = xi["value_meur"].sum().round(1)
mode_tag = {"🤖 AI Official (Performance)": "AI OFFICIAL TEAM OF THE TOURNAMENT",
            "⚖️ ML Cluster Balanced XI": "ML CLUSTER-BASED BALANCED XI",
            "🌱 Under-23 Young Stars XI": "UNDER-23 YOUNG STARS XI",
            "💵 Value-for-Money XI": "VALUE-FOR-MONEY XI"}
st.subheader(f"🏟️ {mode_tag[mode]}")
c1, c2 = st.columns(2)
c1.metric("Tổng Analytics Score", total_score)
c2.metric("Tổng giá trị đội hình", f"{total_val:.1f}M €")

# ---------- Pitch display ----------
formation_y = {"GK": 6, "DEF": 26, "MID": 52, "FWD": 80}
fig = go.Figure()
fig.add_shape(type="rect", x0=2, y0=2, x1=98, y1=98,
              line=dict(color="#7CE87C", width=2))
fig.add_shape(type="line", x0=2, y0=50, x1=98, y1=50,
              line=dict(color="#7CE87C", width=1.5))
fig.update_layout(paper_bgcolor="#0d2818", plot_bgcolor="#0d2818",
                  xaxis=dict(range=[0, 100], visible=False),
                  yaxis=dict(range=[0, 100], visible=False),
                  height=520, margin=dict(l=10, r=10, t=30, b=10))

for role, ybase in formation_y.items():
    members = xi[xi["position"] == role].reset_index(drop=True)
    n = len(members)
    for j, (_, r) in enumerate(members.iterrows()):
        xpos = 50 if n == 1 else 15 + 70 * j / (n - 1)
        fig.add_trace(go.Scatter(
            x=[xpos], y=[ybase], mode="markers+text",
            marker=dict(size=44, color="#FFD600",
                        line=dict(width=2, color="#111")),
            text=[f"<b>{r['player_name']}</b><br>{r['team']} · "
                  f"{r['overall_score']:.0f}"],
            textposition="bottom center", textfont=dict(color="white"),
            hoverinfo="text"))
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Thống kê chi tiết 11 chính thức"):
    show_cols = [c for c in ("player_name", "position", "team", "minutes",
                             "overall_score", "attacking_score",
                             "chance_creation_score", "passing_score",
                             "defensive_score", "value_meur")
                 if c in xi.columns]
    st.dataframe(xi[show_cols], use_container_width=True, hide_index=True)
