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
    """Percentile rank 0-100 cua Series (NaN -> 0 nho fillna truoc)."""
    return (s.rank(pct=True) * 100).round(1)


def main():
    """4 diem chuyen mon + overall theo ROLE_MIX (percentile trong vai tro).

    Ghi analytics_scores.csv + score_validation.csv (Spearman overall~output).
    """
    df = pd.read_csv(FEAT)
    df = df[df["minutes"] >= MIN_MIN].copy()

    # Uu tien cot shrunk (chong hat-trick 1 tran), fallback cot goc.
    def _col(c):
        s = c + "_shrunk"
        return s if s in df.columns else c

    # 4 score chuyen mon cho outfield
    for sc_name, weights in SCORE_DEFS.items():
        # So sanh tung chi so voi cau thu cung vi tri; rank toan bo pool se
        # lam lech diem vi phan bo thong ke DEF/MID/FWD khac nhau.
        df[sc_name] = 0.0
        for pos in ROLE_MIX:
            mask = df["position"] == pos
            total = pd.Series(0.0, index=df.index[mask])
            for col, w in weights.items():
                col = _col(col) if col != "pass_accuracy_pct" else col
                if col in df.columns:
                    total += w * pct_rank(df.loc[mask, col].fillna(0))
            df.loc[mask, sc_name] = total.round(1)

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

    # Bien luan ROLE_MIX bang so lieu: overall phai tuong quan voi san luong
    # (goals+assists) hon la voi minutes don thuan trong tung vai tro.
    val = result.copy()
    feat_full = pd.read_csv(FEAT)
    val = val.merge(feat_full[["player_id", "total_goals", "total_assists",
                               "total_tackles", "total_interceptions",
                               "total_clearances"]],
                    on="player_id", how="left")
    val["ga"] = val["total_goals"].fillna(0) + val["total_assists"].fillna(0)
    val["def_act"] = (val["total_tackles"].fillna(0)
                      + val["total_interceptions"].fillna(0)
                      + val["total_clearances"].fillna(0))
    # Output chuan theo vai tro: DEF do bang hanh dong phong ngu, MID/FWD do
    # bang goals+assists (hau ve hiem khi ghi ban nen tuong quan goals thap la
    # dung ban chat, khong phai loi weights).
    TARGET = {"DEF": "def_act", "MID": "ga", "FWD": "ga"}
    vrows = []
    for pos in ("DEF", "MID", "FWD"):
        m = val[val["position"] == pos]
        if len(m) > 5:
            tgt = TARGET[pos]
            vrows.append({"position": pos, "n": len(m), "target": tgt,
                          "spearman_overall_vs_output": round(
                              m["overall_score"].corr(m[tgt], method="spearman"), 3),
                          "spearman_overall_vs_minutes": round(
                              m["overall_score"].corr(m["minutes"], method="spearman"), 3)})
    pd.DataFrame(vrows).to_csv(f"{OUT}/score_validation.csv", index=False)
    print("\nBien luan ROLE_MIX (overall ~ output, khong phai minutes):")
    print(pd.DataFrame(vrows).to_string(index=False))

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
    """Xep hang GK theo saves_p90/save_pct/clean-sheet (thang rieng)."""
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
