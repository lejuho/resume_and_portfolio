# Workspace Evidence Fit Signals Implementation Plan

Branch: feature/cycle-30-workspace-fit-signals

## Summary
Cycles 27-29 established the new `/workspace` shell, design tokens, visual polish, and dark-mode
toggle. The Workspace now looks like a durable surface, but its coverage panel still says theme
matching is available in a later cycle. Cycle 30 makes that panel useful by adding simple
client-side evidence fit signals.

This cycle helps the user decide which live cards support the current application target before
generating a draft. It does not change provider prompts, Application Writing backend behavior,
card persistence, or matching through LLMs.

## Input/Output Spec
- Input:
  - Existing `GET /workspace` shell.
  - Existing `GET /static/workspace.js`.
  - Existing `GET /api/cards` JSON array, filtered client-side to `status === "live"`.
  - User-entered target context fields: organization, role, question/prompt, competency focus,
    optional job description.
  - User-selected live cards.
- Output:
  - Normal:
    - Coverage panel updates as target fields and selected cards change.
    - Shows a deterministic client-side fit summary based on shared keywords/themes between
      target context and selected cards.
    - Shows matched terms when overlap exists.
    - Shows a helpful gap message when target context or selected evidence is missing.
    - Existing generate-preview behavior remains unchanged.
  - Failure:
    - No new backend failures.
    - If cards cannot load, existing card-load error UI remains.

## Key Changes
- Frontend: `scripts/static/workspace.js`
  - Add small deterministic tokenization helpers for target text and card text.
  - Compute selected-card fit from title, summary, type, metrics, and evidence URL/text where
    available in the current card object shape.
  - Update `#ws-coverage-value` and `#ws-coverage-gap` when:
    - cards load,
    - card selection changes,
    - target input fields change.
  - Keep `/api/cards` array response handling, `status === "live"` filter, and no `data.cards`
    access.
  - Keep `generateWorkspacePreview()` payload and backend endpoint unchanged.
- Frontend: `scripts/templates/workspace.html`
  - Add stable hooks for matched terms or gap details only if needed.
  - Keep visual style token-driven and compatible with Cycle 29 dark/light modes.
- Tests: `tests/test_cycle30.py`
  - Add source/route regression tests for fit helper presence and selector wiring.
  - Add test-client fixture coverage for route availability and static JS contracts.

## Sprint Contract
- Passing criteria:
  - `/workspace` and `/studio` both return HTTP 200.
  - Workspace JS defines deterministic fit/tokenization helpers.
  - Coverage panel value is no longer static-only; it can be updated from selected cards and target
    context.
  - Target inputs trigger fit recalculation through event listeners.
  - Card selection still toggles `ws-card-selected` and also refreshes coverage.
  - Matched terms are rendered into the coverage panel when overlap exists.
  - Missing target context and missing selected evidence have distinct safe messages.
  - `/api/cards` response contract remains array-based with `Array.isArray(data)`.
  - `status === "live"` filter remains.
  - `workspace.js` still does not read `data.cards`.
  - `generateWorkspacePreview()` request shape is unchanged.
  - No new backend mutation/persistence route is added.
  - Existing Studio/Application Writing tests remain green.
- Automatic checks:
  - `uv run pytest tests/test_cycle27.py tests/test_cycle28.py tests/test_cycle29.py tests/test_cycle30.py -v`
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Test cases:
  - Source test: fit tokenization helper exists.
  - Source test: fit computation reads target fields and selected live cards.
  - Source test: target fields wire `input`/`change` listeners to coverage refresh.
  - Source test: `_wsOnCardToggle` refreshes coverage after toggling selected class.
  - Source test: matched terms output hook/text exists.
  - Regression test: `/api/cards` array/live/no-`data.cards` contract.
  - Regression test: `generateWorkspacePreview()` still posts to
    `/api/studio/application-preview` with `output_type`, `card_ids`, and `target_context`.
  - Route regression: `/workspace` and `/studio` return HTTP 200.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Very short or noisy target words can create weak matches; filter stop words and very short
  tokens to avoid noisy coverage.
- Evidence URLs may produce technical tokens from paths/domains; include them conservatively and
  cap rendered matched terms.
- Client-side source tests can verify wiring and deterministic helper presence but not full browser
  interaction; keep helper functions simple and expose only what tests need.

## Simpler Alternative
Only show the selected-card count in the coverage panel. This is safer and already exists, but it
does not answer the user's next need: whether selected evidence actually fits the prompt. A small
rule-based signal is still low-risk and makes the Workspace materially more useful.

## Assumptions
- Fit signals are advisory UI only; they do not alter provider payload or generated drafts.
- No LLM/provider call is used for matching in this cycle.
- No card files are modified.
- `landing.md` remains a local design reference and is not staged unless explicitly requested.

## Review Guidance
### Enumeration Needed
- Workspace JS fit flow:
  - Search: `rg -n "fit|coverage|matched|token|stop|ws-coverage|addEventListener|_wsOnCardToggle|generateWorkspacePreview" scripts/static/workspace.js`
  - Confirm target input changes and card selection both refresh coverage.
- Workspace selector contract:
  - Search: `rg -n "Array\\.isArray|status === \"live\"|data\\.cards" scripts/static/workspace.js`
  - `data.cards` should be absent.
- Backend mutation check:
  - Search: `rg -n "workspace|api/workspace|@app\\.(post|put|delete|patch)" scripts/dashboard.py`
  - No new Workspace mutation/persistence route should be present.
- Preview payload check:
  - Search: `rg -n "application-preview|output_type|card_ids|target_context" scripts/static/workspace.js`
  - Request shape should remain compatible with Cycle 21 Application Writing API.

### Verification Method Guide
- Route availability:
  - Flask test client route tests are sufficient.
- JS helper and wiring contracts:
  - Source tests are sufficient for this cycle because the behavior is deterministic and UI-only.
- Provider/payload invariants:
  - Source tests are sufficient because this cycle must not modify backend provider assembly.
- No persistence/mutation:
  - Source search is sufficient; no filesystem write integration test is required unless
    implementation adds a write path, which would be out of scope.
