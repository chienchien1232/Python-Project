from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

try:
    from .ml_data import (
        add_per90_features,
        add_position_group,
        ensure_result_dir,
        load_player_data,
        numeric_fill_by_group,
    )
except ImportError:
    from ml_data import (
        add_per90_features,
        add_position_group,
        ensure_result_dir,
        load_player_data,
        numeric_fill_by_group,
    )


BASE_FEATURES = [
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "yellow_cards_per90",
    "red_cards_per90",
    "penalty_goals_per90",
    "own_goals_per90",
    "clean_sheets_per90",
    "saves_per90",
    "goals_conceded_per90",
    "average_rating",
    "matches_started",
]


POSITION_FEATURES = {
    "GK": [
        "saves_per90",
        "goals_conceded_per90",
        "clean_sheets_per90",
        "average_rating",
        "matches_started",
    ],
    "DF": [
        "goals_per90",
        "assists_per90",
        "shots_per90",
        "shots_on_target_per90",
        "yellow_cards_per90",
        "red_cards_per90",
        "clean_sheets_per90",
        "average_rating",
        "matches_started",
    ],
    "MF": [
        "goals_per90",
        "assists_per90",
        "shots_per90",
        "shots_on_target_per90",
        "yellow_cards_per90",
        "red_cards_per90",
        "average_rating",
        "matches_started",
    ],
    "FW": [
        "goals_per90",
        "assists_per90",
        "shots_per90",
        "shots_on_target_per90",
        "penalty_goals_per90",
        "own_goals_per90",
        "yellow_cards_per90",
        "average_rating",
        "matches_started",
    ],
}


def choose_k(X_scaled: np.ndarray, min_k: int = 2, max_k: int = 6) -> int:
    n = len(X_scaled)
    if n < 4:
        return 1

    upper = min(max_k, n - 1)
    scores = {}

    for k in range(min_k, upper + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(X_scaled)
        if len(np.unique(labels)) < 2:
            continue
        scores[k] = silhouette_score(X_scaled, labels)

    return max(scores, key=scores.get) if scores else min(min_k, n)


def prepare_player_features(df: pd.DataFrame) -> pd.DataFrame:
    out = add_position_group(df)
    out = add_per90_features(
        out,
        [
            "goals",
            "assists",
            "shots",
            "shots_on_target",
            "yellow_cards",
            "red_cards",
            "penalty_goals",
            "own_goals",
            "clean_sheets",
            "saves",
            "goals_conceded",
        ],
    )
    return out


def cluster_players(
    df: pd.DataFrame | None = None,
    min_k: int = 2,
    max_k: int = 6,
) -> pd.DataFrame:
    if df is None:
        df = load_player_data()

    df = prepare_player_features(df)
    result = []

    for position, group in df.groupby("position_group", sort=True):
        features = POSITION_FEATURES.get(position, BASE_FEATURES)
        features = [c for c in features if c in group.columns]

        if len(group) < 2 or not features:
            tmp = group[["player_id", "player_name", "team_id", "position", "position_group"]].copy()
            tmp["cluster"] = 0
            tmp["n_clusters"] = 1
            tmp["silhouette_score"] = np.nan
            result.append(tmp)
            continue

        work = numeric_fill_by_group(group, features)
        X = work[features].to_numpy(dtype=float)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        k = choose_k(X_scaled, min_k=min_k, max_k=max_k)

        if k == 1:
            labels = np.zeros(len(work), dtype=int)
            score = np.nan
        else:
            model = KMeans(n_clusters=k, random_state=42, n_init=20)
            labels = model.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels) if len(np.unique(labels)) > 1 else np.nan

        tmp = work[["player_id", "player_name", "team_id", "position", "position_group"]].copy()
        tmp["cluster"] = labels
        tmp["n_clusters"] = k
        tmp["silhouette_score"] = score
        result.append(tmp)

    return pd.concat(result, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster cầu thủ theo profile thống kê.")
    parser.add_argument("--min-k", type=int, default=2)
    parser.add_argument("--max-k", type=int, default=6)
    args = parser.parse_args()

    output = cluster_players(min_k=args.min_k, max_k=args.max_k)
    path = ensure_result_dir() / "player_clusters.csv"
    output.to_csv(path, index=False)
    print(f"Saved: {path}")
    print(output.groupby(["position_group", "cluster"]).size())


if __name__ == "__main__":
    main()
