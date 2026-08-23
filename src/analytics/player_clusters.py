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

        # ---- dien giai ten cum theo centroid z-score (spec 3.1) ----
        pop_mean = sub[feats].mean()
        pop_std = sub[feats].std().replace(0, 1)
        GROUPS = {
            "Finisher / Goal Scorer": ["goals_p90", "shots_on_target_p90", "shots_p90"],
            "Playmaker / Chance Creator": ["assists_p90", "crosses_p90",
                                           "dribbles_attempted_p90"],
            "Ball Progressor": ["passes_p90", "accurate_passes_p90"],
            "Defensive Player": ["tackles_p90", "interceptions_p90",
                                 "clearances_p90", "blocks_p90"],
        }
        labels = {}
        for c in range(k):
            cent = profile.loc[c]
            z = {f: (cent.get(f, 0) - pop_mean.get(f, 0)) / pop_std.get(f, 1)
                 for f in feats}
            gscores = {g: sum(z.get(f, 0) for f in flist) / len(flist)
                       for g, flist in GROUPS.items()}
            best_g = max(gscores, key=gscores.get)
            if max(gscores.values()) < 0.25:
                best_g = "Box-to-Box / All-rounder"
            labels[c] = best_g
            print(f"  Cum {c}: {best_g}")
        sub["cluster_label"] = sub["cluster"].map(labels)
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
            # z-score tung chieu de so sanh dung thang do
            zg = pd.DataFrame(Xg, columns=gcols)
            zg["cluster"] = kmg.labels_
            cent_z = zg.groupby("cluster")[gcols].mean()
            prof = gk.groupby("cluster")[gcols].mean().round(2)
            prof.to_csv(f"{OUT}/cluster_profile_gk.csv")
            glbl = {}
            for c in range(kg):
                glbl[c] = ("Shot Stopper"
                           if cent_z.loc[c, "saves_p90"] >= cent_z.loc[c, "save_pct"]
                           else "Safe Hands")
            gk["cluster_label"] = gk["cluster"].map(glbl)
            print(f"GK: {len(gk)} players -> {kg} cum | {glbl}")
            out_parts.append(gk.assign(position="GK"))

    result = pd.concat(out_parts)
    result.to_csv(f"{OUT}/player_clusters.csv", index=False)
    print("saved:", f"{OUT}/player_clusters.csv")


if __name__ == "__main__":
    main()
