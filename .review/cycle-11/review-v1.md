# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [MEDIUM] Studio save can persist raw pasted note text through `portfolio_body`

- Location: `scripts/dashboard.py:350`, `scripts/dashboard.py:427`, `scripts/dashboard.py:511`
- Analysis: `_mock_refine()` copies every raw input line after the first into `body_text`, places that verbatim into `draft["portfolio_body"]`, and `api_studio_save()` writes that field directly to the MDX body. The current raw-input test only proves that an extra `raw_text` key sent to `/api/studio/save` is ignored; it does not prove that raw material sent to `/api/studio/refine` is absent from the saved card.
- Impact: This violates the Sprint Contract item "Raw pasted input is not persisted by default" and the plan requirement "Saves refined portfolio narrative into MDX body. Does not store raw pasted input by default." A user pasting private rough notes after the title line would get those notes saved verbatim.
- Fix direction: Make mock refinement generate deterministic transformed narrative text instead of embedding `body_text` verbatim. Keep extracted facts such as metrics, URLs, and inferred title/type, but do not copy the original raw body wholesale. Add a test that refines and saves raw text containing a unique sensitive phrase in the raw body, then asserts the written MDX does not contain that exact phrase.

## Sprint Contract Check

- `/studio` opens and renders the core Studio hooks: PASS
- `/dashboard` still opens and renders the existing admin dashboard: PASS
- Mock refinement is deterministic and intent-sensitive: PASS
- Studio save creates a valid draft card: PASS
- Duplicate ids are rejected without overwrite: PASS
- Raw pasted input is not persisted by default: FAIL
- Existing dashboard card/build behavior remains intact: PASS

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

RESOLVED: ISSUE-1 — raw pasted body no longer persists through refine→save pipeline

- `_mock_refine`: removed `body_text` variable; `summary` now uses `title` only; `portfolio_body` uses templated sections referencing only extracted facts (title, metric) — no raw lines from the paste
- Added `test_studio_save_does_not_persist_raw_body`: refines raw text with "SECRET_BODY_PHRASE" in body line (not title), saves draft, asserts phrase absent from written MDX file
- 213 tests pass, ruff clean
