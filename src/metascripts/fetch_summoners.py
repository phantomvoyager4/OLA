import requests
import json


def fetch_latest_summoners():
    patch_call = requests.get(url='https://ddragon.leagueoflegends.com/api/versions.json')
    live_patch = patch_call.json()[0]
    summoners_call = requests.get(url=f'http://ddragon.leagueoflegends.com/cdn/{live_patch}/data/en_US/summoner.json')   
    json_summoners = summoners_call.json()
    ranked_summoners = []
    for n in json_summoners['data'].values():
        if 'CLASSIC' in n['modes']:
            ranked_summoners.append(n)
    return live_patch, ranked_summoners


def structurize_data(input: list, live_patch):
    summoners_lookup_storage = {}
    summoners_lookup_storage["patch"] = live_patch
    for n in input:
        spell_key = n["key"]
        summoners_lookup_storage[spell_key] = {}
        attributes = ["name", "description", "cooldownBurn", "key"]
        for i in attributes:
            summoners_lookup_storage[spell_key][i] = n[i]
        summoners_lookup_storage[spell_key]["image_path"] = f"https://ddragon.leagueoflegends.com/cdn/{live_patch}/img/spell/{n['image']['full']}"
    return summoners_lookup_storage

def fs():
    patch, summoners = fetch_latest_summoners()
    summoners_dict = structurize_data(input = summoners, live_patch=patch)
    with open('data/static/summoners_lookup_table.json', 'w') as f:
        json.dump(summoners_dict, f)
    print("recent data saved in directory: data/patch_lookup_table.json")

fs()
    
