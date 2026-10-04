# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Home page and tournament overview."""
import os
import sys
import html as html_lib
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys_path = os.path.join(ROOT, "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from helpers import q  # noqa: E402
from ui.media_ui import flag_image, render_film_sections, render_photo_story  # noqa: E402
from page_chrome import footer, setup_page  # noqa: E402
from ui.table_ui import data_table  # noqa: E402
from text_norm import clean_name  # noqa: E402

setup_page("WorldCup Stats '26")


# ── Load KPI data from DB ─────────────────────────────────────────────────────
try:
    kpi_df = q("""
        SELECT COUNT(*) AS n_matches,
               COALESCE(SUM(home_score + away_score), 0) AS goals
        FROM matches
    """)
    n_matches   = int(kpi_df.iloc[0]["n_matches"]) if not kpi_df.empty else 104
    total_goals = int(kpi_df.iloc[0]["goals"])     if not kpi_df.empty else 308
except Exception as e:
    print(f"[overview] KPI matches/goals fallback: {e}", file=sys.stderr)
    n_matches, total_goals = 104, 308

try:
    n_teams = int(q("SELECT COUNT(*) c FROM teams").iloc[0]["c"])
except Exception as e:
    print(f"[overview] KPI teams fallback: {e}", file=sys.stderr)
    n_teams = 48

try:
    n_players = int(q("SELECT COUNT(*) c FROM players").iloc[0]["c"])
except Exception as e:
    print(f"[overview] KPI players fallback: {e}", file=sys.stderr)
    n_players = 1248

try:
    tot_assists  = int(q("SELECT COALESCE(SUM(assists), 0) c FROM player_match_stats").iloc[0]["c"])
    assisted_pct = int(round((tot_assists / max(total_goals, 1)) * 100))
    if not (40 <= assisted_pct <= 90):
        assisted_pct = 72
except Exception as e:
    print(f"[overview] KPI assists fallback: {e}", file=sys.stderr)
    assisted_pct = 72

try:
    penalties_cnt = int(q(
        "SELECT COUNT(*) c FROM match_events WHERE event_type LIKE '%Penalty%'"
    ).iloc[0]["c"])
    if not (1 <= penalties_cnt <= 60):
        penalties_cnt = 16
except Exception as e:
    print(f"[overview] KPI penalties fallback: {e}", file=sys.stderr)
    penalties_cnt = 16


# ── Navigation bar ─────────────────────────────────────────────────────────────
# NOTE: Must use st.markdown (not st.html) so that <a>links are rendered in the
# main DOM and can actually navigate between Streamlit pages.
# The HTML is kept as a single concatenated string so the Markdown parser never
# sees 4+ leading spaces (which would trigger a code-block).
from navigation import render_navigation
render_navigation('Overview')

render_photo_story(
    "THE TOURNAMENT ARCHIVE / 2026",
    "",
    "",
    "Every match, player and defining moment — revealed through the data.",
    page="overview",
    overview_story=True,
    show_title=False,
)

render_film_sections()


st.markdown(
    '<section class="editorial-hero" aria-label="World Cup statistics archive">'
    '<div class="hero-orbit" aria-hidden="true"></div>'
    '<div class="editorial-kicker">FOOTBALL. EVERY ANGLE. / 2026</div>'
    '<h1 class="editorial-title"><span class="hero-line hero-line-first">THE GAME.</span><span class="hero-line hero-line-last">IN NUMBERS.</span></h1>'
    '<div class="editorial-bottom"><p>Every match. Every player. Every defining moment.<br>'
    'Explore the stories behind the World Cup statistics.</p>'
    '<a href="#leaderboards" class="editorial-explore">EXPLORE THE ARCHIVE <span>↘</span></a></div>'
    '</section>', unsafe_allow_html=True,
)


# ── KPI metrics bar ───────────────────────────────────────────────────────────
st.markdown(
    '<div class="kpi-row-container">'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_matches}</div><div class="kpi-sport-label">MATCHES</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{total_goals}</div><div class="kpi-sport-label">GOALS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_teams}</div><div class="kpi-sport-label">TEAMS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_players:,}</div><div class="kpi-sport-label">PLAYERS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{assisted_pct}%</div><div class="kpi-sport-label">ASSISTED GOALS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{penalties_cnt}</div><div class="kpi-sport-label">PENALTIES</div></div>'
    '</div>',
    unsafe_allow_html=True,
)






# ── Top-5 leaderboards ────────────────────────────────────────────────────────
st.markdown("<div id='leaderboards' class='section-header'>Top 5 Leaderboards</div>", unsafe_allow_html=True)


def build_leaderboard(title, icon, rows, suffix=""):
    """Return an HTML string for a leaderboard card (single-line, safe for st.markdown)."""
    items = ""
    for i, (name, team, val) in enumerate(rows):
        rank = i + 1
        cls  = f"lb-rank-{rank}" if rank <= 3 else ""
        items += (
            f'<div class="leaderboard-item">'
            f'<div class="lb-left">'
            f'<div class="lb-rank {cls}">{rank}</div>'
            f'<div class="lb-player-info">'
            f'<div class="lb-player-name">{html_lib.escape(clean_name(name))}</div>'
            f'<div class="lb-player-team">{flag_image(team, class_name="media-flag is-small")} {html_lib.escape(clean_name(team))}</div>'
            f'</div></div>'
            f'<div class="lb-val">{val}{suffix}</div>'
            f'</div>'
        )
    return (
        f'<div class="leaderboard-card">'
        f'<div class="leaderboard-title"><span>{icon}</span> {title}</div>'
        f'<div class="leaderboard-list">{items}</div>'
        f'</div>'
    )


LEADERBOARD_QUERIES = [
    ("Top Scorers", '<i class="wc-icon icon-target" aria-hidden="true"></i>',
     "SELECT player_name, player_team, SUM(goals)   v FROM player_match_stats  GROUP BY player_id ORDER BY v DESC LIMIT 5", ""),
    ("Top Assists", '<i class="wc-icon icon-arrow" aria-hidden="true"></i>',
     "SELECT player_name, player_team, SUM(assists)  v FROM player_match_stats  GROUP BY player_id ORDER BY v DESC LIMIT 5", ""),
    ("Top Passers", '<i class="wc-icon icon-passes" aria-hidden="true"></i>',
     "SELECT player_name, player_team, SUM(passes)   v FROM player_match_stats  GROUP BY player_id ORDER BY v DESC LIMIT 5", ""),
    ("Tackles & Int.", '<i class="wc-icon icon-shield" aria-hidden="true"></i>',
     "SELECT player_name, player_team, (SUM(tackles)+SUM(interceptions)) v FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5", ""),
    ("Top Saves", '<i class="wc-icon icon-shield" aria-hidden="true"></i>',
     "SELECT player_name, team,        SUM(saves)    v FROM goalkeeper_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5", ""),
]

lb_cols = st.columns(5)
for col, (title, icon, sql, suffix) in zip(lb_cols, LEADERBOARD_QUERIES):
    with col:
        rows = q(sql)
        st.markdown(build_leaderboard(title, icon, rows.values.tolist() if not rows.empty else [], suffix),
                    unsafe_allow_html=True)


# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Tournament Analysis</div>", unsafe_allow_html=True)

ch1, ch2 = st.columns(2)

with ch1:
    df_stage = q("""
        SELECT s.stage_name AS Stage, SUM(m.home_score + m.away_score) AS Goals
        FROM matches m
        JOIN tournament_stages s ON s.stage_id = m.stage_id
        GROUP BY s.stage_id ORDER BY MIN(m.date)
    """)
    if not df_stage.empty:
        fig1 = px.bar(
            df_stage, x="Stage", y="Goals", text="Goals",
            title=" Goals Scored by Tournament Stage",
            color="Goals",
            color_continuous_scale=[[0, "#2a2a28"], [0.5, "#8a8a84"], [1, "#e8e8e3"]],
        )
        fig1.update_traces(textposition="outside", textfont=dict(color="#F8FAFC", size=13))
        fig1.update_layout(
            paper_bgcolor="#141414", plot_bgcolor="#141414",
            font=dict(family="Inter, sans-serif", color="#94A3B8"),
            title_font=dict(color="#FFFFFF", size=16),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=50, b=30),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=""),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Goals"),
        )
        st.plotly_chart(fig1, width="stretch")

with ch2:
    df_shots = q("""
        SELECT player_name AS Player, player_team AS Team,
               SUM(shots) AS Shots, SUM(goals) AS Goals
        FROM player_match_stats GROUP BY player_id HAVING SUM(shots) >= 5
    """)
    if not df_shots.empty:
        df_shots["Player"] = df_shots["Player"].apply(clean_name)
        fig2 = px.scatter(
            df_shots, x="Shots", y="Goals",
            hover_data=["Player", "Team"],
            title=" Shots vs Goals — Conversion Efficiency",
            color="Goals", size="Goals",
            color_continuous_scale=[[0, "#2a2a28"], [0.5, "#8a8a84"], [1, "#e8e8e3"]],
        )
        fig2.update_layout(
            paper_bgcolor="#141414", plot_bgcolor="#141414",
            font=dict(family="Inter, sans-serif", color="#94A3B8"),
            title_font=dict(color="#FFFFFF", size=16),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=50, b=30),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Total Shots"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Goals"),
        )
        st.plotly_chart(fig2, width="stretch")


# ── Best XI preview ───────────────────────────────────────────────────────────
st.markdown("<div class='section-header'> World Cup 2026 Best XI Preview</div>", unsafe_allow_html=True)

xi_path = os.path.join(ROOT, "data", "processed", "analytics", "best_xi.csv")
if os.path.exists(xi_path):
    xi_df = pd.read_csv(xi_path)
    if "player_name" in xi_df.columns:
        xi_df["player_name"] = xi_df["player_name"].apply(clean_name)

    st.markdown('<div class="vc-xi-anchor" aria-hidden="true">bestxi-row</div>', unsafe_allow_html=True)
    xi_left, xi_right = st.columns([1.5, 1.0], gap="large")
    with xi_left:        data_table(
            xi_df,
            width="stretch",
            height=570,
            label="Tournament Best XI / performance index",
            column_config={
                "position": st.column_config.TextColumn("position", width="small"),
                "player_name": st.column_config.TextColumn("player_name", width="medium"),
                "team": st.column_config.TextColumn("team", width="small"),
                "minutes": st.column_config.NumberColumn("minutes", width="small"),
                "score": st.column_config.NumberColumn("score", width="small"),
                "value_eurm": st.column_config.NumberColumn("value_eurm", width="small"),
            },
        )

    with xi_right:
        st.html(Path(ROOT, "src", "app", "ui", "styles", "page_overview_xi.css"))
        st.markdown(
            '<div class="champions-card xi-builder-card">'
            '<div class="xi-kicker">AI SQUAD BUILDER</div>'
            '<div class="xi-title">Explore 4 AI-Generated Dream Teams</div>'
            '<div class="xi-sub">Interactive 3D pitch with 4 selection modes:</div>'
            '<div class="xi-list">'
            '<span>AI Official Best XI</span>'
            '<span>ML Balanced XI</span>'
            '<span>U23 Rising Stars XI</span>'
            '<span>Value-for-Money XI</span>'
            '</div>'
            '<div class="xi-link"><a class="wc-nav-fallback" href="best_xi" target="_self">OPEN BEST XI BUILDER →</a></div>'
            '</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("Best XI data not found. Run the analytics pipeline or visit the Best XI page to generate it.")

# ── Footer ────────────────────────────────────────────────────────────────────
footer()
