"""Re-fetch stored crawl matches and compare their scoring features with today's code.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/skew_check.py --n 12
Spends one Riot API call per match (--n); stop the backend first.
"""
from __future__ import annotations

import argparse
import random
from collections import defaultdict

from BACKEND import model, riot_api
from BACKEND.metascripts.build_score_reference import load_matches
from BACKEND.model import Player
from BACKEND.pipeline import load_api_key
from check_auc import DATA_DIR

riot_api.RIOT_RATE_LIMITER = riot_api.DualWindowRateLimiter(15, 1.0, 70, 120.0)

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=12)
args = parser.parse_args()
key = load_api_key()

stored = [m for m in load_matches(DATA_DIR) if not model.is_remake(m)]
sample = random.Random(1).sample(stored, args.n)
diffs = defaultdict(list)
compared = 0
for m in sample:
    status, raw = riot_api.riot_get_json(
        f"https://europe.api.riotgames.com/lol/match/v5/matches/{m['match_id']}", {"api_key": key})
    if status != 200:
        print(f"{m['match_id']}: HTTP {status}")
        continue
    info = raw["info"]
    live_duration = info["gameDuration"] / 60.0
    stored_duration = model.game_duration_minutes(m["metadata"])
    diffs["game length (min)"].append(abs(live_duration - stored_duration))
    fresh = {p["puuid"]: Player(p, game_duration_sec=info["gameDuration"]).to_dict() for p in info["participants"]}
    for p in m["players"]:
        q = fresh.get(p.get("puuid"))
        if q is None:
            continue
        compared += 1
        a = model._extract_performance_features(p, stored_duration)
        b = model._extract_performance_features(q, live_duration)
        for f in model.PERFORMANCE_FEATURE_WEIGHTS:
            diffs[f].append(abs(a[f] - b[f]))
        diffs["teamPosition differs"].append(float(p.get("teamPosition") != q.get("teamPosition")))
        diffs["win differs"].append(float(bool(p.get("win")) != bool(q.get("win"))))
    print(f"{m['match_id']}: compared {len(m['players'])} players, remake flag now {any(x.get('gameEndedInEarlySurrender') for x in info['participants'])}")

print(f"\nplayers compared={compared}")
for f, v in diffs.items():
    print(f"  {f:22s} max |diff| {max(v):.4f}  rows with |diff|>1e-6: {sum(x > 1e-6 for x in v)}/{len(v)}")
