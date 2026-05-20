# Cycle 6 Release Readiness + Acceptance Evidence Plan

Branch: feature/cycle-6-release-readiness
Cycle: 6
Created: 2026-05-20

## Summary

Cycle 5 completed the v1 polish scope and was merged into local `main`. Cycle 6 should be a small release-readiness cycle: capture repeatable acceptance evidence, tighten sample/local setup documentation, and make it easy to verify that a fresh checkout can produce the expected PDF and PPTX artifacts.

This cycle should not add new product features. No dashboard, ingestion automation, new render layouts, or new LLM capabilities are in scope.

## 입력/출력 명세

- 입력:
  - current repository on `feature/cycle-6-release-readiness`
  - existing cards, presets, templates, and profile fallback
  - local Typst binary for full PDF smoke
  - optional `ANTHROPIC_API_KEY`; automated release checks must not require it
- 출력:
  - normal:
    - a checked-in acceptance checklist/report template for v1
    - a repeatable smoke command/script or documented command list
    - updated README section explaining v1 verification and manual artifact review
    - generated artifacts remain ignored and outside git
  - failure:
    - smoke failures clearly identify which acceptance item failed
    - missing Typst is reported as a skipped/manual prerequisite, not confused with CLI failure

## Key Changes

- Release evidence:
  - Add `docs/acceptance-v1.md` or equivalent with the seven acceptance criteria, command used, expected result, and manual notes.
  - Include places to record generated PDF/PPTX filenames and visual-open status.
- Smoke workflow:
  - Add a lightweight script or documented checklist for:
    - `uv run pytest -v`
    - `uv run ruff check scripts tests templates`
    - `uv run ruff format --check scripts tests templates`
    - `uv run pcli validate`
    - `uv run pcli build resume --dry-run`
    - `uv run pcli build portfolio --dry-run`
    - `uv run pcli build resume --preset bok-interview`
    - `uv run pcli build portfolio --tags web3`
  - Keep it cross-platform friendly for Windows PowerShell first.
- README polish:
  - Add a short "Verify v1" section pointing to the acceptance document.
  - Clarify that generated PDFs/PPTXs are ignored and should live under `output/resumes/` and `output/portfolios/`.
  - Clarify that `.review/` is intentionally tracked as cycle history.
- Git hygiene:
  - Confirm `.gitignore` does not hide `.review/`.
  - Keep local-only files such as `.claude-flow/`, `.mcp.json`, and `CLAUDE.md` out of this cycle unless explicitly requested.

## Sprint Contract

- 통과 기준:
  - Acceptance evidence doc exists and maps directly to all seven v1 acceptance criteria.
  - Smoke workflow can be run from PowerShell with copy-paste commands or a script.
  - README links or references the acceptance evidence.
  - Running the smoke commands produces PDF/PPTX artifacts in the expected ignored output subdirectories.
  - No generated PDF/PPTX/cache/build artifacts are staged.
  - `.review/cycle-6/status.txt` remains `in_progress` until review passes.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - `uv run pcli build resume --preset bok-interview`
  - `uv run pcli build portfolio --tags web3`
- 테스트 케이스:
  - If a smoke script is added, test or manually run its success path.
  - If only docs/checklist are added, verify every command listed still exists and matches current CLI names.
  - Confirm `git status --short` after smoke does not show output artifacts.
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- A fresh user may not have Typst installed, causing acceptance step 3 to fail before the CLI is meaningfully tested.
- PowerShell and bash syntax differ for environment variables and copy commands.
- Generated artifacts can share minute-level timestamps and overwrite or confuse manual review if commands are run repeatedly within one minute.

## 더 단순한 대안 1개

Do nothing after Cycle 5 and treat v1 as complete. Rejected because v1 acceptance includes manual artifact opening and timing checks; a short evidence cycle makes the final state auditable without changing product behavior.

## Assumptions

- The current real card set is acceptable for smoke verification even if the final personal content set grows later.
- A live LLM call is not required for release readiness; Cycle 4/5 fake and fallback tests cover automated behavior.
- Manual PDF/PPTX visual opening can be recorded in the acceptance document rather than automated.

## Review Guidance

### Enumeration 필요 항목

- Acceptance mapping:
  - 검색: `rg "Acceptance|v1|criteria|pcli build resume|pcli build portfolio|Typst|Keynote|PowerPoint" README.md docs .review/cycle-6`
  - 확인: all seven criteria from `requirements.md` are represented.
- Smoke commands:
  - 검색: `rg "uv run pytest|ruff check|ruff format|pcli validate|pcli build resume|pcli build portfolio" README.md docs scripts .review/cycle-6`
  - 확인: commands match current CLI exactly.
- Git hygiene:
  - 검색: `rg "^\\.review/|output/|\\.cache/|\\.build/|\\*.pdf|\\*.pptx" .gitignore`
  - 확인: `.review/` is not ignored, outputs/cache/build artifacts are ignored.

### 검증 방식 가이드

- Documentation-only changes still require executing the listed smoke commands.
- PDF/PPTX file creation is sufficient for automated review; visual opening remains manual.
- Use `git status --short` after smoke to ensure generated artifacts stay ignored.
