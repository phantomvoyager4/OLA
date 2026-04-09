import copy
import requests
import json
from datetime import datetime



class Caller:
    """
    1. Obtain user riot account PUUID
    2. Fetch last {number} user matches ID
    3. Fetch last {number} user matches data and store it into a separate file / variable (TBD)
    """
    def __init__(self, platform, api_key, player_name, player_tag, count):
        """
        Args:
        region - Regional Routing Value for player. Can be: europe, americas, asia, sea
        api_key - RDP key for API calls
        player_name - riot account username
        player_tag - riot account tagline
        """
        self.platform = platform 
        platform_to_region = {
            "BR1": "americas",
            "LA1": "americas",
            "LA2": "americas",
            "NA1": "americas",
            "EUN1": "europe",
            "EUW1": "europe",
            "TR1": "europe",
            "RU": "europe",
            "ME1": "europe",
            "JP1": "asia",
            "KR": "asia",
            "OC1": "sea",
            "PH2": "sea",
            "SG2": "sea",
            "TH2": "sea",
            "TW2": "sea",
            "VN2": "sea"
        }

        self.region = platform_to_region.get(self.platform.upper())
        if not self.region:
            raise ValueError(f"Invalid platform '{self.platform}'. Cannot map to a region.")

        self.api_key = api_key
        self.player_name = player_name
        self.player_tag = player_tag
        self.url_base_platform = f'https://{self.platform}.api.riotgames.com'
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
    
    def player_metadata_call(self):
        pass


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
        self.championName = player_data.get("championName", default_value)

        
        # Basic Combat Stats
        self.kills = player_data.get("kills", 0)
        self.deaths = player_data.get("deaths", 0)
        self.assists = player_data.get("assists", 0)
        self.champLevel = player_data.get("champLevel", 0)
        self.KDA = round((int(self.kills) + int(self.assists)) / max(1, int(self.deaths)), 2)
        
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
        
        # Farming and Creep Score
        self.totalMinionsKilled = player_data.get("totalMinionsKilled", 0)
        self.neutralMinionsKilled = player_data.get("neutralMinionsKilled", 0)
        self.totalAllyJungleMinionsKilled = player_data.get("totalAllyJungleMinionsKilled", 0)
        self.totalEnemyJungleMinionsKilled = player_data.get("totalEnemyJungleMinionsKilled", 0)
        
        # Vision and Wards
        self.visionScore = player_data.get("visionScore", 0)
        self.wardsPlaced = player_data.get("wardsPlaced", 0)
        self.wardsKilled = player_data.get("wardsKilled", 0)
        self.detectorWardsPlaced = player_data.get("detectorWardsPlaced", 0)
        self.visionWardsBoughtInGame = player_data.get("visionWardsBoughtInGame", 0)

        # Communication and Pings
        self.assistMePings = player_data.get("assistMePings", 0)
        self.commandPings = player_data.get("commandPings", 0)
        self.dangerPings = player_data.get("dangerPings", 0)
        self.enemyMissingPings = player_data.get("enemyMissingPings", 0)
        self.onMyWayPings = player_data.get("onMyWayPings", 0)
        self.retreatPings = player_data.get("retreatPings", 0)

        # Damage Dealt (Offensive)
        self.totalDamageDealtToChampions = player_data.get("totalDamageDealtToChampions", 0)
        self.physicalDamageDealtToChampions = player_data.get("physicalDamageDealtToChampions", 0)
        self.magicDamageDealtToChampions = player_data.get("magicDamageDealtToChampions", 0)
        self.trueDamageDealtToChampions = player_data.get("trueDamageDealtToChampions", 0)
        
        # Damage Taken and Mitigation
        self.totalDamageTaken = player_data.get("totalDamageTaken", 0)
        self.physicalDamageTaken = player_data.get("physicalDamageTaken", 0)
        self.damageSelfMitigated = player_data.get("damageSelfMitigated", 0)
        self.totalHealsOnTeammates = player_data.get("totalHealsOnTeammates", 0)
        self.totalDamageShieldedOnTeammates = player_data.get("totalDamageShieldedOnTeammates", 0)
        
        # Objectives and Utility
        self.objectiveStolen = player_data.get("objectivesStolen", 0)
        self.damageDealtToObjectives = player_data.get("damageDealtToObjectives", 0)
        self.damageDealtToTurrets = player_data.get("damageDealtToTurrets", 0)
        self.timeCCingOthers = player_data.get("timeCCingOthers", 0)
        
        # Game State and Miscellaneous
        self.win = player_data.get("win", False)
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

class Match:
    def __init__(self, match_data: dict):
        """
        Extract generic match data like duration, mode, patch version, 
        and team results based on the Match dictionary.

        Args:
            match_data (dict): raw match data obtained from the Riot API
        """
        self.match_data = match_data
        
        metadata = match_data.get("metadata", {})
        info = match_data.get("info", {})
        
        # Metadata
        self.matchId = metadata.get("matchId", "No data")
        
        # Game Information
        self.gameType = info.get("gameType", "No data")
        self.gameVersion = info.get("gameVersion", "No data")
        self.platformId = info.get("platformId", "No data")
        self.queueId = info.get("queueId", 0)
        gameStartDate = datetime.fromtimestamp(info["gameStartTimestamp"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        gameEndDate = datetime.fromtimestamp(info["gameEndTimestamp"] / 1000).strftime('%H:%M:%S')
        self.gameDate = f"{gameStartDate} - {gameEndDate}"
        self.gameDuration_min = int(info["gameDuration"]) / 60
        
        # Team Results Summary (store list of team IDs and their win status)
        self.teams = []
        for team in info.get("teams", []):
            self.teams.append({
                "teamId": team.get("teamId"),
                "win": team.get("win"),
                "objectives": team.get("objectives", {})
            })

    def to_dict(self):
        """
        Convert Match object into a serializable dictionary.
        """
        data_to_serialize = copy.deepcopy(vars(self))
        if "match_data" in data_to_serialize:
            del data_to_serialize["match_data"]
        return data_to_serialize

    def to_json(self, filepath: str = None):
        """
        Convert the Match object to JSON.
        """
        data_to_serialize = self.to_dict()

        if filepath:
            with open(filepath, "w") as f:
                json.dump(data_to_serialize, f, indent=4)

        return json.dumps(data_to_serialize, indent=4)
