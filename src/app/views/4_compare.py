# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Head-to-Head Player & Team Comparison."""
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

from helpers import cfg_num, flag_img, icon_badge, icon_svg, load_analytics_csv, player_avatar_html, q  # noqa: E402

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


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span> HEAD-TO-HEAD ENGINE</div>'
    '<div class="wc-hero-dates">SIDE-BY-SIDE ANALYTICAL COMPARISON</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">HEAD-TO-HEAD</span>'
    '<span class="title-lime">COMPARISON.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Compare any two players or national teams head-to-head. Analyze multi-axis radar profiles, '
    'historical match encounters, Per-90 statistical deltas, and AI similarity metrics.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Tabs: Player vs Player & Team vs Team ─────────────────────────────────────
tab_pvp, tab_tvt = st.tabs(["Player vs Player", "Team vs Team"])


# ==============================================================================
# PLAYER VS PLAYER
# ==============================================================================
with tab_pvp:
    df_p = q("SELECT * FROM v_player_season WHERE minutes >= 90")
    if df_p.empty:
        st.error("No player dataset loaded.")
    else:
        df_p["player_name"] = df_p["player_name"].apply(clean_name)
        df_p["team"] = df_p["team"].apply(clean_name)

        p_names = sorted(df_p["player_name"].unique().tolist())
        idx_a = p_names.index("Lionel Messi") if "Lionel Messi" in p_names else 0
        idx_b = p_names.index("Kylian Mbappé") if "Kylian Mbappé" in p_names else min(1, len(p_names)-1)

        c1, c2 = st.columns(2)
        with c1:
            pA_name = st.selectbox("Select Player A (Primary / Neon Lime):", p_names, index=idx_a)
        with c2:
            pB_name = st.selectbox("Select Player B (Challenger / Sky Blue):", p_names, index=idx_b)

        rA = df_p[df_p["player_name"] == pA_name].iloc[0]
        rB = df_p[df_p["player_name"] == pB_name].iloc[0]

        flA = flag(rA["team"])
        flB = flag(rB["team"])
        avA = player_avatar_html(rA["player_id"], pA_name, 96)
        avB = player_avatar_html(rB["player_id"], pB_name, 96)
        flA_img = flag_img(rA["team"], 46, fallback_emoji=flA)
        flB_img = flag_img(rB["team"], 46, fallback_emoji=flB)

        # Scorecard Matchup Banner
        st.markdown(
            f'<div class="match-hero-card">'
            f'<div class="match-scoreboard-main" style="margin:8px 0">'
            f'<div class="match-team-block home">'
            f'<div style="display:flex;align-items:center;gap:14px">'
            f'{avA}'
            f'<div>'
            f'<div class="match-team-name-big" style="color:#ccff00;font-size:28px">{pA_name}</div>'
            f'<div style="color:#94a3b8;font-size:12px">{flag_img(rA["team"], 14, fallback_emoji=flA)} {rA["team"]} · {rA["position"]} · {int(rA["minutes"])} mins</div>'
            f'</div>'
            f'</div>'
            f'<div class="match-team-flag-big">{flA_img}</div>'
            f'</div>'
            f'<div class="match-score-display" style="min-width:110px">'
            f'<div class="match-score-numbers" style="font-size:28px;color:#FFFFFF">VS</div>'
            f'<div class="match-status-pill">H2H RADAR</div>'
            f'</div>'
            f'<div class="match-team-block away">'
            f'<div class="match-team-flag-big">{flB_img}</div>'
            f'<div style="display:flex;align-items:center;gap:14px">'
            f'{avB}'
            f'<div>'
            f'<div class="match-team-name-big" style="color:#38bdf8;font-size:28px">{pB_name}</div>'
            f'<div style="color:#94a3b8;font-size:12px">{flag_img(rB["team"], 14, fallback_emoji=flB)} {rB["team"]} · {rB["position"]} · {int(rB["minutes"])} mins</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        col_radar, col_table = st.columns([1.15, 1.0], gap="large")

        axes_p = [
            ("goals_p90", "Goals/90"),
            ("assists_p90", "Assists/90"),
            ("shots_p90", "Shots/90"),
            ("passes_p90", "Passes/90"),
            ("tackles_p90", "Tackles/90"),
            ("interceptions_p90", "Interceptions/90"),
            ("clearances_p90", "Clearances/90"),
            ("recoveries_p90", "Recoveries/90"),
        ]

        with col_radar:
            st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('radar')} Head-to-Head Per-90 Radar Profile</div>", unsafe_allow_html=True)
            
            fig_h2h = go.Figure()
            for r_item, p_label, clr, fill_clr in [
                (rA, pA_name, "#ccff00", "rgba(204,255,0,0.18)"),
                (rB, pB_name, "#38bdf8", "rgba(56,189,248,0.18)")
            ]:
                vals = [float(r_item.get(c, 0.0) or 0.0) for c, _ in axes_p]
                maxes = [max(df_p[c].fillna(0).max(), 1e-6) for c, _ in axes_p]
                pct = [round(100.0 * min(v / mx, 1.0), 1) for v, mx in zip(vals, maxes)]

                fig_h2h.add_trace(go.Scatterpolar(
                    r=pct + [pct[0]],
                    theta=[lbl for _, lbl in axes_p] + [axes_p[0][1]],
                    fill="toself",
                    fillcolor=fill_clr,
                    name=p_label,
                    line=dict(color=clr, width=2.8),
                ))

            fig_h2h.update_layout(
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
                height=380,
            )
            st.plotly_chart(fig_h2h, width="stretch")

        with col_table:
            st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('chart')} Direct Metric Comparison</div>", unsafe_allow_html=True)
            
            comp_rows = []
            for col_key, label_str in axes_p:
                va = float(rA.get(col_key, 0.0) or 0.0)
                vb = float(rB.get(col_key, 0.0) or 0.0)
                delta = va - vb
                comp_rows.append({
                    "Metric": label_str,
                    f"{pA_name}": round(va, 2),
                    f"{pB_name}": round(vb, 2),
                    "Delta (A - B)": f"{delta:+.2f}",
                })
            comp_df = pd.DataFrame(comp_rows)
            st.dataframe(comp_df, width="stretch", hide_index=True, column_config={c: cfg_num(c) for c in comp_df.columns if c != "Metric"})

            # Similarity between Player A and Player B
            sim_path = os.path.join(ROOT, "data", "processed", "analytics", "similarity_matrix.parquet")
            if os.path.exists(sim_path):
                try:
                    sim = pd.read_parquet(sim_path)
                    key_a = next((x for x in sim.index if f"#{rA['player_id']}" in x or x == pA_name), None)
                    key_b = next((x for x in sim.index if f"#{rB['player_id']}" in x or x == pB_name), None)
                    if key_a and key_b and key_a in sim.columns and key_b in sim.index:
                        val_sim = float(sim.loc[key_b, key_a]) * 100
                        st.markdown(
                            f'<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:14px;margin-top:16px">'
                            f'<div style="font-size:11px;font-weight:800;color:#94a3b8;text-transform:uppercase;letter-spacing:1px">{icon_svg("cpu", 12)} AI PLAYSTYLE SIMILARITY</div>'
                            f'<div style="font-family:var(--font-sport);font-size:26px;font-weight:900;color:#ccff00;margin:4px 0">{val_sim:.1f}%</div>'
                            f'<div style="font-size:12px;color:#64748b">Direct cosine distance over 18 normalized Per-90 tactical features</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                except Exception:
                    pass


# ==============================================================================
# TEAM VS TEAM
# ==============================================================================
with tab_tvt:
    t_df = q("SELECT team_id, team_name, confederation FROM teams ORDER BY team_name")
    t_df["team_name"] = t_df["team_name"].apply(clean_name)
    teams_all = t_df["team_name"].tolist()

    idx_ta = teams_all.index("Argentina") if "Argentina" in teams_all else 0
    idx_tb = teams_all.index("France") if "France" in teams_all else 1

    c_t1, c_t2 = st.columns(2)
    with c_t1:
        tA_name = st.selectbox("Select Team A (Primary / Neon Lime):", teams_all, index=idx_ta)
    with c_t2:
        tB_name = st.selectbox("Select Team B (Challenger / Sky Blue):", teams_all, index=idx_tb)

    fl_ta = flag(tA_name)
    fl_tb = flag(tB_name)

    # Scorecard Banner
    st.markdown(
        f'<div class="match-hero-card">'
        f'<div class="match-scoreboard-main" style="margin:8px 0">'
        f'<div class="match-team-block home">'
        f'<div>'
        f'<div class="match-team-name-big" style="color:#ccff00;font-size:28px">{tA_name}</div>'
        f'<div style="color:#94a3b8;font-size:12px">{flag_img(tA_name, 14, fallback_emoji=fl_ta)} Qualified Nation</div>'
        f'</div>'
        f'<div class="match-team-flag-big">{flag_img(tA_name, 44, fallback_emoji=fl_ta)}</div>'
        f'</div>'
        f'<div class="match-score-display" style="min-width:110px">'
        f'<div class="match-score-numbers" style="font-size:28px;color:#FFFFFF">VS</div>'
        f'<div class="match-status-pill">TEAM H2H</div>'
        f'</div>'
        f'<div class="match-team-block away">'
        f'<div class="match-team-flag-big">{flag_img(tB_name, 44, fallback_emoji=fl_tb)}</div>'
        f'<div>'
        f'<div class="match-team-name-big" style="color:#38bdf8;font-size:28px">{tB_name}</div>'
        f'<div style="color:#94a3b8;font-size:12px">{flag_img(tB_name, 14, fallback_emoji=fl_tb)} Qualified Nation</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_h2h_matches, col_h2h_stats = st.columns([1.1, 1.0], gap="large")

    with col_h2h_matches:
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('stadium')} Matches Between Teams at Tournament</div>", unsafe_allow_html=True)
        h2h_m = q("""
            SELECT d.date AS Date, d.stage_name AS Stage,
                   d.home_team_name AS Home_Team, d.home_score AS Home_Score,
                   d.away_score AS Away_Score, d.away_team_name AS Away_Team,
                   d.stadium_name AS Stadium, d.result_type AS Result_Type
            FROM matches_detailed d
            WHERE (d.home_team_name = ? AND d.away_team_name = ?)
               OR (d.home_team_name = ? AND d.away_team_name = ?)
            ORDER BY d.date
        """, (tA_name, tB_name, tB_name, tA_name))

        if not h2h_m.empty:
            m_h2h_html = '<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:16px">'
            for _, r in h2h_m.iterrows():
                h_n = clean_name(r["Home_Team"])
                a_n = clean_name(r["Away_Team"])
                hs = int(r["Home_Score"])
                as_ = int(r["Away_Score"])
                m_h2h_html += (
                    f'<div class="stat-row" style="display:flex;align-items:center;justify-content:space-between;padding:12px;background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:10px;margin-bottom:8px">'
                    f'<div style="font-size:12px;color:#94a3b8">{r["Stage"]}<br><span style="color:#64748b">{r["Date"]}</span></div>'
                    f'<div style="font-size:15px;font-weight:700;color:#FFFFFF">'
                    f'{flag_img(h_n, 16, fallback_emoji=flag(h_n))} {h_n} <span style="color:#ccff00;font-family:var(--font-sport);font-size:20px;font-weight:900;padding:0 8px">{hs} - {as_}</span> {a_n} {flag_img(a_n, 16, fallback_emoji=flag(a_n))}'
                    f'</div>'
                    f'<div style="font-size:11.5px;color:#94a3b8">{r["Result_Type"]}</div>'
                    f'</div>'
                )
            m_h2h_html += '</div>'
            st.markdown(m_h2h_html, unsafe_allow_html=True)
        else:
            st.info(f"{tA_name} and {tB_name} did not face each other directly during the 2026 World Cup.")

    with col_h2h_stats:
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('chart')} Tournament Aggregated Statistics</div>", unsafe_allow_html=True)
        
        stat_t = q("""
            SELECT t.team_name,
                   ROUND(AVG(x.possession_pct), 1) AS avg_possession,
                   ROUND(AVG(x.total_shots), 1) AS avg_shots,
                   ROUND(AVG(x.shots_on_target), 1) AS avg_sot,
                   ROUND(AVG(x.corners), 1) AS avg_corners,
                   ROUND(AVG(x.saves), 1) AS avg_saves,
                   ROUND(AVG(x.fouls), 1) AS avg_fouls
            FROM match_team_stats x
            JOIN teams t ON t.team_id = x.team_id
            WHERE t.team_name IN (?, ?)
            GROUP BY t.team_id
        """, (tA_name, tB_name))

        if len(stat_t) >= 1:
            stat_t["team_name"] = stat_t["team_name"].apply(clean_name)
            stat_specs_team = [
                ("Possession %", "avg_possession", "%"),
                ("Avg Shots / 90", "avg_shots", ""),
                ("Shots on Target", "avg_sot", ""),
                ("Corner Kicks", "avg_corners", ""),
                ("Goalkeeper Saves", "avg_saves", ""),
                ("Fouls Committed", "avg_fouls", ""),
            ]

            tA_row = stat_t[stat_t["team_name"] == tA_name]
            tB_row = stat_t[stat_t["team_name"] == tB_name]

            st_card_html = '<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:18px">'
            for label, col, unit in stat_specs_team:
                va = float(tA_row.iloc[0][col]) if not tA_row.empty and pd.notna(tA_row.iloc[0].get(col)) else 0.0
                vb = float(tB_row.iloc[0][col]) if not tB_row.empty and pd.notna(tB_row.iloc[0].get(col)) else 0.0
                tot = max(va + vb, 1e-6)
                pct_a = round((va / tot) * 100, 1)
                pct_b = 100.0 - pct_a

                st_card_html += (
                    f'<div class="match-stat-row">'
                    f'<div class="match-stat-labels">'
                    f'<span class="match-stat-val" style="color:#ccff00">{va:.1f}{unit}</span>'
                    f'<span class="match-stat-name">{label}</span>'
                    f'<span class="match-stat-val" style="color:#38bdf8">{vb:.1f}{unit}</span>'
                    f'</div>'
                    f'<div class="match-bar-bg">'
                    f'<div class="match-bar-home" style="width:{pct_a}%"></div>'
                    f'<div class="match-bar-away" style="width:{pct_b}%"></div>'
                    f'</div>'
                    f'</div>'
                )
            st_card_html += '</div>'
            st.markdown(st_card_html, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
