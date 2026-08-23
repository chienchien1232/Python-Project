# -*- coding: utf-8 -*-
"""3.4 Anomaly Detection - IsolationForest theo nhom vi tri + luat Z-score."""
import os

import pandas as pd
from sklearn.ensemble import IsolationForest

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90
CONTAM = 0.05


def main():
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    feats = [c for c in df.columns if c not in DROP and not c.startswith("total_")]

    flags = pd.Series(0, index=df.index)
    for pos in ("GK", "DEF", "MID", "FWD"):
        m = df["position"] == pos
        if m.sum() < 10:
            continue
        iso = IsolationForest(contamination=CONTAM, random_state=42)
        flags[m] = iso.fit_predict(df.loc[m, feats].fillna(0))

    df["anomaly"] = (flags == -1).astype(int)

    # luat cung: ngo le dau ra ro rang
    if "saves_p90" in df.columns:
        gk_hot = pd.to_numeric(df["saves_p90"], errors="coerce").fillna(0) >= 3.5
    else:
        gk_hot = pd.Series(False, index=df.index)
    hard = (
        (df["total_goals"] >= 3) |
        (df["goals_p90"] >= 0.9) |
        ((df["position"] == "GK") & gk_hot)
    )
    df["anomaly_hard"] = hard.astype(int)
    df["is_anomaly"] = (df["anomaly"] | df["anomaly_hard"])

    cols_show = ["player_name", "position", "team", "minutes",
                 "total_goals", "goals_p90", "tackles_p90",
                 "interceptions_p90", "anomaly"]
    res = df[df["is_anomaly"] == 1][cols_show].sort_values("minutes", ascending=False)
    res.to_csv(f"{OUT}/anomalies.csv", index=False)
    print(f"phat hien {len(res)} man trinh dien bat thuong / {len(df)} cau thu (>= {MIN_MIN} phut)")
    print(res.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
