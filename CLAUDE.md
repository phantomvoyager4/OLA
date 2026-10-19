# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# OLA

Player-performance site for League of Legends ranked solo/duo (queue 420 only).

- `src/BACKEND`: Python 3.12 FastAPI app and scoring (`model.py`), imported as the `BACKEND` package from `src`
- `src/FRONTEND`: React 19 + Vite + Tailwind 4
- `src/ANALYSIS`: offline analysis; `fetching_script.py` crawls matches into `data/`, which the score reference is built from
- `data/static`: lookup tables and `score_reference.json`; also Vite's `publicDir`
- `data/example_data/401dmg#6969_20.json`: fixture the scoring tests load

Python runs on the system interpreter. `.env` is a dotenv file holding `RIOT_API_KEY` (plus optional `GROQ_API_KEY`/`GROQ_MODEL` for the AI overview), not a virtualenv; don't read or commit it. `check_auc.py` also needs numpy and scikit-learn, which aren't in `requirements.txt`.

## Commands

- Tests: `cd src && python -m unittest BACKEND.tests.test_scoring`
- Single test: `cd src && python -m unittest BACKEND.tests.test_scoring.RemakeTest.test_riot_flag_decides_when_present`
- Score evaluation (held-out, split by match_id): `cd src && python check_auc.py --seeds 0 1 2 3 4`
- Rebuild score reference: `cd src && python -m BACKEND.metascripts.build_score_reference --data-dir ANALYSIS/data`
- Refresh lookup tables (run from repo root): `python src/BACKEND/metascripts/run_all_scripts.py`
- Backend: `cd src && python -m uvicorn BACKEND.main:app --reload --port 8000`
- Frontend: `cd src/FRONTEND && npm run dev` / `npm run build` / `npm run lint`. Outside Docker, set `VITE_PROXY_TARGET=http://127.0.0.1:8000`; the `/api` proxy defaults to the Docker host `backend:8000`.
- Full stack: `docker compose up --build` (both services hot-reload from the mounted source)

## Architecture

`/api/matches` → `pipeline.pipeline()` → `model.Caller` fetches the PUUID, match IDs and match payloads → each participant becomes a `Player`, each game a `Match` → `annotate_player_performance` adds scores → `summarizer` stats are appended as the last element of the returned list, so filter on `"players" in item`.

- Every Riot call goes through `riot_api.riot_get_json`: one process-wide rate limiter (18/s and 90/120s, under the dev key's 20/100) plus an in-memory TTL cache. All state lives in the single backend process and is lost on restart.
- The dev-key budget is small: a 20-match profile costs about 22 calls. Don't loop live requests.
- Tier list: `python -m BACKEND.tier_list_fetcher` is an offline collector that atomically writes `data/tier_list/euw_master_plus_latest.json`; the `/api/tier-list` routes only read that snapshot. Stop the backend while collecting, since both spend the same key budget.
- `ai_overview.py` turns a digest the browser posts into prose via Groq. It makes no Riot calls and never affects scores.
- The frontend's `/match/:id` page reads matches cached in memory by the profile page; opened directly it shows "Match data not found."

## Scoring gotchas

- After changing a feature in `_extract_performance_features`, rebuild the score reference. It is only checked by feature names, so a stale one is used silently.
- `load_score_reference()` is `lru_cache`d: restart the backend after rebuilding the reference.
- Without a usable reference (or for a role missing from it), players are ranked only against the current request, so scores depend on which matches were loaded.
- Get game length with `game_duration_minutes()`: matches saved before `gameDuration_sec` existed store `gameDuration_min` as minutes.seconds.
- Detect remakes with `is_remake()`; remakes are not scored.

## Rules

- Never report a metric without the exact command and its output.
- Before any evaluation, check that no match_id appears in both train and test.
- Ask before changing `PERFORMANCE_FEATURE_WEIGHTS`.
