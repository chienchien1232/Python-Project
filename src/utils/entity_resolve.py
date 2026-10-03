# -*- coding: utf-8 -*-
"""Noi thuc the (entity resolution) dung chung cho moi join moi.

Nguyen tac (chi stdlib: difflib + concurrent.futures, khong them lib):
  1. Blocking: chi so ten trong nhom (nationality, birth_year +-1,
     position_group) -> 1248xN con ~1-5 ung vien/khoa.
  2. Fuzzy: difflib.SequenceMatcher tren chuoi da chuan hoa (bo dau,
     lower, chi [a-z0-9]); duoi nguong -> None de review tay.
  3. Song song ThreadPool (tranh joblib/loky von gay loi pickle tren Windows).
  4. Ket qua ghi bridge CSV offline 1 lan; web/ML chi pd.merge (ms).

Quy uoc bridge: data/processed/<ten>_bridge.csv
  cot: from_id, to_id, score, verified (0/1)
  + file <ten>_conflicts.csv cho ca khong khop de sua tay.
"""
import difflib
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

#: Nhom vi tri rong de blocking (thu hep hon so full string).
POS_GROUP = {
    "GK": "GK", "GOALKEEPER": "GK",
    "DEF": "DEF", "DEFENDER": "DEF", "DF": "DEF",
    "MID": "MID", "MIDFIELDER": "MID", "MF": "MID",
    "FWD": "FWD", "FORWARD": "FWD", "FW": "FWD", "ATTACKER": "FWD",
}


def norm_key(s):
    """Chuan hoa chuoi ve [a-z0-9] khong dau de so sanh."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def birth_year(date_of_birth):
    """Lay nam sinh tu 'YYYY-MM-DD'; None neu loi."""
    try:
        return int(str(date_of_birth)[:4])
    except (ValueError, TypeError):
        return None


def pos_group(position):
    """Nhom vi tri rong (GK/DEF/MID/FWD); 'OTHER' neu la."""
    if not position:
        return "OTHER"
    return POS_GROUP.get(str(position).strip().upper(), "OTHER")


def block_key(nationality, date_of_birth, position):
    """Khoa blocking (quoctich, nam sinh, nhom vi tri)."""
    nat = norm_key(nationality)
    return (nat, birth_year(date_of_birth), pos_group(position))


def best_match(name, choices, threshold=0.82):
    """Ten khop nhat trong choices (difflib); (match|None, score).

    Args:
        name: ten can noi.
        choices: iterable cac ten ung vien (da duoc blocking).
        threshold: duoi nguong nay tra (None, score) de review tay.
    """
    target = norm_key(name)
    best, best_score = None, 0.0
    for c in choices:
        score = difflib.SequenceMatcher(None, target, norm_key(c)).ratio()
        if score > best_score:
            best, best_score = c, score
    if best is None or best_score < threshold:
        return None, round(best_score, 3)
    return best, round(best_score, 3)


def _match_one(args):
    """Worker cho ThreadPool: (name, choices, threshold) -> (name, match, score)."""
    name, choices, threshold = args
    match, score = best_match(name, choices, threshold)
    return name, match, score


def match_all(names, choices, threshold=0.82, max_workers=8):
    """Noi hang loat ten (song song threads; difflib nha GIL o C).

    Returns:
        List (name, match|None, score) cung thu tu names.
    """
    jobs = [(n, choices, threshold) for n in names]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(_match_one, jobs))


def match_blocked(left_rows, right_names_by_key, threshold=0.82,
                   max_workers=8):
    """Noi co blocking.

    Args:
        left_rows: list dict co khoa name/nationality/date_of_birth/position
            (ten khoa truyen qua name_key/nat_key/dob_key/pos_key).
        right_names_by_key: dict {(nat, year, posg): [ten]} phia phai.
        threshold: nguong fuzzy (them +-1 tuoi o khoa nam sinh).
    Returns:
        List (left_row, match|None, score).
    """
    jobs = []
    order = []
    for row in left_rows:
        key = (norm_key(row.get("nat", "")),
               birth_year(row.get("dob", "")),
               pos_group(row.get("pos", "")))
        cands = []
        for year in ({key[1]} if key[1] is None
                     else {key[1] - 1, key[1], key[1] + 1}):
            cands += right_names_by_key.get((key[0], year, key[2]), [])
        jobs.append((row.get("name", ""), cands, threshold))
        order.append(row)
    out = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for row, (_, match, score) in zip(order, pool.map(_match_one, jobs)):
            out.append((row, match, score))
    return out
