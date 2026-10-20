"""Audit the scoring inputs stored in the crawl against what today's Player computes.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/input_audit.py
"""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from BACKEND.metascripts.build_score_reference import load_matches
from BACKEND.model import game_duration_minutes, is_remake

KEYS = ["kills","deaths","assists","KDA","killParticipation","damagePerMinute","goldPerMinute",
        "visionScorePerMinute","wardsPlaced","cs_min","totalMinionsKilled","totalJungleMinionsKilled",
        "damageDealtToObjectives","timeCCingOthers","soloKills","teamDamagePercentage","totalTimeSpentDead",
        "teamPosition","gameEndedInEarlySurrender"]
matches = load_matches(Path("ANALYSIS/data"))
rows = [p for m in matches if not is_remake(m) for p in m["players"]]
print(f"unique matches={len(matches)} non-remake player rows={len(rows)}")
for k in KEYS:
    present = [p[k] for p in rows if k in p]
    types = Counter(type(v).__name__ for v in present)
    zeros = sum(1 for v in present if v in (0, 0.0, "0", "0.0%"))
    print(f"  {k:26s} present {len(present):6d}/{len(rows)}  types={dict(types)}  zero={zeros}")

# cs_min: stored value vs recomputed from totals and the real game length
bad = 0; diffs = []
for m in matches:
    if is_remake(m): continue
    dur = game_duration_minutes(m.get("metadata") or {})
    for p in m["players"]:
        if "cs_min" not in p: continue
        cs = int(p.get("totalMinionsKilled",0)) + int(p.get("totalJungleMinionsKilled", p.get("neutralMinionsKilled",0)))
        d = p["cs_min"] - round(cs/dur, 1)
        diffs.append(d)
        bad += abs(d) > 0.051
print(f"cs_min stored vs recomputed with game_duration_minutes: mismatches>0.05 {bad}/{len(diffs)}, mean diff {sum(diffs)/len(diffs):+.3f}")
md = Counter(tuple(sorted((m.get('metadata') or {}).keys())) for m in matches)
print("metadata key sets:", [ (len(k), n) for k,n in md.most_common(5)])
print("metadata keys example:", sorted((matches[0].get('metadata') or {}).keys()))
print("player keys example count:", len(matches[0]['players'][0]))
