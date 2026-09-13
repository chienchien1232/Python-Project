"""Reusable player and team comparison workspace for the Players page."""
from __future__ import annotations

import datetime as dt
import html as html_lib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from helpers import load_similarity_matrix, q
from media_ui import country_palette, flag_image, player_portrait, static_url

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


def flag(team_name: str) -> str:
    return FLAGS.get(clean_name(team_name), "—")


def render_compare_workspace() -> None:
    """Render the full player-v-player and team-v-team comparison tools."""
    tab_pvp, tab_tvt = st.tabs([" Player vs Player", " Team vs Team"])


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
            idx_a = next((i for i, name in enumerate(p_names) if "Messi" in name), 0)
            idx_b = next((i for i, name in enumerate(p_names) if "Mbapp" in name), min(1, len(p_names)-1))

            c1, c2 = st.columns(2)
            with c1:
                pA_name = st.selectbox("Select Player A:", p_names, index=idx_a)
            with c2:
                pB_name = st.selectbox("Select Player B:", p_names, index=idx_b)

            rA = df_p[df_p["player_name"] == pA_name].iloc[0]
            rB = df_p[df_p["player_name"] == pB_name].iloc[0]
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
            def _drib90(row):
                mins = float(row.get("minutes") or 0)
                if mins <= 0:
                    return 0.0
                if "dribbles_p90" in df_p.columns and pd.notna(row.get("dribbles_p90")):
                    return float(row.get("dribbles_p90"))
                return float(row.get("dribbles_attempted") or 0) / mins * 90

            dA, dB = _drib90(rA), _drib90(rB)

            meta = q(
                "SELECT CAST(player_id AS TEXT) AS pid, date_of_birth, height_cm, caps "
                "FROM players WHERE CAST(player_id AS TEXT) IN (?, ?)",
                (str(rA["player_id"]), str(rB["player_id"])),
            )
            meta_map = {str(x["pid"]): x for _, x in meta.iterrows()} if not meta.empty else {}

            def _bio(pid):
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

            ageA, cmA, capsA = _bio(rA["player_id"])
            ageB, cmB, capsB = _bio(rB["player_id"])

            def _tourney_goals(row):
                mins = float(row.get("minutes") or 0)
                return int(round(float(row.get("goals_p90") or 0) * mins / 90)) if mins > 0 else 0

            gA, gB = _tourney_goals(rA), _tourney_goals(rB)

            def _split_name(full):
                parts = str(full).split()
                if len(parts) == 1:
                    return "", parts[0].upper()
                return " ".join(parts[:-1]), parts[-1].upper()

            firstA, lastA = _split_name(pA_name)
            firstB, lastB = _split_name(pB_name)

            H2H_STAT_ROWS = [
                ("goals_p90", "Goals (per 90)", "g", "{:.2f}"),
                ("assists_p90", "Assists (per 90)", "a", "{:.2f}"),
                ("shots_p90", "Shots (per 90)", "s", "{:.1f}"),
                ("dribbles_p90", "Dribbles (per 90)", "d", "{:.1f}"),
                ("pass_accuracy_pct", "Pass Accuracy", "p", "{:.0f}%"),
            ]
            H2H_ICONS = {"g": "◉", "a": "➤", "s": "◎", "d": "≋", "p": "⬡"}

            def _stat_val(row, key, driv):
                if key == "dribbles_p90":
                    return driv
                v = row.get(key)
                return float(v) if pd.notna(v) else 0.0

            def _panel_rows(row, driv):
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

            rowsA_html, rowsB_html = _panel_rows(rA, dA), _panel_rows(rB, dB)

            # ── Versus hero: national colour atmosphere, original portraits ──
            st.markdown(
                '<style>'
                '.h2h-hero{display:grid;grid-template-columns:minmax(0,1fr) 92px minmax(0,1fr);gap:0;'
                'background:#080b10;border:1px solid #343434;border-radius:0;overflow:hidden;margin:14px 0 22px;'
                'opacity:0;animation:h2h-hero-in .72s cubic-bezier(.22,.61,.36,1) .04s both;}'
                '.h2h-panel{position:relative;display:grid;grid-template-columns:minmax(0,46fr) minmax(0,54fr);'
                'min-height:500px;overflow:hidden;background:#080b10;isolation:isolate;}'
                '.h2h-panel.is-a{border-top:2px solid #f1f0eb;}'
                '.h2h-panel.is-b{border-top:1px solid #686862;}'
                '.h2h-stadium{position:absolute;inset:-3%;width:106%;height:106%;object-fit:cover;object-position:center;'
                'filter:brightness(.18) saturate(.45) blur(3px);opacity:.68;z-index:0;transform:scale(1.03);}'
                '.h2h-panel::before{content:"";position:absolute;inset:-8%;z-index:1;pointer-events:none;'
                'background:radial-gradient(circle at 30% 34%,rgba(var(--h2h-primary-rgb),.26),rgba(var(--h2h-primary-rgb),.12) 28%,transparent 62%),'
                'radial-gradient(circle at 62% 88%,rgba(var(--h2h-secondary-rgb),.11),transparent 64%);'
                'animation:h2h-glow-drift 14s ease-in-out infinite alternate;}'
                '.h2h-panel.is-b::before{background:radial-gradient(circle at 70% 34%,rgba(var(--h2h-primary-rgb),.26),rgba(var(--h2h-primary-rgb),.12) 28%,transparent 62%),'
                'radial-gradient(circle at 38% 88%,rgba(var(--h2h-secondary-rgb),.11),transparent 64%);animation-direction:alternate-reverse;}'
                '.h2h-panel::after{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;'
                'background:linear-gradient(90deg,rgba(4,6,9,.10),transparent 38%,rgba(4,6,9,.76)),linear-gradient(180deg,rgba(4,6,9,.12),transparent 42%,rgba(4,6,9,.62));}'
                '.h2h-panel.is-b::after{background:linear-gradient(270deg,rgba(4,6,9,.10),transparent 38%,rgba(4,6,9,.76)),linear-gradient(180deg,rgba(4,6,9,.12),transparent 42%,rgba(4,6,9,.62));}'
                '.h2h-photo{position:relative;min-height:500px;overflow:hidden;z-index:2;}'
                '.h2h-photo .player-portrait{position:absolute;inset:0;width:100% !important;height:100% !important;'
                'border:none !important;display:block;overflow:visible;background:transparent;}'
                '.h2h-panel.is-a .h2h-photo .player-portrait{animation:h2h-photo-a .76s cubic-bezier(.22,.61,.36,1) .10s both;}'
                '.h2h-panel.is-b .h2h-photo .player-portrait{animation:h2h-photo-b .76s cubic-bezier(.22,.61,.36,1) .10s both;}'
                '.h2h-photo .player-portrait img{object-position:center top;transform:scale(1.18);transform-origin:center top;'
                'filter:none !important;image-rendering:auto;-webkit-backface-visibility:hidden;backface-visibility:hidden;'
                'transition:opacity .6s ease,transform .7s cubic-bezier(.22,.61,.36,1);}'
                '.h2h-giant{position:absolute;top:8px;font-size:120px;font-weight:400;line-height:1;'
                'color:transparent;-webkit-text-stroke:1px rgba(241,240,235,0.35);letter-spacing:-4px;pointer-events:none;z-index:4;}'
                '.h2h-panel.is-b .h2h-giant{-webkit-text-stroke-color:rgba(155,155,149,0.4);}'
                '.h2h-panel.is-a .h2h-giant{left:12px;}'
                '.h2h-panel.is-b .h2h-giant{right:12px;}'
                '.h2h-sign{position:absolute;bottom:26px;font-size:11px;font-weight:700;letter-spacing:2px;'
                'color:#d2d2cc;pointer-events:none;text-transform:uppercase;z-index:4;}'
                '.h2h-panel.is-a .h2h-sign{left:16px;}'
                '.h2h-panel.is-b .h2h-sign{right:16px;}'
                '.h2h-body{position:relative;z-index:3;padding:30px 24px 22px;border-left:1px solid rgba(255,255,255,0.10);'
                'background:linear-gradient(90deg,rgba(var(--h2h-primary-rgb),.08),rgba(8,11,16,.82) 34%,rgba(8,11,16,.94));'
                'animation:h2h-info-in .72s cubic-bezier(.22,.61,.36,1) .18s both;}'
                '.h2h-panel.is-b .h2h-body{border-left:none;border-right:1px solid rgba(255,255,255,0.08);}'
                '.h2h-flag .team-flag-photo{position:relative;width:44px;height:30px;display:inline-block;overflow:hidden;border-radius:0;border:1px solid #343434;}'
                '.h2h-first{font-size:15px;color:#9b9b95;margin-top:10px;letter-spacing:1px;text-transform:uppercase;}'
                '.h2h-last{font-size:clamp(28px,2.2vw,38px);font-weight:400;color:#f1f0eb;line-height:1;letter-spacing:-0.5px;margin:2px 0 6px;overflow-wrap:anywhere;}'
                '.h2h-sub{font-size:12px;color:#9b9b95;}'
                '.h2h-trio{display:grid;grid-template-columns:repeat(3,1fr);margin:16px 0 14px;text-align:center;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08);}'
                '.h2h-trio > div{padding:10px 4px;border-left:1px solid rgba(255,255,255,0.08);}'
                '.h2h-trio > div:first-child{border-left:none;}'
                '.h2h-trio b{display:block;font-size:21px;font-weight:400;color:#f1f0eb;}'
                '.h2h-trio span{font-size:10px;letter-spacing:1.4px;color:#9b9b95;}'
                '.h2h-row{display:flex;align-items:center;gap:9px;padding:9px 2px;border-top:1px solid rgba(255,255,255,0.08);}'
                '.h2h-ico{color:#9b9b95;font-size:13px;}'
                '.h2h-lbl{font-size:12px;color:#9b9b95;}'
                '.h2h-val{margin-left:auto;font-size:14px;font-weight:700;color:#f1f0eb;}'
                '.h2h-vs{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;'
                'background:#080808;padding:10px 4px;border-left:1px solid rgba(255,255,255,0.08);border-right:1px solid rgba(255,255,255,0.08);}'
                '.h2h-vs .slash{width:1px;height:56px;background:rgba(255,255,255,0.20);}'
                '.h2h-vs b{font-size:34px;font-weight:400;color:#f1f0eb;letter-spacing:1px;}'
                '.h2h-vs span{font-size:10px;font-weight:700;letter-spacing:2.5px;color:#9b9b95;}'
                '@keyframes h2h-hero-in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}'
                '@keyframes h2h-photo-a{from{opacity:0;transform:translateX(-24px)}to{opacity:1;transform:translateX(0)}}'
                '@keyframes h2h-photo-b{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:translateX(0)}}'
                '@keyframes h2h-info-in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}'
                '@keyframes h2h-glow-drift{from{transform:translate3d(-4px,-2px,0)}to{transform:translate3d(4px,6px,0)}}'
                '@media (max-width:900px){.h2h-hero{grid-template-columns:1fr;}.h2h-panel,.h2h-photo{min-height:460px;}.h2h-vs{flex-direction:row;padding:14px;border:none;border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08);}.h2h-vs .slash{width:56px;height:1px;}}'
                '@media (max-width:560px){.h2h-panel{grid-template-columns:minmax(0,44fr) minmax(0,56fr);min-height:400px;}.h2h-photo{min-height:400px;}.h2h-body{padding:22px 14px 18px;}.h2h-photo .player-portrait img{transform:scale(1.10);}.h2h-first{font-size:11px;}.h2h-last{font-size:25px;}.h2h-trio b{font-size:17px;}.h2h-trio span,.h2h-lbl{font-size:9px;}.h2h-row{gap:6px;}.h2h-ico{display:none;}}'
                '@media (prefers-reduced-motion:reduce){.h2h-hero,.h2h-photo .player-portrait,.h2h-body,.h2h-panel::before{animation:none !important;opacity:1 !important;transform:none !important;}.h2h-photo .player-portrait img{transition:none !important;}}'
                '</style>'
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

            axes_p = [
                ("goals_p90", "Goals/90", False, "{:.2f}"),
                ("assists_p90", "Assists/90", False, "{:.2f}"),
                ("shots_p90", "Shots/90", False, "{:.1f}"),
                ("dribbles_p90", "Dribbles/90", True, "{:.1f}"),
                ("pass_accuracy_pct", "Pass Accuracy", False, "{:.0f}%"),
                ("passes_p90", "Passes/90", False, "{:.1f}"),
                ("tackles_p90", "Tackles/90", False, "{:.1f}"),
            ]

            def _ax_val(row, key, derived, driv):
                if derived:
                    return driv
                v = row.get(key)
                return float(v) if pd.notna(v) else 0.0

            st.markdown(
                '<style>'
                '.h2h-panel-head{display:flex;align-items:center;gap:9px;font-size:15px;font-weight:700;'
                'letter-spacing:1.2px;color:#f1f0eb;text-transform:uppercase;margin-bottom:6px;}'
                '.h2h-dot{width:8px;height:8px;border-radius:50%;background:#f1f0eb;flex:0 0 auto;}'
                '.h2h-year{margin-left:auto;font-size:10px;font-weight:600;letter-spacing:1px;color:#9b9b95;}'
                '.h2h-table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px;}'
                '.h2h-table th{font-size:11px;font-weight:600;color:#9b9b95;text-align:right;padding:8px 10px;'
                'border-bottom:1px solid rgba(255,255,255,0.14);font-weight:600;}'
                '.h2h-table th:first-child{text-align:left;}'
                '.h2h-table td{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,0.08);text-align:right;color:#f1f0eb;}'
                '.h2h-table td:first-child{text-align:left;color:#9b9b95;}'
                '.h2h-table tr:last-child td{border-bottom:none;}'
                '.h2h-delta-up{color:#f1f0eb;font-weight:700;}'
                '.h2h-delta-dn{color:#9b9b95;font-weight:700;}'
                '.h2h-delta-eq{color:#9b9b95;font-weight:700;}'
                '</style>',
                unsafe_allow_html=True,
            )

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
                        vals = [_ax_val(r_item, c, der, driv) for c, _, der, _ in axes_p]
                        maxes = []
                        for c, _, der, _ in axes_p:
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
                            theta=[lbl for _, lbl, _, _ in axes_p] + [axes_p[0][1]],
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
                    for col_key, label_str, derived, fmt in axes_p:
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
                        f'<span class="h2h-year">{len(axes_p)} RECORDS / 4 FIELDS</span></div>'
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
                    hs = int(r["Home_Score"])
                    as_ = int(r["Away_Score"])
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

                st_card_html = '<div style="background:#0e0e0e;border:1px solid #343434;border-radius:0;padding:18px">'
                for label, col, unit in stat_specs_team:
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




