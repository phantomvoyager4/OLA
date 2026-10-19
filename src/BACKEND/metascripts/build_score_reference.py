"""Build the fixed scoring reference from the collected match dataset.

The API standardizes each performance feature against the player's role and
turns the weighted sum into a percentile. This script computes the per-role
mean and standard deviation of every feature, plus the percentiles of the final
score, once from the whole dataset and saves them to data/static, so live
scores no longer depend on which other matches happen to be in a request.

Run from the src directory:
    python -m BACKEND.metascripts.build_score_reference --data-dir ANALYSIS/data
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from BACKEND.model import (
    FEATURE_VERSION,
    PERFORMANCE_FEATURE_WEIGHTS,
    ROLES,
    SCORE_REFERENCE_PATH,
    _extract_performance_features,
    game_duration_minutes,
    is_remake,
)

MIN_ROWS_PER_ROLE = 200  # below this a role keeps the old per-request comparison


def load_matches(data_dir: Path) -> list[dict]:
    matches = {}
    for path in sorted(data_dir.glob("*.json")):
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload.values() if isinstance(payload, dict) else payload
        for match in items:
            if isinstance(match, dict) and "players" in match:
                match_id = match.get("match_id") or (match.get("metadata") or {}).get("matchId")
                matches[match_id] = match  # the same match can appear in two files
    return list(matches.values())


def collect_features(matches: list[dict]) -> dict[str, list[dict]]:
    rows = {role: [] for role in ROLES}
    for match in matches:
        if is_remake(match):  # remakes say nothing about performance
            continue
        duration = game_duration_minutes(match.get("metadata") or {})
        for player in match["players"]:
            role = player.get("teamPosition")
            if role in rows:
                rows[role].append(_extract_performance_features(player, duration))
    return rows


def role_reference(feature_rows: list[dict]) -> dict:
    count = len(feature_rows)
    means, stds = {}, {}
    for name in PERFORMANCE_FEATURE_WEIGHTS:
        values = [row[name] for row in feature_rows]
        mean = sum(values) / count
        variance = sum((value - mean) ** 2 for value in values) / count
        means[name] = mean
        stds[name] = math.sqrt(variance) if variance > 0 else 1.0

    scores = sorted(
        sum((row[name] - means[name]) / stds[name] * weight for name, weight in PERFORMANCE_FEATURE_WEIGHTS.items())
        for row in feature_rows
    )
    # quantiles[i] = score at the i-th percentile, i = 0..100
    quantiles = [scores[round(i * (count - 1) / 100)] for i in range(101)]
    return {"count": count, "mean": means, "std": stds, "quantiles": quantiles}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, required=True, help="folder with data_full_*.json files")
    parser.add_argument("--out", type=Path, default=SCORE_REFERENCE_PATH)
    args = parser.parse_args()

    matches = load_matches(args.data_dir)
    rows = collect_features(matches)

    roles = {}
    for role, feature_rows in rows.items():
        if len(feature_rows) < MIN_ROWS_PER_ROLE:
            print(f"Skipping {role}: only {len(feature_rows)} rows")
            continue
        roles[role] = role_reference(feature_rows)
        print(f"{role}: {len(feature_rows)} rows")

    days = sorted(
        (m.get("metadata") or {}).get("gameDateDay") for m in matches if (m.get("metadata") or {}).get("gameDateDay")
    )
    reference = {
        "features": list(PERFORMANCE_FEATURE_WEIGHTS),
        "featureVersion": FEATURE_VERSION,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "matches": len(matches),
            "rows": sum(role["count"] for role in roles.values()),
            "firstDay": days[0] if days else None,
            "lastDay": days[-1] if days else None,
            "excludes": "remakes",
        },
        "roles": roles,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(reference, handle, indent=1)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
