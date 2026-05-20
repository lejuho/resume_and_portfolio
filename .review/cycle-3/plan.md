# Phase 3 Presets and Template Variants Plan

Branch: feature/cycle-3-presets-variants
Cycle: 3
Created: 2026-05-20

## Summary

Implement Phase 3 from `requirements.md`: repeatable build presets, a Korean `bok` resume template variant, and portfolio layout variants. This cycle should make audience-specific outputs reproducible from YAML presets while preserving the existing direct CLI flag behavior.

Scope is limited to preset loading/running/saving, `bok` resume rendering, sample preset files, and portfolio `grouped-by-type` / `timeline` layouts. LLM tailoring, dashboard UI, and advanced design polish remain out of scope.

## 입력/출력 명세

- 입력:
  - `presets/<name>.yaml`
  - existing `profile.yaml` / `profile.example.yaml`
  - existing validated `cards/*.mdx`
  - CLI build flags, which override preset values
- 출력:
  - 정상:
    - `uv run pcli preset run <name>` builds the preset target
    - `uv run pcli build resume --preset bok-interview` creates a PDF using `templates/resume/bok.typ`
    - `uv run pcli build portfolio --preset colosseum` creates a PPTX
    - `uv run pcli build portfolio --layout grouped-by-type` creates section-divider slides by card type
    - `uv run pcli build portfolio --layout timeline` creates a timeline overview plus highlight slides
    - `uv run pcli preset save <name>` saves the most recent build arguments to `presets/<name>.yaml`
  - 실패:
    - missing preset exits non-zero with a clear message
    - preset without `target` exits non-zero
    - `bok` resume fails clearly if an included card lacks `summary_ko`

## Key Changes

- Preset system
  - Add YAML preset loading and merge logic.
  - Support `target`, `template`, `layout`, `lang`, `filters`, `include_cards`, `exclude_cards`, `cover_title`, `cover_subtitle`.
  - CLI flags override preset fields when both are supplied.
  - `include_cards` force-includes cards after filters; `exclude_cards` removes cards after inclusion.
  - Add `pcli preset run <name>` and `pcli preset save <name>`.
- Resume variants
  - Add `templates/resume/bok.typ`.
  - `bok` uses Korean profile summary, places education higher, and requires `summary_ko` for included cards.
  - Keep `default.typ` behavior unchanged.
- Portfolio variants
  - Extend portfolio renderer to support `grouped-by-type` and `timeline`.
  - `grouped-by-type`: cover → TOC → type divider → cards for that type → closing.
  - `timeline`: cover → timeline overview slide → highlight one-per-card slides for live cards with metrics → closing.
- Sample presets
  - Add `presets/bok-interview.yaml`, `presets/colosseum.yaml`, and `presets/ethglobal.yaml`.

## Sprint Contract

- 통과 기준:
  - `uv run pcli build resume --preset bok-interview --dry-run` shows selected cards and `lang=ko`/template intent.
  - `uv run pcli build resume --preset bok-interview` produces a PDF under `output/resumes/`.
  - `uv run pcli build portfolio --preset colosseum` produces a PPTX under `output/portfolios/`.
  - `uv run pcli preset run colosseum` produces the same kind of PPTX as `build portfolio --preset colosseum`.
  - `uv run pcli build portfolio --layout grouped-by-type --dry-run` succeeds and validates layout support.
  - `uv run pcli build portfolio --layout timeline --dry-run` succeeds and validates layout support.
  - `uv run pcli preset save smoke-test` writes `presets/smoke-test.yaml` with the latest build target/options.
  - Existing Phase 1/2 commands still work without presets.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --preset bok-interview --dry-run`
  - `uv run pcli build portfolio --preset colosseum --dry-run`
  - `uv run pcli preset run colosseum`
- 테스트 케이스:
  - Preset load/merge with CLI override.
  - `include_cards` and `exclude_cards` selection behavior.
  - Missing preset and missing target errors.
  - `bok` build fails when selected card lacks `summary_ko`.
  - `grouped-by-type` PPTX contains divider slide text.
  - `timeline` PPTX contains timeline overview text and only highlight cards with metrics.
  - `preset save` writes a valid YAML file.
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- Preset includes a card id that does not exist.
- CLI `--cards` conflicts with preset filters/include/exclude.
- `bok` preset selects English-only cards and should fail before Typst with a helpful error.

## 더 단순한 대안 1개

Only add sample YAML files and manually pass equivalent flags. Rejected because Phase 3 Definition of Done explicitly requires a preset system with at least two working presets.

## Assumptions

- `--cards` remains the strongest selection override: when provided, normal filters are ignored, then `exclude_cards` may still remove ids if coming from preset.
- CLI flags override preset scalar values (`template`, `layout`, `lang`, `max_items`, `cover_title`, `cover_subtitle`).
- Preset `filters.types` maps to existing CLI `--types`; preset `filters.tags` maps to `--tags`.
- `preset save` can persist only the most recent build command from the current local repo using a small local state file under `.cache/last-build.yaml`.
- `bok` visual design should be functional and Korean-readable; final typography polish can happen later.

## Review Guidance

### Enumeration 필요 항목

- Preset command surface
  - 검색: `rg "preset|Preset|last-build|include_cards|exclude_cards" scripts tests presets`
  - 예상 결과: load/run/save paths and tests exist.
- Resume template variants
  - 검색: `rg "bok|summary_ko|template" scripts templates tests presets`
  - 예상 결과: `bok.typ` exists and selected Korean summaries are enforced.
- Portfolio layout variants
  - 검색: `rg "grouped-by-type|timeline|one-per-card" scripts templates tests`
  - 예상 결과: all three layouts are recognized; unsupported layouts still fail.

### 검증 방식 가이드

- "Preset merge works":
  - Unit tests should assert final selected card ids and options, not just command exit code.
- "Bok summary_ko required":
  - Test should use a fixture card without `summary_ko` and confirm non-zero exit before Typst.
- "Portfolio layouts work":
  - Automated tests should open generated PPTX with `python-pptx` and inspect slide text/count.
- "Preset save works":
  - Test may use isolated tmp repo and assert the YAML can be loaded and has `target`.
