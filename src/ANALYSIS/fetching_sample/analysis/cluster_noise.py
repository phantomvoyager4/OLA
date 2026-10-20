"""H1 x H7: does building the reference from different crawls add noise beyond
building it from different random matches?

A held-out set of matches is scored with two references built from disjoint
halves of the remaining matches. The halves are split either by match or by
crawl file (balanced per tier; tiers with one file are split by match).

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/cluster_noise.py
"""

from __future__ import annotations

import contextlib
import io
import math
from collections import defaultdict

import numpy as np

from BACKEND import model
from check_auc import build_reference, score_matches, split_matches

with contextlib.redirect_stdout(io.StringIO()):
    from verify_fetching_hypotheses import load
import re


def main() -> None:
    files, matches, first_file, _ = load()
    playable = [m for m in matches.values() if not model.is_remake(m)]
    tier_of = lambda name: re.match(r"data_full_[^_]+_([A-Z]+)_", name).group(1)
    print(f"{'seed':<6}{'split':<10}{'half sizes':>14}{'overlap':>9}{'disagree':>10}{'one full ref':>14}")
    for seed in (0, 1, 2):
        rng = np.random.default_rng(seed)
        rest, held = split_matches(playable, 0.2, seed)
        held_ids = {m["match_id"] for m in held}
        by_match = split_matches(rest, 0.5, seed)

        files_by_tier = defaultdict(list)
        for name in files:
            files_by_tier[tier_of(name)].append(name)
        side = {}
        for names in files_by_tier.values():
            for i, name in enumerate(rng.permutation(names)):
                side[name] = i % 2 if len(names) > 1 else None
        half_a, half_b = [], []
        for m in rest:
            s = side[first_file[m["match_id"]]]
            (half_a if (s if s is not None else rng.integers(0, 2)) == 0 else half_b).append(m)

        for label, (a, b) in (("by match", by_match), ("by file", (half_a, half_b))):
            ids_a, ids_b = {m["match_id"] for m in a}, {m["match_id"] for m in b}
            overlap = len(ids_a & ids_b) + len((ids_a | ids_b) & held_ids)
            sa, _, _ = score_matches(held, build_reference(a))
            sb, _, _ = score_matches(held, build_reference(b))
            d = np.abs(sa - sb).mean()
            full = d / math.sqrt(2) * math.sqrt(min(len(a), len(b)) / len(playable))
            print(f"{seed:<6}{label:<10}{f'{len(a)}/{len(b)}':>14}{overlap:>9}{d:>10.2f}{full:>14.2f}")


if __name__ == "__main__":
    main()
