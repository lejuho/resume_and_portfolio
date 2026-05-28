# Advisor Feedback: Cycle 21 Step-003 — Amendment v3 Implementation

Type: Approach check + Completion check
Scope: scripts/dashboard.py, tests/test_cycle21.py
Plan baseline: Escalation Amendment v3 (plan.md) — Unified Blind-Hiring Boundary

## Approach Check (before implementation)

Query: `_build_safe_projection` return shape, empty projection → 422, `_sanitize_advisory` interface.

Key guidance received:
1. `missing_info_additions` owned by `_build_safe_projection`. Caller appends only. Leak risk if caller composes.
2. 422 correct for all-excluded. Submitted cards schema-valid but policy-unprocessable — classic 422 semantics. 400 implies malformed input.
3. Pass full advisory in, return full sanitized advisory + additions list. Single-pass screening across all four fields avoids partial-sanitization drift; tuple keeps additions separate so caller merges with ledger-level notices uniformly.

Decision: Applied all three advisor guidance points.

## Completion Check (after implementation)

Changes:
- `scripts/dashboard.py`: `_build_fact_ledger` (3-tuple) removed; replaced by `_build_safe_projection` (dict projection) + `_sanitize_advisory`. `_mock_application_preview` signature changed from `(output_type, cards, target_context)` to `(output_type, projection, target_context)`. Endpoint: single `_build_safe_projection` call; blind+empty → 422; `_sanitize_advisory` replaces inline ISSUE-8 screening; LLM and mock paths both use projection.
- `tests/test_cycle21.py`: 4 identity_client tests updated to expect 422 (not 200). LLM-path identity test updated to assert LLM not called. 5 new Amendment v3 tests added.

Regression risks verified:
1. `_mock_application_preview` only called from one site (endpoint); no other callers. Safe.
2. No test monkeypatches `_build_fact_ledger`; all coverage now through `_build_safe_projection` or endpoint assertions. Removal clean.
3. Non-blind empty projection: 422 gate is blind-only; non-blind falls to mock. Matches prior behavior.

## Decision

PROCEED. 460 tests pass (455 → +5 Amendment v3 tests). All 3 regressions green.

Auto checks: pytest ✅ 460 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
