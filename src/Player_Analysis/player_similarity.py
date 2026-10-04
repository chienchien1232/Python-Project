from __future__ import annotations
import os
import sys

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def compute_player_similarity(
    df: pd.DataFrame | None = None,
    top_k: int = 10,
    include_self: bool = False,
) -> pd.DataFrame:
    if df is None:
        df = load_player_data()

    df = prepare_features(df)
    all_rows = []

    for position, group in df.groupby("position_group", sort=True):
        features = POSITION_FEATURES.get(position, BASE_FEATURES)
        features = [c for c in features if c in group.columns]

        if len(group) < 2 or not features:
            continue

        work = numeric_fill_by_group(group, features)
        X = work[features].to_numpy(dtype=float)
        X_scaled = StandardScaler().fit_transform(X)

        sim = cosine_similarity(X_scaled)
        ids = work["player_id"].to_numpy()

        for i in range(len(work)):
            order = np.argsort(-sim[i])

            count = 0
            for j in order:
                if not include_self and i == j:
                    continue

                all_rows.append(
                    {
                        "player_id": ids[i],
                        "player_name": work.iloc[i]["player_name"],
                        "position_group": position,
                        "similar_player_id": ids[j],
                        "similar_player_name": work.iloc[j]["player_name"],
                        "similarity": float(sim[i, j]),
                    }
                )

                count += 1
                if count >= top_k:
                    break

    result = pd.DataFrame(all_rows)
    if not result.empty:
        result = result.sort_values(
            ["player_id", "similarity"],
            ascending=[True, False],
        ).reset_index(drop=True)

    return result


def find_similar_players(
    player_id: int,
    top_k: int = 10,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    result = compute_player_similarity(df=df, top_k=top_k)
    return result[result["player_id"] == player_id].copy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Tìm cầu thủ tương đồng bằng cosine similarity.")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    output = compute_player_similarity(top_k=args.top_k)
    path = ensure_result_dir() / "player_similarity.csv"
    output.to_csv(path, index=False)
    print(f"Saved: {path}")
    print(f"Rows: {len(output):,}")


if __name__ == "__main__":
    main()
