"""Summarise a ladder_sampler run: time taken, projection to a target size, and
the drift check with intervals.

The projection uses each drawn player's number of patch games from draws.jsonl,
so it reflects the tier mix and activity of the real run. Intervals come from a
bootstrap over drawn players (projection) and over matches (scores).

Run from src:
    PYTHONPATH=. python ANALYSIS/fetching_sample/analysis/sample_summary.py ANALYSIS/fetching_sample/samples/16.20 --target 4000
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from BACKEND import model

ROUTES = {"EUW1": "europe", "EUN1": "europe", "NA1": "americas", "BR1": "americas", "KR": "asia"}
LOG_TIME = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \[")
RNG = np.random.default_rng(3)


def last_session(log_path: Path) -> dict:
    """Timestamps of the last session in run.log: patch found, quotas set, finished."""
    lines = log_path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if "] Patch " in line or "] Resuming" in line]
    marks = {}
    for line in lines[starts[-1]:] if starts else []:
        match = LOG_TIME.match(line)
        if not match:
            continue
        stamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        for key, needle in (("patch", "] Patch "), ("quotas", "] Quotas:"), ("finished", "] Finished:")):
            if needle in line and key not in marks:
                marks[key] = stamp
    return marks


def per_draw_costs(draws: list, k: int) -> np.ndarray:
    """Rows of (regional calls, games) a draw would give with up to k games per player."""
    rows = []
    for draw in draws:
        if draw["status"] in ("inactive", "repeat_player", "empty_page"):
            rows.append((0.0, 0.0))  # no regional call
            continue
        n = draw.get("patch_games", 0)
        pages = 1 + (n >= 100) + (n >= 200)
        games = min(n, k)
        rows.append((pages + games, games))
    return np.array(rows)


def score_rows(records: list) -> list:
    """Score with the saved reference, the same way the live site does."""
    scored = model.annotate_player_performance(copy.deepcopy(records))
    return [(i, p["performanceScore"], int(bool(p.get("win"))), p["performanceBand"])
            for i, r in enumerate(scored) for p in r["players"] if p.get("performanceScore") is not None]


def drift(rows: list, label: str) -> None:
    matches = sorted({i for i, *_ in rows})
    by_match = {i: [r for r in rows if r[0] == i] for i in matches}

    def stats(sample):
        flat = [r for i in sample for r in by_match[i]]
        return np.mean([r[1] for r in flat]), np.mean([r[3] == "low" for r in flat])

    mean, low = stats(matches)
    boot = [stats(RNG.choice(matches, len(matches))) for _ in range(2000)]
    m_lo, m_hi = np.percentile([b[0] for b in boot], [2.5, 97.5])
    l_lo, l_hi = np.percentile([b[1] for b in boot], [2.5, 97.5])
    bands = Counter(r[3] for r in rows)
    auc = roc_auc_score([r[2] for r in rows], [r[1] for r in rows])
    band_text = "/".join(f"{bands[b] / len(rows):.0%}" for b in ("low", "solid", "strong", "elite"))
    print(f"  {label:<6} games={len(matches):3d} players={len(rows):4d}  mean score {mean:5.1f} [{m_lo:4.1f}, {m_hi:4.1f}]  "
          f"low {low:.0%} [{l_lo:.0%}, {l_hi:.0%}]  bands {band_text}  AUC {auc:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("patch_dir", type=Path)
    parser.add_argument("--target", type=int, default=4000)
    parser.add_argument("--games-per-player", type=int, default=3)
    parser.add_argument("--calls-per-second", type=float, default=90 / 120)
    args = parser.parse_args()
    servers = sorted(p.parent for p in args.patch_dir.glob("*/manifest.json"))

    print("== Time of this run ==")
    all_draws, fetched, accepted = [], 0, 0
    for out in servers:
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        draws = [json.loads(line) for line in (out / "draws.jsonl").read_text(encoding="utf-8").splitlines()]
        all_draws += draws
        accepted += sum(len(d.get("games", [])) for d in draws)
        fetched += sum(len(d.get("games", [])) + sum(r != "already_seen" for r in d.get("rejected", {}).values()) for d in draws)
        run = manifest["runs"][-1]
        started = datetime.fromisoformat(run["started"]).astimezone().replace(tzinfo=None)
        marks = last_session(out / "run.log")
        span = lambda a, b: f"{(b - a).total_seconds() / 60:5.1f} min"
        calls = {k: v for k, v in run["calls"].items() if not k.startswith("HTTP")}
        statuses = Counter(d["status"] for d in draws)
        print(f"  {manifest['platform']:<5} probe {span(started, marks['patch'])}, ladder {span(marks['patch'], marks['quotas'])}, "
              f"games {span(marks['quotas'], marks['finished'])}, total {span(started, marks['finished'])}; "
              f"calls {calls}; draws {len(draws)} ({statuses.get('no_patch_games', 0)} with no patch games)")
    fetch_factor = fetched / accepted
    print(f"  games fetched per game kept: {fetch_factor:.2f} ({fetched - accepted} rejected of {fetched})")

    k = args.games_per_player
    costs = per_draw_costs(all_draws, k)
    def per_game(rows):
        games = rows[:, 1].sum()
        calls = rows[:, 0].sum() + rows[:, 1].sum() * (fetch_factor - 1)
        return calls / games, len(rows) / games
    regional, draws_per_game = per_game(costs)
    boot = np.array([per_game(costs[RNG.integers(0, len(costs), len(costs))]) for _ in range(2000)])
    r_lo, r_hi = np.percentile(boot[:, 0], [2.5, 97.5])
    d_lo, d_hi = np.percentile(boot[:, 1], [2.5, 97.5])
    active = np.mean([d.get("patch_games", 0) > 0 for d in all_draws])
    print(f"\n== Projection to {args.target} games per server, up to {k} games per player ==")
    print(f"  from {len(all_draws)} drawn players: {active:.0%} played this patch; "
          f"route calls per game {regional:.2f} [{r_lo:.2f}, {r_hi:.2f}]; league-page calls per game {draws_per_game:.2f} [{d_lo:.2f}, {d_hi:.2f}]")
    rate = args.calls_per_second
    for route in ("europe", "americas", "asia"):
        names = [s.name for s in servers if ROUTES.get(s.name) == route]
        if not names:
            continue
        games = args.target * len(names)
        hours = lambda c: games * c / rate / 3600
        print(f"  {route:<9} {'+'.join(names):<10} {games:5d} games: {games * regional:6.0f} calls, "
              f"{hours(regional):.1f} h [{hours(r_lo):.1f}, {hours(r_hi):.1f}]")
    page_hours = args.target * draws_per_game / rate / 3600
    print(f"  each server's own budget: {args.target * draws_per_game:.0f} league-page calls, {page_hours:.1f} h, in parallel")

    print("\n== Drift check: new games scored with the saved reference (expect mean 50, low 40%) ==")
    pooled = []
    for out in servers:
        records = list(json.loads((out / "processed" / "matches.json").read_text(encoding="utf-8")).values())
        rows = score_rows(records)
        drift(rows, out.name)
        pooled += [(f"{out.name}:{i}", *rest) for i, *rest in rows]
    drift(pooled, "ALL")


if __name__ == "__main__":
    main()
