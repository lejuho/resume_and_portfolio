# Cycle 8 Dashboard UX Polish Plan

Branch: feature/cycle-8-dashboard-ux-polish
Cycle: 8
Created: 2026-05-20

## Summary

Cycle 7 delivered the first local dashboard MVP: browse cards, filter/search, select cards, and trigger resume/portfolio builds through the existing CLI. Cycle 8 should make that workflow comfortable enough for daily use before adding any card editing write paths.

This cycle remains read-only for `cards/*.mdx`. No card creation/editing, auth, cloud sync, GitHub ingestion, or new build formats are in scope.

## 입력/출력 명세

- 입력:
  - existing dashboard served by `uv run pcli dashboard`
  - existing `cards/*.mdx`, presets, and output folders
  - dashboard build result JSON from `/api/build`
- 출력:
  - normal:
    - dashboard makes selected-card workflow easier to scan and reorder/clear
    - build result panel extracts and highlights generated output paths
    - output paths are copyable/openable from the UI where browser security allows
    - preset choices are visible or at least build actions show current target/options clearly
    - dashboard visual layout is polished enough for repeated use on desktop
  - failure:
    - build errors remain visible with command, exit code, stdout, stderr
    - no source card files are modified

## Key Changes

- Selection UX:
  - Add a selected-card panel with compact list, remove buttons, and selected count.
  - Preserve selected order from user clicks where possible.
  - Add clear all and select filtered controls that are obvious and stable.
- Build result UX:
  - Parse build stdout for output paths under `output/resumes/` and `output/portfolios/`.
  - Render output path as a prominent result row.
  - Add copy-to-clipboard button for command and output path.
  - Keep raw stdout/stderr available in a collapsible/details area.
- Dashboard layout polish:
  - Improve table density, sticky header, empty states, pending state, and disabled build buttons.
  - Avoid card-inside-card visual nesting; keep it utilitarian and scannable.
  - Make text fit at common desktop widths and a narrow browser width.
- API polish:
  - Include parsed `output_path` in `/api/build` JSON when detectable.
  - Include `target`, `dry_run`, and `selected_ids` in result JSON for UI rendering.
  - Keep structured error responses for build failure and timeout.
- Optional preset visibility:
  - If simple, expose available preset names in read-only form.
  - Do not implement preset editing in this cycle.
- Tests:
  - Add tests for output path parsing.
  - Add tests for `/api/build` result schema including `output_path`.
  - Add tests that selected IDs preserve order in command generation.
  - Add tests that dashboard code does not write `cards/*.mdx`.

## Sprint Contract

- 통과 기준:
  - Dashboard still starts with `uv run pcli dashboard`.
  - Card table remains visible and filter/search still works.
  - Selected-card panel shows selected IDs and allows removal/clear.
  - Build dry-run result shows command and selected IDs.
  - Real build result highlights generated PDF/PPTX path when command succeeds.
  - Build failure result shows exit code and stderr/stdout.
  - No dashboard path mutates `cards/*.mdx`.
  - Existing CLI and Cycle 7 dashboard tests still pass.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - local dashboard smoke on a non-default port
- 테스트 케이스:
  - output path parser handles resume and portfolio stdout
  - output path parser returns null/empty for dry-run
  - build API includes `output_path`, `command`, `exit_code`, `ok`, `stdout`, `stderr`
  - selected card order is preserved in `--cards id1,id2`
  - invalid build target remains rejected
  - source MDX remains unchanged after build action
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- Build stdout line wrapping on Windows may split paths across lines.
- Browser clipboard API may require HTTPS or user gesture; fallback text selection may be needed.
- User builds twice within the same minute and output filenames collide or appear ambiguous.

## 더 단순한 대안 1개

Jump directly to card creation/editing UI. Rejected because write paths to `cards/*.mdx` add much higher risk; the dashboard should first become a reliable read/select/build console.

## Assumptions

- Desktop browser is the primary target; mobile is not required for this cycle.
- Local-only Flask dashboard remains acceptable.
- It is acceptable to parse output paths from current CLI stdout rather than refactor all builders to return structured objects.

## Review Guidance

### Enumeration 필요 항목

- Build result schema:
  - 검색: `rg "output_path|stdout|stderr|exit_code|selected_ids|command" scripts/dashboard.py tests/test_dashboard.py scripts/templates/dashboard.html`
  - 확인: API and UI agree on result keys.
- Selection order and mutation safety:
  - 검색: `rg "selected_ids|--cards|write_text|cards/" scripts/dashboard.py tests/test_dashboard.py scripts/templates/dashboard.html`
  - 확인: selected order is preserved; no MDX writes.
- UI controls:
  - 검색: `rg "copy|selected|remove|clear|details|output" scripts/templates/dashboard.html`
  - 확인: command/output path copy and raw log visibility exist.

### 검증 방식 가이드

- Python tests are sufficient for parser/API behavior.
- Browser/manual smoke should verify layout, selection, pending state, and copy buttons at least once.
- Existing Cycle 7 dashboard smoke should still pass after polish.
