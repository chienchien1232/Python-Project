# -*- coding: utf-8 -*-
"""Consolidate penalty-saves / punches into goalkeeper_match_stats.csv.

Sources: ESPN summaries (all 104 matches, via pen_punch_part1/2.json).
- penalty_saves = regulation-time saved penalties credited to keeper's team
  (shootout saves excluded, counted separately in raw file)
- punches = GK punches from play commentary
- bench GKs (never on pitch): factual known-zeros for action columns
- high_claims / errors: no public source publishes them -> stay NULL (documented)
"""
import csv
import json
import re
import unicodedata
from collections import defaultdict

WC = "data/processed/wc2026_player_match"


def norm(s):
    """Chuan hoa ten ve chu thuong khong dau de join."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]", "", s.lower())


ALIAS = {"korearepublic": "southkorea", "unitedstates": "usa",
         "bosniaherzegovina": "bosniaandherzegovina", "capeverde": "caboverde"}


def load_json(path):
    """Doc JSON, tra dict rong neu thieu file (ghi log thay vi crash)."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        print(f"  skip {path}: {e}")
        return {}


def load_rows(path):
    """Doc CSV tra ve list dict."""
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def keeper_team(sentence):
    """Doi cua thu mon tu ten trong ngoac don cuoi cau."""
    parens = re.findall(r"\(([^()]+)\)", sentence or "")
    t = norm(parens[-1]) if parens else None
    return ALIAS.get(t, t)


def main():
    """Ghep pen-saves/punches ESPN vao gk stats (chi dien o trong)."""
    p1 = load_json("data/raw/espn/pen_punch_part1.json")
    p2 = load_json("data/raw/espn/pen_punch_part2.json")

    ms = {r["match_id"]: r for r in load_rows("data/processed/csv/matches.csv")}
    teams = {r["team_id"]: r["team_name"] for r in load_rows("data/processed/csv/teams.csv")}

    def side_of(mid, team_norm):
        m = ms.get(mid)
        if m is None or not team_norm:
            return None
        h = ALIAS.get(norm(teams[m["home_team_id"]]), norm(teams[m["home_team_id"]]))
        a = ALIAS.get(norm(teams[m["away_team_id"]]), norm(teams[m["away_team_id"]]))
        if team_norm == h:
            return "home"
        if team_norm == a:
            return "away"
        return None

    pensave_by: dict = defaultdict(int)   # (mid, side) -> n  (regulation only)
    sosave_by: dict = defaultdict(int)
    punch_by: dict = defaultdict(int)
    unparsed = []
    for srcname, src in (("part1", p1), ("part2", p2)):
        for mid, v in src.items():
            if mid.startswith("_"):
                continue
            for x in v.get("penalties", []):
                kind = x.get("kind", "")
                sent = x.get("sentence", "") or x.get("ctx", "")
                so = bool(x.get("shootout"))
                kt = keeper_team(sent)
                side = side_of(mid, kt) if kt else None
                if side is None:
                    unparsed.append((srcname, mid, kind, sent[:80]))
                    continue
                if "Saved" in kind:
                    if so:
                        sosave_by[(mid, side)] += 1
                    else:
                        pensave_by[(mid, side)] += 1
            for sent in v.get("punches", []):
                kt = None
                mm = re.search(r"\(([^()]+)\)", sent or "")
                if mm:
                    t = norm(mm.group(1))
                    kt = ALIAS.get(t, t)
                side = side_of(mid, kt) if kt else None
                if side is None:
                    unparsed.append((srcname, mid, "Punch", (sent or "")[:80]))
                    continue
                punch_by[(mid, side)] += 1

    print(f"regulation pen-saves: {sum(pensave_by.values())} | shootout saves: {sum(sosave_by.values())} | punches(GK): {sum(punch_by.values())}")
    print("unparsed events:", len(unparsed), unparsed[:3])

    with open(f"{WC}/goalkeeper_match_stats.csv", newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames
        rows = list(r)

    n_played_fill = n_bench_fill = n_side_unknown = 0
    for row in rows:
        played = row["minutes_played"] not in ("", "0")
        m = ms.get(row["match_id"])
        if m is None:
            n_side_unknown += 1
            continue
        home_n = teams[m["home_team_id"]]
        away_n = teams[m["away_team_id"]]
        if row["team"] == home_n:
            side = "home"
        elif row["team"] == away_n:
            side = "away"
        else:
            # Ten doi lech chuan hoa: bo qua thay vi gan nham phe.
            n_side_unknown += 1
            continue
        if played:
            key = (row["match_id"], side)
            if row["penalty_saves"] == "":
                row["penalty_saves"] = pensave_by.get(key, 0)
            if row["punches"] == "":
                row["punches"] = punch_by.get(key, 0)
            if "+espn.com" not in row["data_source"]:
                row["data_source"] += "+espn.com"
            n_played_fill += 1
        else:
            # never stepped on pitch -> all action counts are factual zeros
            for c in ("saves", "shots_faced", "goals_conceded_on_pitch", "clean_sheet",
                      "penalty_saves", "punches"):
                if row[c] == "":
                    row[c] = 0
            if "+derived-known-zero" not in row["data_source"]:
                row["data_source"] += "+derived-known-zero"
            n_bench_fill += 1

    with open(f"{WC}/goalkeeper_match_stats.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"played rows processed: {n_played_fill} | bench rows zero-filled: {n_bench_fill}"
          f" | side unknown (skipped): {n_side_unknown}")

    miss = {c: sum(1 for x in rows if str(x[c]).strip() == "") for c in cols}
    print("\nCON LAI TRONG:")
    for c, v in miss.items():
        if v:
            print(f"  {c}: {v}")
    if not any(miss.values()):
        print("  KHONG CO - file day du 100%")

    # shootout saves luong rieng, luu tham khao
    with open(f"{WC}/shootout_saves_reference.json", "w", encoding="utf-8") as f:
        json.dump({"shootout_saves_by_match_side": {f"{a}|{b}": v for (a, b), v in sosave_by.items()},
                   "note": "khong gan vao cot penalty_saves (chi tinh regulation)"},
                  f, indent=1)


if __name__ == "__main__":
    main()
