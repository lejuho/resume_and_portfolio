# Workspace Dark Polish Implementation Plan

Branch: feature/cycle-29-workspace-dark-polish

## Summary
Cycle 27 introduced the separate `/workspace` route and Cycle 28 centralized the first
Workspace design tokens. The current screen is still visually bright and only lightly polished.
Cycle 29 will refine the Workspace shell with OS-level dark mode support and tighter visual
states while preserving the existing Studio route and all generation behavior.

This cycle is intentionally UI-only. It does not change matching, generation, provider calls,
Application Writing semantics, persistence, or backend mutation behavior.

## Input/Output Spec
- Input:
  - Browser request to `GET /workspace`
  - Browser request to `GET /static/workspace.js`
  - Existing `GET /api/cards` array response consumed by `workspace.js`
- Output:
  - Normal:
    - `/workspace` returns the Workspace shell.
    - Light mode remains the default token set.
    - Dark mode is applied through `@media (prefers-color-scheme: dark)` token overrides.
    - Workspace card hover, selected, focus, pane, section, and preview states remain readable
      in both light and dark modes.
  - Failure:
    - No new failure modes.
    - Existing empty/error UI for missing cards remains unchanged in behavior.

## Key Changes
- Frontend: `scripts/templates/workspace.html`
  - Add dark-mode token overrides under `@media (prefers-color-scheme: dark)`.
  - Keep component CSS consuming semantic `--ws-*` tokens rather than scattering dark colors.
  - Polish Workspace spacing, pane surfaces, section hierarchy, card hover/selected/focus states,
    and preview contrast.
  - Keep uppercase transform and heavy `font-weight: 600/700` out of Workspace CSS.
- Frontend: `scripts/static/workspace.js`
  - Preserve existing `/api/cards` array contract, `status === "live"` filter, and no `data.cards`
    regression.
  - Add or preserve class hooks needed for hover/selected/focus polish only if necessary.
- Tests: `tests/test_cycle29.py`
  - Add source/route regression tests for dark-mode token overrides and visual-polish contracts.
  - Reuse existing Cycle 27/28 contract checks where relevant.

## Sprint Contract
- Passing criteria:
  - `/workspace` and `/studio` both return HTTP 200.
  - `workspace.html` includes `@media (prefers-color-scheme: dark)`.
  - Dark mode overrides semantic `--ws-*` tokens rather than styling components directly with
    scattered dark raw colors.
  - Light-mode token definitions from Cycle 28 remain present.
  - Workspace card hover, selected, and focus-visible styling exists.
  - Workspace preview and section surfaces remain token-driven.
  - Workspace CSS still avoids `text-transform: uppercase`.
  - Workspace CSS still avoids `font-weight: 600` and `font-weight: 700`.
  - `workspace.js` still consumes `/api/cards` as an array, filters `status === "live"`, and does
    not access `data.cards`.
  - No new backend mutation/persistence route is added.
  - Existing Studio/Application Writing tests remain green.
- Automatic checks:
  - `uv run pytest tests/test_cycle27.py tests/test_cycle28.py tests/test_cycle29.py -v`
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Test cases:
  - Source test: dark media query exists.
  - Source test: dark block overrides expected semantic tokens, such as `--ws-bg`,
    `--ws-surface`, `--ws-text`, `--ws-text-muted`, `--ws-border`, and `--ws-accent`.
  - Source test: component CSS uses token variables for dark-sensitive surfaces/borders.
  - Source test: hover, selected, and focus-visible card states exist.
  - Regression test: no uppercase transform or `font-weight: 600/700`.
  - Regression test: Workspace JS keeps array/live/no-`data.cards` contract.
  - Route regression: `/workspace` and `/studio` return HTTP 200.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Dark-mode contrast can look acceptable in source tests but still be visually weak in a real
  browser; manual browser inspection is useful if the local app is running.
- `prefers-color-scheme` handles OS preference but does not provide a manual toggle; this is
  deliberate for scope control.
- Raw colors may still be acceptable inside token definitions or genuinely one-off values; review
  should distinguish token definitions from component-level duplication.

## Simpler Alternative
Only lower the light-mode brightness by changing the existing light tokens and skip dark mode.
This is faster, but it does not address the user's explicit concern that the screen is too bright
and would force another token pass later. OS-level dark mode is still small enough for this cycle.

## Assumptions
- `/workspace` remains the experimental route for the new UI shell.
- `/studio` remains the existing stable route and should not be redesigned in this cycle.
- Dark mode should initially follow OS preference only; no persisted user setting or toggle is
  introduced.
- `landing.md` is a local reference artifact, not a source file to stage unless explicitly
  requested.

## Review Guidance
### Enumeration Needed
- Workspace template CSS:
  - Search: `rg -n "prefers-color-scheme|--ws-|font-weight: 600|font-weight: 700|text-transform|ws-card|ws-section|ws-preview" scripts/templates/workspace.html`
  - Confirm dark-sensitive component styles consume `var(--ws-...)` tokens.
- Workspace JS selector contract:
  - Search: `rg -n "Array\\.isArray|status === \"live\"|data\\.cards|ws-card-selected" scripts/static/workspace.js`
  - `data.cards` should be absent.
- Backend route mutation check:
  - Search: `rg -n "workspace|api/workspace|@app\\.(post|put|delete|patch)" scripts/dashboard.py`
  - No new Workspace mutation/persistence route should be present.

### Verification Method Guide
- Route availability:
  - Flask/FastAPI test client route tests are sufficient.
- CSS/token contracts:
  - Source tests are sufficient for token presence, dark media query presence, and prohibited
    typography patterns.
  - Source tests are not sufficient for perceived contrast; manual browser inspection may be noted
    but is not required for merge unless visual regressions are obvious.
- JS selector contract:
  - Existing source-inspection tests are sufficient because the regression class is static
    response-shape misuse.
- No persistence/mutation:
  - Source search and existing route tests are sufficient; no database or filesystem integration
    test is required because this cycle must not add backend write behavior.

---

## User Amendment v1: Manual Theme Toggle

The initial Cycle 29 plan scoped dark mode to OS preference only. User feedback after review:
"다크모드 토글 버튼이 없어" ("there is no dark-mode toggle button"). Treat manual theme switching
as expected UI behavior for this cycle.

Additional scope:
- Add a visible Workspace theme toggle button in the header.
- Keep OS preference as the default when no manual choice exists.
- Allow the toggle to switch between light and dark themes without backend calls.
- Persist only the local browser preference, for example through `localStorage`; do not add server
  persistence, card writes, provider behavior, or backend routes.
- Preserve existing `/workspace`, `/studio`, `/api/cards` selector contracts.

Additional tests:
- Workspace HTML exposes a theme toggle button with a stable id.
- Workspace JS defines theme apply/toggle helpers.
- Workspace JS uses `localStorage` for browser-only theme preference.
- Manual dark selector exists separately from the OS `prefers-color-scheme` block.
