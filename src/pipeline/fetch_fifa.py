import json, subprocess, time, os, sys

os.makedirs("data/raw/fifa", exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}

def fetch_json(url, retries=3):
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

# 1) calendar
cal = fetch_json("https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&count=300")
matches = cal["Results"]
print("calendar matches:", len(matches))
with open("data/raw/fifa/calendar.json", "w", encoding="utf-8") as f:
    json.dump(matches, f, ensure_ascii=False)

ok = fail = 0
for i, m in enumerate(matches, 1):
    mid, stg, sea, comp = m["IdMatch"], m["IdStage"], m["IdSeason"], m["IdCompetition"]
    out = f"data/raw/fifa/match_{mid}.json"
    if os.path.exists(out) and os.path.getsize(out) > 5000:
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
