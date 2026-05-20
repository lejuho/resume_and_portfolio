# Step 027 — Cycle-7 Dashboard MVP Completion check

Cycle: 7
Pass: 1
Files Changed: scripts/dashboard.py, scripts/templates/dashboard.html, scripts/pcli.py, tests/test_dashboard.py, pyproject.toml

## Advisor Verdict
OK

## Advisor Feedback
1. Verify Flask deferred import — confirm `from scripts.dashboard import run_server` is inside cmd_dashboard(), not module top. ✓ Confirmed.
2. Confirm scripts/templates/ ignored — ruff only processes .py files, pytest only collects test_*.py. ✓ Safe.
3. Align defaults — /api/cards was defaulting to status="live" while index showed all cards. Fix: change default to status=None (all cards). ✓ Fixed.
4. Run uv run pcli --help to confirm non-dashboard commands import without Flask. ✓ Passes.

## Sonnet Response
- 확인 (1): pcli.py line 798 — import is inside cmd_dashboard().
- 확인 (2): ruff check scripts tests templates — html files skipped automatically.
- 적용 (3): /api/cards status default → None. test_cards_endpoint_returns_sample_id 쿼리에 ?status=live 명시.
- 확인 (4): uv run pcli --help — Flask 없이 정상 동작.
- 148/148 tests pass, ruff clean. Committed.
