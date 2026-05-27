# Advisor Feedback: Cycle 21 Completion Check

Type: Completion check
Scope: scripts/dashboard.py, scripts/llm.py, tests/test_cycle21.py
Implementation commits: cb18354..0080228 (review-v3 through review-v5 fixes)
Plan baseline: Escalation Amendment v1 (plan.md)

## Validation Results

1. VERIFIED — `_build_fact_ledger` executes before the `if can_try_llm` block; the
   `not _id_flagged` guard prevents any identity-flagged card text from reaching the
   provider. Route falls through to mock with `fallback_reason=None` on flag.

2. VERIFIED — `answer_draft` is always assigned via `_compose_answer_draft()` using
   `_safe_titles` (activity-kind ledger entries) and submitted `target_context` fields only.
   LLM free prose cannot reach this field in either the LLM or mock path.

3. VERIFIED — Unknown/adversarial `selected_fact_ids` are discarded by set intersection
   with `_valid_ids_set`. Selection then expands to include the activity-kind entry for
   every represented `source_card_id`, so `selected_facts` traces to every factual string
   present in the server-composed draft.

4. VERIFIED — Under `blind_hiring=True`, `_ai_guidance` is filtered through `_IDENTITY_RE`
   after the provider call; withheld entries trigger `BLIND_HIRING_GUIDANCE_REDACTED` in
   `missing_info`. Guard runs on the advisory list before the response is serialized.

5. VERIFIED — Cache payload at `scripts/llm.py:733` uses `"fact_ledger": fact_ledger`
   (full dict list). `_cache_key` serializes via `json.dumps(payload, sort_keys=True)`;
   two ledgers with the same positional ID but different `text` or `source_card_id`
   produce distinct SHA-256 keys.

6. VERIFIED — 72 tests pass; `uv run ruff check scripts tests` reports all checks passed;
   `uv run ruff format --check scripts tests` reports 28 files already formatted.

## Decision

All six completion criteria satisfied. No implementation changes needed from this pass.

Advisor note: The two items initially flagged as RISK were resolved by reading
`scripts/llm.py:733` and executing the test suite. Both concerns cleared on first check.
