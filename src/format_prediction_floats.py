# -*- coding: utf-8 -*-
"""Standardize float columns in prediction feature files to 1 decimal place,
international rounding (ROUND_HALF_UP). Integer/ID/date columns untouched."""
import csv
from decimal import Decimal, ROUND_HALF_UP

BASE = "data/processed/csv"
FILES = ["match_prediction_features", "match_prediction_features_X"]

for fname in FILES:
    with open(f"{BASE}/{fname}.csv", newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames
        rows = list(r)

    # float columns = any non-empty value containing '.' (excluding date/time text)
    float_cols = []
    for c in cols:
        if c in ("date", "kickoff_time_utc"):
            continue
        vals = [row[c] for row in rows if row[c] != ""]
        if vals and any("." in v for v in vals):
            # safety: every non-empty value must parse as Decimal
            try:
                [Decimal(v) for v in vals]
            except Exception:
                continue
            float_cols.append(c)

    changed = 0
    for row in rows:
        for c in float_cols:
            v = row[c]
            if v == "":
                continue
            q = Decimal(v).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            s = f"{q:f}"          # '6.0', '2.3'; avoid exponent notation
            if s != v:
                changed += 1
            row[c] = s

    with open(f"{BASE}/{fname}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"{fname}: formatted {len(float_cols)} float columns, {changed} cells rewritten")
