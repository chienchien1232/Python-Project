# -*- coding: utf-8 -*-
"""Build World Cup 2026 player x match datasets from FIFA official API raw dumps.

Sources:
  - data/raw/fifa/calendar.json        : api.fifa.com/api/v3/calendar/matches (idCompetition=17, idSeason=285023)
  - data/raw/fifa/match_<id>.json      : api.fifa.com/api/v3/live/football/{comp}/{season}/{stage}/{match}
  - data/processed/csv/match_events.csv: pre-existing Sofascore-sourced events (assists / VAR / shootout misses)

Conventions (documented, deterministic derivations - no fabricated values):
  - effective_minute = base minute + added-time marker (e.g. 90'+3' -> 93)
  - minutes_played   : starter [0 -> exit]; substitute [entry -> exit]; exit = sub-off /
                       red-card / full time (90 regular, 120 after extra time).
                       Extra-time stoppage not published by source -> treated as 0.
  - clean_sheet (GK) : played > 0 min and opponent scored 0.
"""
import csv
import glob
import json
import os
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict

RAW = "data/raw/fifa"
LOCAL = "data/processed/csv"
OUT = "data/processed/wc2026_player_match"
os.makedirs(OUT, exist_ok=True)

STAGE_MAP = {
    "First Stage": "Group Stage",
    "Round of 32": "Round of 32",
    "Round of 16": "Round of 16",
    "Quarter-final": "Quarter-final",
    "Semi-final": "Semi-final",
    "Bronze final": "Third-place",
    "Final": "Final",
}
POS_MAP = {0: "GK", 1: "DEF", 2: "MID", 3: "FWD"}
CARD_MAP = {1: "Yellow Card", 2: "Red Card", 3: "Second Yellow"}

NULL_COLS_ADVANCED = [
    "shots", "shots_on_target", "shots_off_target", "blocked_shots", "big_chances",
    "big_chances_missed", "touches", "touches_in_opponent_box", "passes",
    "accurate_passes", "pass_accuracy", "key_passes", "crosses", "accurate_crosses",
    "long_balls", "accurate_long_balls", "through_balls", "chances_created",
    "xg", "xa", "tackles", "tackles_won", "interceptions", "clearances", "blocks",
    "recoveries", "duels", "duels_won", "aerial_duels", "aerial_duels_won",
    "dribbles_attempted", "successful_dribbles", "dispossessed", "possession_lost",
    "fouls_won", "errors_leading_to_shot", "errors_leading_to_goal",
]


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


ALIAS = {"korearepublic": "southkorea"}


def name_key(s):
    k = norm(s)
    return ALIAS.get(k, k)


def tokens(s):
    """Tokenize a human-readable string into lowercase alnum word tokens."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def desc(localized):
    if isinstance(localized, list):
        return localized[0]["Description"] if localized else ""
    return localized or ""


def parse_minute(mstr):
    """Return (base, added, effective). effective=None when unknown.

    FIFA minute formats: "9'", "90'+4'" (added-time marker after apostrophe).
    """
    if mstr is None:
        return None, None, None
    s = str(mstr).strip().strip("'")
    m = re.fullmatch(r"(\d+)'?\+(\d+)", s)
    if m:
        b, a = int(m.group(1)), int(m.group(2))
        return b, a, b + a
    m = re.fullmatch(r"(\d+)", s)
    if m:
        return int(m.group(1)), None, int(m.group(1))
    return None, None, None


def load_local_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    # ---------- 1. load raw ----------
    cal = json.load(open(f"{RAW}/calendar.json", encoding="utf-8"))
    details = {}
    for fp in glob.glob(f"{RAW}/match_*.json"):
        d = json.load(open(fp, encoding="utf-8"))
        details[d["IdMatch"]] = d
    print(f"calendar={len(cal)} details={len(details)}")

    lmatches = load_local_csv(f"{LOCAL}/matches.csv")
    levents = load_local_csv(f"{LOCAL}/match_events.csv")
    lsquads = load_local_csv(f"{LOCAL}/squads_and_players.csv")
    lvenues = load_local_csv(f"{LOCAL}/venues.csv")
    # FIFA stadium name is a prefix of the local venue name, e.g.
    # "Mexico City Stadium" in "Mexico City Stadium (Estadio Azteca)"
    venue_lookup = {}
    venue_lookup_full = {}
    for v in lvenues:
        venue_lookup[norm(v["stadium_name"].split("(")[0])] = v
        venue_lookup_full[norm(v["stadium_name"])] = v

    # ---------- 2. map fifa id -> local match_id (team pair + nearest date) ----------
    pair_to_locals = defaultdict(list)
    for lm in lmatches:
        h = name_key(next(t for t in [None]))  # placeholder replaced below
    tid2name = {}
    # build local team id->name from squads file fallback teams.csv
    teams_rows = load_local_csv(f"{LOCAL}/teams.csv")
    tid2name = {r["team_id"]: r["team_name"] for r in teams_rows}

    for lm in lmatches:
        h = name_key(tid2name[lm["home_team_id"]])
        a = name_key(tid2name[lm["away_team_id"]])
        pair_to_locals[frozenset((h, a))].append(lm)

    id2local = {}
    used_local = set()
    unmatched = []
    for i, m in enumerate(cal):
        h = name_key(desc(m["Home"]["TeamName"]))
        a = name_key(desc(m["Away"]["TeamName"]))
        cands = pair_to_locals.get(frozenset((h, a)), [])
        cands = [c for c in cands if c["match_id"] not in used_local]
        if not cands:
            unmatched.append((i, h, a))
            continue
        if len(cands) == 1:
            pick = cands[0]
        else:
            d_iso = m["Date"][:10]
            pick = min(cands, key=lambda c: abs((int(c["date"][8:10]) - int(d_iso[8:10]))))
        used_local.add(pick["match_id"])
        id2local[m["IdMatch"]] = int(pick["match_id"])
    print(f"mapped={len(id2local)} unmatched={len(unmatched)}")
    assert len(id2local) == 104, f"mapping incomplete: {unmatched}"

    # ---------- 3. matches.csv ----------
    matches_out = []
    meta = {}
    for m in cal:
        mid = m["IdMatch"]
        lid = id2local[mid]
        stage_raw = desc(m["StageName"])
        stadium = m.get("Stadium") or {}
        venue = desc(stadium.get("Name")) or None
        city = desc(stadium.get("CityName")) or stadium.get("City") or None
        country = desc(stadium.get("CountryName")) or None
        vref = venue_lookup.get(norm((venue or "").split("(")[0]))
        if not vref and venue:
            vn = norm(venue)
            for k, v in venue_lookup.items():
                if vn and (vn in k or k in vn):
                    vref = v
                    break
        if not vref and venue:
            vt = tokens(venue)
            for v in lvenues:
                kt = tokens(v["stadium_name"])
                if vt and (vt.issubset(kt) or kt.issubset(vt)):
                    vref = v
                    break
        if vref:
            city = city or vref["city"]
            country = country or {"MEX": "Mexico", "USA": "United States", "CAN": "Canada"}.get(
                vref["country"], vref["country"])
        date_utc = m["Date"]
        rt = m.get("ResultType")
        result_type = {1: "Regular", 2: "AET", 3: "Penalty Shootout"}.get(rt)
        hs = m["Home"].get("Score")
        as_ = m["Away"].get("Score")
        officials = m.get("Officials") or []
        referee = next((desc(o.get("Name")) for o in officials if o.get("OfficialType") == 1), None)
        meta[mid] = {
            "lid": lid, "stage": STAGE_MAP[stage_raw], "group": desc(m.get("GroupName")) or None,
            "home_name": desc(m["Home"]["TeamName"]), "away_name": desc(m["Away"]["TeamName"]),
            "home_id": m["Home"]["IdTeam"], "away_id": m["Away"]["IdTeam"],
            "home_score": hs, "away_score": as_,
            "home_pen": m.get("HomeTeamPenaltyScore"), "away_pen": m.get("AwayTeamPenaltyScore"),
        }
        matches_out.append({
            "match_id": lid,
            "competition": "FIFA World Cup 2026",
            "season": "2026",
            "match_date": date_utc[:10],
            "kickoff_time_utc": date_utc[11:16],
            "stage": STAGE_MAP[stage_raw],
            "group": desc(m.get("GroupName")) or "",
            "round": m.get("MatchNumber"),
            "venue": venue or "",
            "city": city or "",
            "country": country or "",
            "home_team": meta[mid]["home_name"],
            "away_team": meta[mid]["away_name"],
            "home_score": hs,
            "away_score": as_,
            "home_penalty_score": m.get("HomeTeamPenaltyScore"),
            "away_penalty_score": m.get("AwayTeamPenaltyScore"),
            "result_type": result_type,
            "status": "Completed" if m.get("MatchStatus") == 0 else m.get("MatchStatus"),
            "attendance": m.get("Attendance"),
            "referee": referee,
            "fifa_match_id": mid,
            "data_source": "api.fifa.com",
        })
    matches_out.sort(key=lambda r: r["match_id"])

    # ---------- 4. local assist / var / shootout-miss index ----------
    # local team id -> side for each local match
    loc_side = {}
    for lm in lmatches:
        loc_side[int(lm["match_id"])] = {
            lm["home_team_id"]: "home", lm["away_team_id"]: "away",
        }
    ev_by_match = defaultdict(list)
    for e in levents:
        ev_by_match[int(e["match_id"])].append(e)

    def surname_tokens(name):
        return tokens(name)

    def map_local_pid(pid, team_lid, roster):
        """Map local player_id -> fifa IdPlayer using roster name tokens."""
        sq = next((s for s in lsquads if s["player_id"] == str(pid)), None)
        if not sq:
            return None
        ltoks = set(surname_tokens(sq["player_name"]))
        if not ltoks:
            return None
        hits = []
        for p in roster:
            ftoks = set(surname_tokens(desc(p["PlayerName"])))
            inter = ltoks & ftoks
            if inter:
                hits.append((len(inter), p["IdPlayer"]))
        if not hits:
            return None
        best = max(h[0] for h in hits)
        top = [h[1] for h in hits if h[0] == best]
        return top[0] if len(top) == 1 else None

    # ---------- 5. per-match processing ----------
    pms_rows = []          # player match stats
    gk_rows = []
    events_rows = []
    players_master = {}
    pid_names = defaultdict(set)
    val = Counter()
    ev_seq = 0             # global event counter (never resets per match)

    for m in cal:
        mid = m["IdMatch"]
        lid = id2local[mid]
        det = details[mid]
        mm = meta[mid]
        home_len_extra = int(m.get("FirstHalfExtraTime") or 0)
        sh_extra = int(m.get("SecondHalfExtraTime") or 0)
        # full-length effective minutes: regular = 90 + H2 added time;
        # after extra time = 120 (ET added time not published by source -> 0).
        full_len = (90 + sh_extra) if (m.get("ResultType") or 1) == 1 else 120

        # collect fifa events per side first
        side_of_team = {mm["home_id"]: "home", mm["away_id"]: "away"}
        goals = []
        subs = []
        cards = []
        for side in ("HomeTeam", "AwayTeam"):
            t = det[side]
            team_id = t["IdTeam"]
            opp_id = mm["home_id"] if team_id == mm["away_id"] else mm["away_id"]
            for g in t.get("Goals") or []:
                b, a, eff = parse_minute(g.get("Minute"))
                goals.append({
                    "side": side_of_team[team_id], "scorer": g.get("IdPlayer"),
                    "assist": g.get("IdAssistPlayer"), "minute": g.get("Minute"),
                    "eff": eff, "period": g.get("Period"), "type": g.get("Type"),
                    "team_id": team_id, "opp_id": opp_id,
                })
            for b_ in t.get("Bookings") or []:
                bb, ba, beff = parse_minute(b_.get("Minute"))
                is_person = bool(b_.get("IdPlayer"))
                cards.append({
                    "side": side_of_team[b_.get("IdTeam")] if b_.get("IdTeam") in side_of_team else side_of_team[team_id],
                    "player": b_.get("IdPlayer"),
                    "coach": b_.get("IdCoach") or b_.get("IdStaff"),
                    "minute": b_.get("Minute"),
                    "eff": beff, "card": b_.get("Card"),
                    "person": is_person,
                })
            for s in t.get("Substitutions") or []:
                sb, sa, seff = parse_minute(s.get("Minute"))
                subs.append({
                    "side": side_of_team[s.get("IdTeam")] if s.get("IdTeam") in side_of_team else side_of_team[team_id],
                    "on": s.get("IdPlayerOn"), "off": s.get("IdPlayerOff"),
                    "minute": s.get("Minute"), "eff": seff,
                })

        # effective end of play: published half lengths extended by the largest
        # added-time marker observed in this match's event minutes
        all_eff = [g["eff"] for g in goals] + [c["eff"] for c in cards] + [s["eff"] for s in subs]
        all_eff = [e for e in all_eff if e is not None]
        full_end = max([full_len] + all_eff)

        red_eff = defaultdict(lambda: None)
        for c in cards:
            if c["card"] in (2, 3) and c["player"]:
                cur = red_eff[c["player"]]
                red_eff[c["player"]] = c["eff"] if cur is None else min(cur, c["eff"])

        sub_off_eff, sub_on_eff = {}, {}
        sub_on_unknown = set()
        for s in subs:
            if s["off"]:
                sub_off_eff.setdefault(s["off"], s["eff"])
            if s["on"]:
                if s["eff"] is None:
                    sub_on_unknown.add(s["on"])
                else:
                    sub_on_eff.setdefault(s["on"], s["eff"])

        # goals against while GK on pitch handled later; first compute per-player rows
        rosters = {}
        for side in ("HomeTeam", "AwayTeam"):
            rosters[side] = det[side]["Players"]
        # true team membership of every player in this match (feed may place a
        # goal/OG entry under either team's array -> resolve via roster)
        pid2side = {}
        for side in ("HomeTeam", "AwayTeam"):
            s = "home" if side == "HomeTeam" else "away"
            for p in det[side]["Players"]:
                pid2side[p["IdPlayer"]] = s
        for g in goals:
            s_side = pid2side.get(g["scorer"])
            if s_side:
                g["scorer_side"] = s_side
                g["benef_side"] = ("away" if s_side == "home" else "home") if g["type"] == 3 else s_side

        # local assist candidates for this match (sofascore)
        assist_pool = defaultdict(list)  # (lid, side, eff) -> [local player ids]
        for e in ev_by_match.get(lid, []):
            if e["event_type"] == "Assist":
                side = loc_side.get(lid, {}).get(e["team_id"])
                _, _, e_eff = parse_minute(e["minute"])
                if side:
                    assist_pool[(side, e_eff)].append(e)

        var_pool = [e for e in ev_by_match.get(lid, []) if e["event_type"] == "VAR Review"]
        miss_pool = [e for e in ev_by_match.get(lid, []) if e["event_type"] == "Penalty Shootout Miss"]

        # attach assists to goals by (scorer true side, eff)
        used_assist = set()
        for g in goals:
            if g["period"] == 11 or g["type"] == 3:
                continue
            s_side = g.get("scorer_side") or g["side"]
            pool = assist_pool.get((s_side, g["eff"]), [])
            for e in pool:
                ek = (lid, s_side, g["eff"], e["event_id"])
                if ek in used_assist:
                    continue
                roster = rosters["HomeTeam" if s_side == "home" else "AwayTeam"]
                fid = map_local_pid(e["player_id"],
                                    mm["home_id"] if s_side == "home" else mm["away_id"],
                                    roster)
                if fid:
                    g["assist"] = fid
                    g["assist_source"] = "sofascore.com"
                    used_assist.add(ek)
                    break

        # ---- player rows ----
        for side in ("HomeTeam", "AwayTeam"):
            t = det[side]
            team_id = t["IdTeam"]
            opp_id = mm["home_id"] if team_id == mm["away_id"] else mm["away_id"]
            team_name = mm["home_name"] if side == "HomeTeam" else mm["away_name"]
            opp_name = mm["away_name"] if side == "HomeTeam" else mm["home_name"]
            opp_goals_full = (as_ if side == "HomeTeam" else hs)
            formation = t.get("Tactics")

            for p in t.get("Players") or []:
                pid = p["IdPlayer"]
                pname = desc(p["PlayerName"])
                status = p.get("Status")
                pos_code = p.get("Position")
                starter = status == 1
                captain = bool(p.get("Captain"))

                on_eff = 0 if starter else sub_on_eff.get(pid)
                off_eff = None
                cand_offs = [sub_off_eff.get(pid), red_eff.get(pid)]
                cand_offs = [c for c in cand_offs if c is not None]
                if cand_offs:
                    off_eff = min(cand_offs)
                if on_eff is None and pid not in sub_on_unknown:
                    minutes = 0          # unused bench - did not play
                    played = False
                elif on_eff is None:
                    minutes = ""         # entered but entry minute unknown -> NULL
                    played = True
                else:
                    end = off_eff if off_eff is not None else full_end
                    minutes = max(0, (end or full_end) - on_eff)
                    if minutes == 0:
                        # entered at/beyond the last recorded timestamp: residual
                        # stoppage unknown -> NULL instead of a false 0
                        minutes = ""
                    played = True

                g_goals = sum(1 for g in goals if g["scorer"] == pid and g["type"] != 3 and g["period"] != 11)
                g_assists = sum(1 for g in goals if g["assist"] == pid)
                g_og = sum(1 for g in goals if g["scorer"] == pid and g["type"] == 3 and g["period"] != 11)
                yc = sum(1 for c in cards if c["player"] == pid and c["card"] == 1)
                rc_straight = any(c["player"] == pid and c["card"] == 2 for c in cards)
                rc_second = any(c["player"] == pid and c["card"] == 3 for c in cards)
                pens_scored = sum(1 for g in goals if g["scorer"] == pid and g["type"] == 1 and g["period"] == 11)

                row = {
                    "match_id": lid,
                    "competition": "FIFA World Cup 2026",
                    "season": "2026",
                    "match_date": m["Date"][:10],
                    "stage": mm["stage"],
                    "group": mm["group"] or "",
                    "venue": next(r["venue"] for r in matches_out if r["match_id"] == lid),
                    "city": next(r["city"] for r in matches_out if r["match_id"] == lid),
                    "home_team": mm["home_name"],
                    "away_team": mm["away_name"],
                    "home_score": mm["home_score"],
                    "away_score": mm["away_score"],
                    "player_team": team_name,
                    "opponent_team": opp_name,
                    "home_or_away": "home" if side == "HomeTeam" else "away",
                    "player_id": pid,
                    "player_name": pname,
                    "date_of_birth": "",
                    "nationality": "",
                    "position": POS_MAP.get(pos_code),
                    "shirt_number": p.get("ShirtNumber"),
                    "starter": int(starter),
                    "substitute": int(not starter),
                    "minutes_played": minutes,
                    "starting_minute": on_eff if (starter or on_eff) else "",
                    "ending_minute": (on_eff + int(minutes)) if (played and minutes != "") else "",
                    "substitution_in_minute": sub_on_eff.get(pid, ""),
                    "substitution_out_minute": sub_off_eff.get(pid, ""),
                    "captain": int(captain),
                    "formation_position": POS_MAP.get(pos_code),
                    "formation": formation or "",
                    "goals": g_goals,
                    "assists": g_assists,
                    "own_goals": g_og,
                    "penalties_scored_shootout": pens_scored,
                    "yellow_cards": yc,
                    "red_cards": int(rc_straight or rc_second),
                    "second_yellow": int(rc_second),
                    "fouls_committed": "",
                    "offsides": "",
                    "data_source": "api.fifa.com",
                    "source_url": f"https://api.fifa.com/api/v3/live/football/17/285023/{m['IdStage']}/{mid}",
                }
                for c in NULL_COLS_ADVANCED:
                    row[c] = ""
                pms_rows.append(row)
                val["pm_rows"] += 1

                players_master.setdefault(pid, {
                    "player_id": pid, "player_name": pname,
                    "positions": set(), "teams": set(), "n_matches": 0,
                    "date_of_birth": "", "height_cm": "", "nationality": "",
                })
                players_master[pid]["positions"].add(POS_MAP.get(pos_code))
                players_master[pid]["teams"].add(team_name)
                players_master[pid]["n_matches"] += 1
                pid_names[pid].add(norm(pname))

                if POS_MAP.get(pos_code) == "GK":
                    conceded_on_pitch = ""
                    cs = ""
                    if played and minutes != "":
                        # conceded while on pitch: goals benefiting the opponent
                        # (resolved via scorer roster membership)
                        my_side = "home" if side == "HomeTeam" else "away"
                        ga = sum(1 for g in goals
                                 if g.get("benef_side") not in (None, my_side)
                                 and g["period"] != 11
                                 and g["eff"] is not None
                                 and on_eff <= g["eff"] <= (on_eff + int(minutes)))
                        conceded_on_pitch = ga
                        cs = int(ga == 0)
                    gk_rows.append({
                        "match_id": lid,
                        "player_id": pid,
                        "player_name": pname,
                        "team": team_name,
                        "opponent_team": opp_name,
                        "starter": int(starter),
                        "minutes_played": minutes,
                        "saves": "",
                        "shots_faced": "",
                        "goals_conceded_on_pitch": conceded_on_pitch,
                        "clean_sheet": cs,
                        "penalty_saves": "",
                        "punches": "",
                        "high_claims": "",
                        "errors": "",
                        "data_source": "api.fifa.com",
                    })

        # ---- events rows ----
        def add_ev(minute, added, team, pid, pname, etype, esub, rel_pid, descr, src):
            nonlocal ev_seq
            ev_seq += 1
            events_rows.append({
                "event_id": ev_seq,
                "match_id": lid,
                "minute": minute,
                "added_time": added,
                "team": team,
                "player_id": pid or "",
                "player_name": pname or "",
                "event_type": etype,
                "event_subtype": esub,
                "related_player_id": rel_pid or "",
                "description": descr or "",
                "data_source": src,
            })

        id2pname = {}
        for side in ("HomeTeam", "AwayTeam"):
            for p in det[side]["Players"]:
                id2pname[p["IdPlayer"]] = desc(p["PlayerName"])

        for g in goals:
            scorer = id2pname.get(g["scorer"], "")
            s_side = g.get("scorer_side") or g["side"]
            b_side = g.get("benef_side") or g["side"]
            team = mm["home_name"] if b_side == "home" else mm["away_name"]
            scorer_team = mm["home_name"] if s_side == "home" else mm["away_name"]
            base, added, _ = parse_minute(g["minute"])
            if g["period"] == 11:
                add_ev("", "", scorer_team, g["scorer"], scorer, "Penalty Shootout Goal", "penalty_shootout",
                       g["assist"], "Shootout kick scored", "api.fifa.com")
            elif g["type"] == 3:
                # own goal: event credited to BENEFICIARY team; scorer put ball in own net
                add_ev(base, added, team, g["scorer"], scorer, "Own Goal", "own_goal",
                       "", "Own goal by opposing player (beneficiary shown)", "api.fifa.com")
            elif g["type"] == 1:
                add_ev(base, added, team, g["scorer"], scorer, "Goal", "penalty",
                       g["assist"], "Penalty scored", "api.fifa.com")
            else:
                add_ev(base, added, team, g["scorer"], scorer, "Goal", "open_play",
                       g["assist"], "", "api.fifa.com")
            if g["assist"] and g["period"] != 11:
                a_side = pid2side.get(g["assist"], s_side)
                assist_team = mm["home_name"] if a_side == "home" else mm["away_name"]
                add_ev(base, added, assist_team, g["assist"], id2pname.get(g["assist"], ""),
                       "Assist", "assist", g["scorer"],
                       "assist attributed via sofascore.com" if g.get("assist_source") else "",
                       g.get("assist_source", "api.fifa.com"))
        for c in cards:
            team = mm["home_name"] if c["side"] == "home" else mm["away_name"]
            base, added, _ = parse_minute(c["minute"])
            etype = CARD_MAP.get(c["card"], "Card")
            esub = ""
            descr = ""
            if not c["person"]:
                esub = "coach_or_staff"
                descr = "Coach/staff booking"
                if c["card"] in (2, 3):
                    etype = "Red Card"
                    esub += "_red" if c["card"] == 2 else "_second_yellow_red"
            elif c["card"] == 3:
                etype = "Red Card"
                esub = "second_yellow"
            add_ev(base, added, team, c["player"],
                   id2pname.get(c["player"], ""), etype, esub, "", descr, "api.fifa.com")
        for s in subs:
            team = mm["home_name"] if s["side"] == "home" else mm["away_name"]
            base, added, _ = parse_minute(s["minute"])
            add_ev(base, added, team, s["on"], id2pname.get(s["on"], ""), "Substitution",
                   "substitution", s["off"],
                   f"IN: {id2pname.get(s['on'], '')} / OUT: {id2pname.get(s['off'], '')}",
                   "api.fifa.com")
        for e in var_pool:
            side = loc_side.get(lid, {}).get(e["team_id"])
            team = (mm["home_name"] if side == "home" else mm["away_name"]) if side else ""
            base, added, _ = parse_minute(e["minute"])
            add_ev(base, added, team, "", "", "VAR Review", "", "", "from sofascore.com", "sofascore.com")
        for e in miss_pool:
            side = loc_side.get(lid, {}).get(e["team_id"])
            team = (mm["home_name"] if side == "home" else mm["away_name"]) if side else ""
            base, added, _ = parse_minute(e["minute"])
            roster = rosters["HomeTeam"] if side == "home" else rosters["AwayTeam"]
            fid = map_local_pid(e["player_id"], mm["home_id"] if side == "home" else mm["away_id"], roster) if side else None
            add_ev(base, added, team, fid or "", "", "Penalty Shootout Miss", "penalty_shootout",
                   "", f"from sofascore.com (local_player_ref={e['player_id']})", "sofascore.com")
        val["events"] += ev_seq

    # ---------- 6. write outputs ----------
    def write_csv(path, rows):
        if not rows:
            return
        cols = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    write_csv(f"{OUT}/matches.csv", matches_out)
    write_csv(f"{OUT}/player_match_stats.csv", pms_rows)
    write_csv(f"{OUT}/goalkeeper_match_stats.csv", gk_rows)
    write_csv(f"{OUT}/match_events.csv", events_rows)

    pmaster_rows = []
    for pid, info in sorted(players_master.items(), key=lambda kv: kv[1]["player_name"]):
        pmaster_rows.append({
            "player_id": pid,
            "player_name": info["player_name"],
            "positions": "/".join(sorted(x for x in info["positions"] if x)),
            "teams": "/".join(sorted(info["teams"])),
            "n_matches": info["n_matches"],
            "date_of_birth": "",
            "height_cm": "",
            "nationality": "",
            "data_source": "api.fifa.com",
        })
    write_csv(f"{OUT}/players.csv", pmaster_rows)

    # ---------- 7. sqlite ----------
    db_path = f"{OUT}/wc2026.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    for name, rows in (("matches", matches_out), ("player_match_stats", pms_rows),
                       ("goalkeeper_match_stats", gk_rows), ("match_events", events_rows),
                       ("players", pmaster_rows)):
        cols = list(rows[0].keys())
        con.execute(f"CREATE TABLE {name} ({', '.join(repr(c) for c in cols)})")
        con.executemany(
            f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
            [[r[c] for c in cols] for r in rows])
    con.commit()
    con.close()

    # ---------- 7b. parquet ----------
    try:
        import pandas as pd

        def to_df(rows):
            df = pd.DataFrame(rows).replace("", None)
            return df

        for name, rows in (("matches", matches_out), ("player_match_stats", pms_rows),
                           ("goalkeeper_match_stats", gk_rows), ("match_events", events_rows),
                           ("players", pmaster_rows)):
            to_df(rows).to_parquet(f"{OUT}/{name}.parquet", index=False)
        parquet_ok = True
    except Exception as e:
        print("parquet skipped:", e)
        parquet_ok = False

    # ---------- 8. summary stats for report ----------
    missing = {}
    for name, rows in (("matches", matches_out), ("player_match_stats", pms_rows),
                       ("goalkeeper_match_stats", gk_rows), ("match_events", events_rows)):
        miss = Counter()
        for r in rows:
            for k, v in r.items():
                if v is None or v == "":
                    miss[k] += 1
        missing[name] = dict(miss)

    dup_pm = len(pms_rows) - len({(r["match_id"], r["player_id"]) for r in pms_rows})
    multi_name = {p: ns for p, ns in pid_names.items() if len(ns) > 1}

    report = {
        "n_matches": len(matches_out),
        "n_players": len(players_master),
        "n_player_match_rows": len(pms_rows),
        "n_gk_rows": len(gk_rows),
        "n_events": len(events_rows),
        "dup_player_match_pairs": dup_pm,
        "players_with_inconsistent_names": multi_name,
        "missing_values": missing,
    }
    with open(f"{OUT}/build_summary.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({k: v for k, v in report.items() if k != "missing_values"},
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
