"""Run from the src directory: python -m unittest BACKEND.tests.test_scoring"""

import copy
import json
import unittest
from pathlib import Path
from unittest import mock

from BACKEND import model

EXAMPLE_MATCHES = Path(__file__).resolve().parents[3] / "data" / "example_data" / "401dmg#6969_20.json"


def load_example_matches():
    with open(EXAMPLE_MATCHES, encoding="utf-8") as handle:
        payload = json.load(handle)
    return [match for match in payload if "players" in match]


def scores_of_first_match(matches):
    annotated = model.annotate_player_performance(copy.deepcopy(matches))
    return [player["performanceScore"] for player in annotated[0]["players"]]


class PercentileFromQuantilesTest(unittest.TestCase):
    quantiles = [float(i) for i in range(101)]  # score i sits at percentile i

    def test_ends_are_clamped(self):
        self.assertEqual(model._percentile_from_quantiles(-5.0, self.quantiles), 0.0)
        self.assertEqual(model._percentile_from_quantiles(500.0, self.quantiles), 100.0)

    def test_values_between_quantiles_are_interpolated(self):
        self.assertAlmostEqual(model._percentile_from_quantiles(42.5, self.quantiles), 42.5)

    def test_repeated_quantiles_do_not_divide_by_zero(self):
        flat = [0.0] * 50 + [1.0] * 51
        self.assertEqual(model._percentile_from_quantiles(0.0, flat), 0.0)
        self.assertAlmostEqual(model._percentile_from_quantiles(0.5, flat), 49.5)


class GameDurationTest(unittest.TestCase):
    def test_match_stores_decimal_minutes_and_seconds(self):
        match = model.Match({"info": {"gameDuration": 1629}})  # 27:09
        self.assertEqual(match.gameDuration_sec, 1629)
        self.assertAlmostEqual(match.gameDuration_min, 27.15)

    def test_seconds_are_preferred(self):
        self.assertAlmostEqual(model.game_duration_minutes({"gameDuration_sec": 1629, "gameDuration_min": 27.15}), 27.15)

    def test_legacy_minutes_seconds_value_is_converted(self):
        self.assertAlmostEqual(model.game_duration_minutes({"gameDuration_min": 27.09}), 27.15)
        self.assertAlmostEqual(model.game_duration_minutes({"gameDuration_min": 30.3}), 30.5)  # 30:30 saved as 30.3


class RemakeTest(unittest.TestCase):
    @staticmethod
    def match(seconds=None, legacy_min=None, flag=None):
        metadata = {"gameDuration_sec": seconds} if seconds is not None else {"gameDuration_min": legacy_min}
        player = {"teamPosition": "TOP"} if flag is None else {"teamPosition": "TOP", "gameEndedInEarlySurrender": flag}
        return {"metadata": metadata, "players": [dict(player) for _ in range(10)]}

    def test_riot_flag_decides_when_present(self):
        self.assertTrue(model.is_remake(self.match(seconds=170, flag=True)))
        self.assertFalse(model.is_remake(self.match(seconds=170, flag=False)))

    def test_legacy_matches_use_the_three_minute_limit(self):
        self.assertTrue(model.is_remake(self.match(legacy_min=2.16)))  # 2:16
        self.assertFalse(model.is_remake(self.match(legacy_min=3.08)))  # early surrender at 3:08 is a real game
        self.assertFalse(model.is_remake(self.match(legacy_min=4.54)))

    def test_remakes_are_marked_and_not_scored(self):
        annotated = model.annotate_player_performance([self.match(seconds=100, flag=True)])
        self.assertTrue(annotated[0]["metadata"]["isRemake"])
        self.assertTrue(all(p["performanceScore"] is None and p["performanceBand"] == "remake" for p in annotated[0]["players"]))


class FixedReferenceTest(unittest.TestCase):
    def setUp(self):
        self.matches = load_example_matches()
        self.assertIsNotNone(model.load_score_reference(), "data/static/score_reference.json is missing")

    def test_score_does_not_depend_on_other_matches_in_request(self):
        first_batch = self.matches[:10]
        second_batch = [self.matches[0]] + self.matches[10:]
        self.assertEqual(scores_of_first_match(first_batch), scores_of_first_match(second_batch))

    def test_single_match_is_still_scored(self):
        scores = scores_of_first_match(self.matches[:1])
        self.assertTrue(all(0.0 <= score <= 100.0 for score in scores))
        self.assertGreater(len(set(scores)), 1)  # not everyone is "elite" any more

    def test_falls_back_to_request_comparison_without_reference(self):
        with mock.patch.object(model, "load_score_reference", return_value=None):
            scores = scores_of_first_match(self.matches)
        self.assertTrue(all(0.0 <= score <= 100.0 for score in scores))


if __name__ == "__main__":
    unittest.main()
