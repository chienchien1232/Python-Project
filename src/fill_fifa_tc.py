# -*- coding: utf-8 -*-
"""Phase A: fill player_match_stats missing columns from FIFA Training Centre
open data (source: training.fifa.com post-match reports; Kaggle mirror
heshamelalamy47/worldcup-2026-open-data).

Column mapping (documented):
  tackles            <- oop.tackles_made_won  left part  (made)
  tackles_won        <- oop.tackles_made_won  right part (won)
  interceptions      <- interceptions
  clearances         <- clearances
  blocks             <- blocks
  recoveries         <- possession_regains
  aerial_duels_won   <- duels_won_aerial
  duels_won          <- duels_won_aerial + duels_won_physical
  passes             <- inp.passes_attempted
  accurate_passes    <- passes_completed
  pass_accuracy      <- pass_completion_pct (no %)
  crosses            <- crosses_attempted
  accurate_crosses   <- crosses_completed
  dribbles_attempted <- take_ons
  shots_off_target / blocked_shots <- attempts_at_goal outcome buckets
Only EMPTY cells are filled; provenance appended to data_source.
"""
import csv
import re
import unicodedata
from collections import defaultdict

TC = "data/raw/fifa_training_centre/data/csv"
WC = "data/processed/wc2026_player_match"
ALIAS = {"korearepublic": "southkorea", "unitedstates": "usa",
         "bosniaherzegovina": "bosniaandherzegovina", "capeverde": "caboverde",
         "drcongo": "congodr", "ivorycoast": "cotedivoire"}


def load(p):
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]", "", s.lower())


def tkey(row_or_tuple_team):
    pass


ms_local = {r["match_id"]: r for r in load("data/processed/csv/matches.csv")}
teams = {r["team_id"]: r["team_name"] for r in load("data/processed/csv/teams.csv")}
tc_matches = load(f"{TC}/matches.csv")

# ---- map tc -> local via team-pair + nearest date ----
MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}


def tc_date_iso(s):
    d, mon, y = s.split()
    return f"{y}-{MONTHS[mon]:02d}-{int(d):02d}"


pair2locals = defaultdict(list)
for lid, lm in ms_local.items():
    h = ALIAS.get(norm(teams[lm["home_team_id"]]), norm(teams[lm["home_team_id"]]))
    a = ALIAS.get(norm(teams[lm["away_team_id"]]), norm(teams[lm["away_team_id"]]))
    pair2locals[frozenset((h, a))].append(lid)

tcnum2local = {}
used = set()
for tcm in tc_matches:
    mn = str(int(tcm["match_number"]))
    hkey = ALIAS.get(norm(tcm["home_team"]), norm(tcm["home_team"]))
    akey = ALIAS.get(norm(tcm["away_team"]), norm(tcm["away_team"]))
    cands = [lid for lid in pair2locals.get(frozenset((hkey, akey)), []) if lid not in used]
    if not cands:
        continue
    if len(cands) == 1:
        lid = cands[0]
    else:
        d_iso = tc_date_iso(tcm["date"])
        def daydiff(lid):
            lm = ms_local[lid]
            return abs((int(lm["date"][8:10]) - int(d_iso[8:10])) % 28)
        lid = min(cands, key=daydiff)
    used.add(lid)
    tcnum2local[mn] = lid
print(f"mapped tc->local: {len(tcnum2local)}/104")
assert len(tcnum2local) == 104, "match mapping incomplete"


def mn_of(tc_match_id):
    return str(int(re.match(r"2026-M(\d{3})-", tc_match_id).group(1)))


local2mn = {lid: mn for mn, lid in tcnum2local.items()}

# ---- attempts aggregation: shots off target & own-blocked shots ----
att_off = defaultdict(int)
att_blk = defaultdict(int)
for a in load(f"{TC}/attempts_at_goal.csv"):
    key = (mn_of(a["match_id"]),
           ALIAS.get(norm(a["team"]), norm(a["team"])),
           str(a["shirt_number"]))
    oc = a["outcome"]
    if oc.startswith("Deflected Off Target") or oc == "Off Target":
        att_off[key] += 1
    elif oc == "Incomplete - Blocked":
        att_blk[key] += 1

oop = {(mn_of(r["match_id"]), ALIAS.get(norm(r["team"]), norm(r["team"])), str(r["shirt_number"])): r
       for r in load(f"{TC}/player_out_of_possession.csv")}
inp = {(mn_of(r["match_id"]), ALIAS.get(norm(r["team"]), norm(r["team"])), str(r["shirt_number"])): r
       for r in load(f"{TC}/player_in_possession_distributions.csv")}
print(f"tc rows: oop={len(oop)} inp={len(inp)}")

# ---- apply ----
PMS = f"{WC}/player_match_stats.csv"
with open(PMS, newline="", encoding="utf-8-sig") as f:
    r_ = csv.DictReader(f)
    cols = r_.fieldnames
    rows = list(r_)

filled = defaultdict(int)
touched_src_rows = 0
unmatched_played = []
for row in rows:
    if row["minutes_played"] in ("", "0"):
        continue
    m = ms_local[row["match_id"]]
    mn = local2mn[row["match_id"]]
    side_team = teams[m["home_team_id"]] if row["home_or_away"] == "home" else teams[m["away_team_id"]]
    key = (mn, ALIAS.get(norm(side_team), norm(side_team)), str(row["shirt_number"]))
    src_o, src_i = oop.get(key), inp.get(key)
    if src_o is None and src_i is None:
        unmatched_played.append(key)
        continue

    row_touched = False

    def put(col, val):
        nonlocal_dummy = None
        global touched_src_rows
        if row[col] == "" and val not in (None, ""):
            sv = str(val)
            if col == "pass_accuracy":
                sv = sv.replace("%", "")
            row[col] = sv
            filled[col] += 1
            return True
        return False

    if src_i:
        row_touched |= bool(put("passes", src_i["passes_attempted"]))
        row_touched |= bool(put("accurate_passes", src_i["passes_completed"]))
        row_touched |= bool(put("pass_accuracy", src_i["pass_completion_pct"]))
        row_touched |= bool(put("crosses", src_i["crosses_attempted"]))
        row_touched |= bool(put("accurate_crosses", src_i["crosses_completed"]))
        row_touched |= bool(put("dribbles_attempted", src_i["take_ons"]))
    if src_o:
        parts = re.split(r"\s*/\s*", src_o["tackles_made_won"])
        made = parts[0].strip() if parts else ""
        won = parts[1].strip() if len(parts) > 1 else ""
        row_touched |= bool(put("tackles", made))
        row_touched |= bool(put("tackles_won", won))
        row_touched |= bool(put("interceptions", src_o["interceptions"]))
        row_touched |= bool(put("clearances", src_o["clearances"]))
        row_touched |= bool(put("blocks", src_o["blocks"]))
        row_touched |= bool(put("recoveries", src_o["possession_regains"]))
        row_touched |= bool(put("aerial_duels_won", src_o["duels_won_aerial"]))
        try:
            dw = int(src_o["duels_won_aerial"] or 0) + int(src_o["duels_won_physical"] or 0)
            row_touched |= bool(put("duels_won", str(dw)))
        except Exception:
            pass
    akey = (mn, key[1], str(row["shirt_number"]))
    if akey in att_off and row["shots_off_target"] == "":
        row["shots_off_target"] = att_off[akey]
        filled["shots_off_target"] += 1
        row_touched = True
    if akey in att_blk and row["blocked_shots"] == "":
        row["blocked_shots"] = att_blk[akey]
        filled["blocked_shots"] += 1
        row_touched = True
    if row_touched:
        touched_src_rows += 1
        if "+fifa-training-centre" not in row["data_source"]:
            row["data_source"] += "+fifa-training-centre"

with open(PMS, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

print("\ncells filled theo cot:")
for c, v in sorted(filled.items(), key=lambda kv: -kv[1]):
    print(f"  {c}: {v}")
print(f"\nrows touched: {touched_src_rows} | played rows unmatched trong FIFA TC: {len(unmatched_played)}")
for u in unmatched_played[:10]:
    print("  ", u)
