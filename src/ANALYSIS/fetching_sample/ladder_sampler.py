"""Collect a ladder-sampled set of ranked solo/duo games for one patch.

Replaces the snowball crawl in fetching_script.py. Players are drawn at random
from Riot's ranked ladder (league-v4): each tier gets games in proportion to its
player count, each division within a tier in proportion to its own, and every
drawn player gives up to games_per_player random games from the target patch.
A game counts only if its platformId, queueId, end-of-game result and
gameVersion (major.minor; hotfix builds share a patch) match the target.

Run from src, with the backend stopped (it spends the same key budget):
    python -m ANALYSIS.fetching_sample.ladder_sampler
    python -m ANALYSIS.fetching_sample.ladder_sampler --regions EUN1 --games-per-region 20
    python -m ANALYSIS.fetching_sample.ladder_sampler --report-only

Settings come from settings.json next to this file. patch "current" reads each
platform's Data Dragon realm, and patch_start "auto" finds when that patch went
live from apex players' histories, so a rerun on the next patch needs no edits.
"auto" only works for the patch that is live now; for an older one give
patch_start as an ISO date.

Output, one folder per patch and platform (<output_dir>/<patch>/<platform>/):
    manifest.json            settings, patch window, ladder counts, quotas, calls, status
    draws.jsonl              one line per drawn player; a rerun resumes from it
    raw/<match_id>.json.gz   Riot's match payload, unchanged
    processed/matches.json   today's Match/Player shape, for
                             build_score_reference --data-dir <that folder>
    report.txt, run.log      end-of-run checks and the log
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import math
import os
import random
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

SRC_PATH = Path(__file__).resolve().parents[2]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from BACKEND import model  # noqa: E402
from BACKEND.model import Match, Player  # noqa: E402
from BACKEND.pipeline import load_api_key  # noqa: E402
from BACKEND.tier_list_fetcher import data_patch_line, patch_line  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_SETTINGS = HERE / "settings.json"
PAGE_SIZE = 205  # league-v4 entries per page
DIVISIONS = ("I", "II", "III", "IV")
APEX_ENDPOINTS = {"MASTER": "masterleagues", "GRANDMASTER": "grandmasterleagues", "CHALLENGER": "challengerleagues"}
# platform -> (match-v5 route, Data Dragon realm). Riot counts the rate limit per
# route, so EUW1 and EUN1 share "europe" while NA1 and KR run on budgets of their own.
PLATFORMS = {
    "EUW1": ("europe", "euw"), "EUN1": ("europe", "eune"), "TR1": ("europe", "tr"), "RU": ("europe", "ru"),
    "NA1": ("americas", "na"), "BR1": ("americas", "br"), "LA1": ("americas", "lan"), "LA2": ("americas", "las"),
    "KR": ("asia", "kr"), "JP1": ("asia", "jp"),
}
MAX_CONSECUTIVE_ERRORS = 10
MAX_THROTTLED_RETRIES = 20

_PRINT_LOCK = threading.Lock()
_FILE_LOCK = threading.Lock()


class Stopped(RuntimeError):
    """The run is stopping (Ctrl-C or a rejected key)."""


class KeyRejected(RuntimeError):
    """Riot answered 401/403: the key is missing, wrong or expired."""


class RiotError(RuntimeError):
    """A request still failed after all retries."""


# ---------------------------------------------------------------- patches


def patch_tuple(version: str) -> tuple[int, int]:
    """'16.20.824.8524' or '16.20' -> (16, 20); hotfix builds share a patch."""
    major, minor = patch_line(version).split(".")
    return int(major), int(minor)


def patch_name(line: tuple[int, int]) -> str:
    return f"{line[0]}.{line[1]}"


def realm_patch(realm: str) -> tuple[int, int] | None:
    """The data patch Data Dragon publishes for a realm, or None if unreachable."""
    try:
        response = requests.get(f"https://ddragon.leagueoflegends.com/realms/{realm}.json", timeout=(3.05, 15.0))
        response.raise_for_status()
        return patch_tuple(data_patch_line(response.json()["v"]))
    except (requests.RequestException, ValueError, KeyError):
        return None


def check_match(payload: dict | None, platform: str, target: tuple[int, int], queue_id: int) -> str | None:
    """Return None if the game belongs in the sample, else why it doesn't."""
    info = (payload or {}).get("info") or {}
    if not info:
        return "incomplete"
    # A history covers every server on the route, so a drawn NA1 player can return LA1 games.
    if info.get("platformId") != platform:
        return "other_platform"
    if info.get("queueId") != queue_id:
        return "other_queue"
    try:
        line = patch_tuple(info.get("gameVersion", ""))
    except ValueError:
        return "bad_version"
    if line != target:
        return "other_patch"
    if info.get("endOfGameResult", "GameComplete") != "GameComplete":
        return "incomplete"
    if len(info.get("participants") or []) != 10:
        return "bad_participants"
    return None


# ---------------------------------------------------------------- rate limits and transport


def parse_limits(header: str | None) -> list[tuple[int, float]]:
    """'100:120,20:1' -> [(100, 120.0), (20, 1.0)]."""
    windows = []
    for part in (header or "").split(","):
        limit, _, seconds = part.strip().partition(":")
        if limit.isdigit() and seconds:
            windows.append((int(limit), float(seconds)))
    return windows


class WindowLimiter:
    """Sliding-window limiter for one Riot budget, pausable for Retry-After."""

    def __init__(self, windows):
        self.windows = [(max(1, int(limit)), float(seconds)) for limit, seconds in windows]
        self._stamps = [deque() for _ in self.windows]
        self._paused_until = 0.0
        self._condition = threading.Condition()

    def pause(self, seconds: float) -> None:
        with self._condition:
            self._paused_until = max(self._paused_until, time.monotonic() + seconds)

    def acquire(self, stop: threading.Event) -> None:
        with self._condition:
            while True:
                if stop.is_set():
                    raise Stopped()
                now = time.monotonic()
                wait = self._paused_until - now
                for (limit, seconds), stamps in zip(self.windows, self._stamps):
                    while stamps and stamps[0] <= now - seconds:
                        stamps.popleft()
                    if len(stamps) >= limit:
                        wait = max(wait, stamps[0] + seconds - now)
                if wait <= 0:
                    for stamps in self._stamps:
                        stamps.append(now)
                    return
                self._condition.wait(timeout=min(wait, 0.5))


class RiotClient:
    """GET Riot JSON with one limiter per route, plus per-method limits Riot reports."""

    def __init__(self, api_key: str, settings: dict, stop: threading.Event):
        limits = settings["rate_limit"]
        self.app_windows = [(limits["short_limit"], limits["short_window_s"]), (limits["long_limit"], limits["long_window_s"])]
        self.method_safety = limits["method_limit_safety"]
        self.timeout = tuple(settings["request_timeout_s"])
        self.max_retries = settings["max_retries"]
        self.network_patience = float(settings["network_patience_s"])
        self.api_key = api_key
        self.stop = stop
        self._lock = threading.Lock()
        self._app: dict[str, WindowLimiter] = {}
        self._method: dict[str, WindowLimiter] = {}
        self._local = threading.local()
        self.limits_seen: dict[str, dict] = {}

    def _app_limiter(self, host: str) -> WindowLimiter:
        with self._lock:
            if host not in self._app:
                self._app[host] = WindowLimiter(self.app_windows)
            return self._app[host]

    def _session(self) -> requests.Session:
        session = getattr(self._local, "session", None)
        if session is None:
            # The key goes in a header so it never appears in a URL or log.
            session = self._local.session = requests.Session()
            session.headers["X-Riot-Token"] = self.api_key
        return session

    def _learn_limits(self, host: str, method: str, headers) -> None:
        key = f"{host}:{method}"
        with self._lock:
            if key in self.limits_seen:
                return
            self.limits_seen[key] = {"app": headers.get("X-App-Rate-Limit"), "method": headers.get("X-Method-Rate-Limit")}
            windows = [(math.floor(limit * self.method_safety), seconds) for limit, seconds in parse_limits(headers.get("X-Method-Rate-Limit"))]
            if windows:
                self._method[key] = WindowLimiter(windows)

    def _sleep(self, seconds: float) -> None:
        if self.stop.wait(seconds):
            raise Stopped()

    def get(self, host: str, path: str, method: str, params: dict | None, tally: Counter):
        """Return parsed JSON, or None for 404. Raise RiotError when retries run out.

        Server errors get max_retries attempts. A dropped connection is waited out
        for up to network_patience_s, and 429s, which are normal back-pressure while
        the backend shares the key, get an allowance of their own.
        """
        url = f"https://{host}.api.riotgames.com{path}"
        last, server_errors, throttled, network_waited = "no response", 0, 0, 0.0
        while server_errors <= self.max_retries and throttled <= MAX_THROTTLED_RETRIES:
            backoff = min(8.0, 2 ** server_errors + random.uniform(0, 0.25))
            method_limiter = self._method.get(f"{host}:{method}")
            if method_limiter is not None:
                method_limiter.acquire(self.stop)
            self._app_limiter(host).acquire(self.stop)
            tally[host] += 1
            try:
                response = self._session().get(url, params=params, timeout=self.timeout)
            except requests.RequestException as error:
                last = f"{type(error).__name__}: {str(error)[:160]}"
                if network_waited >= self.network_patience:
                    break
                if network_waited == 0:
                    with _PRINT_LOCK:
                        print(f"Network error on {host} ({type(error).__name__}); retrying for up to {self.network_patience:.0f}s", flush=True)
                wait = min(60.0, 5.0 + network_waited / 2)
                network_waited += wait
                self._sleep(wait)
                continue
            network_waited = 0.0
            self._learn_limits(host, method, response.headers)
            status = response.status_code
            tally[f"HTTP {status}"] += 1
            if status == 200:
                try:
                    return response.json()
                except ValueError:
                    last, server_errors = "invalid JSON", server_errors + 1
                    self._sleep(backoff)
                    continue
            if status in (401, 403):
                raise KeyRejected(f"HTTP {status} from {host} {method}")
            if status == 404:
                return None
            last = f"HTTP {status}"
            if status == 429:
                throttled += 1
                try:
                    retry_after = float(response.headers.get("Retry-After") or backoff)
                except ValueError:
                    retry_after = backoff
                limit_type = response.headers.get("X-Rate-Limit-Type", "")
                if limit_type == "application":
                    self._app_limiter(host).pause(retry_after)  # every thread on this route waits
                elif limit_type == "method" and method_limiter is not None:
                    method_limiter.pause(retry_after)
                else:
                    self._sleep(retry_after)
                continue
            if status >= 500:
                server_errors += 1
                self._sleep(backoff)
                continue
            break
        raise RiotError(f"{host} {method} failed: {last}")


# ---------------------------------------------------------------- ladder


def count_entries(page_length, hint_pages: int | None = None) -> int:
    """Count a division's players from as few page reads as possible.

    page_length(p) is the number of entries on page p; every page before the last
    holds PAGE_SIZE. hint_pages, the last page of a previous count, usually
    settles it in two reads; without it the search doubles, then bisects.
    """
    seen: dict[int, int] = {}

    def full(page: int) -> bool:
        if page not in seen:
            seen[page] = page_length(page)
        return seen[page] == PAGE_SIZE

    low, high = 0, max(1, int(hint_pages or 1))
    if full(high):
        low, high = high, high * 2
        while full(high):
            low, high = high, high * 2
    elif high > 1 and full(high - 1):
        low = high - 1
    while high - low > 1:
        middle = (low + high) // 2
        if full(middle):
            low = middle
        else:
            high = middle
    full(high)
    return (high - 1) * PAGE_SIZE + seen[high]


def allocate(total: int, weights: dict) -> dict:
    """Split total into whole numbers proportional to weights (largest remainder)."""
    weight_sum = sum(w for w in weights.values() if w > 0)
    if total <= 0 or weight_sum <= 0:
        return {key: 0 for key in weights}
    exact = {key: total * w / weight_sum for key, w in weights.items() if w > 0}
    quotas = {key: math.floor(value) for key, value in exact.items()}
    left = total - sum(quotas.values())
    for key in sorted(exact, key=lambda k: (exact[k] - quotas[k], k), reverse=True)[:left]:
        quotas[key] += 1
    return {key: quotas.get(key, 0) for key in weights}


def draw_rng(seed, patch: str, platform: str, tier: str, index: int) -> random.Random:
    """Each draw's randomness depends only on its index, so a resumed run repeats it exactly."""
    return random.Random(f"{seed}|{patch}|{platform}|{tier}|{index}")


# ---------------------------------------------------------------- state


def read_draws(path: Path) -> list[dict]:
    """Read draws.jsonl, dropping a line cut off by a crash so appends stay valid."""
    if not path.exists():
        return []
    records, kept, broken = [], [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
            kept.append(line)
        except json.JSONDecodeError:
            broken = True
    if broken:
        path.write_text("".join(f"{line}\n" for line in kept), encoding="utf-8")
    return records


class SampleState:
    def __init__(self, records=()):
        self.next_index = Counter()
        self.draws = Counter()
        self.accepted = Counter()
        self.status = Counter()
        self.puuids: set[str] = set()
        self.matches: set[str] = set()
        for record in records:
            self.add(record)

    def add(self, record: dict) -> None:
        tier = record["tier"]
        self.next_index[tier] = max(self.next_index[tier], record["index"] + 1)
        self.draws[tier] += 1
        self.accepted[tier] += len(record.get("games", []))
        self.status[record["status"]] += 1
        if record.get("puuid"):
            self.puuids.add(record["puuid"])
        self.matches.update(record.get("games", []))
        self.matches.update(record.get("rejected", {}))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def write_raw(path: Path, payload: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    os.replace(temporary, path)


def read_raw(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


# ---------------------------------------------------------------- one platform


class PlatformRun:
    def __init__(self, platform: str, settings: dict, client: RiotClient, out_root: Path):
        self.platform = platform
        self.route, self.realm = PLATFORMS[platform]
        self.host = platform.lower()
        self.settings = settings
        self.client = client
        self.out_root = out_root
        self.calls = Counter()
        self.out: Path | None = None
        self.started = datetime.now(timezone.utc)

    # -- logging and requests

    def log(self, message: str) -> None:
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} [{self.platform}] {message}"
        with _PRINT_LOCK:
            print(line, flush=True)
            if self.out is not None and self.out.exists():
                with open(self.out / "run.log", "a", encoding="utf-8") as handle:
                    handle.write(line + "\n")

    def league_page(self, tier: str, division: str, page: int) -> list:
        path = f"/lol/league/v4/entries/{self.settings['queue_type']}/{tier}/{division}"
        entries = self.client.get(self.host, path, "league-entries", {"page": page}, self.calls)
        if entries is None:
            raise RiotError(f"league page {tier} {division} {page} not found")
        return entries

    def apex_entries(self, tier: str) -> list:
        path = f"/lol/league/v4/{APEX_ENDPOINTS[tier]}/by-queue/{self.settings['queue_type']}"
        league = self.client.get(self.host, path, "league-apex", None, self.calls) or {}
        entries = [{**entry, "tier": tier} for entry in league.get("entries", []) if entry.get("puuid")]
        return sorted(entries, key=lambda entry: entry["puuid"])  # Riot's order varies; a resumed draw must not

    def match_ids(self, puuid: str, start: int, end: int) -> list:
        ids = []
        path = f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids"
        for page in range(self.settings["max_match_pages"]):
            params = {"queue": self.settings["queue_id"], "startTime": start, "endTime": end, "start": page * 100, "count": 100}
            batch = self.client.get(self.route, path, "match-ids", params, self.calls)
            if not batch:
                break
            ids.extend(batch)
            if len(batch) < 100:
                break
        return ids

    def match(self, match_id: str) -> dict | None:
        return self.client.get(self.route, f"/lol/match/v5/matches/{match_id}", "match", None, self.calls)

    # -- setup

    def resolve_target(self) -> tuple[tuple[int, int] | None, str]:
        wanted = self.settings["patch"]
        if wanted != "current":
            return patch_tuple(data_patch_line(str(wanted))), "settings"
        return realm_patch(self.realm), f"Data Dragon realm {self.realm}"

    def probe_window(self, apex: dict, target, window_end: int) -> tuple[tuple[int, int] | None, dict | None]:
        """Find when the target patch went live here from apex players' histories.

        A platform moves every game to the new gameVersion at once (no overlap was
        found in 3,488 games), so the newest pre-patch game in a player's history
        is a lower bound for the start, and the oldest patch game an upper bound.
        """
        lookback = window_end - int(self.settings["probe_lookback_days"] * 86400)
        rng = random.Random(f"{self.settings['seed']}|probe|{self.platform}")
        candidates = []
        for tier in ("CHALLENGER", "GRANDMASTER", "MASTER"):
            entries = [entry for entry in apex.get(tier, []) if not entry.get("inactive")]
            rng.shuffle(entries)
            candidates.extend(entries)
        cache: dict[str, tuple | None] = {}

        def version_at(match_id):
            if match_id not in cache:
                info = (self.match(match_id) or {}).get("info") or {}
                ok = info.get("platformId") == self.platform and info.get("gameVersion")
                cache[match_id] = (patch_tuple(info["gameVersion"]), info["gameStartTimestamp"] // 1000) if ok else None
            return cache[match_id]

        bounds, newest_seen = [], Counter()
        for entry in candidates[: self.settings["probe_players"] * 5]:
            if len(bounds) >= self.settings["probe_players"]:
                break
            ids = self.match_ids(entry["puuid"], lookback, window_end)
            newest = version_at(ids[0]) if len(ids) >= 2 else None
            if newest is None:
                continue
            newest_seen[patch_name(newest[0])] += 1
            if target is None:
                target = newest[0]
            if newest[0] != target:
                continue
            oldest = version_at(ids[-1])
            if oldest is None or oldest[0] == target:
                continue  # no pre-patch game within reach
            low, high, usable = 0, len(ids) - 1, True  # ids[low] on the patch, ids[high] before it
            while high - low > 1:
                middle = (low + high) // 2
                found = version_at(ids[middle])
                if found is None:
                    usable = False  # another platform's game: can't tell which side it is on
                    break
                low, high = (middle, high) if found[0] == target else (low, middle)
            if usable:
                bounds.append({"last_before": version_at(ids[high])[1], "first_on_patch": version_at(ids[low])[1]})
        if not bounds:
            self.log(f"Patch probe found no boundary; newest apex games were on {dict(newest_seen)}")
            return target, None
        return target, {
            "start": max(bound["last_before"] for bound in bounds),
            "first_seen": min(bound["first_on_patch"] for bound in bounds),
            "probes": bounds,
            "newest_seen": dict(newest_seen),
        }

    def count_ladder(self, apex: dict) -> dict:
        """Count players per division, saving each count as soon as it is known.

        A count younger than ladder_reuse_hours is used as is, so a run cut off
        while counting picks up where it stopped. An older one is the starting
        hint for a recount, which then usually needs two page reads.
        """
        cache_path = self.out_root / "ladder_cache.json"

        def read_cache() -> dict:
            return json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

        with _FILE_LOCK:
            cached = read_cache().get(self.platform, {})
        counts = {}
        for tier in self.settings["tiers"]:
            if tier in APEX_ENDPOINTS:
                counts[tier] = {"I": len(apex.get(tier, []))}
                continue
            counts[tier] = {}
            for division in DIVISIONS:
                known = cached.get(tier, {}).get(division)
                if known:
                    age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(known["at"])).total_seconds() / 3600
                    if age_hours < self.settings["ladder_reuse_hours"]:
                        counts[tier][division] = known["players"]
                        continue
                players = count_entries(
                    lambda page: len(self.league_page(tier, division, page)),
                    math.ceil(known["players"] / PAGE_SIZE) if known else None,
                )
                counts[tier][division] = players
                with _FILE_LOCK:
                    cache = read_cache()
                    cache.setdefault(self.platform, {}).setdefault(tier, {})[division] = {
                        "players": players, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
                    write_json(cache_path, cache)
            self.log(f"Ladder {tier}: {counts[tier]}")
        return counts

    def setup(self) -> dict | None:
        target, target_source = self.resolve_target()
        if target is not None:
            self.out = self.out_root / patch_name(target) / self.platform
            manifest_path = self.out / "manifest.json"
            if manifest_path.exists():
                return self.resume(json.loads(manifest_path.read_text(encoding="utf-8")))

        apex = {tier: self.apex_entries(tier) for tier in self.settings["tiers"] if tier in APEX_ENDPOINTS}
        window_end = int(self.started.timestamp())
        start_setting = self.settings["patch_start"]
        if start_setting == "auto":
            target, probe = self.probe_window(apex, target, window_end)
            if probe is None:
                self.log("Could not find when the patch started here. Rerun later, or set patch_start in settings.")
                return None
            window = {"start": probe["start"], "end": window_end, "source": "probe", "probe": probe}
        else:
            start = int(datetime.fromisoformat(start_setting).replace(tzinfo=timezone.utc).timestamp())
            window = {"start": start, "end": window_end, "source": "settings"}
        if target is None:
            self.log("No target patch: Data Dragon was unreachable and the probe found no games.")
            return None

        self.out = self.out_root / patch_name(target) / self.platform
        if (self.out / "manifest.json").exists():  # Data Dragon was down, the probe named the patch
            return self.resume(json.loads((self.out / "manifest.json").read_text(encoding="utf-8")))
        (self.out / "raw").mkdir(parents=True, exist_ok=True)
        start_text = datetime.fromtimestamp(window["start"], timezone.utc).isoformat(timespec="minutes")
        self.log(f"Patch {patch_name(target)} ({target_source}); games from {start_text} until this run started")

        # Written before the ladder is counted, so a rerun keeps this patch window.
        manifest = {
            "platform": self.platform,
            "route": self.route,
            "patch": patch_name(target),
            "patch_source": target_source,
            "window": window,
            "settings": self.settings,
            "created": self.started.isoformat(timespec="seconds"),
            "git_commit": git_commit(),
            "status": "counting ladder",
        }
        write_json(self.out / "manifest.json", manifest)
        return self.prepare(manifest, apex)

    def resume(self, manifest: dict) -> dict | None:
        old = manifest["settings"]
        for key in ("seed", "games_per_player", "queue_id", "tiers"):
            if old.get(key) != self.settings.get(key):
                self.log(f"Refusing to resume: setting {key!r} changed ({old.get(key)!r} -> {self.settings.get(key)!r}). "
                         "Use another output_dir or restore the setting.")
                return None
        manifest["settings"] = {**old, "games_per_region": self.settings["games_per_region"]}
        self.log(f"Resuming patch {manifest['patch']} sample started {manifest['created']}")
        apex = {tier: self.apex_entries(tier) for tier in self.settings["tiers"] if tier in APEX_ENDPOINTS}
        return self.prepare(manifest, apex)

    def prepare(self, manifest: dict, apex: dict) -> dict:
        self.manifest = manifest
        if "ladder" not in manifest:
            manifest["ladder"] = self.count_ladder(apex)
            manifest["ladder_counted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            manifest["status"] = "running"
        counts = manifest["ladder"]
        players = {tier: sum(counts[tier].values()) for tier in self.settings["tiers"]}
        manifest["quotas"] = allocate(self.settings["games_per_region"], players)
        write_json(self.out / "manifest.json", manifest)
        self.manifest, self.apex, self.target = manifest, apex, patch_tuple(manifest["patch"])
        self.log(f"Quotas: {manifest['quotas']}")
        return manifest

    # -- sampling

    def pick_entry(self, rng: random.Random, tier: str) -> tuple[dict | None, dict]:
        if tier in APEX_ENDPOINTS:
            entries = self.apex[tier]
            return (rng.choice(entries) if entries else None), {"division": "I"}
        counts = self.manifest["ladder"][tier]
        divisions = [division for division in DIVISIONS if counts.get(division)]
        division = rng.choices(divisions, weights=[counts[d] for d in divisions])[0]
        position = rng.randrange(counts[division])
        page, slot = position // PAGE_SIZE + 1, position % PAGE_SIZE
        entries = self.league_page(tier, division, page)
        where = {"division": division, "page": page, "slot": slot}
        if not entries:
            return None, where
        if slot >= len(entries):  # the division shrank since it was counted
            slot = where["slot"] = rng.randrange(len(entries))
        return {**entries[slot], "tier": tier}, where

    def run_draw(self, state: SampleState, tier: str, index: int) -> dict:
        rng = draw_rng(self.settings["seed"], self.manifest["patch"], self.platform, tier, index)
        entry, where = self.pick_entry(rng, tier)
        record = {"index": index, "tier": tier, **where, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if entry is None:
            return {**record, "status": "empty_page"}
        record |= {key: entry.get(key) for key in ("puuid", "rank", "leaguePoints", "wins", "losses", "inactive", "veteran", "freshBlood", "hotStreak")}
        if self.settings["skip_inactive"] and entry.get("inactive"):
            return {**record, "status": "inactive"}
        if entry["puuid"] in state.puuids:
            return {**record, "status": "repeat_player"}

        window = self.manifest["window"]
        ids = self.match_ids(entry["puuid"], window["start"], window["end"])
        record["patch_games"] = len(ids)
        if not ids:
            return {**record, "status": "no_patch_games"}

        wanted = min(self.settings["games_per_player"], self.manifest["quotas"][tier] - state.accepted[tier])
        accepted, rejected, attempts = [], {}, 0
        for match_id in rng.sample(ids, len(ids)):
            if len(accepted) >= wanted or attempts >= 2 * wanted + 2:
                break
            if match_id in state.matches:
                rejected[match_id] = "already_seen"
                continue
            attempts += 1
            raw_path = self.out / "raw" / f"{match_id}.json.gz"
            payload = read_raw(raw_path) if raw_path.exists() else self.match(match_id)
            reason = check_match(payload, self.platform, self.target, self.settings["queue_id"]) if payload else "not_found"
            if reason is None:
                info = payload["info"]
                # Same rule the scorer applies, so the sample holds no game it would skip.
                if model.is_remake({"players": info["participants"], "metadata": {"gameDuration_sec": info.get("gameDuration")}}):
                    reason = "remake"
            if reason:
                rejected[match_id] = reason
                continue
            if not raw_path.exists():
                write_raw(raw_path, payload)
            accepted.append(match_id)
        return {**record, "status": "ok" if accepted else "no_valid_games", "games": accepted, "rejected": rejected}

    def sample(self) -> str:
        draws_path = self.out / "draws.jsonl"
        state = SampleState(read_draws(draws_path))
        quotas, tiers = self.manifest["quotas"], self.settings["tiers"]
        target = sum(quotas.values())
        estimate = (target - sum(state.accepted.values())) * self.settings["expected_calls_per_game"]
        self.log(f"{sum(state.accepted.values())}/{target} games so far; about {estimate:.0f} more {self.route} calls")
        began, errors, since_log = time.monotonic(), 0, 0
        accepted_at_start = sum(state.accepted.values())
        while True:
            open_tiers = [t for t in tiers if quotas[t] and state.accepted[t] < quotas[t]
                          and state.draws[t] < quotas[t] * self.settings["max_draws_per_game"]]
            if not open_tiers:
                break
            # Fill tiers in turn, so a run stopped early is still proportional.
            tier = min(open_tiers, key=lambda t: (state.accepted[t] / quotas[t], -quotas[t], t))
            try:
                record = self.run_draw(state, tier, state.next_index[tier])
            except RiotError as error:
                errors += 1
                self.log(f"Draw failed ({error}); {errors} in a row")
                if errors >= MAX_CONSECUTIVE_ERRORS:
                    return "stopped: repeated request errors"
                continue
            errors = 0
            with open(draws_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            state.add(record)
            since_log += 1
            if since_log >= 25:
                since_log = 0
                done = sum(state.accepted.values())
                rate = (done - accepted_at_start) / max(1.0, time.monotonic() - began)
                eta = (target - done) / rate / 3600 if rate else float("nan")
                self.log(f"{done}/{target} games, {sum(state.draws.values())} draws, "
                         f"{self.calls[self.route]} {self.route} calls this run, about {eta:.1f} h left")
        short = {t: f"{state.accepted[t]}/{quotas[t]}" for t in tiers if state.accepted[t] < quotas[t]}
        if short:
            self.log(f"Some tiers ran out of draws before their quota: {short}")
        return "complete" if not short else "complete with short tiers"

    def finish(self, status: str) -> None:
        if self.out is None or not (self.out / "manifest.json").exists():
            return
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        manifest["status"] = status
        manifest["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        runs = manifest.setdefault("runs", [])
        runs.append({"started": self.started.isoformat(timespec="seconds"), "ended": manifest["updated"],
                     "status": status, "calls": dict(self.calls)})
        manifest["limits_seen"] = self.client.limits_seen
        write_json(self.out / "manifest.json", manifest)
        build_outputs(self.out, self.log)


# ---------------------------------------------------------------- outputs and report


def to_record(payload: dict, draw: dict, platform: str, queue_type: str) -> dict:
    """Convert a raw match the way the live site does, marking the drawn player."""
    info = payload["info"]
    duration = info.get("gameDuration", 0)
    players = []
    for participant in info["participants"]:
        player = Player(participant, game_duration_sec=duration).to_dict()
        player["caller"] = participant.get("puuid") == draw["puuid"]
        player["metadata"] = (
            {key: draw.get(key) for key in ("tier", "rank", "leaguePoints", "wins", "losses")} | {"queueType": queue_type}
            if player["caller"] else {}
        )
        players.append(player)
    return {
        "match_id": payload["metadata"]["matchId"],
        "metadata": Match(payload).to_dict(),
        "players": players,
        "sample": {"platform": platform, "tier": draw["tier"], "division": draw.get("division"),
                   "draw": f"{draw['tier']}:{draw['index']}", "puuid": draw["puuid"]},
    }


def build_outputs(out: Path, log=print) -> None:
    """Write processed/matches.json and report.txt from what is on disk; no API calls."""
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    draws = read_draws(out / "draws.jsonl")
    processed = {}
    for draw in draws:
        for match_id in draw.get("games", []):
            path = out / "raw" / f"{match_id}.json.gz"
            if path.exists():
                processed[match_id] = to_record(read_raw(path), draw, manifest["platform"], manifest["settings"]["queue_type"])
    write_json(out / "processed" / "matches.json", processed)
    report = make_report(manifest, draws, list(processed.values()))
    (out / "report.txt").write_text(report, encoding="utf-8")
    log("Report:\n" + report)


def make_report(manifest: dict, draws: list, records: list) -> str:
    lines = [f"{manifest['platform']} patch {manifest['patch']}: status {manifest.get('status')}"]
    window = manifest["window"]
    fmt = lambda ts: datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"window {fmt(window['start'])} .. {fmt(window['end'])} ({window['source']})")
    quotas = manifest.get("quotas", {})
    accepted = Counter(); tried = Counter()
    for draw in draws:
        tried[draw["tier"]] += 1
        accepted[draw["tier"]] += len(draw.get("games", []))
    lines.append("tier          quota  games  draws")
    for tier, quota in quotas.items():
        if quota or accepted[tier]:
            lines.append(f"  {tier:<11} {quota:5d}  {accepted[tier]:5d}  {tried[tier]:5d}")
    lines.append(f"draws by status: {dict(Counter(d['status'] for d in draws))}")
    lines.append(f"rejected games: {dict(Counter(r for d in draws for r in d.get('rejected', {}).values()))}")
    calls = Counter()
    for run in manifest.get("runs", []):
        calls.update(run.get("calls", {}))
    games = len(records)
    route_calls = calls.get(manifest["route"], 0)
    lines.append(f"calls: {dict(calls)}; {manifest['route']} calls per game {route_calls / games:.2f}" if games else f"calls: {dict(calls)}")
    if not records:
        return "\n".join(lines) + "\n"

    versions = Counter(".".join(r["metadata"]["gameVersion"].split(".")[:2]) for r in records)
    platforms = Counter(r["metadata"]["platformId"] for r in records)
    lines.append(f"patch purity: {dict(versions)}; platforms: {dict(platforms)}")
    per_player = Counter(len(d.get("games", [])) for d in draws if d.get("games"))
    lines.append(f"games per sampled player: {dict(sorted(per_player.items()))}")

    # Clustering: the snowball crawl shared a player in 2.3% of pairs and put a
    # median 97% of a file's games on its 3 busiest days.
    owners = defaultdict(list)
    for i, record in enumerate(records):
        for player in record["players"]:
            owners[player["puuid"]].append(i)
    draw_of = [r["sample"]["draw"] for r in records]
    sharing = {(a, b) for ids in owners.values() for a in ids for b in ids if a < b and draw_of[a] != draw_of[b]}
    per_draw = Counter(draw_of)
    pairs = games * (games - 1) // 2 - sum(n * (n - 1) // 2 for n in per_draw.values())
    days = Counter(r["metadata"]["gameDateDay"] for r in records)
    busiest = sum(n for _, n in days.most_common(3)) / games
    share_text = f"{len(sharing)}/{pairs} ({len(sharing) / pairs:.2%})" if pairs else "n/a"
    lines.append(f"pairs of games from different draws sharing a player: {share_text}; "
                 f"games on the 3 busiest days {busiest:.0%} over {len(days)} days")

    reference = model.load_score_reference()
    if reference is None:
        lines.append("drift check: no usable score reference")
        return "\n".join(lines) + "\n"
    scored = model.annotate_player_performance(copy.deepcopy(records))
    rows = [(p["performanceScore"], bool(p.get("win")), p["performanceBand"]) for r in scored for p in r["players"]
            if p.get("performanceScore") is not None]
    if rows:
        scores = [s for s, _, _ in rows]
        bands = Counter(b for _, _, b in rows)
        band_text = " ".join(f"{b} {bands[b] / len(rows):.0%}" for b in ("low", "solid", "strong", "elite"))
        auc_text = ""
        try:
            from sklearn.metrics import roc_auc_score
            if len({w for _, w, _ in rows}) == 2:
                auc_text = f", AUC {roc_auc_score([w for _, w, _ in rows], scores):.3f}"
        except ImportError:
            pass
        lines.append(f"drift check vs saved reference ({len(rows)} players): mean score {sum(scores) / len(rows):.1f} "
                     f"(expect 50), bands {band_text} (expect 40/20/20/20){auc_text}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- main


def load_settings(args) -> dict:
    settings = json.loads(Path(args.settings).read_text(encoding="utf-8"))
    overrides = {"regions": args.regions, "games_per_region": args.games_per_region, "games_per_player": args.games_per_player,
                 "patch": args.patch, "patch_start": args.patch_start}
    settings.update({key: value for key, value in overrides.items() if value is not None})
    unknown = [region for region in settings["regions"] if region not in PLATFORMS]
    if unknown:
        raise SystemExit(f"Unknown regions {unknown}; known: {sorted(PLATFORMS)}")
    bad_tiers = [t for t in settings["tiers"] if t not in APEX_ENDPOINTS and t not in
                 ("IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND")]
    if bad_tiers:
        raise SystemExit(f"Unknown tiers {bad_tiers}")
    if not 1 <= settings["games_per_player"] <= 20:
        raise SystemExit("games_per_player must be between 1 and 20")
    return settings


def warn_if_backend_running() -> None:
    try:
        status = requests.get("http://127.0.0.1:8000/api/rate-limit", timeout=0.5).json()
    except (requests.RequestException, ValueError):
        return
    print(f"Warning: the backend on 127.0.0.1:8000 is running ({status.get('long_used')}/{status.get('long_limit')} "
          "calls in its last 2 minutes). It spends the same key; stop it (docker compose stop backend) for full speed.", flush=True)


def keep_awake() -> None:
    """On macOS, hold off sleep until this process exits.

    A closed lid on battery still sleeps (that cut the first smoke run), so
    long runs need the lid open or the charger in.
    """
    if sys.platform != "darwin":
        return
    try:
        subprocess.Popen(["caffeinate", "-i", "-s", "-w", str(os.getpid())])
    except OSError:
        print("Warning: caffeinate is unavailable; keep the machine awake yourself.", flush=True)


def run_platform(run: PlatformRun, stop: threading.Event, results: dict) -> None:
    status = "not started"
    try:
        if run.setup() is None:
            status = "not started: setup failed"
        else:
            status = run.sample()
    except KeyRejected as error:
        status = f"stopped: API key rejected ({error}); renew the key and rerun to resume"
        stop.set()
    except Stopped:
        status = "interrupted; rerun to resume"
    except RiotError as error:
        status = f"stopped: {error}"
    finally:
        results[run.platform] = status
        try:
            run.finish(status)
        except Exception as error:  # the report must never hide the sampling status
            run.log(f"Could not write outputs: {type(error).__name__}: {error}")
        run.log(f"Finished: {status}; calls this run {dict(run.calls)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--settings", default=str(DEFAULT_SETTINGS))
    parser.add_argument("--regions", nargs="+")
    parser.add_argument("--games-per-region", type=int)
    parser.add_argument("--games-per-player", type=int)
    parser.add_argument("--patch", help="'current', or a patch such as 16.21 or 26.21")
    parser.add_argument("--patch-start", help="'auto' or an ISO date such as 2026-10-21T00:00")
    parser.add_argument("--report-only", action="store_true", help="rebuild processed/ and report.txt from disk; no API calls")
    args = parser.parse_args()
    settings = load_settings(args)
    out_root = (Path(args.settings).resolve().parent / settings["output_dir"]).resolve()

    if args.report_only:
        for region in settings["regions"]:
            folders = sorted(out_root.glob(f"*/{region}/manifest.json"), key=lambda p: patch_tuple(p.parent.parent.name))
            wanted = [p for p in folders if settings["patch"] == "current" or p.parent.parent.name == patch_name(patch_tuple(data_patch_line(settings["patch"])))]
            if wanted:
                build_outputs(wanted[-1].parent)
            else:
                print(f"No sample for {region} in {out_root}")
        return

    api_key = load_api_key()
    if not api_key:
        raise SystemExit("RIOT_API_KEY is missing from .env")
    warn_if_backend_running()
    keep_awake()
    stop = threading.Event()
    client = RiotClient(api_key, settings, stop)
    results: dict[str, str] = {}
    runs = [PlatformRun(region, settings, client, out_root) for region in settings["regions"]]
    threads = [threading.Thread(target=run_platform, args=(run, stop, results), name=run.platform) for run in runs]
    for thread in threads:
        thread.start()
    try:
        for thread in threads:
            while thread.is_alive():
                thread.join(timeout=0.5)
    except KeyboardInterrupt:
        print("Stopping after the current requests; progress is saved and a rerun resumes.", flush=True)
        stop.set()
        for thread in threads:
            thread.join()
    print("\nSummary:")
    for run in runs:
        print(f"  {run.platform}: {results.get(run.platform)} -> {run.out}")
    if not all(str(results.get(run.platform, "")).startswith("complete") for run in runs):
        sys.exit(1)


if __name__ == "__main__":
    main()
