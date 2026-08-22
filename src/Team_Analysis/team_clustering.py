from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

try:
    from .ml_data import ensure_result_dir, load_team_data, numeric_fill_by_group
except ImportError:
    from ml_data import ensure_result_dir, load_team_data, numeric_fill_by_group


MATCH_FEATURES = [
    "possession_pct",
    "total_shots",
    "shots_on_target",
    "corners",
    "fouls",
    "offsides",
    "saves",
]


def choose_k(X_scaled: np.ndarray, min_k: int = 2, max_k: int = 8) -> int:
    n = len(X_scaled)
    if n < 4:
        return 1

    upper = min(max_k, n - 1)
    scores = {}

    for k in range(min_k, upper + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(X_scaled)
        if len(np.unique(labels)) >= 2:
            scores[k] = silhouette_score(X_scaled, labels)

    return max(scores, key=scores.get) if scores else min(min_k, n)


def build_team_features(df: pd.DataFrame) -> pd.DataFrame:
    match_features = [c for c in MATCH_FEATURES if c in df.columns]

    agg = (
        df.groupby("team_id", as_index=False)[match_features]
        .mean()
        .rename(columns={c: f"avg_{c}" for c in match_features})
    )

    counts = (
        df.groupby("team_id", as_index=False)
        .size()
        .rename(columns={"size": "matches_observed"})
    )

    metadata_cols = [
        "team_id",
        "team_name",
        "fifa_code",
        "group_letter",
        "confederation",
        "fifa_ranking_pre_tournament",
        "elo_rating",
        "manager_name",
    ]
    metadata_cols = [c for c in metadata_cols if c in df.columns]
    meta = df[metadata_cols].drop_duplicates("team_id")

    out = meta.merge(agg, on="team_id", how="left").merge(counts, on="team_id", how="left")

    if "fifa_ranking_pre_tournament" in out.columns:
        out["fifa_ranking_pre_tournament"] = pd.to_numeric(
            out["fifa_ranking_pre_tournament"], errors="coerce"
        )
    if "elo_rating" in out.columns:
        out["elo_rating"] = pd.to_numeric(out["elo_rating"], errors="coerce")

    return out


def cluster_teams(
    df: pd.DataFrame | None = None,
    min_k: int = 2,
    max_k: int = 8,
) -> pd.DataFrame:
    if df is None:
        df = load_team_data()

    features_df = build_team_features(df)

    feature_cols = [
        c for c in features_df.columns
        if c.startswith("avg_") or c in {"fifa_ranking_pre_tournament", "elo_rating"}
    ]

    work = numeric_fill_by_group(
        features_df,
        feature_cols,
        group_column="confederation",
    )

    X = work[feature_cols].to_numpy(dtype=float)
    X_scaled = StandardScaler().fit_transform(X)

    k = choose_k(X_scaled, min_k=min_k, max_k=max_k)

    if k == 1:
        labels = np.zeros(len(work), dtype=int)
        score = np.nan
    else:
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)

    output = work.copy()
    output["cluster"] = labels
    output["n_clusters"] = k
    output["silhouette_score"] = score
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster các đội tuyển theo lối chơi/thống kê.")
    parser.add_argument("--min-k", type=int, default=2)
    parser.add_argument("--max-k", type=int, default=8)
    args = parser.parse_args()

    output = cluster_teams(min_k=args.min_k, max_k=args.max_k)
    path = ensure_result_dir() / "team_clusters.csv"
    output.to_csv(path, index=False)
    print(f"Saved: {path}")
    print(output.groupby("cluster").size())


if __name__ == "__main__":
    main()
