# -*- coding: utf-8 -*-
"""Read-only audit of data/processed/csv - no modifications."""
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict

BASE = "data/processed/csv"
FILES = ["match_events", "match_lineups", "match_prediction_features",
         "match_prediction_features_X", "match_prediction_targets_y",
         "match_team_stats", "matches", "matches_detailed", "player_stats",
         "squads_and_players", "teams", "tournament_stages", "venues"]


def load(name):
    with open(f"{BASE}/{name}.csv", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


D = {n: load(n) for n in FILES}
F = {}

# ---------- 1. per-file schema ----------
print("=" * 70)
for n, rows in D.items():
    cols = list(rows[0].keys()) if rows else []
    def kind(vals):
        vals = [v for v in vals if v != ""]
        if not vals:
            return "empty"
        if all(re.fullmatch(r"-?\d+", v) for v in vals):
            return "int"
        if all(re.fullmatch(r"-?\d*\.\d+", v) for v in vals):
            return "float"
        if all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) for v in vals):
            return "date"
        return "text"
    dt = {c: kind([r[c] for r in rows]) for c in cols}
    nulls = {c: sum(1 for r in rows if r[c] == "") for c in cols}
    nulls = {c: v for c, v in nulls.items() if v}
    F[n] = {"rows": len(rows), "cols": list(cols), "dtypes": dt,
            "nulls": nulls}
    print(f"\n[{n}] rows={len(rows)}")
    print("  cols:", ", ".join(f"{c}:{dt[c]}" for c in cols))
    if nulls:
        print("  nulls:", {c: f"{v}({100*v//max(1,len(rows))}%)" for c, v in nulls.items()})

# ---------- 2. PK / dup checks ----------
print("\n" + "=" * 70)
def dupcheck(name, key):
    rows = D[name]
    cnt = Counter(tuple(r[k] for k in key) for r in rows)
    dups = {k: c for k, c in cnt.items() if c > 1}
    print(f"PK {name}{tuple(key)}: {'UNIQUE OK' if not dups else 'DUP x'+str(len(dups))+' e.g.'+str(list(dups)[:3])}")
    return dups

dupcheck("teams", ["team_id"])
dupcheck("tournament_stages", ["stage_id"])
dupcheck("venues", ["venue_id"])
dupcheck("squads_and_players", ["player_id"])
dupcheck("player_stats", ["player_id"])
dupcheck("matches", ["match_id"])
dupcheck("match_lineups", ["lineup_id"])
dupcheck("match_lineups", ["match_id", "player_id"])
dupcheck("match_events", ["event_id"])
dupcheck("match_team_stats", ["match_id", "team_id"])
dupcheck("match_prediction_features", ["match_id"])
dupcheck("match_prediction_features_X", ["match_id"])
dupcheck("match_prediction_targets_y", ["match_id"])

# duplicate matches by (home,away,date)
mm = Counter((r["home_team_id"], r["away_team_id"], r["date"]) for r in D["matches"])
d = [k for k, c in mm.items() if c > 1]
print("matches dup (home,away,date):", d or "none")

# ---------- 3. FK checks ----------
print("\n" + "=" * 70)
team_ids = {r["team_id"] for r in D["teams"]}
stage_ids = {r["stage_id"] for r in D["tournament_stages"]}
venue_ids = {r["venue_id"] for r in D["venues"]}
player_ids = {r["player_id"] for r in D["squads_and_players"]}
match_ids = {r["match_id"] for r in D["matches"]}

def fk(child, col, parent_ids, pname):
    bad = sorted({r[col] for r in D[child] if r[col] not in parent_ids})
    print(f"FK {child}.{col} -> {pname}: {'OK' if not bad else 'VIOLATIONS '+str(bad[:8])}")
    return bad

fk("matches", "home_team_id", team_ids, "teams")
fk("matches", "away_team_id", team_ids, "teams")
fk("matches", "stage_id", stage_ids, "stages")
fk("matches", "venue_id", venue_ids, "venues")
fk("squads_and_players", "team_id", team_ids, "teams")
fk("player_stats", "player_id", player_ids, "squads")
fk("player_stats", "team_id", team_ids, "teams")
fk("match_lineups", "match_id", match_ids, "matches")
fk("match_lineups", "player_id", player_ids, "squads")
fk("match_lineups", "team_id", team_ids, "teams")
fk("match_events", "match_id", match_ids, "matches")
fk("match_events", "team_id", team_ids, "teams")
fk("match_events", "player_id", player_ids, "squads")
fk("match_team_stats", "match_id", match_ids, "matches")
fk("match_team_stats", "team_id", team_ids, "teams")
fk("match_prediction_features", "match_id", match_ids, "matches")
fk("match_prediction_features", "home_team_id", team_ids, "teams")
fk("match_prediction_features", "away_team_id", team_ids, "teams")
fk("match_prediction_features", "stage_id", stage_ids, "stages")
fk("match_prediction_features", "venue_id", venue_ids, "venues")

# matches.player_of_the_match_id -> squads?
potm_bad = sorted({r["player_of_the_match_id"] for r in D["matches"]
                   if r["player_of_the_match_id"] and r["player_of_the_match_id"] not in player_ids})
print("FK matches.player_of_the_match_id -> squads:", potm_bad or "OK")

# coverage: every match present in child tables?
for child in ("match_lineups", "match_events", "match_team_stats", "matches_detailed"):
    cov = {r["match_id"] for r in D[child]}
    miss = sorted(match_ids - cov, key=int)
    extra = sorted(cov - match_ids, key=int)
    print(f"coverage matches->{child}: missing={len(miss)} extra={len(extra)}")

# ---------- 4. domain / format checks ----------
print("\n" + "=" * 70)
print("positions squads:", dict(Counter(r["position"] for r in D["squads_and_players"])))
print("positions player_stats:", dict(Counter(r["position"] for r in D["player_stats"])))
print("positions lineups:", dict(Counter(r["tactical_position"] for r in D["match_lineups"])))
print("booleans stages.is_knockout:", dict(Counter(r["is_knockout"] for r in D["tournament_stages"])))
print("booleans lineups.is_starting_xi:", dict(Counter(r["is_starting_xi"] for r in D["match_lineups"])))
print("status:", dict(Counter(r["status"] for r in D["matches"])))
print("result_type:", dict(Counter(r["result_type"] for r in D["matches"])))
print("data_source player_stats:", dict(Counter(r["data_source"] for r in D["player_stats"])))
print("date fmt matches ok:", all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]) for r in D["matches"]))
print("kickoff fmt sample:", sorted({r["kickoff_time_utc"] for r in D["matches"]})[:5])

# ---------- 5. football logic ----------
print("\n" + "=" * 70)
same_team = [r["match_id"] for r in D["matches"] if r["home_team_id"] == r["away_team_id"]]
print("home==away:", same_team or "none")
neg = [(r["match_id"]) for r in D["matches"] if int(r["home_score"]) < 0 or int(r["away_score"]) < 0]
print("negative scores:", neg or "none")
bad_sot = [r["player_id"] for r in D["player_stats"]
           if r["shots_on_target"] and r["shots"] and int(r["shots_on_target"]) > int(r["shots"])]
print("player SoT>Shots:", bad_sot or "none")
bad_sot_t = [r["match_id"] for r in D["match_team_stats"]
             if int(r["shots_on_target"]) > int(r["total_shots"])]
print("team SoT>Shots:", len(bad_sot_t), bad_sot_t[:5])
mins_bad = [r["lineup_id"] for r in D["match_lineups"] if not (0 <= int(r["minutes_played"]) <= 130)]
print("lineup minutes out of range:", mins_bad[:5] or "none")
ev_min_bad = [r["event_id"] for r in D["match_events"] if not (0 <= int(r["minute"]) <= 130)]
print("event minutes out of range:", ev_min_bad[:5] or "none")

# starting XI per team-match
xi = Counter((r["match_id"], r["team_id"]) for r in D["match_lineups"] if r["is_starting_xi"] == "1")
odd_xi = {k: c for k, c in xi.items() if c != 11}
print("team-matches with XI != 11:", odd_xi or "none", f"(total team-matches={len(xi)})")

# player for both teams in same match
mt = defaultdict(set)
for r in D["match_lineups"]:
    mt[(r["match_id"], r["player_id"])].add(r["team_id"])
both = [k for k, v in mt.items() if len(v) > 1]
print("players appearing for both teams:", both or "none")

# event player belongs to event team (per lineup)
lt = {(r["match_id"], r["player_id"]): r["team_id"] for r in D["match_lineups"]}
wrong_team = [e["event_id"] for e in D["match_events"]
              if lt.get((e["match_id"], e["player_id"])) not in (None, e["team_id"])]
print("events where player team != event team:", wrong_team[:5] or "none", f"(n={len(wrong_team)})")

# goals+assists per events vs score
evg = Counter()
oga = Counter()
for e in D["match_events"]:
    mid = int(e["match_id"])
    m = next(x for x in D["matches"] if x["match_id"] == e["match_id"])
    if e["event_type"] == "Goal":
        evg[mid] += 1 if e["team_id"] == m["home_team_id"] else 0
        if e["team_id"] == m["away_team_id"]:
            evg[mid] += 0
        # count properly below
score_check_fail = []
by_match = defaultdict(lambda: [0, 0])
mid2m = {r["match_id"]: r for r in D["matches"]}
for e in D["match_events"]:
    m = mid2m[e["match_id"]]
    home_is = e["team_id"] == m["home_team_id"]
    if e["event_type"] == "Goal":
        by_match[e["match_id"]][0 if home_is else 1] += 1
    elif e["event_type"] == "Own Goal":
        by_match[e["match_id"]][1 if home_is else 0] += 1
for mid, (h, a) in by_match.items():
    m = mid2m[mid]
    if h != int(m["home_score"]) or a != int(m["away_score"]):
        score_check_fail.append((mid, h, a, m["home_score"], m["away_score"]))
print("events-goals vs score mismatches:", len(score_check_fail), score_check_fail[:5])

# player_stats totals vs events totals (goals/cards)
ps_goals = {r["player_id"]: int(r["goals"] or 0) for r in D["player_stats"]}
ev_goals = Counter(e["player_id"] for e in D["match_events"] if e["event_type"] == "Goal")
diff_g = [(p, ps_goals[p], ev_goals.get(p, 0)) for p in ev_goals
          if p and ps_goals.get(p) is not None and ps_goals[p] != ev_goals.get(p, 0)]
print("players whose event-goals != player_stats.goals:", len(diff_g), diff_g[:5])

# ---------- 6. mojibake scan ----------
print("\n" + "=" * 70)
MOJI = re.compile(r"[ÃÂ]|ï¿½|\ufffd|A\uFFFD")
for n, rows in D.items():
    hits = Counter()
    samples = []
    for r in rows:
        for c, v in r.items():
            if v and MOJI.search(v):
                hits[c] += 1
                if len(samples) < 3:
                    samples.append((c, v))
    if hits:
        print(f"{n}: SUSPECT ENCODING {dict(hits)} | e.g. {samples}")

# same normalized name different ids (squads)
def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]", "", s.lower())
nm = defaultdict(set)
for r in D["squads_and_players"]:
    nm[norm(r["player_name"])].add(r["player_id"])
coll = {k: v for k, v in nm.items() if k and len(v) > 1}
print("name collisions (different ids, same name):", len(coll))

json.dump(F, open("data/processed/audit_schema.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nsaved schema -> data/processed/audit_schema.json")
