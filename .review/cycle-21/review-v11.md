# Codex Review v11

## Verdict

BLOCKED

## Findings

### ISSUE-13 [MEDIUM] ISSUE-12 regression tests do not exercise the broken Studio selector

- Location: `tests/test_cycle21.py:1975-2011`, `scripts/static/studio.js:300-323`
- Analysis: The production fix in `loadAppCards()` correctly changes the selector to read the
  `/api/cards` JSON array. However, both new tests interact only with Flask endpoints:
  one asserts that `/api/cards` returns a live card, and the other submits that ID directly
  to `/api/studio/application-preview`. Neither executes or inspects `loadAppCards()`.
  Therefore the tests would still pass with the original buggy JavaScript expression
  `(data.cards || [])`, while the UI would again display a false empty state.
- Impact: Amendment v4 requires automated regression coverage for the selector failure. The
  current suite verifies backend prerequisites, not the user-visible integration that failed.
- Fix direction: Add coverage that fails when `loadAppCards()` reads `data.cards` instead of
  the array response. Follow the repository's existing UI-test style at minimum by asserting
  the Studio JS array-consumption contract and retained live filtering/empty state; use an
  executable DOM/fetch JavaScript test if the current toolchain supports it without expanding
  scope.

## Previous Issue Status

- ISSUE-1 through ISSUE-11: RESOLVED - unchanged from prior reviews.
- ISSUE-12: PARTIALLY RESOLVED - production JavaScript fix is correct, but the required
  regression test does not yet protect that fix.

## Regression Check

No functional regression identified in the ISSUE-12 code change itself. Coverage is
insufficient to prevent reintroduction of the same Studio integration failure.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Application Writing consumes live cards from the existing array API response | PASS | `scripts/static/studio.js` now uses `Array.isArray(data) ? data : []`. |
| Regression coverage catches the previously broken selector contract | FAIL | New tests do not read or execute `loadAppCards()`. |
| Amendment v3 blind-hiring boundary and documentation | PASS | Not affected by ISSUE-12 changes. |

## Automatic Checks

- Not rerun for this review: the blocker is that the submitted tests cannot fail on the
  reviewed UI regression. Executor must rerun the full required checks after adding effective
  coverage.

## Changes Outside Plan

No new product scope identified. ISSUE-13 is completion of Amendment v4's required regression
coverage for ISSUE-12.

---

## RESOLVED

### Issue Classification
- ISSUE-13: APPLY

### Applied

RESOLVED: ISSUE-13 — Added source-inspection regression tests that fail when `loadAppCards()` reads `data.cards`
- `tests/test_cycle21.py`: added two tests using the existing `client.get("/static/studio.js")` + `assert b"..." in rv.data` style (no new tooling):
  - `test_studio_js_uses_array_guard`: asserts `Array.isArray(data)`, `status === "live"` filter, and `No live cards found` empty-state text are all present in the JS source. Fails if the array-consumption contract or preserved behaviors are removed.
  - `test_studio_js_no_data_cards_access`: asserts `data.cards` is absent from the JS source. Fails if the buggy `(data.cards || [])` expression is reintroduced.
- Regression guard confirmed by simulation: reverting the fix would cause `data.cards` to appear and `Array.isArray(data)` to disappear, triggering both tests.

자동 체크: pytest ✅ 470 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
