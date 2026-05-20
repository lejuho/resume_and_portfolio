# Cycle 5 Polish + v1 Acceptance Plan

Branch: feature/cycle-5-polish-acceptance
Cycle: 5
Created: 2026-05-20

## Summary

Cycle 4 has been merged into local `main`, and this branch starts Cycle 5 from that merged state. The remaining Phase 5 scope in `requirements.md` is polish: caching behavior, error UX, dry-run consistency, rich output, README, and end-to-end acceptance verification.

This cycle should not add dashboard/web UI, GitHub ingestion, ATS automation, new LLM features, or new template families. The goal is to make the current CLI v1 coherent, documented, and acceptance-testable.

## 입력/출력 명세

- 입력:
  - existing `cards/*.mdx`, `profile.yaml` or `profile.example.yaml`, `presets/*.yaml`
  - CLI flags already implemented across `pcli new/validate/ls/show/build/preset/llm`
  - optional `ANTHROPIC_API_KEY` for live LLM paths
- 출력:
  - normal:
    - all commands expose useful `--help`
    - non-LLM commands work without `ANTHROPIC_API_KEY`
    - dry-run output clearly shows selected cards and build intent without creating final artifacts
    - README gets a current 5-minute quickstart covering resume, portfolio, presets, and optional LLM
    - acceptance smoke commands can be run from a clean checkout with predictable results
  - failure:
    - invalid filters, missing presets, missing templates, missing JD files, missing API key, and missing assets produce actionable rich errors or warnings with correct exit codes
    - missing visuals in portfolio continue to warn and use placeholder, not fail

## Key Changes

- README and user docs:
  - Update `README.md` from Phase 1 quickstart to current CLI v1 quickstart.
  - Document output locations:
    - resume PDFs: `output/resumes/`
    - portfolio PPTX: `output/portfolios/`
    - temp context: `.build/resume-data.json`
    - LLM cache: `.cache/llm/`
  - Add 5-minute first PDF path and a portfolio build path.
  - Add presets examples: `pcli build resume --preset bok-interview`, `pcli preset run <name>`, `pcli preset save <name>`.
  - Add optional LLM section with `ANTHROPIC_API_KEY`, cache behavior, fallback behavior, and `--show-llm-diff`.
- CLI polish:
  - Audit all public commands for help text consistency and flag naming drift from `requirements.md`.
  - Improve dry-run output where needed so resume/portfolio/preset paths show target, template/layout, language, filters, max items, output destination intent, and selected card IDs.
  - Ensure `--tone` accepted values are validated as `formal|founder|technical`.
  - Ensure `--lang` accepted values are validated as `en|ko`.
  - Ensure `--layout` accepted values are validated with clear errors.
  - Ensure `--max-items` rejects zero/negative values with a clear error.
- Error UX:
  - Normalize user-facing errors for:
    - missing preset
    - preset target mismatch
    - missing resume template
    - missing JD file
    - unknown explicit card IDs
    - invalid month filters
    - no selected cards
  - Keep exit code behavior aligned with requirements:
    - validation/user input errors: exit 1
    - render/tooling failures: exit 2
    - missing portfolio visual: warning + exit 0
- Cache and artifact polish:
  - Confirm `.cache/llm` read/write behavior is deterministic and documented.
  - Keep `.cache`, `.build`, `output`, and sensitive `profile.yaml` ignored.
  - Add or update tests ensuring dry-run does not create final PDF/PPTX artifacts.
- Acceptance harness:
  - Add a lightweight smoke script or documented checklist for the seven v1 acceptance criteria.
  - Prefer testable CLI commands over manual-only checks.
  - Manual checks remain only for opening generated PDF/PPTX visually.

## Sprint Contract

- 통과 기준:
  - `README.md` explains current v1, not just Phase 1.
  - All public command groups and subcommands respond to `--help`.
  - `uv run pcli validate` passes on current cards.
  - `uv run pcli build resume --dry-run` clearly reports selection and does not require Typst.
  - `uv run pcli build portfolio --dry-run` clearly reports selection and does not create PPTX.
  - `uv run pcli build resume --preset bok-interview` builds a PDF in `output/resumes/` when Typst is installed.
  - `uv run pcli build portfolio --tags web3` builds a PPTX in `output/portfolios/`.
  - Non-LLM commands pass with no `ANTHROPIC_API_KEY`.
  - LLM commands or LLM flags fail/fallback exactly as documented when no key/cache is available.
  - Invalid `--tone`, `--lang`, `--layout`, and non-positive `--max-items` are rejected with actionable messages.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli --help`
  - `uv run pcli build resume --help`
  - `uv run pcli build portfolio --help`
  - `uv run pcli preset --help`
  - `uv run pcli llm --help`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - `uv run pcli build resume --preset bok-interview`
  - `uv run pcli build portfolio --tags web3`
- 테스트 케이스:
  - help coverage for all public command groups/subcommands
  - invalid enum values: tone/lang/layout
  - invalid max-items values
  - dry-run does not create final artifacts
  - missing preset and target mismatch produce clear exit 1
  - missing template produces render/tooling exit 2
  - README command examples remain valid enough for smoke execution
  - LLM no-key behavior does not break non-LLM commands
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- `--jd -` with empty stdin should not silently produce misleading LLM behavior.
- Preset values plus CLI overrides can combine into invalid values, such as `max_items: 0` or `lang: jp`.
- Dry-run commands might still update `.cache/last-build.yaml` or create output directories, making them less stateless than users expect.

## 더 단순한 대안 1개

Only update README and run acceptance manually. Rejected because Phase 5 is exactly where small UX regressions become visible; adding focused tests for invalid inputs and dry-run behavior will prevent future cycles from re-breaking the CLI surface.

## Assumptions

- Typst is installed locally for full PDF smoke verification, as previous cycles successfully built PDFs.
- PowerPoint/Keynote manual opening remains a user-side check; automated tests only verify PPTX creation and basic structure.
- Live Anthropic calls are not required for automated checks. Existing fake/client-cache tests are sufficient for CI-style validation.
- Existing real card count may be below the final desired 10 cards; Cycle 5 verifies the tool can support 10, not that personal content creation is complete.

## Review Guidance

### Enumeration 필요 항목

- Public CLI command surface:
  - 검색: `rg "@.*\\.command|add_typer|Typer\\(" scripts/pcli.py`
  - 확인: each command/group has help coverage or is included in a smoke checklist.
- User-facing option validation:
  - 검색: `rg "tone|lang|layout|max_items|max-items|preset|template|JD|LLM error|WARN|Exit" scripts tests`
  - 확인: invalid inputs have tests and clear output.
- Artifact/cache behavior:
  - 검색: `rg "output|\\.cache|\\.build|last-build|dry_run|write_text|mkdir" scripts tests .gitignore README.md`
  - 확인: dry-run does not create final PDF/PPTX, and generated artifacts remain ignored.
- README command examples:
  - 검색: `rg "uv run pcli|ANTHROPIC_API_KEY|output/resumes|output/portfolios|preset|portfolio|LLM" README.md`
  - 확인: README reflects Cycle 4/5 command surface.

### 검증 방식 가이드

- Help coverage:
  - CLI integration tests are sufficient.
- Invalid input UX:
  - Typer runner tests are sufficient for enum/range validation.
  - Missing external binary/template render errors should be checked with integration-style tests or explicit command runs.
- PDF/PPTX creation:
  - Automated file existence checks are sufficient for CI.
  - Visual correctness remains manual acceptance.
- LLM paths:
  - Mock/fake client tests are sufficient for scoring/rewrite/cache behavior.
  - No live network call should be required.
