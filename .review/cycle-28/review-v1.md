# Codex Review v1

## Verdict
BLOCKED

## Findings
### ISSUE-1 [MEDIUM] Workspace token alignment leaves repeated accent/surface colors hard-coded
- Location: `scripts/templates/workspace.html:34`, `scripts/templates/workspace.html:38`,
  `scripts/templates/workspace.html:59`, `scripts/templates/workspace.html:69`,
  `scripts/templates/workspace.html:70`, `scripts/templates/workspace.html:71`
- Analysis: Cycle 28's purpose is design-token alignment, and the plan says to replace repeated
  hard-coded blue/gray values with token variables where practical. The implementation defines
  useful tokens, but repeated workspace-specific values still remain hard-coded in the selected
  card tint, pill tint, coverage panel tint/border, button hover, disabled button, input surface,
  preview surface, and muted text fallbacks. Some one-off colors are acceptable, but these are
  reusable token roles: accent tint, accent border, accent hover, disabled surface, input surface,
  preview surface, and secondary text.
- Impact: The Workspace shell is only partially tokenized. Future UI work will still duplicate
  the exact values this cycle was meant to centralize.
- Fix direction: Add and consume focused tokens for repeated roles, for example
  `--ws-accent-tint`, `--ws-accent-border`, `--ws-accent-hover`, `--ws-disabled`,
  `--ws-input-bg`, `--ws-preview-bg`, and `--ws-text-secondary` as needed. Add source tests that
  the repeated raw values are absent outside token definitions, at least for `rgba(74, 144, 217`
  and `#3a7fc7`.

### ISSUE-2 [LOW] Advisor feedback claims label-wrapping was applied, but markup uses sibling input/label
- Location: `.review/cycle-28/advisor-feedback/step-001.md:15`,
  `.review/cycle-28/advisor-feedback/step-002.md:17`, `scripts/static/workspace.js:51`
- Analysis: Advisor step-001 recommended wrapping the checkbox inside
  `<label class="ws-card-body">`, and its Decision says all guidance was applied. Step-002 also
  says the card body is wrapped in `<label class="ws-card-body">`. The actual markup emits the
  checkbox first, followed by a sibling `<label class="ws-card-body" for="...">`. That structure
  is valid and preserves click-to-toggle, so the implementation itself can be acceptable. The
  problem is the advisor/executor record is inaccurate.
- Impact: This violates the advisor feedback accounting rule. Reviewers cannot trust the step
  files to describe what was actually implemented.
- Fix direction: Correct the Sonnet Response/accounting in the advisor feedback. Either update
  the record to say the implementation intentionally kept the input/label sibling structure, or
  change the markup to match the recorded label-wrapped structure. Do not edit quoted advisor
  guidance; correct the executor decision/accounting.

## Sprint Contract Check
| Contract Item | Status | Notes |
| --- | --- | --- |
| `/workspace` remains HTTP 200 and `/studio` remains HTTP 200 | PASS | Existing route tests pass. |
| `workspace.html` defines workspace design tokens in `:root` | PASS | Core token variables were added. |
| Workspace CSS contains no uppercase transform | PASS | Cycle 27 test remains green. |
| Workspace CSS contains no `font-weight: 600` or `700` | PASS | Source tests cover this. |
| Workspace shell uses token variables for accent/info and common surfaces/borders | FAIL | ISSUE-1: repeated accent/surface roles remain hard-coded. |
| Card markup/classes include pill, title, context, metadata, selected-state hook | PASS | `workspace.js` emits the planned classes. |
| Workspace JS toggles selected-state styling | PASS | `_wsOnCardToggle(cb)` toggles `ws-card-selected`. |
| Workspace JS preserves `/api/cards` array/live/no-`data.cards` contract | PASS | Source tests cover this. |
| No new backend mutation/persistence route | PASS | No backend route added. |
| Existing Studio/Application Writing tests remain green | PASS | Full test suite passes. |
| Advisor feedback accounting | FAIL | ISSUE-2: step files describe label-wrapping that is not implemented. |

## Automatic Checks
- `uv run pytest tests/test_cycle27.py tests/test_cycle28.py -v`: PASS — 40 passed
- `uv run pytest -v`: PASS — 564 passed, 7 existing `datetime.utcnow()` deprecation warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 35 files already formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`

## Changes Outside Plan
No feature scope creep identified. Changes are limited to Workspace styling/markup/tests, but
tokenization and advisor accounting need correction before merge.

---

## RESOLVED

### Issue Classification

- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Finish workspace token alignment

- Added 7 tokens to `:root`: `--ws-text-secondary`, `--ws-accent-tint`,
  `--ws-accent-border`, `--ws-accent-hover`, `--ws-disabled`, `--ws-input-bg`,
  `--ws-preview-bg`.
- Replaced all `rgba(74, 144, 217, ...)` outside `:root` with `var(--ws-accent-tint)`
  or `var(--ws-accent-border)` (multiple alpha values unified into two semantic roles;
  minor visual delta accepted for token alignment cycle).
- Replaced `#3a7fc7` → `var(--ws-accent-hover)`, `#aaa` → `var(--ws-disabled)`,
  `#fafafa` → `var(--ws-input-bg)`, `#f8f8ff` → `var(--ws-preview-bg)`,
  `#555` → `var(--ws-text-secondary)`.
- Added `test_workspace_html_no_raw_rgba_accent_outside_root` and
  `test_workspace_html_no_raw_accent_hover_outside_root` to `tests/test_cycle28.py`.
  Each test carries `rv.status_code == 200` + positive `var(--ws-accent-*)` anchor.

RESOLVED: ISSUE-2 — Correct advisor feedback accounting

- `step-001.md` Decision line updated to note item-2 deviation.
- `step-001.md` Sonnet Response updated: records that sibling input/label was kept
  instead of label-wrapping, with explanation (accessibility clarity, `this` binding).
- `step-002.md` item 3 corrected to accurately describe sibling structure.
- Advisor Guidance sections in both files not modified.

자동 체크: pytest ✅ 566 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅
