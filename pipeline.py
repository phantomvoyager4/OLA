import os
import json
from dotenv import load_dotenv
from model import Caller, Parser


def pipeline(api_key, player_name, player_tag, region, count):
    """
    Create Caller class instance with appropriate arguments -> 
    Fetch PUUID by username and tagline -> 
    Fetch ID's of last matches played ->
    Fetch last matches data

    (TBA) extract most important data from match info (Parser class)
    (TBA) create Player class instance for each player with parser data as attributes
    """ 
    usercall = Caller(region=region, api_key=api_key, player_name=player_name, player_tag=player_tag, count=count)
    puuidme = usercall.get_puuid()
    matches_id = usercall.last_matches_id_call(puuidme)
    matches_data = usercall.last_matches_data_call(matches_id)
    with open(f'data/data_from_{count}_previous_matches.json', 'w') as f:
        json.dump(matches_data, f)
    return matches_data
    



load_dotenv()
api_key = os.getenv('RIOT_API_KEY')
softmax = pipeline(api_key=api_key, region='europe', player_name='softmax', player_tag='EUNE1', count=3)