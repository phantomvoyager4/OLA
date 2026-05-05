import sys
import os

# Get the absolute path of the parent directory (src/) and add it to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import load_api_key, pipeline

api_key = load_api_key()
test_obj = pipeline(api_key=api_key, platform='EUW1', player_name='401dmg', player_tag='6969', count=1, save=False)
player_object = test_obj[0]['players'][0]
