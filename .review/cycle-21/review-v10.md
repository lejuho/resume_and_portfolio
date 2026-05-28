# Codex Review v10

## Verdict

BLOCKED

## Findings

### ISSUE-12 [HIGH] Application Writing live-card selector reads the wrong `/api/cards` response shape

- Location: `scripts/static/studio.js:304-313`, `scripts/dashboard.py:152-168`
- Analysis: `GET /api/cards` returns a JSON array of card objects, but `loadAppCards()`
  reads `data.cards || []`. Because the array has no `cards` property, the selector always
  receives an empty list and renders "No live cards found. Mark cards as Live in Dashboard
  first." even when validated live cards exist.
- Impact: Application Writing cannot be used from Studio because users cannot select any
  live evidence card, despite valid live cards being available through the existing API.
- Fix direction: Preserve the existing `/api/cards` array response contract and update
  `loadAppCards()` to consume that array while retaining `status === "live"` filtering and
  the existing empty/error display behavior. Add an automated regression test covering the
  Studio selector contract when `/api/cards` supplies a live card.

## Previous Issue Status

- ISSUE-1 through ISSUE-11: RESOLVED - no regression in the previously reviewed
  Application Writing boundary behavior is identified by this finding.

## Regression Check

This is a newly identified merge-blocking UI integration regression: the backend exposes
live cards, but the Studio Application Writing selector consumes an incompatible response
shape.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Application Writing can select approved live evidence cards | FAIL | ISSUE-12: selector renders empty list against the existing API array response. |
| Amendment v3 blind-hiring boundary and advisory sanitization | PASS | Prior v9 review remains valid; not changed by this finding. |
| Documentation alignment for Amendment v3 | PASS | Prior v9 review remains valid; not changed by this finding. |

## Automatic Checks

- Not rerun for this review: defect is demonstrated directly by the incompatible response
  shapes in `scripts/dashboard.py` and `scripts/static/studio.js`.
- Executor must run relevant regression coverage and the full required check set after the
  fix.

## Changes Outside Plan

No new product scope. ISSUE-12 is a merge-blocking regression in the Cycle 21 Application
Writing UI flow.

---

## RESOLVED

### Issue Classification
- ISSUE-12: APPLY

### Applied

RESOLVED: ISSUE-12 — Fixed `loadAppCards()` to consume the `/api/cards` JSON array response
- `scripts/static/studio.js:306`: replaced `(data.cards || [])` with `(Array.isArray(data) ? data : [])`. The `/api/cards` endpoint returns a bare JSON array; the previous `.cards` property lookup always resolved to `undefined`, producing a permanent false empty state. `status === "live"` filter, empty-state render, and request-error display are preserved unchanged.
- `tests/test_cycle21.py`: added `test_api_cards_returns_array_with_live_card` (asserts `/api/cards` returns a list with at least one live card carrying `id`/`title`/`status` fields) and `test_api_cards_live_card_usable_in_application_preview` (fetches a live card id from `/api/cards`, then POSTs it to `/api/studio/application-preview`, asserts 200 + `ok: true` — proving the selector→preview API flow end-to-end).

자동 체크: pytest ✅ 468 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
