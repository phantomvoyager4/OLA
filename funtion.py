from dotenv import load_dotenv
import os
import pandas as pd
import requests
import json




load_dotenv()
api_key = os.getenv('RIOT_API_KEY')

def last_matches_id_call(puuid, api_key, region, count=20):
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids'
    params = {
        'start': 0,
        'count': count,
        'api_key': api_key

    }
    response = requests.get(url=url, params=params)
    if response.status_code == 200:
        return response.json() 
    else:
        return f"Error: {response.status_code}"


m1 = last_matches_id_call(puuid=user_puuid, api_key=api_key, region='europe')
print(m1)
last_match_id = m1[1]
print(last_match_id)

def last_match_info_call(region, match_id):
    url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    params = {
        'api_key': api_key
    }
    response = requests.get(url=url, params=params)
    if response.status_code == 200:
        return response.json() 
    else:
        return f"Error: {response.status_code}"
    

meczyk = last_match_info_call(region='europe', match_id=last_match_id)
print(meczyk['info']['gameMode'])