"""Local Riot ID index that powers search autocomplete.

Riot's API has no prefix search: account-v1 only resolves an exact
``gameName#tagLine``. Asking Riot on every keystroke would also burn the
development key's 90-requests-per-2-minutes budget in a few seconds of
typing. Suggestions are therefore served from players this backend has
already seen in match payloads it fetched anyway, so autocomplete costs
zero Riot quota.
"""

from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Iterable

# Frontend region labels -> Riot platform routing values. Mirrors the mapping
# in ``model.Caller`` so suggestions are filtered by the same platform the
# profile page will query.
SERVER_TO_PLATFORM = {
    "BR": "BR1",
    "EUN": "EUN1",
    "EUNE": "EUN1",
    "EUW": "EUW1",
    "JP": "JP1",
    "KR": "KR",
    "LAN": "LA1",
    "LAS": "LA2",
    "NA": "NA1",
    "OCE": "OC1",
    "TR": "TR1",
    "RU": "RU",
    "PH": "PH2",
    "SG": "SG2",
    "TH": "TH2",
    "TW": "TW2",
    "VN": "VN2",
    "ME": "ME1",
}

DEFAULT_INDEX_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "player_index.json"


def normalize_platform(platform: str | None) -> str:
    upper = str(platform or "").replace(" ", "").upper()
    return SERVER_TO_PLATFORM.get(upper, upper)


def _fold(value: str) -> str:
    # Riot IDs are case-insensitive; casefold also handles non-ASCII names.
    return value.strip().casefold()


class PlayerIndex:
    """Thread-safe in-memory Riot ID index, persisted to a small JSON file.

    Entries are keyed by ``(platform, folded name, folded tag)``. ``searches``
    counts successful profile lookups and ranks above ``seen`` (appearances in
    fetched matches), so players people actually look up surface first.
    """

    def __init__(
        self,
        path: Path | None = DEFAULT_INDEX_PATH,
        max_entries: int = 50_000,
        save_interval_seconds: float = 30.0,
    ) -> None:
        self.path = path
        self.max_entries = max_entries
        self.save_interval_seconds = save_interval_seconds
        self._entries: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._dirty = False
        self._last_save = 0.0
        self._load()

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        except (OSError, ValueError) as error:
            print(f"Player index: could not read {self.path} ({error}). Starting empty.")
            return
        for row in rows if isinstance(rows, list) else []:
            try:
                key = (row["platform"], _fold(row["name"]), _fold(row["tag"]))
            except (KeyError, TypeError, AttributeError):
                continue
            self._entries[key] = row

    def _upsert(self, platform: str, name: str, tag: str, now: float, searched: bool) -> None:
        key = (platform, _fold(name), _fold(tag))
        entry = self._entries.get(key)
        if entry is None:
            entry = {"platform": platform, "name": name, "tag": tag, "seen": 0, "searches": 0}
            self._entries[key] = entry
        # Keep the latest capitalisation Riot reports.
        entry["name"], entry["tag"] = name, tag
        entry["last_seen"] = now
        if searched:
            entry["searches"] += 1
        else:
            entry["seen"] += 1
        self._dirty = True

    def record_matches(
        self,
        match_payloads: Iterable[dict[str, Any] | None],
        searched_puuid: str | None = None,
    ) -> None:
        """Index every participant of already-fetched raw match-v5 payloads."""
        now = time.time()
        searched_done = False
        with self._lock:
            for payload in match_payloads:
                info = (payload or {}).get("info") or {}
                platform = normalize_platform(info.get("platformId"))
                if not platform:
                    continue
                for participant in info.get("participants") or []:
                    name = str(participant.get("riotIdGameName") or "").strip()
                    tag = str(participant.get("riotIdTagline") or "").strip()
                    if not name or not tag:
                        continue
                    searched = (
                        not searched_done
                        and searched_puuid is not None
                        and participant.get("puuid") == searched_puuid
                    )
                    self._upsert(platform, name, tag, now, searched)
                    searched_done = searched_done or searched
            self._evict()
        self.save_if_due()

    def _evict(self) -> None:
        overflow = len(self._entries) - self.max_entries
        if overflow <= 0:
            return
        stalest = sorted(self._entries, key=lambda k: self._entries[k].get("last_seen", 0))
        for key in stalest[:overflow]:
            del self._entries[key]

    def suggest(self, query: str, platform: str, limit: int = 8) -> list[dict[str, Any]]:
        """Return Riot IDs on ``platform`` matching ``query``.

        ``query`` may be ``name`` or ``name#tag``. Name-prefix matches rank
        above matches starting at a later word, which rank above substrings.
        """
        platform = normalize_platform(platform)
        raw_name, _, raw_tag = query.partition("#")
        name_q, tag_q = _fold(raw_name), _fold(raw_tag)
        if not name_q:
            return []

        scored = []
        with self._lock:
            for (entry_platform, name, tag), entry in self._entries.items():
                if entry_platform != platform or (tag_q and not tag.startswith(tag_q)):
                    continue
                if name.startswith(name_q):
                    tier = 0
                elif f" {name_q}" in name:
                    tier = 1
                elif name_q in name:
                    tier = 2
                else:
                    continue
                scored.append((
                    tier,
                    -entry["searches"],
                    -entry["seen"],
                    -entry.get("last_seen", 0),
                    len(name),
                    entry,
                ))

        scored.sort(key=lambda row: row[:5])
        return [
            {"name": row[5]["name"], "tag": row[5]["tag"], "platform": row[5]["platform"]}
            for row in scored[:limit]
        ]

    def save_if_due(self, force: bool = False) -> None:
        """Write the index at most once per ``save_interval_seconds``."""
        if not self.path:
            return
        with self._lock:
            now = time.monotonic()
            if not self._dirty or (not force and now - self._last_save < self.save_interval_seconds):
                return
            rows = list(self._entries.values())
            self._dirty = False
            self._last_save = now
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False)
            os.replace(tmp_path, self.path)
        except OSError as error:
            print(f"Player index: could not save {self.path} ({error}).")
            with self._lock:
                self._dirty = True

    def __len__(self) -> int:
        return len(self._entries)


class ClientThrottle:
    """Non-blocking per-client sliding window for the suggestion endpoint.

    The endpoint never calls Riot, so this only guards the server against a
    runaway client. The frontend debounces to far below this ceiling.
    """

    def __init__(self, limit: int = 10, window_seconds: float = 5.0, max_clients: int = 10_000) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def try_acquire(self, client: str) -> float:
        """Record a hit and return 0, or return seconds until one is allowed."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = self._hits.get(client)
            if hits is None:
                if len(self._hits) >= self.max_clients:
                    self._prune(cutoff)
                hits = self._hits[client] = deque()
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(0.0, hits[0] + self.window_seconds - now)
            hits.append(now)
            return 0.0

    def _prune(self, cutoff: float) -> None:
        for client in [c for c, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[client]


PLAYER_INDEX = PlayerIndex()
SUGGEST_THROTTLE = ClientThrottle()
