# Advisor Feedback: Cycle 21 Step-008 — review-v10 ISSUE-12

Type: Approach check + Completion check
Scope: scripts/static/studio.js, tests/test_cycle21.py
Plan baseline: Escalation Amendment v4 (plan.md) — Studio live-card selector contract fix

## Approach Check (before implementation)

Query: JS replacement expression; regression test scope and placement.

Key guidance received:
1. Use `Array.isArray(data) ? data : []` — safer than `data || []`; defends against future
   shape drift; truthy non-arrays (object) would pass `|| []` but be caught by `Array.isArray`.
2. Both assertions needed: `/api/cards` shape test (proves the array contract the JS fix
   depends on) and `POST /api/studio/application-preview` with a card id from that response
   (closest Python proxy for the broken selector→preview flow).
3. Both tests go in `test_cycle21.py` — ISSUE-12 is a Cycle 21 regression; colocation with
   sibling fixes keeps one review surface.

Decision: Applied all three guidance points.

## Completion Check (after implementation)

Changes:
- `scripts/static/studio.js:306` — replaced `(data.cards || [])` with
  `(Array.isArray(data) ? data : [])`. `status === "live"` filter, empty-state render, and
  error-catch UI block are unchanged.
- `tests/test_cycle21.py` — added two tests:
  - `test_api_cards_returns_array_with_live_card`: GET /api/cards; asserts response is a list,
    contains at least one live card, and each live entry has `id`, `title`, `status` fields.
  - `test_api_cards_live_card_usable_in_application_preview`: fetches live card id from
    /api/cards, then POSTs it to /api/studio/application-preview; asserts 200 + `ok: true`.
    Proves the selector→preview flow end-to-end at API level.

Regression risks verified:
1. Non-live cards: `Array.isArray(data)` returns the full array; `status === "live"` filter
   still excludes non-live cards. ✓
2. Empty response `[]`: `Array.isArray([])` is true; empty-state path triggers as before. ✓
3. Network error: caught by existing `catch (_)` block; error UI unchanged. ✓
4. All existing 466 tests remain green; no new failures. ✓

## Decision

PROCEED. 468 tests pass (466 → +2 ISSUE-12 regression tests). All checks green.

Auto checks: pytest ✅ 468 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
