from dotenv import load_dotenv
import os
import requests
import json


load_dotenv()
api_key = os.getenv('RIOT_API_KEY')


class Caller:
    """
    Class designed to:
    1. Obtain user riot account PUUID
    2. Fetch last 20 user matches ID
    3. Fetch last 20 user matches data and store it into a separate file / variable (TBD)
    """
    def __init__(self, region, api_key, player_name, player_tag):
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

    def last_matches_id_call(self, puuid, count=5): 
        """
        Fetch user last {count} matches ID

        Args:
        puuid - unique riot account ID obtained in get_puuid function
        """
        url = f'{self.url_base}/lol/match/v5/matches/by-puuid/{puuid}/ids'
        params = {
            'start': 0,
            'count': count,
            'api_key': self.api_key
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








# Pipeline: Creating Caller class instance with appropriate  arguments -> Fetching PUUID by username and tagline -> Fetching ID's of last 20 matches played
usercall = Caller('europe', api_key, 'softmax', 'EUNE1')
puuidme = usercall.get_puuid()
print(f'User PUUID: {puuidme}')
matches_id = usercall.last_matches_id_call(puuidme)
print(f'Matches_id list: {matches_id}')
matches_data = usercall.last_matches_data_call(matches_id)
print(matches_data)


