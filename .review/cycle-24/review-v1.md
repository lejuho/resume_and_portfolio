# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [HIGH] Cycle 24 creates the cross-cycle advisor artifacts it is meant to prevent

- Location: `.review/cycle-24/advisor-feedback/step-003.md:1`,
  `.review/cycle-24/advisor-feedback/step-004.md:1`, `tests/test_cycle24.py:49-93`
- Analysis: The plan requires preventing cross-cycle advisor-feedback duplication. The
  implementation adds tests for synthetic cross-reference fixtures, but the actual Cycle 24
  advisor directory now contains files headed `Session Cross-Reference: Cycle 23 ISSUE-1`.
  These are exactly the artifacts the new AGENTS.md rule says are forbidden. Because the test
  helper only checks `tmp_path` fixtures and never scans the live `.review/cycle-*` tree, the
  suite can pass while the repository still contains forbidden advisor files.
- Impact: Sprint Contract items "Hygiene check detects advisor files whose heading or body
  indicates they are Session Cross-Reference" and "Running git status does not show unrelated
  cross-cycle notes" are not satisfied. The proposed guard does not protect the actual merge
  path.
- Fix direction: Remove or leave unstaged the cross-reference advisor files from
  `.review/cycle-24/advisor-feedback/`. Add a repository-level hygiene test that scans real
  tracked/untracked `.review/cycle-*/advisor-feedback/step-*.md` files under the working tree
  and fails on `Session Cross-Reference` headings or wrong-cycle headings. Keep fixture tests
  if useful, but they are not sufficient by themselves.

## Regression Check

No application code regression identified. The blocker is in cycle artifact hygiene: the new
workflow rule and tests do not yet enforce the real repository state.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| `.read-counter` files under `.review/` are ignored by git | PASS | `git status --short` no longer lists `.review/cycle-*/.read-counter`. |
| AGENTS.md documents no cross-cycle advisor-feedback duplication | PASS | New AGENTS.md section forbids Session Cross-Reference copies. |
| Hygiene check detects cross-reference advisor artifacts | FAIL | ISSUE-1: live Cycle 24 `step-003.md` and `step-004.md` are cross-reference artifacts and current tests do not scan them. |
| Hygiene check allows valid advisor-feedback files | PASS | Fixture coverage exists for valid heading/directory match. |

## Automatic Checks

- Not rerun for this review: blocker is visible in the reviewed files and must be fixed before
  the final full check run.

## Changes Outside Plan

The cross-reference advisor files are outside the plan's allowed artifact model and should not
be staged or merged.

---

## RESOLVED

### Issue Classification

- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — Delete forbidden cross-reference step files; add real-tree hygiene test

- Deleted `.review/cycle-24/advisor-feedback/step-003.md` and `step-004.md`
  (headings contained "Session Cross-Reference: Cycle 23 ISSUE-1"; untracked, no history loss).
- Deleted `.review/cycle-23/advisor-feedback/step-004.md` through `step-009.md`
  (all had "Session Cross-Reference" headings; untracked stubs created for a now-resolved hook
  conflict).
- Added `test_real_tree_advisor_hygiene` to `tests/test_cycle24.py`: walks
  `repo_root.glob(".review/cycle-*/advisor-feedback/step-*.md")`, applies
  `_advisor_hygiene_error()` to each file in the working tree (tracked + untracked), asserts
  no violations. Fails with path + heading in the error message.
- Existing `tmp_path` fixture tests retained — they remain useful as unit tests for the
  checker logic itself.

자동 체크: pytest ✅ 488 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ /
pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ /
evaluate_studio_grounding.py --dry-run ✅
