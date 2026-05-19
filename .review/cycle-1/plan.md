# Phase 1 Implementation Plan

Branch: feature/phase-1-cli-resume
Cycle: 1
Created: 2026-05-19

## Summary

This cycle bootstraps the Card-Based Portfolio/Resume Builder into a usable Python CLI. The goal is to establish the project structure, card schema, core card IO, filtering/listing commands, and a minimal Typst-based resume build path.

The cycle is intentionally limited to Phase 1 from `requirements.md`: schema, CLI skeleton, `new`/`validate`/`ls`/`show`, default Typst resume template, and `build resume` without LLM or preset support. Portfolio rendering, presets, `bok` template, and LLM tailoring are deferred to later cycles.

## 입력/출력 명세

- 입력:
  - `requirements.md` as the authoritative product spec
  - `profile.yaml` or `profile.example.yaml`
  - `cards/*.mdx` files with YAML frontmatter and optional markdown body
  - CLI commands via `scripts/pcli.py`
- 출력:
  - 정상:
    - `pcli new <type> <slug>` creates `cards/<YYYY-MM>-<slug>.mdx`
    - `pcli validate` exits `0` when cards pass error-level validation
    - `pcli ls` prints filtered cards as a Rich table
    - `pcli show <slug>` pretty-prints one card
    - `pcli build resume` writes `.build/resume-data.json` and a PDF under `output/`
  - 실패:
    - validation errors exit `1` with file path and field context
    - missing Typst binary or Typst compile failure exits `2` with raw error context
    - missing card/profile/template paths print actionable Rich errors

## Key Changes

- Project bootstrap
  - `pyproject.toml` — package metadata, dependencies, `pcli` entry point
  - `.gitignore` — ignore `output/`, `.cache/`, `.build/`, local profile and Python artifacts
  - `README.md` — Phase 1 quickstart only
- Data directories and examples
  - `cards/` — sample card files for smoke testing
  - `assets/` — placeholder or minimal referenced assets if needed
  - `profile.example.yaml` — non-sensitive profile example
  - `templates/resume/default.typ` and `_macros.typ` — minimal one-page resume template
- CLI and core modules
  - `scripts/pcli.py` — Typer app and command routing
  - `scripts/card.py` — Pydantic v2 models, frontmatter parsing, validation, repo loading
  - `scripts/select.py` — filters, sorting, explicit card selection
  - `scripts/render_resume.py` — JSON build context and Typst subprocess invocation
- Tests
  - `tests/` — focused tests for card validation, filters, and CLI happy paths where practical

## Sprint Contract

- 통과 기준:
  - Repository can be bootstrapped with the required directories and Python package metadata.
  - `uv run pcli --help` and each Phase 1 command `--help` display successfully.
  - `uv run pcli new hackathon sample-card --title "Sample Card" --start 2026-05-01` creates a valid MDX stub.
  - `uv run pcli validate` catches error-level schema violations listed in `requirements.md`.
  - `uv run pcli ls` supports `--type`, `--tag`, `--since`, `--until`, `--status`, and `--sort`.
  - `uv run pcli show <slug>` resolves a card by id or filename slug and prints all important fields.
  - `uv run pcli build resume --dry-run` prints selected cards without requiring Typst.
  - `uv run pcli build resume` creates `.build/resume-data.json` and invokes Typst to produce a PDF when Typst is installed.
  - API key absence never breaks non-LLM commands.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
- 테스트 케이스:
  - Unit: schema validation for id, filename match, summary length, type enum, visual path existence, warning rules.
  - Unit: filter OR matching for tags and status/type comma lists.
  - CLI: `new`, `validate`, `ls`, `show`, `build resume --dry-run`.
  - Manual: real Typst PDF generation if Typst binary is available in the environment.
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- Duplicate ids across multiple `cards/*.mdx` files with different filename prefixes.
- `period.end` omitted or null for ongoing work and how it sorts against completed cards.
- Card narrative absent in frontmatter but present in markdown body, requiring body fallback.

## 더 단순한 대안 1개

Implement only JSON export first and postpone Typst rendering. Rejected because Phase 1 Definition of Done requires a generated one-page PDF, and adding the Typst invocation now proves the end-to-end data contract early.

## Assumptions

- The implementation root is `C:\resume_and_portfolio`; no nested `portfolio-cards/` directory will be created unless the user requests it.
- Python 3.11+ and `uv` are available or can be installed by the user.
- Typst may not be installed in the current Windows environment, so `--dry-run` must remain useful and tests should not require the Typst binary.
- `profile.yaml` is local/private; `profile.example.yaml` is committed.
- `narrative` frontmatter is preferred; markdown body is fallback when frontmatter narrative is missing.

## Review Guidance

### Enumeration 필요 항목

- Phase 1 command surface
  - 검색: `rg "def .*\\(|@app|@.*command" scripts`
  - 예상 결과: `new`, `validate`, `ls`, `show`, `build resume` handlers exist.
- Card validation rules from requirements
  - 검색: `rg "summary_ko|visuals|evidence|metrics|narrative|kebab|duplicate|filename" scripts tests`
  - 예상 결과: every error rule is implemented, warning rules are represented in validation output and strict mode.
- Build artifact paths
  - 검색: `rg "output|\\.build|resume-data|typst" scripts templates .gitignore`
  - 예상 결과: generated files go under `output/` and `.build/`, both gitignored.

### 검증 방식 가이드

- "Card schema conforms to requirements":
  - Unit tests are sufficient for model-level constraints.
  - Duplicate id and visual path checks require repo-level fixture tests, not only Pydantic field tests.
- "CLI commands work":
  - Typer CliRunner tests are sufficient for help/new/validate/ls/show/dry-run.
  - Real `pcli build resume` PDF output should be manual or environment-gated because Typst is an external binary.
- "Non-LLM commands work without API key":
  - Test by clearing `ANTHROPIC_API_KEY` and running Phase 1 commands.
- "One-page PDF generated":
  - Requires Typst installed. If unavailable in CI/local Windows, reviewer should accept dry-run plus JSON context tests as automated coverage and mark real PDF as manual pending environment.
