# Codex Review v7

## Verdict
BLOCKED

## Findings

### ISSUE-10 [MEDIUM] Public contract documents still describe the superseded blind-hiring behavior
- Location: `requirements-dashboard.md:610-631`, `docs/test-cases.md:192-197`,
  `docs/acceptance-studio.md:92-102`
- Analysis: Amendment v3 changes the API behavior to a unified safe projection, opaque card
  references in blind mode, field-level sanitization with partial-success previews, all-empty
  HTTP 422 responses, full advisory sanitization, and a target-context exception. The current
  requirement and acceptance text still states that a title/summary identity match always
  prevents the provider call and tests only guidance screening. It also describes raw
  `source_card_id` provenance without the blind-mode opaque-reference rule.
- Impact: Manual acceptance and published behavior no longer exercise or explain the
  implemented privacy boundary, so the v3 interface cannot be accepted from the documented
  contract.
- Fix direction: Update all three documents to record the v3 projection model, opaque refs,
  partial sanitization versus HTTP 422 behavior, advisory-wide screening, and the permitted
  `target_context` rule.

### ISSUE-11 [LOW] Required provider-payload test for identity-bearing canonical IDs is absent
- Location: `.review/cycle-21/plan.md:614-630`, `tests/test_cycle21.py:1608-1635`
- Analysis: `test_blind_hiring_opaque_card_id_in_preview` disables the provider and proves
  only that the returned mock preview does not expose `alumni-program-2024`. Amendment v3
  explicitly requires the identity-bearing canonical ID case to assert that captured
  provider fact payloads also contain only opaque references. Existing LLM-input tests cover
  metric/evidence filtering, not an identity-bearing canonical ID.
- Impact: The code currently appears to pass sanitized ledger data into the provider path,
  but a mandatory trust-boundary regression is not executable, leaving that interface
  unguarded against later changes.
- Fix direction: Add a configured-provider route test using the identity-bearing ID fixture,
  capture `fact_ledger` passed to `application_preview_llm()`, and assert the raw ID is absent
  while opaque card refs remain present.

## Previous Issue Status

- ISSUE-1: RESOLVED - verified draft provenance remains server-composed and selection-linked.
- ISSUE-2: RESOLVED - blind-hiring content is sanitized through the unified projection path.
- ISSUE-3: RESOLVED - safe fallback reason handling remains tested.
- ISSUE-4: RESOLVED - rationale and assumptions remain rendered.
- ISSUE-5: RESOLVED - initial Cycle 21 documents exist; ISSUE-10 concerns new v3 changes.
- ISSUE-6: RESOLVED - cache isolation remains covered.
- ISSUE-7: REGRESSION - amendment documentation was previously aligned for v1/v2, but has
  not been updated for the v3 public behavior.
- ISSUE-8: RESOLVED - advisory visible strings are centralized through `_sanitize_advisory`.
- ISSUE-9: RESOLVED - field-level card sanitization and opaque blind-mode provenance are
  implemented, with a missing required provider-ID regression test noted in ISSUE-11.

## Regression Check

The v3 implementation introduces `_build_safe_projection()` and `_sanitize_advisory()`,
uses opaque blind-mode card references, supports partial redaction, rejects an empty safe
projection before provider invocation, and suppresses identity-bearing competency assertions
in verified drafts. No new functional privacy leak was reproduced in the reviewed paths.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Unified projection is used before mock and LLM processing | PASS | `scripts/dashboard.py` routes both paths through `_build_safe_projection()`. |
| Blind-mode provider/preview provenance uses opaque refs | PARTIAL | Code path implemented; mandatory provider-ID regression test missing, ISSUE-11. |
| Card/provider protected content is sanitized | PASS | v6/v3 adversarial tests and centralized advisory sanitizer pass. |
| Target context remains context and is not asserted as applicant background | PASS | Mock and LLM competency-policy tests pass. |
| Partial sanitization succeeds; empty safe projection returns 422 before LLM | PASS | Field-level and all-redacted tests pass. |
| Public documentation describes the implemented contract | FAIL | ISSUE-10. |

## Automatic Checks

- `uv run pytest -v`: PASS (`465 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

No unrelated implementation scope expansion identified. Amendment v3 and advisor
`step-003.md` through `step-005.md` are authorized escalation artifacts. Hook-owned
`status.txt=escalated` and unrelated untracked local skill/read-counter files are excluded
from implementation findings.

---

## RESOLVED

### Issue Classification
- ISSUE-10: APPLY
- ISSUE-11: APPLY

### Applied

RESOLVED: ISSUE-10 — Updated three public contract documents to describe Amendment v3 blind-hiring behavior
- `requirements-dashboard.md:627-629`: replaced superseded "Blind-hiring pre-provider check" bullet with v3 unified projection description (per-field screening, safe display label, opaque refs `C1`/`C2`, partial-success → 200 + warning, all-excluded → HTTP 422, `_sanitize_advisory` scope covering all four advisory fields, `target_context.competency` assertion policy).
- `docs/test-cases.md:197` (PT-APP-006): updated expected result to describe per-field screening, 422 on all-excluded, opaque refs in provider payload and preview, full advisory sanitization, and competency assertion policy.
- `docs/acceptance-studio.md:96` (row 7): updated expected result to describe per-field screening, safe display label `Evidence C1`, opaque canonical-ID replacement, 422 when all cards have no usable field, and serialized JSON absence assertion. Row 8 unchanged.

RESOLVED: ISSUE-11 — Added provider-route regression test for identity-bearing canonical card ID
- `tests/test_cycle21.py`: added `test_blind_hiring_opaque_card_id_in_provider_payload` using `opaque_id_client` fixture (card `alumni-program-2024`) with configured Anthropic provider. Captures `fact_ledger` passed to `application_preview_llm()` and asserts: canonical ID absent from `source_card_id` values; opaque ref `C1` present; returned preview `fact_ledger` also uses opaque refs; serialized preview JSON does not contain canonical ID.

自動 체크: pytest ✅ 466 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
