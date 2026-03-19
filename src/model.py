import copy
import requests
import json



class Caller:
    """
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
            self.puuid = call.json()['puuid']
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
    def __init__(self, match_data: dict, target_puuid: str):
        self.match_data = match_data
        self.target_puuid = target_puuid
        self.players_data = self.match_data["info"]["participants"]

        with open("data/patch_lookup_table.json", "r") as f:
            self.lookup_table = json.load(f)

        self.player_index = self.indexing()
        self.player_data = self.players_data[self.player_index] if self.player_index is not None else None

    def indexing(self):
        for index, participant in enumerate(self.players_data):
            if participant.get("puuid") == self.target_puuid:
                return index
        return None


class Player:
    def __init__(self, player_data: dict):
        """Map dictionary values to correct class attributes (based on OOD)
           Prepare JSON file for server response

        Args:
            player_data (dict): input from Parser class
        """
        self.player_data = player_data
        default_value = "No data"
        
        # Identity and Position
        self.name = player_data.get("riotIdGameName", default_value)
        self.tagline = player_data.get("riotIdTagline", default_value)
        self.puuid = player_data.get("puuid", default_value)
        self.lane = player_data.get("lane", default_value)
        self.teamPosition = player_data.get("teamPosition", default_value)
        
        # Basic Combat Stats
        self.kills = player_data.get("kills", 0)
        self.deaths = player_data.get("deaths", 0)
        self.assists = player_data.get("assists", 0)
        self.champLevel = player_data.get("champLevel", 0)
        self.championName = player_data.get("championName", default_value)
        
        # Multi-kills and Sprees
        self.doubleKills = player_data.get("doubleKills", 0)
        self.tripleKills = player_data.get("tripleKills", 0)
        self.quadraKills = player_data.get("quadraKills", 0)
        self.pentaKills = player_data.get("pentaKills", 0)
        self.killingSprees = player_data.get("killingSprees", 0)
        self.largestKillingSpree = player_data.get("largestKillingSpree", 0)
        
        # Economy and Items
        self.goldEarned = player_data.get("goldEarned", 0)
        self.goldSpent = player_data.get("goldSpent", 0)
        self.itemsPurchased = player_data.get("itemsPurchased", 0)
        
        # Damage Dealt (Offensive)
        self.totalDamageDealtToChampions = player_data.get("totalDamageDealtToChampions", 0)
        self.physicalDamageDealtToChampions = player_data.get("physicalDamageDealtToChampions", 0)
        self.magicDamageDealtToChampions = player_data.get("magicDamageDealtToChampions", 0)
        self.trueDamageDealtToChampions = player_data.get("trueDamageDealtToChampions", 0)
        
        # Damage Taken (Defensive)
        self.totalDamageTaken = player_data.get("totalDamageTaken", 0)
        self.physicalDamageTaken = player_data.get("physicalDamageTaken", 0)
        
        # Objectives and Jungle
        self.neutralMinionsKilled = player_data.get("neutralMinionsKilled", 0)
        self.totalAllyJungleMinionsKilled = player_data.get("totalAllyJungleMinionsKilled", 0)
        self.totalEnemyJungleMinionsKilled = player_data.get("totalEnemyJungleMinionsKilled", 0)
        self.objectiveStolen = player_data.get("objectivesStolen", 0)
        
        # Game State and Miscellaneous
        self.gameEndedInSurrender = player_data.get("gameEndedInSurrender", False)
        self.totalTimeSpentDead = player_data.get("totalTimeSpentDead", 0)

        # Runes 
        self.runes = player_data.get("perks", {})

    def runes_mapping(self, lookup_table: dict):
        """Find given rune data using patch lookup table

        Args:
            runes_map (dict): current runes data fetch from ddragon
        """
        if not self.runes: return None

        self.stat_perks = list(self.runes.get("statPerks", {}).values())
        self.style_names = []
        self.perks = []
        
        for n in self.runes.get("styles", []):
            self.style_names.append(n.get("style"))
            for i in n.get("selections", []):
                self.perks.append(i.get("perk"))
        all_ids = self.stat_perks + self.style_names + self.perks
        all_ids_strings = []
        for n in all_ids:
            if n is not None:
                all_ids_strings.append(str(n))

        self.runes_mapped = []
        for rune_id in all_ids_strings:
            mapped_rune = lookup_table.get(rune_id)
            if mapped_rune:
                self.runes_mapped.append(mapped_rune)

    def to_dict(self):
        """
        Convert Player object into a serializable dictionary.
        If mapped runes are available, they replace raw runes.
        """
        data_to_serialize = copy.deepcopy(vars(self))

        if "player_data" in data_to_serialize:
            del data_to_serialize["player_data"]

        if "runes_mapped" in data_to_serialize:
            data_to_serialize["runes"] = data_to_serialize["runes_mapped"]
            del data_to_serialize["runes_mapped"]

        for key in ("stat_perks", "style_names", "perks"):
            data_to_serialize.pop(key, None)

        return data_to_serialize

    def to_json(self, filepath: str = None):
        """
        Convert the Player object to JSON.
        """
        data_to_serialize = self.to_dict()

        if filepath:
            with open(filepath, "w") as f:
                json.dump(data_to_serialize, f, indent=4)

        return json.dumps(data_to_serialize, indent=4)

class Match_Data:
        def __init__(self, match_data: dict):
            self.match_data = match_data
