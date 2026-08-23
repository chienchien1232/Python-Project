# -*- coding: utf-8 -*-
"""3.3 Team Clustering - phong cach doi tuyen (co dien giai ten nhom)."""
import os

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

MTS = "data/processed/csv/match_team_stats.csv"
MATCHES = "data/processed/csv/matches.csv"
TEAMS_CSV = "data/processed/csv/teams.csv"
OUT = "data/processed/analytics"


def main():
    mts = pd.read_csv(MTS, dtype={"team_id": str, "match_id": str})
    matches = pd.read_csv(MATCHES, dtype={"team_id": str, "match_id": str})
    teams = pd.read_csv(TEAMS_CSV, dtype={"team_id": str})

    # goals for / against tung dong (team x match)
    def gf(row):
        return row["home_score"] if row["team_id"] == row["home_team_id"] \
            else row["away_score"]

    def ga(row):
        return row["away_score"] if row["team_id"] == row["home_team_id"] \
            else row["home_score"]

    m = mts.merge(matches[["match_id", "home_team_id", "away_team_id",
                           "home_score", "away_score"]],
                  on="match_id", how="left")
    m["gf"] = m.apply(gf, axis=1)
    m["ga"] = m.apply(ga, axis=1)

    feat_cols = ["possession_pct", "total_shots", "shots_on_target",
                 "corners", "saves", "gf_pg", "ga_pg"]
    m["gf_pg"] = 0.0
    m["ga_pg"] = 0.0

    agg = m.groupby("team_id").agg(
        possession=("possession_pct", "mean"),
        shots=("total_shots", "mean"),
        sot=("shots_on_target", "mean"),
        corners=("corners", "mean"),
        saves=("saves", "mean"),
        gf=("gf", "mean"),
        ga=("ga", "mean"),
    ).round(2)
    agg["gd"] = (agg["gf"] - agg["ga"]).round(2)

    num_cols = ["possession", "shots", "sot", "corners", "saves", "gf", "ga", "gd"]
    X = StandardScaler().fit_transform(agg[num_cols])
    best_k, best_s = 3, -1
    for k in range(3, 7):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        s = silhouette_score(X, km.labels_)
        print(f"  k={k} silhouette={s:.3f}")
        if s > best_s:
            best_k, best_s = k, s
    km = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(X)
    agg["cluster"] = km.labels_

    # ---- dien giai ten nhom theo centroid z-score (spec 3.3) ----
    zdf = pd.DataFrame(X, index=agg.index, columns=num_cols)
    cent_z = zdf.groupby(agg["cluster"]).mean()
    names = {}
    for c in sorted(cent_z.index):
        row = cent_z.loc[c]
        if row["gf"] >= 0.4 and row["gf"] >= max(row.get("ga", 0), 0) + 0.2:
            nm = "Attacking Teams"
        elif row["possession"] >= 0.4:
            nm = "Possession / Passing Teams"
        elif row["ga"] <= -0.4:
            nm = "Defensive Teams"
        else:
            nm = "Balanced Teams"
        names[c] = nm
    agg["cluster_label"] = agg["cluster"].map(names)

    agg = agg.merge(teams[["team_id", "team_name"]], left_index=True,
                    right_on="team_id", how="left")
    agg.to_csv(f"{OUT}/team_clusters.csv", index=False)

    print(f"\n48 doi -> {best_k} nhom phong cach | saved: {OUT}/team_clusters.csv")
    for c in sorted(names):
        members = agg[agg["cluster"] == c]["team_name"].tolist()
        print(f"  Cluster {c} [{names[c]}] ({len(members)}): "
              f"{', '.join(members[:8])}...")


if __name__ == "__main__":
    main()
