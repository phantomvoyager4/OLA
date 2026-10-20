"""Score fresh league-sampled games with the saved reference and measure drift.

A reference that fits a population gives its random games a mean score of 50
and bands of 40/20/20/20 (low/solid/strong/elite). Fresh games are reweighted
to the reference's tier mix; intervals come from a bootstrap over matches.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/fresh_analysis.py ANALYSIS/fetching_sample/samples/pilot_2026-10-20
"""
from __future__ import annotations

import copy
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from BACKEND import model
from BACKEND.metascripts.build_score_reference import ROLES, load_matches
from check_auc import DATA_DIR, build_reference, split_matches

TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER"]
BANDS = ["low", "solid", "strong", "elite"]
EXPECTED = {"low": 0.40, "solid": 0.20, "strong": 0.20, "elite": 0.20}
RNG = np.random.default_rng(7)

saved = model.load_score_reference()
assert saved is not None, "saved reference refused"


def caller_tier(match):
    tier = next((p.get("metadata") or {}).get("tier") for p in match["players"])
    return "MASTER" if tier in ("GRANDMASTER", "CHALLENGER") else tier


def score(matches, reference):
    playable = [copy.deepcopy(m) for m in matches if not model.is_remake(m)]
    original = model.load_score_reference
    model.load_score_reference = lambda: reference
    try:
        model.annotate_player_performance(playable)
    finally:
        model.load_score_reference = original
    return playable


def rows_of(scored, weights=None):
    rows = []
    for i, m in enumerate(scored):
        duration = model.game_duration_minutes(m["metadata"])
        for p in m["players"]:
            if p.get("performanceScore") is None or p.get("teamPosition") not in ROLES:
                continue
            rows.append({
                "match": i, "w": (weights or {}).get(m["match_id"], 1.0), "score": p["performanceScore"],
                "win": int(bool(p.get("win"))), "role": p["teamPosition"],
                "band": model._performance_band(math.floor(p["performanceScore"] + 0.5)),
                "features": model._extract_performance_features(p, duration), "puuid": p.get("puuid"),
            })
    return rows


def summary(rows, label):
    by_match = defaultdict(list)
    for r in rows:
        by_match[r["match"]].append(r)
    groups = list(by_match.values())

    def stats(sample):
        flat = [r for g in sample for r in g]
        w = np.array([r["w"] for r in flat])
        s = np.array([r["score"] for r in flat])
        bands = {b: np.sum(w * np.array([r["band"] == b for r in flat])) / w.sum() for b in BANDS}
        return np.sum(w * s) / w.sum(), bands

    mean, bands = stats(groups)
    boot = [stats([groups[j] for j in RNG.integers(0, len(groups), len(groups))]) for _ in range(400)]
    lo, hi = np.percentile([b[0] for b in boot], [2.5, 97.5])
    band_ci = {b: np.percentile([x[1][b] for x in boot], [2.5, 97.5]) for b in BANDS}
    s = np.array([r["score"] for r in rows]); w = np.array([r["win"] for r in rows])
    auc = roc_auc_score(w, s) if len(set(w)) > 1 else float("nan")
    band_text = "  ".join(f"{b} {bands[b]:.1%} [{band_ci[b][0]:.0%},{band_ci[b][1]:.0%}]" for b in BANDS)
    print(f"{label:<26} matches={len(groups):4d} rows={len(rows):5d}  mean score {mean:5.1f} [{lo:4.1f}, {hi:4.1f}]  AUC {auc:.3f}")
    print(f"{'':<26} {band_text}")
    return mean


def feature_drift(rows, label):
    shifts = []
    for role in ROLES:
        rr = [r for r in rows if r["role"] == role]
        if not rr:
            continue
        w = np.array([r["w"] for r in rr])
        for f in model.PERFORMANCE_FEATURE_WEIGHTS:
            v = np.array([r["features"][f] for r in rr])
            shifts.append(((np.sum(w * v) / w.sum() - saved["roles"][role]["mean"][f]) / saved["roles"][role]["std"][f], role, f))
    shifts.sort(key=lambda x: -abs(x[0]))
    print(f"  {label}: mean |shift| {np.mean([abs(s[0]) for s in shifts]):.3f} SD; largest: "
          + ", ".join(f"{role} {f} {s:+.2f}" for s, role, f in shifts[:4]))


# Baseline: old EUW data, reference built on train only, held-out test.
old = load_matches(DATA_DIR)
ref_share = Counter(caller_tier(m) for m in old if not model.is_remake(m))
total = sum(ref_share.values())
ref_share = {t: ref_share.get(t, 0) / total for t in TIERS}
print("reference tier mix:", {t: f"{v:.1%}" for t, v in ref_share.items()})

print("\n== Baseline (old crawl, held-out) ==")
for seed in range(2):
    train, test = split_matches(old, 0.3, seed)
    assert not ({m["match_id"] for m in train} & {m["match_id"] for m in test})
    summary(rows_of(score(test, build_reference(train))), f"old EUW test seed {seed}")

old_ids = {m["match_id"] for m in old}
fresh_dir = Path(sys.argv[1])
fresh = {}
for path in sorted(fresh_dir.glob("fresh_*.json")):
    for m in json.loads(path.read_text()):
        fresh[m["match_id"]] = m
print(f"\nfresh matches={len(fresh)}, also in old crawl={len(set(fresh) & old_ids)}")
print("fresh patches:", Counter(".".join(m["metadata"]["gameVersion"].split(".")[:2]) for m in fresh.values()))
print("fresh remakes:", sum(model.is_remake(m) for m in fresh.values()))

print("\n== Fresh games scored with the saved reference (tier-weighted to the reference mix) ==")
fresh_rows = {}
for platform in ("EUW1", "EUN1", "NA1"):
    ms = [m for m in fresh.values() if m["sample"]["platform"] == platform]
    if not ms:
        continue
    share = Counter(m["sample"]["tier"] for m in ms)
    weights = {m["match_id"]: ref_share[m["sample"]["tier"]] / (share[m["sample"]["tier"]] / len(ms)) for m in ms}
    rows = rows_of(score(ms, saved), weights)
    fresh_rows[platform] = rows
    summary(rows, f"{platform} fresh")
    feature_drift(rows, platform)

def patch_of(m):
    major, minor = m["metadata"]["gameVersion"].split(".")[:2]
    return int(major), int(minor)


print("\n== By patch age, all platforms, tier-weighted (16.13 is the reference patch) ==")
groups = {
    "recent 16.17-16.20": lambda p: p >= (16, 17),
    "middle 16.14-16.16": lambda p: (16, 14) <= p <= (16, 16),
    "old <=16.13": lambda p: p <= (16, 13),
}
for label, keep in groups.items():
    for platform in ("EUW1", "EUN1", "NA1", None):
        ms = [m for m in fresh.values() if keep(patch_of(m)) and (platform is None or m["sample"]["platform"] == platform)]
        if len(ms) < 15:
            continue
        share = Counter(m["sample"]["tier"] for m in ms)
        weights = {m["match_id"]: ref_share[m["sample"]["tier"]] / (share[m["sample"]["tier"]] / len(ms)) for m in ms}
        rows = rows_of(score(ms, saved), weights)
        summary(rows, f"{label} {platform or 'ALL'}")
        if label.startswith("recent"):
            feature_drift(rows, f"{label} {platform or 'ALL'}")

print("\n== Per tier, all platforms, unweighted (each tier vs the all-tier reference) ==")
for tier in TIERS:
    ms = [m for m in fresh.values() if m["sample"]["tier"] == tier]
    if ms:
        summary(rows_of(score(ms, saved)), f"{tier}")

print("\n== Latest game vs a random game from the last 20, same sampled player ==")
pairs = defaultdict(dict)
for m in fresh.values():
    s = m["sample"]
    scored = score([m], saved)
    if not scored:
        continue
    for p in scored[0]["players"]:
        if p.get("puuid") == s["puuid"] and p.get("performanceScore") is not None:
            pairs[(s["platform"], s["puuid"])][s["kind"]] = (p["performanceScore"], int(bool(p.get("win"))))
both = [v for v in pairs.values() if "latest" in v and "random" in v]
d_score = np.array([v["latest"][0] - v["random"][0] for v in both])
d_win = np.array([v["latest"][1] - v["random"][1] for v in both])
boot = [(RNG.choice(d_score, len(d_score)).mean(), RNG.choice(d_win, len(d_win)).mean()) for _ in range(2000)]
ci_s = np.percentile([b[0] for b in boot], [2.5, 97.5]); ci_w = np.percentile([b[1] for b in boot], [2.5, 97.5])
print(f"  pairs={len(both)}  score latest-random {d_score.mean():+.1f} [{ci_s[0]:+.1f}, {ci_s[1]:+.1f}]  "
      f"win latest-random {d_win.mean():+.1%} [{ci_w[0]:+.1%}, {ci_w[1]:+.1%}]")
print(f"  win rate latest {np.mean([v['latest'][1] for v in both]):.1%}, random {np.mean([v['random'][1] for v in both]):.1%}")
