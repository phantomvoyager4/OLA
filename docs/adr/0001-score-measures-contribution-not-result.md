---
status: accepted
---

# The performance score measures contribution, not the game result

The performance score is meant to say how much a player contributed compared with others in the same role, as far as possible apart from whether their team won. The original weights were judged by how well the score separated wins from losses (ROC-AUC 0.790 on EUW ranked solo), but several features rise with winning regardless of the player (gold per minute, counted twice; objective damage; kill participation; survival), so a high win AUC partly rewards the score for tracking the result. Win AUC is therefore reported for comparison and never optimised for.

A change to the score is adopted only if it passes all of these, measured in separate modules under `src/ANALYSIS/validation/` that each fill in `src/ANALYSIS/number_card.md`, with the current score and a mean-KDA baseline alongside:

1. **Predictive validity**: a player's mean score over their first 5 games (in time order) correlates with their win rate over the next 5 (Spearman ρ across players); the 95% bootstrap lower bound is above 0 and the estimate is at least the KDA baseline's.
2. **Rank validity**: on a reference that mixes all ranks, tier correlates with a player's mean score (Spearman ρ); the 95% lower bound is above 0.
3. **Stability**: a player's scores agree across their own games (ICC); the 95% lower bound is above 0 and the estimate is at least the KDA baseline's.
4. **No leakage**: no evaluated game is in the reference used to score it, the later 5 games in test 1 never enter the reference, and with shuffled results test 1 averages within ±0.02 of 0 over 20 shuffles.

## Considered options

- **Keep win AUC as the target.** Rejected: it favours a score that tracks team outcome, which is not what a player looks at a per-game score to learn.
