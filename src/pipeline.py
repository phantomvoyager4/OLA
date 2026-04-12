import os
import json
from pathlib import Path
from dotenv import load_dotenv
from model import Caller, Player, Match


def pipeline(api_key, player_name, player_tag, platform, count, save):
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

        project_root = Path(__file__).resolve().parent.parent
        data_dir = project_root / "data"
        os.makedirs(data_dir, exist_ok=True)

        usercall = Caller(platform=platform, api_key=api_key, player_name=player_name, player_tag=player_tag, count=count)
        puuidme = usercall.get_puuid()

        matches_id = usercall.last_matches_id_call(puuidme)
        if not isinstance(matches_id, list) or not matches_id:
            raise RuntimeError(f"No valid match IDs returned from Riot API: {matches_id}")
        else: print("Matches fetched")

        matches_data = usercall.last_matches_data_call(matches_id)
        if not matches_data:
            raise RuntimeError("No match payloads returned from Riot API")

        # Ensure we are looking in the project root correctly
        project_root = Path(__file__).resolve().parent.parent
        data_dir = project_root / "data"

        mapping_data = ['runes', 'summoners', 'items']
        lookup_tables = {}
        
        for name in mapping_data:
            path = data_dir / "static" / f"{name}_lookup_table.json"
            with open(path, "r") as f:
                lookup_tables[name] = json.load(f)
        
        combined_records = []

        for match_id in matches_id:
            match_payload = matches_data.get(match_id)
            if not match_payload:
                continue

            match_object = Match(match_data=match_payload)
            
            # Extract game duration in seconds to pass to the Player object
            game_duration = match_payload.get("info", {}).get("gameDuration", 0)
            
            # 1. Match metadata and list of players
            match_entry = {
                "match_id": match_id,
                "metadata": match_object.to_dict(),
                "players": []
            }

            # 2. All players in the match
            participants = match_payload.get("info", {}).get("participants", [])
            for participant in participants:
                player_object = Player(player_data=participant, game_duration_sec=game_duration)
                player_object.summoners_mapping(lookup_tables['summoners'])
                player_object.runes_mapping(lookup_tables['runes'])
                player_object.items_mapping(lookup_tables['items'])
                
                # Check if this participant is the one we instantiated the pipeline for
                player_dict = player_object.to_dict()
                player_dict["caller"] = (participant.get("puuid") == puuidme)
                if player_dict["caller"]:
                    player_dict['metadata'] = usercall.player_metadata_call()
                
                match_entry["players"].append(player_dict)

            combined_records.append(match_entry)

        if not combined_records:
            raise RuntimeError("No matched elements built.")
        else: 
            print("objects created sucessfuly :)")
        
        # Ensure data folder exists relative to project root
        os.makedirs(data_dir, exist_ok=True)
        if save:
            # eg. softmax#EUNE1_1 <- last softmax#EUNE1 match data
            output_path = data_dir / f"{player_name}#{player_tag}_{count}.json"
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


if __name__ == '__main__':
    api_key = load_api_key()
    pipeline(api_key=api_key, platform='EUW1', player_name='401dmg', player_tag='6969', count=1, save=True) #H2P_Gucio