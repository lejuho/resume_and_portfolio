# Cycle 18 Plan: Google Gemini Provider Adapter

Branch: feature/cycle-18-google-gemini-provider

## Summary
Cycle 17 introduced provider-aware configuration but kept Anthropic as the only implemented live provider. Cycle 18 should add a real Google Gemini provider path so the user can run Studio refinement with Google AI Studio credits.

The goal is to support:

```env
AI_PROVIDER=google
GOOGLE_API_KEY=<key>
AI_MODEL=gemini-2.5-flash
```

No browser-side key entry should be added.

## Input / Output Spec
- Input:
  - Environment variables loaded server-side:
    - `AI_PROVIDER=google`
    - `GOOGLE_API_KEY` or `GEMINI_API_KEY`
    - optional `AI_API_KEY` alias for the selected provider
    - optional `AI_MODEL`, defaulting to a safe Gemini model for Google
  - Existing LLM callers:
    - `studio_refine_llm`
    - `score_cards`
    - `rewrite_summary`
    - `suggest_card_from_text`
- Output:
  - Google provider returns plain text response content compatible with existing JSON parsing.
  - `/api/studio/ai-status` reports `provider: google`, configured state, mode, and model without secrets.
  - Unsupported/misconfigured providers continue to fall back to mock in Studio refine.
  - Existing Anthropic behavior remains unchanged.

## Key Changes
- Dependency:
  - Add `google-genai` as a normal dependency if project dependency management supports it cleanly.
  - If dependency installation requires lockfile updates, keep them narrowly scoped.
- Backend: refactor `scripts/llm.py` provider boundary.
  - Extend supported providers to include `google`.
  - Resolve keys by provider:
    - Anthropic: `ANTHROPIC_API_KEY`, then `AI_API_KEY`
    - Google: `GOOGLE_API_KEY`, then `GEMINI_API_KEY`, then `AI_API_KEY`
  - Resolve default model by provider:
    - Anthropic: current `MODEL`
    - Google: `gemini-2.5-flash`
  - Keep placeholder key rejection for all providers.
  - Replace the single Anthropic-shaped `_call()` with a minimal provider adapter layer.
- Google adapter:
  - Use official `google-genai` SDK.
  - Create a Google client with the resolved key.
  - Call `models.generate_content` with the resolved model and prompt.
  - Extract response text into the same string shape Anthropic uses.
  - Raise `LLMError` with a clear message on missing package, missing key, unsupported response, or provider mismatch.
- Dashboard:
  - Keep `/api/studio/ai-status` secret-free.
  - Display configured Google provider/model as available for LLM mode.
  - No frontend key input, model picker, or live credential validation button in this cycle.
- Tests:
  - Add fake Google client tests without live API calls.
  - Keep Anthropic fake-client tests passing.
  - Add env resolution tests for `GOOGLE_API_KEY`, `GEMINI_API_KEY`, and alias fallback.
  - Add status/refine tests for Google provider.

## Sprint Contract
- Passing Criteria:
  - `AI_PROVIDER=google` with `GOOGLE_API_KEY` makes `/api/studio/ai-status` report `configured: true`, `mode: llm`, `provider: google`.
  - `GEMINI_API_KEY` works as a Google key alias.
  - `AI_API_KEY` works as a generic key alias when provider is Google.
  - `AI_MODEL` overrides the Google default model.
  - Studio refine can use a fake Google client and return `refine_source=llm`.
  - Existing Anthropic tests and behavior still pass.
  - Placeholder keys such as `your_key_here` are not treated as configured for Google.
  - No API keys are returned in JSON or rendered into browser assets.
  - No live API calls are required in automated tests.
- Automatic Checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test Cases:
  - Unit: Google provider config selects `GOOGLE_API_KEY` before aliases.
  - Unit: `GEMINI_API_KEY` fallback works.
  - Unit: Google default model is `gemini-2.5-flash` when `AI_MODEL` is absent.
  - Unit: fake Google adapter returns text from SDK response shape.
  - Unit: malformed Google response raises `LLMError`.
  - API: `/api/studio/ai-status` reports Google status without leaking key.
  - API: `/api/studio/refine` with fake Google path returns LLM source.
  - Regression: Anthropic fake path still returns LLM source.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set with different values.
- Google SDK response has candidates but no `.text` convenience property.
- The installed SDK import path differs from examples or changes method naming.

## Simpler Alternative
Use raw REST calls with `requests` instead of adding `google-genai`. This avoids an SDK dependency but increases response-shape parsing and auth handling code. Prefer the official SDK for maintainability unless dependency installation is blocked.

## Assumptions
- Google AI Studio Gemini API key is the intended Google path, not Vertex AI service-account auth.
- `AI_PROVIDER=google` is the provider selector; `gemini` may be treated as an alias only if trivial.
- Google prompt format can reuse the existing plain-text prompt harness.
- Live API smoke testing is manual and optional after automated fake-client tests pass.

## Review Guidance
### Enumeration Required
- Provider resolution:
  - Search: `rg "AI_PROVIDER|ANTHROPIC_API_KEY|GOOGLE_API_KEY|GEMINI_API_KEY|AI_API_KEY|resolve_provider_config" scripts tests`
  - Confirm all key paths are provider-specific and no secret values are serialized.
- Provider adapter calls:
  - Search: `rg "_build_client|_call|generate_content|messages.create|provider" scripts/llm.py tests`
  - Confirm Anthropic and Google call shapes are both covered.
- Dashboard behavior:
  - Search: `rg "api_studio_ai_status|api_studio_refine|refine_source|AI: configured" scripts tests`

### Verification Method Guide
- Use monkeypatched/fake clients for Google and Anthropic; no live API in tests.
- If `google-genai` cannot be installed in the environment, implementation should fail the cycle rather than silently using untested REST code unless the plan is amended.
- Status endpoint verification must inspect response text for absence of key values.
- Studio refine fallback behavior should be tested through the Flask endpoint, not only direct `scripts.llm` calls.
