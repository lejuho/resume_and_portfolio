# Workspace Design Token Alignment Plan

Branch: feature/cycle-28-workspace-design-tokens

## Summary
Cycle 27 added an additive `/workspace` route shell. It follows the broad `landing.md`
direction, but it does not yet fully align with the design-system tokens in `landing.md`.
The current workspace CSS still uses hard-coded colors, `font-weight: 600`, `1px` borders, and
simple checkbox rows rather than the calmer tokenized curation-card shell described in the
landing brief.

This cycle aligns the Workspace shell with the `landing.md` design system without adding a
matching engine, changing provider behavior, or replacing `/studio`.

## Input/Output Spec
- Input:
  - Existing `/workspace` route.
  - Existing `scripts/templates/workspace.html` and `scripts/static/workspace.js`.
  - Existing `/api/cards` array response.
  - `landing.md` design-system direction as reference only; do not stage `landing.md` unless
    explicitly requested.
- Output:
  - Normal:
    - `/workspace` still renders a two-pane shell.
    - CSS uses explicit design tokens for neutral surfaces, text, muted blue info/accent, spacing,
      radius, and borders.
    - Workspace typography uses only 400/500 weights.
    - Workspace copy remains sentence case with no uppercase transform.
    - Card rows move closer to the `landing.md` collapsed-card shell:
      - tag/status pill area
      - title
      - one-line context/summary
      - result/evidence metadata line
      - clear selected state using info tint/border
    - Existing `/studio` remains unchanged.
  - Failure:
    - No live-card empty/error states remain safe and readable.

## Key Changes
- Frontend template:
  - Refactor `scripts/templates/workspace.html` CSS to define `:root` workspace tokens:
    - neutral background/surface/text/muted
    - info/accent color
    - spacing values based on 4/8/16/24/32 rhythm
    - radius md=8px and lg=12px
    - low-alpha border token
  - Remove remaining `font-weight: 600` from workspace CSS; use 400/500 only.
  - Replace hard-coded repeated blue/gray values with token variables where practical.
  - Preserve two-pane route shell and existing DOM hook ids.
- Frontend JS:
  - Keep `scripts/static/workspace.js` independent from `studio.js`.
  - Improve live-card rendering markup/classes to support collapsed-card visual structure.
  - Add selected state class/tint behavior when checkboxes change.
  - Keep `/api/cards` array guard, live filter, and no `data.cards`.
  - Do not add STAR expansion, command palette, or real matching engine in this cycle.
- Tests:
  - Add/extend `tests/test_cycle28.py`.
  - Preserve Cycle 27 route/source tests.
  - Add source contract tests for token presence and obvious token violations.
- Docs:
  - No broad docs update required.

## Sprint Contract
- Passing criteria:
  - `/workspace` remains HTTP 200 and `/studio` remains HTTP 200.
  - `workspace.html` defines workspace design tokens in `:root`.
  - Workspace CSS contains no `text-transform: uppercase`.
  - Workspace CSS contains no `font-weight: 600` or `font-weight: 700`.
  - Workspace shell uses token variables for accent/info and common surfaces/borders.
  - Workspace card markup/classes include:
    - pill/tag/status element
    - title element
    - context/summary element
    - metadata/result line
    - selected-state class hook
  - Workspace JS toggles selected-state styling when card selection changes.
  - Workspace JS still uses `Array.isArray(data)`, filters `status === "live"`, and does not
    read `data.cards`.
  - No new backend mutation/persistence route is added.
  - Existing Studio/Application Writing tests remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Test cases:
  - `GET /workspace` includes token variable definitions such as `--ws-accent`,
    `--ws-surface`, `--ws-radius-md`, `--ws-radius-lg`, and `--ws-border`.
  - Workspace HTML has no uppercase transform and no 600/700 font weights.
  - Workspace JS emits card markup classes for pill/title/context/meta.
  - Workspace JS toggles selected class on selection change.
  - Workspace JS source still satisfies Cycle 27 array/live/no-`data.cards` contract.
  - Visiting `/workspace` does not create card files.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Card summary/context is empty; collapsed card should still render a safe fallback line.
- Card title or summary is long; one-line context should truncate visually without hiding the
  entire card.
- Checkbox selected state and label click target can drift if markup changes.

## Simpler Alternative
Only tweak colors and spacing in the current CSS. This is not selected because the current shell
would still miss the more important `landing.md` design constraints: tokenized CSS, 400/500 type
weight, and card-row structure suitable for later STAR/progressive-disclosure work.

## Assumptions
- `landing.md` remains an untracked reference artifact for this cycle.
- This cycle keeps Flask templates and vanilla JS.
- Real theme coverage, STAR expansion, recommendation badges, and command palette are later
  cycles.
- Direct CSS source tests are sufficient for design-token alignment at this stage.

## Review Guidance
### Enumeration Needed
Review every Workspace style/markup path:

```bash
rg -n "ws-|workspace|font-weight|text-transform|--ws-|data.cards|Array.isArray|status === \"live\"" scripts/templates/workspace.html scripts/static/workspace.js tests .review/cycle-28
```

Expected surfaces:
- `scripts/templates/workspace.html`
- `scripts/static/workspace.js`
- `tests/test_cycle28.py`
- existing `tests/test_cycle27.py`

### Verification Method Guide
- Design token compliance:
  - Source tests are sufficient for token definitions, no uppercase transform, and no
    disallowed font weights.
- Card shell:
  - Source tests are sufficient for class hooks and selected-state behavior.
- Route coexistence:
  - Flask test-client route tests are required.
- No-persistence:
  - Existing `/workspace` no-mutation route/file tests are sufficient unless backend code changes.
