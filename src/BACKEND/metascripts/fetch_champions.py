import requests
import json


def fetch_latest_champions():
    patch_call = requests.get(url='https://ddragon.leagueoflegends.com/api/versions.json')
    live_patch = patch_call.json()[0]
    champs_call = requests.get(url=f'http://ddragon.leagueoflegends.com/cdn/{live_patch}/data/en_US/champion.json')
    json_champs = champs_call.json()
    return live_patch, json_champs


def structurize_data(input: dict, live_patch: str):
    champs_lookup_storage = {}
    champs_lookup_storage["patch"] = live_patch
    for champ_id_str, champ_data in input['data'].items():
        # Using 'key' (numeric ID) as lookup key to match API responses
        numeric_id = champ_data['key']
        champs_lookup_storage[numeric_id] = {}
        attributes = ["name", "title", "blurb"]
        for i in attributes:
            champs_lookup_storage[numeric_id][i] = champ_data.get(i, "")
        champs_lookup_storage[numeric_id]["image_path"] = f"https://ddragon.leagueoflegends.com/cdn/{live_patch}/img/champion/{champ_data['image']['full']}"
    return champs_lookup_storage


def fc():
    patch, champs = fetch_latest_champions()
    champs_dict = structurize_data(input=champs, live_patch=patch)
    # Ensure directory exists before saving
    with open('data/static/champions_lookup_table.json', 'w') as f:
        json.dump(champs_dict, f)
    print("recent data saved in directory: data/static/champions_lookup_table.json")


fc()