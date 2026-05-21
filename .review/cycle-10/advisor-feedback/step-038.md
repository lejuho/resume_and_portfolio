# Step 038 — Cycle-10 Review-v1 BLOCKED Fixes Completion check

Cycle: 10
Pass: 2
Files Changed: scripts/dashboard.py, scripts/static/dashboard.js, scripts/templates/dashboard.html, tests/test_dashboard.py

## Advisor Verdict
OK

## Advisor Feedback
1. Concern 1 (incoming_fields scope) — VALID, behavior correct. Guard keys on incoming_fields (request payload), not merged dict. Title-only PUT has no "visuals" key, so pre-existing cards with broken visual paths are not blocked. Correct intended scope.
2. Concern 2 (af-body-field hidden breaks create) — No break. POST/create branch never reads af-body.value; only PUT/edit branch does. openNew() also clears af-body to ''. Hiding #af-body-field does not affect the create submit path.
3. Minor note: GET /api/cards/{id} visual_hints already exposes path validity — consistent with new PUT 422 guard.
4. No regressions found; both fixes are sound.

## Sonnet Response
- Both concerns cleared. No additional changes needed.
- 195 tests pass, ruff clean.
