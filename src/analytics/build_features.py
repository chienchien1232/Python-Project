# -*- coding: utf-8 -*-
"""Feature store cho analytics suite.

Tong hop player_match_stats theo cau thu:
  - tong + per-90 cho cac cot han dong
  - GK rieng sang gk_features.csv
Output: data/processed/analytics/player_features.csv, gk_features.csv
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics.common import (ACTION_COLS, load_gk, load_pms, played, to_int)

OUT = "data/processed/analytics"

# Shrinkage cho per-90: keo chi so cua mau nho ve trung binh de hat-trick
# 1 tran 90' khong thong tri top score/cluster. Cong thuc Bayes don gian:
#   p90_shrunk = p90 * minutes / (minutes + SHRINK_K), SHRINK_K ~ 3 tran.
# Cot *_shrunk chi ADDITIVE (giut MIN_MIN=90 de so dong output khong doi).
SHRINK_K = 270


def per90(total, minutes):
    """Trung binh per-90. Tra None khi minutes = 0."""
    m = int(minutes or 0)
    return round(90.0 * total / m, 3) if m > 0 else None


def per90_shrunk(total, minutes, k=SHRINK_K):
    """Per-90 co shrinkage Bayes: keo mau nho ve 0 (k ~ 3 tran)."""
    m = int(minutes or 0)
    if m <= 0:
        return None
    raw = 90.0 * total / m
    return round(raw * m / (m + k), 3)


def build_players():
    """Gop player_match_stats theo cau thu (tong + per-90 + shrunk).

    Returns:
        List dict sap xep theo minutes giam dan, moi dict co total_*/ *_p90 /
        *_p90_shrunk cho 18 cot hanh dong + pass_accuracy_pct.
    """
    rows = [r for r in load_pms() if played(r)]
    agg = {}
    for r in rows:
        pid = r["player_id"]
        a = agg.setdefault(pid, {
            "player_id": pid,
            "player_name": r["player_name"],
            "position": r["position"],
            "team": r["player_team"],
            "nationality": r.get("nationality", ""),
            "matches": 0, "minutes": 0, "_sum": {c: 0 for c in ACTION_COLS},
        })
        a["matches"] += 1
        a["minutes"] += to_int(r["minutes_played"])
        for c in ACTION_COLS:
            a["_sum"][c] += to_int(r[c])

    out = []
    for pid, a in sorted(agg.items(), key=lambda kv: kv[1]["minutes"], reverse=True):
        rec = {"player_id": a["player_id"], "player_name": a["player_name"],
               "position": a["position"], "team": a["team"],
               "nationality": a["nationality"],
               "matches": a["matches"], "minutes": a["minutes"]}
        for c in ACTION_COLS:
            rec[f"total_{c}"] = a["_sum"][c]
            rec[f"{c}_p90"] = per90(a["_sum"][c], a["minutes"])
            rec[f"{c}_p90_shrunk"] = per90_shrunk(a["_sum"][c], a["minutes"])
        # pass accuracy %
        pa = a["_sum"]["accurate_passes"]
        tp = a["_sum"]["passes"]
        rec["pass_accuracy_pct"] = round(100.0 * pa / tp, 2) if tp else None
        out.append(rec)
    return out


def build_gk():
    """Gop goalkeeper_match_stats theo thu mon (save_pct, saves_p90)."""
    rows = [r for r in load_gk() if played(r)]
    agg = {}
    for r in rows:
        pid = r["player_id"]
        a = agg.setdefault(pid, {
            "player_id": pid, "player_name": r["player_name"],
            "team": r["team"],
            "matches": 0, "minutes": 0, "saves": 0, "shots_faced": 0,
            "conceded": 0, "clean_sheets": 0, "starts": 0,
        })
        a["matches"] += 1
        a["minutes"] += to_int(r["minutes_played"])
        a["saves"] += to_int(r["saves"])
        a["shots_faced"] += to_int(r["shots_faced"])
        a["conceded"] += to_int(r["goals_conceded_on_pitch"])
        a["clean_sheets"] += to_int(r["clean_sheet"])
        a["starts"] += to_int(r["starter"])

    out = []
    for pid, a in agg.items():
        faced = a["saves"] + a["conceded"]
        out.append({
            **{k: v for k, v in a.items() if k != "starts"},
            "starts": a["starts"],
            "save_pct": round(100.0 * a["saves"] / faced, 2) if faced else None,
            "saves_p90": per90(a["saves"], a["minutes"]),
        })
    return out


def write_csv(path, records):
    """Ghi list dict ra CSV (tu tao thu muc). Returns: (path, so dong)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(records)
    return path, len(records)


if __name__ == "__main__":
    players = build_players()
    keepers = build_gk()
    p1 = write_csv(f"{OUT}/player_features.csv", players)
    p2 = write_csv(f"{OUT}/gk_features.csv", keepers)
    print(f"player_features: {p1[1]} rows ({sum(1 for x in players if x['minutes'] >= 90)} du >=90')")
    print(f"gk_features:     {p2[1]} rows")
