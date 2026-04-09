# Open League Analyzer (OLA)

### This repository contains source code for OLA, open-source league of legends player performance analyzer.

## Current state

for now, repo can pull json file from riot server and create an optimized object of your match data! What you need to do:
1. In repo directory, create `venv` folder,
2. Inside it, create .env file with this structure:
```bash
RIOT_API_KEY = "[YOUR_API_KEY_HERE]"
# To acquire api key, create an account on https://developer.riotgames.com site and generate api key
```

3. Install dependencies:
```bash
# Make sure your bash is in this repo directory
pip install requirements.txt
```

4. Open `src/pipeline.py` file and create your function instance:

```python
pipeline(api_key=api_key, platform=[YOUR_PLATFORM*], player_name=[YOUR_RIOT_ACCOUNT_USERNAME], player_tag=[YOUR_RIOT_ACCOUNT_TAG], count=[quantity of matches you want to fetch])

#here is in example for my account:
pipeline(api_key=api_key, platform='EUN1', player_name='softmax', player_tag='EUNE1', count=1)
```
if everything goes correctly, you should see this message in your bash:
```bash
Matches fetched
objects created sucessfuly :)
Combined objects created in directory: data/your_file_name.json
```

<br><br>

*Insert platform codes accordingly:
BR1: Brazil
EUN1: Europe Nordic & East
EUW1: Europe West
JP1: Japan
KR: Korea
LA1: Latin America North
LA2: Latin America South
NA1: North America
OC1: Oceania
TR1: Turkey
RU: Russia
PH2: Philippines
SG2: Singapore
TH2: Thailand
TW2: Taiwan
VN2: Vietnam 