"""Aggregate, persist, and serve the generated champion tier-list snapshot."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from fastapi import APIRouter, HTTPException


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SNAPSHOT_PATH = PROJECT_ROOT / "data" / "tier_list" / "euw_master_plus_latest.json"
CHAMPION_LOOKUP_PATH = PROJECT_ROOT / "data" / "static" / "champions_lookup_table.json"
VALID_ROLES = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
ROLE_ALIASES = {"MID": "MIDDLE", "BOT": "BOTTOM", "ADC": "BOTTOM", "SUPPORT": "UTILITY"}

tier_list_router = APIRouter(prefix="/api/tier-list", tags=["tier-list"])


def _normalise_role(participant: dict[str, Any]) -> str | None:
    role = str(participant.get("teamPosition") or participant.get("individualPosition") or "").upper()
    role = ROLE_ALIASES.get(role, role)
    return role if role in VALID_ROLES else None


def _percentile_ranks(values: list[float]) -> list[float]:
    """Return tie-aware percentile ranks in the inclusive 0..100 interval."""

    if not values:
        return []
    if len(values) == 1:
        return [100.0]

    sorted_values = sorted(values)
    rank_by_value: dict[float, float] = {}
    for value in sorted(set(sorted_values)):
        positions = [index for index, candidate in enumerate(sorted_values) if candidate == value]
        average_index = sum(positions) / len(positions)
        rank_by_value[value] = 100.0 * average_index / (len(values) - 1)
    return [rank_by_value[value] for value in values]


def _tier_from_score(score: float) -> str:
    if score >= 90:
        return "S"
    if score >= 70:
        return "A"
    if score >= 40:
        return "B"
    if score >= 15:
        return "C"
    return "D"


def _load_champion_lookup(path: str | os.PathLike[str] | None = None) -> dict[str, dict[str, Any]]:
    lookup_path = Path(path) if path else CHAMPION_LOOKUP_PATH
    try:
        with lookup_path.open("r", encoding="utf-8") as handle:
            raw_lookup = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not load champion lookup at {lookup_path}: {error}") from error

    return {
        str(champion_id): value
        for champion_id, value in raw_lookup.items()
        if str(champion_id).isdigit() and isinstance(value, dict)
    }


def aggregate_tier_list(
    source: dict[str, Any],
    *,
    min_games: int = 3,
    champion_lookup_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Convert filtered match-v5 payloads into champion-role ranking rows."""

    if min_games < 1:
        raise ValueError("min_games must be at least 1")
    matches = source.get("matches")
    if not isinstance(matches, list) or not matches:
        raise ValueError("Tier-list source does not contain any matches")

    lookup = _load_champion_lookup(champion_lookup_path)
    picks: dict[tuple[int, str], dict[str, int]] = defaultdict(lambda: {"games": 0, "wins": 0})
    bans: dict[int, int] = defaultdict(int)
    participant_count = 0
    included_matches = 0

    for match in matches:
        info = match.get("info", {}) if isinstance(match, dict) else {}
        participants = info.get("participants", []) if isinstance(info, dict) else []
        if not isinstance(participants, list):
            continue

        match_rows = 0
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            role = _normalise_role(participant)
            champion_id = int(participant.get("championId", 0) or 0)
            if not role or champion_id <= 0:
                continue
            row = picks[(champion_id, role)]
            row["games"] += 1
            row["wins"] += int(bool(participant.get("win")))
            match_rows += 1

        if match_rows == 0:
            continue
        participant_count += match_rows
        included_matches += 1

        match_bans: set[int] = set()
        for team in info.get("teams", []) or []:
            if not isinstance(team, dict):
                continue
            for ban in team.get("bans", []) or []:
                champion_id = int(ban.get("championId", 0) or 0) if isinstance(ban, dict) else 0
                if champion_id > 0:
                    match_bans.add(champion_id)
        for champion_id in match_bans:
            bans[champion_id] += 1

    if included_matches == 0:
        raise ValueError("No valid participant rows were found in the collected matches")

    rows_by_role: dict[str, list[dict[str, Any]]] = {role: [] for role in VALID_ROLES}
    for (champion_id, role), counts in picks.items():
        games = counts["games"]
        if games < min_games:
            continue
        wins = counts["wins"]
        champion = lookup.get(str(champion_id), {})
        win_rate = 100.0 * wins / games
        pick_rate = 100.0 * games / included_matches
        ban_rate = 100.0 * bans.get(champion_id, 0) / included_matches

        # A 30-game neutral prior keeps tiny samples from dominating the list.
        smoothed_win_rate = 100.0 * (wins + 15.0) / (games + 30.0)
        rows_by_role[role].append(
            {
                "championId": champion_id,
                "championName": champion.get("name") or f"Champion {champion_id}",
                "championTitle": champion.get("title") or "",
                "championImage": champion.get("image_path") or "",
                "role": role,
                "games": games,
                "wins": wins,
                "winRate": round(win_rate, 2),
                "pickRate": round(pick_rate, 2),
                "banRate": round(ban_rate, 2),
                "_smoothedWinRate": smoothed_win_rate,
            }
        )

    champion_rows: list[dict[str, Any]] = []
    for role in VALID_ROLES:
        role_rows = rows_by_role[role]
        if not role_rows:
            continue
        win_ranks = _percentile_ranks([row["_smoothedWinRate"] for row in role_rows])
        pick_ranks = _percentile_ranks([float(row["pickRate"]) for row in role_rows])
        ban_ranks = _percentile_ranks([float(row["banRate"]) for row in role_rows])

        raw_scores: list[float] = []
        for index, row in enumerate(role_rows):
            confidence = min(1.0, row["games"] / 20.0)
            raw_score = 0.60 * win_ranks[index] + 0.30 * pick_ranks[index] + 0.10 * ban_ranks[index]
            raw_scores.append(50.0 + (raw_score - 50.0) * (0.55 + 0.45 * confidence))

        relative_scores = _percentile_ranks(raw_scores)
        for row, score in zip(role_rows, relative_scores):
            row.pop("_smoothedWinRate", None)
            row["score"] = round(score, 1)
            row["tier"] = _tier_from_score(score)
            champion_rows.append(row)

    champion_rows.sort(
        key=lambda row: (
            VALID_ROLES.index(row["role"]),
            -float(row["score"]),
            -int(row["games"]),
            row["championName"],
        )
    )

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "region": str(source.get("region") or "EUW"),
        "rank": str(source.get("rank") or "MASTER+"),
        "patch": str(source.get("patch") or "unknown"),
        "dataPatch": str(source.get("dataPatch") or source.get("patch") or "unknown"),
        "lastUpdated": generated_at,
        "sample": {
            "matches": included_matches,
            "participants": participant_count,
            "players": int(source.get("sourcePlayers", 0) or 0),
        },
        "methodology": {
            "queue": "RANKED_SOLO_5x5",
            "minimumGames": min_games,
            "winRatePriorGames": 30,
            "scoreWeights": {"winRate": 0.60, "pickRate": 0.30, "banRate": 0.10},
            "scope": "Matches discovered from current EUW Master, Grandmaster and Challenger players; all valid match participants are aggregated.",
        },
        "champions": champion_rows,
    }


def save_tier_list_snapshot(
    snapshot: dict[str, Any],
    output_path: str | os.PathLike[str] | None = None,
) -> Path:
    """Atomically replace the public snapshot, never exposing partial JSON."""

    path = Path(output_path) if output_path else DEFAULT_SNAPSHOT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(snapshot, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary_name = handle.name
        Path(temporary_name).replace(path)
    finally:
        if temporary_name:
            temporary_path = Path(temporary_name)
            if temporary_path.exists():
                temporary_path.unlink()
    return path


def load_tier_list_snapshot(
    snapshot_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    path = Path(snapshot_path) if snapshot_path else DEFAULT_SNAPSHOT_PATH
    try:
        with path.open("r", encoding="utf-8") as handle:
            snapshot = json.load(handle)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Tier-list snapshot is not ready. Run python -m BACKEND.tier_list_fetcher first."
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read tier-list snapshot: {error}") from error

    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("champions"), list):
        raise RuntimeError("Tier-list snapshot has an invalid schema")
    return snapshot


def refresh_tier_list_snapshot(
    api_key: str,
    *,
    config: Any = None,
    target_patch: str | None = None,
    min_games: int = 3,
    output_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Run the collector, build the ranking, then publish it atomically."""

    from .tier_list_fetcher import collect_tier_list_source

    source = collect_tier_list_source(api_key, config=config, target_patch=target_patch)
    snapshot = aggregate_tier_list(source, min_games=min_games)
    save_tier_list_snapshot(snapshot, output_path)
    return snapshot


@tier_list_router.get("")
def get_tier_list() -> dict[str, Any]:
    """Serve the last completed snapshot without consuming Riot API quota."""

    try:
        return load_tier_list_snapshot()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@tier_list_router.get("/status")
def get_tier_list_status() -> dict[str, Any]:
    """Report snapshot readiness without starting a refresh."""

    try:
        snapshot = load_tier_list_snapshot()
    except FileNotFoundError:
        return {"ready": False}
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return {
        "ready": True,
        "patch": snapshot.get("patch"),
        "dataPatch": snapshot.get("dataPatch"),
        "lastUpdated": snapshot.get("lastUpdated"),
        "sample": snapshot.get("sample", {}),
        "entries": len(snapshot.get("champions", [])),
    }
