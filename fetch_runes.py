from dotenv import load_dotenv
import os
import requests
import json

def fetch_latest_data(): 
    """
    Fetch latest patch number and runes page
    """
    patch_call = requests.get(url='https://ddragon.leagueoflegends.com/api/versions.json')
    live_patch = patch_call.json()[0]
    runes_call = requests.get(url=f'http://ddragon.leagueoflegends.com/cdn/{live_patch}/data/en_US/runesReforged.json')   
    json_runes = runes_call.json()     
    return live_patch, json_runes

load_dotenv()
api_key = os.getenv('RIOT_API_KEY')


def structurize_data(input: dict, live_patch):
    clean_runes_storage = {}
    clean_runes_storage["patch"] = live_patch
    for style in input:
        for slot in style['slots']:
            for rune in slot['runes']:
                clean_runes_storage[rune['id']] = [rune["name"], rune['shortDesc']]
    return clean_runes_storage

patch, runes = fetch_latest_data()



runes_dict = structurize_data(input = runes, live_patch=patch)
with open('data/data_dict.json', 'w') as f:
    json.dump(runes_dict, f)

