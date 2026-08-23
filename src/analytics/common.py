# -*- coding: utf-8 -*-
"""Common helpers cho analytics suite (3.1-3.7)."""
import csv
import re
import unicodedata

PMS = "data/processed/wc2026_player_match/player_match_stats.csv"
GK = "data/processed/wc2026_player_match/goalkeeper_match_stats.csv"
TEAMS = "data/processed/csv/teams.csv"

# Cot hanh dong dung de tinh per-90 (tren pms)
ACTION_COLS = [
    "goals", "assists", "shots", "shots_on_target", "passes", "accurate_passes",
    "crosses", "tackles", "interceptions", "clearances", "blocks", "recoveries",
    "duels_won", "aerial_duels_won", "dribbles_attempted",
    "fouls_committed", "fouls_won", "offsides",
]


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_pms():
    with open(PMS, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_gk():
    with open(GK, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_teams():
    """Return list rows + dict team_id -> team_name."""
    with open(TEAMS, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
    return rows, {x["team_id"]: x["team_name"] for x in rows}


def played(row):
    """Dong co thuc su thi dau."""
    return row["minutes_played"] != "" and int(row["minutes_played"]) > 0


def to_int(v):
    v = str(v).strip()
    return int(v) if v else 0


def to_float(v):
    v = str(v).strip().rstrip("%")
    try:
        return float(v) if v else None
    except ValueError:
        return None
