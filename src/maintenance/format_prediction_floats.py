# -*- coding: utf-8 -*-
"""Standardize float columns in prediction feature files to 1 decimal place,
international rounding (ROUND_HALF_UP). Integer/ID/date columns untouched."""
import csv
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

BASE = "data/processed/csv"
FILES = ["match_prediction_features", "match_prediction_features_X"]


def is_float_column(vals):
    """True neu moi gia tri deu parse duoc Decimal va co it nhat 1 dau '.'."""
    if not vals or not any("." in v for v in vals):
        return False
    for v in vals:
        try:
            Decimal(v)
        except (InvalidOperation, ValueError, OverflowError):
            return False
    return True


def main():
    """Quantize cac cot float ve 1 thap phan, giu nguyen cot int/ID/date."""
    for fname in FILES:
        with open(f"{BASE}/{fname}.csv", newline="", encoding="utf-8-sig") as f:
            r = csv.DictReader(f)
            cols = r.fieldnames
            rows = list(r)

        # float columns = co dau '.' va parse duoc Decimal (tru date/time text)
        float_cols = []
        for c in cols:
            if c in ("date", "kickoff_time_utc"):
                continue
            vals = [row[c] for row in rows if row[c] != ""]
            if is_float_column(vals):
                float_cols.append(c)

        changed = skipped = 0
        for row in rows:
            for c in float_cols:
                v = row[c]
                if v == "":
                    continue
                try:
                    q = Decimal(v).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ValueError, OverflowError):
                    skipped += 1
                    continue
                s = f"{q:f}"          # '6.0', '2.3'; avoid exponent notation
                if s != v:
                    changed += 1
                row[c] = s

        with open(f"{BASE}/{fname}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

        print(f"{fname}: formatted {len(float_cols)} float columns, "
              f"{changed} cells rewritten, {skipped} skipped")


if __name__ == "__main__":
    main()
