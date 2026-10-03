"""Tai calendar + chi tiet tran FIFA ve data/raw/fifa (chay thu cong)."""
import json
import os
import subprocess
import sys
import time

RAW_DIR = os.path.join("data", "raw", "fifa")


def fetch_json(url, retries=3):
    """GET JSON qua curl.exe, tra dict hoac None sau het retries."""
    for i in range(retries):
        r = subprocess.run(
            ["curl.exe", "-s", "--max-time", "40",
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
             "-H", "Accept: application/json", url],
            capture_output=True)
        if r.returncode == 0 and r.stdout:
            try:
                return json.loads(r.stdout.decode("utf-8-sig"))
            except Exception as e:
                print("  parse err", e, file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None


def _valid_match_payload(out, min_bytes=5000):
    """File cu chi dung duoc khi doc duoc JSON co HomeTeam."""
    if not (os.path.exists(out) and os.path.getsize(out) > min_bytes):
        return False
    try:
        with open(out, encoding="utf-8") as f:
            return "HomeTeam" in json.load(f)
    except (OSError, ValueError):
        return False


def main():
    """Tai calendar (bat buoc) roi lan luot tai chi tiet tung tran."""
    os.makedirs(RAW_DIR, exist_ok=True)

    # 1) calendar
    cal = fetch_json("https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&count=300")
    if not cal or "Results" not in cal:
        print("FAIL: khong tai duoc calendar (kiem tra mang/API).", file=sys.stderr)
        raise SystemExit(1)
    matches = cal["Results"]
    print("calendar matches:", len(matches))
    with open(os.path.join(RAW_DIR, "calendar.json"), "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False)

    ok = fail = 0
    for i, m in enumerate(matches, 1):
        mid, stg, sea, comp = m["IdMatch"], m["IdStage"], m["IdSeason"], m["IdCompetition"]
        out = os.path.join(RAW_DIR, f"match_{mid}.json")
        if _valid_match_payload(out):
            ok += 1
            continue
        d = fetch_json(f"https://api.fifa.com/api/v3/live/football/{comp}/{sea}/{stg}/{mid}")
        if d and "HomeTeam" in d:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
            ok += 1
        else:
            fail += 1
            print("FAIL match", mid, file=sys.stderr)
        if i % 10 == 0:
            print(f"progress {i}/{len(matches)} ok={ok} fail={fail}", flush=True)
        time.sleep(0.35)

    print(f"DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
