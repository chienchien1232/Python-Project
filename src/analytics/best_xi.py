# -*- coding: utf-8 -*-
"""3.7 Optimal Best XI - tu dong tao doi hinh tieu bieu.

Rang buoc: formation (mac dinh 4-3-3) theo bucket DEF/MID/FWD + 1 GK.
Score = Analytics Score dieu chinh Elo doi thu trung binh (toggle).
Gioi han: vi tri chi co 4 bucket generic -> khong phan canh trai/phai.
"""
import csv
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

SCORES = "data/processed/analytics/analytics_scores.csv"
TEAMS = "data/processed/csv/teams.csv"
OUT = "data/processed/analytics"
MIN_MIN = 90


def load_elo():
    with open(TEAMS, newline="", encoding="utf-8-sig") as f:
        return {r["team_name"]: float(r["elo_rating"]) for r in csv.DictReader(f)}


def main(formation=(1, 4, 3, 3), elo_adjust=False):
    df = pd.read_csv(SCORES)
    df = df[df["minutes"] >= MIN_MIN].copy()
    elo = load_elo()

    if elo_adjust:
        # thuong so khi thang/draw/tran kho khan: +score nho theo elo doi thu
        def opp_bonus(row):
            opp_elo = elo.get(row.get("opponent_team", ""), 1700)
            return min(max((opp_elo - 1650) / 1000.0, 0), 0.05)
        df["final_score"] = (df["analytics_score"] * (1 + df.apply(opp_bonus, axis=1))).round(2)
    else:
        df["final_score"] = df["analytics_score"]

    picks = []
    used = set()
    for role, n in zip(("GK", "DEF", "MID", "FWD"), formation):
        pool = df[(df["position"] == role) & (~df.index.isin(used))]
        top = pool.nlargest(n, "final_score")
        used.update(top.index)
        for _, r in top.iterrows():
            picks.append({"role": role, "player_id": r["player_id"],
                          "player_name": r["player_name"], "team": r["team"],
                          "matches": r["matches"], "minutes": r["minutes"],
                          "score": r["final_score"]})

    xi = pd.DataFrame(picks)
    xi.to_csv(f"{OUT}/best_xi.csv", index=False)

    print(f"BEST XI ({formation[0]}-{formation[1]}-{formation[2]}-{formation[3]})")
    print("=" * 46)
    for _, r in xi.iterrows():
        print(f"  [{r['role']:>3}] {r['player_name']:26s} {r['team']:20s} "
              f"score={r['score']:.1f} | {r['matches']} trän / {r['minutes']}'")

    bench = df[~df.index.isin(used)].nlargest(7, "final_score")
    bench.to_csv(f"{OUT}/best_xi_bench.csv", index=False)
    print("\nDự bị (7):")
    for _, r in bench.iterrows():
        print(f"  [{r['position']:>3}] {r['player_name']:26s} score={r['final_score']:.1f}")


if __name__ == "__main__":
    import sys
    elo_adj = "--elo" in sys.argv
    main(elo_adjust=elo_adj)
