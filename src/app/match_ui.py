"""HTML components for the editorial match calendar and match programme."""
from __future__ import annotations

from html import escape
from typing import Any
from urllib.parse import urlencode

import pandas as pd

from match_data import team_code
from media_ui import flag_image


def safe(value: Any, fallback: str = "—") -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return escape(text) if text else fallback


def format_date(value: Any, compact: bool = False) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "—"
    return parsed.strftime("%d %b" if compact else "%d %b %Y").upper()


def is_completed(match: pd.Series) -> bool:
    status = str(match.get("Status", "")).lower()
    return "complete" in status or (
        pd.notna(match.get("Home_Score")) and pd.notna(match.get("Away_Score"))
    )


def match_status(match: pd.Series) -> str:
    status = str(match.get("Status", "")).strip()
    if "live" in status.lower():
        return "LIVE"
    if is_completed(match):
        result_type = str(match.get("Result_Type", "")).strip().lower()
        if result_type and result_type not in {"regular", "nan", "none"}:
            return result_type.upper()
        return "FULL TIME"
    return "UPCOMING"


def score_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(int(float(value)))


def detail_url(match_id: Any) -> str:
    return "/match_detail?" + urlencode({"match_id": str(int(match_id))})


def section_heading(number: str, title: str, anchor: str) -> str:
    return (
        f'<div id="{anchor}" class="match-section-anchor"></div>'
        '<div class="match-section-heading">'
        f'<span>{escape(number)}.</span><h2>{escape(title)}</h2>'
        '</div>'
    )


def render_calendar_hero(match_count: int) -> str:
    return (
        '<div class="match-experience match-calendar-mode" aria-hidden="true"></div>'
        '<section class="match-calendar-hero">'
        '<div class="match-motion-layer match-motion-grid"></div>'
        '<div class="match-motion-layer match-motion-ring"></div>'
        '<div class="match-motion-layer match-motion-slash"></div>'
        '<div class="match-hero-meta"><span>MATCH CALENDAR / 2026</span>'
        f'<span>{match_count:03d} FIXTURES &amp; RESULTS</span></div>'
        '<div class="match-calendar-title"><span>TOURNAMENT</span><span>MATCHES.</span></div>'
        '<div class="match-calendar-intro">'
        '<p>Explore every fixture and result from the 2026 FIFA World Cup.</p>'
        '<span>SELECT A MATCH<br>ENTER THE STORY</span>'
        '</div></section>'
    )


def render_stat_strip(match_count: int, goals: int, average: float, attendance: int) -> str:
    compact_attendance = (
        f"{attendance / 1_000_000:.2f}M" if attendance >= 1_000_000 else f"{attendance:,}"
    )
    items = (
        (match_count, "MATCHES"), (goals, "GOALS"),
        (f"{average:.2f}", "GOALS / MATCH"), (compact_attendance, "ATTENDANCE"),
    )
    cells = "".join(
        f'<div class="match-stat-cell"><strong>{value}</strong><span>{label}</span></div>'
        for value, label in items
    )
    return f'<div class="match-stat-strip">{cells}</div>'


def render_match_card(match: pd.Series, anomalous: bool = False) -> str:
    completed = is_completed(match)
    live = "live" in str(match.get("Status", "")).lower()
    home = safe(match.get("Home_Team")).upper()
    away = safe(match.get("Away_Team")).upper()
    home_code = safe(team_code(match.get("Home_Team"), match.get("Home_Code")))
    away_code = safe(team_code(match.get("Away_Team"), match.get("Away_Code")))
    home_flag = flag_image(match.get("Home_Team"), match.get("Home_Code"), "team-flag-photo")
    away_flag = flag_image(match.get("Away_Team"), match.get("Away_Code"), "team-flag-photo")
    home_score = score_value(match.get("Home_Score"))
    away_score = score_value(match.get("Away_Score"))
    score = f"{home_score}<i>—</i>{away_score}" if completed else "<em>VS</em>"
    attendance = match.get("Attendance")
    attendance_text = f"{int(attendance):,}" if pd.notna(attendance) and attendance else "—"
    referee = safe(match.get("Referee"))
    anomaly = '<span class="match-anomaly">ANOMALY</span>' if anomalous else ""
    live_class = " is-live" if live else ""
    match_id = int(match["ID"])
    return (
        f'<a class="fixture-card{live_class}" href="{detail_url(match_id)}" target="_self" '
        f'aria-label="View match {match_id}: {home} versus {away}">'
        '<div class="fixture-card-top">'
        f'<span>MATCH {match_id:02d}</span><span>{safe(match.get("Stage")).upper()}</span></div>'
        f'<div class="fixture-card-date">{format_date(match.get("Date"))}</div>'
        f'<div class="fixture-card-city">{safe(match.get("City")).upper()}</div>'
        f'<div class="fixture-card-venue">{safe(match.get("Stadium"))}</div>'
        '<div class="fixture-matchup">'
        f'<div class="fixture-team">{home_flag}<span class="fixture-code">{home_code}</span><b>{home}</b></div>'
        f'<div class="fixture-score">{score}</div>'
        f'<div class="fixture-team away"><b>{away}</b><span class="fixture-code">{away_code}</span>{away_flag}</div>'
        '</div>'
        f'<div class="fixture-status"><span>{match_status(match)}</span>{anomaly}</div>'
        '<div class="fixture-facts">'
        f'<span>ATTENDANCE <b>{attendance_text}</b></span><span>REFEREE <b>{referee}</b></span></div>'
        '<div class="fixture-cta"><span>VIEW MATCH DETAILS</span><b aria-hidden="true">→</b></div>'
        '</a>'
    )


def _team_stat_rows(match: pd.Series, stats: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    if stats.empty:
        return None, None
    home_id = str(match.get("Home_Team_ID"))
    away_id = str(match.get("Away_Team_ID"))
    home = stats[stats["team_id"].astype(str) == home_id]
    away = stats[stats["team_id"].astype(str) == away_id]
    if home.empty or away.empty:
        return (stats.iloc[0], stats.iloc[1]) if len(stats) >= 2 else (None, None)
    return home.iloc[0], away.iloc[0]


def render_detail_hero(match: pd.Series) -> str:
    home = safe(match.get("Home_Team")).upper()
    away = safe(match.get("Away_Team")).upper()
    home_code = safe(team_code(match.get("Home_Team"), match.get("Home_Code")))
    away_code = safe(team_code(match.get("Away_Team"), match.get("Away_Code")))
    home_flag = flag_image(match.get("Home_Team"), match.get("Home_Code"), "team-flag-photo")
    away_flag = flag_image(match.get("Away_Team"), match.get("Away_Code"), "team-flag-photo")
    completed = is_completed(match)
    score = (
        f'<strong>{score_value(match.get("Home_Score"))}<i>—</i>'
        f'{score_value(match.get("Away_Score"))}</strong>'
        if completed else '<strong class="versus">VS</strong>'
    )
    facts = (
        ("DATE", format_date(match.get("Date"))),
        ("STADIUM", safe(match.get("Stadium")).upper()),
        ("CITY", safe(match.get("City")).upper()),
        ("ATTENDANCE", f"{int(match['Attendance']):,}" if pd.notna(match.get("Attendance")) and match.get("Attendance") else "—"),
        ("REFEREE", safe(match.get("Referee")).upper()),
        ("MANAGERS", f'{safe(match.get("Home_Manager")).upper()}<br>{safe(match.get("Away_Manager")).upper()}'),
    )
    fact_html = "".join(
        f'<div><span>{label}</span><b>{value}</b></div>' for label, value in facts
    )
    return (
        '<div class="match-experience match-detail-mode" aria-hidden="true"></div>'
        '<section class="match-detail-hero">'
        '<div class="detail-motion-layer detail-layer-grid"></div>'
        '<div class="detail-motion-layer detail-layer-score"></div>'
        '<div class="detail-motion-layer detail-layer-line"></div>'
        '<div class="detail-kicker">'
        f'<span>MATCH {int(match["ID"]):02d}</span><span>{safe(match.get("Stage")).upper()}</span>'
        f'<span>{format_date(match.get("Date"))}</span><span>{safe(match.get("City")).upper()}</span></div>'
        '<div class="detail-matchup">'
        f'<div class="detail-team">{home_flag}<span>{home_code}</span><h1>{home}</h1></div>'
        f'<div class="detail-score">{score}<span>{match_status(match)}</span></div>'
        f'<div class="detail-team away"><h1>{away}</h1><span>{away_code}</span>{away_flag}</div>'
        '</div>'
        '<div class="worldcup-tricolor" aria-hidden="true"></div>'
        f'<div class="detail-info-bar">{fact_html}</div>'
        '</section>'
    )


def render_anomaly_panel(details: pd.DataFrame) -> str:
    """Explain why a flagged match is anomalous, in match-programme style."""
    if details.empty:
        return ""
    rows = []
    for _, row in details.iterrows():
        direction = "ABOVE" if row["z"] >= 0 else "BELOW"
        rows.append(
            '<div class="anomaly-row">'
            f'<span class="anomaly-team">{escape(str(row["team_name"])).upper()}</span>'
            f'<span class="anomaly-metric">{escape(str(row["metric"]))}</span>'
            f'<span class="anomaly-values">{row["value"]:.1f}{row["unit"]} '
            f'<i>AVG {row["average"]:.1f}{row["unit"]}</i></span>'
            f'<span class="anomaly-z">Z {row["z"]:+.1f}σ · {direction} AVG</span>'
            '</div>'
        )
    return (
        '<section class="anomaly-programme" aria-label="Why this match is flagged anomalous">'
        '<div class="anomaly-head"><span>STATISTICAL ANOMALY</span>'
        '<span>WHY THIS MATCH IS FLAGGED · |Z| &gt; 2.3 VS TOURNAMENT AVG</span></div>'
        '<div class="anomaly-list">' + "".join(rows) + '</div>'
        '<div class="anomaly-foot">σ = STANDARD DEVIATIONS FROM THE TOURNAMENT TEAM-MATCH AVERAGE · '
        'SAME DETECTION AS THE MATCH CALENDAR ANOMALY BADGE</div>'
        '</section>'
    )


def safe_number(value: Any) -> str:
    if value is None or pd.isna(value):
        return "—"
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.1f}"


def render_comparison_stats(match: pd.Series, stats: pd.DataFrame) -> str:
    home, away = _team_stat_rows(match, stats)
    if home is None or away is None:
        return '<div class="match-empty-state">Head-to-head statistics are unavailable.</div>'
    specs = (
        ("POSSESSION", "possession_pct", "%"), ("TOTAL SHOTS", "total_shots", ""),
        ("SHOTS ON TARGET", "shots_on_target", ""), ("CORNER KICKS", "corners", ""),
        ("FOULS COMMITTED", "fouls", ""), ("OFFSIDES", "offsides", ""),
        ("GOALKEEPER SAVES", "saves", ""),
    )
    rows = []
    for label, column, unit in specs:
        home_value = float(home[column]) if pd.notna(home.get(column)) else 0
        away_value = float(away[column]) if pd.notna(away.get(column)) else 0
        total = max(home_value + away_value, 1)
        home_width = home_value / total * 100
        away_width = away_value / total * 100
        rows.append(
            '<div class="comparison-row">'
            f'<div class="comparison-values"><strong>{safe_number(home_value)}{unit}</strong>'
            f'<span>{label}</span><strong>{safe_number(away_value)}{unit}</strong></div>'
            '<div class="comparison-bars">'
            f'<i style="--bar:{home_width:.1f}%"></i><i style="--bar:{away_width:.1f}%"></i>'
            '</div></div>'
        )
    return (
        '<div class="comparison-head"><span>' + safe(match.get("Home_Team")).upper()
        + '</span><span>' + safe(match.get("Away_Team")).upper() + '</span></div>'
        '<div class="comparison-list">' + "".join(rows) + '</div>'
    )


def render_timeline(match: pd.Series, events: pd.DataFrame) -> str:
    if events.empty:
        return '<div class="match-empty-state">Timeline data unavailable for this match.</div>'
    home_id = str(match.get("Home_Team_ID"))
    items = ['<div class="timeline-boundary">0′</div>']
    for _, event in events.iterrows():
        side = "home" if str(event.get("team_id")) == home_id else "away"
        event_type = safe(event.get("event_type")).upper()
        kind = "goal" if "GOAL" in event_type else "red" if "RED" in event_type else "yellow" if "YELLOW" in event_type else "var" if "VAR" in event_type else "sub" if "SUB" in event_type else "assist" if "ASSIST" in event_type else "event"
        items.append(
            f'<div class="timeline-event {side} {kind}">'
            '<div class="timeline-copy">'
            f'<span>{safe(event.get("minute"))}′ / {event_type}</span>'
            f'<strong>{safe(event.get("player_name"), "PLAYER UNAVAILABLE")}</strong>'
            f'<small>{safe(event.get("team_name"))}</small></div>'
            f'<i aria-label="{event_type}"></i></div>'
        )
    items.append('<div class="timeline-boundary end">90′</div>')
    return '<div class="editorial-timeline">' + "".join(items) + '</div>'


def render_match_facts(match: pd.Series, stats: pd.DataFrame, players: pd.DataFrame) -> str:
    home_stats, _ = _team_stat_rows(match, stats)
    facts: list[tuple[str, str]] = [
        (score_value(match.get("Home_Score")) or "—", f'{safe(match.get("Home_Team")).upper()} GOALS'),
        (score_value(match.get("Away_Score")) or "—", f'{safe(match.get("Away_Team")).upper()} GOALS'),
    ]
    if home_stats is not None and pd.notna(home_stats.get("possession_pct")):
        facts.append((f'{safe_number(home_stats.get("possession_pct"))}%', f'{safe(match.get("Home_Team")).upper()} POSSESSION'))
    if pd.notna(match.get("Attendance")) and match.get("Attendance"):
        facts.append((f'{int(match["Attendance"]):,}', "ATTENDANCE"))
    if not players.empty:
        cards = players[["Yellow", "Red"]].fillna(0).sum().sum()
        facts.append((safe_number(cards), "TOTAL CARDS"))
    fact_html = "".join(
        f'<div class="programme-fact"><strong>{value}</strong><span>{label}</span></div>'
        for value, label in facts
    )
    return f'<div class="programme-facts">{fact_html}</div>'


def render_venue(match: pd.Series) -> str:
    capacity = match.get("Venue_Capacity")
    capacity_html = (
        f'<div><span>CAPACITY</span><strong>{int(capacity):,}</strong></div>'
        if pd.notna(capacity) and capacity else ""
    )
    return (
        '<div class="venue-programme">'
        f'<span>HOST VENUE / {safe(match.get("Country")).upper()}</span>'
        f'<h3>{safe(match.get("Stadium")).upper()}</h3>'
        f'<p>{safe(match.get("City")).upper()}</p>{capacity_html}</div>'
    )


def render_fixture_navigation(previous: pd.Series | None, following: pd.Series | None) -> str:
    def item(match: pd.Series | None, direction: str) -> str:
        if match is None:
            return '<div class="fixture-nav-item is-empty"></div>'
        arrow = "←" if direction == "PREVIOUS MATCH" else "→"
        if is_completed(match):
            matchup = (
                f'{safe(match.get("Home_Team")).upper()} '
                f'{score_value(match.get("Home_Score"))} — '
                f'{score_value(match.get("Away_Score"))} '
                f'{safe(match.get("Away_Team")).upper()}'
            )
        else:
            matchup = (
                f'{safe(match.get("Home_Team")).upper()} VS '
                f'{safe(match.get("Away_Team")).upper()}'
            )
        return (
            f'<a class="fixture-nav-item" href="{detail_url(match["ID"])}" target="_self">'
            f'<span>{arrow} {direction}</span><small>MATCH {int(match["ID"]):02d}</small>'
            f'<strong>{matchup}</strong></a>'
        )
    return '<div class="fixture-navigation">' + item(previous, "PREVIOUS MATCH") + item(following, "NEXT MATCH") + '</div>'
