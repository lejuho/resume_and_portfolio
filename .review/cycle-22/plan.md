# Studio UI Contract Smoke Tests Plan

Branch: feature/cycle-22-studio-ui-smoke-tests

## Summary

Cycle 21 shipped the Application Writing harness and exposed a gap: backend endpoint tests
could pass while the Studio JavaScript consumed the wrong response shape. Cycle 22 adds a
small smoke-test layer for Studio UI contracts so critical browser-facing flows fail fast when
frontend/backend assumptions drift.

This cycle is test infrastructure and regression coverage only. It should not redesign Studio
UX or add new product behavior.

## Input/Output Specification

- Input:
  - Existing `/studio` page and static Studio JavaScript.
  - Existing `/api/cards`, `/api/studio/application-preview`, and related Studio endpoints.
  - Existing test fixtures and Flask test client.
- Output:
  - Normal: automated tests proving the Application Writing UI contract can load live cards,
    submit a preview request, render key preview sections, and keep copyable draft text
    separate from advisory guidance.
  - Failure: tests fail with clear assertions when a required UI contract string, endpoint
    path, response-shape assumption, or copy/advisory separation is broken.

## Key Changes

- Tests: add focused Studio UI contract smoke coverage using existing test style and tooling.
- Tests: prefer current Flask/static-source assertions where enough; use an executable JS/DOM
  harness only if one already exists or can be added without external dependencies.
- Documentation: update Studio acceptance docs only if test coverage clarifies an existing
  manual acceptance step.
- Backend/Frontend: no product code changes unless a smoke test exposes a real bug.

## Sprint Contract

- Pass criteria:
  - Application Writing selector contract is covered end to end enough to catch the Cycle 21
    `/api/cards` array-vs-object regression.
  - Studio JS still calls `/api/studio/application-preview` with selected live card IDs and
    target context fields.
  - Preview rendering contract covers verified draft, selected facts/cards, assumptions or
    missing-info display, and AI guidance separation.
  - Copy action contract ensures only verified draft text is copied; advisory guidance is not
    included.
  - Empty/error states for live-card loading and preview generation remain covered.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - `uv run python scripts/evaluate_studio_grounding.py --dry-run`
- Test cases:
  - Static/source contract tests for endpoint paths, response-shape guards, selected-card
    extraction, target-context field collection, preview rendering hooks, and copy handler.
  - API-level smoke test that selects a live card from `/api/cards` and submits it to
    `/api/studio/application-preview`.
  - If feasible without new tooling, executable JavaScript smoke for `loadAppCards()` and
    preview rendering with mocked `fetch` and DOM nodes.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates

- `/api/cards` returns an empty array: selector should show the existing empty state and not
  leave stale selected cards.
- `/api/cards` returns non-live cards mixed with live cards: selector should show only live
  cards.
- Preview generation fails after a card is selected: UI should surface the error and restore
  the generate button state.

## Simpler Alternative

Only add one source assertion for `Array.isArray(data)` in `studio.js`. This is fast but too
narrow: Cycle 21 showed that a single source assertion can protect one bug while leaving other
UI contracts untested. The chosen approach stays lightweight but covers the main user flow.

## Assumptions

- Existing Flask test client can serve `/studio` and `/static/studio.js`.
- No Node/browser test runner is currently required for this repository.
- The goal is smoke coverage, not pixel-perfect UI automation.
- Existing untracked local skill/read-counter artifacts are unrelated to this cycle.

## Review Guidance

### Enumeration Needed

Review all Studio JavaScript entry points that participate in Application Writing:

- Search: `rg -n "Application Writing|loadAppCards|generateAppPreview|renderApp|copy|clipboard|application-preview|st-app" scripts/static scripts/templates tests`
- Expected areas:
  - `scripts/static/studio.js`
  - `scripts/templates/studio.html`
  - `tests/test_cycle21.py`
  - possibly `tests/test_studio.py`

Review all relevant API contracts:

- Search: `rg -n "/api/cards|application-preview|selected_cards|ai_guidance|answer_draft|target_context" scripts tests requirements-dashboard.md docs`

### Verification Method Guide

- Source/static tests are sufficient for contract strings, endpoint paths, DOM hook IDs, and
  explicit copy/advisory separation logic.
- API-level Flask tests are sufficient for endpoint request/response shape and live-card
  availability.
- A real browser or new JS test runner is not required unless the executor chooses to add one
  with clear justification; avoid expanding tooling unless source/API smoke tests cannot cover
  the contract.
- Mock-only endpoint tests are insufficient for frontend/backend response-shape mismatches
  unless they also inspect or execute the frontend consumer.
