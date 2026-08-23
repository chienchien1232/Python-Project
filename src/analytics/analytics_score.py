# -*- coding: utf-8 -*-
"""3.6a Analytics Score - 5 chi so rieng biet theo spec.

Attacking / Chance Creation / Passing / Defensive / Overall
Cong truc trong so minh bach, percentile 0-100 trong noi bo vai tro.
GK tinh rieng tu gk_features.
"""
import os
import sys

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEAT = "data/processed/analytics/player_features.csv"
GK = "data/processed/analytics/gk_features.csv"
OUT = "data/processed/analytics"
MIN_MIN = 90

SCORE_DEFS = {
    "attacking_score": {
        "goals_p90": .35, "shots_on_target_p90": .25, "shots_p90": .15,
        "assists_p90": .15, "dribbles_attempted_p90": .10,
    },
    "chance_creation_score": {
        "assists_p90": .35, "crosses_p90": .20, "fouls_won_p90": .20,
        "accurate_passes_p90": .15, "dribbles_attempted_p90": .10,
    },
    "passing_score": {
        "passes_p90": .30, "accurate_passes_p90": .30,
        "pass_accuracy_pct": .25, "crosses_p90": .15,
    },
    "defensive_score": {
        "tackles_p90": .25, "interceptions_p90": .20, "clearances_p90": .15,
        "blocks_p90": .15, "recoveries_p90": .15, "duels_won_p90": .10,
    },
}
ROLE_MIX = {  # tron 4 score thanh Overall theo vai tro
    "FWD": {"attacking_score": .55, "chance_creation_score": .25,
            "passing_score": .10, "defensive_score": .10},
    "MID": {"attacking_score": .20, "chance_creation_score": .30,
            "passing_score": .25, "defensive_score": .25},
    "DEF": {"attacking_score": .10, "chance_creation_score": .10,
            "passing_score": .20, "defensive_score": .60},
}


def pct_rank(s):
    return (s.rank(pct=True) * 100).round(1)


def main():
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()

    # 4 score chuyen mon cho outfield
    for sc_name, weights in SCORE_DEFS.items():
        total = pd.Series(0.0, index=df.index)
        for col, w in weights.items():
            if col in df.columns:
                total += w * pct_rank(df[col].fillna(0))
        df[sc_name] = total.round(1)

    # Overall theo role mix
    overall = pd.Series(0.0, index=df.index)
    for pos, mix in ROLE_MIX.items():
        m = df["position"] == pos
        for sc_name, w in mix.items():
            overall[m] += w * df.loc[m, sc_name]
    df["overall_score"] = overall.round(1)

    cols_out = ["player_id", "player_name", "position", "team", "matches",
                "minutes"] + list(SCORE_DEFS.keys()) + ["overall_score"]
    result = df[cols_out]

    # GK: overall rieng tu gk_features, ghep vao output
    gk_rows = _top_gk(MIN_MIN)
    if not gk_rows.empty:
        gk_out = gk_rows.assign(position="GK")[
            ["player_id", "player_name", "position", "team",
             "matches", "minutes", "overall_score"]]
        result = pd.concat([result[result["position"] != "GK"], gk_out],
                           ignore_index=True)

    result = result.sort_values("overall_score", ascending=False)
    os.makedirs(OUT, exist_ok=True)
    result.to_csv(f"{OUT}/analytics_scores.csv", index=False)

    print(f"Analytics Scores: {len(result)} cau thu (>= {MIN_MIN} phut)")
    print("\nTop OVERALL theo vai tro:")
    for pos in ("GK", "DEF", "MID", "FWD"):
        top3 = result[result["position"] == pos].head(3) if pos != "GK" else \
            _top_gk(MIN_MIN)[:3]
        if len(top3) == 0:
            continue
        print(f"\n  [{pos}]")
        for _, r in top3.iterrows():
            name = r.get("player_name")
            team = r.get("team")
            ov = r["overall_score"]
            print(f"    {ov:5.1f}  {name} ({team})")


def _top_gk(min_min):
    gk = pd.read_csv(GK)
    gk = gk[gk["minutes"] >= min_min].copy()
    gk["saves_p90"] = pd.to_numeric(gk["saves_p90"], errors="coerce").fillna(0)
    gk["save_pct"] = pd.to_numeric(gk["save_pct"], errors="coerce").fillna(0)
    cs_rate = (gk["clean_sheets"] / gk["matches"].replace(0, 1)) * 100
    gk["overall_score"] = (
        0.45 * pct_rank(gk["saves_p90"]) +
        0.30 * pct_rank(gk["save_pct"]) +
        0.25 * pct_rank(cs_rate)
    ).round(1)
    return gk.sort_values("overall_score", ascending=False)


if __name__ == "__main__":
    main()
