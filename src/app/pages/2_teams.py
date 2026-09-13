# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Teams & Tactical Profiles."""
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

from helpers import q, load_analytics_csv  # noqa: E402
from media_ui import flag_image, player_portrait, render_photo_story  # noqa: E402

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Teams & Squads | WorldCup Stats '26",
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
from navigation import nav_link, render_navigation
from table_ui import data_table
render_navigation('Teams')

render_photo_story(
    "NATIONAL TEAM DIRECTORY / 2026",
    "48 NATIONS.",
    "ONE CUP.",
    "Squads, tactical identities and every route through the tournament.",
    index="6 CONFEDERATIONS",
    page="teams",
)


# ── Load Aggregated Teams Dataset ─────────────────────────────────────────────
sql_teams = """
    SELECT t.team_id AS ID,
           t.team_name AS Team,
           t.fifa_code AS Code,
           t.group_letter AS Group_Letter,
           t.confederation AS Confederation,
           t.fifa_ranking_pre_tournament AS FIFA_Rank,
           t.manager_name AS Manager,
           COUNT(m.match_id) AS Matches_Played,
           SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score >m.away_score) OR (m.away_team_id=t.team_id AND m.away_score >m.home_score) THEN 1 ELSE 0 END) AS Wins,
           SUM(CASE WHEN m.home_score = m.away_score AND m.match_id IS NOT NULL THEN 1 ELSE 0 END) AS Draws,
           SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score < m.away_score) OR (m.away_team_id=t.team_id AND m.away_score < m.home_score) THEN 1 ELSE 0 END) AS Losses,
           COALESCE(SUM(CASE WHEN m.home_team_id=t.team_id THEN m.home_score WHEN m.away_team_id=t.team_id THEN m.away_score END), 0) AS Goals_For,
           COALESCE(SUM(CASE WHEN m.home_team_id=t.team_id THEN m.away_score WHEN m.away_team_id=t.team_id THEN m.home_score END), 0) AS Goals_Against
    FROM teams t
    LEFT JOIN matches m ON m.home_team_id=t.team_id OR m.away_team_id=t.team_id
    GROUP BY t.team_id
"""
df_teams = q(sql_teams)
df_teams["Team"] = df_teams["Team"].apply(clean_name)
df_teams["Goal_Diff"] = df_teams["Goals_For"] - df_teams["Goals_Against"]

# Load Squad Values
sq_val = q("""
    SELECT t.team_id,
           ROUND(SUM(s.market_value_eur) / 1e6, 1) AS Squad_Value_MEur,
           COUNT(s.player_id) AS Squad_Size
    FROM teams t
    LEFT JOIN squads_and_players s ON s.team_id = t.team_id
    GROUP BY t.team_id
""")
df_teams = df_teams.merge(sq_val, left_on="ID", right_on="team_id", how="left")
df_teams["Squad_Value_MEur"] = df_teams["Squad_Value_MEur"].fillna(0.0)

# Merge AI Cluster Labels if available
tc = load_analytics_csv("team_clusters.csv")
if tc is not None and "team_name" in tc.columns:
    tc["team_name"] = tc["team_name"].apply(clean_name)
    df_teams = df_teams.merge(tc[["team_name", "cluster_label"]], left_on="Team", right_on="team_name", how="left")
    df_teams["AI_Cluster"] = df_teams["cluster_label"].fillna("Standard Profile")
    df_teams = df_teams.drop(columns=["team_name", "cluster_label"], errors="ignore")
else:
    df_teams["AI_Cluster"] = "Standard Profile"

tot_val = round(df_teams["Squad_Value_MEur"].sum() / 1000, 1)
avg_val = int(round(df_teams["Squad_Value_MEur"].mean()))


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span>TEAM DIRECTORY</div>'
    '<div class="wc-hero-dates">48 QUALIFIED NATIONS · 6 CONFEDERATIONS</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">TOURNAMENT</span>'
    '<span class="title-lime">TEAMS.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Comprehensive team dossiers for all 48 national squads competing in the 2026 FIFA World Cup. '
    'Inspect market valuations, official 26-man squads, tactical radar footprints, and AI cluster styles.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="kpi-row-container" style="margin-bottom:28px">'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{len(df_teams)}</div><div class="kpi-sport-label">NATIONS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">6</div><div class="kpi-sport-label">CONFEDERATIONS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">€{tot_val}B</div><div class="kpi-sport-label">TOTAL MARKET VALUE</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">€{avg_val}M</div><div class="kpi-sport-label">AVG SQUAD VALUE</div></div>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Team Selection & Deep-Dive Profile ────────────────────────────────────────
st.markdown(
    '<div class="tm-select-head"><span class="tm-dot"></span>'
    'SELECT NATIONAL TEAM<span class="tm-year">/ 2026</span></div>',
    unsafe_allow_html=True,
)

col_s1, col_s2 = st.columns([1.2, 1.8])

with col_s1:
    confed_list = ["All Confederations"] + sorted(df_teams["Confederation"].dropna().unique().tolist())
    sel_confed = st.selectbox("Filter by Confederation", confed_list)

filtered_teams = df_teams.copy()
if sel_confed != "All Confederations":
    filtered_teams = filtered_teams[filtered_teams["Confederation"] == sel_confed]

team_options = {}
for _, r in filtered_teams.sort_values("Team").iterrows():
    t_name = r["Team"]
    fl = flag(t_name)
    opt_label = f"{fl} {t_name} ({r['Confederation']})"
    team_options[opt_label] = t_name

with col_s2:
    sel_opt = st.selectbox(
        "Choose team to inspect complete dossier:",
        list(team_options.keys()) if team_options else ["No teams available"]
    )

selected_team = team_options.get(sel_opt, df_teams["Team"].iloc[0] if not df_teams.empty else "Spain")


# ── Team Dossier Presentation ─────────────────────────────────────────────────
if selected_team:
    t_row = df_teams[df_teams["Team"] == selected_team].iloc[0]
    t_flag = flag(selected_team)
    t_flag_img = flag_image(selected_team, t_row.get("Code"), "team-flag-photo")
    t_mgr = clean_name(t_row.get("Manager", "Unknown"))
    t_rank = int(t_row["FIFA_Rank"]) if pd.notna(t_row.get("FIFA_Rank")) else "N/A"
    t_val = float(t_row.get("Squad_Value_MEur", 0.0))
    t_cluster = t_row.get("AI_Cluster", "Standard Profile")
    t_wins = int(t_row["Wins"])
    t_draws = int(t_row["Draws"])
    t_losses = int(t_row["Losses"])
    t_gf = int(t_row["Goals_For"])
    t_ga = int(t_row["Goals_Against"])
    t_gd = int(t_row["Goal_Diff"])
    t_mp = int(t_row["Matches_Played"])

    # Hero Team Showcase Card
    st.markdown(
        f'<div class="match-hero-card">'
        f'<div class="match-hero-meta">'
        f'<div><span class="match-stage-badge">{t_row["Confederation"]}</span> '
        f'<span style="background:rgba(255,255,255,0.08);color:#f2f1ec;border:1px solid rgba(255,255,255,0.35);border-radius:0;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px">Group {t_row.get("Group_Letter", "-")}</span> '
        f'<span style="background:rgba(232,232,227,0.12);color:#e8e8e3;border:1px solid rgba(232,232,227,0.35);border-radius:0;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px"> {t_cluster}</span></div>'
        f'<div class="match-venue-text">FIFA Rank: <strong>#{t_rank}</strong> &nbsp;·&nbsp; Head Coach: <strong>{t_mgr}</strong></div>'
        f'</div>'
        f'<div class="match-scoreboard-main" style="margin:14px 0">'
        f'<div style="display:flex;align-items:center;gap:18px">'
        f'{t_flag_img}'
        f'<div>'
        f'<div class="match-team-name-big" style="font-size:36px">{selected_team}</div>'
        f'<div style="color:#94a3b8;font-size:13px;font-weight:600;letter-spacing:1px;text-transform:uppercase">{t_row["Code"]} · {t_row["Confederation"]}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex;gap:20px;align-items:center">'
        f'<div style="text-align:right">'
        f'<div style="font-size:11px;font-weight:800;color:#64748b;letter-spacing:1.2px;text-transform:uppercase">TOURNAMENT RECORD</div>'
        f'<div style="font-family:var(--font-sport);font-size:26px;font-weight:900;color:#FFFFFF">{t_wins}W &nbsp;{t_draws}D &nbsp;{t_losses}L</div>'
        f'<div style="font-size:12.5px;color:#94a3b8">{t_gf} scored · {t_ga} conceded ({t_gd:+d})</div>'
        f'</div>'
        f'<div style="text-align:right;border-left:1px solid rgba(255,255,255,0.08);padding-left:20px">'
        f'<div style="font-size:11px;font-weight:800;color:#64748b;letter-spacing:1.2px;text-transform:uppercase">SQUAD VALUATION</div>'
        f'<div style="font-family:var(--font-sport);font-size:26px;font-weight:900;color:#e8e8e3">€{t_val:.0f}M</div>'
        f'<div style="font-size:12.5px;color:#94a3b8">26 Players Roster</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Dossier styles (scoped .tm-, editorial dark) ──
    st.markdown(
        '<style>'
        '.tm-select-head{display:flex;align-items:center;gap:10px;font-size:30px;font-weight:900;'
        'letter-spacing:-0.5px;color:#fff;text-transform:uppercase;margin:6px 0 14px;}'
        '.tm-dot{width:9px;height:9px;border-radius:50%;background:#fff;flex:0 0 auto;}'
        '.tm-year{font-size:11px;font-weight:600;letter-spacing:1px;color:#6b7280;}'
        '.tm-panel{background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;'
        'padding:16px 16px 14px;margin-bottom:16px;min-width:0;}'
        '[data-testid="stVerticalBlockBorderWrapper"]{background:#0e0e0e;border:0;border-top:1px solid rgba(255,255,255,0.18);'
        'border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;margin-bottom:16px;}'
        '[data-testid="stVerticalBlockBorderWrapper"] > div{padding:16px 16px 14px;}'
        '.tm-panel-head{display:flex;align-items:center;gap:9px;font-size:14px;font-weight:800;'
        'letter-spacing:1.2px;color:#f3f2ed;text-transform:uppercase;margin-bottom:12px;min-width:0;flex-wrap:wrap;}'
        '.tm-panel-head .tm-dot{width:8px;height:8px;}'
        '.tm-panel-head .tm-year{margin-left:auto;white-space:nowrap;}'
        '.tm-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px;}'
        '.tm-kpi{background:#111111;border:0;border-left:1px solid rgba(255,255,255,0.12);border-radius:0;'
        'padding:10px 12px;min-width:0;}'
        '.tm-kpi-lbl{font-size:9.5px;font-weight:700;letter-spacing:1px;color:#8a8f98;text-transform:uppercase;'
        'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
        '.tm-kpi-val{font-size:21px;font-weight:900;color:#fff;margin-top:2px;}'
        '.tm-kpi-delta{font-size:11px;font-weight:700;}'
        '.tm-kpi-sub{font-size:10px;color:#6b7280;}'
        '.up{color:#00e676;}.dn{color:#ff5252;}'
        '.tm-match{display:flex;align-items:center;gap:10px;min-width:0;padding:9px 10px;'
        'background:rgba(255,255,255,0.02);border:0;border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;margin-bottom:8px;}'
        '.tm-match-date{flex:0 0 74px;font-size:10.5px;color:#8a8f98;line-height:1.5;}'
        '.tm-match-mid{flex:1 1 auto;display:flex;align-items:center;justify-content:center;gap:8px;min-width:0;'
        'font-size:13px;font-weight:600;color:#e8e8e3;}'
        '.tm-match-mid .media-flag{flex:0 0 auto;}'
        '.tm-match-team{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
        '.tm-match-score{font-size:16px;font-weight:900;color:#fff;white-space:nowrap;}'
        '.tm-badge{flex:0 0 auto;font-size:10px;font-weight:800;letter-spacing:0.8px;border-radius:6px;padding:4px 10px;}'
        '.tm-badge.win{background:rgba(0,230,118,0.14);color:#00e676;}'
        '.tm-badge.draw{background:rgba(255,255,255,0.09);color:#cbd5e1;}'
        '.tm-badge.loss{background:rgba(255,82,82,0.14);color:#ff5252;}'
        '.tm-roster-wrap{display:flex;align-items:stretch;gap:8px;}'
        '.tm-roster-nav{flex:0 0 auto;align-self:center;width:30px;height:64px;background:#11141b;'
        'border:1px solid rgba(255,255,255,0.10);border-radius:8px;color:#cbd5e1;font-size:15px;cursor:pointer;}'
        '.tm-roster-nav:hover{background:#1b2029;color:#fff;}'
        '.tm-roster-rail{display:flex;flex-wrap:nowrap;gap:10px;overflow-x:auto;flex:1 1 auto;min-width:0;'
        'padding:2px 2px 6px;scrollbar-width:thin;scrollbar-color:#2e2e2e transparent;}'
        '.tm-roster-rail::-webkit-scrollbar{height:6px;}'
        '.tm-roster-rail::-webkit-scrollbar-track{background:transparent;}'
        '.tm-roster-rail::-webkit-scrollbar-thumb{background:#2e2e2e;border-radius:3px;}'
        '.tm-rcard{flex:0 0 208px;width:208px;display:flex;gap:10px;background:#111111;'
        'border:0;border-top:1px solid rgba(255,255,255,0.12);border-bottom:1px solid rgba(255,255,255,0.08);border-radius:0;padding:10px;min-width:0;}'
        '.tm-rcard:hover{border-color:rgba(255,255,255,0.24);}'
        '.tm-rcard .player-portrait{flex:0 0 76px;width:76px !important;height:96px !important;'
        'border-radius:6px;border:1px solid rgba(255,255,255,0.10) !important;}'
        '.tm-rcard-info{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:3px;}'
        '.tm-rcard-name{font-size:13px;font-weight:700;color:#f3f2ed;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
        '.tm-pos{display:inline-block;font-size:9.5px;font-weight:800;letter-spacing:0.8px;color:#f2f1ec;'
        'background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.30);border-radius:0;padding:1px 7px;}'
        '.tm-rcard-sub{font-size:11px;color:#a7abb3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
        '.tm-rcard-club{font-size:11px;color:#8a8f98;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}'
        '@media (max-width:900px){.tm-kpis{grid-template-columns:repeat(2,1fr);}'
        '.tm-select-head{font-size:22px;}.tm-match-date{flex-basis:60px;}}'
        '</style>',
        unsafe_allow_html=True,
    )

    col_t_left, col_t_right = st.columns([1.15, 1.0], gap="large")

    with col_t_left:
        # Tactical Radar Footprint (computations unchanged)
        per_match = q("""
            SELECT AVG(x.possession_pct) AS possession,
                   AVG(x.total_shots) AS shots,
                   AVG(x.shots_on_target) AS sot,
                   AVG(x.corners) AS corners,
                   AVG(x.saves) AS saves,
                   AVG(x.fouls) AS fouls
            FROM match_team_stats x
            WHERE x.team_id IN (SELECT team_id FROM teams WHERE team_name = ?)
              AND x.match_id IN (
                  SELECT match_id FROM matches
                  WHERE home_team_id = x.team_id OR away_team_id = x.team_id)
        """, (selected_team,))

        league_avg = q("""
            SELECT AVG(possession_pct) AS possession,
                   AVG(total_shots) AS shots,
                   AVG(shots_on_target) AS sot,
                   AVG(corners) AS corners,
                   AVG(saves) AS saves,
                   AVG(fouls) AS fouls
            FROM match_team_stats
        """)

        tourn_avg = q("""
            SELECT COALESCE(SUM(home_score + away_score), 0) * 1.0 / NULLIF(COUNT(*), 0) AS gpm
            FROM matches
        """)
        tourn_gpm = float(tourn_avg.iloc[0]["gpm"]) if not tourn_avg.empty and pd.notna(tourn_avg.iloc[0]["gpm"]) else 0.0
        team_gpm = (t_gf / t_mp) if t_mp > 0 else 0.0

        has_stats = not per_match.empty and pd.notna(per_match.iloc[0]["possession"])
        vals = [0.0] * 6
        lavgs = [1.0] * 6
        if has_stats:
            axes = ["Possession %", "Total Shots", "Shots on Target", "Corner Kicks", "Defensive Saves", "Fouls"]
            metric_keys = ["possession", "shots", "sot", "corners", "saves", "fouls"]

            vals = [float(per_match.iloc[0][k]) if pd.notna(per_match.iloc[0][k]) else 0.0 for k in metric_keys]
            lavgs = [float(league_avg.iloc[0][k]) if pd.notna(league_avg.iloc[0][k]) else 1.0 for k in metric_keys]

            # Scaled normalized score (50 is exact league average)
            pct = [round(min(max((v / max(l, 1e-6)) * 50.0, 10.0), 95.0), 1) for v, l in zip(vals, lavgs)]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=pct + [pct[0]],
                theta=axes + [axes[0]],
                fill="toself",
                # Muted aqua keeps the selected team legible on black without
                # introducing a neon accent into the minimal visual system.
                fillcolor="rgba(168, 218, 220, 0.22)",
                name=selected_team,
                line=dict(color="#a8dadc", width=2.5),
                marker=dict(color="#a8dadc", size=4),
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[50] * (len(axes) + 1),
                theta=axes + [axes[0]],
                name="Tournament Avg (Baseline 50)",
                line=dict(color="#d7c3a3", dash="dash", width=1.6),
            ))
            fig_radar.update_layout(
                paper_bgcolor="#000000",
                plot_bgcolor="#000000",
                font=dict(family="Inter, sans-serif", color="#a7abb3", size=11),
                polar=dict(
                    bgcolor="#000000",
                    radialaxis=dict(visible=True, range=[0, 100],
                                    gridcolor="rgba(255,255,255,0.10)",
                                    linecolor="rgba(255,255,255,0.12)",
                                    tickfont=dict(color="#6b7280", size=9)),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.10)",
                                     linecolor="rgba(255,255,255,0.12)"),
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
                            font=dict(size=10)),
                margin=dict(l=35, r=35, t=20, b=45),
                height=340,
            )

        if has_stats:
            d_poss, d_shots, d_sot = vals[0] - lavgs[0], vals[1] - lavgs[1], vals[2] - lavgs[2]
            d_gpm = team_gpm - tourn_gpm

            def _drow(lbl, val_txt, d, d_txt):
                cls = "up" if d >= 0 else "dn"
                arrow = "▲" if d >= 0 else "▼"
                return (
                    '<div class="tm-kpi"><div class="tm-kpi-lbl">' + lbl + '</div>'
                    f'<div class="tm-kpi-val">{val_txt} '
                    f'<span class="tm-kpi-delta {cls}">{arrow} {d_txt}</span></div>'
                    '<div class="tm-kpi-sub">vs. tournament avg</div></div>'
                )

            with st.container(border=True):
                st.markdown(
                    '<div class="tm-panel-head"><span class="tm-dot"></span>'
                    'TACTICAL RADAR PROFILE (VS TOURNAMENT AVERAGE)'
                    '<span class="tm-year">/ 2026</span></div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(fig_radar, width="stretch")
                st.markdown(
                    '<div class="tm-kpis">'
                    + _drow("Avg Possession", f"{vals[0]:.1f}%", d_poss, f"{d_poss:+.1f}%")
                    + _drow("Avg Shots / 90", f"{vals[1]:.1f}", d_shots, f"{d_shots:+.1f}")
                    + _drow("Shots on Target", f"{vals[2]:.1f}", d_sot, f"{d_sot:+.1f}")
                    + _drow("Goals per Match", f"{team_gpm:.1f}", d_gpm, f"{d_gpm:+.1f}")
                    + '</div>',
                    unsafe_allow_html=True,
                )
        else:
            with st.container(border=True):
                st.markdown(
                    '<div class="tm-panel-head"><span class="tm-dot"></span>'
                    'TACTICAL RADAR PROFILE (VS TOURNAMENT AVERAGE)'
                    '<span class="tm-year">/ 2026</span></div>',
                    unsafe_allow_html=True,
                )
            st.info("Match statistics not yet accumulated for this team.")

    with col_t_right:
        # Tournament Matches of this Team (query unchanged)
        m_list = q("""
            SELECT d.date AS Date, d.stage_name AS Stage,
                   d.home_team_name AS Home_Team, d.home_score AS Home_Score,
                   d.away_score AS Away_Score, d.away_team_name AS Away_Team,
                   d.result_type AS Result_Type
            FROM matches_detailed d
            WHERE d.home_team_name = ? OR d.away_team_name = ?
            ORDER BY d.date
        """, (selected_team, selected_team))

        with st.container(border=True):
            hc1, hc2 = st.columns([3, 1.6], gap="small", vertical_alignment="center")
            with hc1:
                st.markdown(
                    '<div class="tm-panel-head"><span class="tm-dot"></span>MATCH RESULTS'
                    '<span class="tm-year">/ 2026</span></div>',
                    unsafe_allow_html=True,
                )
            with hc2:
                nav_link("pages/1_matches.py", "View All Matches →")
            if not m_list.empty:
                rows_html = ""
                for _, mr in m_list.iterrows():
                    h_name = clean_name(mr["Home_Team"])
                    a_name = clean_name(mr["Away_Team"])
                    hs = int(mr["Home_Score"])
                    as_ = int(mr["Away_Score"])

                    # Determine Win/Draw/Loss badge for the selected team
                    if (h_name == selected_team and hs > as_) or (a_name == selected_team and as_ > hs):
                        res_badge = '<span class="tm-badge win">WIN</span>'
                    elif hs == as_:
                        res_badge = '<span class="tm-badge draw">DRAW</span>'
                    else:
                        res_badge = '<span class="tm-badge loss">LOSS</span>'

                    rows_html += (
                        '<div class="tm-match">'
                        f'<div class="tm-match-date">{html_lib.escape(str(mr["Date"]))}<br>'
                        f'{html_lib.escape(str(mr["Stage"]))}</div>'
                        f'<div class="tm-match-mid">'
                        f'{flag_image(h_name, class_name="media-flag is-small")}'
                        f'<span class="tm-match-team">{html_lib.escape(h_name)}</span>'
                        f'<span class="tm-match-score">{hs} - {as_}</span>'
                        f'<span class="tm-match-team">{html_lib.escape(a_name)}</span>'
                        f'{flag_image(a_name, class_name="media-flag is-small")}'
                        f'</div>'
                        f'{res_badge}'
                        '</div>'
                    )
                st.markdown(rows_html, unsafe_allow_html=True)
            else:
                st.info("No matches recorded for this team.")

        # ── Squad roster carousel (query unchanged — layout only) ──
        squad_list = q("""
            SELECT s.player_name AS Player, s.position AS Pos,
                   s.club_team AS Club, s.caps AS Caps,
                   s.height_cm AS Height_cm,
                   ROUND(s.market_value_eur / 1e6, 1) AS Value_MEur
            FROM squads_and_players s
            JOIN teams t ON t.team_id = s.team_id
            WHERE t.team_name = ?
            ORDER BY s.position, Value_MEur DESC
        """, (selected_team,))

        if not squad_list.empty:
            squad_list["Player"] = squad_list["Player"].apply(clean_name)
            n_squad = len(squad_list)
            cards_html = ""
            for name, pos, caps, club in squad_list[["Player", "Pos", "Caps", "Club"]].itertuples(index=False, name=None):
                pos_txt = html_lib.escape(str(pos)) if pd.notna(pos) else "—"
                try:
                    caps_txt = f"{int(float(caps))} caps" if pd.notna(caps) else ""
                except (TypeError, ValueError):
                    caps_txt = ""
                club_txt = clean_name(club) if pd.notna(club) else ""
                cards_html += (
                    '<article class="tm-rcard">'
                    + player_portrait(name, "player-portrait")
                    + '<div class="tm-rcard-info">'
                    f'<div class="tm-rcard-name">{html_lib.escape(name)}</div>'
                    f'<div><span class="tm-pos">{pos_txt}</span></div>'
                    + (f'<div class="tm-rcard-sub">{html_lib.escape(caps_txt)}</div>' if caps_txt else "")
                    + (f'<div class="tm-rcard-club">{html_lib.escape(club_txt)}</div>' if club_txt else "")
                    + '</div></article>'
                )
            with st.container(border=True):
                rc1, rc2 = st.columns([3, 1.6], gap="small", vertical_alignment="center")
                with rc1:
                    st.markdown(
                        '<div class="tm-panel-head"><span class="tm-dot"></span>'
                        'OFFICIAL 26-MAN SQUAD ROSTER'
                        f'<span class="tm-year">{n_squad} PLAYERS / 2026</span></div>',
                        unsafe_allow_html=True,
                    )
                with rc2:
                    nav_link("pages/3_players.py", "View Full Squad →")
                st.markdown(
                    '<div class="tm-roster-wrap">'
                    '<button class="tm-roster-nav" '
                    'onclick="document.getElementById(\'tmRosterRail\').scrollBy({left:-440,behavior:\'smooth\'})" '
                    'aria-label="Scroll roster left">←</button>'
                    f'<div class="tm-roster-rail" id="tmRosterRail">{cards_html}</div>'
                    '<button class="tm-roster-nav" '
                    'onclick="document.getElementById(\'tmRosterRail\').scrollBy({left:440,behavior:\'smooth\'})" '
                    'aria-label="Scroll roster right">→</button>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            with st.expander("Full squad register (table)", expanded=False):
                table_df = squad_list.copy()
                table_df.columns = ["Player", "Position", "Club Team", "Caps", "Height (cm)", "Value (€M)"]
                data_table(table_df, width="stretch", height=280, label="Official squad register")

# ── Full 48-Teams Tournament Standings Table ──────────────────────────────────
with st.container(border=True):
    st.markdown(
        '<div class="tm-panel-head"><span class="tm-dot"></span>'
        'ALL 48 NATIONS OVERVIEW &amp; TACTICAL CLUSTERS'
        '<span class="tm-year">/ 2026</span></div>',
        unsafe_allow_html=True,
    )
    f_n1, f_n2, f_n3 = st.columns([1.4, 1.0, 1.0])
    with f_n1:
        search_nation = st.text_input("Search nations...", value="", placeholder="Search nations...")
    with f_n2:
        confed_opts = ["All Confederations"] + sorted(df_teams["Confederation"].dropna().unique().tolist())
        sel_confed_tbl = st.selectbox("Confederation", confed_opts, key="nations_confed")
    with f_n3:
        style_opts = ["All Tactical Styles"] + sorted(df_teams["AI_Cluster"].dropna().unique().tolist())
        sel_style_tbl = st.selectbox("Tactical style", style_opts, key="nations_style")

    display_teams = df_teams[["Team", "Confederation", "Group_Letter", "FIFA_Rank", "Manager", "Matches_Played", "Wins", "Draws", "Losses", "Goals_For", "Goals_Against", "Goal_Diff", "Squad_Value_MEur", "AI_Cluster"]].copy()
    display_teams.columns = ["Nation", "Confederation", "Group", "FIFA Rank", "Head Coach", "P", "W", "D", "L", "GF", "GA", "GD", "Value (€M)", "AI Tactical Style"]
    if search_nation:
        display_teams = display_teams[display_teams["Nation"].str.contains(search_nation, case=False, na=False)]
    if sel_confed_tbl != "All Confederations":
        display_teams = display_teams[display_teams["Confederation"] == sel_confed_tbl]
    if sel_style_tbl != "All Tactical Styles":
        display_teams = display_teams[display_teams["AI Tactical Style"] == sel_style_tbl]

    code_map = dict(zip(df_teams["Team"], df_teams["Code"]))
    display_teams.insert(
        0, "Flag",
        display_teams["Nation"].map(
            lambda n: f"https://api.fifa.com/api/v3/picture/flags-sq-4/{code_map.get(n, '')}"
            if code_map.get(n) else ""
        ),
    )

    data_table(
        display_teams.sort_values(["W", "GD", "GF"], ascending=[False, False, False]),
        width="stretch",
        label="Nation performance index",
        column_config={"Flag": st.column_config.ImageColumn("Flag", help="National flag", width="small")},
    )


# ── AI Tactical Cluster Analysis Summary ──────────────────────────────────────
if tc is not None and "cluster_label" in tc.columns:
    st.markdown("<div class='section-header'>AI Cluster Characteristics Breakdown</div>", unsafe_allow_html=True)

    stat_feature_cols = [c for c in ["possession", "shots", "sot", "corners", "saves", "gf", "ga", "gd"] if c in tc.columns]
    if stat_feature_cols:
        cluster_summary = tc.groupby("cluster_label")[stat_feature_cols].mean().round(2).reset_index()
        cluster_summary.columns = ["AI Tactical Style", "Avg Possession %", "Avg Shots", "Avg SOT", "Avg Corners", "Avg Saves", "Avg Goals For", "Avg Goals Against", "Avg Goal Diff"]
        data_table(cluster_summary, width="stretch", label="AI tactical cluster index")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
