"""Pilot: per-route rate-limit buckets, games per player on the current patch, league page size.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/pilot.py ANALYSIS/fetching_sample/samples/pilot_2026-10-20
Spends about 125 Riot API calls; stop the backend first.
"""
import glob, json, sys, time
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import quote
import numpy as np
import requests
from BACKEND import riot_api
from BACKEND.pipeline import load_api_key

sp = sys.argv[1]
key = load_api_key()
limiter = riot_api.DualWindowRateLimiter(15, 1.0, 70, 120.0)
ROUTE = {"EUW1": "europe", "EUN1": "europe", "NA1": "americas"}
PATCH_START = int(datetime(2026, 10, 7, tzinfo=timezone.utc).timestamp())
calls = 0

def get(url, params=None):
    global calls
    for attempt in range(5):
        limiter.acquire(); calls += 1
        r = requests.get(url, params={**(params or {}), "api_key": key}, timeout=20)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", 2))); continue
        return r
    return r

print("== rate-limit buckets (X-App-Rate-Limit-Count after each call) ==")
probe_puuid = {}
for m in (m for f in sorted(glob.glob(f"{sp}/fresh_*.json")) for m in json.load(open(f))):
    probe_puuid.setdefault(m["sample"]["platform"], m["sample"]["puuid"])
for label, url in [
    ("europe #1", f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{quote(probe_puuid['EUW1'])}/ids"),
    ("europe #2", f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{quote(probe_puuid['EUN1'])}/ids"),
    ("americas #1", f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{quote(probe_puuid['NA1'])}/ids"),
    ("euw1 league", "https://euw1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/II"),
    ("na1 league", "https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/II"),
]:
    r = get(url, {"count": 1} if "match" in url else {"page": 1})
    extra = f" entries on page={len(r.json())}" if "league" in label else ""
    print(f"  {label:12s} HTTP {r.status_code} app-limit={r.headers.get('X-App-Rate-Limit')} count={r.headers.get('X-App-Rate-Limit-Count')}{extra}")

print("\n== ranked solo games since 2026-10-07 (patch 16.20) per sampled player ==")
players = {}
for m in (m for f in sorted(glob.glob(f"{sp}/fresh_*.json")) for m in json.load(open(f))):
    s = m["sample"]; players[(s["platform"], s["puuid"])] = s["tier"]
counts = defaultdict(list)
for (platform, puuid), tier in players.items():
    r = get(f"https://{ROUTE[platform]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{quote(puuid)}/ids",
            {"queue": 420, "startTime": PATCH_START, "count": 100})
    if r.status_code == 200:
        counts[(platform, tier)].append(len(r.json()))
json.dump({f"{p}|{t}": v for (p, t), v in counts.items()}, open(f"{sp}/pilot_counts.json", "w"))
tiers = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER"]
for tier in tiers:
    v = [x for (p, t), xs in counts.items() if t == tier for x in xs]
    print(f"  {tier:9s} n={len(v):2d} active={np.mean([x > 0 for x in v]):.0%} mean={np.mean(v):5.1f} median={np.median(v):4.0f} max={max(v):3d}")
v = [x for xs in counts.values() for x in xs]
print(f"  ALL       n={len(v)} active={np.mean([x > 0 for x in v]):.0%} mean={np.mean(v):.1f} mean among active={np.mean([x for x in v if x]):.1f} share hitting 100 cap={np.mean([x >= 100 for x in v]):.0%}")
for platform in ROUTE:
    w = [x for (p, t), xs in counts.items() if p == platform for x in xs]
    print(f"  {platform:9s} active={np.mean([x > 0 for x in w]):.0%} mean={np.mean(w):.1f}")
print(f"calls={calls}")
