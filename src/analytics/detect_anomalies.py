# -*- coding: utf-8 -*-
"""3.4 Anomaly Detection - IsolationForest theo nhom vi tri + luat Z-score."""
import os

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

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

    all_X = pd.DataFrame(StandardScaler().fit_transform(df[feats].fillna(0)),
                         index=df.index, columns=feats)

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

    # nguyen nhan anomaly: 2 feature lech |z| lon nhat so voi trung binh vi tri
    zdf = all_X
    zmean = pd.DataFrame(0.0, index=df.index, columns=feats)
    for pos in ("GK", "DEF", "MID", "FWD"):
        m = df["position"] == pos
        if m.sum():
            sub = zdf[m]
            zmean[m] = (sub - sub.mean()) / sub.std().replace(0, 1)

    cols_show = ["player_name", "position", "team", "minutes",
                 "total_goals", "goals_p90", "tackles_p90",
                 "interceptions_p90", "anomaly"]
    res = df[df["is_anomaly"] == 1][cols_show].copy()
    reasons = []
    for idx in res.index:
        top2 = zmean.loc[idx].abs().sort_values(ascending=False).head(2)
        reasons.append(", ".join(f"{c} ({'+' if zmean.loc[idx, c] > 0 else '-'}"
                                 f"{abs(zmean.loc[idx, c]):.1f}σ)"
                                 for c in top2.index))
    res["nguyen_nhan"] = reasons
    res.to_csv(f"{OUT}/anomalies.csv", index=False)
    print(f"phat hien {len(res)} man trinh dien bat thuong / {len(df)} cau thu (>= {MIN_MIN} phut)")
    print(res.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
