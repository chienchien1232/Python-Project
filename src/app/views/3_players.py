# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Player Statistics & Profiles."""
import os
import sys
import html as html_lib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys_path = os.path.join(ROOT, "src")
app_path = os.path.join(ROOT, "src", "app")
for p in [app_path, sys_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers import (  # noqa: E402
    flag_img,
    flag_url,
    load_analytics_csv,
    cfg_num,
    icon_badge,
    icon_svg,
    load_player_photos,
   
    player_avatar_html,
    q,
)

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


# ── Load Dataset ──────────────────────────────────────────────────────────────
df = q("SELECT * FROM v_player_season ORDER BY minutes DESC")
if df.empty:
    st.error("Player season database view not found.")
    st.stop()

df["player_name"] = df["player_name"].apply(clean_name)
df["team"] = df["team"].apply(clean_name)

clusters = load_analytics_csv("player_clusters.csv")
mv = load_analytics_csv("market_value_estimates.csv")
if clusters is not None:
    clusters["player_id"] = clusters["player_id"].astype(str)
if mv is not None:
    mv["player_id"] = mv["player_id"].astype(str)


# ── Hero & KPI Summary ────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span> PLAYER DIRECTORY</div>'
    '<div class="wc-hero-dates">1,248 SQUAD MEMBERS · COMPREHENSIVE PER-90 RATINGS</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">PLAYER</span>'
    '<span class="title-lime">STATISTICS.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Browse in-depth player statistics normalized per 90 minutes. Inspect positional percentile radar charts, '
    'AI-calculated player similarity profiles, and post-tournament market value estimations.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

tot_p = len(df)
top_scorer = "Kylian Mbappé (10G)"
top_assists = "Lionel Messi (5A)"

st.markdown(
    '<div class="kpi-row-container" style="margin-bottom:28px">'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{tot_p:,}</div><div class="kpi-sport-label">PLAYERS LOGGED</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{icon_badge("medal", 30, 17)} Mbappé</div><div class="kpi-sport-label">GOLDEN BOOT (10 GOALS)</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{icon_badge("star", 30, 17)} Rodri</div><div class="kpi-sport-label">GOLDEN BALL (MVP)</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">48</div><div class="kpi-sport-label">NATIONAL SQUADS</div></div>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Master Per-90 Table & Filters ─────────────────────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('clipboard')} Master Player Per-90 Statistics</div>", unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 1.6])
with col_f1:
    pos_options = ["All Positions"] + sorted(df["position"].dropna().unique().tolist())
    sel_pos = st.selectbox("Position", pos_options)
with col_f2:
    team_options = ["All Teams"] + sorted(df["team"].dropna().unique().tolist())
    sel_team = st.selectbox("National Team", team_options)
with col_f3:
    search_q = st.text_input("🔍 Search Player Name:")

min_apps = st.slider("Minimum Matches Played", 0, int(df["matches_played"].max()), 2)

view = df[df["matches_played"] >= min_apps].copy()
if sel_pos != "All Positions":
    view = view[view["position"] == sel_pos]
if sel_team != "All Teams":
    view = view[view["team"] == sel_team]
if search_q:
    view = view[view["player_name"].str.contains(search_q, case=False, na=False)]

if clusters is not None and "cluster_label" in clusters.columns:
    view = view.merge(clusters[["player_id", "cluster_label"]], on="player_id", how="left")
    view = view.rename(columns={"cluster_label": "AI Tactical Role"})

# ── Ảnh cầu thủ + ảnh quốc gia (FIFA CDN) cho từng dòng bảng ──────────────────
photo_map = load_player_photos()
view["Photo"] = view["player_id"].astype(str).map(lambda x: photo_map.get(str(x)))
view["Flag"] = view["team"].map(flag_url)

show_cols = [
    "Photo", "Flag",
    "player_name", "position", "team", "matches_played", "minutes",
    "goals_p90", "assists_p90", "shots_p90", "passes_p90",
    "pass_accuracy_pct", "tackles_p90", "interceptions_p90", "clearances_p90"
]
if "AI Tactical Role" in view.columns:
    show_cols.append("AI Tactical Role")

show_cols = [c for c in show_cols if c in view.columns]
display_view = view[show_cols].copy()
display_view.columns = [c.replace("_p90", "/90").replace("_", " ").title() for c in display_view.columns]

st.dataframe(
    display_view,
    width="stretch",
    hide_index=True,
    height=320,
    column_config={
        "Photo": st.column_config.ImageColumn("", width="small"),
        "Flag": st.column_config.ImageColumn("", width="small"),
    },
)


# ── Detailed Player Dossier Profile ───────────────────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('search')} Detailed Player Profile &amp; Radar</div>", unsafe_allow_html=True)

player_list = sorted(df["player_name"].unique().tolist())
default_idx = player_list.index("Kylian Mbappé") if "Kylian Mbappé" in player_list else 0

sel_pname = st.selectbox("Select Player to inspect complete profile:", player_list, index=default_idx)

if sel_pname:
    p = df[df["player_name"] == sel_pname].iloc[0]
    pid = str(p["player_id"])
    p_team = p["team"]
    p_flag = flag(p_team)

    # Detailed metadata from players table
    info = q("SELECT club_team, date_of_birth, height_cm, caps, market_value_eur FROM players WHERE CAST(player_id AS TEXT) = ?", (pid,))
    club = "-"
    mv_meur = 0.0
    caps = "-"
    height = "-"
    if not info.empty:
        r_info = info.iloc[0]
        club = r_info["club_team"] or "-"
        caps = str(r_info["caps"]) if pd.notna(r_info["caps"]) else "-"
        height = f"{int(r_info['height_cm'])} cm" if pd.notna(r_info["height_cm"]) else "-"
        mv_meur = (float(r_info["market_value_eur"]) / 1e6) if pd.notna(r_info["market_value_eur"]) else 0.0

    cluster_badge = "Standard Profile"
    if clusters is not None:
        hit = clusters[clusters["player_id"] == pid]
        if not hit.empty:
            cluster_badge = hit.iloc[0].get("cluster_label", "Standard Profile")

    # Giai tournament bat thuong (tu anomalies.csv cua detect_anomalies)
    anom_note = ""
    _ap = os.path.join(ROOT, "data", "processed", "analytics", "anomalies.csv")
    if os.path.exists(_ap):
        _adf = pd.read_csv(_ap)
        _adf["player_name"] = _adf["player_name"].apply(clean_name)
        _hit = _adf[_adf["player_name"] == sel_pname]
        if not _hit.empty:
            anom_note = str(_hit.iloc[0]["nguyen_nhan"])

    # Player Hero Showcase Card
    st.markdown(
        f'<div class="match-hero-card">'
        f'<div class="match-hero-meta">'
        f'<div><span class="match-stage-badge">{p["position"]}</span> '
        f'<span style="background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.35);border-radius:999px;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px">{club}</span> '
        f'<span style="background:rgba(204,255,0,0.12);color:#ccff00;border:1px solid rgba(204,255,0,0.35);border-radius:999px;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px">{icon_svg("cpu", 12)} {cluster_badge}</span>'
        + (f'<span style="background:rgba(255,82,82,0.12);color:#ff5252;border:1px solid rgba(255,82,82,0.4);border-radius:999px;padding:4px 12px;font-size:11px;font-weight:800;margin-left:6px">⚡ Anomalous tournament: {anom_note}</span>' if anom_note else '')
        + '</div>'
        f'<div class="match-venue-text">Caps: <strong>{caps}</strong> &nbsp;·&nbsp; Height: <strong>{height}</strong></div>'
        f'</div>'
        f'<div class="match-scoreboard-main" style="margin:14px 0">'
        f'<div style="display:flex;align-items:center;gap:18px">'
        f'{player_avatar_html(pid, sel_pname, 128)}'
        f'<div>'
        f'<div class="match-team-name-big" style="font-size:36px">{html_lib.escape(sel_pname)}</div>'
        f'<div style="color:#94a3b8;font-size:13px;font-weight:600;letter-spacing:1px;text-transform:uppercase">{flag_img(p_team, 16, fallback_emoji=p_flag)} {html_lib.escape(str(p_team))} · {p["position"]}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:20px;align-items:center">'
        f'<div style="text-align:right">'
        f'<div style="font-size:11px;font-weight:800;color:#64748b;letter-spacing:1.2px;text-transform:uppercase">TOURNAMENT STATS</div>'
        f'<div style="font-family:var(--font-sport);font-size:26px;font-weight:900;color:#FFFFFF">{int(p["matches_played"])} Matches &nbsp;·&nbsp; {int(p["minutes"])} Mins</div>'
        f'<div style="font-size:12.5px;color:#94a3b8">{float(p.get("goals_p90",0)):.2f} G/90 · {float(p.get("assists_p90",0)):.2f} A/90</div>'
        f'</div>'
        f'<div style="text-align:right;border-left:1px solid rgba(255,255,255,0.08);padding-left:20px">'
        f'<div style="font-size:11px;font-weight:800;color:#64748b;letter-spacing:1.2px;text-transform:uppercase">MARKET VALUATION</div>'
        f'<div style="font-family:var(--font-sport);font-size:26px;font-weight:900;color:#ccff00">€{mv_meur:.1f}M</div>'
        f'<div style="font-size:12.5px;color:#94a3b8">Pre-Tournament Value</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_p_left, col_p_right = st.columns([1.15, 1.0], gap="large")

    with col_p_left:
        # Radar Percentile vs Positional Peers
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('radar', 26, 15)} Percentile vs {p['position']} Peers (Min 90 mins)</div>", unsafe_allow_html=True)

        radar_axes = [
            ("goals_p90", "Goals/90"),
            ("assists_p90", "Assists/90"),
            ("shots_p90", "Shots/90"),
            ("passes_p90", "Passes/90"),
            ("tackles_p90", "Tackles/90"),
            ("interceptions_p90", "Interceptions/90"),
            ("clearances_p90", "Clearances/90"),
            ("recoveries_p90", "Recoveries/90"),
        ]

        peers = df[(df["position"] == p["position"]) & (df["minutes"] >= 90)]
        r_vals = []
        labels_r = []

        for col_k, lbl in radar_axes:
            if col_k in peers.columns and col_k in p:
                p_val = float(p[col_k]) if pd.notna(p[col_k]) else 0.0
                pctv = round(100.0 * (peers[col_k] <= p_val).mean(), 1)
                r_vals.append(pctv)
                labels_r.append(lbl)

        if r_vals:
            fig_p_radar = go.Figure()
            fig_p_radar.add_trace(go.Scatterpolar(
                r=r_vals + [r_vals[0]],
                theta=labels_r + [labels_r[0]],
                fill="toself",
                fillcolor="rgba(204, 255, 0, 0.22)",
                name=sel_pname,
                line=dict(color="#ccff00", width=3),
            ))
            fig_p_radar.add_trace(go.Scatterpolar(
                r=[50] * (len(labels_r) + 1),
                theta=labels_r + [labels_r[0]],
                name="Positional Median (50th Percentile)",
                line=dict(color="#64748b", dash="dash", width=1.8),
            ))
            fig_p_radar.update_layout(
                paper_bgcolor="#111612",
                plot_bgcolor="#111612",
                font=dict(family="Inter, sans-serif", color="#94A3B8", size=11),
                polar=dict(
                    bgcolor="#111612",
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.08)"),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.08)"),
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
                margin=dict(l=35, r=35, t=20, b=45),
                height=350,
            )
            st.plotly_chart(fig_p_radar, width="stretch")

    with col_p_right:
        # AI Player Similarity Top 5
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('cpu')} AI Player Similarity (Top 5 Matches)</div>", unsafe_allow_html=True)

        sim_path = os.path.join(ROOT, "data", "processed", "analytics", "similarity_matrix.parquet")
        if os.path.exists(sim_path):
            try:
                sim = pd.read_parquet(sim_path)
                target = next((x for x in sim.index if f"#{pid}" in x or x == sel_pname), None)
                if target:
                    top5 = sim.loc[target].drop(target, errors="ignore").sort_values(ascending=False).head(5)
                    st.markdown('<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:18px;margin-bottom:20px">', unsafe_allow_html=True)
                    for nm, sval in top5.items():
                        parts = nm.rsplit(" #", 1)
                        clean_target_name = clean_name(parts[0])
                        sim_pid = parts[1].strip() if len(parts) == 2 else None
                        pct_sim = round(min(max(float(sval), 0.0), 1.0) * 100, 1)
                        c_av, c_inf = st.columns([0.12, 0.88])
                        with c_av:
                            st.markdown(player_avatar_html(sim_pid, clean_target_name, 48), unsafe_allow_html=True)
                        with c_inf:
                            st.markdown(f"**{clean_target_name}** — `{pct_sim}%` similarity")
                            st.progress(min(max(float(sval), 0.0), 1.0))
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No direct similarity vector found for this player.")
            except Exception as e:
                st.info("Similarity matrix loading error.")
        else:
            st.info("Run `python src/analytics/player_similarity.py` to generate similarity vectors.")

        # Post-Tournament Market Value Estimation
        if mv is not None:
            mrow = mv[mv["player_id"] == pid]
            if not mrow.empty:
                r_mv = mrow.iloc[0]
                st.markdown(f"<div class='section-header' style='font-size:20px'>{icon_badge('money')} Market Value AI Regression</div>", unsafe_allow_html=True)
                v_pre = float(r_mv["current_value"]) / 1e6
                v_post = float(r_mv["predicted_post_value"]) / 1e6
                chg = float(r_mv["change_pct"])

                st.markdown(
                    f'<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:18px">'
                    f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;text-align:center">'
                    f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">PRE-TOURNAMENT</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#FFFFFF">€{v_pre:.1f}M</div></div>'
                    f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">PREDICTED POST</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#ccff00">€{v_post:.1f}M</div></div>'
                    f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">NET CHANGE</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:{"#00e676" if chg>=0 else "#ff5252"}">{chg:+.1f}%</div></div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Validation: du bao vs gia tri that 8/2026 (Transfermarkt)
        val_path = os.path.join(ROOT, "data", "processed", "analytics",
                                "market_value_validation.csv")
        if os.path.exists(val_path):
            val_df = pd.read_csv(val_path)
            st.markdown(f"<div class='section-header' style='font-size:20px'>{icon_badge('target')} Validation vs Real Values (Aug 2026 - Transfermarkt)</div>", unsafe_allow_html=True)
            # Hien thi don vi trieu Euro cho de doc
            for _c in ("real_value_eur_2026_08", "current_value", "predicted_post_value"):
                val_df[_c] = (pd.to_numeric(val_df[_c], errors="coerce") / 1e6).round(1)
            disp_val = val_df.rename(columns={
                "player_name": "Player", "team": "National Team",
                "real_value_eur_2026_08": "Real Aug 2026 (€M)",
                "current_value": "Dataset Pre-WC (€M)",
                "predicted_post_value": "Model Predicted (€M)",
                "dev_pred_pct": "Dev: Predicted vs Real (%)",
                "dev_cur_pct": "Dev: Dataset vs Real (%)",
            })
            st.dataframe(disp_val, width='stretch', hide_index=True, column_config={
                "Real Aug 2026 (€M)": cfg_num("Real Aug 2026 (€M)", "%.1f"),
                "Dataset Pre-WC (€M)": cfg_num("Dataset Pre-WC (€M)", "%.1f"),
                "Model Predicted (€M)": cfg_num("Model Predicted (€M)", "%.1f"),
                "Dev: Predicted vs Real (%)": st.column_config.NumberColumn(
                "Dev: Predicted vs Real (%)", format="+%.1f"),
                "Dev: Dataset vs Real (%)": st.column_config.NumberColumn(
                "Dev: Dataset vs Real (%)", format="+%.1f")})
            mae_v = float(val_df["dev_pred_pct"].abs().mean())
            std_v = float(val_df["dev_pred_pct"].std())
            hit_v = float((val_df["dev_pred_pct"].abs() <= 25).mean() * 100)
            st.caption(
                f"n={len(val_df)} stars | MAE du bao: {mae_v:.1f}% | "
                f"do lech chuan: {std_v:.1f}% | {hit_v:.0f}% trong +-25% | "
                f"gia pre-WC dataset rat sat that (MAE {val_df['dev_cur_pct'].abs().mean():.1f}%) - model over-estimate."
            )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
