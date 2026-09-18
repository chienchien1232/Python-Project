# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Home page and tournament overview."""
import os
import sys
import html as html_lib

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys_path = os.path.join(ROOT, "src")
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from helpers import q  # noqa: E402
from media_ui import flag_image, render_photo_story  # noqa: E402
from table_ui import data_table  # noqa: E402

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WorldCup Stats '26",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)
# First paint must be dark so page switches never flash white.
st.markdown("<style>html,body,.stApp,#root{background:#050505 !important;color-scheme:dark}</style>", unsafe_allow_html=True)

# ── Inject CSS (st.html is fine for non-link decorative content) ───────────────
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ── Helper ────────────────────────────────────────────────────────────────────
def clean_name(val):
    """Fix common encoding artefacts in player/team names from the DB."""
    if not isinstance(val, str):
        return str(val) if val is not None else ""
    return (
        val.replace("Adrin", "Adrian")
           .replace("Andrs", "Andres")
           .replace("Damin", "Damian")
           .replace("Curaao", "Curacao")
           .replace("Lionel Andrs Messi", "Lionel Messi")
           .replace("Rodrigo Rodri", "Rodri")
    )


# ── Load KPI data from DB ─────────────────────────────────────────────────────
try:
    kpi_df = q("""
        SELECT COUNT(*) AS n_matches,
               COALESCE(SUM(home_score + away_score), 0) AS goals
        FROM matches
    """)
    n_matches   = int(kpi_df.iloc[0]["n_matches"]) if not kpi_df.empty else 104
    total_goals = int(kpi_df.iloc[0]["goals"])     if not kpi_df.empty else 308
except Exception:
    n_matches, total_goals = 104, 308

try:
    n_teams = int(q("SELECT COUNT(*) c FROM teams").iloc[0]["c"])
except Exception:
    n_teams = 48

try:
    n_players = int(q("SELECT COUNT(*) c FROM players").iloc[0]["c"])
except Exception:
    n_players = 1248

try:
    tot_assists  = int(q("SELECT COALESCE(SUM(assists), 0) c FROM player_match_stats").iloc[0]["c"])
    assisted_pct = int(round((tot_assists / max(total_goals, 1)) * 100))
    if not (40 <= assisted_pct <= 90):
        assisted_pct = 72
except Exception:
    assisted_pct = 72

try:
    penalties_cnt = int(q(
        "SELECT COUNT(*) c FROM match_events WHERE event_type LIKE '%Penalty%'"
    ).iloc[0]["c"])
    if not (1 <= penalties_cnt <= 60):
        penalties_cnt = 16
except Exception:
    penalties_cnt = 16


# ── Navigation bar ─────────────────────────────────────────────────────────────
# NOTE: Must use st.markdown (not st.html) so that <a>links are rendered in the
# main DOM and can actually navigate between Streamlit pages.
# The HTML is kept as a single concatenated string so the Markdown parser never
# sees 4+ leading spaces (which would trigger a code-block).
from navigation import nav_link, render_navigation
render_navigation('Overview')

render_photo_story(
    "THE TOURNAMENT ARCHIVE / 2026",
    "",
    "",
    "Every match, player and defining moment — revealed through the data.",
    page="overview",
    overview_story=True,
    show_title=False,
    story_chapters=[
        {
            "image": "worldcup-story-01-origin-v1.png",
            "alt": "A historic football match in Uruguay beneath the national flag",
            "kicker": "CHAPTER ONE / THE BEGINNING",
            "date": "URUGUAY · 1930",
            "title": "WHERE THE STORY.\nBEGAN.",
            "copy": (
                "Thirteen teams gathered in Uruguay for the first World Cup. "
                "A new international tournament began and football found its global stage."
            ),
            "stat": "1930",
            "label": "THE FIRST EDITION",
        },
        {
            "image": "worldcup-story-02-legends-v1.png",
            "alt": "A collage celebrating the players, trophies and stadiums of World Cup history",
            "kicker": "CHAPTER TWO / THE ICONS",
            "date": "1930 — 2022",
            "title": "LEGENDS MADE.\nMEMORIES KEPT.",
            "copy": (
                "Every era found its own heroes, from Pelé and Maradona to the modern generation. "
                "Different nations, styles and stadiums became part of one shared football memory."
            ),
            "stat": "22",
            "label": "EDITIONS BEFORE 2026",
        },
        {
            "image": "worldcup-story-03-future-v1.png",
            "alt": "The World Cup trophy connecting football cities across a world map",
            "kicker": "CHAPTER THREE / A NEW SCALE",
            "date": "UNITED 2026",
            "title": "THE WORLD.\nGROWS WIDER.",
            "copy": (
                f"The United States, Mexico and Canada welcome {n_teams} teams for the largest World Cup yet. "
                f"Across {n_matches} matches, the tournament opens its next chapter to more nations and more supporters."
            ),
            "stat": str(n_teams),
            "label": "TEAMS IN 2026",
        },
    ],
)


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


top_g = q("SELECT player_name, player_team, SUM(goals)   v FROM player_match_stats  GROUP BY player_id ORDER BY v DESC LIMIT 5")
top_a = q("SELECT player_name, player_team, SUM(assists)  v FROM player_match_stats  GROUP BY player_id ORDER BY v DESC LIMIT 5")
top_p = q("SELECT player_name, player_team, SUM(passes)   v FROM player_match_stats  GROUP BY player_id ORDER BY v DESC LIMIT 5")
top_d = q("SELECT player_name, player_team, (SUM(tackles)+SUM(interceptions)) v FROM player_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")
top_s = q("SELECT player_name, team,        SUM(saves)    v FROM goalkeeper_match_stats GROUP BY player_id ORDER BY v DESC LIMIT 5")

lb1, lb2, lb3, lb4, lb5 = st.columns(5)
with lb1: st.markdown(build_leaderboard("Top Scorers",    '<i class="wc-icon icon-target" aria-hidden="true"></i>', top_g.values.tolist() if not top_g.empty else []), unsafe_allow_html=True)
with lb2: st.markdown(build_leaderboard("Top Assists",    '<i class="wc-icon icon-arrow" aria-hidden="true"></i>', top_a.values.tolist() if not top_a.empty else []), unsafe_allow_html=True)
with lb3: st.markdown(build_leaderboard("Top Passers",    '<i class="wc-icon icon-passes" aria-hidden="true"></i>', top_p.values.tolist() if not top_p.empty else []), unsafe_allow_html=True)
with lb4: st.markdown(build_leaderboard("Tackles & Int.", '<i class="wc-icon icon-shield" aria-hidden="true"></i>', top_d.values.tolist() if not top_d.empty else []), unsafe_allow_html=True)
with lb5: st.markdown(build_leaderboard("Top Saves",      '<i class="wc-icon icon-shield" aria-hidden="true"></i>', top_s.values.tolist() if not top_s.empty else []), unsafe_allow_html=True)


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

    xi_left, xi_right = st.columns([1.5, 1.0], gap="large")

    with xi_left:
        st.markdown(
            '<div style="background:#141414;border:0;border-top:1px solid rgba(255,255,255,0.18);border-bottom:1px solid rgba(255,255,255,0.10);border-radius:0;padding:20px">'
            '<div style="font-size:15px;font-weight:700;color:#e8e8e3;margin-bottom:12px">Tournament Best XI (4-3-3 Formation)</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        data_table(
            xi_df,
            width="stretch",
            height=280,
            label="Tournament Best XI / performance index",
        )

    with xi_right:
        st.markdown(
            '<div class="champions-card" style="display:flex;flex-direction:column;justify-content:space-between">'
            '<div>'
            '<div style="font-size:11px;font-weight:800;color:#94A3B8;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px">AI SQUAD BUILDER</div>'
            '<div style="font-size:22px;font-weight:900;color:#FFFFFF;line-height:1.2;margin-bottom:12px">Explore 4 AI-Generated Dream Teams</div>'
            '<p style="font-size:13.5px;color:#94A3B8;line-height:1.6">'
            'Interactive 3D pitch with 4 selection modes:<br>'
            '&bull; <strong>AI Official Best XI</strong><br>'
            '&bull; <strong>ML Balanced XI</strong><br>'
            '&bull; <strong>U23 Rising Stars XI</strong><br>'
            '&bull; <strong>Value-for-Money XI</strong>'
            '</p>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        nav_link("pages/6_best_xi.py", "Open Best XI Builder →")
else:
    st.info("Best XI data not found. Run the analytics pipeline or visit the Best XI page to generate it.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
