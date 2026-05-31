# Codex Review v1

## Verdict
BLOCKED

## Findings
### ISSUE-1 [HIGH] Export can hand off a stale previous preview after a failed regeneration
- Location: `scripts/static/studio.js:394`, `scripts/static/studio.js:457`, `scripts/static/studio.js:536`
- Analysis: `renderAppPreview()` stores the successful preview in `_appLastPreview` and unhides
  `st-app-export-btn`, but `_showAppError()` only replaces the draft text with the error
  message. It does not clear `_appLastPreview`, hide the export button, clear the visible export
  output, or disable draft/export handoff state. Sequence: generate a valid preview, then change
  inputs so the next generation fails validation/provider handling. The panel now shows an error,
  but `exportAppPacket()` still exports the previous successful preview.
- Impact: This violates the Cycle 25 failure/empty-state contract that export is unavailable or
  safe-error-only when there is no current generated preview, and the edge-case requirement that
  export uses the latest successful preview only. From the user side, the exported packet can no
  longer match the visible Application Writing state.
- Fix direction: Add a single reset path for preview handoff state before failed render paths:
  clear `_appLastPreview`, clear `_appDraftText` if the visible draft is replaced by an error,
  hide `st-app-export-btn` and `st-app-copy-btn`, and clear/hide `st-app-export-out`. Add a
  regression source test that `_showAppError()` or a shared reset helper clears export state and
  prevents stale packet export after an error.

## Sprint Contract Check
| Contract Item | Status | Notes |
| --- | --- | --- |
| Generated preview exposes clear export/handoff action | PASS | HTML adds `st-app-export-btn`; `renderAppPreview()` unhides it. |
| Existing verified-draft copy still copies only `answer_draft` | PASS | `copyAppDraft()` still writes `_appDraftText`; existing and new tests cover separation. |
| Export packet includes output type, target context, draft, evidence summary, warnings/source metadata | PASS | `_buildHandoffPacket()` covers these fields from the preview object. |
| Blind-hiring export uses opaque refs/safe labels only | PASS | Packet evidence loop consumes preview `selected_cards` safe display fields rather than `_appCards`. |
| AI guidance is clearly labeled advisory if exported | PASS | Packet uses an `ADVISORY` section. |
| Export creates no new card and mutates no existing card | PASS | Implementation is browser-only; no new backend packet route was added. |
| Empty/error state prevents stale export | FAIL | ISSUE-1: failed regeneration leaves previous preview/export state active. |

## Automatic Checks
- `uv run pytest tests/test_cycle25.py -v`: PASS — 17 passed
- `uv run pytest -v`: PASS — 505 passed, 7 existing `datetime.utcnow()` deprecation warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 32 files already formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`

## Changes Outside Plan
No scope creep identified. Changes are limited to Studio Application Writing export/handoff UI,
browser-side packet composition, acceptance docs, and focused regression tests.

---

## RESOLVED

### Issue Classification

- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — Add `_resetAppHandoffState()` helper; call from `_showAppError()`

- Added `_resetAppHandoffState()` to `scripts/static/studio.js`. Sets `_appLastPreview = null`,
  clears `_appDraftText`, hides `st-app-copy-btn`, hides `st-app-export-btn`, clears and hides
  `st-app-export-out`. Single shared reset path for all handoff state.
- `_showAppError()` now calls `_resetAppHandoffState()` as its first action before displaying
  the error message in the draft box.
- Added 5 regression source tests in `tests/test_cycle25.py` (group G):
  - `test_studio_js_reset_helper_exists`
  - `test_studio_js_show_error_calls_reset`
  - `test_studio_js_reset_clears_last_preview`
  - `test_studio_js_reset_hides_export_and_copy_buttons`
  - `test_studio_js_reset_clears_export_output`

자동 체크: pytest ✅ 510 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅
