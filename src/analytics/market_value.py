# -*- coding: utf-8 -*-
"""Estimate observed player market values from tournament features.

This is a cross-sectional regression against the market values in the input
dataset. It does not forecast a future or post-tournament transfer value.
"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import (GridSearchCV, StratifiedKFold,
                                    cross_val_predict, train_test_split)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEAT = "data/processed/analytics/player_features.csv"
SQ = "data/processed/csv/squads_and_players.csv"
OUT = "data/processed/analytics"
MIN_MIN = 90
REFERENCE_YEAR = 2026

PROFILE_COLS = ["age", "age2", "caps"]
PERF_COLS = ["minutes", "total_goals", "total_assists", "goals_p90",
             "assists_p90", "shots_p90", "shots_on_target_p90",
             "passes_p90", "tackles_p90", "interceptions_p90",
             "clearances_p90"]


def _models():
    """Return scaled regression candidates and compact search grids."""
    return {
        "Linear Regression": (
            make_pipeline(StandardScaler(), LinearRegression()), {}),
        "Ridge": (
            make_pipeline(StandardScaler(), Ridge()),
            {"ridge__alpha": np.logspace(-2, 4, 7)}),
        "Random Forest": (
            RandomForestRegressor(random_state=42, n_jobs=1),
            {"n_estimators": [150, 300], "max_depth": [6, None],
             "min_samples_leaf": [3, 8]}),
        "Gradient Boosting": (
            GradientBoostingRegressor(random_state=42),
            {"n_estimators": [100, 200], "max_depth": [2, 3],
             "learning_rate": [0.03, 0.08]}),
    }


def _load_training_data():
    feat = pd.read_csv(FEAT, dtype={"player_id": str})
    squad = pd.read_csv(SQ, dtype={"player_id": str})
    needed = ["player_id", "market_value_eur", "caps", "date_of_birth"]
    df = feat.merge(squad[needed], on="player_id", how="inner",
                    validate="one_to_one")
    df["market_value_eur"] = pd.to_numeric(df["market_value_eur"], errors="coerce")
    df = df[(df["minutes"] >= MIN_MIN) & (df["market_value_eur"] > 0)].copy()
    if df.empty:
        raise ValueError("Khong co cau thu nao co gia tri duong va da toi thieu 90 phut.")

    birth_year = pd.to_numeric(
        df["date_of_birth"].astype("string").str[:4], errors="coerce")
    df["age"] = (REFERENCE_YEAR - birth_year).where(birth_year.notna())
    for col in ("age", "caps"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df.groupby("position")[col].transform(
            lambda values: values.fillna(values.median()))
        df[col] = df[col].fillna(df[col].median())
    df["age"] = df["age"].clip(15, 45)
    df["age2"] = df["age"] ** 2

    feature_cols = PROFILE_COLS + PERF_COLS
    df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
    X = pd.get_dummies(df[feature_cols + ["position"]],
                       columns=["position"], dtype=float)
    y = np.log1p(df["market_value_eur"].astype(float))
    return df, X, y


def _holdout_metrics(y_true_log, y_pred_log, baseline_mae, min_log, max_log):
    actual = np.expm1(y_true_log)
    predicted = np.expm1(np.clip(y_pred_log, min_log, max_log))
    nonzero = actual > 0
    return {
        "r2_log": round(float(r2_score(y_true_log, y_pred_log)), 3),
        "mae_log": round(float(mean_absolute_error(y_true_log, y_pred_log)), 3),
        "mae_eur": round(float(mean_absolute_error(actual, predicted)), 0),
        "median_absolute_pct_error": round(float(np.median(
            np.abs((predicted[nonzero] - actual[nonzero]) / actual[nonzero])) * 100), 1),
        "position_median_mae_eur": round(float(baseline_mae), 0),
    }


def main():
    """Tune on training-only folds, evaluate once, then fit for all players."""
    df, X, y = _load_training_data()
    x_train, x_test, y_train, y_test, pos_train, pos_test = train_test_split(
        X, y, df["position"], test_size=0.25, random_state=42,
        stratify=df["position"])

    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_splits = list(folds.split(x_train, pos_train))
    min_log, max_log = float(y_train.min()), float(y_train.max())
    best_name, best_score, best_search = None, -np.inf, None
    cv_rows = []
    print(f"So mau train/test: {len(x_train)}/{len(x_test)}\n")
    print(f"{'Mo hinh':22s} {'MAE_cv_log':>11} {'MAE_holdout_log':>16}")

    for name, (estimator, grid) in _models().items():
        search = GridSearchCV(
            estimator, grid, cv=cv_splits, scoring="neg_mean_absolute_error",
            n_jobs=1, refit=True)
        search.fit(x_train, y_train)
        # Search and hyperparameter selection see training data only. The test
        # fold remains untouched until the single final evaluation below.
        pred_test = search.best_estimator_.predict(x_test)
        mae_cv = float(-search.best_score_)
        pred_test = np.clip(pred_test, min_log, max_log)
        mae_test = float(mean_absolute_error(y_test, pred_test))
        print(f"{name:22s} {mae_cv:11.3f} {mae_test:16.3f}")
        cv_rows.append({"model": name, "mae_cv_log": round(mae_cv, 3),
                        "mae_holdout_log": round(mae_test, 3),
                        "best_params": str(search.best_params_) or "-"})
        if -mae_cv > best_score:
            best_name, best_score, best_search = name, -mae_cv, search

    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(cv_rows).to_csv(f"{OUT}/market_value_cv.csv", index=False)

    actual_test = np.expm1(y_test.to_numpy())
    pred_test_log = np.clip(best_search.best_estimator_.predict(x_test), min_log, max_log)
    pred_test_eur = np.expm1(pred_test_log)
    baseline_eur = pd.DataFrame({
        "position": pos_train, "value": np.expm1(y_train)
    }).groupby("position")["value"].median()
    baseline_pred = pos_test.map(baseline_eur).to_numpy()
    holdout = _holdout_metrics(
        y_test.to_numpy(), pred_test_log,
        mean_absolute_error(actual_test, baseline_pred), min_log, max_log)
    holdout["model_mae_eur"] = round(float(mean_absolute_error(actual_test, pred_test_eur)), 0)
    holdout["best_model"] = best_name
    holdout["n_test"] = len(x_test)
    pd.DataFrame([holdout]).to_csv(f"{OUT}/market_value_holdout.csv", index=False)
    print(f"\nModel chon theo MAE CV: {best_name}")
    print("Holdout (khong dung khi chon model):", holdout)

    # Refit for global feature importance. Per-player estimates use OOF
    # predictions so a player's own target does not train its estimate.
    final_model = best_search.best_estimator_
    final_model.fit(X, y)
    all_cv_splits = list(StratifiedKFold(
        n_splits=5, shuffle=True, random_state=2026).split(X, df["position"]))
    estimate_log = cross_val_predict(
        clone(final_model), X, y,
        cv=all_cv_splits,
        n_jobs=1)
    estimate_log = np.clip(estimate_log, float(y.min()), float(y.max()))
    df["current_value"] = df["market_value_eur"].round(0)
    df["model_estimated_value"] = np.expm1(estimate_log).round(0)
    df["model_gap_abs"] = (df["model_estimated_value"] - df["current_value"]).round(0)
    df["model_gap_pct"] = (
        100 * df["model_gap_abs"] / df["current_value"].replace(0, np.nan)
    ).round(1)

    out_cols = ["player_id", "player_name", "team", "position", "age",
                "current_value", "model_estimated_value", "model_gap_abs",
                "model_gap_pct"]
    estimates = df[out_cols].sort_values("model_gap_pct", ascending=False)
    estimates.to_csv(f"{OUT}/market_value_estimates.csv", index=False)

    regressor = final_model.steps[-1][1] if hasattr(final_model, "steps") else final_model
    if hasattr(regressor, "feature_importances_"):
        importance = pd.Series(regressor.feature_importances_, index=X.columns)
        importance.sort_values(ascending=False).to_csv(
            f"{OUT}/market_value_importance.csv")
    elif hasattr(regressor, "coef_"):
        # Ridge/linear coefficients are scaled; preserve feature names.
        importance = pd.Series(np.abs(np.asarray(regressor.coef_).ravel()),
                               index=X.columns)
        importance.sort_values(ascending=False).to_csv(
            f"{OUT}/market_value_importance.csv")

    print(f"\nXuat {len(estimates)} uoc tinh gia tri dataset -> {OUT}/market_value_estimates.csv")
    print("Top chenh lech mo hinh vs gia trong dataset:")
    print(estimates.head(6)[["player_name", "team", "current_value",
                            "model_estimated_value", "model_gap_pct"]]
          .to_string(index=False))
    print("\nLuu y: model gap la do lech cua hoi quy so voi gia tri dataset,")
    print("khong phai muc tang gia sau giai hay du bao chuyen nhuong.")


if __name__ == "__main__":
    main()
