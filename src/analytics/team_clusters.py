# -*- coding: utf-8 -*-
"""3.3 Team Clustering - phong cach doi tuyen."""
import os

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

MTS = "data/processed/csv/match_team_stats.csv"
TEAMS_CSV = "data/processed/csv/teams.csv"
OUT = "data/processed/analytics"


def main():
    mts = pd.read_csv(MTS, dtype={"team_id": str})
    teams = pd.read_csv(TEAMS_CSV, dtype={"team_id": str})
    mts = mts.merge(teams[["team_id", "team_name"]], left_on="team_id",
                    right_on="team_id", how="left")

    stat_cols = ["possession_pct", "total_shots", "shots_on_target",
                 "corners", "fouls", "offsides"]
    agg = mts.groupby("team_name")[stat_cols].mean().round(2)

    X = StandardScaler().fit_transform(agg)
    best_k, best_s = 3, -1
    for k in range(3, 7):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        from sklearn.metrics import silhouette_score
        s = silhouette_score(X, km.labels_)
        print(f"  k={k} silhouette={s:.3f}")
        if s > best_s:
            best_k, best_s = k, s
    km = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(X)
    agg["cluster"] = km.labels_

    agg.sort_values(["cluster", "possession_pct"], ascending=[True, False])
    agg.to_csv(f"{OUT}/team_clusters.csv")
    print(f"\n48 doi -> {best_k} nhom phong cach | saved: {OUT}/team_clusters.csv")
    for c in sorted(agg["cluster"].unique()):
        members = agg[agg["cluster"] == c].index.tolist()
        print(f"  Cluster {c} ({len(members)}): {', '.join(members[:8])}...")


if __name__ == "__main__":
    main()
