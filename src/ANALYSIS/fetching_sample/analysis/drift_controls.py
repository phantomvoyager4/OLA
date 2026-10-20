"""Noise baselines for fresh_analysis: same-size old samples, and a player-cluster bootstrap.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/drift_controls.py ANALYSIS/fetching_sample/samples/pilot_2026-10-20
"""
import sys
from collections import Counter, defaultdict
import numpy as np
sys.argv = [sys.argv[0], sys.argv[1]]
import fresh_analysis as fa  # runs the main report once; reuse its helpers and data
from BACKEND import model

rng = np.random.default_rng(11)
old = [m for m in fa.old if not model.is_remake(m)]

def mean_abs_shift(rows):
    out = []
    for role in fa.ROLES:
        rr = [r for r in rows if r["role"] == role]
        w = np.array([r["w"] for r in rr])
        for f in model.PERFORMANCE_FEATURE_WEIGHTS:
            v = np.array([r["features"][f] for r in rr])
            out.append(abs((np.sum(w * v) / w.sum() - fa.saved["roles"][role]["mean"][f]) / fa.saved["roles"][role]["std"][f]))
    return np.mean(out), np.max(out)

print("\n== CONTROL 1: old-crawl samples of the same size, scored with the saved reference (no drift by construction) ==")
by_tier = defaultdict(list)
for m in old:
    by_tier[fa.caller_tier(m)].append(m)
for n_per_tier, label in ((6, "~49 matches like 'recent' per platform"), (10, "80 matches like one platform")):
    means, mabs, mmax = [], [], []
    for _ in range(40):
        ms = [m for t in fa.TIERS for m in rng.choice(by_tier[t], n_per_tier, replace=len(by_tier[t]) < n_per_tier)]
        share = Counter(fa.caller_tier(m) for m in ms)
        weights = {m["match_id"]: fa.ref_share[fa.caller_tier(m)] / (share[fa.caller_tier(m)] / len(ms)) for m in ms}
        rows = fa.rows_of(fa.score(ms, fa.saved), weights)
        w = np.array([r["w"] for r in rows]); s = np.array([r["score"] for r in rows])
        means.append(np.sum(w * s) / w.sum())
        a, b = mean_abs_shift(rows); mabs.append(a); mmax.append(b)
    print(f"  {label} (40 draws): mean score 2.5-97.5% [{np.percentile(means, 2.5):.1f}, {np.percentile(means, 97.5):.1f}]  "
          f"mean |shift| median {np.median(mabs):.3f} SD (95th {np.percentile(mabs, 95):.3f})  largest |shift| median {np.median(mmax):.2f}")
print("  (in-sample: these old games are part of the saved reference, so this is a lower bound on noise)")

print("\n== CONTROL 2: bootstrap over sampled players instead of matches ==")
for platform, keep, label in (("EUN1", lambda p: True, "EUN1 all"), ("EUN1", lambda p: p >= (16, 17), "EUN1 recent"),
                               ("EUW1", lambda p: p >= (16, 17), "EUW1 recent"), ("NA1", lambda p: True, "NA1 all"),
                               ("EUW1", lambda p: True, "EUW1 all")):
    ms = [m for m in fa.fresh.values() if m["sample"]["platform"] == platform and keep(fa.patch_of(m))]
    share = Counter(m["sample"]["tier"] for m in ms)
    weights = {m["match_id"]: fa.ref_share[m["sample"]["tier"]] / (share[m["sample"]["tier"]] / len(ms)) for m in ms}
    scored = fa.score(ms, fa.saved)
    owner = {i: m["sample"]["puuid"] for i, m in enumerate([m for m in ms if not model.is_remake(m)])}
    rows = fa.rows_of(scored, weights)
    by_player = defaultdict(list)
    for r in rows:
        by_player[owner[r["match"]]].append(r)
    groups = list(by_player.values())
    def wmean(sample):
        flat = [r for g in sample for r in g]
        w = np.array([r["w"] for r in flat]); s = np.array([r["score"] for r in flat])
        return np.sum(w * s) / w.sum()
    boot = [wmean([groups[j] for j in rng.integers(0, len(groups), len(groups))]) for _ in range(2000)]
    print(f"  {label:<12} players={len(groups):3d} matches={len(ms):3d}: mean score {wmean(groups):.1f} [{np.percentile(boot, 2.5):.1f}, {np.percentile(boot, 97.5):.1f}]")
