import os
import json
from pathlib import Path
from dotenv import load_dotenv
from model import Caller, Player, Match


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
        if not isinstance(matches_id, list) or not matches_id:
            raise RuntimeError(f"No valid match IDs returned from Riot API: {matches_id}")
        else: print("Matches fetched")

        matches_data = usercall.last_matches_data_call(matches_id)
        if not matches_data:
            raise RuntimeError("No match payloads returned from Riot API")

        # with open(f'data/{count}_previous_matches.json', 'w') as f:
        #     json.dump(matches_data, f, indent=4)

        with open("data/patch_lookup_table.json", "r") as f:
            lookup_table = json.load(f)

        combined_records = []

        for match_id in matches_id:
            match_payload = matches_data.get(match_id)
            if not match_payload:
                continue

            match_object = Match(match_data=match_payload)
            
            # 1. Match metadata and list of players
            match_entry = {
                "match_id": match_id,
                "metadata": match_object.to_dict(),
                "players": []
            }

            # 2. All players in the match
            participants = match_payload.get("info", {}).get("participants", [])
            for participant in participants:
                player_object = Player(player_data=participant)
                player_object.runes_mapping(lookup_table)
                
                # Check if this participant is the one we instantiated the pipeline for
                player_dict = player_object.to_dict()
                player_dict["caller"] = (participant.get("puuid") == puuidme)
                
                match_entry["players"].append(player_dict)

            combined_records.append(match_entry)

        if not combined_records:
            raise RuntimeError("No matched elements built.")
        else: 
            print("Combined objects created")

        output_path = f"data/{count}_{player_name}_combined_records.json"
        with open(output_path, "w") as f:
            json.dump(combined_records, f, indent=4)

        return combined_records
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Pipeline error: {error}")
        return None


def load_api_key():
    """
    Load api key from environment folder
    """
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