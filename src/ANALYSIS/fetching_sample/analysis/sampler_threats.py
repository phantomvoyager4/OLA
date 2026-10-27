"""Offline checks of ladder_sampler threats on the smoke run and the pilot.

T1 apex list sizes; T2 draws needed per game against max_draws_per_game;
T3 ladder tier mix against the DPM.LOL workbook and the old reference, and
the score shift a tier-mix error implies; T4 patch-window gaps; T5 whether
build_score_reference reads processed/; T6 size per game; T7 time zones in
patch_start; T8 HTTP statuses.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/sampler_threats.py
"""

from __future__ import annotations

import copy
import glob
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from BACKEND import model
from BACKEND.metascripts.build_score_reference import ROLES, collect_features, load_matches

SAMPLES = Path("ANALYSIS/fetching_sample/samples")
SMOKE = SAMPLES / "16.20"
PILOT = SAMPLES / "pilot_2026-10-20"
SHEET = Path("ANALYSIS/data/LoL Rank Distribution via DPM.LOL.xlsx")
TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
RNG = np.random.default_rng(5)

servers = sorted(p.parent for p in SMOKE.glob("*/manifest.json"))
manifests = {s.name: json.loads((s / "manifest.json").read_text()) for s in servers}
draws = {s.name: [json.loads(line) for line in (s / "draws.jsonl").read_text().splitlines()] for s in servers}

print("== T1 apex list sizes (Grandmaster and Challenger have fixed sizes) ==")
for name, manifest in manifests.items():
    ladder = manifest["ladder"]
    print(f"  {name:<5} MASTER {ladder['MASTER']['I']:6d}  GRANDMASTER {ladder['GRANDMASTER']['I']:4d}  CHALLENGER {ladder['CHALLENGER']['I']:4d}")

print("\n== T2 draws per game by tier (cap: max_draws_per_game x quota) ==")
pilot_counts = json.loads((PILOT / "pilot_counts.json").read_text())
patch_games = defaultdict(list)
for key, values in pilot_counts.items():
    patch_games[key.split("|")[1]] += values
for rows in draws.values():
    for d in rows:
        if d["status"] in ("ok", "no_patch_games", "no_valid_games"):
            patch_games[d["tier"]].append(d.get("patch_games", 0))
cap = next(iter(manifests.values()))["settings"]["max_draws_per_game"]
for tier in TIERS:
    values = np.array(patch_games.get(tier, []))
    if not len(values):
        continue
    def need(v):
        given = np.minimum(v, 3).mean()
        return 1 / given if given else float("inf")
    boot = [need(RNG.choice(values, len(values))) for _ in range(2000)]
    hi = np.percentile(boot, 97.5)
    print(f"  {tier:<11} players={len(values):3d} active={np.mean(values > 0):4.0%}  draws per game {need(values):4.1f} "
          f"(95% up to {hi:4.1f})  {'OVER CAP' if hi > cap else 'under cap'} {cap}")

print("\n== T3 tier mix: ladder now vs DPM.LOL workbook (EUW) vs old reference crawl ==")
sheet = pd.read_excel(SHEET, sheet_name="EUW")
ranks = sheet[sheet["Rank"] != "Total"]
book = ranks.groupby(ranks["Tier"].str.upper())["Players_int"].sum()
book = book / book.sum()
old = [m for m in load_matches(Path("ANALYSIS/data")) if not model.is_remake(m)]
old_tier = Counter((m["players"][0].get("metadata") or {}).get("tier") for m in old)
old_share = {t: old_tier.get(t, 0) / len(old) for t in TIERS}

# Mean score of each tier's games on the saved reference, from the pilot (unweighted).
pilot = [m for f in sorted(glob.glob(str(PILOT / "fresh_*.json"))) for m in json.load(open(f))]
scored = model.annotate_player_performance(copy.deepcopy([m for m in pilot if not model.is_remake(m)]))
tier_scores = defaultdict(list)
for m in scored:
    tier_scores[m["sample"]["tier"]] += [p["performanceScore"] for p in m["players"] if p.get("performanceScore") is not None]
offset = {t: np.mean(v) - 50 for t, v in tier_scores.items()}
offset.update({t: offset["MASTER"] for t in ("GRANDMASTER", "CHALLENGER")})
print("  tier means on the saved reference (pilot): " + " ".join(f"{t[:4]}={50 + offset[t]:.1f}" for t in TIERS[:8]))
header = "  tier         " + " ".join(f"{name:>6}" for name in manifests) + "   book    old"
print(header)
shares = {}
for name, manifest in manifests.items():
    players = {t: sum(manifest["ladder"][t].values()) for t in TIERS}
    total = sum(players.values())
    shares[name] = {t: players[t] / total for t in TIERS}
for tier in TIERS:
    print(f"  {tier:<12} " + " ".join(f"{shares[n][tier]:6.1%}" for n in manifests) + f" {book.get(tier, 0):6.1%} {old_share[tier]:6.1%}")
print("  implied mean-score gap vs the old reference's tier mix, sum(dshare x tier offset):")
for name in manifests:
    gap = sum((shares[name][t] - old_share[t]) * offset[t] for t in TIERS)
    print(f"    {name:<5} {gap:+.2f} points")
book_gap = sum((book.get(t, 0) - old_share[t]) * offset[t] for t in TIERS)
print(f"    book  {book_gap:+.2f} points (workbook EUW vs old crawl)")

print("\n== T4 patch window: probe lower bound vs earliest patch game seen ==")
for name, manifest in manifests.items():
    probe = manifest["window"]["probe"]
    fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%m-%d %H:%M")
    gap_h = (probe["first_seen"] - probe["start"]) / 3600
    rejected = Counter(r for d in draws[name] for r in d.get("rejected", {}).values())
    fetched = sum(len(d.get("games", [])) for d in draws[name]) + sum(v for k, v in rejected.items() if k != "already_seen")
    print(f"  {name:<5} start {fmt(probe['start'])}, first patch game seen {fmt(probe['first_seen'])} (gap {gap_h:5.1f} h); "
          f"other_patch {rejected.get('other_patch', 0)}/{fetched} fetched")

print("\n== T5 build_score_reference reads processed/ ==")
for s in servers:
    matches = load_matches(s / "processed")
    rows = collect_features(matches)
    durations = [model.game_duration_minutes(m["metadata"]) for m in matches]
    print(f"  {s.name:<5} matches={len(matches)} remakes={sum(model.is_remake(m) for m in matches)} rows per role="
          f"{ {r: len(rows[r]) for r in ROLES} } length {min(durations):.1f}-{max(durations):.1f} min")

print("\n== T6 size per game, projected to 4,000 games per server ==")
for s in servers:
    games = sum(len(d.get("games", [])) for d in draws[s.name])
    raw = sum(f.stat().st_size for f in (s / "raw").glob("*.gz")) / games
    processed = (s / "processed" / "matches.json").stat().st_size / games
    print(f"  {s.name:<5} raw {raw / 1024:5.1f} KB/game, processed {processed / 1024:5.1f} KB/game -> "
          f"4,000 games: raw {raw * 4000 / 2**20:5.0f} MB, processed/matches.json {processed * 4000 / 2**20:5.0f} MB")

print("\n== T7 patch_start with a time zone ==")
text = "2026-10-21T00:00+02:00"
as_coded = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
correct = datetime.fromisoformat(text).astimezone(timezone.utc)
print(f"  {text}: read as {as_coded.isoformat()}, correct {correct.isoformat()}, off by {(as_coded - correct).total_seconds() / 3600:+.0f} h")

print("\n== T8 HTTP statuses in the smoke run ==")
for name, manifest in manifests.items():
    calls = Counter()
    for run in manifest["runs"]:
        calls.update(run["calls"])
    print(f"  {name:<5} " + ", ".join(f"{k} {v}" for k, v in sorted(calls.items()) if k.startswith("HTTP")))
