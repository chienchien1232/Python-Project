# -*- coding: utf-8 -*-
"""Build wc2026_full.db - SQLite duy nhất cho web dashboard.

Nguon : data/processed/csv/ (chuan) + wc2026_player_match/ (san pham ML)
Dich  : data/db/wc2026_full.db  (5 dim + 6 fact + views)

Usage:
    python src/db/build_db.py            # build tat ca bang
    python src/db/build_db.py --check    # kiem tra so dong DB vs CSV nguon
"""
import csv
import os
import sqlite3
import sys

CSV = "data/processed/csv"
WC = "data/processed/wc2026_player_match"
DB_DIR = "data/db"
DB = os.path.join(DB_DIR, "wc2026_full.db")


def load(path, delim=","):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f, delimiter=delim)
        return list(r), list(r.fieldnames)


def create_table(con, name, cols, drop=True):
    if drop:
        con.execute(f"DROP TABLE IF EXISTS {name}")
    con.execute(f"CREATE TABLE {name} ({', '.join(chr(34)+c+chr(34) for c in cols)})")


def insert_rows(con, name, cols, rows):
    con.executemany(
        f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
        [[r.get(c) for c in cols] for r in rows])


def build():
    os.makedirs(DB_DIR, exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    counts = {}

    # ---------- dimensions ----------
    for name in ("teams", "venues", "tournament_stages"):
        rows, cols = load(f"{CSV}/{name}.csv")
        create_table(con, name, cols)
        insert_rows(con, name, cols, rows)
        counts[name] = len(rows)

    # players tu squads_and_players (bo cot goals trung thong tin? giu nguyen)
    rows, cols = load(f"{CSV}/squads_and_players.csv")
    cols = ["player_id"] + [c for c in cols if c != "player_id"]
    create_table(con, "players", cols)
    insert_rows(con, "players", cols, rows)
    counts["players"] = len(rows)

    # referees: suy ra tu matches (khong co bang rieng trong csv chuan)
    con.execute("""CREATE TABLE referees (
        referee_id INTEGER PRIMARY KEY,
        referee_name TEXT)""")
    seen = {}
    for r in load(f"{CSV}/matches.csv")[0]:
        rid, nm = r.get("referee_id"), r.get("referee_name")
        if rid and rid not in seen:
            seen[rid] = nm
    con.executemany("INSERT INTO referees VALUES (?, ?)", list(seen.items()))
    counts["referees"] = len(seen)

    # ---------- facts ----------
    for name in ("matches", "match_events", "match_lineups",
                 "match_team_stats", "matches_detailed"):
        rows, cols = load(f"{CSV}/{name}.csv")
        create_table(con, name, cols)
        insert_rows(con, name, cols, rows)
        counts[name] = len(rows)

    for name in ("player_match_stats", "goalkeeper_match_stats"):
        rows, cols = load(f"{WC}/{name}.csv")
        create_table(con, name, cols)
        insert_rows(con, name, cols, rows)
        counts[name] = len(rows)

    player_stats, pcols = load(f"{CSV}/player_stats.csv")
    create_table(con, "player_stats_tournament", pcols)
    insert_rows(con, "player_stats_tournament", pcols, player_stats)
    counts["player_stats_tournament"] = len(player_stats)

    # ---------- indexes ----------
    idx = [
        ("idx_matches_stage", "matches(stage_id)"),
        ("idx_matches_home", "matches(home_team_id)"),
        ("idx_matches_away", "matches(away_team_id)"),
        ("idx_events_match", "match_events(match_id)"),
        ("idx_events_player", "match_events(player_id)"),
        ("idx_lineups_match", "match_lineups(match_id)"),
        ("idx_lineups_player", "match_lineups(player_id)"),
        ("idx_mts_match", "match_team_stats(match_id)"),
        ("idx_pms_match", "player_match_stats(match_id)"),
        ("idx_pms_player", "player_match_stats(player_id)"),
        ("idx_gk_match", "goalkeeper_match_stats(match_id)"),
    ]
    for name, expr in idx:
        con.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {expr}")

    # ---------- views cho web ----------
    con.execute("""CREATE VIEW v_player_totals AS
        SELECT player_id,
               MAX(player_name) AS player_name,
               MAX(position)    AS position,
               MAX(nationality) AS nationality,
               COUNT(*)                                   AS matches_played_db,
               SUM(CASE WHEN minutes_played > 0 THEN 1 ELSE 0 END) AS apps,
               SUM(minutes_played)                        AS minutes,
               SUM(goals)                                 AS goals,
               SUM(assists)                               AS assists,
               SUM(shots)                                 AS shots,
               SUM(shots_on_target)                       AS shots_on_target,
               SUM(passes)                                AS passes,
               SUM(accurate_passes)                       AS accurate_passes,
               SUM(tackles)                               AS tackles,
               SUM(interceptions)                         AS interceptions,
               SUM(clearances)                            AS clearances,
               SUM(recoveries)                            AS recoveries,
               SUM(aerial_duels_won)                      AS aerial_duels_won,
               SUM(duels_won)                             AS duels_won,
               SUM(dribbles_attempted)                    AS dribbles_attempted,
               SUM(crosses)                               AS crosses,
               SUM(fouls_committed)                       AS fouls_committed,
               SUM(fouls_won)                             AS fouls_won,
               SUM(yellow_cards)                          AS yellow_cards,
               SUM(red_cards)                             AS red_cards
        FROM player_match_stats
        GROUP BY player_id""")
    con.execute("""CREATE VIEW v_goalkeepers AS
        SELECT * FROM goalkeeper_match_stats WHERE starter = 1""")

    con.commit()

    # ---------- verify ----------
    ok = True
    for name, n_csv in counts.items():
        n_db = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        if n_db != n_csv:
            print(f"[FAIL] {name}: db={n_db} vs csv={n_csv}")
            ok = False
    con.close()
    print("\n=== BUILD SUMMARY ===")
    for k, v in sorted(counts.items()):
        print(f"  {k:28s} {v:>6}")
    print("\nDB:", DB, "|", "ALL ROWS MATCH CSV" if ok else "MISMATCH!")


def check():
    con = sqlite3.connect(DB)
    src_counts = {
        "teams": len(load(f"{CSV}/teams.csv")[0]),
        "players": len(load(f"{CSV}/squads_and_players.csv")[0]),
        "matches": len(load(f"{CSV}/matches.csv")[0]),
        "match_events": len(load(f"{CSV}/match_events.csv")[0]),
        "match_lineups": len(load(f"{CSV}/match_lineups.csv")[0]),
        "match_team_stats": len(load(f"{CSV}/match_team_stats.csv")[0]),
        "player_match_stats": len(load(f"{WC}/player_match_stats.csv")[0]),
        "goalkeeper_match_stats": len(load(f"{WC}/goalkeeper_match_stats.csv")[0]),
    }
    ok = True
    for name, n in src_counts.items():
        n_db = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        status = "OK" if n_db == n else "FAIL"
        ok &= n_db == n
        print(f"  {name:26s} db={n_db:5d} csv={n:5d} [{status}]")
    print("\nCHECK:", "PASS" if ok else "FAIL")
    con.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        build()
