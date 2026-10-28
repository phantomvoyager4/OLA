### <metric>: <value>

- **Number:** value ± spread (mean ± sd over folds/seeds), n rows, share of positives
- **Where from:** exact command, commit or file, date; output saved in <file>
- **What it measures:** which metric, on which rows (which set, how many), positive class, threshold
- **Baseline:** same metric, same split, for a dummy model or the previous version
- **Does the evaluation match real use?** how the model will be used, and how the split copies that
- **Checks done:**
  - [ ] I ran the command myself and got the same number
  - [ ] no entity in both train and test (checked by: ...)
  - [ ] shuffled labels: score drops to about the baseline
  - [ ] no feature that exists only because of the label (leak)
  - [ ] spread over several seeds or folds, not one run
- **Limits:** what this number does not show; where it could break
