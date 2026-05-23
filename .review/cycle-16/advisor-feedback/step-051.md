# Step 051 — Cycle-16 Approach check

Cycle: 16
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. New narrative fields (problem/framing/approach/outcome/insight/decisions_tradeoffs): top-level draft keys, not only embedded in portfolio_body. portfolio_body should also contain them as narrative prose, not copy-paste.
2. Bump _SCHEMA_VER to 2 — invalidates stale cache. Tests monkeypatch _cache_read → None, so safe.
3. Keep single user message pattern (_call unchanged). Add consultant role persona in prompt preamble; system message not needed.

Concerns answered:
- studio.html not rendering new fields: OK for cycle 16; draft JSON carries them, editor ignores unknown keys.
- Prompt instruction "do not copy raw notes into portfolio_body" is sufficient; normalization cannot enforce prose quality.
- _SCHEMA_VER bump safe given test fixtures.

## Sonnet Response
- Bump _SCHEMA_VER to 2.
- Rewrite _STUDIO_REFINE_PROMPT with consultant persona and new required fields.
- Add normalization for problem/framing/approach/outcome/insight/decisions_tradeoffs in studio_refine_llm.
- Add new fields as top-level draft keys.
- Write focused tests for prompt content, field mapping, and normalization.
- 구현 시작.
