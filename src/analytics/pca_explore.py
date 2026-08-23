# -*- coding: utf-8 -*-
"""3.5 PCA - giam chieu & kham pha du lieu cau thu."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90


def main():
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    feats = [c for c in df.columns if c not in DROP and not c.startswith("total_")]
    X = StandardScaler().fit_transform(df[feats].fillna(0))

    pca = PCA(n_components=0.9)
    pcs = pca.fit_transform(X)
    for i, pc in enumerate(pcs.T[:4], 1):
        df[f"PC{i}"] = pc

    ev = pca.explained_variance_ratio_ * 100
    print("Explained variance (%):", [round(x, 1) for x in ev])
    print(f"Tong {len(ev)} thanh phan giai thich >=90% phuong sai")

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = {"GK": "gold", "DEF": "tab:blue", "MID": "tab:green", "FWD": "tab:red"}
    for pos, c in colors.items():
        m = df["position"] == pos
        ax.scatter(pcs[m, 0], pcs[m, 1], label=pos, alpha=0.7, c=c)
    ax.set_xlabel(f"PC1 ({ev[0]:.1f}%)")
    ax.set_ylabel(f"PC2 ({ev[1]:.1f}%)")
    ax.set_title("PCA - Player Features (per-90)")
    ax.legend()
    fig.savefig(f"{OUT}/pca_biplot.png", dpi=120, bbox_inches="tight")

    loadings = pd.DataFrame(pca.components_.T, index=feats,
                            columns=[f"PC{i+1}" for i in range(len(ev))])
    loadings.to_csv(f"{OUT}/pca_loadings.csv")
    df.to_csv(f"{OUT}/player_pcs.csv", index=False)
    print("saved:", f"{OUT}/pca_biplot.png", f"{OUT}/pca_loadings.csv")


if __name__ == "__main__":
    main()
