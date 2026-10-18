---
name: run-ola
description: Start, run and drive the OLA app (FastAPI backend + Vite/React frontend) on live Riot data. Use when asked to run or start OLA, smoke-test the API or performance scores, screenshot or check the profile/match pages, or confirm a backend/scoring change works in the real app.
---

Start the backend with uvicorn and drive it with `.claude/skills/run-ola/smoke.py` (API smoke test on live data). For the UI, start Vite and drive Chrome with the Claude in Chrome tools (`chromium-cli` is not installed here). Paths are relative to the repo root. The commands are Git Bash on Windows, except the PowerShell stop command.

## Prerequisites

- Python 3.12 with `src/BACKEND/requirements.txt` installed. Node 24 with `src/FRONTEND/node_modules` present.
- `.env` at the repo root with `RIOT_API_KEY=...`. It's a dotenv file, not a venv. Don't read it or commit it. Without it, every `/api/matches` call returns 500 "API Key not configured".

## Run (agent path)

Start the backend. It keeps running after the shell exits:

```bash
(cd src && PYTHONIOENCODING=utf-8 nohup python -m uvicorn BACKEND.main:app --host 127.0.0.1 --port 8000 > "${TMPDIR:-/tmp}/ola-backend.log" 2>&1 &)
timeout 60 bash -c 'until curl -sf http://127.0.0.1:8000/ >/dev/null; do sleep 1; done' && curl -s http://127.0.0.1:8000/
```

Smoke-test scoring on live data (≈1 Riot call per match):

```bash
PYTHONIOENCODING=utf-8 python .claude/skills/run-ola/smoke.py EUW1 401dmg 6969 --count 5
```

The script fetches `/api/matches` and checks every match:
- `gameDuration_sec`, `gameDuration_min` and the `gameDate` span agree;
- `metadata.isRemake` matches Riot's `gameEndedInEarlySurrender`;
- remakes are unscored and bands match the scores;
- every live score equals what the current code and `data/static/score_reference.json` give.

It prints `OK` and exits 0, or prints `FAIL ...` lines and exits 1. `--base http://127.0.0.1:5173` goes through the Vite proxy instead; `--out` sets where the raw JSON is saved (default: the temp dir, `ola_smoke.json`).

Start the frontend, proxied to the local backend:

```bash
(cd src/FRONTEND && VITE_PROXY_TARGET=http://127.0.0.1:8000 nohup npx vite --host 127.0.0.1 --port 5173 > "${TMPDIR:-/tmp}/ola-frontend.log" 2>&1 &)
timeout 60 bash -c 'until curl -sf http://127.0.0.1:5173 >/dev/null; do sleep 1; done' && curl -s -w "\nproxy %{http_code}\n" http://127.0.0.1:5173/api/rate-limit
```

Drive the UI with the Claude in Chrome tools: `tabs_context_mcp`, then `navigate` the tab to `http://127.0.0.1:5173/player/EUW/401dmg-6969`. Next, run with `javascript_tool`:

```js
for (let i = 0; i < 60 && !/SCORE/.test(document.body.innerText); i++) await new Promise(r => setTimeout(r, 500));
const t = document.body.innerText;
({ durations: [...t.matchAll(/(\d+:\d{2})\s*min/g)].map(m => m[1]),
   scores: [...t.matchAll(/SCORE\n(\S+)/g)].map(m => m[1]),
   remakes: (t.match(/REMAKE/g) || []).length,
   stats: t.match(/Score (Average|Median)\n[\d.]+/g) })
```

Open the first match from the profile (same tab) and read it. Then take a screenshot with `computer` and use `read_console_messages` (`onlyErrors: true`) to check for errors:

```js
[...document.querySelectorAll('span,i')].find(e => e.textContent.trim() === 'keyboard_arrow_right').click();
const read = () => { const t = document.body.innerText; return { url: location.pathname, duration: (t.match(/\d+:\d{2}/) || [])[0],
  damage: [...t.matchAll(/(\d+\.\dk)/g)].map(m => m[1]).filter((_, i) => i % 2 === 0),
  scores: [...t.matchAll(/\n(\d{1,3}|--)\nscore/gi)].map(m => m[1]) }; };
let r = read();
for (let i = 0; i < 40 && !(r.url.startsWith('/match/') && r.scores.length >= 10); i++) { await new Promise(res => setTimeout(res, 250)); r = read(); }
r
```

Compare against the saved smoke JSON. Displayed damage is `damagePerMinute × gameDuration_sec / 60` and should equal Riot's `totalDamageDealtToChampions`.

Stop both servers (PowerShell):

```powershell
foreach ($port in 8000, 5173) { Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -Confirm:$false; "stopped PID $_ on port $port" } }
```

Logs: `${TMPDIR:-/tmp}/ola-backend.log`, `${TMPDIR:-/tmp}/ola-frontend.log`.

## Test (no server, no Riot calls)

```bash
cd src
python -m unittest BACKEND.tests.test_scoring
python check_auc.py --seeds 0 1 2 3 4
```

The scoring tests should end with `OK`. `check_auc.py` should print `overlap=0` for every seed and an overall AUC around 0.78–0.79.

## Gotchas

- **Don't pipe the launch commands** (`| grep`, `| tee`, or a script run through a pipe). On Git Bash the background server inherits the pipe, so the pipeline never finishes and its output never appears. Run the launch blocks unpiped. They return as soon as the port answers.
- **The Vite proxy defaults to `http://backend:8000`** (the Docker service name), so set `VITE_PROXY_TARGET` when running locally. The backend's CORS only allows origins on port 5173.
- **The Riot dev-key budget is small.** `/api/rate-limit` reports `long_limit` 90. A 20-match profile costs about 22 calls, and after about 4 profiles the UI shows "RIOT API CAPACITY 90/90". Use `--count 5` for smoke runs, and wait about 2 minutes when the budget is spent.
- **The score reference is cached at startup** (`load_score_reference` uses `lru_cache`). After rebuilding `score_reference.json`, restart the backend. `smoke.py` catches a stale server as `FAIL ... live X != current code Y`.
- **A match page opened directly shows "Match data not found."** `/match/<id>` reads the in-memory API cache filled by the profile page, so load the profile in the same tab first.
- **The URL formats differ.** The profile route is `/player/<region without digits>/<name>-<tag>` (`/player/EUW/401dmg-6969`). The API takes `EUW1/401dmg/6969`.
- **Match rows have no link or button**, only a clickable container with a `keyboard_arrow_right` icon. Click the icon via JS as above. Its `click()` bubbles to React's handler.
- **`WARN ... score 40.0 shown with band low`** is a known, already-existing rounding issue. The band comes from the unrounded percentile (39.97), so it's a warning, not a failure.
- **Remakes are rare** (about 3% of games). 100 live games across 5 players had none, so the remake UI (grey "REMAKE", score `--`) needs a profile with a recent remake.

## Troubleshooting

- **`UnicodeEncodeError: 'charmap' codec can't encode characters`** when printing player names: the Windows console uses cp1250. Prefix the command with `PYTHONIOENCODING=utf-8`.
- **`RequestsDependencyWarning: urllib3 ... doesn't match a supported version`** on stderr: harmless noise from the installed `requests`.
