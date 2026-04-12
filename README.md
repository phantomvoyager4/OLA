# Open League Analyzer (OLA)

### This repository contains source code for OLA, open-source league of legends player performance analyzer.

## Current state

The repository runs a FastAPI server that can pull match data from the Riot API and serve optimized JSON responses of your match history. What you need to do:

## Instruction
1. Go to [Riot Developer Portal](https://developer.riotgames.com/), log in and generate api key.
2. Being the project root, open terminal and write:
```bash
cd src
python script.py 
```
3. Insert your API key
```bash
# Sript will ask you for it:
Insert your riot API key: [Your key here]
```
Once server will start up, it will automatically open docslink for you to use it 
4. Test it :)
Here you can easily test the endpoint by providing your parameters:
- `platform`: e.g., `EUN1` (see codes below)
- `player_name`: e.g., `softmax`
- `player_tag`: e.g., `EUNE1`
- `count`: quantity of matches you want to fetch

Alternatively, you can call the endpoint directly in your browser or frontend application:
```text
http://127.0.0.1:8000/api/matches/EUN1/softmax/EUNE1?count=1
```
If everything goes correctly, you will receive a JSON response containing the optimized match data! Our pipeline also securely saves a backup of this processed data inside the `data/` folder.
<br> <br>
*Insert platform codes accordingly:
<br> BR1: Brazil <br>
EUN1: Europe Nordic & East<br>
EUW1: Europe West<br>
JP1: Japan<br>
KR: Korea<br>
LA1: Latin America North<br>
LA2: Latin America South<br>
NA1: North America<br>
OC1: Oceania<br>
TR1: Turkey<br>
RU: Russia<br>
PH2: Philippines<br>
SG2: Singapore<br>
TH2: Thailand<br>
TW2: Taiwan<br>
VN2: Vietnam <br>