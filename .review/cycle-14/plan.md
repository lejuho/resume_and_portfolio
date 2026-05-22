# Cycle 14 Plan: Studio LLM Refine Adapter With Mock Fallback

Branch: feature/cycle-14-studio-llm-refine-adapter

## Summary

Studio currently proves the full review workflow, but its refinement is still deterministic and simplistic. Cycle 14 should introduce an optional LLM-backed refinement adapter for `/api/studio/refine` while preserving the existing deterministic mock fallback when no API key or LLM dependency is available.

The product goal is to move closer to the intended service:

```text
messy career material -> AI structured draft -> human edit -> saved card -> outputs
```

This cycle must not make Studio dependent on live API availability. Local deterministic behavior remains the default fallback and test path.

## Input/Output Spec

- Input:
  - `POST /api/studio/refine`
    - JSON: `{ "raw_text": string, "intent": "resume" | "portfolio" | "both" }`
  - Optional environment:
    - `ANTHROPIC_API_KEY`
- Output:
  - Success response shape remains unchanged:
    - `{ ok, draft, missing_info }`
  - When LLM is available and succeeds:
    - title/type/summary/tags/metrics/evidence/resume bullet/portfolio body may be LLM-derived
    - response includes a non-breaking source marker such as `draft.refine_source = "llm"`
  - When LLM is unavailable or fails safely:
    - current mock behavior remains available
    - response includes `draft.refine_source = "mock"`
- Failure:
  - Empty raw text still returns `400`.
  - Invalid intent still returns `400`.
  - Malformed LLM response must not crash the server; fallback to mock or return a controlled error according to implementation choice.

## Key Changes

- LLM adapter:
  - Add a Studio-specific refine helper, preferably in `scripts/llm.py` or a small new module.
  - Reuse existing Anthropic client/cache patterns where practical.
  - Prompt for a strict JSON object matching Studio draft needs:
    - title
    - type
    - summary
    - tags
    - metrics
    - evidence candidates
    - resume bullet when requested
    - portfolio blocks/body when requested
    - missing info prompts
  - Enforce deterministic tests through fake client injection or monkeypatching.
- Dashboard server:
  - Update `/api/studio/refine` to try LLM refinement only when configured.
  - Preserve mock fallback path.
  - Keep `/api/studio/save` unchanged except for accepting the same draft shape.
- Safety:
  - Validate/normalize LLM output before returning it to the UI.
  - Do not persist raw input.
  - Do not let LLM choose duplicate-id behavior; save endpoint remains responsible for duplicate rejection.
  - Do not let LLM introduce visual paths or uploads in this cycle.
- Tests:
  - Keep existing mock refine tests green without needing an API key.
  - Add fake-client tests for successful LLM refine.
  - Add malformed-LLM-response fallback/error test.
  - Add test that LLM output still saves as a valid draft card.

## Sprint Contract

- Passing criteria:
  - Existing `/studio` mock flow works without `ANTHROPIC_API_KEY`.
  - `/api/studio/refine` can return LLM-derived draft data through a fake client in tests.
  - Response shape remains compatible with existing Studio JS.
  - Malformed LLM output does not produce a 500.
  - Raw pasted input is still not persisted by default.
  - Saved LLM-derived draft passes `CardRepo` validation.
  - No visual upload/path editing is introduced.
  - Existing dashboard and build behavior remains unchanged.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test cases:
  - refine without API key uses mock fallback and returns `refine_source = "mock"`.
  - fake LLM refine returns `refine_source = "llm"`.
  - fake LLM `resume` intent returns resume bullet.
  - fake LLM `portfolio` intent returns portfolio body/blocks.
  - fake LLM `both` intent returns both.
  - malformed LLM JSON does not crash and falls back or returns controlled error.
  - LLM-derived draft can be saved and validates.
  - raw input from an LLM refine request is not written into saved MDX unless it appears as transformed output.
- Manual acceptance:
  - With no API key, `/studio` behaves exactly like the current mock-backed version.
  - With API key configured, paste messy career text and confirm preview is more meaningful than first-line mock behavior.
  - Edit the generated draft and save.
  - Run `uv run pcli validate`.
- Gas limit: N/A
- Slither: N/A

## Missing Edge Case Candidates

- LLM returns valid JSON but invalid card type or overlong summary.
- LLM omits title or returns a title that slugifies to an existing card id.
- LLM includes raw sensitive notes verbatim in portfolio body.

## Simpler Alternative

Call the existing `suggest_card_from_text()` helper directly and keep mock resume/portfolio text.

This is simpler but insufficient: Studio's value depends on output-intent-aware resume bullets and portfolio narratives, not only frontmatter extraction.

## Assumptions

- Anthropic integration remains optional.
- Tests should not require real network/API access.
- Existing `.cache/llm` behavior may be reused if it does not complicate tests.
- Cycle 14 does not add model settings UI.
- Cycle 14 does not add file upload, visual picking, or existing-card update.

## Review Guidance

### Enumeration Needed

- Refine paths:
  - Search: `rg 'api_studio_refine|_mock_refine|refine_source|studio.*llm|suggest_card' scripts tests`
  - Expected: both mock and LLM paths covered.
- Error handling:
  - Search: `rg 'LLMError|Malformed|fallback|refine_source' scripts tests`
  - Expected: malformed LLM result cannot bubble into 500.
- Persistence:
  - Search: `rg 'raw_text|portfolio_body|CardRepo|api_studio_save' tests scripts`
  - Expected: raw input non-persistence still tested.
- Routes:
  - Search: `rg '@app.route' scripts/dashboard.py`
  - Expected: no new route required.

### Verification Method Guide

- Fake-client tests are required for the LLM path; do not rely on live API.
- Mock fallback must be tested with API key absent or LLM disabled.
- Save validation must use actual temporary MDX writes and `CardRepo`, not response JSON alone.
- UI tests only need compatibility with the existing response shape; this cycle is mostly server/refine logic.
