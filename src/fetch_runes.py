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

def structurize_data(input: dict, live_patch):
    """
    Create efficent lookup table for easy data retrieval
    
    :param input: fetched runes list from ddragon dataset
    :type input: dict
    :param live_patch: current patch passed from last function
    """
    runes_lookup_storage = {}
    runes_lookup_storage["patch"] = live_patch
    with open("data/stats.perks.json", 'r') as f:
        stats_perks = json.load(f)
    for style in input:
        style_name = style["name"]
        runes_lookup_storage[str(style['id'])] = {"name": style_name, "group": "Style","icon": "", "description": ""}
        for slot in style['slots']:
            for rune in slot['runes']:
                runes_lookup_storage[str(rune['id'])] = {
                    "name": rune['name'],
                    "group": style_name,
                    "icon": rune['icon'],
                    "description": rune['shortDesc']
                }
    runes_lookup_storage = runes_lookup_storage | stats_perks

    return runes_lookup_storage


def fr():
    patch, runes = fetch_latest_data()
    runes_dict = structurize_data(input = runes, live_patch=patch)
    with open('data/patch_lookup_table.json', 'w') as f:
        json.dump(runes_dict, f)
    print("recent data saved in directory: data/patch_lookup_table.json")

fr()