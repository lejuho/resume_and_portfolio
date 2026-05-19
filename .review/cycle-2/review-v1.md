# Codex Review v1

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] Missing visual fallback is not reachable through the CLI build path
- 위치: `scripts/pcli.py:381`, `scripts/card.py:100`
- 분석: `pcli build portfolio` blocks on any `repo.errors` before rendering. `Card.check_visuals_exist()` turns a missing `visuals[].path` into a validation error, so a card with a missing visual path exits before `templates/portfolio/default.py` can render the placeholder. The direct renderer has fallback behavior, but the public CLI path does not.
- 영향: Cycle 2 plan requires "missing visuals render as placeholders with warnings, not build failures" and Sprint Contract requires "Missing visuals do not fail rendering." Current CLI behavior would fail the build for the exact card shape this requirement describes.
- 수정 방향: For portfolio builds, separate fatal card errors from missing visual errors, or make visual existence a warning/non-fatal condition for portfolio rendering. Keep `pcli validate` behavior if desired, but `pcli build portfolio` must be able to pass cards with missing visual paths to the renderer and emit warnings/placeholders.

### ISSUE-2 [MEDIUM] Unsupported `--layout` is accepted during `--dry-run`
- 위치: `scripts/pcli.py:405`, `scripts/render_portfolio.py:51`
- 분석: Layout validation happens inside `build_portfolio()`, but `cmd_build_portfolio()` returns early for `--dry-run` before calling that function. As a result, `uv run pcli build portfolio --layout timeline --dry-run` exits `0` and prints selected cards.
- 재현: `uv run pcli build portfolio --layout timeline --dry-run` returned success.
- 영향: Cycle 2 plan says unsupported layout should exit with an actionable error, and Cycle 2 supports only `one-per-card`. Dry-run should validate the requested command shape even if it skips file writing.
- 수정 방향: Validate `layout` before selection/dry-run return, or use a Typer enum/Literal-style constraint for the CLI option.

### ISSUE-3 [LOW] Resume PDFs and portfolio PPTXs should be separated under `output/`
- 위치: `scripts/render_resume.py:66`, `scripts/render_portfolio.py:52`
- 분석: Default artifacts currently write directly under `output/` as `resume-<timestamp>.pdf` and `portfolio-<timestamp>.pptx`. As both artifact types accumulate, the output directory becomes harder to scan and clean.
- 영향: The CLI is already producing both PDF resumes and PPTX portfolios. Keeping them in one flat directory creates avoidable operational friction for real usage.
- 수정 방향: Keep the top-level `output/` directory, but change default paths to separate subdirectories: `output/resumes/resume-<timestamp>.pdf` for resumes and `output/portfolios/portfolio-<timestamp>.pptx` for portfolios. Preserve `--out` override behavior exactly as-is.

## Sprint Contract Check
- `uv run pcli build portfolio --help`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run pcli build portfolio --tags web3 --max-items 2`: PASS, creates PPTX
- Explicit `--cards` bypasses normal filters: PASS by test coverage
- Generated deck contains cover, TOC, one slide per card, and closing slide: PASS by test coverage
- Missing visuals do not fail rendering: BLOCKED by ISSUE-1 for the public CLI path
- `--no-narrative` excludes narrative text: PASS by test coverage
- Output artifacts are organized by type under `output/`: BLOCKED by ISSUE-3

## Automatic Checks
- `uv run pytest -v`: PASS, 73 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run pcli build portfolio --tags web3 --max-items 2 --out output\review-cycle2-web3.pptx`: PASS
- `uv run pcli build portfolio --tags web3 --max-items 2 --no-narrative --out output\review-cycle2-no-narrative.pptx`: PASS

## Changes Outside Plan
- No dashboard, preset, LLM, grouped-by-type, or timeline implementation was added.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY
- ISSUE-3: APPLY

### Applied

RESOLVED: ISSUE-1 — Missing visuals non-fatal for portfolio builds via `portfolio_mode`
- `scripts/card.py`: Removed `check_visuals_exist` model_validator from `Card`. Removed
  `ValidationInfo` and `model_validator` pydantic imports. Added `portfolio_mode: bool = False`
  to `CardRepo.__init__`. Added post-append visual disk check in `CardRepo._load()`: non-portfolio
  mode appends `ValidationError` to errors (card still in `repo.cards`); portfolio mode skips
  (renderer handles with placeholder).
- `scripts/pcli.py`: `cmd_build_portfolio` now uses `CardRepo(REPO_ROOT, portfolio_mode=True)`
  directly (bypasses `_repo()` helper which stays strict for validate/ls/show/resume).
- `tests/test_card.py`: Replaced `test_visuals_path_missing` with
  `test_visuals_path_missing_validate_mode` (CardRepo approach) and added
  `test_visuals_path_missing_portfolio_mode`. Renamed `test_visuals_no_context` to
  `test_visuals_schema_accepts_missing_path` to reflect the new model semantics.
- `tests/test_cli.py`: Added `test_build_portfolio_missing_visual_does_not_fail`.
自動チェック: pytest 77/77 ✅ / ruff check ✅ / ruff format ✅

RESOLVED: ISSUE-2 — Layout validated before `--dry-run`
- `scripts/pcli.py`: Added `if layout not in frozenset({"one-per-card"})` guard in
  `cmd_build_portfolio` before the `if dry_run: return` early exit. Exits with code 2.
  `build_portfolio()` in `render_portfolio.py` retains its own check as defense-in-depth.
- `tests/test_cli.py`: Added `test_build_portfolio_unsupported_layout_exits_nonzero`.
自動チェック: pytest 77/77 ✅ / ruff check ✅ / ruff format ✅

RESOLVED: ISSUE-3 — Output artifacts separated into subdirectories
- `scripts/pcli.py`: Default resume path → `output/resumes/resume-<ts>.pdf`; default portfolio
  path → `output/portfolios/portfolio-<ts>.pptx`. Both use `mkdir(parents=True, exist_ok=True)`.
  `--out` override behavior preserved exactly.
- `scripts/render_resume.py`: Fallback default updated to `output/resumes/resume-<ts>.pdf`.
- `scripts/render_portfolio.py`: Fallback default updated to `output/portfolios/portfolio-<ts>.pptx`.
- `tests/test_cli.py`: Added `test_build_portfolio_default_output_in_portfolios_subdir`.
自動チェック: pytest 77/77 ✅ / ruff check ✅ / ruff format ✅
