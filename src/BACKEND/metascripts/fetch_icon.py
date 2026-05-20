import requests
import json


def fetch_latest_summoners():
    patch_call = requests.get(url='https://ddragon.leagueoflegends.com/api/versions.json')
    live_patch = patch_call.json()[0]
    call = requests.get(url=f'http://ddragon.leagueoflegends.com/cdn/{live_patch}/data/en_US/profileicon.json')   
    json_icons = call.json()
    return live_patch, json_icons

def structurize_data(input: list, live_patch):
    icons_lookup_storage = {}
    icons_lookup_storage["patch"] = live_patch
    for item_id, item_data in input['data'].items():
        icons_lookup_storage[item_id] = {}
        icons_lookup_storage[item_id]["image_path"] = f"https://ddragon.leagueoflegends.com/cdn/{live_patch}/img/profileicon/{item_data['image']['full']}"
    return icons_lookup_storage


def fi():
    patch, icons = fetch_latest_summoners()
    icons_dict = structurize_data(input = icons, live_patch=patch)
    with open('data/static/icons_lookup_table.json', 'w') as f:
        json.dump(icons_dict, f)
    print("recent data saved in directory: data/patch_lookup_table.json")

    
fi()
