# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [MEDIUM] Copy button reverts to the old ambiguous label after copy

- Location: `scripts/templates/studio.html:243`, `scripts/static/studio.js:477`,
  `tests/test_cycle23.py:128-131`
- Analysis: The template label was updated to `Copy Verified draft to clipboard`, matching the
  Cycle 23 goal that the copy action clearly applies only to the verified draft. However,
  `copyAppDraft()` still resets the button text to `Copy to clipboard` after the success
  state. The new regression test only checks the initial HTML label, so it does not protect
  the post-copy state.
- Impact: Sprint Contract item "Verified Draft label/copy makes clear that the draft is the
  only copyable text" is not consistently satisfied. After one successful copy, the UI returns
  to the old ambiguous copy label.
- Fix direction: Update the post-copy reset string in `copyAppDraft()` to restore
  `Copy Verified draft to clipboard`, and add a focused source test that guards this reset
  string so the old label cannot be reintroduced.

## Regression Check

No generation, provider, blind-hiring policy, or persistence regression identified. The
blocker is limited to copy-label consistency and regression coverage for the changed UX copy.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Live-card selector shows useful metadata without changing `/api/cards` shape | PASS | Selector renders title, summary, and metric/evidence counts from existing fields. |
| Empty live-card state mentions Dashboard Live state and validation errors | PASS | Empty-state string includes both actions/causes. |
| Verified Draft copy clearly identifies the copied content | FAIL | ISSUE-1: post-copy reset restores old ambiguous label. |
| AI Guidance remains advisory and not copied | PASS | Copy path still uses `_appDraftText`, populated from `preview.answer_draft`; guidance renders separately. |
| Blind-hiring all-redacted `422` message gives corrective action | PASS | Error now tells user to choose cards without identifiers or remove those details. |

## Automatic Checks

- Not rerun for this review: blocker is visible in the reviewed source and should be fixed
  before the final full check run.

## Changes Outside Plan

No scope creep identified. Current changes stay within Application Writing UX polish.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — Post-copy reset string aligned with initial button label
- `scripts/static/studio.js:477`: `setTimeout` reset string in `copyAppDraft()` changed from `"Copy to clipboard"` to `"Copy Verified draft to clipboard"`. No other logic, handler, or timeout changed.
- `tests/test_cycle23.py:test_studio_html_copy_button_label_updated`: extended to also GET `/static/studio.js` and assert `b"Copy Verified draft to clipboard"` present AND `b'"Copy to clipboard"'` (quoted JS literal form) absent. Test-first: RED confirmed before fix applied.
- No other source file retains `"Copy to clipboard"` as a literal — verified by grep.

자동 체크: pytest ✅ 483 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
