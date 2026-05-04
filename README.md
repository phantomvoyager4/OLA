# Open League Analyzer (OLA)

<p align="center">
<img src="https://github.com/phantomvoyager4/OLA/blob/main/data/static/logo/ola%20logo.png" width='300'>
</p>

### This repository contains source code for OLA, open-source league of legends player performance analyzer.

## Tech stack
- Backend: <b>Python</b> (<b>Fast Api</b>)
- frontend: <b> Node.js + React </b>


## Instruction
<b>Before you start using this program, make sure you have python and all libraries from </b> `requirements.txt` <b> installed. </b>
1. Go to [Riot Developer Portal](https://developer.riotgames.com/), log in and generate api key.
2. From project root level, open terminal and write:
```bash
cd src
python script.py 
```
3. Insert your API key
```bash
# Sript will ask you for it:
Insert your riot API key: [Your key here]
```
Once server will start up, it will automatically open a website for you to use
4. Test it :)
Here you can use UI to easily test the endpoint by providing your parameters:
- `platform`: e.g., `EUNE`
- `player_name`: e.g., `softmax`
- `player_tag`: e.g., `EUNE1`


## What's next
1. ML model for player performance analysis.
2. Champions tier list 

## Contributions
This project is open-source, feel free to open a pull request/issue if you want to!
