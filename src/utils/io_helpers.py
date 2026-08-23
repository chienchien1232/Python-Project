# -*- coding: utf-8 -*-
"""Helper doc/ghi CSV chuan cho toan du an."""
import csv


def load_csv(path, delimiter=","):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f, delimiter=delimiter)
        return list(r), list(r.fieldnames)


def save_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def load_pms():
    return load_csv("data/processed/wc2026_player_match/player_match_stats.csv")[0]


def load_gk():
    return load_csv("data/processed/wc2026_player_match/goalkeeper_match_stats.csv")[0]
