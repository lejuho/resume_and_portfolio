# Advisor Feedback: Cycle 21 Step-005 — Amendment v3 target_context.competency Policy Fix

Type: Approach check + Completion check
Scope: scripts/dashboard.py, tests/test_cycle21.py
Plan baseline: Escalation Amendment v3 (plan.md) — blind-hiring boundary for competency assertion

## Approach Check (before implementation)

Query: minimum scope for competency assertion screening; question preamble handling; target_context_used policy.

Key guidance received:
1. Restrict to application_answer path only; cover_letter template has no competency assertion sentence.
2. Screen competency assertion at _compose_answer_draft call site (single guard); do not strip from target_context dict before passing to LLM or serializing into target_context_used.
3. target_context_used serializes the raw input fields — competency string present there is fine; the blind-hiring boundary applies only to what appears in personal_facts and answer_draft.

Decision: Applied all three advisor guidance points. Single guard in _compose_answer_draft; target_context_used unchanged.

## Completion Check (after implementation)

Changes:
- `scripts/dashboard.py` — `_compose_answer_draft`: added guard `if blind_hiring and competency and bool(_IDENTITY_RE.search(competency)): comp_str = ""` before the `comp_str` assignment. `blind_hiring` read from `tc.get("blind_hiring", False)`. When guard fires, competency assertion (`"This reflects {competency}."`) is suppressed; all other template text unaffected. cover_letter path unchanged (no comp_str logic there).
- `tests/test_cycle21.py` — Added `_IDENTITY_COMPETENCY` constant and 2 new tests: `test_blind_hiring_identity_competency_not_in_draft_mock_path` (mock path, clean card, blind+identity competency → 200, competency absent from answer_draft and personal_facts, present in target_context_used) and `test_blind_hiring_identity_competency_not_in_draft_llm_path` (LLM path, same assertions plus refine_source == "llm").

Regression risks verified:
1. Non-blind mode: `blind_hiring = False` → guard never fires → comp_str populated normally. Non-blind path unchanged. ✓
2. cover_letter path: returns before `comp_str` assignment; no change. ✓
3. Empty or non-identity competency: `_IDENTITY_RE.search(competency)` returns None → guard skips → comp_str populated normally. ✓
4. Field-level card screening (step-004): unrelated code path; no interaction. ✓

## Decision

PROCEED. 465 tests pass (463 → +2 competency policy tests). All checks green.

Auto checks: pytest ✅ 465 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
