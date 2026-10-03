# -*- coding: utf-8 -*-
"""3.2 Player Similarity - cosine top-K tren feature per-90 (chi outfield)."""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, normalize

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90

# Giam dem 2 lan cho cap feature tuong quan cao (giu cot output nhu cu).
# Can cu EDA (eda_corr.csv): passes/accurate r=0.974, goals/sot r=0.644,
# duels_won/aerial_duels_won r=0.998. Key ho tro ca ten goc va shrunk.
CORR_DOWNWEIGHT = {
    "accurate_passes_p90": 0.5,
    "accurate_passes_p90_shrunk": 0.5,
    "shots_on_target_p90": 0.5,
    "shots_on_target_p90_shrunk": 0.5,
    "aerial_duels_won_p90": 0.5,
    "aerial_duels_won_p90_shrunk": 0.5,
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    """Cosine similarity block theo vi tri tren z-score L2-normalized.

    Ghi similarity_matrix.parquet (index 'ten #id'); cross-pos = 0.
    """
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    # Loai GK: toan bo chi so ngoai san cua GK = 0 -> cosine similarity vo nghia
    df = df[df["position"].isin(["DEF", "MID", "FWD"])].copy().reset_index(drop=True)
    feats_base = [c for c in df.columns if c not in DROP and not c.startswith("total_")
                  and not c.endswith("_shrunk")]
    # Uu tien ban shrunk (chong nhieu mau nho), fallback ve goc neu file cu.
    feats = [c + "_shrunk" if c + "_shrunk" in df.columns else c for c in feats_base]
    raw = df[feats].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(dtype=float)
    # Giam dem cap tuong quan truoc khi scale (khong xoa cot, giu contract).
    w = np.array([CORR_DOWNWEIGHT.get(c, 1.0) for c in feats], dtype=float)
    raw = raw * w
    # FIX: StandardScaler roi L2-normalize truoc cosine.
    # Cosine truc tiep tren z-score (co am) meo goc; normalize dua ve mat cau don vi.
    Xz = StandardScaler().fit_transform(raw)
    Xn = normalize(Xz, norm="l2", axis=1)
    # Block theo vi tri: chi so cung pos moi co nghia; khac pos gan 0
    # (giu full ma tran vuong + label cu de UI tra cuu khong vo).
    n = len(df)
    sim = np.zeros((n, n), dtype=float)
    pos_arr = df["position"].to_numpy()
    for pos in ("DEF", "MID", "FWD"):
        idx = np.where(pos_arr == pos)[0]
        if len(idx) < 2:
            if len(idx) == 1:
                sim[idx[0], idx[0]] = 1.0
            continue
        sim[np.ix_(idx, idx)] = cosine_similarity(Xn[idx])
    np.fill_diagonal(sim, 1.0)
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
