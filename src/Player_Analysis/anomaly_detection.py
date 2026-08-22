from __future__ import annotations
import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

try:
    from ml_data import (
        add_per90_features,
        add_position_group,
        ensure_result_dir,
        load_player_data,
        numeric_fill_by_group,
    )
    from .player_clustering import POSITION_FEATURES, BASE_FEATURES
except ImportError:
    from ml_data import (
        add_per90_features,
        add_position_group,
        ensure_result_dir,
        load_player_data,
        numeric_fill_by_group,
    )
    from .player_clustering import POSITION_FEATURES, BASE_FEATURES


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
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


def detect_player_anomalies(
    df: pd.DataFrame | None = None,
    contamination: str | float = "auto",
    random_state: int = 42,
) -> pd.DataFrame:
    if df is None:
        df = load_player_data()

    df = prepare_features(df)
    outputs = []

    for position, group in df.groupby("position_group", sort=True):
        features = POSITION_FEATURES.get(position, BASE_FEATURES)
        features = [c for c in features if c in group.columns]

        if len(group) < 5 or not features:
            tmp = group[["player_id", "player_name", "team_id", "position", "position_group"]].copy()
            tmp["anomaly_score"] = 0.0
            tmp["is_anomaly"] = False
            outputs.append(tmp)
            continue

        work = numeric_fill_by_group(group, features)
        X = work[features].to_numpy(dtype=float)
        X_scaled = StandardScaler().fit_transform(X)

        model = IsolationForest(
            n_estimators=300,
            contamination=contamination,
            random_state=random_state,
        )
        labels = model.fit_predict(X_scaled)
        raw_score = model.score_samples(X_scaled)

        # Higher score = more unusual for easier interpretation.
        anomaly_score = -raw_score

        tmp = work[["player_id", "player_name", "team_id", "position", "position_group"]].copy()
        tmp["anomaly_score"] = anomaly_score
        tmp["is_anomaly"] = labels == -1
        outputs.append(tmp)

    return pd.concat(outputs, ignore_index=True).sort_values(
        "anomaly_score", ascending=False
    ).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phát hiện cầu thủ bất thường bằng Isolation Forest.")
    parser.add_argument("--contamination", default="auto")
    args = parser.parse_args()

    contamination: str | float
    try:
        contamination = float(args.contamination)
    except ValueError:
        contamination = args.contamination

    output = detect_player_anomalies(contamination=contamination)
    path = ensure_result_dir() / "player_anomalies.csv"
    output.to_csv(path, index=False)
    print(f"Saved: {path}")
    print(f"Anomalies: {int(output['is_anomaly'].sum())}/{len(output)}")


if __name__ == "__main__":
    main()
