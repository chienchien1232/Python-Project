# -*- coding: utf-8 -*-
"""WorldCup Stats '26 - Match Center & Detailed Analytics."""
import os
import sys
import html as html_lib

import pandas as pd
import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys_path = os.path.join(ROOT, "src")
app_path = os.path.join(ROOT, "src", "app")
for p in [app_path, sys_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers import cfg_num, flag_img, flag_url, icon_badge, icon_svg, q  # noqa: E402

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


def flag(team_name: str) -> str:
    return FLAGS.get(clean_name(team_name), "⚽")


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


# ── Header & KPI summary ──────────────────────────────────────────────────────
try:
    kpi_m = q("""
        SELECT COUNT(*) AS total_m,
               COALESCE(SUM(home_score + away_score), 0) AS total_g,
               COALESCE(SUM(attendance), 0) AS total_att
        FROM matches
    """)
    n_m = int(kpi_m.iloc[0]["total_m"]) if not kpi_m.empty else 104
    n_g = int(kpi_m.iloc[0]["total_g"]) if not kpi_m.empty else 308
    n_att = int(kpi_m.iloc[0]["total_att"]) if not kpi_m.empty else 0
except Exception:
    n_m, n_g, n_att = 104, 308, 0

avg_g = round(n_g / max(n_m, 1), 2)

st.markdown(
    '<div class="wc-hero-wrapper" style="margin-bottom:20px">'
    '<div class="wc-hero-badge-row">'
    '<div class="wc-hero-badge"><span class="wc-badge-dot"></span> MATCH CENTER</div>'
    '<div class="wc-hero-dates">104 FIXTURES &amp; RESULTS · TOURNAMENT ARCHIVE</div>'
    '</div>'
    '<div class="wc-hero-title" style="font-size:52px;margin-bottom:10px">'
    '<span class="title-white">TOURNAMENT</span>'
    '<span class="title-lime">MATCHES.</span>'
    '</div>'
    '<div class="wc-hero-desc" style="max-width:760px;margin-bottom:16px">'
    'Explore complete match reports from the 2026 FIFA World Cup. Inspect tactical lineups, timeline events, '
    'live head-to-head match statistics, and deep player performance ratings.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="kpi-row-container" style="margin-bottom:28px">'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_m}</div><div class="kpi-sport-label">MATCHES PLAYED</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_g}</div><div class="kpi-sport-label">TOTAL GOALS</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{avg_g}</div><div class="kpi-sport-label">GOALS / MATCH</div></div>'
    f'<div class="kpi-sport-card"><div class="kpi-sport-num">{n_att:,}</div><div class="kpi-sport-label">TOTAL ATTENDANCE</div></div>'
    '</div>',
    unsafe_allow_html=True,
)


# ── Filter controls ───────────────────────────────────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('search')} Filter & Select Match</div>", unsafe_allow_html=True)

try:
    stage_list = ["All Stages"] + [r[0] for r in q("SELECT DISTINCT stage_name FROM matches_detailed ORDER BY stage_name").values.tolist()]
except Exception:
    stage_list = ["All Stages", "Group Stage", "Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Third Place", "Final"]

try:
    team_list = ["All Teams"] + sorted([clean_name(r[0]) for r in q("SELECT DISTINCT team_name FROM teams").values.tolist()])
except Exception:
    team_list = ["All Teams"]

col_f1, col_f2, col_f3 = st.columns([1.2, 1.2, 1.6])
with col_f1:
    sel_stage = st.selectbox("Stage", stage_list)
with col_f2:
    sel_team = st.selectbox("Team", team_list)
# Anomaly detection: z-score ca possession va shots theo tung doi-tran
mts = q("SELECT match_id, team_id, possession_pct, total_shots FROM match_team_stats")
anomaly_detail = {}
anomaly_ids = set()
if not mts.empty:
    zp = (mts["possession_pct"] - mts["possession_pct"].mean()) / max(mts["possession_pct"].std(), 1e-9)
    zs = (mts["total_shots"] - mts["total_shots"].mean()) / max(mts["total_shots"].std(), 1e-9)
    mts = mts.assign(z_poss=zp, z_shots=zs)
    for _, r in mts[(mts["z_poss"].abs() > 2.3) | (mts["z_shots"].abs() > 2.3)].iterrows():
        z_p, z_s = float(r["z_poss"]), float(r["z_shots"])
        met = "possession" if abs(z_p) >= abs(z_s) else "shots"
        sig = round(max(abs(z_p), abs(z_s)), 1)
        mid_ = str(r["match_id"])
        if mid_ not in anomaly_detail or sig > anomaly_detail[mid_]["sigma"]:
            anomaly_detail[mid_] = {"sigma": sig, "metric": met,
                                    "team_id": str(r["team_id"])}
anomaly_ids = set(anomaly_detail.keys())

with col_f3:
    anom_only = st.checkbox(f"⚡ Show Anomalous Matches Only ({len(anomaly_ids)} matches | z > 2.3)")

# Load matches with details
sql = """
    SELECT m.match_id AS ID, d.date AS Date, d.stage_name AS Stage,
           d.home_team_name AS Home_Team, d.home_score AS Home_Score,
           d.away_score AS Away_Score, d.away_team_name AS Away_Team,
           m.attendance AS Attendance,
           th.manager_name AS Home_Manager, ta.manager_name AS Away_Manager,
           d.stadium_name AS Stadium, d.city AS City,
           d.player_of_the_match_name AS MOTM, d.referee_name AS Referee,
           d.result_type AS Result_Type
    FROM matches_detailed d
    JOIN matches m ON m.match_id = d.match_id
    JOIN teams th ON th.team_id = m.home_team_id
    JOIN teams ta ON ta.team_id = m.away_team_id
    WHERE 1=1
"""
params = []
if sel_stage != "All Stages":
    sql += " AND d.stage_name = ?"
    params.append(sel_stage)
if sel_team != "All Teams":
    sql += " AND (d.home_team_name = ? OR d.away_team_name = ?)"
    params.extend([sel_team, sel_team])

df_matches = q(sql + " ORDER BY d.date, m.match_id", params)

if not df_matches.empty:
    df_matches["Home_Team"] = df_matches["Home_Team"].apply(clean_name)
    df_matches["Away_Team"] = df_matches["Away_Team"].apply(clean_name)


if not df_matches.empty:
    df_matches["Anomalous"] = df_matches["ID"].apply(lambda x: f"⚡ {anomaly_detail[x]['sigma']}σ {anomaly_detail[x]['metric']}" if x in anomaly_detail else "")
    if anom_only:
        df_matches = df_matches[df_matches["ID"].isin(anomaly_ids)]

# Match selection mapping
match_options = {}
if not df_matches.empty:
    for _, r in df_matches.iterrows():
        mid = r["ID"]
        h_fl = flag(r["Home_Team"])
        a_fl = flag(r["Away_Team"])
        anom_tag = f" [⚡ {anomaly_detail[mid]['sigma']}σ]" if mid in anomaly_detail else ""
        label = f"Match #{mid}: {h_fl} {r['Home_Team']} {r['Home_Score']} - {r['Away_Score']} {r['Away_Team']} {a_fl} ({r['Stage']}){anom_tag}"
        match_options[label] = mid

sel_label = st.selectbox(
    "Select match to inspect in-depth Match Center:",
    list(match_options.keys()) if match_options else ["No matches found"]
)

selected_mid = match_options.get(sel_label)


# ── Detailed Match Center ─────────────────────────────────────────────────────
if selected_mid:
    info = df_matches[df_matches["ID"] == selected_mid].iloc[0]
    h_team = info["Home_Team"]
    a_team = info["Away_Team"]
    h_score = int(info["Home_Score"])
    a_score = int(info["Away_Score"])
    h_flag = flag(h_team)
    a_flag = flag(a_team)
    is_anom = selected_mid in anomaly_ids

    anom_badge_html = '<span style="background:rgba(255,82,82,0.15);color:#ff5252;border:1px solid #ff5252;border-radius:999px;padding:3px 10px;font-size:11px;font-weight:700;margin-left:8px">⚡ ANOMALOUS PERFORMANCE</span>' if is_anom else ''

    att_str = f"{int(info['Attendance']):,} attendance" if pd.notna(info.get("Attendance")) and info["Attendance"] else "Full capacity"
    ref_str = f"Referee: {clean_name(info['Referee'])}" if pd.notna(info.get("Referee")) and info["Referee"] else ""
    motm_str = f"{icon_svg('star', 12)} MOTM: {clean_name(info['MOTM'])}" if pd.notna(info.get("MOTM")) and info["MOTM"] else ""

    # Scoreboard Card
    st.markdown(
        f'<div class="match-hero-card">'
        f'<div class="match-hero-meta">'
        f'<div><span class="match-stage-badge">{info["Stage"]}</span>{anom_badge_html}</div>'
        f'<div class="match-venue-text">{icon_svg("calendar", 12)} {info["Date"]} &nbsp;·&nbsp; {icon_svg("stadium", 12)} {info["Stadium"]}, {info["City"]}</div>'
        f'</div>'
        f'<div class="match-scoreboard-main">'
        f'<div class="match-team-block home">'
        f'<div class="match-team-name-big">{h_team}</div>'
        f'<div class="match-team-flag-big">{flag_img(h_team, 46, fallback_emoji=h_flag)}</div>'
        f'</div>'
        f'<div class="match-score-display">'
        f'<div class="match-score-numbers">{h_score} &nbsp;–&nbsp; {a_score}</div>'
        f'<div class="match-status-pill">{info.get("Result_Type", "Full Time")}</div>'
        f'</div>'
        f'<div class="match-team-block away">'
        f'<div class="match-team-flag-big">{flag_img(a_team, 46, fallback_emoji=a_flag)}</div>'
        f'<div class="match-team-name-big">{a_team}</div>'
        f'</div>'
        f'</div>'
        f'<div class="match-hero-footer">'
        f'<div>{icon_svg("users", 12)} Managers: <strong>{clean_name(info["Home_Manager"])}</strong> vs <strong>{clean_name(info["Away_Manager"])}</strong></div>'
        f'<div>{motm_str} &nbsp;·&nbsp; {att_str} &nbsp;·&nbsp; {ref_str}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Why is this anomalous? panel
    if is_anom:
        tm = q("SELECT team_id, team_name FROM teams")
        tm_map = dict(zip(tm["team_id"].astype(str), tm["team_name"].apply(clean_name)))
        rows_m = mts[mts["match_id"].astype(str) == str(selected_mid)]
        why_rows = ""
        for _, rr in rows_m.iterrows():
            tname = tm_map.get(str(rr["team_id"]), "?")
            for met, zc in (("possession", "z_poss"), ("shots", "z_shots")):
                zv = float(rr[zc])
                if abs(zv) > 1.5:
                    width = min(abs(zv) / 4 * 100, 100)
                    clr = "#ff5252" if abs(zv) > 3 else "#ffb84d"
                    why_rows += (
                        f'<div style="margin:7px 0">'
                        f'<div style="display:flex;justify-content:space-between;font-size:12.5px">'
                        f'<span style="color:#F8FAFC;font-weight:700">{tname} &mdash; {met}</span>'
                        f'<span style="color:{clr};font-weight:800">{zv:+.1f}σ</span></div>'
                        f'<div style="height:7px;background:rgba(255,255,255,0.06);border-radius:999px">'
                        f'<div style="height:100%;width:{width:.0f}%;border-radius:999px;background:{clr}"></div></div></div>')
        if why_rows:
            st.markdown(
                '<div style="background:#111612;border:1px solid rgba(255,82,82,0.35);border-radius:14px;padding:16px 20px;margin-bottom:18px">'
                '<div style="font-size:11px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#ff5252;margin-bottom:4px">⚡ Why is this match anomalous?</div>'
                '<div style="font-size:12px;color:#94a3b8;margin-bottom:6px">z-score = how far a team number is from the tournament average. |z| &gt; 2.3 &#8776; the most extreme 1% of all team performances.</div>'
                + why_rows + '</div>',
                unsafe_allow_html=True,
            )

    col_det_left, col_det_right = st.columns([1.1, 1.0], gap="large")

    with col_det_left:
        # Match Events Timeline
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('bolt')} Match Timeline &amp; Events</div>", unsafe_allow_html=True)
        events = q("""
            SELECT e.minute, e.event_type, e.team_id,
                   p.player_name, t.team_name
            FROM match_events e
            LEFT JOIN players p ON CAST(p.player_id AS TEXT) = CAST(e.player_id AS TEXT)
            LEFT JOIN teams t ON CAST(t.team_id AS TEXT) = CAST(e.team_id AS TEXT)
            WHERE CAST(e.match_id AS TEXT) = ?
            ORDER BY e.minute, e.event_id
        """, (str(selected_mid),))

        if not events.empty:
            events_html = '<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:16px;margin-bottom:20px">'
            for _, ev in events.iterrows():
                etype = ev["event_type"]
                pname = clean_name(ev["player_name"]) if pd.notna(ev.get("player_name")) else "Unknown"
                tname = clean_name(ev["team_name"]) if pd.notna(ev.get("team_name")) else ""
                icon = icon_svg("ball", 15) if "Goal" in etype else icon_svg("target", 15) if "Assist" in etype else "🟥" if "Red" in etype else "🟨" if "Yellow" in etype else icon_svg("ball", 15)
                events_html += (
                    f'<div class="event-item">'
                    f'<div class="event-min">{ev["minute"]}\'</div>'
                    f'<div class="event-icon">{icon}</div>'
                    f'<div style="flex:1"><strong>{html_lib.escape(pname)}</strong> <span style="color:#64748b">({html_lib.escape(tname)})</span></div>'
                    f'<div style="font-size:12px;font-weight:700;color:#94a3b8">{html_lib.escape(etype)}</div>'
                    f'</div>'
                )
            events_html += '</div>'
            st.markdown(events_html, unsafe_allow_html=True)
        else:
            st.info("No timeline event records available for this match.")

        # Head-to-Head Team Match Stats
        st.markdown(f"<div class='section-header' style='font-size:20px'>{icon_badge('chart')} Head-to-Head Statistics</div>", unsafe_allow_html=True)
        ts = q("""
            SELECT team_id, possession_pct, total_shots, shots_on_target,
                   corners, fouls, offsides, saves
            FROM match_team_stats WHERE CAST(match_id AS TEXT) = ?
        """, (str(selected_mid),))

        if len(ts) >= 2:
            home_s = ts.iloc[0]
            away_s = ts.iloc[1]

            stat_specs = [
                ("Possession", "possession_pct", "%"),
                ("Total Shots", "total_shots", ""),
                ("Shots on Target", "shots_on_target", ""),
                ("Corner Kicks", "corners", ""),
                ("Fouls Committed", "fouls", ""),
                ("Offsides", "offsides", ""),
                ("Goalkeeper Saves", "saves", ""),
            ]

            stat_card_html = '<div style="background:#111612;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:20px;margin-bottom:20px">'
            for label, col, unit in stat_specs:
                h_val = float(home_s[col]) if pd.notna(home_s.get(col)) else 0.0
                a_val = float(away_s[col]) if pd.notna(away_s.get(col)) else 0.0
                tot = max(h_val + a_val, 1e-6)
                h_pct = round((h_val / tot) * 100, 1)
                a_pct = 100.0 - h_pct

                h_display = f"{int(h_val)}{unit}" if unit == "%" or h_val.is_integer() else f"{h_val}{unit}"
                a_display = f"{int(a_val)}{unit}" if unit == "%" or a_val.is_integer() else f"{a_val}{unit}"

                stat_card_html += (
                    f'<div class="match-stat-row">'
                    f'<div class="match-stat-labels">'
                    f'<span class="match-stat-val" style="color:#ccff00">{h_display}</span>'
                    f'<span class="match-stat-name">{label}</span>'
                    f'<span class="match-stat-val" style="color:#38bdf8">{a_display}</span>'
                    f'</div>'
                    f'<div class="match-bar-bg">'
                    f'<div class="match-bar-home" style="width:{h_pct}%"></div>'
                    f'<div class="match-bar-away" style="width:{a_pct}%"></div>'
                    f'</div>'
                    f'</div>'
                )
            stat_card_html += '</div>'
            st.markdown(stat_card_html, unsafe_allow_html=True)

    with col_det_right:
        # Squad Lineups (Starters & Bench)
        st.markdown(f"<div class='section-header' style='font-size:20px;margin-top:0'>{icon_badge('users')} Tactical Lineups</div>", unsafe_allow_html=True)
        lu = q("""
            SELECT CAST(l.team_id AS TEXT) AS team_id,
                   t.team_name,
                   CAST(l.is_starting_xi AS INTEGER) AS is_starting_xi,
                   pm.shirt_number,
                   p.player_name,
                   l.tactical_position,
                   l.minutes_played
            FROM match_lineups l
            LEFT JOIN teams t ON CAST(t.team_id AS TEXT) = CAST(l.team_id AS TEXT)
            LEFT JOIN players p ON CAST(p.player_id AS TEXT) = CAST(l.player_id AS TEXT)
            LEFT JOIN player_match_stats pm
                   ON CAST(pm.match_id AS TEXT) = CAST(l.match_id AS TEXT)
                  AND CAST(pm.player_id AS TEXT) = CAST(l.player_id AS TEXT)
            WHERE CAST(l.match_id AS TEXT) = ?
            ORDER BY l.is_starting_xi DESC, pm.shirt_number, l.lineup_id
        """, (str(selected_mid),))

        if not lu.empty:
            lu["player_name"] = lu["player_name"].apply(clean_name)
            lu["team_name"] = lu["team_name"].apply(clean_name)

            tab_home, tab_away = st.tabs([f"🏠 {h_flag} {h_team} (Home)", f"✈️ {a_flag} {a_team} (Away)"])

            with tab_home:
                h_starters = lu[(lu["team_name"] == h_team) & (lu["is_starting_xi"] == 1)][["shirt_number", "player_name", "tactical_position", "minutes_played"]]
                h_starters.columns = ["#", "Player", "Pos", "Mins"]
                h_bench = lu[(lu["team_name"] == h_team) & (lu["is_starting_xi"] == 0)][["shirt_number", "player_name", "tactical_position", "minutes_played"]]
                h_bench.columns = ["#", "Substitute", "Pos", "Mins"]

                st.markdown(f"**{h_flag} {h_team} — Starting XI (11 Players)**")
                st.dataframe(h_starters, width="stretch", hide_index=True, column_config={"#": cfg_num("#", "%.0f"), "Mins": cfg_num("Mins", "%.0f")})
                st.markdown(f"**{h_flag} {h_team} — Substitutes Bench (15 Players)**")
                st.dataframe(h_bench, width="stretch", hide_index=True, column_config={"#": cfg_num("#", "%.0f"), "Mins": cfg_num("Mins", "%.0f")})

            with tab_away:
                a_starters = lu[(lu["team_name"] == a_team) & (lu["is_starting_xi"] == 1)][["shirt_number", "player_name", "tactical_position", "minutes_played"]]
                a_starters.columns = ["#", "Player", "Pos", "Mins"]
                a_bench = lu[(lu["team_name"] == a_team) & (lu["is_starting_xi"] == 0)][["shirt_number", "player_name", "tactical_position", "minutes_played"]]
                a_bench.columns = ["#", "Substitute", "Pos", "Mins"]

                st.markdown(f"**{a_flag} {a_team} — Starting XI (11 Players)**")
                st.dataframe(a_starters, width="stretch", hide_index=True, column_config={"#": cfg_num("#", "%.0f"), "Mins": cfg_num("Mins", "%.0f")})
                st.markdown(f"**{a_flag} {a_team} — Substitutes Bench (15 Players)**")
                st.dataframe(a_bench, width="stretch", hide_index=True, column_config={"#": cfg_num("#", "%.0f"), "Mins": cfg_num("Mins", "%.0f")})
        else:
            st.info("Lineup data not recorded for this match.")

    # Player Match Performance Ratings Table
    st.markdown(f"<div class='section-header'>{icon_badge('star')} Player Match Performance Ratings</div>", unsafe_allow_html=True)
    pm = q("""
        SELECT player_team AS Team, shirt_number AS No,
               player_name AS Player, position AS Pos,
               minutes_played AS Mins, goals AS Goals, assists AS Assists,
               shots AS Shots, passes AS Passes, accurate_passes AS Acc_Passes,
               tackles AS Tackles, interceptions AS Interceptions, clearances AS Clearances,
               fouls_committed AS Fouls, yellow_cards AS Yellow, red_cards AS Red
        FROM player_match_stats
        WHERE CAST(match_id AS TEXT) = ?
        ORDER BY Team, minutes_played DESC, Goals DESC, Assists DESC
    """, (str(selected_mid),))

    if not pm.empty:
        pm["Player"] = pm["Player"].apply(clean_name)
        pm["Team"] = pm["Team"].apply(clean_name)

        # Baseline vi tri toan giai (per-90) -> z-score tung cau thu trong tran
        pms_all = q("SELECT position, minutes_played, goals, assists, shots, passes, tackles, interceptions FROM player_match_stats WHERE minutes_played > 0")
        for _c in ("minutes_played", "goals", "assists", "shots", "passes",
                   "tackles", "interceptions"):
            pms_all[_c] = pd.to_numeric(pms_all[_c], errors="coerce")
        pms_all = pms_all[pms_all["minutes_played"] > 0]
        for _c in ("goals", "assists", "shots", "passes"):
            pms_all[_c + "_p90"] = 90.0 * pms_all[_c] / pms_all["minutes_played"].replace(0, pd.NA)
        _mcols = [c + "_p90" for c in ("goals", "assists", "shots", "passes")]
        _gb = pms_all.groupby("position")[_mcols].agg(["mean", "std"])

        def _z(pos, col, val):
            try:
                mu = _gb.loc[pos, (col + "_p90", "mean")]
                sd = _gb.loc[pos, (col + "_p90", "std")]
                if sd == sd and sd > 0:
                    return float((val - mu) / sd)
            except Exception:
                pass
            return 0.0

        gk_all = q("SELECT minutes_played, saves FROM goalkeeper_match_stats WHERE minutes_played > 0")
        gk_all["saves"] = pd.to_numeric(gk_all["saves"], errors="coerce")
        gk_all["minutes_played"] = pd.to_numeric(gk_all["minutes_played"], errors="coerce")
        gk_all = gk_all[gk_all["saves"].notna() & (gk_all["minutes_played"] > 0)]
        _gkr = 90.0 * gk_all["saves"] / gk_all["minutes_played"]
        gk_mean, gk_std = float(_gkr.mean()), float(_gkr.std() or 1.0)
        gk_match = q("SELECT player_name, minutes_played, saves FROM goalkeeper_match_stats WHERE CAST(match_id AS TEXT) = ?", (str(selected_mid),))
        if not gk_match.empty:
            gk_match["saves"] = pd.to_numeric(gk_match["saves"], errors="coerce")
            gk_match["minutes_played"] = pd.to_numeric(gk_match["minutes_played"], errors="coerce")

        pm["_z"] = 0.0
        pm["_why"] = ""
        for i, r in pm.iterrows():
            mins = float(r["Mins"] or 0)
            zbest, lbl = 0.0, ""
            if mins > 0:
                zg = _z(r["Pos"], "goals", 90.0 * float(r["Goals"] or 0) / mins)
                za = _z(r["Pos"], "assists", 90.0 * float(r["Assists"] or 0) / mins)
                zsh = _z(r["Pos"], "shots", 90.0 * float(r["Shots"] or 0) / mins)
                zbest, lbl = max((zg, "goals"), (za, "assists"), (zsh, "shots"))
            gk_row = gk_match[gk_match["player_name"] == r["Player"]] if not gk_match.empty else pd.DataFrame()
            if not gk_row.empty and mins > 0:
                zs = ((90.0 * float(gk_row.iloc[0]["saves"] or 0) / mins) - gk_mean) / gk_std
                if abs(zs) > abs(zbest):
                    zbest, lbl = zs, "saves"
            pm.at[i, "_z"] = round(zbest, 1)
            pm.at[i, "_why"] = f"{lbl} {zbest:+.1f}σ"

        motm_name = clean_name(str(info["MOTM"])) if pd.notna(info.get("MOTM")) and info["MOTM"] else ""
        pm["_sort"] = (pm["_z"] >= 2.0).astype(int) * 100 + pm["_z"].clip(0, 10)
        pm = pm.sort_values("_sort", ascending=False, kind="stable")

        heads = ["Team", "#", "Player", "Pos", "Mins", "Goals", "Assists", "Shots", "Passes", "Acc. Passes", "Tackles", "Int.", "Clear.", "Fouls", "Yellow", "Red", "Perf vs Avg"]
        keys = ["Team", "No", "Player", "Pos", "Mins", "Goals", "Assists", "Shots", "Passes", "Acc_Passes", "Tackles", "Interceptions", "Clearances", "Fouls", "Yellow", "Red"]
        rows_h = ""
        for _, r in pm.iterrows():
            standout = float(r["_z"]) >= 2.0
            is_m = bool(motm_name) and str(r["Player"]) == motm_name
            bg = "rgba(204,255,0,0.07)" if standout else ("rgba(255,215,0,0.05)" if is_m else "rgba(255,255,255,0.02)")
            bd = "rgba(204,255,0,0.35)" if standout else "var(--border-subtle)"
            badge = ""
            if standout:
                badge += (f'<span style="background:rgba(204,255,0,0.15);color:#ccff00;border-radius:6px;padding:1px 7px;font-size:10px;font-weight:800;margin-left:6px">{icon_svg("flame", 11)} {r["_why"]}</span>')
            if is_m:
                badge += ('<span style="background:rgba(255,215,0,0.15);color:#ffd700;border-radius:6px;padding:1px 7px;font-size:10px;font-weight:800;margin-left:6px">⭐ MOTM</span>')
            tds = ""
            for k in keys:
                v = r[k]
                v = "" if pd.isna(v) else (str(int(v)) if isinstance(v, float) and v == int(v) else str(v))
                sty = ("font-weight:800;color:#F8FAFC;white-space:nowrap" if k == "Player" else "color:#CBD5E1;white-space:nowrap")
                tds += f'<td style="padding:6px 10px;font-size:12.5px;{sty}">{html_lib.escape(v)}</td>'
            tds += (f'<td style="padding:6px 10px;font-size:12px;font-weight:800;color:{"#ccff00" if standout else "#64748b"};white-space:nowrap">'
                     f'{(r["_why"] if standout else "—")}{badge}</td>')
            rows_h += f'<tr style="background:{bg};border-bottom:1px solid {bd};">{tds}</tr>'
        head_h = "".join(f'<th style="padding:8px 10px;font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:#64748b;text-align:left;border-bottom:1px solid var(--border-subtle)">{h}</th>' for h in heads)
        st.markdown(
            '<div style="background:#111612;border:1px solid var(--border-subtle);border-radius:12px;overflow-x:auto">'
            '<table style="width:100%;border-collapse:collapse">'
            f'<thead><tr>{head_h}</tr></thead><tbody>{rows_h}</tbody></table></div>',
            unsafe_allow_html=True,
        )
        n_std = int((pm["_z"] >= 2.0).sum())
        st.caption(f"Flame badge = performance at least 2σ above the positional tournament average ({n_std} standouts in this match) | ⭐ = Player of the Match.")


# ── Full Matches Fixtures Table ───────────────────────────────────────────────
st.markdown(f"<div class='section-header'>{icon_badge('clipboard')} All Filtered Fixtures &amp; Results</div>", unsafe_allow_html=True)

if not df_matches.empty:
    display_df = df_matches[["ID", "Date", "Stage", "Home_Team", "Home_Score", "Away_Score", "Away_Team", "Stadium", "City", "Attendance", "Anomalous"]].copy()
    display_df.columns = ["ID", "Date", "Stage", "Home Team", "Home", "Away", "Away Team", "Stadium", "City", "Attendance", "Notes"]
    display_df.insert(3, " ", df_matches["Home_Team"].map(flag_url))
    display_df.insert(7, "  ", df_matches["Away_Team"].map(flag_url))
    st.dataframe(display_df, width="stretch", hide_index=True, column_config={" ": st.column_config.ImageColumn("", width="small"),"  ": st.column_config.ImageColumn("", width="small"),"Home": cfg_num("Home", "%.0f"), "Away": cfg_num("Away", "%.0f"),"Attendance": cfg_num("Attendance", "%.0f")})
else:
    st.warning("No matches found matching the selected filter criteria.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:12.5px;padding:20px 0;border-top:1px solid rgba(255,255,255,0.06)'>"
    "WorldCup Stats '26 Analytics Platform &nbsp;·&nbsp; Data powered by FIFA, ESPN &amp; official match records &nbsp;·&nbsp; Built with Python &amp; Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
