"""AUC on held-out rows split by whether the account also appears in train.

Run from src:
    PYTHONPATH=.:ANALYSIS/fetching_sample:ANALYSIS/fetching_sample/analysis python ANALYSIS/fetching_sample/analysis/leak_auc.py
"""
import copy
import numpy as np
from sklearn.metrics import roc_auc_score
from BACKEND import model
from BACKEND.metascripts.build_score_reference import ROLES, load_matches
from check_auc import DATA_DIR, build_reference, split_matches

matches = load_matches(DATA_DIR)
for seed in range(5):
    train, test = split_matches(matches, 0.3, seed)
    assert not ({m["match_id"] for m in train} & {m["match_id"] for m in test})
    train_ids = {p.get("puuid") for m in train for p in m["players"]}
    ref = build_reference(train)
    playable = [copy.deepcopy(m) for m in test if not model.is_remake(m)]
    model.load_score_reference = lambda: ref
    model.annotate_player_performance(playable)
    rows = [(p["performanceScore"], int(bool(p["win"])), p.get("puuid") in train_ids)
            for m in playable for p in m["players"] if p.get("teamPosition") in ROLES]
    s, w, shared = map(np.array, zip(*rows))
    print(f"seed {seed} overlap=0: all {roc_auc_score(w, s):.4f} (n={len(s)})  "
          f"shared accounts {roc_auc_score(w[shared], s[shared]):.4f} (n={shared.sum()})  "
          f"unseen accounts {roc_auc_score(w[~shared], s[~shared]):.4f} (n={(~shared).sum()})")
