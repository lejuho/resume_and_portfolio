# Advisor Feedback: Cycle 21 Step-006 — review-v7 ISSUE-10 and ISSUE-11

Type: Approach check + Completion check
Scope: requirements-dashboard.md, docs/test-cases.md, docs/acceptance-studio.md, tests/test_cycle21.py
Plan baseline: Escalation Amendment v3 (plan.md)

## Approach Check (before implementation)

Query: doc update scope for ISSUE-10; provider-payload capture strategy for ISSUE-11.

Key guidance received:
1. requirements-dashboard.md: replace only the "Blind-hiring pre-provider check" bullet; keep
   the surrounding status block.
2. test-cases.md: PT-APP-006 row only; PT-APP-001 unaffected (source_card_id note is about
   provenance, not blind-mode opaque refs).
3. acceptance-studio.md: row 7 only; row 8 (guidance screen) unchanged.
4. ISSUE-11 capture strategy: monkeypatch `application_preview_llm` with a wrapper that appends
   `fact_ledger` to a local list; assert on captured input.
5. ISSUE-11 assertion scope: both provider-input (canonical ID absent, C1 present) and returned
   preview (same as existing mock test); prevents regression on both sides.

Decision: Applied all five guidance points.

## Completion Check (after implementation)

Changes:
- `requirements-dashboard.md:627-629` — replaced superseded "Blind-hiring pre-provider check"
  bullet with v3 unified projection description: per-field screening, safe display label, opaque
  refs, partial-success vs HTTP 422, `_sanitize_advisory` scope, competency assertion policy.
- `docs/test-cases.md:197` — PT-APP-006 row updated to describe per-field screening, partial
  redaction (200 + warning), all-excluded (422), opaque refs in provider payload and preview,
  full advisory sanitization, and target_context.competency assertion policy.
- `docs/acceptance-studio.md:96` — row 7 updated to describe per-field screening, safe display
  label, opaque canonical-ID replacement, 422 on all-empty, and absence assertion on serialized
  preview JSON. Row 8 unchanged.
- `tests/test_cycle21.py` — added
  `test_blind_hiring_opaque_card_id_in_provider_payload` using `opaque_id_client` fixture.
  Monkeypatches `application_preview_llm` with a capturing wrapper; asserts:
  - LLM was actually called
  - `alumni-program-2024` absent from all `source_card_id` values in captured `fact_ledger`
  - opaque ref `C1` present in captured `fact_ledger`
  - returned preview `fact_ledger` also uses opaque refs
  - serialized preview JSON does not contain canonical ID

Regression risks verified:
1. Non-blind path: `opaque_id_client` fixture used only with `blind_hiring=True`; non-blind
   path unaffected. ✓
2. Existing `test_blind_hiring_opaque_card_id_in_preview` (mock path): unchanged; still passes. ✓
3. Doc edits are append/replace only within identified line ranges; no surrounding text altered. ✓

## Decision

PROCEED. 466 tests pass (465 → +1 provider-payload regression test). All checks green.

Auto checks: pytest ✅ 466 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
