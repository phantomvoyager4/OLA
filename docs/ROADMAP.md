# OLA roadmap

Agreed 2026-10-28. Goal: a clean, publicly hosted prototype to send with a Riot production-key application, then a performance score that passes the tests in [ADR 0001](adr/0001-score-measures-contribution-not-result.md). Terms follow [GLOSSARY.md](../GLOSSARY.md).

Steps 1–4 must be finished before applying for the production key. Each step has a GitHub issue.

## 1. Cleanup

- [ ] Fix the 15 `npm run lint` errors (`Match.jsx`, `PlayerProfile.jsx`, `vite.config.js`), including the dead `handleDuoClick`.
- [ ] Response shape `{searched_player, ranked_entry, matches}`: the ranked entry is sent once, not copied onto all 10 participants, and the summary is no longer the last list element.
- [ ] Distinct errors instead of 404 for everything: 404 for an unknown Riot ID (hint: check it, or try the old name after a recent rename), 429/503 when the key budget is full, 502 when Riot fails. The frontend shows a message for each.
- [ ] Remove `save` from the public `/api/matches` route.
- [ ] Send the Riot key in the `X-Riot-Token` header, not as a query parameter.
- [ ] Rename caller to `searched_player` throughout.
- [ ] One platform table shared by the backend, the suggestion index and the ladder sampler, with exactly the 11 platforms in the glossary; the server picker offers only those (four options are broken today).
- [ ] Load lookup tables once at startup, not on every request.
- [ ] Heatmap days in the viewer's time zone, not the server's.
- [ ] Profile summary computed in the frontend from every loaded match, so "Show more" updates it; add Vitest with tests for it.
- [ ] `VITE_DEMO_MODE=true` hides `/login`, `/signup` and `/prediction` and their nav links; the pages stay in the code.

## 2. Postgres

- [ ] Postgres service in `docker-compose.yml`; SQLAlchemy with Alembic migrations.
- [ ] Match payloads stored as JSONB and kept indefinitely; a match in Postgres costs no Riot call.
- [ ] Search suggestions keyed by PUUID, keeping the latest Riot ID seen, so a rename replaces the old name; import `data/player_index.json` once.
- [ ] Scores computed on read, never stored, so a rebuilt reference applies at once.
- [ ] Unchanged: Riot ID → PUUID cached 24 h in memory; match ID lists, ranked entries and mastery keep their short in-memory caches; one in-process rate limiter.

## 3. Production setup

- [ ] `docker-compose.prod.yml`: Postgres with a named volume, the backend production image with exactly one uvicorn worker (the rate limiter is per process), Caddy serving the built frontend with HTTPS and proxying `/api`, and a migration step before the backend starts. `docker-compose.yml` stays the dev setup.
- [ ] Oracle Cloud Always Free Ampere VM (Ubuntu): ports 80/443 open in the security list and the VM's `iptables`, SSH by key only, Docker installed, `.env` only on the server.
- [ ] Domain: DuckDNS subdomain or a bought domain, A record to the VM; Caddy issues the certificate.
- [ ] Tier-list snapshot collected locally and shipped with the release; no collector on the server until the production key.

## 4. CI/CD

- [ ] On every push and pull request: backend scoring tests, sampler tests, `npm run lint`, Vitest, `npm run build`.
- [ ] On `main`: build arm64 images tagged with the commit SHA and push them to GHCR.
- [ ] Deploy over SSH: `docker compose pull`, migrate, `up -d`, then a health check on `/api/rate-limit`.
- [ ] Rollback by redeploying the previous SHA tag.

## 5. Production key

- [ ] Apply with the live link once steps 1–4 are done.
- [ ] Until it is approved, the development key on the server is replaced every 24 hours and the backend restarted.

## 6. Validation data and modules

- [ ] Ladder run on EUW1 and EUN1 with 10 games per player; project the time with `sample_summary.py` first; backend stopped while it runs.
- [ ] One documented module per test in `src/ANALYSIS/validation/` (predictive, rank, stability, leakage, win AUC), each filling `src/ANALYSIS/number_card.md` into `validation/cards/<test>_<score>.md`; `run_all.py` runs them for the current and a candidate score and prints pass/fail.
- [ ] Number cards for the current score.
- [ ] `validation/rank_mix.py`: ranked entries of all 10 participants for the first 300 games per platform, measured against the rule fixed in advance (every player within 1 tier of the game's average in most games). It produces a report; the grouping decision is made after reading it.

## 7. Score revision

- [ ] Candidate scores judged by the four tests in ADR 0001; win AUC reported for comparison only.
- [ ] Ask before changing `PERFORMANCE_FEATURE_WEIGHTS`.
