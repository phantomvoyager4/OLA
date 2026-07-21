import unittest
from unittest.mock import Mock, patch

from BACKEND import riot_api


class RiotApiTransportTests(unittest.TestCase):
    def setUp(self):
        original_cache = riot_api.RIOT_CACHE
        original_limiter = riot_api.RIOT_RATE_LIMITER
        self.addCleanup(setattr, riot_api, "RIOT_CACHE", original_cache)
        self.addCleanup(setattr, riot_api, "RIOT_RATE_LIMITER", original_limiter)
        riot_api.RIOT_CACHE = riot_api.TtlCache()
        riot_api.RIOT_RATE_LIMITER = Mock()

    @patch("BACKEND.riot_api.requests.get")
    def test_successful_response_is_cached_without_api_key_in_identity(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {"puuid": "abc"}
        get.return_value = response
        url = "https://europe.api.riotgames.com/account"

        first = riot_api.riot_get_json(
            url,
            {"api_key": "first-key", "name": "Player"},
            ttl_seconds=60,
        )
        second = riot_api.riot_get_json(
            url,
            {"api_key": "rotated-key", "name": "Player"},
            ttl_seconds=60,
        )

        self.assertEqual(first, (200, {"puuid": "abc"}))
        self.assertEqual(second, first)
        get.assert_called_once()
        riot_api.RIOT_RATE_LIMITER.acquire.assert_called_once()

    @patch("BACKEND.riot_api.time.sleep")
    def test_429_retry_is_bounded(self, sleep):
        requester = Mock()
        requester.get.return_value = Mock(
            status_code=429,
            headers={"Retry-After": "2"},
        )

        status, payload = riot_api.riot_get_json(
            "https://europe.api.riotgames.com/match",
            {"api_key": "test-key"},
            session=requester,
            max_retries=2,
        )

        self.assertEqual((status, payload), (429, None))
        self.assertEqual(requester.get.call_count, 3)
        self.assertEqual(riot_api.RIOT_RATE_LIMITER.acquire.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_rate_limiter_snapshot_reports_usage_and_limits(self):
        limiter = riot_api.DualWindowRateLimiter(
            short_limit=3,
            short_window=1,
            long_limit=5,
            long_window=120,
        )
        limiter.acquire()
        limiter.acquire()

        snapshot = limiter.snapshot()

        self.assertEqual(snapshot["short_used"], 2)
        self.assertEqual(snapshot["short_limit"], 3)
        self.assertEqual(snapshot["long_used"], 2)
        self.assertEqual(snapshot["long_limit"], 5)
        self.assertGreater(snapshot["long_reset_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
