# Cycle 15 Plan: AI Status, `.env` Loading, and Refine Source Visibility

Branch: feature/cycle-15-ai-status-env-refine-source

## Summary

Cycle 14 connected Studio refinement to an optional Anthropic-backed LLM path with deterministic mock fallback. Cycle 15 should make that connection visible and safer to operate locally:

- allow local `.env` loading for `ANTHROPIC_API_KEY`
- keep API keys server-side only
- expose AI connection/fallback status to the Studio UI
- show whether a generated preview came from `llm` or `mock`

This cycle is about configuration and observability, not prompt quality. Consultant-style prompt harness improvements stay out of scope and should be planned separately in Cycle 16.

## Input/Output Spec

- Input:
  - server startup via `uv run pcli dashboard`
  - optional `.env` file at repo root containing `ANTHROPIC_API_KEY=...`
  - `GET /api/studio/ai-status`
  - existing `POST /api/studio/refine`
- Output:
  - `.env` values are loaded on server startup or dashboard module import, without requiring code edits.
  - `.env` and local variants are gitignored.
  - `GET /api/studio/ai-status` returns no secret values.
  - Suggested response:
    - `{ ok: true, configured: bool, provider: "anthropic", mode: "llm" | "mock", model: string | null }`
  - Studio UI shows compact status:
    - `AI: connected`
    - `AI: mock fallback`
    - `API key not configured`
  - Studio preview displays `refine_source` as a small non-editable indicator.
- Failure:
  - malformed `.env` or missing key must not prevent dashboard startup.
  - status endpoint must not leak the API key or any prefix/suffix of it.

## Key Changes

- Configuration:
  - Add lightweight `.env` loading for local dashboard/server usage.
  - Prefer `python-dotenv` only if already available; otherwise implement a tiny safe parser for simple `KEY=value` lines.
  - Do not overwrite an environment variable that is already set.
  - Add `.env`, `.env.local`, and similar local env files to `.gitignore`.
- API:
  - Add `GET /api/studio/ai-status`.
  - Return whether `ANTHROPIC_API_KEY` is configured and which refine mode Studio will attempt.
  - Do not return secrets.
- Studio UI:
  - Fetch AI status on load.
  - Render status in the Studio header or capture panel.
  - Render preview source after refine:
    - `Source: LLM`
    - `Source: Mock`
  - Keep the UI compact; do not add an API-key input field.
- Tests:
  - `.env` loading sets env value when not already set.
  - existing env value is not overwritten by `.env`.
  - `.gitignore` includes `.env` patterns.
  - status endpoint reports configured/unconfigured modes.
  - status endpoint does not include the key value.
  - Studio HTML/JS contains status and refine-source hooks.

## Sprint Contract

- Passing criteria:
  - Dashboard still starts without `.env`.
  - `.env` can configure `ANTHROPIC_API_KEY` for local use.
  - Existing environment value takes precedence over `.env`.
  - `/api/studio/ai-status` works and never leaks secret material.
  - Studio displays AI connection/fallback status.
  - Studio displays `refine_source` after preview generation.
  - No browser-side API key input or storage is added.
  - Existing LLM refine fallback tests remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test cases:
  - `.env` file with `ANTHROPIC_API_KEY=fake` is loaded in a temp repo/import-safe path.
  - pre-set `ANTHROPIC_API_KEY` is not overwritten.
  - `/api/studio/ai-status` returns mock/unconfigured when key absent.
  - `/api/studio/ai-status` returns configured/llm when key present.
  - response JSON never contains the actual key.
  - Studio static JS fetches `/api/studio/ai-status`.
  - Studio preview renders `refine_source` indicator from refine response.
- Manual acceptance:
  - Start without `.env`, open `/studio`, confirm mock/fallback status.
  - Add local `.env` with key, restart, confirm connected status.
  - Generate preview and confirm source indicator shows LLM or Mock.
- Gas limit: N/A
- Slither: N/A

## Missing Edge Case Candidates

- `.env` contains quotes, comments, or blank lines.
- `.env` exists but `ANTHROPIC_API_KEY` is empty.
- A real LLM call fails even though key is configured; refine source should still show mock fallback for that preview.

## Simpler Alternative

Only document the PowerShell environment variable command and skip `.env`/status UI.

This is simpler, but it leaves the user unable to tell whether Studio actually used LLM or mock fallback. Cycle 15 should make that state visible without exposing secrets.

## Assumptions

- The tool remains local-only and solo-use.
- API keys are never entered in the browser.
- `.env` is local configuration and must not be committed.
- Cycle 15 does not change the Studio prompt harness or LLM output schema.
- Cycle 16 should handle consultant/portfolio-maker prompt redesign.

## Review Guidance

### Enumeration Needed

- Secret handling:
  - Search: `rg 'ANTHROPIC_API_KEY|api-key|api_key|secret|\\.env' scripts tests templates .gitignore`
  - Expected: key is read server-side only; no template/JS contains or receives key value.
- Status API:
  - Search: `rg 'ai-status|refine_source|configured|mock fallback|connected' scripts tests`
  - Expected: endpoint, UI hook, and tests present.
- Prompt scope:
  - Search: `git diff main..HEAD -- scripts/llm.py`
  - Expected: no prompt-harness redesign in this cycle unless strictly required for source/status.

### Verification Method Guide

- Use monkeypatch/temp files for `.env` tests; do not require a real API key.
- Inspect response JSON to ensure no secret value is present.
- Existing LLM tests should continue to verify fallback and fake-client behavior.
- UI tests can assert hook/copy presence; browser automation is not required for this small cycle.
