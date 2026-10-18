"""Evaluate the live performance score as a win predictor on held-out matches.

Matches are split into train and test by match_id, the score reference (role
means, standard deviations and percentiles) is built from train matches only,
and test matches are scored with the same code path the API uses.

Run from the src directory:
    python check_auc.py [--seeds 0 1 2 3 4] [--test-size 0.3]
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

from BACKEND import model
from BACKEND.metascripts.build_score_reference import (
    ROLES,
    collect_features,
    load_matches,
    role_reference,
)

DATA_DIR = Path(__file__).resolve().parent / "ANALYSIS" / "data"


def split_matches(matches: list[dict], test_size: float, seed: int) -> tuple[list[dict], list[dict]]:
    """Split whole matches, so no game contributes players to both sides."""
    ids = [match["match_id"] for match in matches]
    train_idx, test_idx = next(GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed).split(ids, groups=ids))
    train = [matches[i] for i in train_idx]
    test = [matches[i] for i in test_idx]
    overlap = {m["match_id"] for m in train} & {m["match_id"] for m in test}
    if overlap:
        raise RuntimeError(f"{len(overlap)} match_ids appear in both train and test")
    return train, test


def build_reference(matches: list[dict]) -> dict:
    rows = collect_features(matches)
    return {"features": list(model.PERFORMANCE_FEATURE_WEIGHTS), "roles": {role: role_reference(rows[role]) for role in ROLES}}


def score_matches(matches: list[dict], reference: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Score with the API's own function, using the given reference instead of the saved file."""
    playable = [copy.deepcopy(m) for m in matches if not model.is_remake(m)]
    original = model.load_score_reference
    model.load_score_reference = lambda: reference
    try:
        annotated = model.annotate_player_performance(playable)
    finally:
        model.load_score_reference = original

    scores, wins, roles = [], [], []
    for match in annotated:
        for player in match["players"]:
            if player.get("teamPosition") in ROLES:
                scores.append(player["performanceScore"])
                wins.append(int(bool(player.get("win"))))
                roles.append(player["teamPosition"])
    return np.array(scores), np.array(wins), np.array(roles)


def auc_report(scores: np.ndarray, wins: np.ndarray, roles: np.ndarray) -> dict:
    report = {"ALL": roc_auc_score(wins, scores)}
    for role in ROLES:
        mask = roles == role
        report[role] = roc_auc_score(wins[mask], scores[mask])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--test-size", type=float, default=0.3)
    args = parser.parse_args()

    matches = load_matches(args.data_dir)
    full_reference = build_reference(matches)
    print(f"matches={len(matches)}")

    columns = ["ALL", *ROLES]
    print(f"{'seed':>4} {'reference':<10} " + " ".join(f"{c:>8}" for c in columns))
    for seed in args.seeds:
        train, test = split_matches(matches, args.test_size, seed)
        print(f"seed={seed} train matches={len(train)} test matches={len(test)} overlap=0")
        for label, reference in (("train-only", build_reference(train)), ("all-data", full_reference)):
            report = auc_report(*score_matches(test, reference))
            print(f"{seed:>4} {label:<10} " + " ".join(f"{report[c]:8.4f}" for c in columns))


if __name__ == "__main__":
    main()
