# -*- coding: utf-8 -*-
"""Minimal cleaning of core CSVs. Backups first; ML-derived files untouched."""
import csv
import json
import os
import re
import shutil
import unicodedata

BASE = "data/processed/csv"
BAK = "data/raw/csv_original"
os.makedirs(BAK, exist_ok=True)


def load(name):
    with open(f"{BASE}/{name}.csv", newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        return list(r), list(r.fieldnames)


def save(name, rows, cols):
    with open(f"{BASE}/{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


ALIAS = {"korearepublic": "southkorea"}
changes = []

# ---------- 0. backups ----------
for f in os.listdir(BASE):
    if f.endswith(".csv") and not os.path.exists(f"{BAK}/{f}"):
        shutil.copy2(f"{BASE}/{f}", f"{BAK}/{f}")
print("backup ->", BAK, len(os.listdir(BAK)), "files")

# ---------- 1. tournament_stages.is_knockout True/False -> 1/0 ----------
rows, cols = load("tournament_stages")
MAP = {"True": 1, "False": 0}
n = sum(1 for r in rows if r["is_knockout"] in MAP)
for r in rows:
    if r["is_knockout"] in MAP:
        r["is_knockout"] = MAP[r["is_knockout"]]
save("tournament_stages", rows, cols)
changes.append(f"tournament_stages.is_knockout: {n} values True/False -> 1/0")

# ---------- 2. kickoff_time_utc true UTC from FIFA calendar ----------
cal = json.load(open("data/raw/fifa/calendar.json", encoding="utf-8"))
teams_rows, _ = load("teams")
tid2name = {r["team_id"]: r["team_name"] for r in teams_rows}

def name_key(s):
    k = norm(s)
    return ALIAS.get(k, k)

pair_to_cal = {}
for m in cal:
    h = name_key(m["Home"]["TeamName"][0]["Description"])
    a = name_key(m["Away"]["TeamName"][0]["Description"])
    pair_to_cal.setdefault(frozenset((h, a)), []).append(m)

def find_fifa(lm):
    if "home_team_id" in lm:
        h = name_key(tid2name[lm["home_team_id"]])
        a = name_key(tid2name[lm["away_team_id"]])
    else:
        h = name_key(lm["home_team_name"])
        a = name_key(lm["away_team_name"])
    cands = pair_to_cal.get(frozenset((h, a)), [])
    if len(cands) == 1:
        return cands[0]
    best, bd = None, 99
    for c in cands:
        d = abs((int(c["Date"][8:10]) - int(lm["date"][8:10]))) % 28
        if d < bd:
            best, bd = c, d
    return best

for fname in ("matches", "matches_detailed"):
    rows, cols = load(fname)
    n_t = n_d = 0
    for lm in rows:
        fm = find_fifa(lm)
        if fm is None:
            continue
        utc_d, utc_t = fm["Date"][:10], fm["Date"][11:16]
        if lm["kickoff_time_utc"] != utc_t:
            lm["kickoff_time_utc"] = utc_t
            n_t += 1
        if lm["date"] != utc_d:
            lm["date"] = utc_d
            n_d += 1
    save(fname, rows, cols)
    changes.append(f"{fname}: {n_t}/104 kickoff_time_utc + {n_d}/104 date corrected to true UTC (api.fifa.com)")

print("\n".join(changes))
