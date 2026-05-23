# Step 057 — Cycle-19 Approach check

Cycle: 19
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Raise `LLMError` with `error_code` attached — don't return failure dicts. Success returns `{"status": "ok", "provider": ..., "model": ...}`; all failures raise. Keeps return type unambiguous and callers can't forget to check status fields.
2. `check_provider_connection()` attaches structured `error_code` to `LLMError`; endpoint forwards it directly. String matching is brittle across SDK versions — structured codes are the only safe boundary.
3. Use `"hi"` — single token, no safety risk, valid for both Anthropic and Google, response irrelevant (any non-exception response = connected).

## Sonnet Response
- `check_provider_connection()`: resolve config → reject bad key (not_configured) → build client → _call("hi") → return success dict; catch errors and re-raise as LLMError with error_code.
- `POST /api/studio/ai-check`: call check_provider_connection, on success return connected:true, on LLMError forward error_code.
- Studio UI: add "Check AI connection" button wired to click handler only.
- 구현 시작.
