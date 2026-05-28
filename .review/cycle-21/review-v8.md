# Codex Review v8

## Verdict
BLOCKED

## Findings

### ISSUE-10 [MEDIUM] Amendment v3 documentation remains internally inconsistent and incomplete
- Location: `requirements-dashboard.md:616-637`, `docs/acceptance-studio.md:96-97`
- Analysis: The revised v3 bullet correctly documents sanitized facts, opaque references,
  partial success, HTTP 422, and `_sanitize_advisory`. However, the preceding requirement
  still says the provider receives "only ledger IDs, never raw card text", while
  `application_preview_llm()` receives and prompts with sanitized ledger text. Manual
  acceptance row 8 still checks only `ai_guidance`, although v3 and the code screen
  `question_intent`, `competency_target`, and `missing_info[].message` as visible advisory
  surfaces too.
- Impact: The published trust-boundary contract misstates what sanitized personal evidence is
  sent to the provider and does not provide a manual acceptance step for the full advisory
  sanitizer. ISSUE-10 is therefore only partially resolved.
- Fix direction: Replace the provider-input description with the actual sanitized
  fact-text-plus-opaque-reference contract, and extend acceptance row 8 to check all
  `_sanitize_advisory` visible fields and the corresponding safe warning behavior.

## Previous Issue Status

- ISSUE-1: RESOLVED - server-composed draft/provenance behavior remains covered.
- ISSUE-2: RESOLVED - unified projection prevents card-derived blind-hiring leakage.
- ISSUE-3: RESOLVED - safe fallback reason handling remains green.
- ISSUE-4: RESOLVED - review UI continues to render rationale and assumptions.
- ISSUE-5: RESOLVED - initial documentation exists; remaining mismatch is tracked in ISSUE-10.
- ISSUE-6: RESOLVED - advisory cache separation remains covered.
- ISSUE-7: UNRESOLVED - document alignment regressed into ISSUE-10 and remains incomplete.
- ISSUE-8: RESOLVED - advisory visible-string sanitizer coverage passes.
- ISSUE-9: RESOLVED - per-field projection and opaque reference behavior passes.
- ISSUE-10: UNRESOLVED - v3 docs were updated partially, but still contain the contradictions above.
- ISSUE-11: RESOLVED - provider-input opaque-reference regression test was added and passes.

## Regression Check

No new functional regression identified. The v7 resolution adds the missing configured-provider
opaque-ID coverage, and all v3 boundary tests pass. Remaining issue is contract documentation.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Unified safe projection and advisory sanitization | PASS | Code and adversarial tests pass. |
| Blind-mode opaque provenance in preview and provider payload | PASS | New provider capture test passes. |
| Partial sanitization and empty-projection 422 behavior | PASS | Field-level and all-redacted tests pass. |
| Target context not asserted as applicant background | PASS | Mock and LLM competency tests pass. |
| Public/manual contract matches implemented behavior | FAIL | ISSUE-10. |

## Automatic Checks

- `uv run pytest -v`: PASS (`466 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

No unrelated implementation scope expansion identified. Amendment v3 and advisor
`step-003.md` through `step-006.md` are authorized escalation artifacts. Hook-owned
`status.txt=escalated` and unrelated untracked local skill/read-counter files are excluded
from implementation findings.

---

## RESOLVED

### Issue Classification
- ISSUE-10: APPLY

### Applied

RESOLVED: ISSUE-10 — Corrected provider-input description and extended advisory sanitizer acceptance step
- `requirements-dashboard.md:618`: replaced "The provider receives only ledger IDs, never raw card text." with the accurate contract — blind mode sends sanitized ledger entries (id, kind, text, opaque `source_card_id` `C1`/`C2`…); non-blind mode sends full ledger text with canonical IDs.
- `docs/acceptance-studio.md:97` (row 8): retitled "Blind-hiring: guidance screen" → "Blind-hiring: advisory sanitizer"; action extended to trigger identity content in all four fields (`question_intent`, `competency_target`, `missing_info[].message`, `ai_guidance[]`); expected result extended to specify "withheld" sentinel replacement for the first three, `BLIND_HIRING_ADVISORY_REDACTED` warning, `ai_guidance` item drop, `BLIND_HIRING_GUIDANCE_REDACTED` warning, and full absence of identity/background phrases from every advisory visible field.

자동 체크: pytest ✅ 466 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
