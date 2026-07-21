"""Shared Riot API transport with caching, throttling, and bounded retries."""

from __future__ import annotations

from collections import OrderedDict, deque
import random
import threading
import time
from typing import Any

import requests


class DualWindowRateLimiter:
    """Thread-safe sliding-window limiter for a single Riot API key."""

    def __init__(
        self,
        short_limit: int = 18,
        short_window: float = 1.0,
        long_limit: int = 90,
        long_window: float = 120.0,
    ) -> None:
        self.short_limit = short_limit
        self.short_window = short_window
        self.long_limit = long_limit
        self.long_window = long_window
        self._short_requests: deque[float] = deque()
        self._long_requests: deque[float] = deque()
        self._condition = threading.Condition()

    @staticmethod
    def _discard_expired(timestamps: deque[float], cutoff: float) -> None:
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

    def acquire(self) -> None:
        with self._condition:
            while True:
                now = time.monotonic()
                self._discard_expired(self._short_requests, now - self.short_window)
                self._discard_expired(self._long_requests, now - self.long_window)

                short_available = len(self._short_requests) < self.short_limit
                long_available = len(self._long_requests) < self.long_limit
                if short_available and long_available:
                    self._short_requests.append(now)
                    self._long_requests.append(now)
                    return

                waits = []
                if not short_available:
                    waits.append(self._short_requests[0] + self.short_window - now)
                if not long_available:
                    waits.append(self._long_requests[0] + self.long_window - now)

                self._condition.wait(timeout=max(0.001, min(waits)))

    def snapshot(self) -> dict[str, int | float]:
        """Return current usage without consuming a request slot."""
        with self._condition:
            now = time.monotonic()
            self._discard_expired(self._short_requests, now - self.short_window)
            self._discard_expired(self._long_requests, now - self.long_window)

            short_reset = (
                max(0.0, self._short_requests[0] + self.short_window - now)
                if self._short_requests
                else 0.0
            )
            long_reset = (
                max(0.0, self._long_requests[0] + self.long_window - now)
                if self._long_requests
                else 0.0
            )
            return {
                "short_used": len(self._short_requests),
                "short_limit": self.short_limit,
                "short_reset_seconds": short_reset,
                "long_used": len(self._long_requests),
                "long_limit": self.long_limit,
                "long_reset_seconds": long_reset,
            }


class TtlCache:
    """Small in-memory LRU/TTL cache shared by all backend requests."""

    def __init__(self, max_entries: int = 5000) -> None:
        self.max_entries = max_entries
        self._values: OrderedDict[tuple[Any, ...], tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: tuple[Any, ...]) -> Any | None:
        now = time.monotonic()
        with self._lock:
            cached = self._values.get(key)
            if cached is None:
                return None

            expires_at, value = cached
            if expires_at <= now:
                del self._values[key]
                return None

            self._values.move_to_end(key)
            return value

    def set(self, key: tuple[Any, ...], value: Any, ttl_seconds: float) -> None:
        with self._lock:
            self._values[key] = (time.monotonic() + ttl_seconds, value)
            self._values.move_to_end(key)
            while len(self._values) > self.max_entries:
                self._values.popitem(last=False)


# Leave headroom below the key's documented 20/second and 100/120-second limits.
RIOT_RATE_LIMITER = DualWindowRateLimiter()
RIOT_CACHE = TtlCache()


def _cache_key(url: str, params: dict[str, Any]) -> tuple[Any, ...]:
    safe_params = tuple(sorted((key, str(value)) for key, value in params.items() if key != "api_key"))
    return (url, *safe_params)


def riot_get_json(
    url: str,
    params: dict[str, Any],
    *,
    ttl_seconds: float = 0,
    session: requests.Session | None = None,
    max_retries: int = 4,
    timeout: tuple[float, float] = (3.05, 20.0),
) -> tuple[int, Any | None]:
    """GET JSON from Riot while respecting both key limits.

    Successful responses can be cached. Rate-limit and transient network retries
    are bounded so a failed upstream call cannot recurse forever.
    """

    key = _cache_key(url, params)
    if ttl_seconds > 0:
        cached = RIOT_CACHE.get(key)
        if cached is not None:
            return 200, cached

    requester = session or requests
    last_status = 503

    for attempt in range(max_retries + 1):
        RIOT_RATE_LIMITER.acquire()
        try:
            response = requester.get(url=url, params=params, timeout=timeout)
        except requests.RequestException:
            if attempt >= max_retries:
                return 503, None
            time.sleep(min(8.0, (2 ** attempt) + random.uniform(0, 0.25)))
            continue

        last_status = response.status_code
        if response.status_code == 200:
            try:
                payload = response.json()
            except ValueError:
                return 502, None

            if ttl_seconds > 0:
                RIOT_CACHE.set(key, payload, ttl_seconds)
            return 200, payload

        if response.status_code == 429 and attempt < max_retries:
            try:
                retry_after = float(response.headers.get("Retry-After", "1"))
            except ValueError:
                retry_after = 1.0
            backoff = min(8.0, (2 ** attempt) + random.uniform(0, 0.25))
            time.sleep(max(retry_after, backoff))
            continue

        if response.status_code >= 500 and attempt < max_retries:
            time.sleep(min(8.0, (2 ** attempt) + random.uniform(0, 0.25)))
            continue

        return response.status_code, None

    return last_status, None
