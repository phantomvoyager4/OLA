from dotenv import load_dotenv
import os
import requests
import json



class Caller:
    """
    Class designed to:
    1. Obtain user riot account PUUID
    2. Fetch last 20 user matches ID
    3. Fetch last 20 user matches data and store it into a separate file / variable (TBD)
    """
    def __init__(self, region, api_key, player_name, player_tag, count):
        """
        Args:
        region - Regional Routing Value for player. Can be: europe, americas, asia, sea
        api_key - RDP key for API calls
        player_name - riot account username
        player_tag - riot account tagline
        """
        self.region = region
        self.api_key = api_key
        self.player_name = player_name
        self.player_tag = player_tag
        self.url_base = f'https://{self.region}.api.riotgames.com'
        self.count = count

    def get_puuid(self):
        """
        Fetch puuid (unique ID value for each riot account)
        by player name and tagline
        """
        url = f'{self.url_base}/riot/account/v1/accounts/by-riot-id/{self.player_name}/{self.player_tag}'
        params = {
            'api_key': self.api_key
        }
        call = requests.get(url=url, params=params)
        if call.status_code == 200:
            return call.json()['puuid']

    def last_matches_id_call(self, puuid): 
        """
        Fetch user last {count} matches ID

        Args:
        puuid - unique riot account ID obtained in get_puuid function
        """
        url = f'{self.url_base}/lol/match/v5/matches/by-puuid/{puuid}/ids'
        params = {
            'start': 0,
            'count': self.count,
            'api_key': self.api_key,
            'queue': 420
        }
        response = requests.get(url=url, params=params)
        if response.status_code == 200:
            return response.json() 
        else:
            return f'Error getting user matches ID: {response.status_code}'
    
    def last_matches_data_call(self, matches_id: list):
        """
        Obtain user last matches statistics via matches id call
        
        Args:
        matches_id - list of user last matches id
        """
        matches_storage = {}
        for match in matches_id:
            url = f'{self.url_base}/lol/match/v5/matches/{match}'
            params = {'api_key': self.api_key}
            response = requests.get(url, params)
            if response.status_code == 200:
                matches_storage[match] = response.json()
        return matches_storage

class Parser:
    def __init__(self, input: dict, player_index: int):
        self.input = input
        self.player_index = player_index

    def extract(self):
        index = ""


class Player:
    pass
    # def __init__(self, input, game_id, player_index):
    #     self.input = input
    #     self.player_index = player_index
    #     self.game_id = game_id
    #     self.kills = input[game_id]["info"]["participants"][player_index]["kills"]
        


