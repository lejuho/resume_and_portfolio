# Advisor Feedback: Cycle 25 Step-003 — ISSUE-1 Fix (Error Path Clears Handoff State)

Type: Approach check + Completion check
Scope: scripts/static/studio.js, tests/test_cycle25.py

## Fix

Added `_resetAppHandoffState()` shared helper:
- Sets `_appLastPreview = null`
- Clears `_appDraftText = ""`
- Hides `st-app-copy-btn` (hidden = true)
- Hides `st-app-export-btn` (hidden = true)
- Clears and hides `st-app-export-out` (textContent = "", display = none)

`_showAppError()` calls `_resetAppHandoffState()` as its first action before rendering
the error message into the draft box.

## Regression tests added (5 new, group G)

- `test_studio_js_reset_helper_exists`: `_resetAppHandoffState` defined in JS.
- `test_studio_js_show_error_calls_reset`: `_showAppError` body contains `_resetAppHandoffState`.
- `test_studio_js_reset_clears_last_preview`: reset body contains `_appLastPreview = null` and `_appDraftText`.
- `test_studio_js_reset_hides_export_and_copy_buttons`: reset body contains both button IDs and `hidden = true`.
- `test_studio_js_reset_clears_export_output`: reset body contains `st-app-export-out`.

## Checks

510 passed / ruff check ✅ / ruff format ✅

## Sonnet Response

- 적용: 모든 항목 적용.
- 무시: 없음.
