from __future__ import annotations

from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = PROJECT_ROOT / "data" / "processed" / "csv"
RESULT_DIR = PROJECT_ROOT / "data" / "processed" / "ml_results"


def load_csv(name: str) -> pd.DataFrame:
    path = CSV_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy dataset: {path}")
    return pd.read_csv(path)


def load_player_data() -> pd.DataFrame:
    stats = load_csv("player_stats.csv")
    squads = load_csv("squads_and_players.csv")

    # Avoid duplicated columns after merge.
    extra = squads.drop(columns=["player_name", "team_id", "position", "goals"], errors="ignore")
    df = stats.merge(extra, on="player_id", how="left")
    return df


def load_team_data() -> pd.DataFrame:
    match_stats = load_csv("match_team_stats.csv")
    teams = load_csv("teams.csv")
    return match_stats.merge(teams, on="team_id", how="left")


def ensure_result_dir() -> Path:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    return RESULT_DIR


def numeric_fill_by_group(
    df: pd.DataFrame,
    numeric_columns: Iterable[str],
    group_column: str = "position_group",
) -> pd.DataFrame:
    """Fill missing numeric values by position-group median, then global median, then 0."""
    out = df.copy()
    for col in numeric_columns:
        if col not in out.columns:
            continue

        out[col] = pd.to_numeric(out[col], errors="coerce")

        if group_column in out.columns:
            group_median = out.groupby(group_column)[col].transform("median")
            out[col] = out[col].fillna(group_median)

        out[col] = out[col].fillna(out[col].median()).fillna(0.0)

    return out


def normalize_position(value: object) -> str:
    if pd.isna(value):
        return "UNK"

    text = str(value).strip().upper()
    aliases = {
        "GOALKEEPER": "GK",
        "KEEPER": "GK",
        "GK": "GK",
        "DEFENDER": "DF",
        "DEF": "DF",
        "DF": "DF",
        "D": "DF",
        "MIDFIELDER": "MF",
        "MID": "MF",
        "MF": "MF",
        "M": "MF",
        "FORWARD": "FW",
        "FWD": "FW",
        "FW": "FW",
        "ATTACKER": "FW",
        "ST": "FW",
        "F": "FW",
    }

    if text in aliases:
        return aliases[text]

    # Handle strings such as "Left Back", "Central Midfielder", etc.
    if any(token in text for token in ("KEEP", "GOAL")):
        return "GK"
    if any(token in text for token in ("BACK", "DEFEN", "CENTER-BACK", "CENTRE-BACK")):
        return "DF"
    if "MID" in text:
        return "MF"
    if any(token in text for token in ("FORWARD", "STRIKER", "WINGER", "ATTACK")):
        return "FW"

    return "UNK"


def add_position_group(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["position_group"] = out["position"].map(normalize_position)
    return out


def add_per90_features(
    df: pd.DataFrame,
    count_columns: Iterable[str],
    minutes_column: str = "minutes_played",
) -> pd.DataFrame:
    out = df.copy()
    minutes = pd.to_numeric(out[minutes_column], errors="coerce").fillna(0.0)
    denominator = minutes.replace(0, np.nan)

    for col in count_columns:
        if col not in out.columns:
            continue
        values = pd.to_numeric(out[col], errors="coerce")
        out[f"{col}_per90"] = (values / denominator * 90.0).replace([np.inf, -np.inf], np.nan)

    return out
