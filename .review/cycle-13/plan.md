# Cycle 13 Plan: Studio UX Language + Status Help

Branch: feature/cycle-13-ux-language-status-help

## Summary

Cycle 11 and 12 made `/studio` usable enough to capture, refine, edit, save, and continue into output builds. The next small cycle should improve product comprehension: make the UI explain core concepts like Career Memory, Draft, Live, and Archived without turning Studio into a manual or a database form.

This cycle is UI/UX copy and lightweight affordances only. Do not change card schema, filtering semantics, build behavior, or save behavior.

## Input/Output Spec

- Input:
  - `GET /studio`
  - `GET /dashboard`
- Output:
  - Studio uses clearer product language for the capture/refine/save flow.
  - Dashboard exposes compact status explanations near the status filter.
  - Save success explains that new Studio cards are saved as Draft and can be marked Live in Dashboard when ready for normal output selection.
  - Missing info remains a follow-up prompt, not a blocking validation error.
- Failure:
  - No new API failure modes.

## Key Changes

- Studio copy:
  - Prefer "Career Memory", "Refine", "Draft", and "Output" language.
  - Add short helper text near capture/preview explaining the flow:
    - loose memory
    - refined draft
    - saved card
    - generated outputs
  - After save, show concise status guidance:
    - "Saved as Draft. Mark it Live in Dashboard when it is ready for normal output generation."
- Dashboard copy:
  - Add compact status explanations near the status filter:
    - Draft: work in progress
    - Live: ready for output
    - Archived: kept but hidden
  - Keep the admin dashboard dense and precise; do not redesign the page.
- Tests:
  - Add rendered HTML tests for the new Studio helper language.
  - Add rendered HTML tests for Dashboard status explanation text.
  - Keep existing Studio/Dashboard tests passing.

## Sprint Contract

- Passing criteria:
  - `/studio` still opens and keeps existing core hooks.
  - `/dashboard` still opens and keeps existing admin hooks.
  - Studio includes light copy explaining the Career Memory → Draft → Output flow.
  - Studio save-success area explains Draft vs Live in one concise sentence.
  - Dashboard status filter includes short descriptions for Draft, Live, and Archived.
  - No schema/API/build behavior changes.
  - Existing Cycle 11/12 Studio tests remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test cases:
  - `/studio` contains "Career Memory" or equivalent capture language.
  - `/studio` contains "Saved as Draft" guidance in the post-save area.
  - `/dashboard` contains descriptions for draft/live/archived.
  - `/dashboard` still contains the Studio nav button.
  - No new API endpoints are introduced.
- Manual acceptance:
  - Start: `uv run pcli dashboard --port 5097`
  - Open `/studio`.
  - Confirm the page explains what the user is doing without looking like a long help document.
  - Save a draft and confirm the post-save status sentence is visible.
  - Open `/dashboard`.
  - Confirm status meanings are visible near the status filter.
- Gas limit: N/A
- Slither: N/A

## Missing Edge Case Candidates

- Copy becomes too verbose and visually competes with the main capture flow.
- Dashboard status explanations wrap poorly on the narrow sidebar.
- Terms in Studio and Dashboard drift, causing more confusion instead of less.

## Simpler Alternative

Only add title attributes/tooltips to status labels.

This is simpler, but not enough: the user may never hover, and the Studio save flow needs visible guidance about why Draft exists.

## Assumptions

- This cycle is copy/UI-only.
- No live LLM integration.
- No behavior change to which statuses are selected by default.
- Dashboard remains the admin surface; Studio remains the creative capture surface.

## Review Guidance

### Enumeration Needed

- UI copy locations:
  - Search: `rg 'Career Memory|Saved as Draft|work in progress|ready for output|kept but hidden' scripts/templates tests`
  - Expected: Studio and Dashboard templates plus tests.
- API routes:
  - Search: `rg '@app.route' scripts/dashboard.py`
  - Expected: no new routes for this cycle.
- Behavior changes:
  - Search: `git diff main..HEAD -- scripts/dashboard.py scripts/static`
  - Expected: no server behavior change; JS changes only if needed for displaying text.

### Verification Method Guide

- Rendered HTML tests are sufficient for copy presence.
- Existing API/build/card tests provide regression coverage.
- Reviewer should inspect that copy is concise and does not convert Studio into a long instruction page.
