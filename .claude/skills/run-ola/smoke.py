"""Smoke-test the running OLA backend on live Riot data.

Fetches /api/matches for one player and checks what the scoring promises:
game durations, remake handling, performance bands, and that every live score
equals what the current code and data/static/score_reference.json produce
(a mismatch means the server runs old code or loaded an old reference).

Run from the repo root while the backend is up:
    PYTHONIOENCODING=utf-8 python .claude/skills/run-ola/smoke.py EUW1 401dmg 6969 --count 5

Exit code 0 = no problems (warnings allowed), 1 = problems listed.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from BACKEND import model  # noqa: E402

BANDS = [(80, "elite"), (60, "strong"), (40, "solid"), (0, "low")]


def band_of(score: float) -> str:
    return next(name for limit, name in BANDS if score >= limit)


def recomputed_percentile(player: dict, minutes: float, reference: dict) -> float | None:
    role = reference["roles"].get(player.get("teamPosition") or "")
    if not role:
        return None
    features = model._extract_performance_features(player, minutes)
    score = sum(
        (features[name] - role["mean"][name]) / role["std"][name] * weight
        for name, weight in model.PERFORMANCE_FEATURE_WEIGHTS.items()
    )
    return round(model._percentile_from_quantiles(score, role["quantiles"]), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("platform", help="e.g. EUW1")
    parser.add_argument("name")
    parser.add_argument("tag")
    parser.add_argument("--count", type=int, default=5, help="matches to fetch; each costs ~1 Riot API call")
    parser.add_argument("--base", default="http://127.0.0.1:8000", help="backend, or http://127.0.0.1:5173 to go through the Vite proxy")
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir()) / "ola_smoke.json")
    args = parser.parse_args()

    url = f"{args.base}/api/matches/{args.platform}/{urllib.parse.quote(args.name)}/{urllib.parse.quote(args.tag)}?count={args.count}"
    with urllib.request.urlopen(url, timeout=300) as response:
        body = response.read()
    args.out.write_bytes(body)
    payload = json.loads(body)
    matches = [m for m in payload if isinstance(m, dict) and "players" in m]
    print(f"GET {url} -> {len(matches)} matches (saved to {args.out})")

    reference = model.load_score_reference()
    problems, warnings = [], []
    if reference is None:
        problems.append("data/static/score_reference.json missing or built for other features")

    checked = 0
    for match in matches:
        mid, meta, players = match["match_id"], match["metadata"], match["players"]
        seconds = meta.get("gameDuration_sec")
        if seconds is None:
            problems.append(f"{mid}: no gameDuration_sec")
            continue
        if meta.get("gameDuration_min") != round(seconds / 60, 2):
            problems.append(f"{mid}: gameDuration_min {meta.get('gameDuration_min')} != {seconds}/60")
        if " - " in str(meta.get("gameDate")):
            start, end = meta["gameDate"].split(" - ")
            span = (datetime.strptime(start[:11] + end, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start, "%Y-%m-%d %H:%M:%S")).total_seconds() % 86400
            if abs(span - seconds) > 2:
                problems.append(f"{mid}: gameDate span {span:.0f}s vs gameDuration_sec {seconds}")

        flagged = any(p.get("gameEndedInEarlySurrender") in (True, "true") for p in players)
        if meta.get("isRemake") is not flagged:
            problems.append(f"{mid}: isRemake={meta.get('isRemake')} but early-surrender flag={flagged}")
        if flagged:
            bad = [p for p in players if p.get("performanceScore") is not None or p.get("performanceBand") != "remake"]
            if bad:
                problems.append(f"{mid}: remake has {len(bad)} scored players")
            continue

        minutes = model.game_duration_minutes(meta)
        for player in players:
            live, band = player.get("performanceScore"), player.get("performanceBand")
            if live is None or not 0 <= live <= 100:
                problems.append(f"{mid}: {player.get('username')} score {live}")
                continue
            if band != band_of(live):
                # Known: the band comes from the unrounded percentile, so 39.97 shows as 40.0 / "low".
                kind = warnings if live in (40.0, 60.0, 80.0) else problems
                kind.append(f"{mid}: score {live} shown with band {band}")
            if reference is not None:
                expected = recomputed_percentile(copy.deepcopy(player), minutes, reference)
                if expected is None:
                    warnings.append(f"{mid}: role {player.get('teamPosition')!r} not in reference, ranked within request")
                elif abs(expected - live) > 0.05:
                    problems.append(f"{mid}: {player.get('username')} live {live} != current code {expected}")
                else:
                    checked += 1

    scored = [p for m in matches if not m["metadata"].get("isRemake") for p in m["players"]]
    print(f"patches: {dict(Counter('.'.join(m['metadata']['gameVersion'].split('.')[:2]) for m in matches))}")
    print(f"remakes: {sum(bool(m['metadata'].get('isRemake')) for m in matches)}, "
          f"shortest game: {min((m['metadata'].get('gameDuration_sec') or 0) for m in matches)}s")
    print(f"scores matching current code + reference: {checked}/{len(scored)}")
    if scored:
        print("band shares %:", {name: round(sum(p['performanceBand'] == name for p in scored) / len(scored) * 100, 1) for _, name in reversed(BANDS)})
    for line in warnings:
        print("WARN", line)
    for line in problems:
        print("FAIL", line)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
