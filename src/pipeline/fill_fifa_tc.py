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
import datetime as dt
import re
import unicodedata
from collections import defaultdict

TC = "data/raw/fifa_training_centre/data/csv"
WC = "data/processed/wc2026_player_match"
ALIAS = {"korearepublic": "southkorea", "unitedstates": "usa",
         "bosniaherzegovina": "bosniaandherzegovina", "capeverde": "caboverde",
         "drcongo": "congodr", "ivorycoast": "cotedivoire"}


def load(p):
    """Doc CSV tra ve list dict (giu encoding BOM)."""
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def norm(s):
    """Chuan hoa ten ve chu thuong khong dau de join."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]", "", s.lower())


def alias_key(name):
    """Ap alias đội tuyển, fallback ve norm goc."""
    n = norm(name)
    return ALIAS.get(n, n)


MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}


def tc_date_iso(s):
    """'11 June 2026' -> '2026-06-11'."""
    d, mon, y = s.split()
    return f"{y}-{MONTHS[mon]:02d}-{int(d):02d}"


def date_gap_days(a_iso, b_iso):
    """Khoang cach ngay; None neu parse loi (fallback o caller)."""
    try:
        a = dt.date.fromisoformat(a_iso[:10])
        b = dt.date.fromisoformat(b_iso[:10])
        return abs((a - b).days)
    except (ValueError, TypeError):
        return None


def mn_of(tc_match_id):
    """'2026-M001-...' -> '1'; None neu format la (bo qua thay vi crash)."""
    m = re.match(r"2026-M(\d{3})-", str(tc_match_id))
    return str(int(m.group(1))) if m else None


def put(row, filled, col, val):
    """Dien o trong; tra True neu co dien (dem vao filled)."""
    if row.get(col) == "" and val not in (None, ""):
        sv = str(val)
        if col == "pass_accuracy":
            sv = sv.replace("%", "")
        row[col] = sv
        filled[col] += 1
        return True
    return False


def main():
    """Map tc->local, tong hop attempts, dien o trong PMS."""
    ms_local = {r["match_id"]: r for r in load("data/processed/csv/matches.csv")}
    teams = {r["team_id"]: r["team_name"] for r in load("data/processed/csv/teams.csv")}
    tc_matches = load(f"{TC}/matches.csv")

    # ---- map tc -> local via team-pair + nearest date ----
    pair2locals = defaultdict(list)
    for lid, lm in ms_local.items():
        h = alias_key(teams[lm["home_team_id"]])
        a = alias_key(teams[lm["away_team_id"]])
        pair2locals[frozenset((h, a))].append(lid)

    tcnum2local = {}
    used = set()
    for tcm in tc_matches:
        mn = str(int(tcm["match_number"]))
        hkey = alias_key(tcm["home_team"])
        akey = alias_key(tcm["away_team"])
        cands = [lid for lid in pair2locals.get(frozenset((hkey, akey)), []) if lid not in used]
        if not cands:
            continue
        if len(cands) == 1:
            lid = cands[0]
        else:
            d_iso = tc_date_iso(tcm["date"])

            def daydiff(lid):
                gap = date_gap_days(ms_local[lid]["date"], d_iso)
                if gap is not None:
                    return gap
                lm = ms_local[lid]
                return abs((int(lm["date"][8:10]) - int(d_iso[8:10])) % 28)

            lid = min(cands, key=daydiff)
        used.add(lid)
        tcnum2local[mn] = lid
    print(f"mapped tc->local: {len(tcnum2local)}/104")
    assert len(tcnum2local) == 104, "match mapping incomplete"

    local2mn = {lid: mn for mn, lid in tcnum2local.items()}

    # ---- attempts aggregation: shots off target & own-blocked shots ----
    att_off: dict = defaultdict(int)
    att_blk: dict = defaultdict(int)
    skipped_attempts = 0
    for a in load(f"{TC}/attempts_at_goal.csv"):
        mn = mn_of(a["match_id"])
        if mn is None:
            skipped_attempts += 1
            continue
        key = (mn, alias_key(a["team"]), str(a["shirt_number"]))
        oc = a["outcome"]
        if oc.startswith("Deflected Off Target") or oc == "Off Target":
            att_off[key] += 1
        elif oc == "Incomplete - Blocked":
            att_blk[key] += 1

    oop = {}
    for r in load(f"{TC}/player_out_of_possession.csv"):
        mn = mn_of(r["match_id"])
        if mn is None:
            continue
        oop[(mn, alias_key(r["team"]), str(r["shirt_number"]))] = r
    inp = {}
    for r in load(f"{TC}/player_in_possession_distributions.csv"):
        mn = mn_of(r["match_id"])
        if mn is None:
            continue
        inp[(mn, alias_key(r["team"]), str(r["shirt_number"]))] = r
    print(f"tc rows: oop={len(oop)} inp={len(inp)} (skipped bad ids: {skipped_attempts})")

    # ---- apply ----
    PMS = f"{WC}/player_match_stats.csv"
    with open(PMS, newline="", encoding="utf-8-sig") as f:
        r_ = csv.DictReader(f)
        cols = r_.fieldnames
        rows = list(r_)

    filled: dict = defaultdict(int)
    touched_src_rows = 0
    unmatched_played = []
    skipped_rows = 0
    for row in rows:
        if row["minutes_played"] in ("", "0"):
            continue
        m = ms_local.get(row["match_id"])
        mn = local2mn.get(row["match_id"])
        if m is None or mn is None:
            skipped_rows += 1
            continue
        side_team = teams[m["home_team_id"]] if row["home_or_away"] == "home" else teams[m["away_team_id"]]
        key = (mn, alias_key(side_team), str(row["shirt_number"]))
        src_o, src_i = oop.get(key), inp.get(key)
        if src_o is None and src_i is None:
            unmatched_played.append(key)
            continue

        row_touched = False
        if src_i:
            row_touched |= bool(put(row, filled, "passes", src_i["passes_attempted"]))
            row_touched |= bool(put(row, filled, "accurate_passes", src_i["passes_completed"]))
            row_touched |= bool(put(row, filled, "pass_accuracy", src_i["pass_completion_pct"]))
            row_touched |= bool(put(row, filled, "crosses", src_i["crosses_attempted"]))
            row_touched |= bool(put(row, filled, "accurate_crosses", src_i["crosses_completed"]))
            row_touched |= bool(put(row, filled, "dribbles_attempted", src_i["take_ons"]))
        if src_o:
            parts = re.split(r"\s*/\s*", src_o["tackles_made_won"])
            made = parts[0].strip() if parts else ""
            won = parts[1].strip() if len(parts) > 1 else ""
            row_touched |= bool(put(row, filled, "tackles", made))
            row_touched |= bool(put(row, filled, "tackles_won", won))
            row_touched |= bool(put(row, filled, "interceptions", src_o["interceptions"]))
            row_touched |= bool(put(row, filled, "clearances", src_o["clearances"]))
            row_touched |= bool(put(row, filled, "blocks", src_o["blocks"]))
            row_touched |= bool(put(row, filled, "recoveries", src_o["possession_regains"]))
            row_touched |= bool(put(row, filled, "aerial_duels_won", src_o["duels_won_aerial"]))
            try:
                dw = int(src_o["duels_won_aerial"] or 0) + int(src_o["duels_won_physical"] or 0)
                row_touched |= bool(put(row, filled, "duels_won", str(dw)))
            except (ValueError, TypeError):
                print(f"  skip duels_won {key}: {src_o.get('duels_won_aerial')}/{src_o.get('duels_won_physical')}")
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
    print(f"\nrows touched: {touched_src_rows} | played rows unmatched trong FIFA TC: {len(unmatched_played)}"
          f" | skipped rows: {skipped_rows}")
    for u in unmatched_played[:10]:
        print("  ", u)


if __name__ == "__main__":
    main()
