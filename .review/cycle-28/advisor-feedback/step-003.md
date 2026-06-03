# Advisor Feedback: Cycle 28 Step-003 — ISSUE-1/ISSUE-2 Fix Completion

Type: Completion check
Scope: scripts/templates/workspace.html, tests/test_cycle28.py,
       .review/cycle-28/advisor-feedback/step-001.md,
       .review/cycle-28/advisor-feedback/step-002.md

## Completion Check (after implementation)

Changes applied:
1. `workspace.html` `:root`: added `--ws-text-secondary`, `--ws-accent-tint`,
   `--ws-accent-border`, `--ws-accent-hover`, `--ws-disabled`, `--ws-input-bg`,
   `--ws-preview-bg`.
2. All `rgba(74, 144, 217, ...)` outside `:root` replaced with `var(--ws-accent-tint)`
   or `var(--ws-accent-border)`. `#3a7fc7` replaced with `var(--ws-accent-hover)`.
   `#aaa`, `#fafafa`, `#f8f8ff`, `#555` replaced with respective token vars.
3. `tests/test_cycle28.py`: added `test_workspace_html_no_raw_rgba_accent_outside_root`
   and `test_workspace_html_no_raw_accent_hover_outside_root` (19 total).
   Each test asserts `rv.status_code == 200`, positive `var(--ws-accent-*)` presence,
   and raw value absence outside `:root`.
4. `step-001.md` Decision + Sonnet Response: updated to record sibling input/label
   deviation from label-wrapping guidance, with explanation.
5. `step-002.md` item 3: corrected to state sibling structure, not label-wrapping.

Regression verification:
1. No alpha-specific assertion in any test — alpha unification safe. ✓
2. `:root` block is flat (no nested `{}`); `_after_root` index terminates correctly. ✓
3. Both new absence tests now have positive `var(--ws-accent-*)` anchor assertions
   plus `rv.status_code == 200`; false-pass risk on empty response eliminated. ✓
4. 566 total tests pass, ruff check ✓, ruff format ✓, pcli validate ✓. ✓

## Advisor Verdict

PASS

## Sonnet Response

- 적용: 모든 3개 regression concern 확인 완료. concern 3(false-pass risk) 즉시 수정.
- 무시: 없음.
