# Cycle 12 Plan: Studio Editable Preview + Save Actions

Branch: feature/cycle-12-studio-editable-preview-actions

## Summary

Cycle 11 proved the first `/studio` vertical slice:

```text
raw career material -> deterministic draft preview -> saved draft card
```

Cycle 12 should make that slice feel like a usable review workspace rather than a one-shot demo. The user should be able to edit the generated draft before saving, understand missing information without the UI feeling like form validation, and immediately continue into resume/portfolio/dashboard actions after save.

Live LLM integration remains out of scope for this cycle. Keep the deterministic mock refine path so tests stay stable while the Studio interaction model improves.

## Input/Output Spec

- Input:
  - `GET /studio`
  - `POST /api/studio/refine`
  - `POST /api/studio/save`
  - Existing `POST /api/build`
- Output:
  - `/studio` renders editable preview fields after refinement.
  - Save uses the user-edited preview values, not only the original draft JSON.
  - Missing info appears as readable badge + message rows, not concatenated text.
  - After save, Studio shows actions:
    - open saved card in `/dashboard`
    - build resume with the saved card selected
    - build portfolio with the saved card selected
  - Build actions reuse the existing `/api/build` endpoint.
- Failure:
  - invalid edited save payload returns the existing structured API error
  - build failures show the existing structured command/stdout/stderr feedback

## Key Changes

- Studio UI:
  - Replace read-only preview blocks with editable fields for:
    - title
    - summary
    - resume bullet
    - portfolio narrative/body
  - Keep generated missing-info prompts visible but visually separate them as non-blocking follow-up questions.
  - Add lightweight source chips during input for detected:
    - date
    - metric
    - link
    - visual mention
  - These chips should be hints only; do not show password-style live error validation while typing.
- Studio JS:
  - Maintain an editable draft state.
  - Before save, collect values from editable preview fields.
  - After save, show:
    - saved path
    - open in dashboard link
    - build resume button
    - build portfolio button
    - build result output area
  - Call `/api/build` with `selected_ids: [saved_id]`.
- Server/API:
  - Keep Cycle 11 endpoints and write safety behavior unchanged.
  - Accept edited draft values through the existing `/api/studio/save` payload.
  - Do not add live LLM or new durable data stores.
- Tests:
  - Add API/UI-level tests for editable preview hooks and post-save actions.
  - Add JS/static hook tests where practical through rendered HTML/string checks.
  - Preserve all Cycle 11 tests.

## Sprint Contract

- Passing criteria:
  - `/studio` still opens.
  - Generated preview fields are editable in the DOM.
  - Editing title/summary/body before save affects the saved MDX card.
  - Missing info code and message render as separate elements.
  - Input source chips can detect date, metric, URL, and visual mention without blocking input.
  - Save success exposes dashboard, resume build, and portfolio build actions.
  - Resume/portfolio build actions call existing `/api/build` with the saved card id.
  - No raw pasted input is persisted by default.
  - Existing `/dashboard`, `/api/cards`, and `/api/build` regressions remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test cases:
  - `/studio` contains editable preview hook containers.
  - `/studio` contains post-save action hook containers.
  - refine result can be edited client-side and saved through `/api/studio/save`.
  - edited summary is persisted in frontmatter.
  - edited portfolio body is persisted in MDX body.
  - edited resume bullet is persisted as narrative/frontmatter.
  - missing-info rendering has separate code/message hooks.
  - source-chip detection JS exposes hooks for date/metric/link/visual hints.
  - save success response can drive selected-card build calls.
  - existing dashboard build endpoint still receives `selected_ids` correctly.
- Manual acceptance:
  - Start: `uv run pcli dashboard --port 5097`
  - Open: `http://127.0.0.1:5097/studio`
  - Type messy text with a date, metric, URL, and screenshot mention.
  - Confirm source chips appear as hints.
  - Generate preview.
  - Edit title, summary, resume bullet, and portfolio narrative.
  - Save as draft card.
  - Confirm edited values are what appear in the saved card.
  - Click build resume and build portfolio for the saved card.
  - Open `/dashboard` and confirm the card is visible.
- Gas limit: N/A
- Slither: N/A

## Missing Edge Case Candidates

- User deletes title after generation and tries to save.
- User edits summary beyond the card schema length limit.
- Build action is clicked before save or after a failed save.

## Simpler Alternative

Only polish the missing-info visual layout and leave preview read-only.

This would be quicker, but it would leave Studio feeling like a generator that silently decides the output. Editable preview is a stronger match for the "AI refines, human approves" requirement.

## Assumptions

- Cycle 12 still uses deterministic mock refinement.
- Editing happens in the Studio preview DOM; no separate markdown editor dependency is needed.
- Existing `/api/studio/save` can remain the save boundary if it accepts the edited draft payload.
- Build actions can reuse `/api/build` and do not need new server endpoints.
- Raw input remains transient and is not saved by default.

## Review Guidance

### Enumeration Needed

- Studio route and static hooks:
  - Search: `rg 'st-|studio|source-chip|missing' scripts/templates scripts/static tests`
  - Expected: editable preview hooks, missing-info code/message hooks, post-save action hooks.
- Save path:
  - Search: `rg 'api_studio_save|summary|portfolio_body|resume_bullet|Card.model_validate' scripts/dashboard.py tests`
  - Expected: edited values pass through validation and persist to the intended frontmatter/body fields.
- Build reuse:
  - Search: `rg '/api/build|selected_ids|build resume|build portfolio' scripts/static scripts/templates tests`
  - Expected: Studio calls existing build endpoint with the saved card id.

### Verification Method Guide

- Editable persistence must be verified by writing a temporary MDX card and reading it back.
- Build action reuse can be verified with mocked `/api/build` server behavior or JS hook/string tests plus existing endpoint tests.
- Missing-info visual split can be verified through HTML/JS output structure.
- Source chips are UX hints and should not be treated as validation blockers.
- Raw input non-persistence still requires inspecting the saved MDX file.
