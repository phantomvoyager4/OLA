# Open League Analyzer (OLA)

<p align="center">
<img src="https://github.com/phantomvoyager4/OLA/blob/main/data/static/logo/ola%20logo.png" width='300'>
</p>

### This repository contains source code for OLA, open-source league of legends player performance analyzer. It contains frontend app (Vite + React) and backend app (Python FastAPI), contenerized via Docker.

## Tech stack
- Backend: <b>Python</b> (<b>Fast Api</b>)
- Frontend: <b> Node.js + Vite + React </b>
- Docker for correct accros-platform deployment

## Prerequisites
Make sure you have docker install on your computer: [Docker](https://www.docker.com/)


## Instruction
1. Go to Riot Developer Portal, log in and generate api key.
2. Create `.env` file in root directory and insert your API key:
```env
RIOT_API_KEY=[YOUR_KEY]
```
3. Open terminal in project root directory and run:
```env
docker compose up --build
# Add --build while running for the first time, later don't
```
This creates docker images for backend and frontend, which are then composed via `docker-compose.yml` file.

4. Open frontend link: http://localhost:5173 and enjoy application. If you want to terminate application,  use `Ctrl + C` in docker cmd window.



## What's next?
1. ML model for player performance analysis.
2. Champions tier list 

## Contributions
This project is open-source, feel free to open a pull request/issue if you want to!
