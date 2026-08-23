# -*- coding: utf-8 -*-
"""3.6b Market Value - so sanh 3 mo hinh regression (spec 3.6b).

LUU Y (quan trong): target hop le can market_value SAU giai lam ground truth.
Hien chi co gia TRUOC giai -> ket qua la "estimate" cho UI flow:
  Current Value -> Predicted Post-Tournament -> Estimated Change %
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEAT = "data/processed/analytics/player_features.csv"
SQ = "data/processed/csv/squads_and_players.csv"
OUT = "data/processed/analytics"


def main():
    feat = pd.read_csv(FEAT, dtype={"player_id": str})
    sq = pd.read_csv(SQ, dtype={"player_id": str})
    sq["value_log"] = np.log1p(sq["market_value_eur"])

    df = feat.merge(sq[["player_id", "value_log", "caps",
                        "date_of_birth"]], on="player_id", how="inner")
    df = df[df["minutes"] >= 90].copy()
    df["age"] = 2026 - df["date_of_birth"].str[:4].astype(float)

    feature_cols = ["position", "age", "caps", "goals_p90", "assists_p90",
                    "shots_p90", "shots_on_target_p90", "passes_p90",
                    "tackles_p90", "interceptions_p90", "clearances_p90"]
    X = pd.get_dummies(df[feature_cols].fillna(0), columns=["position"])
    y = df["value_log"]

    Xtr, Xte, ytr, yte, itr, ite = train_test_split(
        X, y, df, test_size=0.25, random_state=42)

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=300, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, random_state=42),
    }
    print(f"So mau train/test: {len(Xtr)}/{len(Xte)}\n")
    print(f"{'Mo hinh':22s} {'R2':>7} {'MAE(log)':>9}")
    best_name, best_model, best_r2 = None, None, -9
    results = {}
    for name, mdl in models.items():
        mdl.fit(Xtr, ytr)
        pred = mdl.predict(Xte)
        r2 = r2_score(yte, pred)
        mae = mean_absolute_error(yte, pred)
        print(f"{name:22s} {r2:7.3f} {mae:9.3f}")
        results[name] = {"r2": round(r2, 3), "mae_log": round(mae, 3)}
        if r2 > best_r2:
            best_name, best_model, best_r2 = name, mdl, r2

    # luu du bao tren toan bo dataset bang mo hinh tot nhat (dung cho web)
    df["predicted_value_log"] = best_model.predict(X)
    df["current_value"] = np.expm1(y).round(0)
    df["predicted_post_value"] = np.expm1(df["predicted_value_log"]).round(0)
    change = df["predicted_post_value"] - df["current_value"]
    df["change_abs"] = change.round(0)
    df["change_pct"] = (100 * change / df["current_value"].replace(0, np.nan)).round(1)

    out_cols = ["player_id", "player_name", "team", "position", "age",
                "current_value", "predicted_post_value", "change_abs", "change_pct"]
    mv_out = df[out_cols].sort_values("change_pct", ascending=False)
    mv_out.to_csv(f"{OUT}/market_value_estimates.csv", index=False)

    imp_path = f"{OUT}/market_value_importance.csv"
    if hasattr(best_model, "feature_importances_"):
        imp = pd.Series(best_model.feature_importances_, index=X.columns)
        imp.sort_values(ascending=False).to_csv(imp_path)

    print(f"\nModel tot nhat: {best_name}")
    print(f"Xuat {len(mv_out)} du bao -> {OUT}/market_value_estimates.csv")
    print("\nTop tang gia du kien (ESTIMATE chua validated):")
    cols_show = ["player_name", "team", "position", "current_value",
                 "predicted_post_value", "change_pct"]
    print(mv_out.head(6)[cols_show].to_string(index=False))
    print("\nDISCLAIMER: thieu ground truth gia-tri-sau-giai -> con so chi la")
    print("uoc luong tham khao tu perf WC + tuoi + caps.")


if __name__ == "__main__":
    main()
