# -*- coding: utf-8 -*-
"""3.6a Analytics Score - chi so tong hop theo vai tro (percentile 0-100)."""
import os

import pandas as pd

FEAT = "data/processed/analytics/player_features.csv"
OUT = "data/processed/analytics"
MIN_MIN = 90

# Trong so theo vai tro (tong = 1.0) - thiet ke minh bach, co the chinh
WEIGHTS = {
    "FWD": {"goals_p90": .30, "assists_p90": .20, "shots_on_target_p90": .15,
            "dribbles_attempted_p90": .10, "fouls_won_p90": .10,
            "passes_p90": .05, "accurate_passes_p90": .10},
    "MID": {"assists_p90": .20, "passes_p90": .15, "accurate_passes_p90": .15,
            "interceptions_p90": .10, "tackles_p90": .10,
            "recoveries_p90": .10, "goals_p90": .10, "crosses_p90": .10},
    "DEF": {"tackles_p90": .25, "interceptions_p90": .20, "clearances_p90": .15,
            "blocks_p90": .10, "aerial_duels_won_p90": .15,
            "recoveries_p90": .10, "accurate_passes_p90": .05},
}

# GK: dung gk_features.csv
GK_WEIGHTS = {"saves_p90": .45, "save_pct": .35, "clean_sheets_per_match": .20}


def pct_rank(s, higher=True):
    return (s.rank(pct=True) * 100).round(1) if higher else ((1 - s.rank(pct=True)) * 100).round(1)


def main():
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()
    scores = []

    for pos, weights in WEIGHTS.items():
        sub = df[df["position"] == pos].copy()
        if sub.empty:
            continue
        total = 0.0
        for col, w in weights.items():
            if col not in sub:
                continue
            total += w * pct_rank(sub[col]).fillna(0)
        sub["analytics_score"] = total.round(1)
        scores.append(sub)

    # GK tu gk_features
    gk_path = f"{OUT}/gk_features.csv"
    if os.path.exists(gk_path):
        gk = pd.read_csv(gk_path)
        gk = gk[gk["minutes"] >= MIN_MIN].copy()
        if not gk.empty:
            gk["clean_sheets_per_match"] = (gk["clean_sheets"] / gk["matches"]).round(3)
            total = 0.0
            for col, w in GK_WEIGHTS.items():
                if col in gk:
                    total += w * pct_rank(gk[col].fillna(0))
            gk["position"] = "GK"
            gk["analytics_score"] = total.round(1)
            keep = ["player_id", "player_name", "position", "team",
                    "matches", "minutes", "analytics_score"]
            keep += [c for c in ("saves_p90", "save_pct") if c in gk]
            scores.append(gk[keep])

    cols_common = ["player_id", "player_name", "position", "team",
                   "matches", "minutes", "analytics_score"]
    result = pd.concat([s[cols_common + [c for c in s.columns
                                         if c.startswith("total_goals")]] for s in scores],
                       ignore_index=False) if False else pd.concat(scores, ignore_index=True)
    result = result.sort_values("analytics_score", ascending=False)
    result.to_csv(f"{OUT}/analytics_scores.csv", index=False)
    print(f"Analytics Score cho {len(result)} cau thu -> {OUT}/analytics_scores.csv")
    for pos in ("GK", "DEF", "MID", "FWD"):
        top = result[result["position"] == pos].head(3)
        if len(top):
            print(f"\nTop {pos}:")
            for _, r in top.iterrows():
                print(f"  {r['analytics_score']:5.1f}  {r['player_name']} ({r['team']})")


if __name__ == "__main__":
    main()
