from datetime import datetime
import unittest
from unittest.mock import patch

from BACKEND.pipeline import activity_pipeline


class ActivityPipelineTests(unittest.TestCase):
    @patch("BACKEND.pipeline.Caller")
    def test_returns_dates_without_fetching_profile_metadata(self, caller_class):
        caller = caller_class.return_value
        caller.get_puuid.return_value = "player-puuid"
        caller.last_matches_id_call.return_value = ["MATCH_1", "MATCH_2"]
        caller.last_matches_data_call.return_value = {
            "MATCH_1": {"info": {"gameStartTimestamp": 1_720_310_400_000}},
            "MATCH_2": {"info": {"gameStartTimestamp": 1_720_396_800_000}},
        }

        result = activity_pipeline(
            api_key="test-key",
            player_name="Player",
            player_tag="TAG",
            platform="EUW",
            count=40,
            start=20,
        )

        expected_dates = [
            datetime.fromtimestamp(1_720_310_400).strftime("%Y-%m-%d"),
            datetime.fromtimestamp(1_720_396_800).strftime("%Y-%m-%d"),
        ]
        self.assertEqual(result, {"dates": expected_dates, "matches": 2})
        caller.last_matches_id_call.assert_called_once_with("player-puuid", start=20)
        caller.last_matches_data_call.assert_called_once_with(["MATCH_1", "MATCH_2"])
        caller.player_metadata_call.assert_not_called()
        caller.player_mastery.assert_not_called()

    @patch("BACKEND.pipeline.Caller")
    def test_empty_match_history_is_a_valid_response(self, caller_class):
        caller = caller_class.return_value
        caller.get_puuid.return_value = "player-puuid"
        caller.last_matches_id_call.return_value = []

        result = activity_pipeline(
            api_key="test-key",
            player_name="Player",
            player_tag="TAG",
            platform="EUW",
        )

        self.assertEqual(result, {"dates": [], "matches": 0})
        caller.last_matches_data_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
