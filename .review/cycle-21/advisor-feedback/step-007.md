# Advisor Feedback: Cycle 21 Step-007 — review-v8 ISSUE-10

Type: Approach check + Completion check
Scope: requirements-dashboard.md, docs/acceptance-studio.md
Plan baseline: Escalation Amendment v3 (plan.md)

## Approach Check (before implementation)

Query: requirements-dashboard.md replacement scope; acceptance-studio.md row 8 extension scope.

Key guidance received:
1. Fix 1: replace line 618 only; keep surrounding sentence context.
2. Fix 1 wording: state sanitized ledger entries (id, kind, text, opaque source_card_id) in
   blind mode; full text and canonical IDs in non-blind mode.
3. Fix 2: extend both action and expected result for full coverage.
4. Fix 2 action: trigger sanitization across all four advisory fields (question_intent,
   competency_target, missing_info[].message, ai_guidance[]).
5. Fix 2 expected: identity-bearing values become "withheld" sentinel; emit
   BLIND_HIRING_ADVISORY_REDACTED for the first three fields; BLIND_HIRING_GUIDANCE_REDACTED
   when ai_guidance items are dropped.

Decision: Applied all five guidance points.

## Completion Check (after implementation)

Changes:
- `requirements-dashboard.md:618` — replaced "The provider receives only ledger IDs, never
  raw card text." with the accurate contract: blind mode → sanitized entries with opaque
  source_card_id; non-blind mode → full ledger text with canonical IDs.
- `docs/acceptance-studio.md:97` (row 8) — retitled scenario from "Blind-hiring: guidance
  screen" to "Blind-hiring: advisory sanitizer"; extended action to trigger all four advisory
  fields; extended expected result to specify "withheld" sentinel replacement for
  question_intent / competency_target / missing_info[].message, BLIND_HIRING_ADVISORY_REDACTED
  warning, ai_guidance drop, BLIND_HIRING_GUIDANCE_REDACTED warning, and absence of all
  identity/background phrases from every advisory visible field.

Regression risks verified:
1. No code changes; tests unchanged. 466 tests still pass. ✓
2. Surrounding text in requirements-dashboard.md unmodified; only the inaccurate sentence
   replaced. ✓
3. Acceptance row numbers unchanged; no other rows affected. ✓

## Decision

PROCEED. 466 tests pass. All checks green. ISSUE-10 fully resolved.

Auto checks: pytest ✅ 466 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
