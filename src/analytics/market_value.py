# -*- coding: utf-8 -*-
"""3.6b Market Value - Counterfactual ML (spec 3.6b, phien ban cai tien).

CU CHI (sua loi cu): model cu du doan MUC GIA hien tai tu per-90 stats roi lay
chenh lech muc gia goi la "tang/giam" -> sieu sao bi "giam gia" vi model khong
nhin thay thuong hieu. Ban moi dung TYLE counterfactual:

  pre_pred  = du doan voi perf features thay bang median vi tri (gia dinh
              "mot giai trung binh")
  post_pred = du doan voi perf that cua cau thu
  ratio     = post_pred / pre_pred  (muc gia triet tieu trong ti le)
  change    = clamp((ratio - 1) * 100, -25, +80)
  post      = current * ratio

Features: profile (age, age^2, caps, position) + san luong that (minutes,
total_goals, total_assists) + per-90 + thanh tich doi (team_win_pct).
LUU Y: van thieu ground truth gia-tri-sau-giai -> ket qua la ESTIMATE.
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEAT = "data/processed/analytics/player_features.csv"
SQ = "data/processed/csv/squads_and_players.csv"
MATCHES = "data/processed/csv/matches.csv"
MTS = "data/processed/csv/match_team_stats.csv"
OUT = "data/processed/analytics"

PROFILE_COLS = ["age", "age2", "caps"]
PERF_COLS = ["minutes", "total_goals", "total_assists", "goals_p90",
             "assists_p90", "shots_p90", "shots_on_target_p90",
             "passes_p90", "tackles_p90", "interceptions_p90",
             "clearances_p90", "team_win_pct"]


def team_win_pct():
    """Ty le thang cua moi doi tu match_team_stats + matches -> {team_id: win_pct}."""
    mts = pd.read_csv(MTS, dtype={"team_id": str, "match_id": str})
    m = pd.read_csv(MATCHES, dtype={"match_id": str})
    mm = mts.merge(m[["match_id", "home_team_id", "away_team_id",
                      "home_score", "away_score"]],
                   on="match_id", how="left")
    is_home = mm["team_id"] == mm["home_team_id"]
    gf = np.where(is_home, mm["home_score"], mm["away_score"])
    ga = np.where(is_home, mm["away_score"], mm["home_score"])
    tmp = pd.DataFrame({"team_id": mm["team_id"], "win": (gf > ga).astype(int)})
    g = tmp.groupby("team_id").agg(matches=("win", "size"), wins=("win", "sum"))
    return (g["wins"] / g["matches"].replace(0, np.nan)).fillna(0.5).round(3)


def main():
    feat = pd.read_csv(FEAT, dtype={"player_id": str})
    sq = pd.read_csv(SQ, dtype={"player_id": str})
    sq["value_log"] = np.log1p(sq["market_value_eur"])

    df = feat.merge(sq[["player_id", "value_log", "caps", "date_of_birth",
                        "team_id"]], on="player_id", how="inner")
    df = df[df["minutes"] >= 90].copy()
    df["age"] = 2026 - df["date_of_birth"].str[:4].astype(float)
    df["age2"] = df["age"] ** 2
    df["team_win_pct"] = df["team_id"].map(team_win_pct()).astype(float)

    feature_cols = PROFILE_COLS + PERF_COLS
    df[feature_cols] = df[feature_cols].fillna(0)
    X = pd.get_dummies(df[feature_cols + ["position"]], columns=["position"])
    y = df["value_log"]

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=300, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, random_state=42),
    }
    print(f"So mau train/test: {len(Xtr)}/{len(Xte)}\n")
    print(f"{'Mo hinh':22s} {'R2':>7} {'MAE(log)':>9}")
    best_name, best_model, best_r2 = None, None, -9
    for name, mdl in models.items():
        mdl.fit(Xtr, ytr)
        pred = mdl.predict(Xte)
        r2 = r2_score(yte, pred)
        mae = mean_absolute_error(yte, pred)
        print(f"{name:22s} {r2:7.3f} {mae:9.3f}")
        if r2 > best_r2:
            best_name, best_model, best_r2 = name, mdl, r2

    # ---- counterfactual: perf -> median vi tri (gia dinh giai trung binh) ----
    X_pre = X.copy()
    med = df.groupby("position")[PERF_COLS].transform("median")
    for c in PERF_COLS:
        X_pre[c] = med[c]

    post_log = best_model.predict(X)
    pre_log = best_model.predict(X_pre)
    diff = post_log - pre_log

    # Tu hieu chuan do phan tan: hieu suat top 5% ~ +40% de Linear/RF khong
    # extrapolate vo tan (raw ratio co the lon hon 10x voi mo hinh tuyen tinh).
    pos_diff = diff[diff > 0]
    pos_q = float(np.quantile(pos_diff, 0.95)) if pos_diff.size else 1.0
    scale = (0.40 / pos_q) if pos_q > 0 else 1.0
    print(f"Hieu chuan counterfactual: scale={scale:.3f} (P95 diff={pos_q:.3f})")

    ratio = np.exp(scale * diff)
    df["change_pct"] = (100 * scale * diff).clip(-25, 80).round(1)
    df["current_value"] = np.expm1(y).round(0)
    df["predicted_post_value"] = (df["current_value"] * ratio).round(0)
    df["change_abs"] = (df["predicted_post_value"] - df["current_value"]).round(0)

    out_cols = ["player_id", "player_name", "team", "position", "age",
                "current_value", "predicted_post_value", "change_abs", "change_pct"]
    mv_out = df[out_cols].sort_values("change_pct", ascending=False)
    mv_out.to_csv(f"{OUT}/market_value_estimates.csv", index=False)

    if hasattr(best_model, "feature_importances_"):
        imp = pd.Series(best_model.feature_importances_, index=X.columns)
        imp.sort_values(ascending=False).to_csv(f"{OUT}/market_value_importance.csv")

    # ---- sanity: top vua pha luoi BAT BUOC tang gia ----
    top10 = df.nlargest(10, "total_goals")
    bad = top10[top10["change_pct"] <= 0]["player_name"].tolist()
    assert not bad, f"top vua pha luoi bi change <= 0: {bad}"

    print(f"\nModel tot nhat: {best_name} (R2={best_r2:.3f})")
    print(f"Xuat {len(mv_out)} du bao -> {OUT}/market_value_estimates.csv")
    cols_show = ["player_name", "team", "position", "current_value",
                 "predicted_post_value", "change_pct"]
    print("\nTop tang gia du kien (ESTIMATE chua validated):")
    print(mv_out.head(6)[cols_show].to_string(index=False))
    print("\nTop 10 vua pha luoi (sanity check - phai duong):")
    print(df.nlargest(10, "total_goals")[cols_show].to_string(index=False))
    # ---- validation voi gia tri that 8/2026 (Transfermarkt, neu co file) ----
    gt_path = f"{OUT}/market_value_ground_truth.csv"
    if os.path.exists(gt_path):
        gt = pd.read_csv(gt_path, dtype={"player_id": str})
        val = gt.merge(df[["player_id", "current_value", "predicted_post_value",
                           "change_pct"]], on="player_id", how="left")
        val["dev_pred_pct"] = (100 * (val["predicted_post_value"]
                                      - val["real_value_eur_2026_08"])
                               / val["real_value_eur_2026_08"]).round(1)
        val["dev_cur_pct"] = (100 * (val["current_value"]
                                     - val["real_value_eur_2026_08"])
                              / val["real_value_eur_2026_08"]).round(1)
        mae_pred = float(val["dev_pred_pct"].abs().mean().round(1))
        std_pred = float(val["dev_pred_pct"].std().round(1))
        mae_cur = float(val["dev_cur_pct"].abs().mean().round(1))
        hit = float((val["dev_pred_pct"].abs() <= 25).mean().round(3) * 100)
        val_out = val[["player_name", "team", "real_value_eur_2026_08",
                       "current_value", "predicted_post_value",
                       "dev_pred_pct", "dev_cur_pct"]]
        val_out.to_csv(f"{OUT}/market_value_validation.csv", index=False)
        print("\n=== VALIDATION vs GIA THAT 8/2026 (Transfermarkt, n="
              f"{len(val)}) ===")
        print(val_out.to_string(index=False))
        print(f"MAE du bao (post vs real): {mae_pred}% | do lech chuan: "
              f"{std_pred}% | MAE gia hien tai (dataset vs real): {mae_cur}%")
        print(f"Ty le du bao trong khoang +-25% so voi gia that: {hit}%")
        print("validation saved:", f"{OUT}/market_value_validation.csv")

    print("\nDISCLAIMER: thieu ground truth gia-tri-sau-giai -> day la uoc luong")
    print("counterfactual ML (perf that vs perf trung binh vi tri), tham khao thoi.")


if __name__ == "__main__":
    main()
