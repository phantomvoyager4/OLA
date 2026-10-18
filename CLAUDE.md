# OLA

Python 3.12, Backend in src/BACKEND.

- Tests: cd src && python -m unittest BACKEND.tests.test_scoring.
- Score evaluation: cd src && python check_auc.py.
- Evaluation of players only in ranked solo/duo.

Rules:

- Never report a metric without the exact command and its output.
- Before any evaluation, check that no match_id appears in both train and test.
- Ask before changing PERFORMANCE_FEATURE_WEIGHTS.
