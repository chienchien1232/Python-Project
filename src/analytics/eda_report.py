# -*- coding: utf-8 -*-
"""P1 - Bao cao EDA cho BTL ML (chay duoc, khong phai placeholder).

Doc player_features.csv / gk_features.csv, xuat:
  - eda_missing.csv      : ti le thieu tung cot
  - eda_corr.csv         : ma tran tuong quan 18 chi so p90
  - eda_minutes_bins.csv : mean/std goals_p90 theo nhom phut (chot MIN_MIN + shrinkage)
  - eda_minutes_hist.png / eda_corr_heatmap.png / eda_shrinkage.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEAT = "data/processed/analytics/player_features.csv"
GK = "data/processed/analytics/gk_features.csv"
OUT = "data/processed/analytics"

P90_COLS = ["goals_p90", "assists_p90", "shots_p90", "shots_on_target_p90",
            "passes_p90", "accurate_passes_p90", "crosses_p90", "tackles_p90",
            "interceptions_p90", "clearances_p90", "blocks_p90", "recoveries_p90",
            "duels_won_p90", "aerial_duels_won_p90", "dribbles_attempted_p90",
            "fouls_committed_p90", "fouls_won_p90", "offsides_p90"]


def main():
    """EDA phuc vu BTL: missing, variance theo phut, corr, shrinkage.

    Ghi eda_missing/corr/minutes_bins.csv + 3 bieu do PNG.
    """
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_csv(FEAT)
    gk = pd.read_csv(GK)
    print(f"player_features: {df.shape} | gk_features: {gk.shape}")
    print("Vi tri:", df["position"].value_counts().to_dict())

    # 1. Missing rates
    miss = pd.DataFrame({"column": df.columns,
                         "missing_pct": (df.isna().mean().values * 100).round(2),
                         "dtype": [str(t) for t in df.dtypes.values]})
    miss.to_csv(f"{OUT}/eda_missing.csv", index=False)
    print("\nTop thieu:")
    print(miss.sort_values("missing_pct", ascending=False).head(8).to_string(index=False))

    # 2. Minutes distribution + variance theo bins -> chot MIN_MIN / shrinkage
    print("\nPhan vi minutes:", df["minutes"].describe().round(1).to_dict())
    bins = [0, 90, 180, 270, 360, 540, 900]
    labels = ["0-90", "90-180", "180-270", "270-360", "360-540", "540+"]
    df["min_bin"] = pd.cut(df["minutes"], bins=bins, labels=labels)
    grp = df.groupby("min_bin", observed=True).agg(
        n=("goals_p90", "size"),
        goals_p90_std=("goals_p90", "std"),
        goals_p90_max=("goals_p90", "max")).round(3)
    grp.to_csv(f"{OUT}/eda_minutes_bins.csv")
    print("\nVariance goals_p90 theo phut:")
    print(grp.to_string())

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["minutes"], bins=30, color="#a8dadc", edgecolor="#080808")
    ax.axvline(90, color="#d7c3a3", linestyle="--", label="MIN_MIN=90")
    ax.axvline(270, color="#ff5252", linestyle="--", label="SHRINK_K=270")
    ax.set_xlabel("minutes"); ax.set_ylabel("players")
    ax.set_title("Phan phoi minutes - co so cho MIN_MIN + shrinkage")
    ax.legend()
    fig.savefig(f"{OUT}/eda_minutes_hist.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # 3. Correlation 18 p90 -> can cu downweight
    corr = df[P90_COLS].apply(pd.to_numeric, errors="coerce").corr().round(3)
    corr.to_csv(f"{OUT}/eda_corr.csv")
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    print("\nTop tuong quan:")
    print(pairs.sort_values(ascending=False).head(8).to_string())

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(corr.values, cmap="Greys", vmin=-1, vmax=1)
    ax.set_xticks(range(len(P90_COLS)), P90_COLS, rotation=90, fontsize=7)
    ax.set_yticks(range(len(P90_COLS)), P90_COLS, fontsize=7)
    fig.colorbar(im, ax=ax, label="Pearson r")
    ax.set_title("Tuong quan 18 chi so p90 (can cu downweight 0.5)")
    fig.savefig(f"{OUT}/eda_corr_heatmap.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # 4. Shrinkage curve: K=90/270/540 cho cau thu 90' ghi 3 ban (p90=3.0)
    ks = [90, 270, 540]
    print("\nShrinkage cho hat-trick 90' (p90=3.0):")
    for k in ks:
        print(f"  K={k}: {3.0 * 90 / (90 + k):.2f}")
    m = np.linspace(90, 720, 100)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k in ks:
        ax.plot(m, 3.0 * m / (m + k), label=f"K={k}")
    ax.set_xlabel("minutes"); ax.set_ylabel("goals_p90_shrunk (nen p90=3.0)")
    ax.set_title("K=270: 90' -> 0.75, 540' -> 2.0 (giam nhieu mau nho)")
    ax.legend()
    fig.savefig(f"{OUT}/eda_shrinkage.png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("\nsaved: eda_missing/corr/minutes_bins.csv + 3 png")


if __name__ == "__main__":
    main()
