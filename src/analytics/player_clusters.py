# -*- coding: utf-8 -*-
"""3.1 Player Clustering - KMeans theo vai tro (GK tach rieng)."""
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, davies_bouldin_score,
                             silhouette_score)
from sklearn.preprocessing import StandardScaler

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90


def best_k(X, kmin=4, kmax=8, tag="outfield"):
    """Chon k theo silhouette, kem Davies-Bouldin + on dinh ARI de bao ve.

    Tra ve (best_k, bang tuning). On dinh = ARI trung binh cua 3 seed
    phu (1, 2, 3) so voi seed chinh 42. DB thap la tot.
    """
    rows = []
    best, best_s = kmin, -1
    for k in range(kmin, kmax + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        s = silhouette_score(X, km.labels_)
        db = davies_bouldin_score(X, km.labels_)
        aris = [adjusted_rand_score(
            km.labels_,
            KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(X))
            for seed in (1, 2, 3)]
        stab = round(float(np.mean(aris)), 3)
        rows.append({"group": tag, "k": k, "silhouette": round(float(s), 3),
                     "davies_bouldin": round(float(db), 3),
                     "stability_ARI": stab})
        print(f"  k={k} silhouette={s:.3f} DB={db:.3f} ARI_stab={stab:.3f}")
        if s > best_s:
            best, best_s = k, s
    print(f"  -> chon k={best}")
    return best, rows


def main():
    """KMeans outfield (k chon theo silhouette, co DB + ARI) + GK rieng.

    Ghi player_clusters.csv, cluster_profile_outfield/gk.csv, cluster_tuning.csv.
    """
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    # FEATS_BASE: 18 cot p90 goc (giu schema profile cho UI).
    # FEATS_MODEL: ban shrunk neu co (chong nhieu mau 90'), fallback ve goc.
    feats = [c for c in df.columns if c not in DROP and not c.startswith("total_")
             and not c.endswith("_shrunk")]
    feats_model = [c + "_shrunk" if c + "_shrunk" in df.columns else c for c in feats]

    out_parts = []
    tuning_rows = []
    # ---- OUTFIELD tu player_features ----
    sub = df[df["position"].isin(["DEF", "MID", "FWD"])].copy()
    if not sub.empty:
        X = StandardScaler().fit_transform(sub[feats_model].fillna(0))
        k, tune = best_k(X, 4, 8, tag="outfield")
        tuning_rows += tune
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sub["cluster"] = km.labels_
        # Profile hien thi giu cot goc; centroid model (shrunk) dung de dat ten.
        profile_model = sub.groupby("cluster")[feats_model].mean().round(2)

        # ---- dien giai ten cum theo centroid z-score (spec 3.1) ----
        pop_mean = sub[feats_model].mean()
        pop_std = sub[feats_model].std().replace(0, 1)
        GROUPS = {
            "Finisher / Goal Scorer": ["goals_p90_shrunk", "shots_on_target_p90_shrunk", "shots_p90_shrunk"],
            "Playmaker / Chance Creator": ["assists_p90_shrunk", "crosses_p90_shrunk",
                                           "dribbles_attempted_p90_shrunk"],
            "Ball Progressor": ["passes_p90_shrunk", "accurate_passes_p90_shrunk"],
            "Defensive Player": ["tackles_p90_shrunk", "interceptions_p90_shrunk",
                                 "clearances_p90_shrunk", "blocks_p90_shrunk"],
        }
        # Fallback neu file cu chua co cot shrunk.
        GROUPS = {g: [f if f in feats_model else f.replace("_shrunk", "") for f in fl]
                  for g, fl in GROUPS.items()}
        labels = {}
        for c in range(k):
            cent = profile_model.loc[c]
            z = {f: (cent.get(f, 0) - pop_mean.get(f, 0)) / pop_std.get(f, 1)
                 for f in feats_model}
            gscores = {g: sum(z.get(f, 0) for f in flist) / len(flist)
                       for g, flist in GROUPS.items()}
            best_g = max(gscores, key=gscores.get)
            if max(gscores.values()) < 0.25:
                best_g = "Box-to-Box / All-rounder"
            labels[c] = best_g
            print(f"  Cum {c}: {best_g}")
        sub["cluster_label"] = sub["cluster"].map(labels)

        # ---- profile + so cau thu + dai dien (cho ML Explorer) ----
        profile = sub.groupby("cluster")[feats].mean().round(2)
        profile["cluster_label"] = profile.index.map(labels)
        profile["n_players"] = sub.groupby("cluster").size()
        profile["top_players"] = (
            sub.sort_values("minutes", ascending=False)
            .groupby("cluster")["player_name"]
            .apply(lambda s: "; ".join(s.head(3)))
        )
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
            kg, tune_gk = best_k(Xg, 2, 5, tag="gk")
            tuning_rows += tune_gk
            kmg = KMeans(n_clusters=kg, n_init=10, random_state=42).fit(Xg)
            gk["cluster"] = kmg.labels_
            gk["position"] = "GK"
            # z-score tung chieu de so sanh dung thang do
            zg = pd.DataFrame(Xg, columns=gcols)
            zg["cluster"] = kmg.labels_
            cent_z = zg.groupby("cluster")[gcols].mean()
            glbl = {}
            for c in range(kg):
                z_saves = float(cent_z.loc[c, "saves_p90"])
                z_pct = float(cent_z.loc[c, "save_pct"])
                if z_saves >= 0 and z_saves >= z_pct:
                    glbl[c] = "Shot Stopper"      # cuu nhieu cu phut (tai trong lon)
                elif z_pct >= 0:
                    glbl[c] = "Safe Hands"        # hieu suat cuu cao
                else:
                    glbl[c] = "Backup / Limited Minutes"  # ca 2 deu duoi TB
            prof = gk.groupby("cluster")[gcols].mean().round(2)
            prof["cluster_label"] = prof.index.map(glbl)
            prof["n_players"] = gk.groupby("cluster").size()
            prof["top_players"] = (
                gk.sort_values("minutes", ascending=False)
                .groupby("cluster")["player_name"]
                .apply(lambda s: "; ".join(s.head(3)))
            )
            prof.to_csv(f"{OUT}/cluster_profile_gk.csv")
            gk["cluster_label"] = gk["cluster"].map(glbl)
            print(f"GK: {len(gk)} players -> {kg} cum | {glbl}")
            out_parts.append(gk.assign(position="GK"))

    result = pd.concat(out_parts)
    # An toan: output bat buoc co ca cau thu ngoai san va GK
    n_gk = (result["position"] == "GK").sum()
    n_out = (result["position"] != "GK").sum()
    assert n_out > 0 and n_gk > 0, f"player_clusters.csv thieu thanh phan (out={n_out}, gk={n_gk})"
    result.to_csv(f"{OUT}/player_clusters.csv", index=False)
    pd.DataFrame(tuning_rows).to_csv(f"{OUT}/cluster_tuning.csv", index=False)
    print(f"saved: {OUT}/player_clusters.csv | outfield={n_out}, gk={n_gk}")
    print(f"saved: {OUT}/cluster_tuning.csv ({len(tuning_rows)} dong)")


if __name__ == "__main__":
    main()
