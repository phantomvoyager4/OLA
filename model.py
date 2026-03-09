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
    def __init__(self, input: dict, match_id: str, player_index: int):
        """
        Extract player data from match statistics

        Args:
            input (dict): data in dict format from matches endpoint request
            player_index (int): index of player to extract data for
            match_id (str): id of match to extract data from
        """
        self.input = input
        self.player_index = player_index
        self.game_id = match_id
        self.player_data = input[self.game_id]["info"]["participants"][self.player_index]
        with open("data/patch_lookup_table.json", 'r') as f:
            self.lookup_table = json.load(f)

class Player:
    def __init__(self, player_data: dict):
        """Map dictionary values to correct class attributes (based on OOD)
           Prepare JSON file for server response

        Args:
            player_data (dict): input from Parser class
        """
        self.player_data = player_data
        
        # Identity and Position
        self.name = player_data["riotIdGameName"]
        self.tagline = player_data["riotIdTagline"]
        self.lane = player_data["lane"]
        self.teamPosition = player_data["teamPosition"]
        
        # Basic Combat Stats
        self.kills = player_data["kills"]
        self.deaths = player_data["deaths"]
        self.assists = player_data["assists"]
        self.champLevel = player_data["champLevel"]
        self.championName = player_data["championName"]
        
        # Multi-kills and Sprees
        self.doubleKills = player_data["doubleKills"]
        self.tripleKills = player_data["tripleKills"]
        self.quadraKills = player_data["quadraKills"]
        self.pentaKills = player_data["pentaKills"]
        self.killingSprees = player_data["killingSprees"]
        self.largestKillingSpree = player_data["largestKillingSpree"]
        
        # Economy and Items
        self.goldEarned = player_data["goldEarned"]
        self.goldSpent = player_data["goldSpent"]
        self.itemsPurchased = player_data["itemsPurchased"]
        
        # Damage Dealt (Offensive)
        self.totalDamageDealtToChampions = player_data["totalDamageDealtToChampions"]
        self.physicalDamageDealtToChampions = player_data["physicalDamageDealtToChampions"]
        self.magicDamageDealtToChampions = player_data["magicDamageDealtToChampions"]
        self.trueDamageDealtToChampions = player_data["trueDamageDealtToChampions"]
        
        # Damage Taken (Defensive)
        self.totalDamageTaken = player_data["totalDamageTaken"]
        self.physicalDamageTaken = player_data["physicalDamageTaken"]
        
        # Objectives and Jungle
        self.neutralMinionsKilled = player_data["neutralMinionsKilled"]
        self.totalAllyJungleMinionsKilled = player_data["totalAllyJungleMinionsKilled"]
        self.totalEnemyJungleMinionsKilled = player_data["totalEnemyJungleMinionsKilled"]
        self.objectiveStolen = player_data["objectivesStolen"]
        
        # Game State and Miscellaneous
        self.gameEndedInSurrender = player_data["gameEndedInSurrender"]
        self.totalTimeSpentDead = player_data["totalTimeSpentDead"]

        # Runes 
        self.runes_raw = player_data["perks"]

    def runes_mapping(self, lookup_table: dict):
        """Find given rune data using patch lookup table

        Args:
            runes_map (dict): current runes data fetch from ddragon
        """

        self.runes_mapped = {}
        self.stat_runes = self.runes_raw["statPerks"]
        self.primaryStyle = self.runes_raw["styles"][0]
        self.subStyle = self.runes_raw["styles"][1]



        




        


