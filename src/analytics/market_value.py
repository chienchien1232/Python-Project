# -*- coding: utf-8 -*-
"""3.6b Market Value - regression tu tuoi/caps + WC performance.

LUU Y: gia tri chuyen nhuong quyet dinh boi su nghiep CLB, tuoi, hop dong.
WC chi 5-7 tran -> mo hinh giai thich it; ket qua CHI mang tinh tham khao.
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

FEAT = "data/processed/analytics/player_features.csv"
SQ = "data/processed/csv/squads_and_players.csv"
OUT = "data/processed/analytics"


def main():
    feat = pd.read_csv(FEAT, dtype={"player_id": str})
    sq = pd.read_csv(SQ, dtype={"player_id": str})
    sq["market_value_eur"] = np.log1p(sq["market_value_eur"])

    df = feat.merge(sq[["player_id", "market_value_eur", "caps"]],
                    on="player_id", how="inner")
    df = df[df["minutes"] >= 90].copy()
    # age tu date_of_birth
    dob = sq.set_index("player_id")["date_of_birth"]
    df["birth_year"] = df["player_id"].map(dob).str[:4].astype(float)
    df["age"] = 2026 - df["birth_year"]

    y = df["market_value_eur"]
    X = pd.get_dummies(df[["position", "age", "caps",
                           "goals_p90", "assists_p90", "passes_p90",
                           "tackles_p90", "interceptions_p90"]].fillna(0),
                       columns=["position"])

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)

    r2 = r2_score(yte, pred)
    mae_log = mean_absolute_error(yte, pred)
    print(f"R2(log value) = {r2:.3f} | MAE(log) = {mae_log:.3f}")
    print(f"MAE thuc te ≈ {np.expm1(mae_log):,.0f} EUR (trung binh)")

    imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
    print("\nTop feature importance:")
    print(imp.head(8).round(3).to_string())
    imp.to_csv(f"{OUT}/market_value_importance.csv")
    print("\nDisclaimer: WC performance giai thich rat it phan sai so cua market")
    print("value (quyet dinh boi CLB/tuoi/hop dong). Ket qua CHI tham khao.")


if __name__ == "__main__":
    main()
