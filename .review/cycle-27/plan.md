# Workspace Route Shell Plan

Branch: feature/cycle-27-workspace-route-shell

## Summary
`landing.md` describes a target-first curation workspace inspired by Teal/Linear/Notion/Read.cv:
left-side evidence cards, right-side target matching/output controls, deterministic coverage, and
AI only at clear boundaries. The existing `/studio` route is valuable but is a legacy vertical
capture/refine/application-writing surface with many safety regressions already covered by tests.

This cycle starts the migration path by adding a parallel `/workspace` route shell. It does not
replace `/studio`, does not introduce a full theme/matching engine, and does not change existing
provider or persistence behavior.

## Input/Output Spec
- Input:
  - Existing `GET /api/cards` array response.
  - Existing live-card fields already exposed to Studio.
  - Existing target-context concepts from Application Writing:
    - organization/company
    - role
    - question
    - competency
    - job description
    - output type
    - blind hiring
- Output:
  - Normal:
    - `GET /workspace` renders a new workspace page.
    - Existing `GET /studio` continues to render the old Studio page unchanged.
    - Workspace page exposes a two-pane shell:
      - left pane: live evidence cards list/selector
      - right pane: target context, output type, placeholder match/coverage panel, preview actions
    - Workspace JavaScript consumes `/api/cards` array response and filters `status === "live"`.
    - Workspace may call the existing `/api/studio/application-preview` endpoint for application
      answer/cover-letter preview, but must not add new provider behavior.
  - Failure:
    - If no live cards exist, workspace shows a safe empty state with next action.
    - If card loading fails, workspace shows a safe error state.

## Key Changes
- Backend:
  - Add `@app.route("/workspace")` in `scripts/dashboard.py`.
  - Serve a new `scripts/templates/workspace.html` template.
  - Reuse existing `/api/cards`, `/api/build`, and `/api/studio/application-preview` contracts.
  - Do not remove or redirect `/studio`.
- Frontend:
  - Add `scripts/static/workspace.js`.
  - Add a two-pane layout shell aligned with `landing.md`:
    - left evidence/card pane with collapsed card rows
    - right target/output pane
    - placeholder deterministic matching panel with `0%`/empty coverage until a later cycle
  - Use design-token direction from `landing.md`:
    - neutral base
    - one muted blue/info accent
    - 8px spacing rhythm
    - 8/12px radii
    - low-alpha borders
    - sentence case copy
  - Workspace card list must be independent from `/studio` DOM ids and JS state.
  - Keep Application Writing preview integration minimal; shell-first is acceptable.
- Tests:
  - Add `tests/test_cycle27.py`.
  - Preserve existing `/studio` tests unchanged.
  - Add route/source contract tests for `/workspace`, `/static/workspace.js`, and legacy route
    coexistence.
- Docs:
  - No broad docs rewrite required.
  - Optional: one acceptance row in `docs/acceptance-studio.md` or a short note if helpful.

## Sprint Contract
- Passing criteria:
  - `/workspace` returns HTTP 200.
  - `/studio` still returns HTTP 200 and continues to serve existing Studio template.
  - Dashboard may link to `/workspace`, but existing `/studio` link must remain unless explicitly
    duplicated as a separate link.
  - Workspace template includes two named panes:
    - evidence/cards pane
    - target/output pane
  - Workspace source includes hooks for:
    - live card list
    - selected card count
    - target company/role/question inputs
    - output type segmented/radio control
    - placeholder match percent/coverage/gap display
    - generate preview action
  - Workspace JS:
    - fetches `/api/cards`
    - consumes a bare array response via `Array.isArray(data)`
    - filters `status === "live"`
    - does not read `data.cards`
    - does not import or depend on `studio.js`
  - No new backend mutation/persistence route is added.
  - Existing Application Writing, export, blind-hiring, and no-persistence tests remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Test cases:
  - `GET /workspace` returns 200 and includes `/static/workspace.js`.
  - `GET /studio` remains 200 and includes `/static/studio.js`.
  - Workspace HTML contains two-pane landmarks/hook ids.
  - Workspace JS uses `Array.isArray(data)` and `status === "live"`.
  - Workspace JS does not contain `data.cards`.
  - Workspace JS calls `/api/studio/application-preview` only if preview integration is included.
  - Workspace route does not create or mutate card files.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- User selects cards, then card reload removes one selected id.
- No live cards but draft cards exist.
- Future match engine introduces themes unavailable on old cards.

## Simpler Alternative
Replace `/studio` directly with the new two-pane workspace. This is not selected because `/studio`
now carries substantial tested behavior: refine, Application Writing, blind-hiring sanitization,
copy/export separation, no-persistence guarantees, and fallback handling. Parallel routing is
faster and safer.

## Assumptions
- `landing.md` is a planning/reference artifact and is not staged unless explicitly requested.
- This project remains Flask templates + vanilla JS for this cycle; Next.js/React migration is
out of scope.
- Theme extraction, match percentage calculation, and recommendation engine are later cycles.
- Workspace starts as shell-first: structural alignment before full parity.

## Review Guidance
### Enumeration Needed
Review all route/template/static additions and confirm legacy Studio is untouched:

```bash
rg -n "workspace|studio|application-preview|api/cards|data.cards|Array.isArray|status === \"live\"" scripts tests docs .review/cycle-27
```

Expected surfaces:
- `scripts/dashboard.py`
- `scripts/templates/workspace.html`
- `scripts/static/workspace.js`
- optional `scripts/templates/dashboard.html`
- `tests/test_cycle27.py`
- existing `scripts/templates/studio.html` and `scripts/static/studio.js` should be unchanged
  unless a clearly justified link/copy adjustment is in plan.

### Verification Method Guide
- Route coexistence:
  - Flask test-client route tests are required.
- JS/API source contract:
  - Source tests are sufficient for array response handling, live filter, no `data.cards`, and
    endpoint names.
- UI shell:
  - Static HTML hook tests are sufficient for this cycle; browser automation is not required.
- No-persistence:
  - Since this cycle should add no mutation endpoint, source/route tests plus existing
    no-persistence tests are sufficient.
