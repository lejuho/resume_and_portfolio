# Cycle 17 Plan: AI Provider Configuration

Branch: feature/cycle-17-ai-provider-config

## Summary
Cycle 16 improved the Studio prompt harness. Cycle 17 should make the AI integration provider-aware without putting API keys into the browser UI.

The goal is a small provider configuration layer that keeps the current Anthropic behavior working, allows explicit local provider selection, and leaves room for OpenAI or other providers in later cycles.

## Input / Output Spec
- Input:
  - Server environment variables loaded from OS env, `.env`, or `.env.local`.
  - Supported in this cycle:
    - `AI_PROVIDER=anthropic`
    - `ANTHROPIC_API_KEY`
    - `AI_API_KEY` as an Anthropic-compatible alias
    - optional `AI_MODEL` override
  - Existing Studio endpoint: `POST /api/studio/refine`
- Output:
  - `/api/studio/ai-status` reports provider, model, configured state, and mode without exposing secrets.
  - LLM refine uses the resolved provider/model config.
  - Unsupported providers fail clearly and fall back to mock in Studio refine.
  - Existing CLI LLM calls still work for Anthropic.

## Key Changes
- Backend: introduce a small provider config resolver in `scripts/llm.py`.
  - Resolve provider from `AI_PROVIDER`, default `anthropic`.
  - Resolve model from `AI_MODEL`, default current `MODEL`.
  - Resolve key from provider-specific key first, then `AI_API_KEY` alias.
  - Do not log, return, or serialize API key values.
- Backend: update Anthropic client path to use resolved provider config.
  - Keep current Anthropic implementation as the only actual provider in this cycle.
  - If `AI_PROVIDER` is not `anthropic`, raise a clear `LLMError`.
  - Keep cache keys provider/model aware.
- Dashboard: update `/api/studio/ai-status`.
  - Show configured provider and model.
  - For unsupported providers, return configured false or mode mock with a safe status message.
  - Do not add browser-side key input.
- Tests:
  - provider default is Anthropic.
  - `ANTHROPIC_API_KEY` works.
  - `AI_API_KEY` alias works.
  - `AI_MODEL` override appears in status and cache payload behavior where testable.
  - unsupported provider does not leak secrets and Studio refine falls back to mock.
  - existing Cycle 15/16 tests still pass.

## Sprint Contract
- Passing Criteria:
  - Existing Anthropic Studio refine path remains functional.
  - Existing CLI LLM helpers still raise clear errors when no key is configured.
  - `/api/studio/ai-status` never returns API key text.
  - `AI_PROVIDER=anthropic` and unset `AI_PROVIDER` behave the same.
  - `AI_API_KEY` remains accepted as a generic local alias.
  - `AI_MODEL` can override the displayed and requested model.
  - Unsupported provider values do not crash `/api/studio/refine`; Studio falls back to mock.
  - No OpenAI SDK, provider router implementation, model picker UI, or frontend key entry is added in this cycle.
- Automatic Checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test Cases:
  - Unit: provider config defaults to Anthropic and default model.
  - Unit: Anthropic key and generic key resolution.
  - Unit: unsupported provider raises `LLMError` from client construction.
  - Unit: cache key changes when provider/model changes.
  - API: `/api/studio/ai-status` reports provider/model without secrets.
  - API: unsupported provider plus key returns safe mock status.
  - API: `/api/studio/refine` falls back to mock for unsupported provider.
  - Regression: Cycle 16 consultant prompt tests still pass.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Both `ANTHROPIC_API_KEY` and `AI_API_KEY` are set with different values.
- `AI_PROVIDER` has whitespace or uppercase input such as `Anthropic`.
- `AI_MODEL` is set to an empty string.

## Simpler Alternative
Keep only `ANTHROPIC_API_KEY` / `AI_API_KEY` checks scattered in the dashboard and LLM modules. This is faster, but it makes adding a second real provider messy and increases the risk of inconsistent status/refine behavior.

## Assumptions
- Anthropic remains the only live provider implemented in Cycle 17.
- `AI_API_KEY` is treated as a generic alias only when the selected provider supports it.
- Frontend displays provider/model status but never accepts or stores credentials.
- Provider-specific prompt differences are out of scope; Cycle 16 harness remains the source of prompt behavior.

## Review Guidance
### Enumeration Required
- Provider/key resolution call sites:
  - Search: `rg "ANTHROPIC_API_KEY|AI_API_KEY|AI_PROVIDER|AI_MODEL|MODEL|_build_client" scripts tests`
  - Expected areas: `scripts/llm.py`, `scripts/dashboard.py`, Cycle 15/16 tests, new Cycle 17 tests.
- Studio status/refine:
  - Search: `rg "api_studio_ai_status|api_studio_refine|studio_refine_llm|refine_source" scripts tests`
- Cache payload behavior:
  - Search: `rg "schema_ver|model|studio_refine|_cache_key" scripts tests`

### Verification Method Guide
- Provider selection should be tested with environment monkeypatching, not live API calls.
- Secret non-leak checks should inspect JSON response text.
- Unsupported provider fallback must be verified through `/api/studio/refine`, because direct `_build_client()` should still raise `LLMError`.
- Do not require browser/manual UI testing unless the status text shape changes in `studio.js`.
