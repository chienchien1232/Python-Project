"""Reusable player and team comparison workspace for the Players page."""
from __future__ import annotations

import datetime as dt
import html as html_lib
import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from helpers import load_similarity_matrix, q
from ui.media_ui import country_palette, flag_image, player_portrait, static_url
from text_norm import clean_name, flag

#: Per-90 rows of the head-to-head panel: (column, label, icon key, format).
H2H_STAT_ROWS: list[tuple[str, str, str, str]] = [
    ("goals_p90", "Goals (per 90)", "g", "{:.2f}"),
    ("assists_p90", "Assists (per 90)", "a", "{:.2f}"),
    ("shots_p90", "Shots (per 90)", "s", "{:.1f}"),
    ("dribbles_p90", "Dribbles (per 90)", "d", "{:.1f}"),
    ("pass_accuracy_pct", "Pass Accuracy", "p", "{:.0f}%"),
]
H2H_ICONS: dict[str, str] = {"g": "◉", "a": "➤", "s": "◎", "d": "≋", "p": "⬡"}

#: Radar axes: (column, label, is_derived, format).
AXES_PVP: list[tuple[str, str, bool, str]] = [
    ("goals_p90", "Goals/90", False, "{:.2f}"),
    ("assists_p90", "Assists/90", False, "{:.2f}"),
    ("shots_p90", "Shots/90", False, "{:.1f}"),
    ("dribbles_p90", "Dribbles/90", True, "{:.1f}"),
    ("pass_accuracy_pct", "Pass Accuracy", False, "{:.0f}%"),
    ("passes_p90", "Passes/90", False, "{:.1f}"),
    ("tackles_p90", "Tackles/90", False, "{:.1f}"),
]

#: Team-vs-team aggregated rows: (label, column, unit).
TEAM_STAT_SPECS: list[tuple[str, str, str]] = [
    ("Possession %", "avg_possession", "%"),
    ("Avg Shots / 90", "avg_shots", ""),
    ("Shots on Target", "avg_sot", ""),
    ("Corner Kicks", "avg_corners", ""),
    ("Goalkeeper Saves", "avg_saves", ""),
    ("Fouls Committed", "avg_fouls", ""),
]


def _drib90(row: pd.Series, columns: pd.Index) -> float:
    """Derived per-90 dribbles for one player season row."""
    mins = float(row.get("minutes") or 0)
    if mins <= 0:
        return 0.0
    if "dribbles_p90" in columns and pd.notna(row.get("dribbles_p90")):
        return float(row.get("dribbles_p90"))
    return float(row.get("dribbles_attempted") or 0) / mins * 90


def _bio(pid: Any, meta_map: dict[str, Any]) -> tuple[str, str, str]:
    """Return (age, height_cm, caps) strings for a player id."""
    age, cm, caps = "-", "-", "-"
    m = meta_map.get(str(pid))
    if m is not None:
        if pd.notna(m.get("date_of_birth")):
            try:
                dob = dt.date.fromisoformat(str(m["date_of_birth"])[:10])
                age = str(int((dt.date.today() - dob).days // 365.25))
            except ValueError:
                pass
        if pd.notna(m.get("height_cm")):
            cm = str(int(float(m["height_cm"])))
        if pd.notna(m.get("caps")):
            caps = str(int(float(m["caps"])))
    return age, cm, caps


def _tourney_goals(row: pd.Series) -> int:
    """Tournament goals reconstructed from goals_p90 and minutes."""
    mins = float(row.get("minutes") or 0)
    return int(round(float(row.get("goals_p90") or 0) * mins / 90)) if mins > 0 else 0


def _split_name(full: Any) -> tuple[str, str]:
    """Split a full name into (first names, LAST NAME)."""
    parts = str(full).split()
    if len(parts) == 1:
        return "", parts[0].upper()
    return " ".join(parts[:-1]), parts[-1].upper()


def _stat_val(row: pd.Series, key: str, driv: float) -> float:
    """Panel metric value, using the derived dribbles when needed."""
    if key == "dribbles_p90":
        return driv
    v = row.get(key)
    return float(v) if pd.notna(v) else 0.0


def _panel_rows(row: pd.Series, driv: float) -> str:
    """HTML rows of the head-to-head stat panel for one player."""
    out = ""
    for key, label, icon_k, fmt in H2H_STAT_ROWS:
        out += (
            '<div class="h2h-row">'
            f'<span class="h2h-ico">{H2H_ICONS[icon_k]}</span>'
            f'<span class="h2h-lbl">{label}</span>'
            f'<span class="h2h-val">{fmt.format(_stat_val(row, key, driv))}</span>'
            '</div>'
        )
    return out


def _ax_val(row: pd.Series, key: str, derived: bool, driv: float) -> float:
    """Radar axis value for one player row."""
    if derived:
        return driv
    v = row.get(key)
    return float(v) if pd.notna(v) else 0.0


def render_pvp() -> None:
    """Render the Player-vs-Player comparison tab."""
    df_p = q("SELECT * FROM v_player_season WHERE minutes >= 90")
    if df_p.empty:
        st.error("No player dataset loaded.")
        return
    df_p["player_name"] = df_p["player_name"].apply(clean_name)
    df_p["team"] = df_p["team"].apply(clean_name)

    p_names = sorted(df_p["player_name"].unique().tolist())
    idx_a = next((i for i, name in enumerate(p_names) if "Messi" in name), 0)
    idx_b = next((i for i, name in enumerate(p_names) if "Mbapp" in name), min(1, len(p_names) - 1))

    c1, c2 = st.columns(2)
    with c1:
        pA_name = st.selectbox("Select Player A:", p_names, index=idx_a)
    with c2:
        pB_name = st.selectbox("Select Player B:", p_names, index=idx_b)

    rA_hit = df_p[df_p["player_name"] == pA_name]
    rB_hit = df_p[df_p["player_name"] == pB_name]
    if rA_hit.empty or rB_hit.empty:
        st.info("One of the selected players is not in the current dataset.")
        return
    rA = rA_hit.iloc[0]
    rB = rB_hit.iloc[0]
    codeA, primaryA, secondaryA, primary_rgbA, secondary_rgbA = country_palette(rA["team"])
    codeB, primaryB, secondaryB, primary_rgbB, secondary_rgbB = country_palette(rB["team"])
    panel_varsA = (
        f"--h2h-primary:{primaryA};--h2h-secondary:{secondaryA};"
        f"--h2h-primary-rgb:{primary_rgbA};--h2h-secondary-rgb:{secondary_rgbA};"
    )
    panel_varsB = (
        f"--h2h-primary:{primaryB};--h2h-secondary:{secondaryB};"
        f"--h2h-primary-rgb:{primary_rgbB};--h2h-secondary-rgb:{secondary_rgbB};"
    )
    stadium_src = html_lib.escape(static_url("hero-players-v1.png"), quote=True)

    # ── Derived per-90 dribbles + bio (age / height / caps) ──
    dA, dB = _drib90(rA, df_p.columns), _drib90(rB, df_p.columns)

    meta = q(
        "SELECT CAST(player_id AS TEXT) AS pid, date_of_birth, height_cm, caps "
        "FROM players WHERE CAST(player_id AS TEXT) IN (?, ?)",
        (str(rA["player_id"]), str(rB["player_id"])),
    )
    meta_map = {str(x["pid"]): x for _, x in meta.iterrows()} if not meta.empty else {}

    ageA, cmA, capsA = _bio(rA["player_id"], meta_map)
    ageB, cmB, capsB = _bio(rB["player_id"], meta_map)

    gA, gB = _tourney_goals(rA), _tourney_goals(rB)

    firstA, lastA = _split_name(pA_name)
    firstB, lastB = _split_name(pB_name)

    rowsA_html, rowsB_html = _panel_rows(rA, dA), _panel_rows(rB, dB)

    # ── Versus hero: national colour atmosphere, original portraits ──
    st.html(os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles", "compare.css"))
    st.markdown(
        f'<section class="h2h-hero">'
        f'<div class="h2h-panel is-a" data-team-code="{html_lib.escape(codeA, quote=True)}" style="{panel_varsA}">'
        f'<img class="h2h-stadium" src="{stadium_src}" alt="" aria-hidden="true" loading="lazy">'
        f'<div class="h2h-giant">{gA}</div>'
        f'<div class="h2h-photo">' + player_portrait(pA_name, "player-portrait h2h-profile-portrait") + '</div>'
        f'<div class="h2h-body"><div class="h2h-flag">{flag_image(rA["team"], class_name="team-flag-photo")}</div>'
        f'<div class="h2h-first">{html_lib.escape(firstA)}</div>'
        f'<div class="h2h-last">{html_lib.escape(lastA)}</div>'
        f'<div class="h2h-sub">{html_lib.escape(str(rA["team"]))} · {html_lib.escape(str(rA["position"]))}</div>'
        f'<div class="h2h-trio"><div><b>{ageA}</b><span>AGE</span></div>'
        f'<div><b>{cmA}</b><span>CM</span></div>'
        f'<div><b>{capsA}</b><span>CAPS</span></div></div>'
        f'{rowsA_html}'
        f'</div><div class="h2h-sign">{html_lib.escape(lastA.title())}</div></div>'
        f'<div class="h2h-vs"><i class="slash b"></i><b>VS</b><span>H2H RADAR</span><i class="slash r"></i></div>'
        f'<div class="h2h-panel is-b" data-team-code="{html_lib.escape(codeB, quote=True)}" style="{panel_varsB}">'
        f'<img class="h2h-stadium" src="{stadium_src}" alt="" aria-hidden="true" loading="lazy">'
        f'<div class="h2h-giant">{gB}</div>'
        f'<div class="h2h-body"><div class="h2h-flag">{flag_image(rB["team"], class_name="team-flag-photo")}</div>'
        f'<div class="h2h-first">{html_lib.escape(firstB)}</div>'
        f'<div class="h2h-last">{html_lib.escape(lastB)}</div>'
        f'<div class="h2h-sub">{html_lib.escape(str(rB["team"]))} · {html_lib.escape(str(rB["position"]))}</div>'
        f'<div class="h2h-trio"><div><b>{ageB}</b><span>AGE</span></div>'
        f'<div><b>{cmB}</b><span>CM</span></div>'
        f'<div><b>{capsB}</b><span>CAPS</span></div></div>'
        f'{rowsB_html}'
        f'</div>'
        f'<div class="h2h-photo">' + player_portrait(pB_name, "player-portrait h2h-profile-portrait") + '</div>'
        f'<div class="h2h-sign">{html_lib.escape("K. " + lastB.title())}</div></div>'
        f'</section>',
        unsafe_allow_html=True
    )

    col_radar, col_table = st.columns([1.15, 1.0], gap="large")

    with col_radar:
        with st.container(border=True):
            st.markdown(
                '<div class="h2h-panel-head"><span class="h2h-dot"></span>'
                'HEAD-TO-HEAD PER 90 RADAR PROFILE'
                '<span class="h2h-year">/ 2026</span></div>',
                unsafe_allow_html=True,
            )
            fig_h2h = go.Figure()
            for r_item, driv, p_label, clr, fill_clr in [
                # Muted aqua and sand separate both players clearly
                # while preserving the monochrome page foundation.
                (rA, dA, pA_name, "#a8dadc", "rgba(168,218,220,0.20)"),
                (rB, dB, pB_name, "#d7c3a3", "rgba(215,195,163,0.18)"),
            ]:
                vals = [_ax_val(r_item, c, der, driv) for c, _, der, _ in AXES_PVP]
                maxes = []
                for c, _, der, _ in AXES_PVP:
                    if der:
                        col_vals = (
                            df_p["dribbles_p90"]
                            if "dribbles_p90" in df_p.columns
                            else (df_p["dribbles_attempted"].fillna(0)
                                  / df_p["minutes"].replace(0, pd.NA) * 90)
                        )
                        maxes.append(max(col_vals.fillna(0).max(), 1e-6))
                    else:
                        maxes.append(max(df_p[c].fillna(0).max(), 1e-6))
                pct = [round(100.0 * min(v / mx, 1.0), 1) for v, mx in zip(vals, maxes)]

                fig_h2h.add_trace(go.Scatterpolar(
                    r=pct + [pct[0]],
                    theta=[lbl for _, lbl, _, _ in AXES_PVP] + [AXES_PVP[0][1]],
                    fill="toself",
                    fillcolor=fill_clr,
                    name=p_label,
                    line=dict(color=clr, width=2.8),
                    marker=dict(color=clr, size=5),
                ))

            fig_h2h.update_layout(
                paper_bgcolor="#080808",
                plot_bgcolor="#080808",
                font=dict(family="Arial, sans-serif", color="#9b9b95", size=11),
                polar=dict(
                    bgcolor="#080808",
                    radialaxis=dict(visible=True, range=[0, 100],
                                    gridcolor="rgba(255,255,255,0.10)",
                                    linecolor="rgba(255,255,255,0.14)",
                                    tickfont=dict(color="#9b9b95", size=9)),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.10)",
                                     linecolor="rgba(255,255,255,0.14)"),
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.18,
                            xanchor="center", x=0.5, font=dict(size=11, color="#f1f0eb")),
                margin=dict(l=35, r=35, t=20, b=45),
                height=380,
            )
            st.plotly_chart(fig_h2h, width="stretch")

    with col_table:
        with st.container(border=True):
            comp_rows_html = ""
            for col_key, label_str, derived, fmt in AXES_PVP:
                va = _ax_val(rA, col_key, derived, dA)
                vb = _ax_val(rB, col_key, derived, dB)
                delta = va - vb
                if "pass_accuracy" in col_key:
                    delta_txt = f"{delta:+.0f}%"
                else:
                    delta_txt = fmt.format(delta) if "%" not in fmt else fmt.format(delta)
                    if not delta_txt.startswith(("+", "-", "−")):
                        delta_txt = ("+" if delta >= 0 else "") + delta_txt
                cls = "h2h-delta-eq" if abs(delta) < 1e-9 else ("h2h-delta-up" if delta > 0 else "h2h-delta-dn")
                comp_rows_html += (
                    "<tr>"
                    f"<td>{label_str}</td>"
                    f"<td>{fmt.format(va)}</td>"
                    f"<td>{fmt.format(vb)}</td>"
                    f'<td class="{cls}">{delta_txt}</td>'
                    "</tr>"
                )
            st.markdown(
                '<div class="h2h-panel-head"><span class="h2h-dot"></span>'
                'DIRECT METRIC COMPARISON'
                f'<span class="h2h-year">{len(AXES_PVP)} RECORDS / 4 FIELDS</span></div>'
                '<table class="h2h-table"><thead><tr>'
                f'<th>Metric</th><th>{html_lib.escape(pA_name)}</th>'
                f'<th>{html_lib.escape(pB_name)}</th><th>Delta (A - B)</th>'
                '</tr></thead><tbody>' + comp_rows_html + '</tbody></table>',
                unsafe_allow_html=True,
            )

        # Similarity between Player A and Player B
        sim = load_similarity_matrix()
        if sim is not None:
            try:
                key_a = next((x for x in sim.index if f"#{rA['player_id']}" in x or x == pA_name), None)
                key_b = next((x for x in sim.index if f"#{rB['player_id']}" in x or x == pB_name), None)
                if key_a and key_b and key_a in sim.columns and key_b in sim.index:
                    val_sim = float(sim.loc[key_b, key_a]) * 100
                    st.markdown(
                        f'<div style="background:#0e0e0e;border:1px solid #343434;border-radius:0;padding:14px;margin-top:16px">'
                        f'<div style="font-size:11px;font-weight:700;color:#9b9b95;text-transform:uppercase;letter-spacing:1px">AI PLAYSTYLE SIMILARITY</div>'
                        f'<div style="font-size:26px;font-weight:400;color:#f1f0eb;margin:4px 0">{val_sim:.1f}%</div>'
                        f'<div style="font-size:12px;color:#9b9b95">Direct cosine distance over 18 normalized Per-90 tactical features</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            except Exception:
                st.caption("AI playstyle similarity is unavailable for this pair.")


def render_tvt() -> None:
    """Render the Team-vs-Team comparison tab."""
    t_df = q("SELECT team_id, team_name, confederation FROM teams ORDER BY team_name")
    t_df["team_name"] = t_df["team_name"].apply(clean_name)
    teams_all = t_df["team_name"].tolist()
    if not teams_all:
        st.info("No team data available.")
        return

    idx_ta = teams_all.index("Argentina") if "Argentina" in teams_all else 0
    idx_tb = teams_all.index("France") if "France" in teams_all else min(1, len(teams_all) - 1)

    c_t1, c_t2 = st.columns(2)
    with c_t1:
        tA_name = st.selectbox("Select Team A:", teams_all, index=idx_ta)
    with c_t2:
        tB_name = st.selectbox("Select Team B:", teams_all, index=idx_tb)

    fl_ta = flag(tA_name)
    fl_tb = flag(tB_name)
    fl_ta_img = flag_image(tA_name, class_name="match-team-flag-big")
    fl_tb_img = flag_image(tB_name, class_name="match-team-flag-big")

    # Scorecard Banner (minimal monochrome)
    st.markdown(
        f'<div class="match-hero-card">'
        f'<div class="match-scoreboard-main" style="margin:8px 0">'
        f'<div class="match-team-block home">'
        f'<div>'
        f'<div class="match-team-name-big" style="color:#f1f0eb;font-size:28px">{tA_name}</div>'
        f'<div style="color:#9b9b95;font-size:12px">{fl_ta} Qualified Nation</div>'
        f'</div>'
        f'{fl_ta_img}'
        f'</div>'
        f'<div class="match-score-display" style="min-width:110px">'
        f'<div class="match-score-numbers" style="font-size:28px;color:#f1f0eb">VS</div>'
        f'<div class="match-status-pill">TEAM H2H</div>'
        f'</div>'
        f'<div class="match-team-block away">'
        f'{fl_tb_img}'
        f'<div>'
        f'<div class="match-team-name-big" style="color:#9b9b95;font-size:28px">{tB_name}</div>'
        f'<div style="color:#9b9b95;font-size:12px">{fl_tb} Qualified Nation</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_h2h_matches, col_h2h_stats = st.columns([1.1, 1.0], gap="large")

    with col_h2h_matches:
        st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>Matches Between Teams at Tournament</div>", unsafe_allow_html=True)
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
            m_h2h_html = '<div style="background:#0e0e0e;border:1px solid #343434;border-radius:0;padding:16px">'
            for _, r in h2h_m.iterrows():
                h_n = clean_name(r["Home_Team"])
                a_n = clean_name(r["Away_Team"])
                try:
                    hs = int(r["Home_Score"])
                    as_ = int(r["Away_Score"])
                except (ValueError, TypeError):
                    continue
                m_h2h_html += (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 2px;background:transparent;border:none;border-bottom:1px solid rgba(255,255,255,0.08);border-radius:0;margin-bottom:0">'
                    f'<div style="font-size:12px;color:#9b9b95">{r["Stage"]}<br><span style="color:#9b9b95">{r["Date"]}</span></div>'
                    f'<div style="font-size:15px;font-weight:700;color:#f1f0eb">'
                    f'{flag(h_n)} {h_n} <span style="color:#f1f0eb;font-size:20px;font-weight:400;padding:0 8px">{hs} - {as_}</span> {a_n} {flag(a_n)}'
                    f'</div>'
                    f'<div style="font-size:11.5px;color:#9b9b95">{r["Result_Type"]}</div>'
                    f'</div>'
                )
            m_h2h_html += '</div>'
            st.markdown(m_h2h_html, unsafe_allow_html=True)
        else:
            st.info(f"{tA_name} and {tB_name} did not face each other directly during the 2026 World Cup.")

    with col_h2h_stats:
        st.markdown("<div class='section-header' style='font-size:20px;margin-top:0'>Tournament Aggregated Statistics</div>", unsafe_allow_html=True)

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
            tA_row = stat_t[stat_t["team_name"] == tA_name]
            tB_row = stat_t[stat_t["team_name"] == tB_name]

            st_card_html = '<div style="background:#0e0e0e;border:1px solid #343434;border-radius:0;padding:18px">'
            for label, col, unit in TEAM_STAT_SPECS:
                va = float(tA_row.iloc[0][col]) if not tA_row.empty and pd.notna(tA_row.iloc[0].get(col)) else 0.0
                vb = float(tB_row.iloc[0][col]) if not tB_row.empty and pd.notna(tB_row.iloc[0].get(col)) else 0.0
                tot = max(va + vb, 1e-6)
                pct_a = round((va / tot) * 100, 1)
                pct_b = 100.0 - pct_a

                st_card_html += (
                    f'<div class="match-stat-row">'
                    f'<div class="match-stat-labels">'
                    f'<span class="match-stat-val" style="color:#f1f0eb">{va:.1f}{unit}</span>'
                    f'<span class="match-stat-name">{label}</span>'
                    f'<span class="match-stat-val" style="color:#9b9b95">{vb:.1f}{unit}</span>'
                    f'</div>'
                    f'<div class="match-bar-bg" style="background:rgba(255,255,255,0.08);height:2px;">'
                    f'<div class="match-bar-home" style="width:{pct_a}%;background:#f1f0eb;box-shadow:none;"></div>'
                    f'<div class="match-bar-away" style="width:{pct_b}%;background:#686862;box-shadow:none;"></div>'
                    f'</div>'
                    f'</div>'
                )
            st_card_html += '</div>'
            st.markdown(st_card_html, unsafe_allow_html=True)


def render_compare_workspace() -> None:
    """Render the full player-v-player and team-v-team comparison tools."""
    tab_pvp, tab_tvt = st.tabs([" Player vs Player", " Team vs Team"])
    with tab_pvp:
        render_pvp()
    with tab_tvt:
        render_tvt()
