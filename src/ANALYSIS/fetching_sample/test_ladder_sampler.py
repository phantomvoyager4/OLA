"""Offline tests for ladder_sampler; no Riot calls.

Run from src:
    python -m unittest ANALYSIS.fetching_sample.test_ladder_sampler
"""

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from ANALYSIS.fetching_sample import ladder_sampler as ls
from BACKEND.tier_list_fetcher import data_patch_line


def fake_division(players):
    reads = []

    def page_length(page):
        reads.append(page)
        return max(0, min(ls.PAGE_SIZE, players - (page - 1) * ls.PAGE_SIZE))

    return page_length, reads


class CountEntriesTest(unittest.TestCase):
    def test_counts_at_page_boundaries(self):
        for players in (0, 1, 204, 205, 206, 410, 411, 12_345, 100_000):
            page_length, _ = fake_division(players)
            self.assertEqual(ls.count_entries(page_length), players, players)

    def test_any_hint_gives_the_exact_count(self):
        for players in (0, 205, 9_999, 100_000):
            for hint in (1, 3, 49, 50, 51, 2_000):
                page_length, _ = fake_division(players)
                self.assertEqual(ls.count_entries(page_length, hint), players, (players, hint))

    def test_a_current_hint_needs_two_reads(self):
        page_length, reads = fake_division(10_000)  # 48 full pages and a partial 49th
        last_page = -(-10_000 // ls.PAGE_SIZE)
        self.assertEqual(ls.count_entries(page_length, last_page), 10_000)
        self.assertLessEqual(len(set(reads)), 2)


class AllocateTest(unittest.TestCase):
    def test_sums_to_total_and_follows_weights(self):
        weights = {"IRON": 34, "GOLD": 243, "MASTER": 9, "CHALLENGER": 0}
        quotas = ls.allocate(4000, weights)
        self.assertEqual(sum(quotas.values()), 4000)
        self.assertEqual(quotas["CHALLENGER"], 0)
        self.assertAlmostEqual(quotas["GOLD"] / 4000, 243 / 286, delta=1 / 4000)

    def test_small_totals(self):
        self.assertEqual(sum(ls.allocate(3, {"A": 1, "B": 1, "C": 1, "D": 1}).values()), 3)
        self.assertEqual(ls.allocate(0, {"A": 1}), {"A": 0})


class PatchTest(unittest.TestCase):
    def test_hotfix_builds_share_a_patch(self):
        self.assertEqual(ls.patch_tuple("16.19.820.7193"), ls.patch_tuple("16.19.823.722"))

    def test_minor_versions_compare_as_numbers(self):
        self.assertNotEqual(ls.patch_tuple("16.2.1"), ls.patch_tuple("16.20.1"))
        self.assertLess(ls.patch_tuple("16.9.1"), ls.patch_tuple("16.10.1"))

    def test_public_name_maps_to_game_version(self):
        self.assertEqual(ls.patch_tuple(data_patch_line("26.20")), (16, 20))


def payload(platform="EUN1", version="16.20.824.8524", queue=420, result="GameComplete", players=10):
    return {"info": {"platformId": platform, "gameVersion": version, "queueId": queue,
                     "endOfGameResult": result, "participants": [{}] * players}}


class CheckMatchTest(unittest.TestCase):
    def check(self, **kwargs):
        return ls.check_match(payload(**kwargs), "EUN1", (16, 20), 420)

    def test_reasons(self):
        self.assertIsNone(self.check())
        self.assertIsNone(self.check(version="16.20.900.1"))
        self.assertEqual(self.check(platform="EUW1"), "other_platform")
        self.assertEqual(self.check(version="16.19.823.722"), "other_patch")
        self.assertEqual(self.check(version="garbage"), "bad_version")
        self.assertEqual(self.check(queue=440), "other_queue")
        self.assertEqual(self.check(result="Abort_Unexpected"), "incomplete")
        self.assertEqual(self.check(players=9), "bad_participants")
        self.assertEqual(ls.check_match({}, "EUN1", (16, 20), 420), "incomplete")


class DrawTest(unittest.TestCase):
    def test_same_index_same_draw(self):
        a = ls.draw_rng(1, "16.20", "EUN1", "GOLD", 7)
        b = ls.draw_rng(1, "16.20", "EUN1", "GOLD", 7)
        self.assertEqual([a.random() for _ in range(5)], [b.random() for _ in range(5)])
        c = ls.draw_rng(1, "16.21", "EUN1", "GOLD", 7)
        self.assertNotEqual(a.random(), c.random())


class StateTest(unittest.TestCase):
    def test_truncated_line_is_dropped_and_file_repaired(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "draws.jsonl"
            good = {"index": 0, "tier": "GOLD", "status": "ok", "puuid": "p", "games": ["EUN1_1"], "rejected": {"EUN1_2": "remake"}}
            path.write_text(json.dumps(good) + "\n" + '{"index": 1, "tier": "GO', encoding="utf-8")
            records = ls.read_draws(path)
            self.assertEqual(records, [good])
            self.assertEqual(path.read_text(encoding="utf-8"), json.dumps(good) + "\n")
            state = ls.SampleState(records)
            self.assertEqual(state.next_index["GOLD"], 1)
            self.assertEqual(state.accepted["GOLD"], 1)
            self.assertEqual(state.matches, {"EUN1_1", "EUN1_2"})


class LimiterTest(unittest.TestCase):
    def test_parse_limits(self):
        self.assertEqual(ls.parse_limits("100:120,20:1"), [(100, 120.0), (20, 1.0)])
        self.assertEqual(ls.parse_limits(None), [])

    def test_waits_when_window_is_full(self):
        limiter = ls.WindowLimiter([(3, 0.2)])
        stop = threading.Event()
        began = time.monotonic()
        for _ in range(4):
            limiter.acquire(stop)
        self.assertGreaterEqual(time.monotonic() - began, 0.19)

    def test_stop_interrupts_a_wait(self):
        limiter = ls.WindowLimiter([(1, 60.0)])
        stop = threading.Event()
        limiter.acquire(stop)
        stop.set()
        with self.assertRaises(ls.Stopped):
            limiter.acquire(stop)


class FakeResponse:
    def __init__(self, status, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body, headers or {}

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.requests = 0

    def get(self, url, params=None, timeout=None):
        self.requests += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_client(outcomes, patience=600):
    settings = {
        "rate_limit": {"short_limit": 1000, "short_window_s": 1.0, "long_limit": 1000, "long_window_s": 1.0, "method_limit_safety": 0.9},
        "request_timeout_s": [1, 1], "max_retries": 2, "network_patience_s": patience,
    }
    client = ls.RiotClient("key", settings, threading.Event())
    session = FakeSession(outcomes)
    client._local.session = session
    waits = []
    client._sleep = waits.append  # record waits instead of sleeping
    return client, session, waits


class ClientTest(unittest.TestCase):
    def get(self, client):
        return client.get("euw1", "/x", "test", None, ls.Counter())

    def test_waits_out_a_dropped_connection(self):
        drop = ls.requests.ConnectionError("down")
        client, session, waits = make_client([drop, drop, drop, FakeResponse(200, [1])])
        self.assertEqual(self.get(client), [1])
        self.assertEqual(len(waits), 3)

    def test_gives_up_after_network_patience(self):
        drop = ls.requests.ConnectionError("down")
        client, _, waits = make_client([drop] * 50, patience=30)
        with self.assertRaises(ls.RiotError):
            self.get(client)
        self.assertGreaterEqual(sum(waits), 30)

    def test_application_429_pauses_the_route(self):
        throttled = FakeResponse(429, headers={"Retry-After": "0.05", "X-Rate-Limit-Type": "application"})
        client, session, _ = make_client([throttled, FakeResponse(200, {"ok": True})])
        began = time.monotonic()
        self.assertEqual(self.get(client), {"ok": True})
        self.assertGreaterEqual(time.monotonic() - began, 0.04)

    def test_rejected_key_and_not_found(self):
        client, _, _ = make_client([FakeResponse(403)])
        with self.assertRaises(ls.KeyRejected):
            self.get(client)
        client, _, _ = make_client([FakeResponse(404)])
        self.assertIsNone(self.get(client))

    def test_server_errors_run_out(self):
        client, session, _ = make_client([FakeResponse(503)] * 10)
        with self.assertRaises(ls.RiotError):
            self.get(client)
        self.assertEqual(session.requests, 3)  # max_retries=2 -> 3 attempts


class LadderCacheTest(unittest.TestCase):
    def test_second_count_reads_no_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            run = ls.PlatformRun.__new__(ls.PlatformRun)
            run.platform, run.out_root, run.out = "EUN1", Path(folder), None
            run.settings = {"tiers": ["IRON", "MASTER"], "ladder_reuse_hours": 24}
            reads = []

            def league_page(tier, division, page):
                reads.append((tier, division, page))
                return [{}] * max(0, min(ls.PAGE_SIZE, 1000 - (page - 1) * ls.PAGE_SIZE))

            run.league_page = league_page
            run.log = lambda message: None
            apex = {"MASTER": [{}] * 7}
            first = run.count_ladder(apex)
            self.assertEqual(first, {"IRON": {d: 1000 for d in ls.DIVISIONS}, "MASTER": {"I": 7}})
            self.assertTrue(reads)
            reads.clear()
            self.assertEqual(run.count_ladder(apex), first)
            self.assertEqual(reads, [])


if __name__ == "__main__":
    unittest.main()
