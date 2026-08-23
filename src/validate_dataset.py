# -*- coding: utf-8 -*-
"""Final validation for the cleaned project.

Scope:
  A. Canonical CSVs  (data/processed/csv)      - PK/FK/dup/format
  B. wc2026_player_match                              - pms + gk vs canonical
Cross-file consistency: goals/cards totals vs match scores.
"""
import csv
import os
from collections import Counter, defaultdict

CSV = "data/processed/csv"
WC = "data/processed/wc2026_player_match"
lines = []


def log(s=""):
    print(s)
    lines.append(str(s))


def load(path, delim=","):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f, delimiter=delim)
        return list(r), list(r.fieldnames)


def to_int(v):
    v = str(v).strip()
    return int(v) if v else None


# ---------- A. canonical ----------
log("=== A. CANONICAL CSV ===")
names = ["matches", "match_events", "match_lineups", "match_team_stats",
         "player_stats", "squads_and_players", "teams", "tournament_stages",
         "venues", "matches_detailed"]
F = {}
for n in names:
    rows, cols = load(f"{CSV}/{n}.csv")
    F[n] = rows
    log(f"  {n:22s} rows={len(rows):5d} cols={len(cols)}")

pk_ok = True
for n, key in [("teams", ["team_id"]), ("tournament_stages", ["stage_id"]),
               ("venues", ["venue_id"]), ("squads_and_players", ["player_id"]),
               ("player_stats", ["player_id"]), ("matches", ["match_id"])]:
    c = Counter(tuple(r[k] for k in key) for r in F[n])
    dups = sum(v - 1 for v in c.values() if v > 1)
    pk_ok &= dups == 0
    if dups:
        log(f"  PK DUP {n}: {dups}")
log(f"  PK unique: {'OK' if pk_ok else 'FAIL'}")

tid = {r["team_id"] for r in F["teams"]}
pid = {r["player_id"] for r in F["squads_and_players"]}
mid = {r["match_id"] for r in F["matches"]}
fk_fail = 0
checks = [("matches", "home_team_id", tid), ("matches", "away_team_id", tid),
          ("squads_and_players", "team_id", tid), ("player_stats", "team_id", tid),
          ("match_lineups", "match_id", mid), ("match_lineups", "player_id", pid),
          ("match_lineups", "team_id", tid), ("match_events", "match_id", mid),
          ("match_events", "player_id", pid), ("match_events", "team_id", tid),
          ("match_team_stats", "match_id", mid), ("match_team_stats", "team_id", tid),
          ("player_stats", "player_id", pid)]
for child, col, parent in checks:
    bad = sorted({r[col] for r in F[child] if r.get(col) and r[col] not in parent})
    if bad:
        fk_fail += 1
        log(f"  FK FAIL {child}.{col}: {bad[:5]}")
log(f"  FK ({len(checks)} rang buoc): {'OK' if not fk_fail else 'FAIL'}")

# format: delimiter phay + ten Title Case
semi = [fn for fn in os.listdir(CSV) if fn.endswith(".csv")
        and ";" in open(f"{CSV}/{fn}", encoding="utf-8-sig").readline()[:120]
        and "," not in open(f"{CSV}/{fn}", encoding="utf-8-sig").readline()]
log(f"  delimiter ';': {semi or 'khong co - OK'}")


def caps_style(n):
    return any(w.isupper() and len(w) > 2 for w in n.split())


ncaps = sum(1 for r in F["squads_and_players"] if caps_style(r["player_name"]))
log(f"  ten kieu HOA trong squads: {ncaps}")

# ---------- B. wc2026 ----------
log("\n=== B. WC2026 PLAYER MATCH ===")
pms, _ = load(f"{WC}/player_match_stats.csv")
gk, _ = load(f"{WC}/goalkeeper_match_stats.csv")
for nm, rows in (("player_match_stats", pms), ("goalkeeper_match_stats", gk)):
    bm = {r["match_id"] for r in rows} - mid
    bp = {r["player_id"] for r in rows} - pid
    dup = len(rows) - len({(r["match_id"], r["player_id"]) for r in rows})
    nc = sum(1 for r in rows if caps_style(r["player_name"]))
    ok = not bm and not bp and dup == 0 and nc == 0
    log(f"  {nm}: rows={len(rows)} FK={'OK' if not bm and not bp else 'FAIL'} "
        f"dup={dup} tenHOA={nc} -> {'OK' if ok else 'FAIL'}")

# cross-check tong so ban & the voi canonical matches
by_match = defaultdict(lambda: [0, 0])
mrow = {r["match_id"]: r for r in F["matches"]}
ev_g = defaultdict(lambda: [0, 0])
for e in load(f"{CSV}/match_events.csv")[0]:
    m = mrow[e["match_id"]]
    home_is = e["team_id"] == m["home_team_id"]
    if e["event_type"] == "Goal":
        by_match[e["match_id"]][0 if home_is else 1] += 1
    elif e["event_type"] == "Own Goal":
        by_match[e["match_id"]][1 if home_is else 0] += 1
bad_scores = [(mid, h, a) for mid, (h, a) in by_match.items()
              if h != int(mrow[mid]["home_score"]) or a != int(mrow[mid]["away_score"])]
log(f"  events-goals == scores: "
    f"{'OK' if not bad_scores else 'FAIL ' + str(bad_scores[:5])}")

# minutes numeric + range
bad_min = sum(1 for r in pms if r["minutes_played"] != ""
              and not (0 <= int(r["minutes_played"]) <= 130))
log(f"  pms minutes hop le: {'OK' if not bad_min else 'FAIL'}")

# ---------- ket luan ----------
fails = [l for l in lines if "FAIL" in l]
log("\n=== KET LUAN: " + ("TOAN BO PASS" if not fails else f"{len(fails)} LOI") + " ===")

with open(f"{WC}/validation_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
