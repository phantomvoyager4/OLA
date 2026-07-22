"""Collect EUW Master+ ranked matches used to build the tier-list snapshot.

This module deliberately contains the expensive Riot API work.  The web API
only reads the generated snapshot, so opening the Tier List page never starts
a large upstream collection job.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import requests

from .pipeline import load_api_key
from .riot_api import riot_get_json


LEAGUE_TIERS = ("challenger", "grandmaster", "master")
RANKED_SOLO_QUEUE = "RANKED_SOLO_5x5"
RANKED_SOLO_QUEUE_ID = 420
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_CHAMPION_LOOKUP = PROJECT_ROOT / "data" / "static" / "champions_lookup_table.json"


class TierListFetchError(RuntimeError):
    """Raised when the collector cannot obtain a required upstream payload."""


@dataclass(frozen=True)
class TierCollectorConfig:
    """Limits the breadth of a single, repeatable collection run."""

    platform_route: str = "euw1"
    regional_route: str = "europe"
    region_label: str = "EUW"
    players_per_tier: int = 10
    matches_per_player: int = 10
    max_unique_matches: int = 300
    workers: int = 8
    queue: str = RANKED_SOLO_QUEUE
    queue_id: int = RANKED_SOLO_QUEUE_ID

    def __post_init__(self) -> None:
        if not 1 <= self.players_per_tier <= 50:
            raise ValueError("players_per_tier must be between 1 and 50")
        if not 1 <= self.matches_per_player <= 100:
            raise ValueError("matches_per_player must be between 1 and 100")
        if not 1 <= self.max_unique_matches <= 1000:
            raise ValueError("max_unique_matches must be between 1 and 1000")
        if not 1 <= self.workers <= 16:
            raise ValueError("workers must be between 1 and 16")


def patch_line(version: str) -> str:
    """Return the major.minor patch used by match-v5 gameVersion values."""

    parts = str(version).split(".")
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(f"Invalid patch version: {version!r}")
    return f"{int(parts[0])}.{int(parts[1])}"


def data_patch_line(version: str) -> str:
    """Normalise a public or internal patch to Riot's gameVersion line.

    Riot's public 2025+ patch names use the calendar year (for example 26.14),
    while Data Dragon and match-v5 still expose the internal 16.14.x version.
    """

    major_text, minor_text = patch_line(version).split(".")
    major = int(major_text)
    if major >= 25:
        major -= 10
    return f"{major}.{minor_text}"


def public_patch_line(version: str) -> str:
    """Convert Riot's internal data version to its public patch name."""

    major_text, minor_text = patch_line(version).split(".")
    major = int(major_text)
    if 15 <= major < 25:
        major += 10
    return f"{major}.{minor_text}"


def fetch_latest_euw_patch(timeout: tuple[float, float] = (3.05, 15.0)) -> str:
    """Read the internal data patch currently published for EUW."""

    url = "https://ddragon.leagueoflegends.com/realms/euw.json"
    remote_error: Exception | None = None
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        version = response.json().get("v")
    except (requests.RequestException, ValueError, AttributeError) as error:
        remote_error = error
        version = None

    if not version:
        try:
            with LOCAL_CHAMPION_LOOKUP.open("r", encoding="utf-8") as handle:
                version = json.load(handle).get("patch")
        except (OSError, json.JSONDecodeError, AttributeError):
            version = None
        if version:
            print(
                "Tier collector warning: Data Dragon realm was unavailable; "
                f"using local lookup patch {version}."
            )

    if not version:
        detail = f": {remote_error}" if remote_error else ""
        raise TierListFetchError(f"Could not determine the current EUW patch{detail}")
    return data_patch_line(str(version))


def _riot_payload(
    url: str,
    api_key: str,
    *,
    params: dict[str, Any] | None = None,
    ttl_seconds: float = 0,
) -> Any:
    request_params = dict(params or {})
    request_params["api_key"] = api_key
    status, payload = riot_get_json(
        url,
        request_params,
        ttl_seconds=ttl_seconds,
    )
    if status != 200 or payload is None:
        raise TierListFetchError(f"Riot API request failed with HTTP {status}: {url}")
    return payload


def fetch_master_plus_players(
    api_key: str,
    config: TierCollectorConfig,
) -> list[dict[str, Any]]:
    """Fetch a deterministic LP-sorted PUUID seed from all Master+ leagues."""

    selected: list[dict[str, Any]] = []
    seen_puuids: set[str] = set()

    for tier in LEAGUE_TIERS:
        url = (
            f"https://{config.platform_route}.api.riotgames.com/lol/league/v4/"
            f"{tier}leagues/by-queue/{config.queue}"
        )
        league = _riot_payload(url, api_key, ttl_seconds=300)
        entries = league.get("entries", []) if isinstance(league, dict) else []
        entries = sorted(
            (entry for entry in entries if isinstance(entry, dict)),
            key=lambda entry: (-int(entry.get("leaguePoints", 0) or 0), str(entry.get("puuid", ""))),
        )

        tier_count = 0
        for entry in entries:
            puuid = str(entry.get("puuid") or "").strip()
            if not puuid or puuid in seen_puuids:
                continue
            seen_puuids.add(puuid)
            selected.append(
                {
                    "puuid": puuid,
                    "tier": tier.upper(),
                    "leaguePoints": int(entry.get("leaguePoints", 0) or 0),
                }
            )
            tier_count += 1
            if tier_count >= config.players_per_tier:
                break

    if not selected:
        raise TierListFetchError("No Master+ players with PUUIDs were returned for EUW")
    return selected


def _fetch_player_match_ids(
    player: dict[str, Any],
    api_key: str,
    config: TierCollectorConfig,
) -> list[str]:
    puuid = quote(str(player["puuid"]), safe="")
    url = (
        f"https://{config.regional_route}.api.riotgames.com/lol/match/v5/"
        f"matches/by-puuid/{puuid}/ids"
    )
    payload = _riot_payload(
        url,
        api_key,
        params={"queue": config.queue_id, "start": 0, "count": config.matches_per_player},
        ttl_seconds=120,
    )
    return [str(match_id) for match_id in payload] if isinstance(payload, list) else []


def _fetch_match(match_id: str, api_key: str, config: TierCollectorConfig) -> dict[str, Any] | None:
    safe_match_id = quote(match_id, safe="")
    url = f"https://{config.regional_route}.api.riotgames.com/lol/match/v5/matches/{safe_match_id}"
    payload = _riot_payload(url, api_key, ttl_seconds=30 * 24 * 60 * 60)
    return payload if isinstance(payload, dict) else None


def _deduplicate(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def is_eligible_match(
    match: dict[str, Any],
    *,
    target_patch: str,
    config: TierCollectorConfig,
) -> bool:
    """Keep completed EUW ranked-solo games from the requested patch only."""

    info = match.get("info")
    if not isinstance(info, dict):
        return False
    try:
        match_patch = data_patch_line(str(info.get("gameVersion", "")))
    except ValueError:
        return False
    target_data_patch = data_patch_line(target_patch)

    platform_id = str(info.get("platformId") or "").upper()
    end_result = info.get("endOfGameResult")
    participants = info.get("participants")
    return (
        match_patch == target_data_patch
        and int(info.get("queueId", 0) or 0) == config.queue_id
        and platform_id == config.platform_route.upper()
        and int(info.get("gameDuration", 0) or 0) >= 300
        and (end_result in (None, "", "GameComplete"))
        and isinstance(participants, list)
        and len(participants) >= 10
    )


def collect_tier_list_source(
    api_key: str,
    config: TierCollectorConfig | None = None,
    *,
    target_patch: str | None = None,
) -> dict[str, Any]:
    """Collect and filter raw matches required by the snapshot aggregator."""

    if not api_key:
        raise TierListFetchError("RIOT_API_KEY is not configured")
    config = config or TierCollectorConfig()
    target_data_patch = data_patch_line(target_patch) if target_patch else fetch_latest_euw_patch()
    public_patch = public_patch_line(target_data_patch)

    players = fetch_master_plus_players(api_key, config)
    print(
        f"Tier collector: {len(players)} EUW Master+ seed players, "
        f"public patch {public_patch} (data version {target_data_patch})."
    )

    match_ids_by_puuid: dict[str, list[str]] = {}
    id_errors: list[str] = []
    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        futures = {
            executor.submit(_fetch_player_match_ids, player, api_key, config): player
            for player in players
        }
        for future in as_completed(futures):
            player = futures[future]
            try:
                match_ids_by_puuid[str(player["puuid"])] = future.result()
            except TierListFetchError as error:
                id_errors.append(f"{player['tier']}: {error}")

    match_ids = [
        match_id
        for player in players
        for match_id in match_ids_by_puuid.get(str(player["puuid"]), [])
    ]
    candidate_match_ids = _deduplicate(match_ids)
    unique_match_ids = candidate_match_ids[: config.max_unique_matches]
    if not unique_match_ids:
        details = f" ({'; '.join(id_errors[:3])})" if id_errors else ""
        raise TierListFetchError(f"No ranked-solo match IDs could be collected{details}")

    if len(candidate_match_ids) > len(unique_match_ids):
        print(
            f"Tier collector: capped {len(candidate_match_ids)} candidate matches "
            f"at {config.max_unique_matches}."
        )

    print(f"Tier collector: fetching {len(unique_match_ids)} unique match payloads.")
    matches: list[dict[str, Any]] = []
    match_errors = 0
    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        futures = {
            executor.submit(_fetch_match, match_id, api_key, config): match_id
            for match_id in unique_match_ids
        }
        for future in as_completed(futures):
            try:
                match = future.result()
            except TierListFetchError:
                match_errors += 1
                continue
            if match and is_eligible_match(match, target_patch=target_data_patch, config=config):
                matches.append(match)

    matches.sort(key=lambda match: str(match.get("metadata", {}).get("matchId", "")))
    if not matches:
        raise TierListFetchError(
            f"Fetched {len(unique_match_ids)} match IDs, but none matched EUW patch {public_patch} "
            f"(data version {target_data_patch})"
        )

    return {
        "region": config.region_label,
        "rank": "MASTER+",
        "patch": public_patch,
        "dataPatch": target_data_patch,
        "collectedAt": datetime.now(timezone.utc).isoformat(),
        "sourcePlayers": len(players),
        "candidateMatchIds": len(candidate_match_ids),
        "requestedMatchIds": len(unique_match_ids),
        "failedMatchRequests": match_errors,
        "matches": matches,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the EUW Master+ tier-list snapshot from Riot match data."
    )
    parser.add_argument("--players-per-tier", type=int, default=10)
    parser.add_argument("--matches-per-player", type=int, default=10)
    parser.add_argument(
        "--max-matches",
        type=int,
        default=300,
        help="Hard cap on unique match detail requests (default: 300)",
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--min-games", type=int, default=3)
    parser.add_argument(
        "--patch",
        help="Optional public or data patch override, for example 26.14 or 16.14",
    )
    parser.add_argument("--output", help="Optional snapshot JSON path")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    api_key = load_api_key()
    if not api_key:
        raise SystemExit("RIOT_API_KEY is not configured")

    config = TierCollectorConfig(
        players_per_tier=args.players_per_tier,
        matches_per_player=args.matches_per_player,
        max_unique_matches=args.max_matches,
        workers=args.workers,
    )

    # Local import prevents a circular module dependency at import time.
    from .tier_list_backend import refresh_tier_list_snapshot

    snapshot = refresh_tier_list_snapshot(
        api_key,
        config=config,
        target_patch=args.patch,
        min_games=args.min_games,
        output_path=args.output,
    )
    sample = snapshot["sample"]
    print(
        f"Tier collector: saved patch {snapshot['patch']} with "
        f"{sample['matches']} matches and {len(snapshot['champions'])} champion-role rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
