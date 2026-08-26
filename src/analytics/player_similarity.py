# -*- coding: utf-8 -*-
"""3.2 Player Similarity - cosine top-K tren feature per-90 (chi outfield)."""
import os

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90


def main():
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    # Loai GK: toan bo chi so ngoai san cua GK = 0 -> cosine similarity vo nghia
    df = df[df["position"].isin(["DEF", "MID", "FWD"])].copy()
    feats = [c for c in df.columns if c not in DROP and not c.startswith("total_")]
    X = StandardScaler().fit_transform(df[feats].fillna(0))
    sim = cosine_similarity(X)  # cung nhom vi tri thi giong nhat; co the loc them
    df["label"] = df["player_name"] + " #" + df["player_id"].astype(str)
    sim_df = pd.DataFrame(sim, index=df["label"], columns=df["label"])
    os.makedirs(OUT, exist_ok=True)
    sim_df.to_parquet(f"{OUT}/similarity_matrix.parquet")

    # demo top-5 tuong dong voi 1 cau thu mau
    target = next((x for x in sim_df.index if "MESSI" in x.upper()), sim_df.index[0])
    top = sim_df[target].drop(target).sort_values(ascending=False).head(5)
    print(f"\nTop-5 tuong dong voi [{target}]:")
    for name, s in top.items():
        print(f"  {s:.3f}  {name}")


if __name__ == "__main__":
    main()
