# Phase 2 Portfolio MVP Plan

Branch: feature/phase-2-portfolio-pptx
Cycle: 2
Created: 2026-05-19

## Summary

Implement the Phase 2 vertical slice: generate a PPTX portfolio from the existing card repository through `pcli build portfolio`. This cycle reuses Phase 1 card loading, validation, filtering, and explicit card selection. It does not add presets, LLM tailoring, dashboard UI, or advanced portfolio layouts.

## 입력/출력 명세

- 입력:
  - `profile.yaml` or `profile.example.yaml`
  - validated `cards/*.mdx`
  - CLI filters/options for portfolio selection
- 출력:
  - 정상:
    - `uv run pcli build portfolio` creates `output/portfolio-<timestamp>.pptx`
    - `--out` writes to the requested path
    - `--dry-run` prints selected cards without writing PPTX
    - missing visuals render as placeholders with warnings, not build failures
  - 실패:
    - invalid cards block before rendering with existing validation output
    - unsupported layout exits with an actionable error

## Key Changes

- Add `python-pptx` as a normal dependency.
- Add `scripts/render_portfolio.py` for profile loading, template dispatch, options, and output path handling.
- Add `templates/portfolio/default.py` exposing `render(cards, profile, options, output_path)`.
- Add `pcli build portfolio` with filters/options mirroring resume selection where applicable.
- Add tests for help, dry-run, PPTX creation, explicit `--cards`, missing visual fallback, and `--no-narrative`.

## Sprint Contract

- 통과 기준:
  - `uv run pcli build portfolio --help` succeeds.
  - `uv run pcli build portfolio --dry-run` prints selected cards.
  - `uv run pcli build portfolio --tags web3 --max-items 2` creates a `.pptx`.
  - Explicit `--cards` bypasses normal filters.
  - Generated deck contains cover, TOC, one slide per card, and closing slide.
  - Missing visuals do not fail rendering.
  - `--no-narrative` excludes narrative text from card slides.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
  - `uv run pcli build portfolio --dry-run`
  - `uv run pcli build portfolio --tags web3 --max-items 2`
- 테스트 케이스:
  - CLI help and dry-run behavior.
  - PPTX file generation and slide count.
  - Explicit card selection despite status/type filters.
  - Missing visual placeholder/warning.
  - Narrative excluded when `--no-narrative` is passed.
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- Very long narrative overflowing slide text boxes.
- Cards with no visuals and no metrics still need a useful slide.
- Mixed audience tags should choose a stable theme without crashing.

## 더 단순한 대안 1개

Generate a single text-only PPTX without visuals or themed layout. Rejected because Phase 2 requirements explicitly include card slides with visual area, tags, evidence, and profile/contact closing slide.

## Assumptions

- `one-per-card` is the only implemented layout in this cycle.
- `python-pptx` is a core dependency because PPTX generation is a v1 requirement.
- PPTX visual polish can improve later; this cycle prioritizes correct data flow and readable slides.
- Manual PowerPoint/Keynote opening remains a human acceptance step.

## Review Guidance

### Enumeration 필요 항목

- Portfolio command surface
  - 검색: `rg "build portfolio|cmd_build_portfolio|PortfolioOptions" scripts tests`
  - 예상 결과: command, options, renderer, and tests exist.
- PPTX renderer contract
  - 검색: `rg "def render\\(" templates/portfolio scripts`
  - 예상 결과: `templates/portfolio/default.py` exposes `render(...)`.
- Phase 2 exclusions
  - 검색: `rg "grouped-by-type|timeline|preset|llm|dashboard" scripts templates tests`
  - 예상 결과: no implementation beyond explicit unsupported layout handling.

### 검증 방식 가이드

- "PPTX generated":
  - Automated test should open the output with `python-pptx` and inspect slide count/text.
- "Missing visuals fallback":
  - Unit/direct renderer test is acceptable because normal repo validation still treats missing visual paths as validation errors.
- "No narrative":
  - Automated test should inspect generated slide text and ensure narrative-only content is absent.
