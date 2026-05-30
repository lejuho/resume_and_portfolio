# Advisor Feedback: Cycle 24 Step-001 — Review Artifact Hygiene

Type: Approach check + Completion check
Scope: .gitignore, AGENTS.md, tests/test_cycle24.py (new)
Plan baseline: Cycle 24 plan.md — Review artifact hygiene

## Approach Check (before implementation)

Query: detection logic placement (inline vs script); path-to-cycle extraction; rule 3 (own
cycle cross-reference handling).

Key guidance received:
1. Inline helper in test file — single use site; no premature script extraction.
2. Extract cycle from path via `\.review/cycle-(\d+)/` regex; compare to heading capture.
3. Rule 1 (Session Cross-Reference substring) already catches own-cycle cross-refs — no
   additional cycle math needed.
4. Rule order: cross-ref substring first → newer heading mismatch → skip older `# Step NNN`.
5. Emit failing path + heading in assertion message for fast triage.
6. Walk only `.review/cycle-*/advisor-feedback/step-*.md`; skip READMEs/index files.
7. Defer extraction to scripts/ only if a second caller appears.

Decision: Applied all seven guidance points.

## Completion Check (after implementation)

Changes:
- `.gitignore`: added `.review/**/.read-counter`. `git status --short` shows no `.read-counter`
  files after the rule is applied; `git check-ignore` confirms the glob matches on Windows.
- `AGENTS.md`: appended two subsections under Advisor Feedback Externalization:
  - "Cross-Cycle 중복 금지" — forbids Session Cross-Reference copies; requires heading N to
    match directory N; links-only policy for cross-cycle references.
  - "Merge 전 Staging 체크리스트" — table of artifacts to exclude before `git add`:
    `.read-counter`, `.agents/`, `skills-lock.json`, cross-cycle step files, RESOLVED
    section re-edits.
- `tests/test_cycle24.py` — 4 tests using inline `_advisor_hygiene_error(path)` helper:
  - `test_valid_advisor_file_passes`: heading cycle matches directory → None returned.
  - `test_cross_reference_advisor_file_fails`: "Session Cross-Reference" in heading → error.
  - `test_wrong_cycle_advisor_file_fails`: heading says Cycle 3, dir is cycle-5 → error with
    both cycle numbers in message.
  - `test_gitignore_contains_read_counter_rule`: `.review/**/.read-counter` in `.gitignore`.
  All tests use `tmp_path`; live `.review/` tree is never touched.

Regression concerns verified:
1. Older format `# Step NNN —` (cycles 1-19): rule 2 only fires on `# Advisor Feedback:
   Cycle N Step` pattern — no false positives. ✓
2. Untracked cycle-23 cross-reference files: tests use `tmp_path` fixtures; live tree
   unaffected. ✓
3. `.gitignore` glob `**` works on Windows per `git check-ignore` confirmation. ✓

## Decision

PROCEED. 487 tests pass (483 → +4). All checks green.

Auto checks: pytest ✅ 487 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
