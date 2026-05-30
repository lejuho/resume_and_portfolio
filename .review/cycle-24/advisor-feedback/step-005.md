# Advisor Feedback: Cycle 24 Step-005 — ISSUE-1 Approach Check

Type: Approach check
Scope: tests/test_cycle24.py, .review/cycle-24/advisor-feedback/, .review/cycle-23/advisor-feedback/

## Query

How to scope the real-tree scan given that cycle-23 also has 6 untracked cross-reference stubs
(step-004 through step-009) with "Session Cross-Reference" headings?

## Advisor Guidance

1. Read cycle-23 step-004..009 first — confirm whether they contain forbidden headings.
2. Delete cycle-24 step-003.md/step-004.md (forbidden headings; untracked, no history loss).
3. Cycle-23 stubs also have forbidden headings → delete them too (untracked, satisfied a now-removed hook requirement).
4. Scope real-tree test: scan all `.review/cycle-*/advisor-feedback/step-*.md` in working tree
   (tracked + untracked) — catches future drift.
5. Write step-005.md with neutral heading (no "Session Cross-Reference" string).
6. Run pytest; confirm all tests pass.

## Decision

Applied all six guidance points. Deleting cycle-23 step-004..009 and cycle-24 step-003..004.
Adding `test_real_tree_advisor_hygiene` to `tests/test_cycle24.py`.

## Sonnet Response

- 적용: 모든 6개 항목 적용.
- 무시: 없음.
