import json
import sys
import os

if os.path.exists('protocole.json'):
    try:
        with open('protocole.json', 'r') as f:
            pro = json.load(f)
    except json.JSONDecodeError:
        pro = {}
else:
    pro = {}

def check_quit(user_input):
    if user_input.lower() == 'q':
        with open('protocole.json', 'w') as f:
            json.dump(pro, f, indent=4)
        sys.exit(0)
    return user_input

while True:
    server = check_quit(input('server: '))
    tier = check_quit(input('tier: '))
    player_nickname = check_quit(input('player input: '))
    
    base_key = f'{server}_{tier}'
    
    count = sum(1 for key in pro if key.startswith(base_key))
    
    unique_key = f'{base_key}_{count + 1}'
    
    pro[unique_key] = {
        'player_nickname': player_nickname
    }
    print(f'saved as {unique_key}')