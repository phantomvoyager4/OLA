"""Collect a fresh, non-snowball sample of ranked solo games for drift checks.

Players are drawn at random from Riot's league lists (per tier, per platform).
Each player contributes their latest game and one random game from their last
20, labelled, so the "latest game" selection can be tested directly. Games are
converted with today's Match/Player code, the same shape the live site scores.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/fresh_sample.py --out <dir> --per-tier 5
Spends about 384 Riot API calls; stop the backend first.
Superseded by ../ladder_sampler.py; kept to reproduce the 2026-10-20 pilot.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from urllib.parse import quote

from BACKEND import riot_api
from BACKEND.model import Match, Player
from BACKEND.pipeline import load_api_key

# Leave headroom under the key's 100/120 s for the Docker backend.
riot_api.RIOT_RATE_LIMITER = riot_api.DualWindowRateLimiter(15, 1.0, 70, 120.0)

PLATFORMS = {"EUW1": "europe", "EUN1": "europe", "NA1": "americas"}
TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER"]
DIVISIONS = ["I", "II", "III", "IV"]
CALLS = 0


def get(url, key, params=None):
    global CALLS
    CALLS += 1
    status, payload = riot_api.riot_get_json(url, {**(params or {}), "api_key": key})
    if status != 200:
        print(f"  HTTP {status}: {url.split('?')[0][-80:]}")
        if status in (401, 403):
            raise SystemExit("API key rejected; stopping.")
        return None
    return payload


def league_entries(platform, tier, key, rng):
    base = f"https://{platform.lower()}.api.riotgames.com/lol/league/v4"
    if tier == "MASTER":
        league = get(f"{base}/masterleagues/by-queue/RANKED_SOLO_5x5", key) or {}
        return [{**e, "tier": "MASTER"} for e in league.get("entries", [])]
    division = rng.choice(DIVISIONS)
    page = rng.randint(1, 5)
    entries = get(f"{base}/entries/RANKED_SOLO_5x5/{tier}/{division}", key, {"page": page}) or []
    if not entries and page != 1:
        entries = get(f"{base}/entries/RANKED_SOLO_5x5/{tier}/{division}", key, {"page": 1}) or []
    return entries


def convert(payload):
    info = payload.get("info", {})
    duration = info.get("gameDuration", 0)
    return {
        "match_id": payload["metadata"]["matchId"],
        "metadata": Match(payload).to_dict(),
        "players": [Player(p, game_duration_sec=duration).to_dict() for p in info.get("participants", [])],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-tier", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--platforms", nargs="+", default=list(PLATFORMS))
    args = parser.parse_args()
    key = load_api_key()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    seen = set()
    started = time.time()

    for platform in args.platforms:
        route = PLATFORMS[platform]
        records, raws = [], {}
        for tier in TIERS:
            entries = [e for e in league_entries(platform, tier, key, rng) if e.get("puuid") and not e.get("inactive")]
            rng.shuffle(entries)
            taken = 0
            for entry in entries[: args.per_tier * 3]:
                if taken >= args.per_tier:
                    break
                ids = get(
                    f"https://{route}.api.riotgames.com/lol/match/v5/matches/by-puuid/{quote(entry['puuid'], safe='')}/ids",
                    key, {"queue": 420, "start": 0, "count": 20},
                ) or []
                if len(ids) < 2:
                    continue
                picks = [("latest", 0), ("random", rng.randint(1, len(ids) - 1))]
                for kind, position in picks:
                    match_id = ids[position]
                    if match_id in seen:
                        continue
                    payload = get(f"https://{route}.api.riotgames.com/lol/match/v5/matches/{match_id}", key)
                    if not payload or payload.get("info", {}).get("queueId") != 420:
                        continue
                    seen.add(match_id)
                    record = convert(payload)
                    record["sample"] = {
                        "platform": platform, "tier": entry.get("tier", tier), "rank": entry.get("rank"),
                        "puuid": entry["puuid"], "kind": kind, "position": position, "history": len(ids),
                    }
                    records.append(record)
                    raws[match_id] = payload
                taken += 1
            print(f"{platform} {tier}: {taken} players, {len(records)} games so far, {CALLS} calls, {time.time() - started:.0f}s", flush=True)
        (args.out / f"fresh_{platform}.json").write_text(json.dumps(records, ensure_ascii=False))
        (args.out / f"raw_{platform}.json").write_text(json.dumps(raws, ensure_ascii=False))
        print(f"saved {platform}: {len(records)} games", flush=True)
    print(f"done: {CALLS} calls in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
