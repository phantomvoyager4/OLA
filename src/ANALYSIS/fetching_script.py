import time
import sys
from pathlib import Path
import json

# Resolve BACKEND relative to this file so imports work regardless of cwd.
backend_path = Path(__file__).resolve().parents[1] / "BACKEND"
sys.path.insert(0, str(backend_path))

# Import functions directly from pipeline.py
from pipeline import load_api_key, pipeline

api_key = load_api_key()

data_full = {}


def names_fetcher(fetcher):
    player_names = []
    for match in fetcher:
        if 'players' not in match:
            continue
        for player in match['players']:
            summoner, tag = [part.strip() for part in player['username'].split('#')]
            player_names.append({'summoner': summoner, 'tag': tag})
    return player_names


def data_fetcher(names: list):
    for index, player in enumerate(names): 
        data = pipeline(api_key=api_key, platform='EUW1', player_name=player['summoner'], player_tag=player['tag'], count=2, save=0)
        time.sleep(5)
        data_full[index] = data



initial_fetcher = pipeline(api_key=api_key, platform='EUW1', player_name='401dmg', player_tag='6969', count=2, save=1) #H2P_Gucio
names_list = names_fetcher(initial_fetcher)
data_fetcher(names_list)
with open('data_full.json', 'w', encoding='utf-8') as f:
    json.dump(data_full, f, indent=4, ensure_ascii=False)






