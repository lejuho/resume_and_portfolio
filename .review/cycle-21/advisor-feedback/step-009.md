# Advisor Feedback: Cycle 21 Step-009 — review-v11 ISSUE-13

Type: Approach check + Completion check
Scope: tests/test_cycle21.py
Plan baseline: Escalation Amendment v4 (plan.md) — ISSUE-12 regression coverage

## Approach Check (before implementation)

Query: test design — source inspection style vs executable DOM; positive vs negative assertions;
single vs split test functions.

Key guidance received:
1. Negative assertion (assert `data.cards` absent) is acceptable — it is the load-bearing guard
   against regression reintroduction.
2. Split into two functions: one for positive contract (`Array.isArray`, `status === "live"`,
   empty-state text), one for negative guard (`data.cards` absent). Keeps failure signals
   distinct.
3. Names: `test_studio_js_uses_array_guard` and `test_studio_js_no_data_cards_access`.
4. No new tooling — use `client.get("/static/studio.js")` + `assert b"..." in rv.data` style,
   matching the existing `test_studio_js_has_app_functions` and sibling tests.

Decision: Applied all four guidance points.

## Completion Check (after implementation)

Changes:
- `tests/test_cycle21.py` — added two tests in the ISSUE-12 section:
  - `test_studio_js_uses_array_guard`: GET /static/studio.js; asserts `b"Array.isArray(data)"`,
    `b'status === "live"'`, and `b"No live cards found"` all present. Fails if the fix reverts
    or filter/empty-state behavior is stripped.
  - `test_studio_js_no_data_cards_access`: GET /static/studio.js; asserts `b"data.cards"` NOT
    in source. Fails if the buggy `data.cards || []` expression is reintroduced.

Regression guard verified: simulated reversion (`Array.isArray(data) ? data : []` → `data.cards || []`) confirms `data.cards` would appear in source and `Array.isArray(data)` would be absent — both tests would fail as required.

No code changes outside test file. JS fix from step-008 is unchanged.

## Decision

PROCEED. 470 tests pass (468 → +2 ISSUE-13 source-inspection tests). All checks green.

Auto checks: pytest ✅ 470 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
