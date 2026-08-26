# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Teams & Tactical Profiles."""
import os
import sys
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

from helpers import cfg_money, cfg_num, flag_img, flag_url, icon_badge, icon_svg, load_analytics_csv, q  # noqa: E402

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
           SUM(CASE WHEN (m.home_team_id=t.team_id AND m.home_score > m.away_score) OR (m.away_team_id=t.team_id AND m.away_score > m.home_score) THEN 1 ELSE 0 END) AS Wins,
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
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span> TEAM DIRECTORY</div>'
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
st.markdown(f"<div class='section-header'>{icon_badge('search')} Select National Team</div>", unsafe_allow_html=True)

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
        f'<span style="background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.35);border-radius:999px;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px">Group {t_row.get("Group_Letter", "-")}</span> '
        f'<span style="background:rgba(204,255,0,0.12);color:#ccff00;border:1px solid rgba(204,255,0,0.35);border-radius:999px;padding:4px 12px;font-size:11px;font-weight:800;letter-spacing:1.2px;text-transform:uppercase;margin-left:6px">{icon_svg("cpu", 12)} {t_cluster}</span></div>'
        f'<div class="match-venue-text">FIFA Rank: <strong>#{t_rank}</strong> &nbsp;·&nbsp; Head Coach: <strong>{t_mgr}</strong></div>'
        f'</div>'
        f'<div class="match-scoreboard-main" style="margin:14px 0">'
        f'<div style="display:flex;align-items:center;gap:18px">'
        f'<div style="line-height:1">{flag_img(selected_team, 56, fallback_emoji=t_flag)}</div>'
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
        f'<div style="font-family:var(--font-sport);font-size:26px;font-weight:900;color:#ccff00">€{t_val:.0f}M</div>'
        f'<div style="font-size:12.5px;color:#94a3b8">26 Players Roster</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_t_left, col_t_right = st.columns([1.15, 1.0], gap="large")

    with col_t_left:
        # Tactical Radar Footprint
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('radar')} Tactical Radar Profile (vs Tournament Average)</div>", unsafe_allow_html=True)
        
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

        if not per_match.empty and pd.notna(per_match.iloc[0]["possession"]):
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
                fillcolor="rgba(204, 255, 0, 0.22)",
                name=selected_team,
                line=dict(color="#ccff00", width=3),
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[50] * (len(axes) + 1),
                theta=axes + [axes[0]],
                name="Tournament Avg (Baseline 50)",
                line=dict(color="#64748b", dash="dash", width=1.8),
            ))
            fig_radar.update_layout(
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
                height=340,
            )
            st.plotly_chart(fig_radar, width="stretch")
        else:
            st.info("Match statistics not yet accumulated for this team.")

        # Key Tactical Metrics Card
        if not per_match.empty and pd.notna(per_match.iloc[0]["possession"]):
            st.markdown(
                f'<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:18px;margin-top:12px">'
                f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;text-align:center">'
                f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">AVG POSSESSION</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#ccff00">{vals[0]:.1f}%</div></div>'
                f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">AVG SHOTS / 90</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#FFFFFF">{vals[1]:.1f}</div></div>'
                f'<div><div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase">SHOTS ON TARGET</div><div style="font-family:var(--font-sport);font-size:22px;font-weight:900;color:#38bdf8">{vals[2]:.1f}</div></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    with col_t_right:
        # Tournament Matches of this Team
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('calendar')} Match Results</div>", unsafe_allow_html=True)
        m_list = q("""
            SELECT d.date AS Date, d.stage_name AS Stage,
                   d.home_team_name AS Home_Team, d.home_score AS Home_Score,
                   d.away_score AS Away_Score, d.away_team_name AS Away_Team,
                   d.result_type AS Result_Type
            FROM matches_detailed d
            WHERE d.home_team_name = ? OR d.away_team_name = ?
            ORDER BY d.date
        """, (selected_team, selected_team))

        if not m_list.empty:
            m_cards_html = '<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px;margin-bottom:20px">'
            for _, mr in m_list.iterrows():
                h_name = clean_name(mr["Home_Team"])
                a_name = clean_name(mr["Away_Team"])
                h_f = flag(h_name)
                a_f = flag(a_name)
                hs = int(mr["Home_Score"])
                as_ = int(mr["Away_Score"])

                # Determine Win/Draw/Loss badge for the selected team
                if (h_name == selected_team and hs > as_) or (a_name == selected_team and as_ > hs):
                    res_badge = '<span style="background:rgba(0,230,118,0.15);color:#00e676;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:800">WIN</span>'
                elif hs == as_:
                    res_badge = '<span style="background:rgba(255,255,255,0.1);color:#cbd5e1;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:800">DRAW</span>'
                else:
                    res_badge = '<span style="background:rgba(255,82,82,0.15);color:#ff5252;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:800">LOSS</span>'

                m_cards_html += (
                    f'<div class="stat-row" style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:10px;margin-bottom:8px">'
                    f'<div style="font-size:11.5px;color:#94a3b8">{mr["Stage"]}<br><span style="font-size:10.5px;color:#64748b">{mr["Date"]}</span></div>'
                    f'<div style="font-size:14px;font-weight:700;color:#FFFFFF;text-align:center">'
                    f'{flag_img(h_name, 16, fallback_emoji=h_f)} {h_name} <span style="color:#ccff00;font-family:var(--font-sport);font-size:17px;font-weight:900;padding:0 6px">{hs} - {as_}</span> {a_name} {flag_img(a_name, 16, fallback_emoji=a_f)}'
                    f'</div>'
                    f'<div>{res_badge}</div>'
                    f'</div>'
                )
            m_cards_html += '</div>'
            st.markdown(m_cards_html, unsafe_allow_html=True)
        else:
            st.info("No matches recorded for this team.")

        # Squad List
        st.markdown(f"<div class='section-header' style='font-size:20px'>{icon_badge('clipboard')} Official 26-Man Squad Roster</div>", unsafe_allow_html=True)
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
            squad_list.columns = ["Player", "Position", "Club Team", "Caps", "Height (cm)", "Value (€M)"]
            st.dataframe(squad_list, width="stretch", hide_index=True, height=280, column_config={"Caps": cfg_num("Caps", "%.0f"), "Height (cm)": cfg_num("Height (cm)", "%.0f"),"Value (€M)": cfg_money("Value (€M)")})


# ── Full 48-Teams Tournament Standings Table ──────────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('medal')} All 48 Nations Overview &amp; Tactical Clusters</div>", unsafe_allow_html=True)

display_teams = df_teams[["Team", "Confederation", "Group_Letter", "FIFA_Rank", "Manager", "Matches_Played", "Wins", "Draws", "Losses", "Goals_For", "Goals_Against", "Goal_Diff", "Squad_Value_MEur", "AI_Cluster"]].copy()
display_teams.columns = ["Nation", "Confederation", "Group", "FIFA Rank", "Head Coach", "P", "W", "D", "L", "GF", "GA", "GD", "Value (€M)", "AI Tactical Style"]
display_teams.insert(0, "Flag", display_teams["Nation"].map(flag_url))

st.dataframe(display_teams.sort_values(["W", "GD", "GF"], ascending=[False, False, False]), width="stretch", hide_index=True, column_config={"Flag": st.column_config.ImageColumn("", width="small"),"GD": st.column_config.NumberColumn("GD", format="+%.0f"),"Value (€M)": cfg_money("Value (€M)"),"P": cfg_num("P", "%.0f"), "W": cfg_num("W", "%.0f"), "D": cfg_num("D", "%.0f"), "L": cfg_num("L", "%.0f"), "GF": cfg_num("GF", "%.0f"), "GA": cfg_num("GA", "%.0f"), "FIFA Rank": cfg_num("FIFA Rank", "%.0f")})


# ── AI Tactical Cluster Analysis Summary ──────────────────────────────────────
if tc is not None and "cluster_label" in tc.columns:
    st.markdown(f"<div class='section-header'>{icon_badge('cpu')} AI Cluster Characteristics Breakdown</div>", unsafe_allow_html=True)
    
    stat_feature_cols = [c for c in ["possession", "shots", "sot", "corners", "saves", "gf", "ga", "gd"] if c in tc.columns]
    if stat_feature_cols:
        cluster_summary = tc.groupby("cluster_label")[stat_feature_cols].mean().round(2).reset_index()
        cluster_summary.columns = ["AI Tactical Style", "Avg Possession %", "Avg Shots", "Avg SOT", "Avg Corners", "Avg Saves", "Avg Goals For", "Avg Goals Against", "Avg Goal Diff"]
        st.dataframe(cluster_summary, width="stretch", hide_index=True, column_config={c: cfg_num(c, "%.1f") for c in cluster_summary.columns if c != "AI Tactical Style"})


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
