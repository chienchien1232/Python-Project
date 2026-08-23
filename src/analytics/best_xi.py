# -*- coding: utf-8 -*-
"""3.7 Optimal Best XI - Linear Programming (PuLP) theo spec.

Constraint Control Panel:
  - Formation: 4-3-3 / 4-2-3-1 / 3-5-2 / 4-4-2 / 3-4-3 ...
  - Budget slider: tong market_value_eur cua XI <= budget (trieu EUR)
  - Max-per-nation: so cau thu toi da cung 1 doi tuyen
Muc tieu: max tong Analytics Score.
"""
import os
import sys

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import pulp
except ImportError:
    sys.exit("Can thu vien PuLP: pip install pulp")

SCORES = "data/processed/analytics/analytics_scores.csv"
SQ = "data/processed/csv/squads_and_players.csv"
OUT = "data/processed/analytics"

FORMATIONS = {
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-4-3": {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3},
}


def main(formation="4-3-3", budget_meur=None, max_per_nation=None):
    df = pd.read_csv(SCORES, dtype={"player_id": str})
    df = df[df["minutes"] >= MIN_MIN] if (MIN_MIN := 90) else df
    sq = pd.read_csv(SQ, dtype={"player_id": str})[
        ["player_id", "market_value_eur", "date_of_birth"]]
    df = df.merge(sq, on="player_id", how="left")
    df["value_meur"] = (df["market_value_eur"] / 1e6).round(1)
    df = df[df["value_meur"].notna()]

    prob = pulp.LpProblem("BestXI", pulp.LpMaximize)
    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in df.index}
    prob += pulp.lpSum(df.loc[i, "overall_score"] * x[i] for i in df.index)

    prob += pulp.lpSum(x.values()) == 11, "total_11"
    for pos, need in FORMATIONS[formation].items():
        idx = df.index[df["position"] == pos]
        prob += pulp.lpSum(x[i] for i in idx) == need, f"need_{pos}"
    if budget_meur:
        prob += pulp.lpSum(df.loc[i, "value_meur"] * x[i] for i in df.index) \
            <= budget_meur, "budget"
    if max_per_nation:
        for nat, grp in df.groupby("team"):
            prob += pulp.lpSum(x[i] for i in grp.index) <= max_per_nation, \
                f"nat_{nat}"

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        print(f"Khong tim du phuong an toi uu ({pulp.LpStatus[status]}). "
              f"Giam rang buoc budget/max-nation.")
        return

    xi = df[[x[i].value() == 1 for i in df.index]].copy()
    order = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
    xi["_o"] = xi["position"].map(order)
    xi = xi.sort_values("_o")
    total_score = xi["overall_score"].sum().round(1)
    total_val = xi["value_meur"].sum().round(1)

    out = xi[["position", "player_name", "team",
              "minutes", "overall_score", "value_meur"]]\
        .rename(columns={"overall_score": "score", "value_meur": "value_eurm"})
    out.to_csv(f"{OUT}/best_xi.csv", index=False)

    print(f"BEST XI [{formation}] | Tong score: {total_score} | "
          f"Tong gia: {total_val}M EUR")
    print("=" * 62)
    for _, r in out.iterrows():
        print(f"  [{r['position']:>3}] {r['player_name']:28s} "
              f"{r['team'][:18]:18s} score={r['score']:5.1f} "
              f"gia={r['value_eurm']:6.1f}M")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--formation", default="4-3-3", choices=FORMATIONS.keys())
    ap.add_argument("--budget", type=float, default=None,
                    help="Ngan sach toi da (trieu EUR)")
    ap.add_argument("--max-nation", type=int, default=None)
    a = ap.parse_args()
    main(a.formation, a.budget, a.max_nation)
