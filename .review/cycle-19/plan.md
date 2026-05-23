# Cycle 19 Plan: Studio AI Connection Check

Branch: feature/cycle-19-ai-connection-check

## Summary
Cycle 18 added Google Gemini as a real provider, but Studio still only shows whether a key is configured and silently falls back to mock when the provider call fails. Cycle 19 should add an explicit Studio connection check so the user can verify the current server-side API key/model before generating a draft.

The goal is to distinguish:
- no usable key configured
- key configured but not live-verified
- live check passed
- live check failed with a safe, useful reason

No API keys should ever be entered in or exposed to the browser.

## Input / Output Spec
- Input:
  - Existing server-side provider env:
    - `AI_PROVIDER`
    - provider key vars such as `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `AI_API_KEY`
    - optional `AI_MODEL`
  - New endpoint:
    - `POST /api/studio/ai-check`
    - No request body required.
- Output:
  - Success:
    ```json
    {
      "ok": true,
      "connected": true,
      "provider": "google",
      "model": "gemini-2.5-flash",
      "message": "Connection check passed"
    }
    ```
  - Failure:
    ```json
    {
      "ok": false,
      "connected": false,
      "provider": "google",
      "model": "gemini-2.5-flash",
      "error_code": "auth_failed",
      "message": "Authentication failed. Check the configured API key."
    }
    ```
  - Failure responses must not include secret values, raw provider stack traces, or raw API response bodies.

## Key Changes
- Backend: add a minimal live-check helper in `scripts/llm.py`.
  - Suggested name: `check_provider_connection()`.
  - Resolve current provider config.
  - Reject missing/placeholder key before any network call.
  - Make a very small provider call using the current provider/model.
  - Anthropic: use existing Anthropic client path with a tiny prompt.
  - Google: use existing Google adapter with a tiny prompt.
  - Return normalized status dict or raise/convert to safe `LLMError`.
- Backend: add `POST /api/studio/ai-check` in `scripts/dashboard.py`.
  - Calls `check_provider_connection()`.
  - Maps known failures to safe `error_code` values:
    - `not_configured`
    - `unsupported_provider`
    - `auth_failed`
    - `quota_or_rate_limit`
    - `network_error`
    - `provider_error`
  - Does not expose API keys.
- Frontend: update Studio UI.
  - Add `Check AI connection` button near the existing AI status text.
  - Button calls `/api/studio/ai-check`.
  - Show `AI: verified` on success.
  - Show `AI: configured, check failed` or similar on failure.
  - Keep existing `Source: LLM` / `Source: Mock` generation output.
  - Do not run live checks automatically on page load.
- Tests:
  - Fake provider calls only; no live API in automated tests.
  - Endpoint success/failure shapes.
  - UI button and JS fetch hooks.
  - Secret non-leak checks.
  - Existing Google/Anthropic provider tests still pass.

## Sprint Contract
- Passing Criteria:
  - `/api/studio/ai-status` remains a cheap configured/mock status check.
  - `/api/studio/ai-check` performs the only live verification path.
  - Studio has a visible connection-check button.
  - A successful fake Google check returns `connected: true`.
  - A successful fake Anthropic check returns `connected: true`.
  - Missing/placeholder key returns a safe non-connected response without attempting provider calls.
  - Provider/auth/quota/network failures return safe messages and do not leak secrets.
  - The live check is not triggered automatically on page load.
  - Existing refine mock fallback behavior remains unchanged.
- Automatic Checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test Cases:
  - Unit: `check_provider_connection()` success with fake Google client.
  - Unit: `check_provider_connection()` success with fake Anthropic client.
  - Unit: missing key returns/raises `not_configured`.
  - Unit: provider exception maps to safe error classification.
  - API: `POST /api/studio/ai-check` success response does not leak key.
  - API: `POST /api/studio/ai-check` failure response does not leak raw provider error containing key-like text.
  - UI: `studio.html` includes check button.
  - UI: `studio.js` calls `/api/studio/ai-check` only from button click, not from `DOMContentLoaded`.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Provider SDK raises an exception class without stable type/message across versions.
- A provider returns an empty text response despite successful HTTP status.
- User checks connection successfully, then changes `.env` without server restart and sees stale process env.

## Simpler Alternative
Trigger a tiny live API check inside `/api/studio/ai-status` on every page load. This is simpler, but it creates hidden latency/cost/rate-limit risk and makes merely opening Studio call an external API. Use an explicit button instead.

## Assumptions
- Live connection check is user-triggered and may consume a small amount of provider quota.
- The endpoint may call external APIs in manual use, but automated tests must fake provider clients.
- `.env` still requires dashboard server restart to reload changed values.
- The purpose is diagnosis and confidence, not full observability or provider billing introspection.

## Review Guidance
### Enumeration Required
- Status/check/refine endpoints:
  - Search: `rg "api_studio_ai_status|api_studio_ai_check|api_studio_refine|ai-check|ai-status" scripts tests`
  - Confirm only `ai-check` performs live provider verification.
- Provider call helpers:
  - Search: `rg "check_provider_connection|_build_client|_call|generate_content|messages.create|LLMError" scripts/llm.py tests`
  - Confirm errors are normalized before reaching JSON responses.
- Secret handling:
  - Search: `rg "api_key|ANTHROPIC_API_KEY|GOOGLE_API_KEY|GEMINI_API_KEY|AI_API_KEY|secret" scripts tests`
  - Confirm no key values are included in response bodies.
- Frontend hooks:
  - Search: `rg "ai-check|ai-status|Check AI connection|DOMContentLoaded" scripts/static scripts/templates tests`

### Verification Method Guide
- Use fake clients and monkeypatches for provider success/failure.
- Do not require a real Google or Anthropic API key in automated checks.
- For manual acceptance, user can put a real Google key in `.env`, restart dashboard, click `Check AI connection`, and then generate a preview.
