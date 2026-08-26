# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Optimal Best XI Squad Builder (PuLP LP Solver)."""
import os
import sys
import html as html_lib

import pandas as pd
import streamlit as st

try:
    import pulp
except ImportError:
    st.error("PuLP library required. Run: pip install pulp")
    st.stop()

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys_path = os.path.join(ROOT, "src")
app_path = os.path.join(ROOT, "src", "app")
ANALYTICS = os.path.join(ROOT, "data", "processed", "analytics")

for p in [app_path, sys_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers import cfg_money, cfg_num, cfg_progress, flag_url, icon_badge, player_face_data_uri, q  # noqa: E402

# ── Page configuration ────────────────────────────────────────────────────────


# ── Team flags lookup ─────────────────────────────────────────────────────────
FLAGS = {
    "Algeria": "🇩🇿", "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹",
    "Belgium": "🇧🇪", "Bosnia and Herzegovina": "🇧🇦", "Brazil": "🇧🇷",
    "Cabo Verde": "🇨🇻", "Canada": "🇨🇦", "Colombia": "🇨🇴", "Congo DR": "🇨🇩",
    "Croatia": "🇭🇷", "Curaçao": "🇨🇼", "Czechia": "🇨🇿", "Côte d'Ivoire": "🇨🇮",
    "Ecuador": "🇪🇨", "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "France": "🇫🇷",
    "Germany": "🇩🇪", "Ghana": "🇬🇭", "Haiti": "🇭🇹", "IR Iran": "🇮🇷",
    "Iraq": "🇮🇶", "Japan": "🇯🇵", "Jordan": "🇯🇴", "Mexico": "🇲🇽",
    "Morocco": "🇲🇦", "Netherlands": "🇳🇱", "New Zealand": "🇳🇿", "Norway": "🇳🇴",
    "Panama": "🇵🇦", "Paraguay": "🇵🇾", "Portugal": "🇵🇹", "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Senegal": "🇸🇳",
    "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸", "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭", "Tunisia": "🇹🇳", "Türkiye": "🇹🇷", "USA": "🇺🇸",
    "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿",
}


def clean_name(val):
    if not isinstance(val, str):
        return str(val) if val is not None else ""
    return (
        val.replace("Adrin", "Adrian")
           .replace("Andrs", "Andres")
           .replace("Damin", "Damian")
           .replace("Curaao", "Curacao")
           .replace("Cte d'Ivoire", "Côte d'Ivoire")
           .replace("Trkiye", "Türkiye")
           .replace("Lionel Andrs Messi", "Lionel Messi")
           .replace("Rodrigo Rodri", "Rodri")
           .replace("Kylian Mbappe", "Kylian Mbappé")
    )


def flag(team_name: str) -> str:
    return FLAGS.get(clean_name(team_name), "⚽")


# ── Formations Mapping ────────────────────────────────────────────────────────
FORMATIONS = {
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
}

scores_path = os.path.join(ANALYTICS, "analytics_scores.csv")
if not os.path.exists(scores_path):
    st.error("Analytics scores file not found. Run `python src/analytics/analytics_score.py`.")
    st.stop()

df = pd.read_csv(scores_path, dtype={"player_id": str})
df = df[df["minutes"].astype(float) >= 90].copy()
df["player_name"] = df["player_name"].apply(clean_name)
df["team"] = df["team"].apply(clean_name)

# Squad market valuations
sq_path = os.path.join(ROOT, "data", "processed", "csv", "squads_and_players.csv")
if os.path.exists(sq_path):
    sq = pd.read_csv(sq_path, dtype={"player_id": str})[["player_id", "market_value_eur",
                                                         "date_of_birth"]]
    df = df.merge(sq, on="player_id", how="left")
    df["value_meur"] = (pd.to_numeric(df["market_value_eur"], errors="coerce") / 1e6).round(1)
else:
    df["value_meur"] = 25.0

# Tactical role clusters (bat che do ML Cluster Balanced XI)
clus_path = os.path.join(ROOT, "data", "processed", "analytics", "player_clusters.csv")
if os.path.exists(clus_path):
    pcl = pd.read_csv(clus_path, dtype={"player_id": str})[["player_id", "cluster_label"]]
    df = df.merge(pcl, on="player_id", how="left")

dob_col = "date_of_birth" if "date_of_birth" in df.columns else None


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span> SQUAD OPTIMIZATION ENGINE</div>'
    '<div class="wc-hero-dates">LINEAR PROGRAMMING (PuLP) · 4 SELECTION MODES</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">OPTIMAL</span>'
    '<span class="title-lime">BEST XI.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Build and visualize optimal World Cup 2026 lineups using Integer Linear Programming (ILP). '
    'Choose from 4 selection modes, custom tactical formations, national quotas, and budget constraints.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Control Panel ─────────────────────────────────────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('gear')} Tactical Settings &amp; Constraints</div>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    formation = st.selectbox("Tactical Formation:", list(FORMATIONS.keys()), index=0)
with c2:
    mode = st.radio("Optimization Selection Mode:", [
        "🤖 AI Official Team of the Tournament",
        "⚖️ ML Cluster Balanced XI",
        "🌱 Under-23 Young Stars XI",
        "💵 Value-for-Money XI"
    ])

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    budget = st.slider("Budget Cap (€M) — applies to 💵 Value-for-Money", 50, 1200, 300, step=25) if "Value-for-Money" in mode else None
with col_opt2:
    max_nation = st.slider("Max Players per Nation Quota:", 1, 8, 4)

df["value_meur"] = df["value_meur"].fillna(
    df["value_meur"].median() if df["value_meur"].notna().any() else 10.0)
pool = df.copy()

if "Under-23" in mode:
    if dob_col and dob_col in pool.columns:
        pool = pool[pd.to_numeric(pool[dob_col].astype(str).str[:4],
                                  errors="coerce") >= 2004]
elif "Value-for-Money" in mode:
    budget = min(budget or 300, 200)

# Guard: pool qua it nguoi -> bo filter, tranh solver Infeasible
if len(pool) < 30:
    st.warning("Not enough players for this selection mode - using the full pool.")
    pool = df.copy()

# Vi tri thieu (VD: khong co thu mon U23 da choi 90+) -> noi bo loc che do
# cho rieng cac vi tri do, bao dam solver luon kha thi.
auto_notes = []
short_pos = [p for p, n in FORMATIONS[formation].items() if (pool['position'] == p).sum() < n]
if short_pos:
    for p in short_pos:
        pool = pd.concat([pool, df[df["position"] == p]]).drop_duplicates(subset="player_id")
    auto_notes.append("position shortage: used all available players for " + ", ".join(short_pos))

has_cluster = "cluster_label" in pool.columns
if "ML Cluster" in mode and not has_cluster:
    mode = "🤖 AI Official Team of the Tournament"


# ── Integer Linear Programming Optimization ──────────────────────────────────
def build_and_solve(budget_cap, nation_cap, cluster_min):
    """Dung va giai bai toan ILP. Tra (status, prob, x)."""
    prob = pulp.LpProblem("BestXI", pulp.LpMaximize)
    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in pool.index}

    if "Value-for-Money" in mode:
        obj = pool["overall_score"] / pool["value_meur"].clip(lower=0.5)
    else:
        obj = pool["overall_score"]

    prob += pulp.lpSum(obj[i] * x[i] for i in pool.index)
    prob += pulp.lpSum(x.values()) == 11, "total_11"

    for pos, need in FORMATIONS[formation].items():
        idx = pool.index[pool["position"] == pos]
        prob += pulp.lpSum(x[i] for i in idx) == need, f"pos_{pos}"

    if budget_cap:
        prob += pulp.lpSum(pool.loc[i, "value_meur"] * x[i]
                           for i in pool.index) <= budget_cap, "budget"

    if nation_cap:
        for nat, grp in pool.groupby("team"):
            prob += pulp.lpSum(x[i] for i in grp.index) <= nation_cap, f"nat_{nat}"

    if "ML Cluster" in mode and cluster_min:
        for j, lbl in enumerate(cluster_min):
            idx = pool.index[pool["cluster_label"] == lbl]
            if len(idx):
                prob += pulp.lpSum(x[i] for i in idx) >= 1, f"min_cluster_{j}"

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    return pulp.LpStatus[status], prob, x

cluster_min = []
if "ML Cluster" in mode and "cluster_label" in pool.columns:
    counts = pool["cluster_label"].value_counts()
    cluster_min = [lbl for lbl, n in counts.items() if n >= 2][:5]

budget_cap = budget if "Value-for-Money" in mode else None
nation_cap = max_nation

attempts = [(budget_cap, nation_cap)]
if budget_cap:
    attempts += [(budget_cap * 2, nation_cap), (budget_cap * 4, nation_cap),
                 (None, nation_cap)]
attempts += [(None, None)]

status, prob, x, used = "Not Solved", None, None, (budget_cap, nation_cap)
for bcap, ncap in attempts:
    status, prob, x = build_and_solve(bcap, ncap, cluster_min)
    used = (bcap, ncap)
    if status == "Optimal":
        break

if status != "Optimal" or len(pool) < 11:
    st.error(f"Solver status: {status}. Khong xay dung duoc XI tu pool hien tai ({len(pool)} cau thu).")
    st.stop()

relax_notes = []
if used[0] != budget_cap and budget_cap:
    relax_notes.append("budget cap removed")
if used[1] != max_nation and max_nation:
    relax_notes.append("nation quota removed")
if relax_notes:
    st.info("Constraints auto-relaxed to keep the XI feasible: "
           + " + ".join(auto_notes + relax_notes) + ".")

xi = pool[[x[i].value() == 1 for i in pool.index]].copy()
order = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
xi["_o"] = xi["position"].map(order)
xi = xi.sort_values("_o")

total_score = xi["overall_score"].sum().round(1)
total_val = xi["value_meur"].sum().round(1)

mode_title = {
    "🤖 AI Official Team of the Tournament": "AI OFFICIAL TEAM OF THE TOURNAMENT",
    "⚖️ ML Cluster Balanced XI": "ML CLUSTER-BALANCED DREAM XI",
    "🌱 Under-23 Young Stars XI": "UNDER-23 YOUNG STARS XI",
    "💵 Value-for-Money XI": "VALUE-FOR-MONEY ROSTER"
}.get(mode, "OPTIMAL BEST XI")


# ── Squad Showcase Hero Banner ────────────────────────────────────────────────
st.markdown(
    f'<div class="match-hero-card" style="margin-top:20px">'
    f'<div class="match-hero-meta">'
    f'<div><span class="match-stage-badge">FORMATION {formation}</span> '
    f'<span style="background:rgba(204,255,0,0.12);color:#ccff00;border:1px solid rgba(204,255,0,0.35);border-radius:999px;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px">{mode_title}</span></div>'
    f'<div class="match-venue-text">Solver Status: <strong>OPTIMAL (PuLP CBC)</strong></div>'
    f'</div>'
    f'<div style="display:flex;justify-content:space-between;align-items:center;margin:14px 0">'
    f'<div>'
    f'<div class="match-team-name-big" style="font-size:32px">World Cup 2026 Best XI</div>'
    f'<div style="color:#94a3b8;font-size:13px;font-weight:600;letter-spacing:1px;text-transform:uppercase">11 Starters Selected from 1,248 Candidates</div>'
    f'</div>'
    f'<div style="display:flex;gap:20px">'
    f'<div style="text-align:right">'
    f'<div style="font-size:11px;font-weight:800;color:#64748b;letter-spacing:1.2px;text-transform:uppercase">TOTAL SCORE</div>'
    f'<div style="font-family:var(--font-sport);font-size:28px;font-weight:900;color:#ccff00">{total_score}</div>'
    f'</div>'
    f'<div style="text-align:right;border-left:1px solid rgba(255,255,255,0.08);padding-left:20px">'
    f'<div style="font-size:11px;font-weight:800;color:#64748b;letter-spacing:1.2px;text-transform:uppercase">TOTAL VALUATION</div>'
    f'<div style="font-family:var(--font-sport);font-size:28px;font-weight:900;color:#FFFFFF">€{total_val:.1f}M</div>'
    f'</div>'
    f'</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True
)


# ── Tactical Pitch Display (HTML/CSS — hiện ảnh mặt cầu thủ) ─────────────────
st.markdown(f"<div class='section-header'>{icon_badge('goal')} Tactical Pitch Lineup</div>", unsafe_allow_html=True)

# Sân tỷ lệ thật 68m x 105m (dọc, tấn công hướng lên). Vẽ bằng HTML/CSS để ảnh
# mặt cầu thủ luôn hiển thị (plotly traces không ổn định trên một số trình duyệt).
PW, PH = 68.0, 105.0
FACE = 19.0  # kích thước ảnh mặt (% bề ngang sân)

formation_y = {"GK": 9, "DEF": 33, "MID": 60, "FWD": 88}


def _px(v):
    return f"{v / PW * 100:.2f}%"


def _py(v):
    return f"{v / PH * 100:.2f}%"


tokens = []
for role, ybase in formation_y.items():
    members = xi[xi["position"] == role].reset_index(drop=True)
    n = len(members)
    for j, (_, r_p) in enumerate(members.iterrows()):
        xpos = PW / 2 if n == 1 else 10 + 48 * j / (n - 1)
        p_fl = flag(r_p["team"])
        surname = str(r_p["player_name"]).split()[-1]
        hover_txt = (f"{r_p['player_name']} ({r_p['position']}) — {p_fl} {r_p['team']} | "
                     f"Rating: {r_p['overall_score']:.1f} | Value: €{r_p['value_meur']:.1f}M")
        uri = player_face_data_uri(r_p["player_id"], r_p["player_name"], 128)
        if uri is None:
            # Fallback: ô tròn chữ cái đầu khi không tạo được ảnh
            initials = "".join(w[0] for w in str(r_p["player_name"]).split()[:2]).upper()
            face_html = (
                '<div style="width:100%;aspect-ratio:1;border-radius:12px;background:#111612;'
                'border:2px solid rgba(204,255,0,0.5);display:flex;align-items:center;'
                f'justify-content:center;font-family:var(--font-sport);font-weight:900;'
                f'font-size:22px;color:#ccff00">{html_lib.escape(initials)}</div>'
            )
        else:
            face_html = (
                f'<img src="{uri}" alt="" loading="lazy" style="width:100%;aspect-ratio:1;'
                f'object-fit:cover;display:block;border-radius:12px;'
                f'border:2px solid rgba(204,255,0,0.5);box-shadow:0 6px 16px rgba(0,0,0,0.55)" />'
            )
        tokens.append(
            f'<div style="position:absolute;left:{_px(xpos)};top:{_py(ybase)};'
            f'width:{FACE}%;transform:translate(-50%,-50%);text-align:center" '
            f'title="{html_lib.escape(hover_txt)}">'
            f'{face_html}'
            f'<div style="font-size:11.5px;font-weight:800;color:#F8FAFC;margin-top:4px;'
            f'text-shadow:0 1px 3px rgba(0,0,0,0.9);white-space:nowrap">'
            f'{html_lib.escape(surname)} · ★{r_p["overall_score"]:.0f}</div>'
            f'</div>'
        )

pitch_html = (
    '<div class="pitch-68">'
    '<div class="p-half"></div>'
    '<div class="p-circle"></div>'
    '<div class="p-areabox p-top"></div>'
    '<div class="p-areabox p-bottom"></div>'
    '<div class="p-goalbox p-top"></div>'
    '<div class="p-goalbox p-bottom"></div>'
    '<div class="p-dot" style="top:10.5%"></div>'
    '<div class="p-dot" style="bottom:10.5%"></div>'
    + "".join(tokens)
    + "</div>"
)
st.markdown(pitch_html, unsafe_allow_html=True)


# ── Full 11 Starters Performance Breakdown Table ──────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('clipboard')} Detailed 11 Starters Metrics Breakdown</div>", unsafe_allow_html=True)

show_cols = [c for c in ("player_name", "position", "team", "minutes",
                         "overall_score", "attacking_score",
                         "chance_creation_score", "passing_score",
                         "defensive_score", "value_meur")
             if c in xi.columns]

disp_xi = xi[show_cols].copy()
disp_xi.columns = [
    "Player", "Position", "National Team", "Minutes", "Overall Score",
    "Attacking Score", "Chance Creation", "Passing Score", "Defensive Score", "Value (€M)"
]

# Cot anh quoc gia (FIFA CDN) canh ten cau thu
disp_xi.insert(1, "Nat", xi["team"].map(flag_url).values)

xi_cfg = {"Nat": st.column_config.ImageColumn("", width="small"),
          "Overall Score": cfg_progress("Overall Score", 100),
          "Attacking Score": cfg_progress("Attacking Score", 100),
          "Chance Creation": cfg_progress("Chance Creation", 100),
          "Passing Score": cfg_progress("Passing Score", 100),
          "Defensive Score": cfg_progress("Defensive Score", 100),
          "Minutes": cfg_num("Minutes", "%.0f"),
          "Value (€M)": cfg_money("Value (€M)")}
st.dataframe(
    disp_xi,
    width="stretch",
    hide_index=True,
    column_config=xi_cfg,
)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
