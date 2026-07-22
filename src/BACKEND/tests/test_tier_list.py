from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from BACKEND.tier_list_backend import (
    aggregate_tier_list,
    load_tier_list_snapshot,
    save_tier_list_snapshot,
)
from BACKEND.tier_list_fetcher import (
    TierCollectorConfig,
    data_patch_line,
    is_eligible_match,
    public_patch_line,
)


ROLES = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")


def make_match(
    *,
    patch: str = "16.14.1",
    platform: str = "EUW1",
    queue_id: int = 420,
    duration: int = 1800,
    end_result: str = "GameComplete",
) -> dict:
    participants = []
    for index, role in enumerate(ROLES):
        participants.extend(
            (
                {"championId": index + 1, "teamPosition": role, "win": True},
                {"championId": index + 10, "teamPosition": role, "win": False},
            )
        )
    return {
        "metadata": {"matchId": "EUW1_TEST"},
        "info": {
            "gameVersion": patch,
            "queueId": queue_id,
            "platformId": platform,
            "gameDuration": duration,
            "endOfGameResult": end_result,
            "participants": participants,
            "teams": [
                {"bans": [{"championId": 1}, {"championId": -1}]},
                {"bans": [{"championId": 1}, {"championId": 2}]},
            ],
        },
    }


class TierListAggregationTests(unittest.TestCase):
    def test_aggregates_roles_and_counts_a_repeated_ban_once_per_match(self) -> None:
        match = make_match()
        source = {
            "region": "EUW",
            "rank": "MASTER+",
            "patch": "26.14",
            "dataPatch": "16.14",
            "sourcePlayers": 3,
            "matches": [match, match, match],
        }

        snapshot = aggregate_tier_list(source, min_games=1)

        self.assertEqual(
            snapshot["sample"],
            {"matches": 3, "participants": 30, "players": 3},
        )
        self.assertEqual(len(snapshot["champions"]), 10)
        self.assertEqual({row["role"] for row in snapshot["champions"]}, set(ROLES))
        annie = next(row for row in snapshot["champions"] if row["championId"] == 1)
        self.assertEqual(annie["banRate"], 100.0)

    def test_snapshot_round_trip(self) -> None:
        snapshot = aggregate_tier_list(
            {
                "patch": "26.14",
                "dataPatch": "16.14",
                "sourcePlayers": 1,
                "matches": [make_match()],
            },
            min_games=1,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            save_tier_list_snapshot(snapshot, path)
            self.assertEqual(load_tier_list_snapshot(path), snapshot)


class TierListEligibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = TierCollectorConfig()

    def test_accepts_completed_euw_ranked_solo_game_from_target_patch(self) -> None:
        self.assertTrue(
            is_eligible_match(make_match(), target_patch="26.14", config=self.config)
        )

    def test_maps_public_patch_to_internal_riot_data_version(self) -> None:
        self.assertEqual(data_patch_line("26.14"), "16.14")
        self.assertEqual(data_patch_line("16.14.1"), "16.14")
        self.assertEqual(public_patch_line("16.14.1"), "26.14")

    def test_rejects_wrong_patch_platform_queue_remake_and_abort(self) -> None:
        invalid_matches = (
            make_match(patch="16.13.1"),
            make_match(platform="NA1"),
            make_match(queue_id=440),
            make_match(duration=299),
            make_match(end_result="Abort_Unexpected"),
        )
        for match in invalid_matches:
            with self.subTest(info=match["info"]):
                self.assertFalse(
                    is_eligible_match(match, target_patch="26.14", config=self.config)
                )


if __name__ == "__main__":
    unittest.main()
