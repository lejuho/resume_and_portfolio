# Cycle 10 Dashboard Card Detail Editing Plan

Branch: feature/cycle-10-dashboard-card-detail-editing
Cycle: 10
Created: 2026-05-20

## Summary

Cycle 9 opened the first safe dashboard write path: creating draft cards and editing a card's basic frontmatter/body. Cycle 10 should make that authoring flow useful for real portfolio cards by adding structured detail editing for the fields that drive resume/portfolio quality: tags, metrics, evidence, visuals, and narrative/body.

This is still a local-only dashboard. Git remains the audit/history layer. This cycle should not add cloud sync, auth, GitHub ingestion, LLM auto-write, drag-and-drop uploads, bulk editing, or a rich markdown editor.

## 입력/출력 명세

- 입력:
  - existing Cycle 9 dashboard card create/edit APIs
  - existing card schema in `scripts/card.py`
  - existing MDX files under `cards/`
  - local assets under `assets/`
- 출력:
  - dashboard edit form can view and modify structured card detail fields
  - saved cards remain valid according to the existing schema
  - invalid detail edits are rejected without partially overwriting the card
  - detail editing does not break dashboard list/filter/select/build workflows
  - no files outside `cards/*.mdx` are written in this cycle

## Scope

- Tags:
  - Edit `tags.domain`, `tags.skill`, and `tags.audience` as comma-separated chip/list inputs.
  - Persist as YAML lists.
- Metrics:
  - Add/remove/reorder simple metric strings.
  - Preserve the existing warning-only limit behavior from validation.
- Evidence:
  - Add/remove evidence entries with `type` and `url`.
  - Validate shape through the existing card model.
  - Keep labels/descriptions out of scope unless already supported by schema.
- Visuals:
  - Add/remove visual references with `path`, `role`, and optional `caption`.
  - Do not upload or move asset files.
  - Show whether referenced local asset exists.
  - Missing visual path should surface validation feedback according to existing validate/build behavior, but portfolio build fallback semantics must remain unchanged.
- Narrative/body:
  - Make narrative/body editing clearer and safer.
  - Preserve the existing body fallback behavior.
  - Do not add WYSIWYG or markdown preview unless very small.
- Read-only hints:
  - Show compact validation hints or save errors near the authoring panel.
  - Show evidence/visual counts in the card list as already done.

## Out of Scope

- Asset upload, image picker, screenshot capture, or file manager.
- LLM suggestion/editing from dashboard.
- Git commit/push buttons.
- Bulk card editing.
- Card rename/move.
- Concurrent edit conflict resolution beyond avoiding partial writes.
- Full CMS polish.

## Key Changes

- API/model glue:
  - Extend existing card detail response if needed so the form has normalized arrays for tags, metrics, evidence, and visuals.
  - Keep `id` immutable.
  - Keep atomic writes.
  - Reject invalid saves before writing.
- UI:
  - Expand the authoring panel into clear sections: Basics, Narrative, Tags, Metrics, Evidence, Visuals.
  - Use add/remove controls for repeated fields.
  - Keep controls compact and dashboard-like, not a marketing page.
  - Avoid nested card styling.
- Tests:
  - Add API tests for updating tags, metrics, evidence, visuals, and body.
  - Add invalid-shape tests that verify the original file is unchanged.
  - Add UI hook tests for detail editor sections.
  - Re-run existing dashboard build and card authoring tests.

## Sprint Contract

- 통과 기준:
  - Dashboard starts with `uv run pcli dashboard`.
  - Existing card listing/filter/search/select/build still works.
  - Existing Cycle 9 create/edit basic flow still works.
  - User can edit tags and saved YAML uses list values.
  - User can edit metrics without corrupting other fields.
  - User can edit evidence entries and invalid evidence is rejected.
  - User can edit visual references and see missing/existing status in the UI/API.
  - User can edit narrative/body text.
  - Invalid detail edits leave the original MDX unchanged.
  - No files outside `cards/*.mdx` are written.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- manual acceptance:
  - Start dashboard on a non-default port.
  - Edit one draft/test card's tags, metrics, evidence, visuals, and narrative.
  - Confirm the card appears correctly in the table after refresh.
  - Run `uv run pcli validate <id>`.
  - Run a portfolio dry-run or build using that card.

## 테스트 케이스

- `GET /api/cards/<id>` returns enough detail data for tags/metrics/evidence/visuals editing.
- `PUT /api/cards/<id>` updates `tags.domain/skill/audience` as lists.
- `PUT /api/cards/<id>` updates metrics list.
- `PUT /api/cards/<id>` updates evidence list.
- `PUT /api/cards/<id>` rejects invalid evidence URL/type shape and leaves file unchanged.
- `PUT /api/cards/<id>` updates visuals list.
- `PUT /api/cards/<id>` rejects invalid visual shape and leaves file unchanged.
- `PUT /api/cards/<id>` updates body/narrative without changing immutable `id`.
- Dashboard template includes detail editor hooks for tags, metrics, evidence, and visuals.
- Build endpoints still preserve selected IDs and do not mutate cards.

## 누락된 엣지 케이스 후보 3개

- YAML round-trip may reorder keys or change formatting, making diffs noisy.
- Empty strings in comma-separated inputs may persist as empty tags unless normalized.
- Asset existence hints can become stale if the user adds/removes files while the dashboard is open.

## 더 단순한 대안 1개

Use a single raw YAML textarea for all frontmatter. Rejected because it is faster to implement but too easy to corrupt card shape; Cycle 10 should make common detail edits safer, not merely possible.

## Assumptions

- The dashboard can normalize list-like fields before calling the existing `PUT /api/cards/<id>` endpoint.
- It is acceptable for unsupported/unknown frontmatter fields to remain preserved by the existing merge behavior.
- Asset file creation remains a manual filesystem/editor action for now.

## Review Guidance

### Enumeration 필요 항목

- Detail write paths:
  - 검색: `rg "tags|metrics|evidence|visuals|body|write_text|os.replace" scripts/dashboard.py tests/test_dashboard.py scripts/templates/dashboard.html`
  - 확인: only target card MDX can be written and invalid saves are pre-write failures.
- UI controls:
  - 검색: `rg "Tags|Metrics|Evidence|Visuals|addMetric|addEvidence|addVisual" scripts/templates/dashboard.html`
  - 확인: repeated fields have add/remove controls and preserve values on load.
- Regression surface:
  - 검색: `rg "id is immutable|already exists|selected_ids|/api/build" scripts/dashboard.py tests/test_dashboard.py`
  - 확인: Cycle 8/9 invariants remain covered.

### 검증 방식 가이드

- Unit/API tests should use temp repos and compare original file contents after rejected saves.
- Manual browser smoke should focus on editing repeated fields and refreshing the table.
- If visual existence is surfaced through API, test both existing and missing asset paths.
