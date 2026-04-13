import requests
import json
from datetime import datetime
from pathlib import Path
import concurrent.futures
import time


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
        upper_platform = platform.upper()
        
        # Map common server names to their routing values
        server_to_platform = {
            "BR": "BR1",
            "EUNE": "EUN1",
            "EUW": "EUW1",
            "JP": "JP1",
            "KR": "KR",
            "LAN": "LA1",
            "LAS": "LA2",
            "NA": "NA1",
            "OCE": "OC1",
            "TR": "TR1",
            "RU": "RU",
            "PH": "PH2",
            "SG": "SG2",
            "TH": "TH2",
            "TW": "TW2",
            "VN": "VN2",
            "ME": "ME1"
        }
        
        # Use mapped value if available, else use the provided value
        self.platform = server_to_platform.get(upper_platform, upper_platform)
        
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
        Obtain user last matches statistics via matches id call using concurrent requests.
        Limiting to 10 workers to respect the Riot Dev API limit of 20 requests per second.
        """
        
        matches_storage = {}
        
        def fetch_match(match):
            url = f'{self.url_base}/lol/match/v5/matches/{match}'
            params = {'api_key': self.api_key}
            
            response = requests.get(url, params)
            
            # Handle rate limiting (HTTP 429 Too Many Requests)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                time.sleep(retry_after)
                # Retry recursively if rate limited
                return fetch_match(match)
                
            if response.status_code == 200:
                return match, response.json()
            return match, None

        # ThreadPoolExecutor runs requests concurrently. 
        # max_workers=12 ensures we never shoot more than 12 requests exactly at the same time,
        # protecting us from hitting the 20 req/1 sec Dev Key rate limit.
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            future_to_match = {executor.submit(fetch_match, match): match for match in matches_id}
            for future in concurrent.futures.as_completed(future_to_match):
                match, data = future.result()
                if data:
                    matches_storage[match] = data
                    
        return matches_storage
    
    def player_metadata_call(self):
        url = f'{self.url_base_platform}/lol/league/v4/entries/by-puuid/{self.puuid}'
        params = {'api_key': self.api_key}
        response = requests.get(url, params)
        if response.status_code == 200:
            player_metadata = response.json()
            ranked_data = next((entry for entry in player_metadata if entry.get("queueType") == "RANKED_SOLO_5x5"), {})
            #winrate calc
            to_pop = ["veteran", "freshBlood", "hotStreak", "inactive", "puuid"]
            for n in to_pop:
                ranked_data.pop(n)
            wins = ranked_data.get("wins", 0)
            losses = ranked_data.get("losses", 0)
            total_matches = wins + losses
            ranked_data["winrate"] = f'{round((wins / total_matches) * 100, 2)}%'

        else:
            return f'Error getting user metadata: {response.status_code}'
        return ranked_data

class Player:
    def __init__(self, player_data: dict, game_duration_sec: int, runes_lookup: dict = None):
        """Map dictionary values to correct class attributes (based on OOD)
           Prepare JSON file for server response

        Args:
            player_data (dict): input from Parser class
            game_duration_sec (int): game duration in seconds passed from match metadata
        """
        self.player_data = player_data

        # Use passed lookup or fallback to default
        if runes_lookup:
            currentPatch = runes_lookup.get("patch", "14.1.1")
        else:
            project_root = Path(__file__).resolve().parent.parent
            lookup_path = project_root / "data" / "static" / "runes_lookup_table.json"
            with open(lookup_path, "r") as f:
                lookup_table = json.load(f)
            currentPatch = lookup_table.get("patch", "14.1.1")

        self.player_data = player_data
        default_value = "No data"
        
        # Identity, Position and Summoners
        self.username = f'{player_data.get("riotIdGameName", default_value)} #{player_data.get("riotIdTagline", default_value)}'
        self.puuid = player_data.get("puuid", default_value)
        self.teamPosition = player_data.get("teamPosition", default_value)
        self.championName = player_data.get("championName", default_value)
        self.championImageLink = f"https://ddragon.leagueoflegends.com/cdn/{currentPatch}/img/champion/{self.championName}.png"
        self.summonerLevel = player_data.get("summonerLevel", default_value)

        
        # Basic Combat Stats
        self.kills = player_data.get("kills", 0)
        self.deaths = player_data.get("deaths", 0)
        self.assists = player_data.get("assists", 0)
        self.champLevel = player_data.get("champLevel", 0)
        self.KDA = round((int(self.kills) + int(self.assists)) / max(1, int(self.deaths)), 2)
        
        
        # Crucial Advanced Metrics (Challenges)
        challenges = player_data.get("challenges", {})
        self.killParticipation = f"{round(challenges.get('killParticipation', 0) * 100, 2)}%"
        self.skillshotsDodged = challenges.get("skillshotsDodged", 0)
        self.skillshotsHit = challenges.get("skillshotsHit", 0)
        self.teamDamagePercentage = f"{round(challenges.get('teamDamagePercentage', 0) * 100, 2)}%"
        self.damageTakenOnTeamPercentage = f"{round(challenges.get('damageTakenOnTeamPercentage', 0) * 100, 2)}%"
        self.damagePerMinute = round(challenges.get("damagePerMinute", 0), 2)
        self.goldPerMinute = round(challenges.get("goldPerMinute", 0), 2)
        self.soloKills = challenges.get("soloKills", 0)
        self.visionScorePerMinute = round(challenges.get("visionScorePerMinute", 0), 2)
        self.maxCsAdvantageOnLaneOpponent = round(challenges.get("maxCsAdvantageOnLaneOpponent", 0), 1)
        
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
        self.totalJungleMinionsKilled = player_data.get("neutralMinionsKilled", 0)

        total_cs = int(self.totalMinionsKilled) + int(self.totalJungleMinionsKilled)
        
        duration_min = game_duration_sec / 60
        if duration_min > 0:
            self.cs_min = round(int(total_cs) / duration_min, 1)
        else:
            self.cs_min = 0.0
            
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
        self.gameEndedInSurrender = player_data.get("gameEndedInSurrender", False)
        self.totalTimeSpentDead = player_data.get("totalTimeSpentDead", 0)

    def runes_mapping(self, lookup_table: dict):
        """Find given rune data using patch lookup table

        Args:
            runes_map (dict): current runes data fetch from ddragon
        """
        runes = self.player_data.get("perks", {})
        if not runes:
            self.runes = []
            return

        self.stat_perks = list(runes.get("statPerks", {}).values())
        self.style_names = []
        self.perks = []
        
        for n in runes.get("styles", []):
            self.style_names.append(n.get("style"))
            for i in n.get("selections", []):
                self.perks.append(i.get("perk"))
        all_ids = self.stat_perks + self.style_names + self.perks
        all_ids_strings = []
        for n in all_ids:
            if n is not None:
                all_ids_strings.append(str(n))

        self.runes = []
        for rune_id in all_ids_strings:
            mapped_rune = lookup_table.get(rune_id)
            if mapped_rune:
                self.runes.append(mapped_rune)
    
    def summoners_mapping(self, lookup_table: dict):
        summoner1 = self.player_data.get("summoner1Id", "No data")
        summoner2 = self.player_data.get("summoner2Id", "No data")
        self.summoners = []
        self.summoners.append(lookup_table.get(str(summoner1), {}))
        self.summoners.append(lookup_table.get(str(summoner2), {}))
        
    def items_mapping(self, lookup_table: dict):
        self.items = []
        for n in range(7):  
            item_id = self.player_data.get(f"item{n}", "No data")
            mapped_item = lookup_table.get(str(item_id), {})
            self.items.append(mapped_item)

    def to_dict(self):
        """
        Convert Player object into a serializable dictionary.
        """
        data_to_serialize = dict(vars(self))

        data_to_serialize.pop("player_data", None)

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
        duration_sec = int(info.get("gameDuration", 0))
        self.gameDuration_min = float(f"{duration_sec // 60}.{duration_sec % 60:02d}")
        
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
        data_to_serialize = dict(vars(self))
        data_to_serialize.pop("match_data", None)
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
