# OLA

Player-performance site for League of Legends ranked solo/duo (queue 420 only).

- `src/BACKEND`: Python 3.12 API and scoring (`model.py`)
- `src/FRONTEND`: React + Vite
- `src/ANALYSIS`: offline analysis; `data/` holds the collected matches the score reference is built from
- `data/static`: lookup tables and `score_reference.json`

Python runs on the system interpreter. `.env` is a dotenv file holding `RIOT_API_KEY`, not a virtualenv; don't read or commit it.

## Commands

- Tests: `cd src && python -m unittest BACKEND.tests.test_scoring`
- Score evaluation (held-out, split by match_id): `cd src && python check_auc.py --seeds 0 1 2 3 4`
- Rebuild score reference: `cd src && python -m BACKEND.metascripts.build_score_reference --data-dir ANALYSIS/data`
- Refresh lookup tables (run from repo root): `python src/BACKEND/metascripts/run_all_scripts.py`
- Frontend: `cd src/FRONTEND && npm run dev` / `npm run build` / `npm run lint`

## Scoring gotchas

- After changing a feature in `_extract_performance_features`, rebuild the score reference. It is only checked by feature names, so a stale one is used silently.
- Get game length with `game_duration_minutes()`: matches saved before `gameDuration_sec` existed store `gameDuration_min` as minutes.seconds.
- Detect remakes with `is_remake()`; remakes are not scored.

## Rules

- Never report a metric without the exact command and its output.
- Before any evaluation, check that no match_id appears in both train and test.
- Ask before changing `PERFORMANCE_FEATURE_WEIGHTS`.
