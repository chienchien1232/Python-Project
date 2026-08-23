# -*- coding: utf-8 -*-
"""3.1 Player Clustering - KMeans theo vai tro (GK tach rieng)."""
import os

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90


def best_k(X, kmin=4, kmax=8):
    best, best_s = kmin, -1
    for k in range(kmin, kmax + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        s = silhouette_score(X, km.labels_)
        print(f"  k={k} silhouette={s:.3f}")
        if s > best_s:
            best, best_s = k, s
    print(f"  -> chon k={best}")
    return best


def main():
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    feats = [c for c in df.columns if c not in DROP and not c.startswith("total_")]

    out_parts = []
    # ---- OUTFIELD tu player_features ----
    sub = df[df["position"].isin(["DEF", "MID", "FWD"])].copy()
    if not sub.empty:
        X = StandardScaler().fit_transform(sub[feats].fillna(0))
        k = best_k(X, 4, 8)
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sub["cluster"] = km.labels_
        profile = sub.groupby("cluster")[feats].mean().round(2)
        profile.to_csv(f"{OUT}/cluster_profile_outfield.csv")
        print(f"OUTFIELD: {len(sub)} players -> {k} cum | profile saved")
        out_parts.append(sub)

    # ---- GK rieng tu gk_features ----
    gk_path = f"{OUT}/gk_features.csv"
    if os.path.exists(gk_path):
        gk = pd.read_csv(gk_path)
        gk = gk[gk["minutes"] >= MIN_MIN].copy()
        gcols = ["save_pct", "saves_p90"]
        if len(gk) >= 3:
            Xg = StandardScaler().fit_transform(gk[gcols].fillna(0))
            kg = best_k(Xg, 2, 5)
            kmg = KMeans(n_clusters=kg, n_init=10, random_state=42).fit(Xg)
            gk["cluster"] = kmg.labels_
            gk["position"] = "GK"
            gk.groupby("cluster")[gcols].mean().round(2)\
              .to_csv(f"{OUT}/cluster_profile_gk.csv")
            print(f"GK: {len(gk)} players -> {kg} cum")
            out_parts.append(gk)

    result = pd.concat(out_parts)
    result.to_csv(f"{OUT}/player_clusters.csv", index=False)
    print("saved:", f"{OUT}/player_clusters.csv")


if __name__ == "__main__":
    main()
