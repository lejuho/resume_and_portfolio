# Step 055 — Cycle-18 Approach check

Cycle: 18
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Keep `_call()` single function; dispatch internally via `isinstance(client, ...)` check — one `if` branch each for Anthropic vs Google. Minimal, no new abstractions.
2. Extend `resolve_provider_config()` to resolve `api_key` per provider: `if provider == "google"` use `GOOGLE_API_KEY → GEMINI_API_KEY → AI_API_KEY` chain. Return same `api_key` key — callers unchanged.
3. Wrap `response.text` access in `try/except AttributeError` plus `if not text` → `raise LLMError("google: empty response (safety filter or blocked)")`. Two lines, no over-engineering.

## Sonnet Response
- Extend `resolve_provider_config()` with per-provider key chain and default model.
- Add `google` to `_SUPPORTED_PROVIDERS`.
- Extend `_build_client()` to instantiate a Google client.
- Add isinstance dispatch in `_call()` for Google response shape.
- Write `tests/test_cycle18.py` with fake Google client.
- 구현 시작.
