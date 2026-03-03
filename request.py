from dotenv import load_dotenv
import os
import requests
import json


load_dotenv()
api_key = os.getenv('RIOT_API_KEY')


class Caller:
    def __init__(self, region, api_key, player_name, player_tag):
        self.region = region
        self.api_key = api_key
        self.player_name = player_name
        self.player_tag = player_tag

    def get_puuid(self):
        url = f'https://{self.region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{self.player_name}/{self.player_tag}'
        params = {
            'api_key': self.api_key
        }
        call = requests.get(url=url, params=params)
        if call.status_code == 200:
            return call.json()['puuid']
        return None

    
    def last_matches_id_call(self, puuid, count=20):
        puuid = self.get_puuid()
        url = f'https://{self.region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids'
        params = {
            'start': 0,
            'count': count,
            'api_key': self.api_key
        }
        response = requests.get(url=url, params=params)
        if response.status_code == 200:
            return response.json() 
        else:
            return f'Error getting user matches: {response.status_code}'
        

usercall = Caller('europe', api_key, 'softmax', 'EUNE1')

# 1. Get PUUID
my_puuid = usercall.get_puuid()

# 2. Get Match IDs if PUUID exists
if my_puuid:
    match_ids = usercall.last_matches_id_call(my_puuid)
    print(f"Found {len(match_ids)} matches. Latest: {match_ids[0]}")
else:
    print("Could not find player.")




