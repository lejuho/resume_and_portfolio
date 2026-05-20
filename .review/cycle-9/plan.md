# Cycle 9 Dashboard Card Authoring MVP Plan

Branch: feature/cycle-9-dashboard-card-authoring
Cycle: 9
Created: 2026-05-20

## Summary

Cycle 8 made the dashboard comfortable for read/select/build workflows. Cycle 9 should add the first carefully bounded write path: creating and editing local card draft files from the dashboard while preserving the existing CLI/stateless-file architecture.

This cycle should not add auth, cloud sync, GitHub ingestion, LLM auto-write, asset upload management, or bulk mutation. The dashboard remains local-only and file-backed.

## 입력/출력 명세

- 입력:
  - existing Flask dashboard served by `uv run pcli dashboard`
  - existing card schema and validation in `scripts/card.py`
  - existing `pcli new`, `pcli validate`, and card loading behavior
  - `cards/*.mdx` as the source of truth
- 출력:
  - dashboard can create a new draft card from required fields
  - dashboard can edit a single existing card's frontmatter/body through a form or structured textarea
  - writes are limited to `cards/*.mdx`
  - invalid card data is rejected with clear validation feedback
  - dashboard list refreshes after create/edit
  - no build output, cache, profile, preset, or review files are modified by authoring actions

## Key Changes

- Card creation UI:
  - Add a "New card" action in the dashboard.
  - Collect required minimum fields: type, slug/id, title, start date, status, summary.
  - Default new cards to `status: draft` and `visibility: public`.
  - Generate filename using the existing `YYYY-MM-<id>.mdx` convention.
  - Reuse existing CLI/card helpers where practical instead of duplicating schema rules.
- Card edit UI:
  - Add an edit action for a selected card.
  - Support editing frontmatter fields and markdown body/narrative in a conservative first form.
  - Preserve unknown frontmatter fields where possible.
  - Avoid rewriting unrelated card files.
- API:
  - Add `GET /api/cards/<id>` for full editable card data.
  - Add `POST /api/cards` for draft creation.
  - Add `PUT /api/cards/<id>` for updates.
  - Return structured JSON errors with validation messages.
  - Reject path traversal, duplicate IDs, invalid type/status, and filename/id mismatch.
- Safety:
  - Write through a temporary file then replace the target file.
  - Normalize writes to the existing MDX/frontmatter style.
  - Do not allow editing cards outside the repo `cards/` directory.
  - Do not trigger LLM writes in this cycle.
- UX:
  - Show save pending/success/error states.
  - Keep read/select/build workflow usable while authoring UI exists.
  - After save, refresh list and keep the edited/new card visible.
  - Make draft status visually distinct from live cards.

## Sprint Contract

- 통과 기준:
  - `uv run pcli dashboard` still starts normally.
  - Existing dashboard card list/filter/search/select/build features still work.
  - A new draft card can be created from the dashboard.
  - Created card appears under `cards/<YYYY-MM>-<id>.mdx`.
  - Created card passes `uv run pcli validate <id>`.
  - Existing single card can be edited and saved.
  - Invalid edits return structured validation errors and do not corrupt the file.
  - Duplicate IDs are rejected.
  - Path traversal attempts are rejected.
  - No unrelated card files are modified during edit/create.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- 테스트 케이스:
  - create card API writes expected filename and content
  - create defaults to draft/public
  - create duplicate ID fails without overwrite
  - create invalid slug/type/status fails
  - edit existing card updates only the target file
  - edit invalid data leaves original file unchanged
  - edit preserves unknown frontmatter fields where practical
  - path traversal card IDs are rejected
  - dashboard index exposes create/edit UI hooks
- manual acceptance:
  - Start dashboard on a non-default port.
  - Create one draft card from browser UI.
  - Edit summary/body once.
  - Run `uv run pcli validate <id>`.
  - Delete the manual test card or keep it only if intentionally useful.

## Out of Scope

- Rich markdown editor.
- Image upload/asset management.
- Bulk edit.
- Git commit/push automation from dashboard.
- LLM suggest writing directly into `cards/`.
- Multi-user concurrency handling.
- Dashboard presets editing.

## 누락된 엣지 케이스 후보 3개

- A user edits a card while the underlying file changes on disk in another editor.
- YAML frontmatter comments/order may not round-trip perfectly.
- Browser form fields may make long narrative editing awkward compared with a plain editor.

## 더 단순한 대안 1개

Only add a dashboard button that opens `pcli new` instructions and avoid writes. Rejected because the next useful product step is proving a minimal safe write path, not another read-only polish pass.

## Assumptions

- The dashboard is local-only, so no auth layer is required.
- Git remains the audit/history layer for card edits.
- It is acceptable for first-pass editing to be functional and conservative rather than a polished CMS.
- Generated test cards should use temporary directories in tests rather than polluting real `cards/`.

## Review Guidance

### Enumeration 필요 항목

- Write paths:
  - 검색: `rg "write_text|replace|rename|open\\(|cards" scripts/dashboard.py tests/test_dashboard.py`
  - 확인: only intended card files are written.
- API routes:
  - 검색: `rg "api_cards|/api/cards|POST|PUT" scripts/dashboard.py tests/test_dashboard.py`
  - 확인: validation and error schemas are covered.
- UI hooks:
  - 검색: `rg "New card|Edit|save|draft|form" scripts/templates/dashboard.html`
  - 확인: create/edit flows are visible and do not break build controls.

### 검증 방식 가이드

- Unit tests should use temporary card directories or monkeypatched repo paths.
- Manual browser smoke is important because this cycle adds forms and save states.
- Review should explicitly check that invalid save attempts do not partially overwrite existing MDX.
