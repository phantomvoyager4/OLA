"""Second pass on the surprising results of verify_fetching_hypotheses.py.

H9: within the same players, is the game fetched as their latest game worse
    than games they appear in as a lobby-mate?
H2: does the weighted reference reproduce the app's reference with equal
    weights, and does a resampled game-weighted reference give the same shift?
H11: where do the extra matches in a file come from?

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/double_check_fetching.py
"""

from __future__ import annotations

import contextlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from BACKEND import model
from check_auc import build_reference, score_matches, split_matches

with contextlib.redirect_stdout(io.StringIO()):
    from verify_fetching_hypotheses import SHEET, TIERS, caller_tier, load, weighted_reference

ROLES = model.ROLES
rng = np.random.default_rng(1)


def main() -> None:
    files, matches, first_file, copies = load()
    playable = [m for m in matches.values() if not model.is_remake(m)]

    print("H9 the same players as crawled player vs as lobby-mate")
    scored = model.annotate_player_performance(json.loads(json.dumps(playable)))
    as_caller, as_mate = defaultdict(list), defaultdict(list)
    for m in scored:
        for p in m["players"]:
            if p.get("performanceScore") is None or p.get("teamPosition") not in ROLES:
                continue
            (as_caller if p.get("caller") else as_mate)[p["puuid"]].append((p["performanceScore"], bool(p.get("win")),
                                                                           model.game_duration_minutes(m["metadata"])))
    both = [k for k in as_caller if k in as_mate]
    caller_rows = np.array([as_caller[k][0] for k in both])
    mate_rows = np.array([np.mean(as_mate[k], axis=0) for k in both])
    diff = caller_rows - mate_rows
    boot = np.array([diff[rng.integers(0, len(diff), len(diff))].mean(axis=0) for _ in range(2000)])
    low, high = np.percentile(boot, [2.5, 97.5], axis=0)
    print(f"  players seen both ways: {len(both)}")
    for i, name in enumerate(("score", "win rate", "game length")):
        scale = 100 if name == "win rate" else 1
        print(f"  {name:<12} latest game {caller_rows[:, i].mean() * scale:6.1f}  as lobby-mate {mate_rows[:, i].mean() * scale:6.1f}  "
              f"difference {diff[:, i].mean() * scale:+.1f} [{low[i] * scale:+.1f}, {high[i] * scale:+.1f}]")
    by_tier = defaultdict(list)
    for m in scored:
        caller = next((p for p in m["players"] if p.get("caller")), None)
        if caller is not None:
            by_tier[caller_tier(m)].append(bool(caller.get("win")))
    print("  crawled players' win rate by tier: " + " ".join(f"{t[:4]}={np.mean(by_tier[t]):.0%}(n={len(by_tier[t])})" for t in TIERS if len(by_tier[t]) >= 100))

    print("\nH2 weighted reference checks (seed 0)")
    train, test = split_matches(playable, 0.3, 0)
    overlap = {m["match_id"] for m in train} & {m["match_id"] for m in test}
    standard, _, _ = score_matches(test, build_reference(train))
    equal, _, _ = score_matches(test, weighted_reference(train, lambda m: 1.0))
    print(f"  overlap={len(overlap)}; equal weights vs app reference: mean |d|={np.abs(equal - standard).mean():.3f}, max |d|={np.abs(equal - standard).max():.2f}")
    sheet = pd.read_excel(SHEET, sheet_name="EUW")
    ranks = sheet[sheet["Rank"] != "Total"].copy()
    ranks["games"] = pd.to_numeric(ranks["Players_int"]) * pd.to_numeric(ranks["Avg Games"], errors="coerce")
    games = ranks.groupby(ranks["Tier"].str.upper())["games"].sum()
    game_share = games / games.sum()
    share = Counter(caller_tier(m) for m in train)
    weights = np.array([game_share[caller_tier(m)] / (share[caller_tier(m)] / len(train)) for m in train])
    shifts = []
    for _ in range(5):
        picked = rng.choice(len(train), size=len(train), replace=True, p=weights / weights.sum())
        resampled, _, _ = score_matches(test, build_reference([train[i] for i in picked]))
        shifts.append((resampled - standard).mean())
    weighted, _, _ = score_matches(test, weighted_reference(train, lambda m: game_share[caller_tier(m)] / (share[caller_tier(m)] / len(train))))
    print(f"  mean signed change, weighted function: {(weighted - equal).mean():+.2f}; resampled game-weighted references (5 draws): "
          + " ".join(f"{s:+.2f}" for s in shifts))
    rows = defaultdict(list)
    for m in playable:
        minutes = model.game_duration_minutes(m["metadata"])
        for p in m["players"]:
            if p.get("teamPosition") in ROLES:
                rows[caller_tier(m)].append(model._extract_performance_features(p, minutes))
    print("  feature means by lobby tier: " + " | ".join(
        f"{t[:4]} cs {np.mean([r['farm_pressure'] for r in rows[t]]):.1f} dpm {np.mean([r['damagePerMinute'] for r in rows[t]]):.0f}"
        for t in ("IRON", "SILVER", "PLATINUM", "DIAMOND", "MASTER")))

    print("\nH11 file contents")
    for name, ids in files.items():
        if "SILVER_100_2" in name:
            with open(Path("ANALYSIS/data") / name, encoding="utf-8") as handle:
                payload = json.load(handle)
            days = sorted(matches[i]["metadata"]["gameDateDay"] for i in ids)
            print(f"  {name}: format={type(payload).__name__}, records={len(ids)}, unique ids={len(set(ids))}, "
                  f"also in other files={sum(copies[i] > 1 for i in ids)}, days {days[0]}..{days[-1]}, top days {Counter(days).most_common(3)}")


if __name__ == "__main__":
    main()
