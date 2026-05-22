# Step 047 — Cycle-14 LLM Refine Adapter Approach check

Cycle: 14
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. studio_refine_llm in scripts/llm.py — reuses _call/cache/LLMError; correct layering.
2. Accept client= param AND monkeypatch _build_client — param for unit isolation, default path tests wiring.
3. Reuse cache pattern keyed on hash(raw_text+intent) — saves cost.
4. Fallback to _mock_refine on LLMError/no-key — transparent degradation, 200-response contract preserved.
5. Validate before returning: type whitelist, summary cap, required-field presence; malformed → LLMError.
6. Add refine_source to BOTH paths; assert in tests + CardRepo validation test.

## Sonnet Response
- studio_refine_llm in llm.py with client= injection.
- Cache keyed on raw_text+intent.
- LLMError → fallback to mock (log warning).
- Validate LLM output fields before return.
- refine_source added to both paths.
- 구현 시작.
