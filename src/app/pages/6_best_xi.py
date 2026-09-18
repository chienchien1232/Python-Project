# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Optimal Best XI Squad Builder (PuLP LP Solver)."""
import os
import sys
import html as html_lib
import json
from pathlib import Path

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

from helpers import load_analytics_csv  # noqa: E402
from media_ui import flag_image, player_portrait, render_photo_story  # noqa: E402

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Đội Hình Tiêu Biểu | WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

# ── Inject custom CSS ──────────────────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ── Team flags lookup ─────────────────────────────────────────────────────────
FLAGS = {
    "Algeria": "DZ", "Argentina": "AR", "Australia": "AU", "Austria": "AT",
    "Belgium": "BE", "Bosnia and Herzegovina": "BA", "Brazil": "BR",
    "Cabo Verde": "CV", "Canada": "CA", "Colombia": "CO", "Congo DR": "CD",
    "Croatia": "HR", "Curaçao": "CW", "Czechia": "CZ", "Côte d'Ivoire": "CI",
    "Ecuador": "EC", "Egypt": "EG", "England": "ENG", "France": "FR",
    "Germany": "DE", "Ghana": "GH", "Haiti": "HT", "IR Iran": "IR",
    "Iraq": "IQ", "Japan": "JP", "Jordan": "JO", "Mexico": "MX",
    "Morocco": "MA", "Netherlands": "NL", "New Zealand": "NZ", "Norway": "NO",
    "Panama": "PA", "Paraguay": "PY", "Portugal": "PT", "Qatar": "QA",
    "Saudi Arabia": "SA", "Scotland": "SCO", "Senegal": "SN",
    "South Africa": "ZA", "South Korea": "KR", "Spain": "ES", "Sweden": "SE",
    "Switzerland": "CH", "Tunisia": "TN", "Türkiye": "TR", "USA": "US",
    "Uruguay": "UY", "Uzbekistan": "UZ",
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


def flag(team_name: str) ->str:
    return FLAGS.get(clean_name(team_name), "—")


# ── Top Navigation Bar ────────────────────────────────────────────────────────
from navigation import render_navigation
from table_ui import data_table
render_navigation('Best XI')
st.html(Path(app_path) / "best_xi.css")

render_photo_story(
    "HỆ THỐNG TỐI ƯU ĐỘI HÌNH / 2026",
    "XÂY DỰNG.",
    "ĐỘI HÌNH HOÀN HẢO.",
    "Thiết lập đội hình xuất sắc nhất giải đấu qua phong độ, vai trò, giá trị và sự cân bằng chiến thuật.",
    index="11 CẦU THỦ ĐÁ CHÍNH",
    page="best-xi",
)


# ── Formations Mapping ────────────────────────────────────────────────────────
FORMATIONS = {
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
}

@st.cache_data(show_spinner=False)
def load_best_xi_pool():
    scores_path = os.path.join(ANALYTICS, "analytics_scores.csv")
    if not os.path.exists(scores_path):
        return None
    pool_df = pd.read_csv(scores_path, dtype={"player_id": str})
    pool_df = pool_df[pool_df["minutes"].astype(float) >= 90].copy()
    pool_df["player_name"] = pool_df["player_name"].apply(clean_name)
    pool_df["team"] = pool_df["team"].apply(clean_name)

    sq_path = os.path.join(ROOT, "data", "processed", "csv", "squads_and_players.csv")
    if os.path.exists(sq_path):
        sq = pd.read_csv(sq_path, dtype={"player_id": str})[["player_id", "market_value_eur", "date_of_birth"]]
        pool_df = pool_df.merge(sq, on="player_id", how="left")
        pool_df["value_meur"] = (pd.to_numeric(pool_df["market_value_eur"], errors="coerce") / 1e6).round(1)
    else:
        pool_df["value_meur"] = 25.0

    clusters = load_analytics_csv("player_clusters.csv")
    if clusters is not None and "cluster_label" in clusters.columns:
        clusters["player_id"] = clusters["player_id"].astype(str)
        pool_df = pool_df.merge(clusters[["player_id", "cluster_label"]].drop_duplicates("player_id"),
                                on="player_id", how="left")
    return pool_df


@st.cache_data(show_spinner=False)
def solve_best_xi(formation: str, mode: str, budget: float | None, max_nation: int):
    raw_pool = load_best_xi_pool()
    if raw_pool is None:
        return None, "Missing Data", 0.0, 0.0

    pool = raw_pool.copy()
    pool["value_meur"] = pool["value_meur"].fillna(pool["value_meur"].median() if pool["value_meur"].notna().any() else 10.0)

    is_val_mode = ("Tối ưu Giá trị" in mode or "Value-for-Money" in mode)
    is_u23_mode = ("U23" in mode or "Under-23" in mode)
    is_ml_mode = ("Cụm ML" in mode or "ML Cluster" in mode)

    if is_u23_mode:
        if "date_of_birth" in pool.columns:
            pool = pool[pd.to_datetime(pool["date_of_birth"], errors="coerce") > pd.Timestamp("2003-06-11")]
        else:
            pool = pool[pool.get("age", pd.Series(99, index=pool.index)) < 23]

    has_cluster = "cluster_label" in pool.columns
    if is_ml_mode and not has_cluster:
        is_ml_mode = False

    prob = pulp.LpProblem("BestXI", pulp.LpMaximize)
    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in pool.index}

    if is_val_mode:
        obj = pool["overall_score"] / pool["value_meur"].clip(lower=0.5)
    else:
        obj = pool["overall_score"]

    prob += pulp.lpSum(obj[i] * x[i] for i in pool.index)
    prob += pulp.lpSum(x.values()) == 11, "total_11"

    for pos, need in FORMATIONS[formation].items():
        idx = pool.index[pool["position"] == pos]
        prob += pulp.lpSum(x[i] for i in idx) == need, f"pos_{pos}"

    if budget is not None and is_val_mode:
        prob += pulp.lpSum(pool.loc[i, "value_meur"] * x[i] for i in pool.index) <= budget, "budget"

    if max_nation:
        for nat, grp in pool.groupby("team"):
            prob += pulp.lpSum(x[i] for i in grp.index) <= max_nation, f"nat_{nat}"

    if is_ml_mode:
        for lbl in ("Finisher / Goal Scorer", "Playmaker / Chance Creator", "Defensive Anchor", "Defensive Player"):
            idx = pool.index[pool.get("cluster_label", "") == lbl]
            if len(idx):
                prob += pulp.lpSum(x[i] for i in idx) >= 1, f"min_{lbl[:8]}"

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status_str = pulp.LpStatus[status]
    if status_str != "Optimal":
        return None, status_str, 0.0, 0.0

    xi = pool[[x[i].value() == 1 for i in pool.index]].copy()
    order = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
    xi["_o"] = xi["position"].map(order)
    xi = xi.sort_values("_o")

    total_score = float(xi["overall_score"].sum().round(1))
    total_val = float(xi["value_meur"].sum().round(1))
    return xi, status_str, total_score, total_val


# ── Best XI workspace marker and heading ─────────────────────────────────────
st.markdown(
    '<div class="best-xi-studio" aria-hidden="true"></div>'
    '<section class="bxi-dashboard-heading">'
    '<div><span>ĐỘI HÌNH TIÊU BIỂU / PHÒNG THIẾT KẾ</span><h2>Xây dựng đội bóng trong mơ.</h2></div>'
    '<p>Chọn sơ đồ chiến thuật và mô hình tuyển chọn. Thuật toán tối ưu sẽ tái thiết lập trọn vẹn 11 vị trí ngay tức thì.</p>'
    '</section>',
    unsafe_allow_html=True,
)
# ── Control Panel ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Thiết Lập Chiến Thuật &amp; Ràng Buộc</div>", unsafe_allow_html=True)

def query_value(name: str, default: str) -> str:
    value = st.query_params.get(name, default)
    return str(value[0] if isinstance(value, list) and value else value)


def query_int(name: str, default: int) -> int:
    try:
        return int(query_value(name, str(default)))
    except (TypeError, ValueError):
        return default


formation_options = list(FORMATIONS.keys())
formation_query = query_value("formation", formation_options[0])
formation_index = formation_options.index(formation_query) if formation_query in formation_options else 0

MODE_ALIAS = {
    "AI Official Team of the Tournament": "Đội hình Tiêu biểu AI Chính thức",
    "ML Cluster Balanced XI": "Đội hình Cân bằng Cụm ML",
    "Under-23 Young Stars XI": "Đội hình Ngôi sao trẻ U23",
    "Value-for-Money XI": "Đội hình Tối ưu Giá trị",
}
mode_options = [
    "Đội hình Tiêu biểu AI Chính thức",
    "Đội hình Cân bằng Cụm ML",
    "Đội hình Ngôi sao trẻ U23",
    "Đội hình Tối ưu Giá trị",
]
mode_query = query_value("mode", mode_options[0])
if mode_query in MODE_ALIAS:
    mode_query = MODE_ALIAS[mode_query]
mode_index = mode_options.index(mode_query) if mode_query in mode_options else 0

c1, c2 = st.columns(2)
with c1:
    formation = st.selectbox("Sơ đồ chiến thuật:", formation_options, index=formation_index)
with c2:
    mode = st.radio("Mô hình tuyển chọn tối ưu:", mode_options, index=mode_index, horizontal=True)

is_val_mode = ("Tối ưu Giá trị" in mode or "Value-for-Money" in mode)

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    budget_query = max(50, min(1200, query_int("budget", 300)))
    budget_query = int(round(budget_query / 25) * 25)
    budget = st.slider("Giới hạn ngân sách (€M) — áp dụng cho Tối ưu Giá trị", 50, 1200, budget_query, step=25) if is_val_mode else None
with col_opt2:
    nation_query = max(1, min(8, query_int("nation", 4)))
    max_nation = st.slider("Hạn ngạch số cầu thủ tối đa mỗi quốc gia:", 1, 8, nation_query)

xi, solve_status, total_score, total_val = solve_best_xi(formation, mode, budget, max_nation)

if solve_status != "Optimal" or xi is None:
    st.error(f"Trạng thái bộ giải: {solve_status}. Vui lòng nới lỏng ngân sách hoặc giới hạn số cầu thủ mỗi quốc gia.")
    st.stop()


mode_title = {
    "Đội hình Tiêu biểu AI Chính thức": "ĐỘI HÌNH TIÊU BIỂU AI CHÍNH THỨC CỦA GIẢI ĐẤU",
    "Đội hình Cân bằng Cụm ML": "ĐỘI HÌNH CÂN BẰNG CHIẾN THUẬT THEO CỤM ML",
    "Đội hình Ngôi sao trẻ U23": "ĐỘI HÌNH NGÔI SAO TRẺ U23 TIÊU BIỂU",
    "Đội hình Tối ưu Giá trị": "ĐỘI HÌNH TỐI ƯU HÓA GIÁ TRỊ CHUYỂN NHƯỢNG",
    "AI Official Team of the Tournament": "ĐỘI HÌNH TIÊU BIỂU AI CHÍNH THỨC CỦA GIẢI ĐẤU",
    "ML Cluster Balanced XI": "ĐỘI HÌNH CÂN BẰNG CHIẾN THUẬT THEO CỤM ML",
    "Under-23 Young Stars XI": "ĐỘI HÌNH NGÔI SAO TRẺ U23 TIÊU BIỂU",
    "Value-for-Money XI": "ĐỘI HÌNH TỐI ƯU HÓA GIÁ TRỊ CHUYỂN NHƯỢNG",
}.get(mode, "ĐỘI HÌNH TIÊU BIỂU TỐI ƯU")


# ── Interactive lineup studio ─────────────────────────────────────────────────
xi_ids = xi["player_id"].astype(str).tolist()
gk_ids = xi.loc[xi["position"] == "GK", "player_id"].astype(str).tolist()
focus_id = query_value("focus", gk_ids[0] if gk_ids else xi_ids[0])
if focus_id not in xi_ids:
    focus_id = gk_ids[0] if gk_ids else xi_ids[0]
focus_name = str(xi.loc[xi["player_id"].astype(str) == focus_id, "player_name"].iloc[0])


st.markdown(
    f'<section class="bxi-club-summary">'
    f'<div class="bxi-crest">XI</div><div><span>WORLD CUP 2026 / ĐỘI HÌNH TỐI ƯU</span>'
    f'<h3>Best XI FC</h3><p>{html_lib.escape(mode_title.title())}</p></div>'
    f'<dl><div><dt>SƠ ĐỒ</dt><dd>{formation}</dd></div>'
    f'<div><dt>ĐIỂM ĐỘI HÌNH</dt><dd>{total_score:.1f}</dd></div>'
    f'<div><dt>GIÁ TRỊ</dt><dd>€{total_val:.1f}M</dd></div></dl>'
    f'</section>',
    unsafe_allow_html=True,
)
roster_cards = ""
for shirt_no, (_, row) in enumerate(xi.iterrows(), start=1):
    player_name = str(row["player_name"])
    is_active = player_name == focus_name
    roster_cards += (
        f'<button type="button" data-player-id="{html_lib.escape(str(row["player_id"]), quote=True)}" '
        f'class="bxi-roster-card{" is-active" if is_active else ""}" '
        f'aria-pressed="{str(is_active).lower()}" '
        f'aria-label="Xem hồ sơ của {html_lib.escape(player_name, quote=True)}">'
        f'<div class="bxi-roster-number">{shirt_no:02d}<small>{html_lib.escape(str(row["position"]))}</small></div>'
        f'{player_portrait(player_name, "player-portrait bxi-roster-portrait")}'
        f'<footer><strong>{html_lib.escape(player_name)}</strong>'
        f'<span>{flag_image(row["team"], class_name="media-flag is-small")} '
        f'{html_lib.escape(str(row["team"]))}</span></footer></button>'
    )


def pitch_row(role: str, line_label: str) -> str:
    members = xi[xi["position"] == role].reset_index(drop=True)
    cards = ""
    for shirt_no, (_, player) in enumerate(members.iterrows(), start=1):
        player_name = str(player["player_name"])
        is_active = player_name == focus_name
        cards += (
            f'<button type="button" data-player-id="{html_lib.escape(str(player["player_id"]), quote=True)}" '
            f'class="bxi-pitch-player{" is-active" if is_active else ""}" '
            f'aria-pressed="{str(is_active).lower()}" '
            f'aria-label="Xem hồ sơ của {html_lib.escape(player_name, quote=True)}">'
            f'<span class="bxi-shirt-number">{shirt_no}</span>'
            f'{player_portrait(player_name, "player-portrait bxi-pitch-portrait")}'
            f'<div><strong>{html_lib.escape(player_name)}</strong>'
            f'<small>{flag_image(player["team"], class_name="media-flag is-small")} '
            f'{html_lib.escape(role)} · {float(player["overall_score"]):.0f}</small></div></button>'
        )
    return f'<div class="bxi-pitch-row bxi-row-{role.lower()}" data-line="{line_label}">{cards}</div>'


pitch_html = (
    '<section class="bxi-pitch-panel">'
    '<header><div><span>SA BÀN CHIẾN THUẬT / TRỰC TIẾP</span><h3>' + formation + '</h3></div>'
    '<p>PuLP CBC / TỐI ƯU<br>TỐI ĐA ' + str(max_nation) + ' CẦU THỦ / ĐỘI</p></header>'
    '<div class="bxi-pitch">'
    '<div class="bxi-pitch-markings" aria-hidden="true"><i></i><b></b><em></em></div>'
    + pitch_row("FWD", "TIỀN ĐẠO")
    + pitch_row("MID", "TIỀN VỆ")
    + pitch_row("DEF", "HẬU VỆ")
    + pitch_row("GK", "THỦ MÔN")
    + '</div></section>'
)

def player_profile_html(selected: pd.Series) -> str:
    player_name = str(selected["player_name"])
    selected_dob = pd.to_datetime(selected.get("date_of_birth"), errors="coerce")
    selected_age = int((pd.Timestamp("2026-06-11") - selected_dob).days / 365.2425) if pd.notna(selected_dob) else None
    selected_role = str(selected.get("cluster_label", "Ngôi sao giải đấu") or "Ngôi sao giải đấu")
    selected_value = float(selected.get("value_meur", 0) or 0)
    selected_minutes = int(float(selected.get("minutes", 0) or 0))
    if str(selected["position"]) == "GK":
        metric_values = [
            ("Tổng điểm", f'{float(selected.get("overall_score", 0) or 0):.0f}'),
            ("Số trận", str(int(float(selected.get("matches", 0) or 0)))),
            ("Số phút", str(selected_minutes)),
            ("Giá trị", f'€{selected_value:.1f}M'),
        ]
    else:
        metric_values = []
        for label, column in (
            ("Tổng điểm", "overall_score"),
            ("Tấn công", "attacking_score"),
            ("Sáng tạo", "chance_creation_score"),
            ("Phòng ngự", "defensive_score"),
        ):
            value = pd.to_numeric(selected.get(column), errors="coerce")
            metric_values.append((label, f"{float(value):.0f}" if pd.notna(value) else "—"))
    metric_html = "".join(
        f'<div><strong>{value}</strong><span>{label}</span></div>'
        for label, value in metric_values
    )
    return (
        '<aside class="bxi-player-profile">'
        f'<div class="bxi-profile-kicker">/ {html_lib.escape(str(selected["position"]))}</div>'
        f'<div class="bxi-profile-visual">{player_portrait(player_name, "player-portrait bxi-profile-portrait")}'
        f'<span class="bxi-profile-watermark">{html_lib.escape(str(selected["position"]))}</span></div>'
        f'<div class="bxi-profile-country">{flag_image(selected["team"], class_name="media-flag")} '
        f'{html_lib.escape(str(selected["team"]))}</div>'
        f'<h3>{html_lib.escape(player_name)}</h3><p>{html_lib.escape(selected_role)}</p>'
        f'<div class="bxi-profile-metrics">{metric_html}</div>'
        '<dl class="bxi-profile-facts">'
        f'<div><dt>TUỔI</dt><dd>{selected_age if selected_age is not None else "—"}</dd></div>'
        f'<div><dt>SỐ PHÚT</dt><dd>{selected_minutes:,}</dd></div>'
        f'<div><dt>GIÁ TRỊ TT</dt><dd>€{selected_value:.1f}M</dd></div>'
        '</dl></aside>'
    )


profile_by_id = {
    str(row["player_id"]): player_profile_html(row)
    for _, row in xi.iterrows()
}
profile_html = profile_by_id[focus_id]
profiles_json = json.dumps(profile_by_id, ensure_ascii=False).replace("</", "<\\/")
component_css = Path(app_path, "best_xi.css").read_text(encoding="utf-8")

lineup_component = f"""
<style>
{component_css}
html,body {{ margin:0; padding:0; background:transparent; color:var(--bxi-text); font-family:Inter,Arial,sans-serif; }}
.bxi-component,.bxi-component * {{ box-sizing:border-box; }}
.bxi-component button {{ margin:0; font:inherit; text-align:left; cursor:pointer; appearance:none; }}
.bxi-component-grid {{ display:grid; grid-template-columns:minmax(0,2.3fr) minmax(280px,1fr); gap:16px; }}
.bxi-component .bxi-player-profile > h3 {{ margin:12px 0 0; color:var(--bxi-text); font-size:clamp(28px,2.7vw,46px); line-height:.9; letter-spacing:-.05em; text-transform:uppercase; }}
.bxi-component .bxi-player-profile > p {{ min-height:34px; margin:8px 0 18px; color:var(--bxi-muted); font-size:11px; }}
.media-flag {{ position:relative; display:inline-grid; place-items:center; width:46px; height:32px; overflow:hidden; border:1px solid #ffffff2e; background:#121212; color:#fff; font-size:9px; font-weight:800; letter-spacing:.08em; vertical-align:middle; }}
.media-flag img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }}
.media-flag.is-small {{ width:27px; height:19px; }}
.player-portrait {{ position:relative; display:inline-grid; place-items:center; width:150px; height:190px; flex:0 0 auto; overflow:hidden; border:1px solid #ffffff2b; background:linear-gradient(145deg,#222,#080808); color:#777; font-size:30px; font-weight:300; }}
.player-portrait img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:center top; filter:saturate(1.08) contrast(1.03); transition:filter .45s var(--bxi-ease),transform .7s var(--bxi-ease); }}
.bxi-roster-card:focus-visible,.bxi-pitch-player:focus-visible {{ outline:2px solid var(--bxi-green); outline-offset:-3px; }}
.bxi-pitch-player {{ transition:border-color .25s var(--bxi-ease),box-shadow .25s var(--bxi-ease),transform .25s var(--bxi-ease); }}
.bxi-pitch-player:hover,.bxi-pitch-player.is-active {{ border-color:var(--bxi-green); box-shadow:0 12px 30px rgba(0,0,0,.44),0 0 24px rgba(255,255,255,.14); transform:translateY(-2px); }}
#bxi-profile-slot {{ min-width:0; }}
@media (max-width:900px) {{
  .bxi-component-grid {{ grid-template-columns:1fr; }}
  .bxi-player-profile {{ min-height:680px; }}
}}
</style>
<div class="bxi-component">
  <div class="bxi-roster-label"><span>ĐỘI HÌNH RA SÂN / 11 CẦU THỦ</span><span>CUỘN DANH SÁCH →</span></div>
  <section class="bxi-roster-rail" aria-label="Selected starting eleven">{roster_cards}</section>
  <div class="bxi-component-grid">
    {pitch_html}
    <div id="bxi-profile-slot" aria-live="polite">{profile_html}</div>
  </div>
</div>
<script>
const profiles = {profiles_json};
const profileSlot = document.getElementById("bxi-profile-slot");
const playerButtons = Array.from(document.querySelectorAll("[data-player-id]"));

playerButtons.forEach((button) => {{
  button.addEventListener("click", () => {{
    const playerId = button.dataset.playerId;
    if (!profiles[playerId]) return;
    profileSlot.innerHTML = profiles[playerId];
    playerButtons.forEach((item) => {{
      const active = item.dataset.playerId === playerId;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    }});
    requestAnimationFrame(reportHeight);
  }});
}});

function reportHeight() {{
  window.parent.postMessage({{
    isStreamlitMessage:true,
    type:"streamlit:setFrameHeight",
    height:document.documentElement.scrollHeight
  }}, "*");
}}
new ResizeObserver(reportHeight).observe(document.body);
window.addEventListener("load", reportHeight);
</script>
"""
st.iframe(lineup_component, height=1040, width="stretch", tab_index=-1)

# ── Full 11 Starters Performance Breakdown Table ──────────────────────────────
st.markdown("<div class='section-header'>Bảng Chi Tiết Chỉ Số 11 Tuyển Thủ Đá Chính</div>", unsafe_allow_html=True)

show_cols = [c for c in ("player_name", "position", "team", "minutes",
                         "overall_score", "attacking_score",
                         "chance_creation_score", "passing_score",
                         "defensive_score", "value_meur")
             if c in xi.columns]

disp_xi = xi[show_cols].copy()
disp_xi.columns = [
    "Cầu thủ", "Vị trí", "Đội tuyển quốc gia", "Số phút", "Tổng điểm",
    "Tấn công", "Tạo cơ hội", "Chuyền bóng", "Phòng ngự", "Giá trị (€M)"
]

data_table(disp_xi, width="stretch", label="11 cầu thủ đá chính / chỉ số hiệu suất")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "Nền tảng Phân tích WorldCup Stats '26 &nbsp;·&nbsp; Dữ liệu từ FIFA, ESPN &amp; biên bản thi đấu chính thức &nbsp;·&nbsp; Phát triển bằng Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
