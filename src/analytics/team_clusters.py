# -*- coding: utf-8 -*-
"""3.3 Team Style Analysis - phan tich phong cach choi cua cac doi tuyen.

Nang cap so voi ban cu:
- 12 chi so danh gia / doi (them fouls, offsides, sot_acc, conv)
- KMeans chon k tot nhat trong khoang 4..6 theo silhouette
- Gan phong cach TU DETERMINISTIC so 6 mau phong cach chuan qua centroid
  z-score (khong con if/elif cam tinh) + do tin cay softmax
- Xoa dead code (feat_cols, gf_pg/ga_pg khong dung)

Nguon : data/processed/csv/match_team_stats.csv + matches.csv + teams.csv
Dich  : data/processed/analytics/team_clusters.csv
        (giu nguyen cot team_name + cluster_label de UI 2_teams.py doc)
"""
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

MTS = "data/processed/csv/match_team_stats.csv"
MATCHES = "data/processed/csv/matches.csv"
TEAMS_CSV = "data/processed/csv/teams.csv"
OUT = "data/processed/analytics"

# Chi so dau vao mo hinh (per-match trung binh cua moi doi)
METRICS = ["possession", "shots", "sot", "corners", "fouls", "offsides",
           "saves", "gf", "ga", "gd", "sot_acc", "conv"]

# 6 mau phong cach chuan: trong so tren z-score cua tung chi so.
# Diem phong cach = tong (trong so x z).rong = gan trung binh moi mat.
STYLE_PROFILES = {
    "Possession Control":    {"possession": +1.0, "corners": +0.8, "fouls": -0.5, "saves": -0.4},
    "High Press Aggressive": {"fouls": +1.0, "offsides": +0.9, "shots": +0.7, "sot": +0.5},
    "Counter Attack":        {"possession": -0.9, "conv": +1.0, "sot_acc": +0.7, "corners": -0.5, "saves": +0.4},
    "Low Block Defensive":   {"saves": +1.0, "shots": -0.8, "gf": -0.7, "possession": -0.5},
    "Direct Attacking":      {"shots": +0.9, "sot": +0.9, "gf": +0.8, "corners": +0.6},
    "Balanced Adaptive":     {},  # diem = -mean(|z|) -> nhom gan trung binh nhat
}


def load_team_matches():
    """Ghep match_team_stats voi ti so -> bang tran-doi (team x match)."""
    mts = pd.read_csv(MTS, dtype={"team_id": str, "match_id": str})
    matches = pd.read_csv(MATCHES, dtype={"team_id": str, "match_id": str})
    m = mts.merge(matches[["match_id", "home_team_id", "away_team_id",
                           "home_score", "away_score"]],
                  on="match_id", how="left")
    is_home = m["team_id"] == m["home_team_id"]
    m["gf"] = np.where(is_home, m["home_score"], m["away_score"])
    m["ga"] = np.where(is_home, m["away_score"], m["home_score"])
    return m


def build_features(m):
    """12 chi so trung binh tran cua moi doi."""
    agg = m.groupby("team_id").agg(
        possession=("possession_pct", "mean"),
        shots=("total_shots", "mean"),
        sot=("shots_on_target", "mean"),
        corners=("corners", "mean"),
        fouls=("fouls", "mean"),
        offsides=("offsides", "mean"),
        saves=("saves", "mean"),
        gf=("gf", "mean"),
        ga=("ga", "mean"),
    )
    agg["gd"] = agg["gf"] - agg["ga"]
    agg["sot_acc"] = np.where(agg["shots"] > 0, agg["sot"] / agg["shots"], 0.0)
    agg["conv"] = np.where(agg["shots"] > 0, agg["gf"] / agg["shots"], 0.0)
    return agg[METRICS].astype(float).round(3)


def pick_best_k(X, k_min=4, k_max=6, save_path=None):
    """Chon k tot nhat theo silhouette (toi da 6 phong cach theo spec).

    Cung luu inertia (elbow) de doi chieu: voi n=48 doi, silhouette thuong
    thap (~0.15-0.2) vi phong cach choi la pho, khong roi rac ro rang -> nen
    trinh bay ca 2 duong cong trong bao cao thay vi chi 1 con so silhouette.
    """
    rows = []
    best_k, best_s, best_model = k_min, -1.0, None
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        s = silhouette_score(X, km.labels_)
        print(f"  k={k} silhouette={s:.3f} inertia={km.inertia_:.1f}")
        rows.append({"k": k, "silhouette": round(s, 4), "inertia": round(km.inertia_, 2)})
        if s > best_s:
            best_k, best_s, best_model = k, s, km
    if save_path:
        pd.DataFrame(rows).to_csv(save_path, index=False)
    return best_model, best_s


def style_scores(cent_z):
    """Ma tran diem (cluster x style) tu centroid z-score."""
    scores = {}
    for style, weights in STYLE_PROFILES.items():
        if weights:
            scores[style] = sum(cent_z[f] * w for f, w in weights.items())
        else:  # Balanced: nhom co cac chi so gan trung binh nhat
            scores[style] = -cent_z.abs().mean(axis=1)
    return pd.DataFrame(scores)


def assign_styles(scores):
    """Gan tham lam moi cluster 1 phong cach khac nhau (deterministic)."""
    pairs = [(scores.loc[c][s], c, s) for c in scores.index for s in scores.columns]
    pairs.sort(key=lambda t: t[0], reverse=True)
    label, used_c, used_s = {}, set(), set()
    for sc, c, s in pairs:
        if c in used_c or s in used_s:
            continue
        label[c] = s
        used_c.add(c)
        used_s.add(s)
        if len(label) == len(scores.index):
            break
    return label


def style_confidence(scores, label):
    """Do tin cay softmax (%) cua phong cach duoc gan cho moi cluster."""
    conf = {}
    for c in scores.index:
        vals = scores.loc[c].values.astype(float)
        e = np.exp(vals - vals.max())
        p = e / e.sum()
        conf[c] = round(float(p[list(scores.columns).index(label[c])]) * 100, 1)
    return conf


def main():
    m = load_team_matches()
    agg = build_features(m)

    X = StandardScaler().fit_transform(agg[METRICS])
    print("Chon so phong cach (k):")
    km, best_s = pick_best_k(X, save_path=f"{OUT}/cluster_k_selection_team.csv")
    agg["cluster"] = km.labels_

    # z-score centroid tung nhom -> gan phong cach chuan + do tin cay
    cent_z = pd.DataFrame(X, index=agg.index, columns=METRICS) \
        .groupby(agg["cluster"]).mean()
    scores = style_scores(cent_z)
    label = assign_styles(scores)
    conf = style_confidence(scores, label)

    agg["cluster_label"] = agg["cluster"].map(label)
    agg["style_confidence"] = agg["cluster"].map(conf)

    teams = pd.read_csv(TEAMS_CSV, dtype={"team_id": str})
    agg = agg.merge(teams[["team_id", "team_name"]], left_index=True,
                    right_on="team_id", how="left")

    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, "team_clusters.csv")
    agg.to_csv(out_path, index=False)

    # ---- bao cao kiem tra ----
    print(f"\n{len(agg)} doi -> {len(label)} phong cach "
          f"(silhouette={best_s:.3f}) | saved: {out_path}")
    for c in sorted(label):
        members = agg[agg["cluster"] == c]["team_name"].tolist()
        print(f"  [{label[c]}] conf={conf[c]}% ({len(members)} doi): "
              f"{', '.join(members[:6])}...")
    dup = agg["team_name"].duplicated().sum()
    assert dup == 0, "co team bi trung"
    assert agg["cluster_label"].notna().all(), "co team chua co phong cach"
    assert agg["cluster_label"].nunique() <= 6, "vuot 6 phong cach"
    print("\nCHECK: PASS")


if __name__ == "__main__":
    main()
