# Application Writing UX Polish Plan

Branch: feature/cycle-23-application-writing-ux-polish

## Summary

Cycle 21 added the Application Writing harness and Cycle 22 added Studio UI contract smoke
coverage. Cycle 23 improves the user-facing Application Writing experience without changing
generation policy, provider behavior, blind-hiring rules, or persistence behavior.

Goal: make it clearer which live cards are useful evidence, why generation may be blocked,
and what content is safe to copy.

## Input/Output Specification

- Input:
  - Existing Studio Application Writing panel.
  - Existing `/api/cards` card metadata.
  - Existing `/api/studio/application-preview` success and error responses.
- Output:
  - Live-card selector displays enough safe metadata for users to choose evidence quickly.
  - Empty/error states tell users the next action.
  - Preview clearly separates copyable verified draft from non-copyable AI guidance.
  - Blind-hiring `422` and related missing-info messages are understandable to a user.
- Non-goals:
  - No new generation policy.
  - No new provider prompt behavior unless required for copy text only.
  - No card creation or persistence from Application Writing.
  - No new test tooling.

## Key Changes

- Frontend: update `scripts/templates/studio.html` and/or `scripts/static/studio.js` copy and
  rendering to improve:
  - live-card selector card rows;
  - empty-state and API-error messages;
  - Verified Draft vs AI Guidance labels;
  - copy-action explanation.
- Backend: only adjust safe error/copy text in `scripts/dashboard.py` if needed for the
  blind-hiring `422` user message. Do not alter sanitization policy.
- Tests: update or add focused source/API tests for the new UI copy and preserved behavior.
- Docs: update `docs/acceptance-studio.md` only if manual acceptance steps need the new copy.

## Sprint Contract

- Pass criteria:
  - Live-card selector shows at least title plus useful selection metadata from available
    fields, such as summary and metric/evidence counts, without changing `/api/cards` shape.
  - Empty live-card state tells the user to mark cards Live in Dashboard and mentions
    validation errors as a possible cause.
  - Application preview error display surfaces the server error and restores the Generate
    button state.
  - Verified Draft label/copy makes clear that the draft is the only copyable text.
  - AI Guidance label/copy makes clear that guidance is advisory and not copied.
  - Blind-hiring all-redacted `422` message explains the action: choose different cards or
    remove identity/background identifiers from evidence cards.
  - Existing blind-hiring safety, no-persistence, and copy-separation tests remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - `uv run python scripts/evaluate_studio_grounding.py --dry-run`
- Test cases:
  - Studio JS/HTML source checks for selector metadata, empty-state copy, draft/guidance
    labels, and copy explanation.
  - API test for blind-hiring `422` safe user-facing error message.
  - Existing Cycle 21 and Cycle 22 tests continue passing.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates

- A live card with no metrics and no evidence should still render in the selector with honest
  counts, not disappear.
- A card summary containing special HTML characters must remain escaped in selector markup.
- Blind-hiring partial redaction should show warnings without implying all selected cards
  failed.

## Simpler Alternative

Only change text labels in the template. This is faster but leaves the selector underpowered:
users still cannot judge which card has evidence before generating. The chosen scope adds
lightweight metadata while keeping behavior unchanged.

## Assumptions

- `/api/cards` already provides `summary`, `metrics_count`, and `evidence_count`.
- Studio's current source/static test style is sufficient for copy and DOM contract checks.
- Selector metadata can be rendered from existing safe card-list fields; no backend API shape
  change is needed.
- Any blind-hiring error-message update remains policy-neutral.

## Review Guidance

### Enumeration Needed

Review Application Writing UI surfaces:

- Search: `rg -n "Application Writing|Live cards|No live cards|Verified draft|AI Guidance|Copy|blind-hiring|st-app" scripts/static scripts/templates tests docs`
- Expected files:
  - `scripts/static/studio.js`
  - `scripts/templates/studio.html`
  - `tests/test_cycle21.py`
  - `tests/test_cycle22.py`
  - possible new `tests/test_cycle23.py`
  - `docs/acceptance-studio.md` if manual copy changes

Review backend safe error surfaces only if changed:

- Search: `rg -n "blind-hiring policy|All submitted cards|application-preview|422" scripts tests`

### Verification Method Guide

- Static/source tests are sufficient for labels, helper copy, DOM hook presence, and selector
  rendering template strings.
- Flask API tests are required for any backend error-message change.
- Mock/provider tests are not needed unless generation logic changes; generation logic should
  not change in this cycle.
- Browser automation is optional and should not be introduced unless existing source/API tests
  cannot cover the UX contract.
