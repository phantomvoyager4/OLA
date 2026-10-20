"""Second-opinion offline checks of the sampling verdicts.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/offline_challenge.py
"""
from __future__ import annotations

import copy
import math
from collections import Counter

import numpy as np

from BACKEND import model
from BACKEND.metascripts.build_score_reference import ROLES, load_matches
from check_auc import DATA_DIR, build_reference, score_matches, split_matches


def band(score):
    return model._performance_band(math.floor(score + 0.5))


def compare(test, ref_a, ref_b):
    a, _, _ = score_matches(test, ref_a)
    b, _, _ = score_matches(test, ref_b)
    flips = np.mean([band(x) != band(y) for x, y in zip(a, b)])
    return np.mean(b - a), np.mean(np.abs(b - a)), flips, len(a)


def without_callers(matches):
    out = []
    for m in matches:
        m2 = copy.copy(m)
        m2["players"] = [p for p in m["players"] if not p.get("caller")]
        out.append(m2)
    return out


matches = load_matches(DATA_DIR)
playable = [m for m in matches if not model.is_remake(m)]
print(f"matches={len(matches)} playable={len(playable)}")

print("\nH9 impact: reference without the crawled player's row vs full reference (held-out test)")
for seed in range(5):
    train, test = split_matches(matches, 0.3, seed)
    overlap = len({m["match_id"] for m in train} & {m["match_id"] for m in test})
    signed, absd, flips, n = compare(test, build_reference(train), build_reference(without_callers(train)))
    print(f"  seed {seed} overlap={overlap} n={n}: mean change {signed:+.2f}, mean |change| {absd:.2f}, band changed {flips:.1%}")

print("\nH7 noise at band level: two disjoint half references, scored on held-out test")
rng = np.random.default_rng(0)
for seed in range(3):
    train, test = split_matches(matches, 0.2, seed)
    ids = [m["match_id"] for m in train]
    rng.shuffle(ids)
    half = set(ids[: len(ids) // 2])
    a = [m for m in train if m["match_id"] in half]
    b = [m for m in train if m["match_id"] not in half]
    overlap = len({m["match_id"] for m in a} & {m["match_id"] for m in b}) + len(
        {m["match_id"] for m in train} & {m["match_id"] for m in test})
    signed, absd, flips, n = compare(test, build_reference(a), build_reference(b))
    print(f"  seed {seed} overlap={overlap} halves {len(a)}/{len(b)} n={n}: mean |diff| {absd:.2f}, band differs {flips:.1%}")

print("\nH13 rows without a usable teamPosition (dropped by the reference, scored live)")
positions = Counter(p.get("teamPosition") for m in playable for p in m["players"])
odd = {k: v for k, v in positions.items() if k not in ROLES}
print(f"  {sum(odd.values())}/{sum(positions.values())} rows: {odd}")

print("\nH15 evaluation leakage: held-out player rows whose account also appears in train")
for seed in range(3):
    train, test = split_matches(matches, 0.3, seed)
    train_ids = {p.get("puuid") for m in train for p in m["players"]}
    rows = [p for m in test if not model.is_remake(m) for p in m["players"]]
    shared = sum(p.get("puuid") in train_ids for p in rows)
    print(f"  seed {seed}: {shared}/{len(rows)} ({shared / len(rows):.1%})")

print("\nH9 mechanism: crawled row win rate vs its own lobby-mates' rate (expected 50%)")
caller_rows = [p for m in playable for p in m["players"] if p.get("caller")]
print(f"  crawled rows {len(caller_rows)}, win rate {np.mean([bool(p.get('win')) for p in caller_rows]):.1%}")
