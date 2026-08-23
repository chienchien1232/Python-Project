# -*- coding: utf-8 -*-
"""Remap wc2026_player_match IDs to canonical data/processed/csv IDs.

Rule: data/processed/csv is the source of truth for ID schemes.
match_id already canonical (1-104); player_id remapped FIFA IdPlayer -> csv id.
Old FIFA id preserved only in players.csv as fifa_player_id.
Idempotent: files already using canonical ids are skipped.
"""
import csv
import json
import os
import re
import shutil
import unicodedata
from collections import defaultdict

WC = "data/processed/wc2026_player_match"
CSV = "data/processed/csv"
BAK = "data/raw/csv_original/wc2026_before_remap"
ALIAS_TEAM = {"korearepublic": "southkorea"}


def norm_tokens(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return frozenset(re.findall(r"[a-z0-9]+", s.lower()))


def team_key(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    k = re.sub(r"[^a-z]", "", s.lower())
    return ALIAS_TEAM.get(k, k)


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        return list(r), list(r.fieldnames)


def save(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


# ---------- backup ----------
os.makedirs(BAK, exist_ok=True)
for f_ in os.listdir(WC):
    src, dst = os.path.join(WC, f_), os.path.join(BAK, f_)
    if f_.endswith((".csv", ".json")) and not os.path.exists(dst):
        shutil.copy2(src, dst)
print("backup ->", BAK)

# ---------- canonical ----------
teams_rows, _ = load(f"{CSV}/teams.csv")
tname_by_id = {r["team_id"]: r["team_name"] for r in teams_rows}
tkey_to_tid = {team_key(v): k for k, v in tname_by_id.items()}
squads, _ = load(f"{CSV}/squads_and_players.csv")
canon_by_team = defaultdict(list)          # tid -> [(local_pid, name)]
for r in squads:
    canon_by_team[r["team_id"]].append((r["player_id"], r["player_name"]))
all_canon = {r["player_id"] for r in squads}
canon_pos = {(r["team_id"], r["player_id"]): r["position"] for r in squads}

# ---------- wc2026 side ----------
pms, pms_cols = load(f"{WC}/player_match_stats.csv")
all_canon_set = all_canon


def _is_canon(rows):
    return all((not r.get("player_id")) or r["player_id"] in all_canon_set for r in rows)


# if current file already remapped, recover original FIFA-side rows from backup
if _is_canon(pms):
    src_pms, _ = load(f"{BAK}/player_match_stats.csv")
    print("pms already canonical -> rebuilding mapping from backup")
else:
    src_pms = pms

by_team_fifa = defaultdict(lambda: defaultdict(list))  # tkey -> fifa_pid -> [tokensets]
for r in src_pms:
    by_team_fifa[team_key(r["player_team"])][r["player_id"]].append(norm_tokens(r["player_name"]))
pos_fifa = defaultdict(set)
for r in src_pms:
    pos_fifa[r["player_id"]].add(r["position"])

mapping, problems, conflicts = {}, [], []

for tkey, fifa_map in by_team_fifa.items():
    tid = tkey_to_tid.get(tkey)
    if tid is None:
        problems.append(f"unknown team key: {tkey}")
        continue
    canon = [(lpid, lname, norm_tokens(lname), canon_pos[(tid, lpid)])
             for lpid, lname in canon_by_team[tid]]
    used_f, used_l = set(), set()
    pairs = []
    for fpid, tl in fifa_map.items():
        ftoks = frozenset().union(*tl)
        for lpid, _ln, ct, _p in canon:
            inter = len(ftoks & ct)
            if inter:
                pairs.append((inter * 10 - len(ftoks | ct), fpid, lpid))
    pairs.sort(reverse=True)
    for _s, fpid, lpid in pairs:
        if fpid not in used_f and lpid not in used_l:
            mapping[fpid] = lpid
            used_f.add(fpid)
            used_l.add(lpid)

    # ---- pass2: leftovers by position ----
    left_f = [p for p in fifa_map if p not in used_f]
    left_l = [x for x in canon if x[0] not in used_l]
    for fp in sorted(left_f):
        cands = [x[0] for x in left_l if x[3] in pos_fifa[fp]]
        if len(cands) == 1:
            choice, why = cands[0], "by position"
        elif len(cands) > 1:
            cands.sort(key=int)
            choice, why = cands[0], f"DETERMINISTIC among {cands}"
        elif left_l:
            choice = sorted(left_l, key=lambda x: int(x[0]))[0][0]
            why = "ELIMINATION - IDENTITY CONFLICT"
            conflicts.append({"team": tkey, "fifa_player_id": fp,
                              "csv_player_id": choice})
        else:
            problems.append(f"{tkey}: cannot place {fp}; no leftover")
            continue
        mapping[fp] = choice
        used_f.add(fp)
        used_l = [x for x in left_l if x[0] != choice]
        left_l = [x for x in left_l if x[0] != choice]
        print(f"[pass2] {tkey}: {fp} -> {choice} ({why})")

if problems:
    print("PROBLEMS:", problems)
assert len(mapping) == 1248, f"incomplete mapping {len(mapping)}/1248"
print(f"mapped {len(mapping)}/1248")

with open(f"{WC}/id_mapping_fifa_to_csv.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=1, sort_keys=True)
with open(f"{WC}/id_conflicts.json", "w", encoding="utf-8") as f:
    json.dump(conflicts, f, indent=1)


def already_canonical(rows):
    return all((not r.get("player_id")) or r["player_id"] in all_canon_set for r in rows)


# ---------- rewrite ----------
if not already_canonical(pms):
    for r in pms:
        r["player_id"] = mapping[r["player_id"]]
    save(f"{WC}/player_match_stats.csv", pms, pms_cols)
else:
    print("player_match_stats: already canonical")

gk, gk_cols = load(f"{WC}/goalkeeper_match_stats.csv")
if not already_canonical(gk):
    for r in gk:
        r["player_id"] = mapping[r["player_id"]]
    save(f"{WC}/goalkeeper_match_stats.csv", gk, gk_cols)
else:
    print("goalkeeper_match_stats: already canonical")

ev, ev_cols = load(f"{WC}/match_events.csv")
if not already_canonical(ev):
    for r in ev:
        if r["player_id"]:
            r["player_id"] = mapping[r["player_id"]]
        if r["related_player_id"]:
            r["related_player_id"] = mapping[r["related_player_id"]]
    save(f"{WC}/match_events.csv", ev, ev_cols)
else:
    print("match_events: already canonical")

pl, _plcols = load(f"{WC}/players.csv")
if pl and pl[0].get("fifa_player_id"):
    print("players: already canonical")
else:
    base_cols = [c for c in _plcols if c != "player_id"]
    new_cols = ["player_id", "fifa_player_id"] + base_cols
    new_rows = []
    for r in pl:
        nr = {"player_id": mapping[r["player_id"]], "fifa_player_id": r["player_id"]}
        for c in base_cols:
            nr[c] = r[c]
        new_rows.append(nr)
    save(f"{WC}/players.csv", new_rows, new_cols)

# ---------- validation ----------
print("\n=== VALIDATION ===")
allok = True
for fname, fields in (("player_match_stats.csv", ["player_id"]),
                      ("goalkeeper_match_stats.csv", ["player_id"]),
                      ("match_events.csv", ["player_id", "related_player_id"]),
                      ("players.csv", ["player_id"])):
    rows_, _ = load(f"{WC}/{fname}")
    bad = {r[fld] for r in rows_ for fld in fields if r[fld] and r[fld] not in all_canon}
    dup = len(rows_) - len({(r.get("match_id"), r.get("player_id")) for r in rows_}) \
        if "match_id" in rows_[0] else 0
    ok = not bad and dup == 0
    allok &= ok
    print(f"{fname}: {'OK' if ok else 'FAIL bad=' + str(list(bad)[:5])} | rows={len(rows_)} dup={dup}")

n_ev_ref = sum(1 for r in ev if r["related_player_id"])
print(f"\n{'ALL IDS CANONICAL - DONE' if allok else 'FAILED'} | events related_player_id remapped: {n_ev_ref}")
