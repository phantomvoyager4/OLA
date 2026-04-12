import requests
import json


def fetch_latest_items(): 
    patch_call = requests.get(url='https://ddragon.leagueoflegends.com/api/versions.json')
    live_patch = patch_call.json()[0]
    items_call = requests.get(url=f'http://ddragon.leagueoflegends.com/cdn/{live_patch}/data/en_US/item.json')   
    json_items = items_call.json()     
    return live_patch, json_items

def structurize_data(input: dict, live_patch: str):
    items_lookup_storage = {}
    items_lookup_storage["patch"] = live_patch
    for item_id, item_data in input['data'].items():
        items_lookup_storage[item_id] = {}
        attributes = ["name", "description"]
        for i in attributes:
            items_lookup_storage[item_id][i] = item_data.get(i, "")
        items_lookup_storage[item_id]["image_path"] = f"https://ddragon.leagueoflegends.com/cdn/{live_patch}/img/item/{item_data['image']['full']}"
        items_lookup_storage[item_id]["price"] = item_data["gold"]["total"]
    return items_lookup_storage

def fi():
    patch, items = fetch_latest_items()
    items_dict = structurize_data(input=items, live_patch=patch)
    with open('data/static/items_lookup_table.json', 'w') as f:
        json.dump(items_dict, f)
    print("recent data saved in directory: data/static/items_lookup_table.json")

fi()