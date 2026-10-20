"""Can info.gameVersion validate that a game is on the current patch?

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/gameversion_check.py ANALYSIS/fetching_sample/samples/pilot_2026-10-20
"""
import glob, json, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
import requests
from BACKEND.metascripts.build_score_reference import load_matches
from BACKEND.tier_list_fetcher import data_patch_line, patch_line
from check_auc import DATA_DIR

sp = sys.argv[1]
FULL = re.compile(r"^\d+\.\d+\.\d+\.\d+$")

def line_key(v):
    a, b = patch_line(v).split("."); return int(a), int(b)

print("== 1. format ==")
raw = {}
for f in sorted(glob.glob(f"{sp}/raw_*.json")):
    raw.update(json.load(open(f)))
old = load_matches(DATA_DIR)
sources = {"fresh raw (3 regions)": [p["info"]["gameVersion"] for p in raw.values()],
           "stored crawl (EUW)": [m["metadata"]["gameVersion"] for m in old]}
for label, versions in sources.items():
    bad = [v for v in versions if not FULL.match(str(v))]
    print(f"  {label}: {len(versions)} games, 4-part numeric {len(versions) - len(bad)}/{len(versions)}, examples {Counter(versions).most_common(2)}")
per_line = defaultdict(set)
for v in sources["fresh raw (3 regions)"] + sources["stored crawl (EUW)"]:
    per_line[patch_line(v)].add(v)
multi = {k: sorted(v) for k, v in per_line.items() if len(v) > 1}
print(f"  patch lines with more than one build: {len(multi)}/{len(per_line)}; e.g. {dict(list(multi.items())[:3])}")

print("\n== 2. Data Dragon realms vs newest in-game version per region ==")
realm_of = {"EUW1": "euw", "EUN1": "eune", "NA1": "na", "BR1": "br", "KR": "kr"}
newest = defaultdict(lambda: (0, None))
for p in raw.values():
    info = p["info"]; plat = info["platformId"]
    if info["gameStartTimestamp"] > newest[plat][0]:
        newest[plat] = (info["gameStartTimestamp"], info["gameVersion"])
versions_json = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=15).json()[:3]
print(f"  ddragon versions.json head: {versions_json}")
for plat, realm in realm_of.items():
    r = requests.get(f"https://ddragon.leagueoflegends.com/realms/{realm}.json", timeout=15).json()
    ts, v = newest[plat]
    seen = f"newest sampled game {v} ({datetime.fromtimestamp(ts/1000, timezone.utc):%Y-%m-%d})" if v else "no sampled games"
    print(f"  {plat}: realm v={r.get('v')} -> line {data_patch_line(r['v'])}; {seen}")

print("\n== 3. does the version change once per region, with no overlap in time? ==")
def check(rows, label):
    by_plat = defaultdict(list)
    for plat, ts, v in rows:
        by_plat[plat].append((ts, line_key(v)))
    for plat, items in sorted(by_plat.items()):
        items.sort()
        inversions = sum(1 for (t1, l1), (t2, l2) in zip(items, items[1:]) if l2 < l1)
        span = defaultdict(lambda: [float("inf"), 0])
        for ts, l in items:
            span[l][0] = min(span[l][0], ts); span[l][1] = max(span[l][1], ts)
        lines = sorted(span)
        overlaps = [(a, b) for a, b in zip(lines, lines[1:]) if span[b][0] < span[a][1]]
        print(f"  {label} {plat}: {len(items)} games, {len(lines)} patch lines, older-version-after-newer steps {inversions}, overlapping line pairs {overlaps}")
check([(p["info"]["platformId"], p["info"]["gameStartTimestamp"], p["info"]["gameVersion"]) for p in raw.values()], "fresh")
def ts_of(m):
    return datetime.strptime(m["metadata"]["gameDate"][:19], "%Y-%m-%d %H:%M:%S").timestamp() * 1000
check([(m["metadata"]["platformId"], ts_of(m), m["metadata"]["gameVersion"]) for m in old], "stored")

print("\n== 4. boundary between 16.19 and 16.20 per region (fresh) ==")
for plat in ("EUW1", "EUN1", "NA1"):
    g = [(p["info"]["gameStartTimestamp"], patch_line(p["info"]["gameVersion"])) for p in raw.values() if p["info"]["platformId"] == plat]
    last19 = max((t for t, l in g if l == "16.19"), default=None); first20 = min((t for t, l in g if l == "16.20"), default=None)
    f = lambda t: datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if t else "-"
    print(f"  {plat}: last 16.19 game {f(last19)}, first 16.20 game {f(first20)}")
print("\n== 5. other fields that confirm a usable ranked game ==")
print("  endOfGameResult:", Counter(p["info"].get("endOfGameResult") for p in raw.values()))
print("  queueId:", Counter(p["info"].get("queueId") for p in raw.values()), " participants:", Counter(len(p["info"]["participants"]) for p in raw.values()))
print("  early-surrender flag set (remake):", sum(any(x.get("gameEndedInEarlySurrender") for x in p["info"]["participants"]) for p in raw.values()))
