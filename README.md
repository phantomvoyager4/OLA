# Open League Analyzer (OLA)



### This repository contains source code for OLA, open-source league of legends player performance analyzer.

## Current state

The repository runs a FastAPI server that can pull match data from the Riot API and serve optimized JSON responses of your match history. 
<br>
<b>Before you start using this program, make sure you have python and all libraries from </b> `requirements.txt` <b> installed. </b>

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
Once server will start up, it will automatically website for you to use
4. Test it :)
Here you can use UI to easily test the endpoint by providing your parameters:
- `platform`: e.g., `EUNE`
- `player_name`: e.g., `softmax`
- `player_tag`: e.g., `EUNE1`

Alternatively, you can call the endpoint directly in your browser or frontend application:
```text
http://127.0.0.1:8000/api/matches/[platform]/[player_name]/[player_tag]?count=20
For example:
http://127.0.0.1:8000/api/matches/EUW/401dmg/6969?count=20
```
If everything goes correctly, you will receive a JSON response containing the optimized match data! Our pipeline also securely saves a backup of this processed data inside the `data/` folder. 

## What's next
1. ML model for player performance analysis
