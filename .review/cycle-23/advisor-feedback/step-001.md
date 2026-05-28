# Advisor Feedback: Cycle 23 Step-001 — Application Writing UX Polish

Type: Approach check + Completion check
Scope: scripts/static/studio.js, scripts/templates/studio.html, scripts/dashboard.py,
       tests/test_cycle23.py (new)
Plan baseline: Cycle 23 plan.md — Application Writing UX polish only

## Approach Check (before implementation)

Query: card metadata rendering approach; empty-state append vs replace; copy note placement;
422 message sentence swap.

Key guidance received:
1. Card metadata: inline innerHTML in existing loop (single use site; helper adds indirection
   without payoff).
2. Summary: trim with ellipsis if >80 chars; counts as "M metrics · E evidence".
3. Empty-state: append to existing string — preserves primary instruction, adds new hint as
   secondary guidance.
4. Copy note: HTML template (static; co-located with button for readability).
5. 422: keep first sentence verbatim; only swap sentence two.

Decision: Applied all five guidance points.

## Completion Check (after implementation)

Changes:

**scripts/static/studio.js**
- `loadAppCards()` card row: replaced `card.title + card-status span` with three-span layout
  (`card-title`, optional `card-summary` ≤80 chars + `…`, `card-counts` = "M metrics · E
  evidence" or "no metrics or evidence"). Fields consumed from existing `_card_to_dict`
  response: `summary`, `metrics_count`, `evidence_count`. No `/api/cards` shape change.
- Empty-state: appended "If a card shows validation errors it will not appear here." to
  existing message.

**scripts/templates/studio.html**
- CSS: replaced `.card-status` rule with `.card-title` (font-weight:500), `.card-summary`
  (color:#555, font-size:.78rem), `.card-counts` (color:#888, font-size:.72rem) and updated
  `.card-check-item` to `align-items: flex-start` + `label` flex-column for stacked metadata.
- Copy button: label changed from "Copy to clipboard" to "Copy Verified draft to clipboard".
- Added `<small id="st-app-copy-note">Only the Verified draft text above is copied — AI
  Guidance is not included.</small>` after copy button.

**scripts/dashboard.py**
- 422 error message: second sentence replaced from "Submit cards without education or
  background identifiers." to "To generate a preview: choose cards without education or
  background identifiers, or remove those details from your evidence cards first." First
  sentence ("All submitted cards were excluded under blind-hiring policy.") unchanged.
  Existing tests asserting `"blind-hiring policy" in body["error"]` continue to pass.

**tests/test_cycle23.py** (new file — 7 tests):
- `test_studio_js_selector_renders_card_metadata` — card-title/summary/counts class refs and
  metrics_count/evidence_count field refs in JS source.
- `test_studio_js_selector_summary_truncation` — `slice(0, 80)` and `…` in JS source.
- `test_studio_js_selector_empty_metric_fallback` — "no metrics or evidence" in JS source.
- `test_studio_js_empty_state_mentions_validation_errors` — "validation errors" + "No live
  cards found" in JS source.
- `test_studio_html_copy_note_present` — `st-app-copy-note`, "Only the Verified draft text",
  "AI Guidance is not included" in HTML.
- `test_studio_html_copy_button_label_updated` — "Copy Verified draft to clipboard" in HTML.
- `test_blind_hiring_422_actionable_message` — 422 error contains "blind-hiring policy" and
  "choose cards" or "remove those details".

Regression risks verified:
1. All existing cycle-21/22 source-inspection tests: `card-status` span removed — checked;
   no test asserts `card-status` (only `.card-status` CSS rule existed, which is replaced). ✓
2. 422 tests asserting `"blind-hiring policy" in body["error"]`: first sentence unchanged. ✓
3. `copyAppDraft` reads `_appDraftText`; button label change only (HTML text). ✓
4. No generation policy, provider, blind-hiring rule, or persistence code changed. ✓

## Decision

PROCEED. 483 tests pass (476 → +7). All checks green.

Auto checks: pytest ✅ 483 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
