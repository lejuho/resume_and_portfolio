# Cycle 7 Dashboard MVP Plan

Branch: feature/cycle-7-dashboard-mvp
Cycle: 7
Created: 2026-05-20

## Summary

CLI v1 is complete and merged through Cycle 6. Cycle 7 starts the next phase: a local dashboard for browsing activity cards, selecting cards for resume/portfolio outputs, and launching existing build flows without replacing the CLI engine.

This cycle should implement the smallest useful dashboard vertical slice. It should not add auth, multi-user support, cloud storage, GitHub ingestion, LLM chat, or a full card editor. The CLI and `cards/*.mdx` remain the source of truth.

## 입력/출력 명세

- 입력:
  - existing `cards/*.mdx`
  - existing `profile.yaml` / `profile.example.yaml`
  - existing presets and build commands
  - local browser at `localhost`
- 출력:
  - normal:
    - local dashboard starts with one command
    - card list loads from the same parser/validation path as CLI
    - user can filter cards by type/tag/status/search text
    - user can select cards and preview selected IDs
    - user can run resume/portfolio dry-run from dashboard
    - user can run real resume/portfolio build and see output path
  - failure:
    - validation errors are surfaced in the dashboard
    - build failures show stderr/exit code without crashing the server
    - missing output artifacts are reported clearly

## Key Changes

- Dashboard app skeleton:
  - Add a local web dashboard under `dashboard/` or `scripts/dashboard.py`.
  - Prefer a lightweight Python-first stack unless implementation discovers a better fit:
    - backend: FastAPI or similar
    - frontend: simple server-rendered HTML or minimal static JS
  - Add dependencies only if needed and document them.
- Data API:
  - Reuse `scripts.card.CardRepo` and `scripts.select.filter_cards`.
  - Expose cards as JSON including id, title, type, status, period, summary, tags, metrics count, evidence count, visual availability.
  - Expose validation errors/warnings.
- Dashboard UI:
  - First screen is the actual working dashboard, not a landing page.
  - Dense, utilitarian layout:
    - left/filter toolbar
    - card table/list
    - selected-card panel
    - build action panel
  - Include status chips, type filters, tag search, text search, selected count.
  - Avoid editing MDX in this cycle.
- Build integration:
  - Add dashboard actions that call existing internal functions or CLI-safe wrappers for:
    - resume dry-run
    - portfolio dry-run
    - resume build
    - portfolio build
  - Show command/result/output path in the UI.
  - Keep outputs in existing ignored folders:
    - `output/resumes/`
    - `output/portfolios/`
- CLI launcher:
  - Add `pcli dashboard` or documented `uv run ...` command to start the local dashboard.
  - If server starts, print URL.
- Tests:
  - Add tests for card JSON endpoint or data adapter.
  - Add tests that selected card IDs are passed into build commands in explicit order.
  - Add tests that build failure returns structured error.

## Sprint Contract

- 통과 기준:
  - `uv run pcli dashboard` or documented equivalent starts a local server.
  - Dashboard first screen shows current cards.
  - Filtering/search works for at least type, status, tag, and text query.
  - Selecting cards updates a selected list without editing source files.
  - Resume/portfolio dry-run can be triggered from dashboard and displays selected card IDs.
  - Resume/portfolio real build can be triggered and displays output path.
  - Existing CLI commands and Cycle 6 smoke still pass.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - dashboard server smoke command, exact command to be defined by implementation
- 테스트 케이스:
  - card list endpoint/data adapter returns current sample card IDs
  - filters produce same IDs as CLI selection logic
  - explicit selected card IDs bypass filters for build action
  - failed build returns non-200 or structured error with message
  - no dashboard action mutates `cards/*.mdx`
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- Browser user selects cards that become invalid/deleted before build.
- A build takes long enough that the UI needs pending state and duplicate-click protection.
- Windows path escaping differs between displayed command, subprocess call, and output link.

## 더 단순한 대안 1개

Build a static HTML report of cards without actions. Rejected because the dashboard’s core value is selecting cards and launching existing resume/portfolio builds; a static report would not materially improve the current CLI workflow.

## Assumptions

- This is a local-only tool; no auth or network exposure beyond localhost is required.
- Dashboard can call Python functions directly or invoke CLI commands, whichever is safer with existing code.
- Card creation/editing remains out of scope for this cycle; it can be Cycle 8 after selection/build UX is proven.
- Visual polish should be workmanlike and clear, not final design.

## Review Guidance

### Enumeration 필요 항목

- Dashboard command surface:
  - 검색: `rg "dashboard|FastAPI|uvicorn|localhost|static|templates" scripts dashboard tests README.md pyproject.toml`
  - 확인: documented launch command and implementation match.
- Card data reuse:
  - 검색: `rg "CardRepo|filter_cards|cards_arg|explicit_ids|build_resume|build_portfolio" scripts dashboard tests`
  - 확인: dashboard does not reimplement parsing/filtering in an incompatible way.
- Mutation safety:
  - 검색: `rg "write_text|open\\(.*w|Remove-Item|unlink|cards/" scripts dashboard tests`
  - 확인: dashboard does not write to `cards/*.mdx` in Cycle 7.
- Build outputs:
  - 검색: `rg "output/resumes|output/portfolios|\\.build|subprocess|build resume|build portfolio" scripts dashboard tests`
  - 확인: outputs stay in existing ignored directories.

### 검증 방식 가이드

- Backend/data behavior should be tested with Python tests.
- Frontend usability should be verified with a local browser screenshot or manual smoke after starting the server.
- Existing CLI smoke from Cycle 6 must still pass, since dashboard is additive.
