"""Cached data access and formatting helpers for the match experience."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd
import streamlit as st

from helpers import q


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


def clean_name(value: Any) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    text = str(value)
    return (
        text.replace("Adrin", "Adrian")
        .replace("Andrs", "Andres")
        .replace("Damin", "Damian")
        .replace("Curaao", "Curacao")
        .replace("Cte d'Ivoire", "Côte d'Ivoire")
        .replace("Trkiye", "Türkiye")
        .replace("Lionel Andrs Messi", "Lionel Messi")
        .replace("Rodrigo Rodri", "Rodri")
        .replace("Kylian Mbappe", "Kylian Mbappé")
    )


def team_code(team_name: Any, fifa_code: Any = None) -> str:
    if fifa_code is not None and not pd.isna(fifa_code) and str(fifa_code).strip():
        return str(fifa_code).strip().upper()
    return FLAGS.get(clean_name(team_name), "—")


def minute_sort_key(value: Any) -> tuple[int, int]:
    """Sort regulation and stoppage-time values such as 45+2 chronologically."""
    numbers = [int(number) for number in re.findall(r"\d+", str(value))]
    if not numbers:
        return (10_000, 0)
    return (numbers[0], numbers[1] if len(numbers) > 1 else 0)


@st.cache_data(ttl=300, show_spinner=False)
def get_matches() -> pd.DataFrame:
    matches = q(
        """
        SELECT m.match_id AS ID,
               d.date AS Date,
               d.kickoff_time_utc AS Kickoff,
               d.stage_name AS Stage,
               d.home_team_name AS Home_Team,
               d.home_fifa_code AS Home_Code,
               d.home_score AS Home_Score,
               d.away_score AS Away_Score,
               d.away_team_name AS Away_Team,
               d.away_fifa_code AS Away_Code,
               COALESCE(m.status, d.status) AS Status,
               COALESCE(m.result_type, d.result_type) AS Result_Type,
               m.attendance AS Attendance,
               m.home_team_id AS Home_Team_ID,
               m.away_team_id AS Away_Team_ID,
               th.manager_name AS Home_Manager,
               ta.manager_name AS Away_Manager,
               d.stadium_name AS Stadium,
               d.city AS City,
               d.country AS Country,
               v.capacity AS Venue_Capacity,
               d.player_of_the_match_name AS MOTM,
               d.referee_name AS Referee
        FROM matches_detailed d
        JOIN matches m ON m.match_id = d.match_id
        LEFT JOIN teams th ON th.team_id = m.home_team_id
        LEFT JOIN teams ta ON ta.team_id = m.away_team_id
        LEFT JOIN venues v ON v.venue_id = m.venue_id
        ORDER BY d.date, m.match_id
        """
    )
    if matches.empty:
        return matches
    matches["Home_Team"] = matches["Home_Team"].map(clean_name)
    matches["Away_Team"] = matches["Away_Team"].map(clean_name)
    matches["MOTM"] = matches["MOTM"].map(clean_name)
    matches["Home_Manager"] = matches["Home_Manager"].map(clean_name)
    matches["Away_Manager"] = matches["Away_Manager"].map(clean_name)
    return matches


@st.cache_data(ttl=300, show_spinner=False)
def get_anomaly_ids() -> set[int]:
    stats = q("SELECT match_id, possession_pct, total_shots FROM match_team_stats")
    if stats.empty:
        return set()
    deviation = (stats["possession_pct"] - stats["possession_pct"].mean()) / max(
        stats["possession_pct"].std(), 1e-9
    )
    return {int(value) for value in stats.loc[deviation.abs() > 2.3, "match_id"]}


ANOMALY_METRICS: tuple[tuple[str, str, str], ...] = (
    ("possession_pct", "POSSESSION", "%"),
    ("total_shots", "TOTAL SHOTS", ""),
    ("shots_on_target", "SHOTS ON TARGET", ""),
    ("corners", "CORNERS", ""),
    ("saves", "SAVES", ""),
    ("fouls", "FOULS", ""),
)


@st.cache_data(ttl=300, show_spinner=False)
def get_match_anomaly_details(match_id: int) -> pd.DataFrame:
    """Explain WHY a flagged match is anomalous: per-team metric z-scores.

    Uses the same |Z| > 2.3 rule as :func:`get_anomaly_ids` so the Matches
    page badge and the detail-page reason always agree.
    """
    stats = q(
        "SELECT x.match_id, x.team_id, t.team_name, x.possession_pct, "
        "x.total_shots, x.shots_on_target, x.corners, x.saves, x.fouls "
        "FROM match_team_stats x "
        "LEFT JOIN teams t ON t.team_id = x.team_id"
    )
    if stats.empty:
        return stats
    rows = []
    for column, label, unit in ANOMALY_METRICS:
        series = stats[column].fillna(0)
        std = max(series.std(), 1e-9)
        deviation = (series - series.mean()) / std
        flagged = stats.loc[deviation.abs() > 2.3].copy()
        for _, row in flagged.iterrows():
            if str(row["match_id"]) != str(match_id):
                continue
            rows.append({
                "team_name": clean_name(row["team_name"]),
                "metric": label,
                "value": float(row[column]) if pd.notna(row[column]) else 0.0,
                "average": float(series.mean()),
                "z": float(deviation.loc[row.name]),
                "unit": unit,
            })
    details = pd.DataFrame(rows, columns=["team_name", "metric", "value", "average", "z", "unit"])
    if not details.empty:
        details = details.sort_values("z", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)
    return details


def get_match(match_id: int) -> pd.Series | None:
    matches = get_matches()
    selected = matches[matches["ID"].astype(str) == str(match_id)]
    return None if selected.empty else selected.iloc[0]


@st.cache_data(ttl=300, show_spinner=False)
def get_match_events(match_id: int) -> pd.DataFrame:
    events = q(
        """
        SELECT e.event_id, e.minute, e.event_type, e.team_id,
               p.player_name, t.team_name
        FROM match_events e
        LEFT JOIN players p ON CAST(p.player_id AS TEXT) = CAST(e.player_id AS TEXT)
        LEFT JOIN teams t ON CAST(t.team_id AS TEXT) = CAST(e.team_id AS TEXT)
        WHERE CAST(e.match_id AS TEXT) = ?
        """,
        (str(match_id),),
    )
    if events.empty:
        return events
    events["player_name"] = events["player_name"].map(clean_name)
    events["team_name"] = events["team_name"].map(clean_name)
    events["_minute_key"] = events["minute"].map(minute_sort_key)
    return events.sort_values(["_minute_key", "event_id"]).drop(columns="_minute_key")


@st.cache_data(ttl=300, show_spinner=False)
def get_match_stats(match_id: int) -> pd.DataFrame:
    return q(
        """
        SELECT team_id, possession_pct, total_shots, shots_on_target,
               corners, fouls, offsides, saves
        FROM match_team_stats
        WHERE CAST(match_id AS TEXT) = ?
        """,
        (str(match_id),),
    )


@st.cache_data(ttl=300, show_spinner=False)
def get_match_lineups(match_id: int) -> pd.DataFrame:
    lineups = q(
        """
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
        """,
        (str(match_id),),
    )
    if not lineups.empty:
        lineups["player_name"] = lineups["player_name"].map(clean_name)
        lineups["team_name"] = lineups["team_name"].map(clean_name)
    return lineups


@st.cache_data(ttl=300, show_spinner=False)
def get_player_match_stats(match_id: int) -> pd.DataFrame:
    players = q(
        """
        SELECT player_team AS Team, shirt_number AS No,
               player_name AS Player, position AS Pos,
               minutes_played AS Mins, goals AS Goals, assists AS Assists,
               shots AS Shots, passes AS Passes, accurate_passes AS Acc_Passes,
               tackles AS Tackles, interceptions AS Interceptions,
               clearances AS Clearances, fouls_committed AS Fouls,
               yellow_cards AS Yellow, red_cards AS Red
        FROM player_match_stats
        WHERE CAST(match_id AS TEXT) = ?
        ORDER BY Team, minutes_played DESC, Goals DESC, Assists DESC
        """,
        (str(match_id),),
    )
    if not players.empty:
        players["Player"] = players["Player"].map(clean_name)
        players["Team"] = players["Team"].map(clean_name)
    return players
