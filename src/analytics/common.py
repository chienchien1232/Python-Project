# -*- coding: utf-8 -*-
"""Common helpers cho analytics suite (3.1-3.7)."""
import csv

PMS = "data/processed/wc2026_player_match/player_match_stats.csv"
GK = "data/processed/wc2026_player_match/goalkeeper_match_stats.csv"

# Cot hanh dong dung de tinh per-90 (tren pms)
ACTION_COLS = [
    "goals", "assists", "shots", "shots_on_target", "passes", "accurate_passes",
    "crosses", "tackles", "interceptions", "clearances", "blocks", "recoveries",
    "duels_won", "aerial_duels_won", "dribbles_attempted",
    "fouls_committed", "fouls_won", "offsides",
]


def load_pms():
    """Doc player_match_stats.csv tra ve list dict."""
    with open(PMS, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_gk():
    """Doc goalkeeper_match_stats.csv tra ve list dict."""
    with open(GK, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def played(row):
    """True neu dong la lan ra san that (minutes_played > 0)."""
    return row["minutes_played"] != "" and int(row["minutes_played"]) > 0


def to_int(v):
    v = str(v).strip()
    return int(v) if v else 0
