# Cycle 11 Plan: Career Studio MVP Shell + Mock Refine

Branch: feature/cycle-11-career-studio-mvp

## Summary

Cycle 11 starts the post-v1 Career Studio track from `requirements-dashboard.md` and `docs/design-system-studio.md`.

The goal is a first vertical slice for `/studio`: a light, creation-first workspace where the user can paste messy career material, choose an output intent, generate a deterministic mock draft, review the result, and save it as a new draft card.

This cycle proves:

```text
raw career material -> structured preview -> saved draft card
```

The existing `/dashboard` remains the admin console and must not regress.

## Input/Output Spec

- Input:
  - `GET /studio`
  - `POST /api/studio/refine`
    - JSON: `{ "raw_text": string, "intent": "resume" | "portfolio" | "both" }`
  - `POST /api/studio/save`
    - JSON: refined draft payload from Studio preview
- Output:
  - `GET /studio`: Studio HTML shell with capture, intent selection, preview, missing-info prompts, save action, and `/dashboard` link.
  - `POST /api/studio/refine`: `{ ok, draft, missing_info }`
  - `POST /api/studio/save`: creates one new draft MDX card and returns `{ ok, id, path }`.
  - Failure:
    - empty raw text: `400`
    - invalid intent: `400`
    - duplicate generated card id: `409`
    - invalid card data: `422`

## Key Changes

- Dashboard server:
  - Add `/dashboard` route while keeping `/` compatibility.
  - Add `/studio`.
  - Add `POST /api/studio/refine`.
  - Add `POST /api/studio/save`.
  - Reuse current card write safety patterns, atomic writes, duplicate-id checks, and `Card` validation.
- Templates/static:
  - Add `scripts/templates/studio.html`.
  - Add `scripts/static/studio.js`.
  - Keep Studio separate from the dense admin `dashboard.html`.
- Mock refine:
  - Deterministic only; no live LLM call.
  - Resume intent returns a concise resume bullet.
  - Portfolio intent returns narrative blocks: Problem, Framing, Approach, Outcome, Insight.
  - Both intent returns both surfaces.
  - Missing date, metrics, evidence, or visual context are surfaced as prompts.
- Save behavior:
  - Creates new cards only.
  - Defaults to `status: draft` and `visibility: public`.
  - Uses title-derived kebab slug; fallback `studio-draft`.
  - Duplicate id returns a clear conflict and does not overwrite.
  - Saves refined portfolio narrative into MDX body.
  - Does not store raw pasted input by default.
- Out of scope:
  - No upload, picker, visual path editing, live LLM integration, existing-card update, or dashboard replacement.

## Sprint Contract

- Passing criteria:
  - `/studio` opens and renders the core Studio hooks.
  - `/dashboard` still opens and renders the existing admin dashboard.
  - Mock refinement is deterministic and intent-sensitive.
  - Studio save creates a valid draft card.
  - Duplicate ids are rejected without overwrite.
  - Raw pasted input is not persisted by default.
  - Existing dashboard card/build behavior remains intact.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Test cases:
  - `/studio` returns `200` and includes core Studio UI hooks.
  - `/dashboard` returns the existing admin dashboard.
  - `POST /api/studio/refine` rejects empty raw text.
  - Resume intent returns a resume bullet and missing info.
  - Portfolio intent returns portfolio narrative blocks.
  - Both intent returns both surfaces.
  - Invalid intent returns `400`.
  - `POST /api/studio/save` creates a draft card from refined draft.
  - Saved Studio card passes `CardRepo` validation.
  - Duplicate generated id returns `409` and does not overwrite.
  - Raw pasted input is not stored by default.
  - Existing dashboard build/authoring regression tests still pass.
- Manual acceptance:
  - Start: `uv run pcli dashboard --port 5097`
  - Open: `http://127.0.0.1:5097/studio`
  - Paste messy activity text.
  - Select `Both`.
  - Generate preview.
  - Confirm resume bullet, portfolio blocks, and missing info are visible.
  - Save as draft card.
  - Run `uv run pcli validate`.
  - Open `/dashboard` and confirm the saved card appears.
- Gas limit: N/A
- Slither: N/A

## Missing Edge Case Candidates

- Raw input contains only a URL or metric with no usable title.
- Title-derived slug collides with an existing card from another month.
- Refined output contains invalid or overlong summary text that would fail card validation.

## Simpler Alternative

Add a single "AI draft" modal inside the existing `/dashboard`.

This would be faster, but it would keep the database/admin feeling as the primary experience. A separate `/studio` route better tests the intended creation-first product direction without disturbing the admin surface.

## Assumptions

- Cycle 11 uses deterministic mock refinement only.
- Studio creates new draft cards only.
- The canonical durable store remains `cards/*.mdx`.
- `period.start` may use today's date when no date is inferable, with uncertainty shown in the preview.
- Raw pasted text is transformation input, not durable card content.
- Visual upload and asset editing remain in `/dashboard` or future cycles.

## Review Guidance

### Enumeration Needed

- Dashboard routes:
  - Search: `rg '@app.route' scripts/dashboard.py`
  - Expected: `/`, `/dashboard`, `/studio`, `/api/cards`, `/api/build`, `/api/studio/refine`, `/api/studio/save`
- Studio files:
  - Search: `rg 'studio' scripts/templates scripts/static scripts/dashboard.py tests`
  - Expected: separate template and JS, not folded into `dashboard.html`
- Card writes:
  - Search: `rg '_write_card_atomic|Card.model_validate|glob\\(f\"\\?\\?\\?\\?-\\?\\?-\\{card_id\\}' scripts/dashboard.py`
  - Expected: Studio save still validates and rejects duplicates.

### Verification Method Guide

- Route rendering can be verified with Flask test client.
- Mock refine behavior can be verified with API tests only; no external API mocking should be needed.
- Save behavior must be verified through actual temporary MDX file creation and `CardRepo` validation, not only response JSON.
- Duplicate safety must verify the original file content remains unchanged.
- Raw input persistence must inspect the written MDX file.
- Existing admin dashboard regression should use the existing dashboard tests and `/api/build` subprocess mocks.
