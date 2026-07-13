import time
import sys
from pathlib import Path
import json
from collections import deque

SRC_PATH = Path(__file__).resolve().parents[1]
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from BACKEND.pipeline import load_api_key, pipeline
from BACKEND.model import Caller

api_key = load_api_key()

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / 'data'
amount_of_matches = 10
FETCH_COUNT = 1
REQUEST_DELAY_SEC = 1.5


def names_fetcher(fetcher, target_tier=None):
    player_names = []
    for match in fetcher:
        if 'players' not in match:
            continue
        for player in match['players']:
            username = player.get('username', '')
            if '#' not in username:
                continue

            metadata = player.get('metadata') or {}
            player_tier = metadata.get('tier')

            if target_tier is not None and player_tier != target_tier:
                continue

            summoner, tag = [part.strip() for part in username.split('#', 1)]
            if summoner and tag:
                player_names.append({
                    'summoner': summoner,
                    'tag': tag,
                    'tier': player_tier,
                })
    return player_names


def normalize_player(player: dict):
    return player['summoner'].strip(), player['tag'].strip()


def safe_filename_part(value):
    text = str(value).strip().replace(' ', '_')
    return ''.join(character for character in text if character.isalnum() or character in ('_', '-')) or 'unknown'


def lookup_player_tier(player_name: str, player_tag: str, platform: str):
    try:
        caller = Caller(
            platform=platform,
            api_key=api_key,
            player_name=player_name,
            player_tag=player_tag,
            count=1,
        )
        puuid = caller.get_puuid()
        if not puuid:
            return None

        metadata = caller.player_metadata_call()
        if not metadata:
            return None

        return metadata.get('tier')
    except Exception as error:
        print(
            f"Rank lookup failed for {player_name}#{player_tag} on {platform}: "
            f"{type(error).__name__}: {error}"
        )
        return None


def next_free_output_path(server: str, tier: str, matches_count: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    server_part = safe_filename_part(server)
    tier_part = safe_filename_part(tier)
    base_name = f'data_full_{server_part}_{tier_part}_{matches_count}'
    next_index = 1
    while (DATA_DIR / f'{base_name}_{next_index}.json').exists():
        next_index += 1
    return DATA_DIR / f'{base_name}_{next_index}.json'


def save_data_full(data_full: dict, server: str, tier: str, matches_count: int, reason: str = ''):
    output_path = next_free_output_path(server=server, tier=tier, matches_count=matches_count)
    if reason:
        print(f"{reason} Saving crawl snapshot to {output_path}...")
    else:
        print(f"Saving crawl snapshot to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_full, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(data_full)} matches to {output_path}")
    return output_path


def crawl_matches(seed_player: dict):
    player_queue = deque([seed_player])
    seen_players = {normalize_player(seed_player)}
    seen_matches = set()
    data_full = {}
    fetching_rank = None
    crawl_platform = seed_player.get('platform', 'EUW1')

    print(
        f"Starting crawl from {seed_player['summoner']}#{seed_player['tag']} "
        f"on {crawl_platform} with a target of {amount_of_matches} unique matches."
    )

    while player_queue and len(data_full) < amount_of_matches:
        current_player = player_queue.popleft()
        print(
            f"Fetching matches for {current_player['summoner']}#{current_player['tag']} "
            f"({len(data_full)} matches collected)..."
        )

        current_platform = current_player.get('platform', crawl_platform)
        current_rank = lookup_player_tier(
            current_player['summoner'],
            current_player['tag'],
            current_platform,
        )

        if current_rank is None:
            print(
                f"Rank check for {current_player['summoner']}#{current_player['tag']}: NOT OK "
                "(rank unavailable)."
            )
            continue

        if fetching_rank is None:
            fetching_rank = current_rank
            print(f"Initial fetching tier set to {fetching_rank}.")

        if current_rank != fetching_rank:
            print(
                f"Rank check for {current_player['summoner']}#{current_player['tag']}: NOT OK "
                f"({current_rank} != {fetching_rank})."
            )
            continue

        print(
            f"Rank check for {current_player['summoner']}#{current_player['tag']}: OK "
            f"({current_rank})."
        )

        fetcher = pipeline(
            api_key=api_key,
            platform=current_platform,
            player_name=current_player['summoner'],
            player_tag=current_player['tag'],
            count=FETCH_COUNT,
            save=0,
        )

        print(f"Waiting {REQUEST_DELAY_SEC} seconds before the next request...")
        time.sleep(REQUEST_DELAY_SEC)

        if not fetcher:
            print(f"No match data returned for {current_player['summoner']}#{current_player['tag']}.")
            continue

        # Cache once so we can inspect rank and reuse the same data.
        matches = list(fetcher)

        before_match_count = len(data_full)

        for match in matches:
            match_id = match.get('match_id')
            if not match_id or match_id in seen_matches:
                continue

            seen_matches.add(match_id)
            data_full[match_id] = match

        added_matches = len(data_full) - before_match_count
        if added_matches:
            print(f"Added {added_matches} new matches. Total is now {len(data_full)}.")

        # Only queue players already matching the caller rank.
        new_players = names_fetcher(matches, target_tier=fetching_rank)
        queued_players = 0
        for player in new_players:
            key = normalize_player(player)
            if key in seen_players:
                continue
            seen_players.add(key)
            player_queue.append({**player, 'platform': current_player.get('platform', crawl_platform)})
            queued_players += 1

        if queued_players:
            print(f"Queued {queued_players} new player names from the latest match data.")
        else:
            print("No new player names were discovered in the latest match data.")

        print(
            f"Finished processing {current_player['summoner']}#{current_player['tag']}; "
            f"it was removed from the active queue."
        )

        print(
            f"Collected {len(data_full)} matches, {len(seen_players)} players, "
            f"and {len(player_queue)} queued players."
        )

        if len(data_full) >= amount_of_matches:
            print(f"Reached the target of {amount_of_matches} unique matches.")
            break

    if not player_queue and len(data_full) < amount_of_matches:
        print("Player queue became empty before the target match count was reached.")

    return data_full, crawl_platform, fetching_rank


if __name__ == '__main__':
    seed_player = {'summoner': 'EMPEROR AGURIN', 'tag': 'ROYAL', 'platform': 'EUW1'}
    data_full, crawl_platform, fetching_rank = crawl_matches(seed_player)

    if data_full:
        save_data_full(
            data_full,
            server=crawl_platform,
            tier=fetching_rank or 'unknown',
            matches_count=amount_of_matches,
            reason='Final save.',
        )
    else:
        print('No match data was collected.')