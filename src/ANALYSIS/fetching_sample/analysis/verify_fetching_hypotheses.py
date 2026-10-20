"""Check data-quality hypotheses about src/ANALYSIS/fetching_sample/fetching_script.py.

Uses only the saved crawl output in src/ANALYSIS/data and the EUW sampling
plan in its spreadsheet. Makes no Riot API calls.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/verify_fetching_hypotheses.py
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from BACKEND import model
from check_auc import build_reference, score_matches, split_matches

with contextlib.redirect_stdout(io.StringIO()):
    import fetching_script  # module level loads the API key; nothing is called

DATA = Path("ANALYSIS/data")
SHEET = DATA / "LoL Rank Distribution via DPM.LOL.xlsx"
ROLES = model.ROLES
TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
rng = np.random.default_rng(0)


def load():
    files, matches, first_file, copies = {}, {}, {}, Counter()
    for path in sorted(DATA.glob("data_full_*.json")):
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload.values() if isinstance(payload, dict) else payload
        files[path.name] = [m["match_id"] for m in items if isinstance(m, dict) and "players" in m]
        for m in items:
            if isinstance(m, dict) and "players" in m:
                matches[m["match_id"]] = m
                first_file.setdefault(m["match_id"], path.name)
                copies[m["match_id"]] += 1
    return files, matches, first_file, copies


def caller_tier(match):
    caller = next((p for p in match["players"] if p.get("caller")), match["players"][0])
    return (caller.get("metadata") or {}).get("tier")


def patch(match):
    return ".".join(str(match["metadata"].get("gameVersion")).split(".")[:2])


def weighted_reference(matches, weight_of):
    """Role reference where every match counts with weight_of(match)."""
    names = list(model.PERFORMANCE_FEATURE_WEIGHTS)
    w_feat = np.array(list(model.PERFORMANCE_FEATURE_WEIGHTS.values()))
    rows = {role: ([], []) for role in ROLES}
    for m in matches:
        if model.is_remake(m):
            continue
        minutes = model.game_duration_minutes(m["metadata"])
        for p in m["players"]:
            if p.get("teamPosition") in ROLES:
                f = model._extract_performance_features(p, minutes)
                rows[p["teamPosition"]][0].append([f[n] for n in names])
                rows[p["teamPosition"]][1].append(weight_of(m))
    roles = {}
    for role, (x, w) in rows.items():
        x, w = np.array(x), np.array(w, dtype=float)
        mean = (w[:, None] * x).sum(0) / w.sum()
        std = np.sqrt((w[:, None] * (x - mean) ** 2).sum(0) / w.sum())
        std[std == 0] = 1.0
        raw = ((x - mean) / std) @ w_feat
        order = np.argsort(raw)
        cum = np.cumsum(w[order]) / w.sum()
        index = np.clip(np.searchsorted(cum, np.arange(101) / 100), 0, len(raw) - 1)
        roles[role] = {"count": len(raw), "mean": dict(zip(names, mean)), "std": dict(zip(names, std)),
                       "quantiles": [float(v) for v in raw[order][index]]}
    return {"features": names, "roles": roles}


def main() -> None:
    files, matches, first_file, copies = load()
    playable = {mid: m for mid, m in matches.items() if not model.is_remake(m)}
    file_tier = {name: re.match(r"data_full_[^_]+_([A-Z]+)_", name).group(1) for name in files}
    print(f"files={len(files)} records={sum(copies.values())} unique matches={len(matches)} playable={len(playable)}")

    # H1 snowball clustering ------------------------------------------------
    print("\nH1 clustering")
    by_file = defaultdict(list)
    for mid in playable:
        by_file[first_file[mid]].append(mid)
    spans, busiest = [], []
    for ids in by_file.values():
        days = sorted(date.fromisoformat(playable[i]["metadata"]["gameDateDay"]) for i in ids)
        spans.append((days[-1] - days[0]).days)
        busiest.append(sum(n for _, n in Counter(days).most_common(3)) / len(days))
    all_days = sorted(date.fromisoformat(m["metadata"]["gameDateDay"]) for m in playable.values())
    print(f"  date span per file: median {np.median(spans):.0f} days, max {max(spans)}; share of a file's games on its 3 busiest days: "
          f"median {np.median(busiest):.0%}; whole dataset spans {(all_days[-1] - all_days[0]).days} days")

    puuid_games = defaultdict(set)
    for mid, m in playable.items():
        for p in m["players"]:
            puuid_games[p["puuid"]].add(mid)
    shared = set()
    for mids in puuid_games.values():
        mids = sorted(mids)
        shared.update((a, b) for i, a in enumerate(mids) for b in mids[i + 1:])
    sizes = Counter(first_file[mid] for mid in playable)
    tier_sizes = Counter(file_tier[first_file[mid]] for mid in playable)
    pairs_same_file = sum(n * (n - 1) // 2 for n in sizes.values())
    pairs_same_tier_other = sum(n * (n - 1) // 2 for n in tier_sizes.values()) - pairs_same_file
    hits_same_file = sum(first_file[a] == first_file[b] for a, b in shared)
    hits_other = sum(first_file[a] != first_file[b] and file_tier[first_file[a]] == file_tier[first_file[b]] for a, b in shared)
    print(f"  match pairs sharing a player: same file {hits_same_file}/{pairs_same_file} ({hits_same_file / pairs_same_file:.3%}), "
          f"other file same tier {hits_other}/{pairs_same_tier_other} ({hits_other / pairs_same_tier_other:.3%})")

    mids = list(playable)
    labels = np.array([first_file[mid] for mid in mids])
    tiers = np.array([file_tier[first_file[mid]] for mid in mids])
    variables = {
        "game length": np.array([model.game_duration_minutes(playable[mid]["metadata"]) for mid in mids]),
        "match mean CS/min": np.array([np.mean([model._coerce_float(p.get("cs_min")) for p in playable[mid]["players"]]) for mid in mids]),
        "match mean damage/min": np.array([np.mean([model._coerce_float(p.get("damagePerMinute")) for p in playable[mid]["players"]]) for mid in mids]),
    }
    file_names = sorted(set(labels))
    n_files, n_tiers, n = len(file_names), len(set(tiers)), len(mids)
    m0 = (n - sum(c * c for c in Counter(labels).values()) / n) / (n_files - 1)

    def msb(values, file_labels):
        resid = values - np.array([values[tiers == t].mean() for t in tiers])
        means = {f: resid[file_labels == f].mean() for f in file_names}
        return sum((file_labels == f).sum() * means[f] ** 2 for f in file_names) / (n_files - n_tiers), resid, means

    for name, values in variables.items():
        observed, resid, means = msb(values, labels)
        msw = sum(((resid[labels == f] - means[f]) ** 2).sum() for f in file_names) / (n - n_files)
        icc = max(0.0, (observed - msw) / (observed + (m0 - 1) * msw))
        permuted = []
        for _ in range(2000):
            shuffled = labels.copy()
            for t in set(tiers):
                idx = np.flatnonzero(tiers == t)
                shuffled[idx] = rng.permutation(labels[idx])
            permuted.append(msb(values, shuffled)[0])
        p_value = (np.sum(np.array(permuted) >= observed) + 1) / (len(permuted) + 1)
        deff = 1 + (n / n_files - 1) * icc
        print(f"  {name:<22} between-file variance (tier removed) p={p_value:.4f}, ICC={icc:.3f}, "
              f"design effect={deff:.1f}, effective matches={n / deff:.0f} of {n}")

    # H2 stratified by players, not games --------------------------------------
    print("\nH2 stratification unit")
    sheet = pd.read_excel(SHEET, sheet_name="EUW")
    ranks = sheet[sheet["Rank"] != "Total"].copy()
    ranks["games"] = pd.to_numeric(ranks["Players_int"]) * pd.to_numeric(ranks["Avg Games"], errors="coerce")
    players = ranks.groupby(ranks["Tier"].str.upper())["Players_int"].sum()
    games = ranks.groupby(ranks["Tier"].str.upper())["games"].sum()
    plan = dict(zip(sheet.iloc[8:18]["Unnamed: 13"].str.upper(), sheet.iloc[8:18]["Unnamed: 16"]))
    actual = Counter(caller_tier(m) for m in playable.values())
    print(f"  {'tier':<12}{'plan':>6}{'actual':>8}{'players %':>11}{'games %':>9}{'actual %':>10}")
    for tier in TIERS:
        print(f"  {tier:<12}{plan[tier]:>6}{actual[tier]:>8}{players[tier] / players.sum():>10.1%}{games[tier] / games.sum():>9.1%}{actual[tier] / len(playable):>10.1%}")

    train, test = split_matches(list(playable.values()), 0.3, 0)
    overlap = {m["match_id"] for m in train} & {m["match_id"] for m in test}
    train_share = Counter(caller_tier(m) for m in train)
    game_share = games / games.sum()
    by_players = weighted_reference(train, lambda m: 1.0)
    by_games = weighted_reference(train, lambda m: game_share[caller_tier(m)] / (train_share[caller_tier(m)] / len(train)))
    s_players, wins, roles = score_matches(test, by_players)
    s_games, _, _ = score_matches(test, by_games)
    test_tiers = np.array([caller_tier(m) for m in test for p in m["players"] if p.get("teamPosition") in ROLES and not model.is_remake(m)])
    shown = lambda s: np.array([model._performance_band(math.floor(v + 0.5)) for v in s])
    print(f"  seed 0 overlap={len(overlap)}: game-weighted vs player-weighted reference on {len(s_players)} test players: "
          f"mean |d|={np.abs(s_games - s_players).mean():.2f}, band changed {np.mean(shown(s_games) != shown(s_players)):.1%}, "
          f"AUC {roc_auc_score(wins, s_players):.4f} -> {roc_auc_score(wins, s_games):.4f}")
    print("  mean signed change by tier of the lobby: " + " ".join(
        f"{t[:4]}={np.mean((s_games - s_players)[test_tiers == t]):+.1f}" for t in TIERS if (test_tiers == t).sum() >= 20))

    # H3 per-player rank lost ---------------------------------------------------
    print("\nH3 per-player rank")
    identical = sum(len({json.dumps(p.get("metadata"), sort_keys=True) for p in m["players"]}) == 1 for m in matches.values())
    named = sum("#" in p.get("username", "") for m in matches.values() for p in m["players"])
    passed = sum(len(fetching_script.names_fetcher([m], target_tier=caller_tier(m))) for m in matches.values())
    print(f"  matches whose 10 players carry identical rank metadata: {identical}/{len(matches)}")
    print(f"  players passing names_fetcher's tier filter: {passed}/{named}")

    # H4 patch and time control ----------------------------------------------
    print("\nH4 patch and time")
    with open("../data/static/runes_lookup_table.json", encoding="utf-8") as handle:
        live = json.load(handle)["patch"]
    patches = Counter(patch(m) for m in playable.values())
    stale = 0
    for ids in by_file.values():
        newest = max(date.fromisoformat(playable[i]["metadata"]["gameDateDay"]) for i in ids)
        stale += sum((newest - date.fromisoformat(playable[i]["metadata"]["gameDateDay"])).days > 14 for i in ids)
    mixed_files = sum(len({patch(playable[i]) for i in ids}) > 1 for ids in by_file.values())
    print(f"  live patch (static tables)={live}; dataset patches={dict(sorted(patches.items()))}")
    print(f"  games >14 days older than their file's newest game: {stale}; files mixing patches: {mixed_files}/{len(by_file)}")

    # H5 region ------------------------------------------------------------------
    print("\nH5 region")
    servers = pd.read_excel(SHEET, sheet_name="Server_sampling")
    print(f"  platforms in data: {dict(Counter(m['metadata'].get('platformId') for m in matches.values()))}")
    print("  planned subsample per server: " + ", ".join(f"{s}={n}" for s, n in zip(servers['Server'], servers['Players subsample size (N=10000)'])))

    # H6 lossy storage -------------------------------------------------------
    print("\nH6 stored fields")
    rows = [p for m in matches.values() for p in m["players"]]
    legacy = [m["metadata"]["gameDuration_min"] for m in matches.values() if "gameDuration_sec" not in m["metadata"]]
    impossible = sum(round((v - math.floor(v)) * 100) >= 60 for v in legacy)
    print(f"  matches with gameDuration_sec: {sum('gameDuration_sec' in m['metadata'] for m in matches.values())}/{len(matches)}; "
          f"legacy minutes.seconds values with seconds >= 60: {impossible}/{len(legacy)}")
    for field in ("individualPosition", "challenges", "damageDealtToBuildings", "teamEarlySurrendered", "gameEndedInEarlySurrender"):
        print(f"  players with {field}: {sum(field in p for p in rows)}/{len(rows)}")
    print(f"  teamDamagePercentage stored as text: {sum(isinstance(p.get('teamDamagePercentage'), str) for p in rows)}/{len(rows)}")

    # H7 sample size ---------------------------------------------------------
    print("\nH7 sample size")
    reference = model.load_score_reference()
    print("  reference rows per role: " + " ".join(f"{r}={reference['roles'][r]['count']}" for r in ROLES)
          + f"; Master+ matches={sum(actual[t] for t in TIERS[7:])}")
    for seed in (0, 1, 2):
        rest, held = split_matches(list(playable.values()), 0.2, seed)
        half_a, half_b = split_matches(rest, 0.5, seed)
        overlap = {m["match_id"] for m in half_a} & {m["match_id"] for m in half_b} | ({m["match_id"] for m in rest} & {m["match_id"] for m in held})
        a, _, _ = score_matches(held, build_reference(half_a))
        b, _, _ = score_matches(held, build_reference(half_b))
        per_reference = np.abs(a - b).mean() / math.sqrt(2)
        print(f"  seed {seed} overlap={len(overlap)}: two references from disjoint halves ({len(half_a)}, {len(half_b)} matches) "
              f"disagree by {np.abs(a - b).mean():.2f} points on {len(a)} held-out players; noise of one full-size reference ~"
              f"{per_reference * math.sqrt(len(half_a) / len(playable)):.2f}")

    # H8 repeated players ------------------------------------------------------
    print("\nH8 repeated players")
    appearances = Counter(p["puuid"] for m in playable.values() for p in m["players"])
    total = sum(appearances.values())
    repeated = sum(c for c in appearances.values() if c >= 2)
    print(f"  player rows={total}, distinct players={len(appearances)}, rows from players seen 2+ times={repeated / total:.1%}, "
          f"max appearances={max(appearances.values())}, players seen 5+ times={sum(c >= 5 for c in appearances.values())}")

    # H9 crawled players vs their lobby-mates ------------------------------------
    print("\nH9 crawled players vs lobby-mates (saved reference)")
    scored = model.annotate_player_performance([json.loads(json.dumps(m)) for m in playable.values()])
    groups = {True: [], False: []}
    for m in scored:
        for p in m["players"]:
            if p.get("performanceScore") is not None and p.get("teamPosition") in ROLES:
                groups[bool(p.get("caller"))].append((p["performanceScore"], bool(p.get("win")), model._coerce_float(p.get("summonerLevel"))))
    for flag, label in ((True, "crawled"), (False, "lobby-mates")):
        values = np.array(groups[flag])
        print(f"  {label:<12} n={len(values):>5} mean score={values[:, 0].mean():5.1f} win rate={values[:, 1].mean():.1%} mean level={values[:, 2].mean():6.1f}")
    crawled = np.array(groups[True])
    boot = [crawled[rng.integers(0, len(crawled), len(crawled)), 0].mean() for _ in range(2000)]
    print(f"  crawled mean score 95% interval [{np.percentile(boot, 2.5):.1f}, {np.percentile(boot, 97.5):.1f}]")

    # H10 duplicates and remakes ------------------------------------------------
    print("\nH10 duplicates and remakes")
    print(f"  extra copies across files={sum(copies.values()) - len(copies)}, remakes stored={len(matches) - len(playable)}")

    # H11 reproducibility ------------------------------------------------------
    print("\nH11 file names vs content")
    off = [(name, int(re.search(r"_(\d+)_\d+\.json$", name).group(1)), len(ids)) for name, ids in files.items()]
    short = [(n, t, c) for n, t, c in off if c != t]
    print(f"  files whose match count differs from the size in their name: {len(short)}/{len(files)}: "
          + ", ".join(f"{n.replace('data_full_EUW1_', '').replace('.json', '')}={c}" for n, t, c in short))


if __name__ == "__main__":
    main()
