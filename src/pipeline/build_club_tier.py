# -*- coding: utf-8 -*-
"""Sinh club_tier_map.csv: (league, league_level, club_tier) cho moi club_team.

Quy tac minh bach (de bao ve):
  - league_level: 1 = Big-5 (ENG/ESP/GER/ITA/FRA), 2 = giai manh khac
    (POR/NED/TUR/BRA/Saudi/Qatar/SCO/...), 3 = con lai (Other).
  - club_tier: 1 = elite (UCL thuong xuyen, list cung), 2 = Big-5 con lai +
    CLB manh giai level-2, 3 = con lai.
Output: data/processed/club_tier_map.csv (club_team, league, league_level,
  club_tier) + in coverage. Chay offline 1 lan; ML/web chi merge.
"""
import os
import sys

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SQ = "data/processed/csv/squads_and_players.csv"
OUT = "data/processed/club_tier_map.csv"

# CLB -> giai dau (chi can top CLB theo so cau thu; con lai = Other).
LEAGUE = {
    # ENG - Premier League
    "Manchester City FC": "ENG", "Arsenal FC": "ENG",
    "Manchester United FC": "ENG", "Liverpool FC": "ENG",
    "Chelsea FC": "ENG", "Aston Villa FC": "ENG",
    "Tottenham Hotspur FC": "ENG", "Newcastle United FC": "ENG",
    "Brighton & Hove Albion FC": "ENG", "Crystal Palace FC": "ENG",
    "Fulham FC": "ENG", "Wolverhampton Wanderers FC": "ENG",
    "AFC Bournemouth": "ENG", "Sunderland AFC": "ENG",
    # ESP - La Liga
    "Real Madrid C. F.": "ESP", "FC Barcelona": "ESP",
    "Atlético De Madrid": "ESP", "Villarreal CF": "ESP",
    "Real Betis": "ESP",
    # GER - Bundesliga
    "FC Bayern München": "GER", "Borussia Dortmund": "GER",
    "Bayer 04 Leverkusen": "GER", "VfB Stuttgart": "GER",
    "Eintracht Frankfurt": "GER", "TSG Hoffenheim": "GER",
    "1. FSV Mainz 05": "GER", "Borussia Mönchengladbach": "GER",
    "RB Leipzig": "GER",
    # ITA - Serie A (bo sung dot 2)
    "AS Roma": "ITA", "Bologna FC": "ITA",
    # FRA - Ligue 1 (bo sung dot 2)
    "Olympique Lyonnais": "FRA", "Olympique Marseille": "FRA",
    # ESP - La Liga (bo sung dot 2)
    "Real Sociedad": "ESP",
    # GER - Bundesliga (bo sung dot 2)
    "VfL Wolfsburg": "GER",
    # ENG - Premier League (bo sung dot 2)
    "West Ham United FC": "ENG", "Nottingham Forest FC": "ENG",
    "Burnley FC": "ENG", "Norwich City FC": "ENG",
    # NED - Eredivisie (bo sung dot 2)
    "Feyenoord Rotterdam": "NED",
    # SCO (bo sung dot 2)
    "Rangers FC": "SCO",
    # BEL
    "Club Brugge": "BEL",
    # ARG
    "CA River Plate": "ARG",
    # TUR (bo sung dot 2; chuoi trong CSV co san mojibake -> giu y nguyen)
    "Beşiktaş JK": "TUR", "Ba ş ak ş ehir FK": "TUR",
    # CZE (chuoi trong CSV co san mojibake -> giu y nguyen)
    "FC Viktoria Plze ň": "CZE",
    # QAT (bo sung dot 2)
    "Al Sadd SC": "QAT",
    # FRA - Ligue 1
    "Paris Saint-Germain": "FRA", "AS Monaco": "FRA",
    "Lille OSC": "FRA", "OGC Nice": "FRA", "RC Strasbourg": "FRA",
    # POR - Primeira Liga
    "SL Benfica": "POR", "Sporting CP": "POR",
    # NED - Eredivisie
    "PSV Eindhoven": "NED",
    # TUR - Super Lig
    "Galatasaray SK": "TUR", "Fenerbahçe SK": "TUR",
    # BRA - Serie A
    "CR Flamengo": "BRA", "SE Palmeiras": "BRA",
    # Saudi / Qatar
    "Al Hilal SC": "KSA", "Al Nassr FC": "KSA", "Al Ahli FC": "KSA",
    "Al Qadsiah FC": "KSA", "Al Duhail SC": "QAT", "Al Hussein SC": "QAT",
    # SCO
    "Celtic FC": "SCO",
    # RSA
    "Mamelodi Sundowns FC": "RSA", "Orlando Pirates FC": "RSA",
    # MEX
    "CD Guadalajara": "MEX",
    # NZL
    "Auckland FC": "NZL",
    # CZE
    "SK Slavia Praha": "CZE",
    # SUI
    "BSC Young Boys": "SUI",
    # IRN
    "Persepolis FC": "IRN",
    # EGY
    "Al Ahly FC": "EGY",
}

BIG5 = {"ENG", "ESP", "GER", "ITA", "FRA"}

ELITE = {
    "Manchester City FC", "Real Madrid C. F.", "FC Barcelona",
    "FC Bayern München", "Paris Saint-Germain", "Liverpool FC",
    "Arsenal FC", "FC Internazionale Milano", "Chelsea FC",
    "Borussia Dortmund", "Atlético De Madrid", "Juventus FC",
    "AC Milan", "Tottenham Hotspur FC", "Bayer 04 Leverkusen",
    "Atalanta Bergamo", "Newcastle United FC", "Aston Villa FC",
}


def main():
    """Map tung club_team -> (league, level, tier); ghi CSV + coverage."""
    sq = pd.read_csv(SQ, dtype={"player_id": str})
    clubs = sorted(sq["club_team"].dropna().unique().tolist())
    rows = []
    for club in clubs:
        league = LEAGUE.get(club, "Other")
        if club in ELITE:
            tier, level = 1, 1
        elif league in BIG5:
            tier, level = 2, 1
        elif league != "Other":
            tier, level = 2, 2
        else:
            tier, level = 3, 3
        rows.append({"club_team": club, "league": league,
                     "league_level": level, "club_tier": tier})
    out = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)
    n_players = sq["club_team"].notna().sum()
    mapped_known = sq["club_team"].isin(LEAGUE).sum()
    print(f"clubs: {len(clubs)} ({sum(1 for c in clubs if c in LEAGUE)} mapped, "
          f"{sum(1 for c in clubs if c not in LEAGUE)} Other)")
    print(f"players covered by known league: {mapped_known}/{n_players} "
          f"({100 * mapped_known / max(n_players, 1):.1f}%)")
    print(out["club_tier"].value_counts().sort_index().to_string())
    print("saved:", OUT)


if __name__ == "__main__":
    main()
