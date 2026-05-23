# Cycle 16 Plan: Consultant Prompt Harness

Branch: feature/cycle-16-consultant-prompt-harness

## Summary
Cycle 15 made real AI usage visible and locally configurable. Cycle 16 should improve what the AI is asked to do: move Studio refinement from a simple extraction prompt toward a consultant-style portfolio and resume shaping harness.

The goal is to make `/studio` feel like it is turning rough career material into a useful career artifact, not merely summarizing text.

## Input / Output Spec
- Input:
  - Existing `POST /api/studio/refine`
  - JSON: `{ "raw_text": string, "intent": "resume" | "portfolio" | "both" }`
  - API key from server env only: `ANTHROPIC_API_KEY` or `AI_API_KEY`
- Output:
  - Normal: existing Studio-compatible draft shape with stronger consultant fields.
  - Failure:
    - Empty raw text: 400
    - Invalid intent: 400
    - LLM failure: fallback to deterministic mock refinement, preserving existing source indication.

## Key Changes
- Backend: update `scripts/llm.py` Studio prompt harness.
  - Model role: career consultant + portfolio narrative designer.
  - Ask AI to infer career value, not just restate input.
  - Require a structured JSON response with:
    - `title`
    - `type`
    - `summary`
    - `resume_bullet`
    - `portfolio_body`
    - `problem`
    - `framing`
    - `approach`
    - `outcome`
    - `insight`
    - `decisions_tradeoffs`
    - `metrics`
    - `evidence`
    - `tags`
    - `missing_info`
  - Keep response mapped to the existing Studio draft contract.
- Backend: normalize and validate LLM draft fields before returning them.
  - Whitelist card `type`, fallback to `project`.
  - Keep `summary` concise.
  - Coerce malformed `metrics`, `evidence`, `tags`, and `missing_info` into safe lists.
  - Avoid copying raw pasted notes wholesale into `portfolio_body`.
- Backend: preserve deterministic mock behavior.
  - Mock path should remain available and testable without a key.
  - Mock does not need to become a full consultant engine in this cycle.
- Tests: add focused tests for the prompt harness.
  - Fake LLM response maps consultant sections into the returned draft.
  - Prompt includes consultant framing and required portfolio sections.
  - Malformed LLM optional fields are normalized.
  - Raw input is not blindly stored as the portfolio body.
  - Existing mock fallback and save flows still pass.

## Sprint Contract
- Passing Criteria:
  - `/api/studio/refine` still returns the current Studio-compatible shape.
  - With fake LLM output, portfolio intent includes problem, framing, approach, outcome, insight, and decisions/tradeoffs in preview-ready fields.
  - Resume intent produces a concise resume bullet suitable for resume generation.
  - Both intent produces both resume and portfolio surfaces.
  - LLM prompt explicitly instructs the model to act as a career consultant / portfolio maker.
  - No raw pasted input is persisted by default.
  - No provider abstraction, OpenAI integration, upload UI, model picker, or existing-card update is added.
- Automatic Checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test Cases:
  - Unit: prompt construction contains consultant role and required JSON keys.
  - Unit: fake LLM response maps new narrative fields into `draft`.
  - Unit: invalid optional fields normalize safely.
  - Integration: `/api/studio/refine` with fake LLM returns `refine_source=llm`.
  - Regression: `/api/studio/refine` with no key returns mock.
  - Regression: Studio save still creates a valid draft card from refined output.
  - Manual: start `uv run pcli dashboard --port 5097`, open `/studio`, paste messy material, generate with `Both`, and confirm the preview reads like a resume/portfolio consultant draft.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- The LLM returns valid JSON with the wrong semantic type, such as `metrics` as an object or `evidence` as plain text.
- The raw input contains confidential notes that the model repeats too directly in `portfolio_body`.
- The LLM produces a strong portfolio narrative but omits fields required for saved card validation.

## Simpler Alternative
Only tweak the prompt text and leave parsing unchanged. This is faster, but it would make the feature fragile because the UI and save path would still trust loosely shaped LLM output.

## Assumptions
- The current Anthropic client remains the only real provider in Cycle 16.
- Generic `AI_API_KEY` remains an alias for the same Anthropic-compatible client, not a provider router.
- Studio preview can use additional draft fields without a full UI redesign.
- Prompt changes should not modify original card files until the user saves a draft card.

## Review Guidance
### Enumeration Required
- Studio refine entry points:
  - Search: `rg "studio_refine|api_studio_refine|refine_source" scripts tests`
  - Expected areas: `scripts/llm.py`, `scripts/dashboard.py`, `scripts/static/studio.js`, related tests.
- Studio save flow:
  - Search: `rg "api_studio_save|studio/save|raw_text|portfolio_body" scripts tests`
  - Confirm save still excludes raw pasted input by default.
- Card validation fields:
  - Search: `rg "Card|CardRepo|missing_info|metrics|evidence|tags" scripts tests`

### Verification Method Guide
- Prompt content checks can be unit tests with monkeypatched fake clients; no live API call is required.
- LLM response normalization must be tested with fake malformed responses.
- Save validity should be verified through existing repo/CardRepo validation or `uv run pcli validate`.
- UI wording is secondary in this cycle; do not block on visual polish unless the Studio preview no longer exposes required generated fields.
