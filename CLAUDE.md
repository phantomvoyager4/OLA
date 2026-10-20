# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# OLA

Player-performance site for League of Legends ranked solo/duo (queue 420 only).

- `src/BACKEND`: Python 3.12 FastAPI app and scoring (`model.py`), imported as the `BACKEND` package from `src`
- `src/FRONTEND`: React 19 + Vite + Tailwind 4
- `src/ANALYSIS`: offline analysis; `data/` holds the snowball crawl (`fetching_sample/fetching_script.py`) the score reference is built from. `fetching_sample/ladder_sampler.py` is its per-patch replacement: it draws players from Riot's ranked ladder and writes to `fetching_sample/samples/<patch>/<platform>/`
- `data/static`: lookup tables and `score_reference.json`; also Vite's `publicDir`
- `data/example_data/401dmg#6969_20.json`: fixture the scoring tests load

Python runs on the system interpreter. `.env` is a dotenv file holding `RIOT_API_KEY` (plus optional `GROQ_API_KEY`/`GROQ_MODEL` for the AI overview), not a virtualenv; don't read or commit it. `check_auc.py` also needs numpy and scikit-learn, which aren't in `requirements.txt`.

## Commands

- Tests: `cd src && python -m unittest BACKEND.tests.test_scoring`
- Single test: `cd src && python -m unittest BACKEND.tests.test_scoring.RemakeTest.test_riot_flag_decides_when_present`
- Score evaluation (held-out, split by match_id): `cd src && python check_auc.py --seeds 0 1 2 3 4`
- Rebuild score reference: `cd src && python -m BACKEND.metascripts.build_score_reference --data-dir ANALYSIS/data`
- Refresh lookup tables (run from repo root): `python src/BACKEND/metascripts/run_all_scripts.py`
- Ladder sample of the live patch (backend stopped; settings in `src/ANALYSIS/fetching_sample/settings.json`): `cd src && python -m ANALYSIS.fetching_sample.ladder_sampler`. Small test: `--regions EUN1 --games-per-region 10`. A rerun resumes; `--report-only` rebuilds `processed/` and `report.txt` with no API calls. The full settings (4,000 games per server, 3 per player) project to about 6.2 h per route; `analysis/sample_summary.py` re-projects from any run. The sampler starts `caffeinate` on macOS, but a closed lid on battery still sleeps and drops every connection, so keep long runs on the charger.
- Sampler tests: `cd src && python -m unittest ANALYSIS.fetching_sample.test_ladder_sampler`
- Backend: `cd src && python -m uvicorn BACKEND.main:app --reload --port 8000`
- Frontend: `cd src/FRONTEND && npm run dev` / `npm run build` / `npm run lint`. Outside Docker, set `VITE_PROXY_TARGET=http://127.0.0.1:8000`; the `/api` proxy defaults to the Docker host `backend:8000`.
- Full stack: `docker compose up --build` (both services hot-reload from the mounted source)

## Architecture

`/api/matches` → `pipeline.pipeline()` → `model.Caller` fetches the PUUID, match IDs and match payloads → each participant becomes a `Player`, each game a `Match` → `annotate_player_performance` adds scores → `summarizer` stats are appended as the last element of the returned list, so filter on `"players" in item`.

- Every Riot call goes through `riot_api.riot_get_json`: one process-wide rate limiter (18/s and 90/120s, under the dev key's 20/100) plus an in-memory TTL cache. All state lives in the single backend process and is lost on restart.
- Riot counts the key's limit per routing value, not per key: EUW1 and EUN1 share `europe` for match and account calls, NA1 and BR1 share `americas`, KR uses `asia`, and each platform host (`euw1`, `eun1`, ...) has its own budget for league calls. The ladder sampler keeps one limiter per route and runs regions in parallel; the backend's single limiter is stricter than it needs to be.
- The dev-key budget is small: a first profile view costs about 65 calls, about 24 for `/api/matches` (account, match list, 20 matches, rank, mastery) and about 41 for the activity heatmap (`/api/activity?count=40&start=20` fetches 40 more matches). Accounts are cached for a day and matches for 30 days, so repeat views cost far less. Two new profiles in a row fill the backend's 90/120s, which the frontend shows as "API capacity full". Don't loop live requests.
- Tier list: `python -m BACKEND.tier_list_fetcher` is an offline collector that atomically writes `data/tier_list/euw_master_plus_latest.json`; the `/api/tier-list` routes only read that snapshot. Stop the backend while collecting, since both spend the same key budget.
- `ai_overview.py` turns a digest the browser posts into prose via Groq. It makes no Riot calls and never affects scores.
- The frontend's `/match/:id` page reads matches cached in memory by the profile page; opened directly it shows "Match data not found."

## Scoring gotchas

- After changing how `_extract_performance_features` computes a feature, bump `FEATURE_VERSION` in `model.py` and rebuild the score reference. A reference built for other feature names or another version is refused with a printed warning.
- `load_score_reference()` is `lru_cache`d: restart the backend after rebuilding the reference.
- Without a usable reference (or for a role missing from it), players are ranked only against the current request, so scores depend on which matches were loaded.
- Players with an empty `teamPosition` are scored in the one role their team is missing (`scoring_positions()`); if that is ambiguous they get no score and the band `unscored`.
- `performanceBand` comes from the number the frontend shows (`floor(score + 0.5)`), not the raw percentile. Keep them in sync if the display rounding changes.
- The reference data in `src/ANALYSIS/data` is EUW ranked solo, 98% patch 16.13 (Mar–Jul 2026). Evaluation results hold for that population, not necessarily the live patch or other regions. Fresh ladder samples scored on it (`fetching_sample/analysis/fresh_analysis.py` and `sample_summary.py`, data in `fetching_sample/samples/`): EUW games on 16.20 average about 50, so no measurable patch drift; EUNE scores about 3 points low (47.2 in the 80-game pilot, 45.5 in the 10-game smoke run); KR may score high (53.9, from 10 games only).
- Get game length with `game_duration_minutes()`: matches saved before `gameDuration_sec` existed store `gameDuration_min` as minutes.seconds.
- Detect remakes with `is_remake()`; remakes are not scored.

## Rules

- Never report a metric without the exact command and its output.
- Before any evaluation, check that no match_id appears in both train and test.
- Ask before changing `PERFORMANCE_FEATURE_WEIGHTS`.
- Riot key currently used in this repo has a rate limit: 20 requests every 1 seconds, 100 requests every 2 minutes. keep that in mind while working.
