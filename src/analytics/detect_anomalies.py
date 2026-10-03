# -*- coding: utf-8 -*-
"""3.4 Anomaly Detection - IsolationForest theo nhom vi tri + luat Z-score."""
import sys

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"

DROP = {"player_id", "player_name", "position", "team", "nationality",
        "matches", "minutes", "pass_accuracy_pct"}
MIN_MIN = 90
CONTAM = 0.05


def main(contamination: float = CONTAM):
    """IsolationForest theo vi tri (scale rieng) + luat cung + ly do z-score.

    Args:
        contamination: ti le ngoai le du kien cho IsolationForest.
    Ghi anomalies.csv + anomaly_tuning.csv (0.03/0.05/0.07).
    """
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    # Giu 18 cot p90 goc (loai *_shrunk) de schema on dinh; shrinkage da ap
    # dung o cluster/similarity/score, anomaly giu nguong cu de UI khong doi.
    feats = [c for c in df.columns if c not in DROP and not c.startswith("total_")
             and not c.endswith("_shrunk")]

    # FIX: scale RIENG theo tung vi tri truoc IsolationForest.
    # Ban cu fit tren raw per-90 -> passes_p90 (~40) de chet goals_p90 (~0.5).
    flags = pd.Series(0, index=df.index)
    for pos in ("GK", "DEF", "MID", "FWD"):
        m = df["position"] == pos
        if m.sum() < 10:
            continue
        X_pos = df.loc[m, feats].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(dtype=float)
        Xs = StandardScaler().fit_transform(X_pos)
        iso = IsolationForest(contamination=contamination, random_state=42)
        flags[m] = iso.fit_predict(Xs)

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

    # Thi nghiem contamination 0.03/0.05/0.07 de bao ve lua chon mac dinh.
    tune_rows = []
    for cont in (0.03, 0.05, 0.07):
        n_iso, n_both = 0, 0
        for pos in ("GK", "DEF", "MID", "FWD"):
            m = df["position"] == pos
            if m.sum() < 10:
                continue
            Xp = StandardScaler().fit_transform(
                df.loc[m, feats].apply(pd.to_numeric, errors="coerce")
                .fillna(0).to_numpy(dtype=float))
            fl = IsolationForest(contamination=cont, random_state=42).fit_predict(Xp)
            iso_m = pd.Series(0, index=df.index)
            iso_m[m] = fl
            hit = (iso_m == -1)
            n_iso += int(hit.sum())
            n_both += int((hit & hard).sum())
        tune_rows.append({"contamination": cont, "n_isolation": n_iso,
                          "n_overlap_hard": n_both,
                          "n_hard": int(hard.sum())})
    pd.DataFrame(tune_rows).to_csv(f"{OUT}/anomaly_tuning.csv", index=False)
    print("Contamination tuning:")
    print(pd.DataFrame(tune_rows).to_string(index=False))

    # nguyen nhan anomaly: 2 feature lech |z| lon nhat so voi trung binh vi tri.
    # FIX: tinh z tren gia tri GOC theo pos (ban cu tru mean tren du lieu
    # da scale global -> scale 2 lan, sigma giai thich sai).
    raw = df[feats].apply(pd.to_numeric, errors="coerce").fillna(0)
    zmean = pd.DataFrame(0.0, index=df.index, columns=feats)
    for pos in ("GK", "DEF", "MID", "FWD"):
        m = df["position"] == pos
        if m.sum():
            sub = raw[m]
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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--contamination", type=float, default=CONTAM)
    a = ap.parse_args()
    main(contamination=a.contamination)
