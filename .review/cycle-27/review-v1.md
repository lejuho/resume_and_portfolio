# Codex Review v1

## Verdict
BLOCKED

## Findings
### ISSUE-1 [MEDIUM] Workspace shell visually violates the planned sentence-case design direction
- Location: `scripts/templates/workspace.html:21`, `scripts/templates/workspace.html:39`,
  `scripts/templates/workspace.html:42`, `scripts/templates/workspace.html:48`
- Analysis: The Cycle 27 plan imports the `landing.md` design-token direction and explicitly
  calls for sentence-case copy. The current workspace shell applies `text-transform: uppercase`
  to pane titles, section headings, field labels, and coverage labels. That means labels such as
  "Evidence cards", "Target", "Organization", and "Themes matched" render as ALL CAPS even
  though the underlying text is sentence case.
- Impact: This is a direct mismatch with the intended Linear/Notion-like calm UI direction and
  makes the new route start from the old admin-console visual language rather than the
  `landing.md` workspace direction.
- Fix direction: Remove the uppercase transforms from the workspace shell. Keep the text itself
  sentence case, and use size/color/weight/spacing for hierarchy instead of capitalization. Add a
  focused Cycle 27 source test that `workspace.html` does not contain `text-transform: uppercase`.

### ISSUE-2 [LOW] Advisor feedback says preview wiring was skipped, but implementation wires it
- Location: `.review/cycle-27/advisor-feedback/step-001.md:17`, `scripts/static/workspace.js:106`
- Analysis: Step 001 advisor guidance says to include `ws-generate-btn` and `ws-preview-out`
  hooks and "skip application-preview wiring (shell-first)." The same file's Decision section
  says all five guidance points were applied. However, `workspace.js` does call
  `/api/studio/application-preview`. The Cycle 27 plan allows minimal preview integration, so the
  implementation choice itself is not out of scope; the problem is the advisor/Sonnet response
  record is inaccurate and does not explain the deviation from advisor guidance.
- Impact: This violates the workflow rule that ignored advisor guidance must be explicitly
  explained. It also makes the review trail misleading.
- Fix direction: Add a correction in the advisor feedback Sonnet Response, or a new advisor step,
  explaining that preview wiring was intentionally kept because the plan allowed minimal reuse of
  `/api/studio/application-preview`. Do not change the advisor's quoted guidance; correct the
  executor response/accounting.

## Sprint Contract Check
| Contract Item | Status | Notes |
| --- | --- | --- |
| `/workspace` returns HTTP 200 | PASS | New route renders `workspace.html`. |
| `/studio` remains HTTP 200 | PASS | Existing Studio route and static JS still pass tests. |
| Dashboard may link to `/workspace` while retaining `/studio` | PASS | Dashboard has both links. |
| Workspace template includes evidence/cards and target/output panes | PASS | `ws-left-pane` and `ws-right-pane` exist. |
| Workspace source includes live card, selected count, target, output, coverage, generate hooks | PASS | Required hooks exist. |
| Workspace JS fetches `/api/cards`, uses `Array.isArray(data)`, filters live, avoids `data.cards` | PASS | Source tests cover this. |
| Workspace JS is independent from `studio.js` and `st-*` ids | PASS | Source tests cover this. |
| No new backend mutation/persistence route | PASS | No `/api/workspace` route added. |
| Existing Studio/Application Writing regressions remain green | PASS | Full test suite passes. |
| Landing-derived sentence-case design direction | FAIL | ISSUE-1: CSS forces multiple labels/headings to uppercase. |
| Advisor feedback accounting | FAIL | ISSUE-2: step-001 claims all guidance applied despite preview wiring deviation. |

## Automatic Checks
- `uv run pytest tests/test_cycle27.py -v`: PASS — 22 passed
- `uv run pytest -v`: PASS — 546 passed, 7 existing `datetime.utcnow()` deprecation warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 34 files already formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`

## Changes Outside Plan
No code scope creep identified. The preview API reuse is allowed by the plan, but the advisor
feedback record needs correction because it says that wiring was skipped.

---

## RESOLVED

### Issue Classification

- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Remove `text-transform: uppercase` from workspace.html

- Removed `text-transform: uppercase` from `.ws-pane-title`, `.ws-section h3`,
  `.ws-field label`, and `.ws-coverage-label`. Hierarchy now expressed through font-size,
  font-weight, color, and reduced letter-spacing only. Underlying text was already sentence
  case; CSS was overriding it.
- Added `test_workspace_html_no_uppercase_transform` to `tests/test_cycle27.py` (group F):
  asserts `text-transform: uppercase` is absent from `/workspace` HTML response.

RESOLVED: ISSUE-2 — Correct advisor feedback accounting in step-001.md

- Updated `Decision` line to note one deviation.
- Updated `Sonnet Response` to accurately record items 1/2/3/5 as applied and item 4's
  "skip wiring" guidance as intentionally not followed.
- Added explicit explanation: Cycle 27 plan allowed minimal `/api/studio/application-preview`
  reuse; implementation wired it; deviation should have been recorded at the time.
- Advisor guidance text in the `Advisor Guidance` section was not modified.

자동 체크: pytest ✅ 547 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅
