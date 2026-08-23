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

    # ---- Plotly tuong tac: mau theo cluster, hover thong tin (spec 3.5) ----
    import plotly.express as px
    clus_path = f"{OUT}/player_clusters.csv"
    hover = ["player_name", "team", "position"]
    if os.path.exists(clus_path):
        clus = pd.read_csv(clus_path)
        keep = [c for c in ("cluster", "cluster_label") if c in clus.columns]
        df = df.merge(clus[["player_id"] + keep], on="player_id", how="left")
        color_col = "cluster_label" if "cluster_label" in df.columns else "position"
        hover += [c for c in ("cluster_label", "cluster") if c in df.columns]
    else:
        color_col = "position"
    fig = px.scatter(df, x="PC1", y="PC2", color=color_col,
                     hover_data=hover + ["goals_p90", "assists_p90",
                                         "passes_p90", "tackles_p90"],
                     title="PCA - Player Style Map (World Cup 2026)",
                     labels={"PC1": f"PC1 ({ev[0]:.1f}%)",
                             "PC2": f"PC2 ({ev[1]:.1f}%)"})
    fig.update_traces(marker=dict(size=8, opacity=0.75))
    fig.write_html(f"{OUT}/pca_interactive.html", include_plotlyjs="cdn")
    print("saved:", f"{OUT}/pca_interactive.html")
    print("saved:", f"{OUT}/pca_biplot.png", f"{OUT}/pca_loadings.csv")


if __name__ == "__main__":
    main()
