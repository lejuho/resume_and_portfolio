# Advisor Feedback: Cycle 21 Step-002 — ISSUE-8/9 Implementation

Type: Approach check + Completion check
Scope: scripts/dashboard.py, tests/test_cycle21.py
Plan baseline: Escalation Amendment v1 + v2 (plan.md), review-v6 ISSUE-8/9

## Approach Check (before implementation)

Query: `_build_fact_ledger` 3-tuple return, ISSUE-8 advisory screening, missing_info item handling.

Key guidance received:
1. 3-tuple `(ledger, card_excluded, field_redacted)` OK. LLM skip: `not card_excluded` only. field_redacted allows LLM on clean ledger.
2. Extract `_question_intent`/`_competency_target` before `if _blind:` block, replace via local variables only. `BLIND_HIRING_ADVISORY_REDACTED` appended once when any advisory redaction occurs.
3. **missing_info**: do NOT drop item entirely — preserve `code` for traceability, replace `message` with safe wording. Advisor overruled initial drop-item approach.

Decision: Applied advisor guidance on point 3 (message replacement, not deletion).

## Completion Check (after implementation)

Changes:
- `_build_fact_ledger`: 3-tuple, metrics/evidence `_IDENTITY_RE` screening
- `_mock_application_preview`: 3-tuple unpack, `identity_flagged = card_excluded or field_redacted`
- `api_studio_application_preview`: LLM skip via `_card_excluded` only; ISSUE-8 advisory screening; ISSUE-9 LLM-path `BLIND_HIRING_PERSONAL_IDENTIFIERS` when `_field_redacted`
- 7 new tests: ISSUE-8 ×3, ISSUE-9 ×4 (mock+LLM for metric and evidence)

Regression risks verified:
1. `card_excluded` path (title/summary identity) → mock fallback + BLIND_HIRING_PERSONAL_IDENTIFIERS: VERIFIED
2. LLM skip on `not _card_excluded` preserves original title/summary identity behavior: VERIFIED
3. `_ledger_to_selected_cards` metric-empty fallback to title-based reason: VERIFIED

## Decision

PROCEED. 455 tests pass. All 3 regressions green.

Auto checks: pytest ✅ 455 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
