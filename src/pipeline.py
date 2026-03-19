import os
import json
from pathlib import Path
from dotenv import load_dotenv
from model import Caller, Parser, Player


def pipeline(api_key, player_name, player_tag, region, count):
    """
    Create Caller class instance with appropriate arguments -> 
    Fetch PUUID by username and tagline -> 
    Fetch ID's of last matches played ->
    Fetch last matches data

    extract most important data from match info (Parser class)
    create Player class instance for each player with parser data as attributes
    """ 
    try:
        if not api_key:
            raise ValueError("Missing RIOT_API_KEY")

        os.makedirs("data", exist_ok=True)

        usercall = Caller(region=region, api_key=api_key, player_name=player_name, player_tag=player_tag, count=count)
        puuidme = usercall.get_puuid()

        matches_id = usercall.last_matches_id_call(puuidme)
        if not matches_id:
            raise RuntimeError("No matches returned from Riot API")

        matches_data = usercall.last_matches_data_call(matches_id)

        with open(f'data/data_from_{count}_previous_matches.json', 'w') as f:
            json.dump(matches_data, f)

        parse_player_data = Parser(match_data=matches_data, match_id=matches_id[0], target_puuid=puuidme)
        if not parse_player_data.player_data:
            raise RuntimeError("Target player not found in selected match")

        player_object = Player(player_data=parse_player_data.player_data)
        player_object.runes_mapping(parse_player_data.lookup_table)
        player_object.to_json(filepath=f"data/player_as_object_{player_name}.json")
        return player_object
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Pipeline error: {error}")
        return None


def load_api_key():
    project_root = Path(__file__).resolve().parent.parent
    env_candidates = [
        project_root / ".env",
        project_root / "venv" / ".env",
        project_root / ".venv" / ".env"
    ]

    load_dotenv(override=False)
    for env_file in env_candidates:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)

    raw_value = os.getenv('RIOT_API_KEY')
    if raw_value is None:
        return None

    normalized_value = raw_value.strip().strip('"').strip("'")
    return normalized_value or None


api_key = load_api_key()
softmax = pipeline(api_key=api_key, region='europe', player_name='softmax', player_tag='EUNE1', count=1)