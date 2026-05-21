# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [MEDIUM] Save button remains disabled after saving once and refining another draft

- Location: `scripts/static/studio.js:107`, `scripts/static/studio.js:136`, `scripts/static/studio.js:151`
- Analysis: `save()` disables the save button and changes its text to `Saving...`. On successful save, it hides the button but never resets `disabled` or the label. `renderPreview()` later unhides the same button for a newly generated preview, but only sets `hidden = false`; it does not restore `disabled = false` or `textContent = "Save as draft card"`.
- Impact: The Studio workspace cannot reliably handle a second `refine -> edit -> save` flow in the same page session. This undercuts the Cycle 12 goal of making Studio feel like a usable review workspace rather than a one-shot demo.
- Fix direction: In `renderPreview()`, reset the save button state whenever a new preview is rendered: `hidden = false`, `disabled = false`, and label text back to `Save as draft card`. Also consider clearing `_savedId` and build output for the new draft. Add a focused test or static assertion that the preview-render path resets the save button after a successful save.

## Sprint Contract Check

- `/studio` still opens: PASS
- Generated preview fields are editable in the DOM: PASS
- Editing title/summary/body before save affects the saved MDX card: PASS
- Missing info code and message render as separate elements: PASS
- Input source chips can detect date, metric, URL, and visual mention without blocking input: PASS
- Save success exposes dashboard, resume build, and portfolio build actions: PASS
- Resume/portfolio build actions call existing `/api/build` with the saved card id: PASS
- No raw pasted input is persisted by default: PASS
- Existing `/dashboard`, `/api/cards`, and `/api/build` regressions remain green: PASS

## Automatic Checks

- `uv run pytest -v`: PASS
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Changes Outside Plan

None found.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — save button state reset in renderPreview() for second refine→save flow

- `renderPreview()` in `studio.js` now resets `saveBtn.disabled = false`, `saveBtn.textContent = "Save as draft card"`, `_savedId = null`, and clears `st-build-output` — ensures a fresh save state whenever a new preview is rendered
- Added `test_studio_js_resets_save_btn_on_render`: static assertion that studio.js contains `disabled = false` and `"Save as draft card"` reset strings
- 225 tests pass, ruff clean
