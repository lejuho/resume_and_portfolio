# Codex Review v1

## Verdict

BLOCKED

Cycle 5 has useful polish work and the automated suite passes, but the implementation does not fully satisfy the plan's input validation contract. In particular, non-positive `--max-items` is only validated for resume builds, not portfolio builds.

## Findings

### 1. BLOCKER: `pcli build portfolio --max-items` accepts zero and negative values

- File: `scripts/pcli.py:515`
- Plan requirement:
  - "Ensure `--max-items` rejects zero/negative values with a clear error."
  - Sprint Contract: "Invalid `--tone`, `--lang`, `--layout`, and non-positive `--max-items` are rejected with actionable messages."
- Current behavior:
  - `uv run pcli build resume --max-items 0 --dry-run` correctly fails.
  - `uv run pcli build portfolio --max-items 0 --dry-run` exits 0 with `No cards selected`.
  - `uv run pcli build portfolio --max-items -1 --dry-run` exits 0 and selects cards because Python slicing treats `[:-1]` as "all but last".
- Why this matters:
  - Negative values silently produce plausible but incorrect output.
  - Tests only cover resume `--max-items`, so the portfolio path regressed against the plan.
- Suggested fix:
  - Add the same positive-integer guard to `cmd_build_portfolio` after preset/default resolution.
  - Add tests for portfolio `--max-items 0` and `--max-items -1`.
  - If presets can provide `max_items`, ensure both resume and portfolio reject invalid preset values too.

### 2. MEDIUM: "No cards selected" still exits 0 despite Cycle 5 error UX contract

- File: `scripts/pcli.py:400`, `scripts/pcli.py:588`
- Plan requirement:
  - Error UX normalization includes "no selected cards".
  - Exit code behavior says validation/user input errors should exit 1.
- Current behavior:
  - `uv run pcli build resume --types no-such-type --dry-run` exits 0.
  - `uv run pcli build portfolio --types no-such-type --dry-run` exits 0.
- Suggested fix:
  - Decide whether "empty selection" is valid informational output or a user input error.
  - If following this Cycle 5 plan strictly, change build commands to exit 1 when filters produce no selected cards and add tests.
  - If keeping exit 0 intentionally, update the plan/README/review notes to state that empty selection is non-error.

## Sprint Contract Check

- README explains current v1, not just Phase 1: PASS
- Public command groups respond to `--help`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run pcli build resume --preset bok-interview`: PASS
- `uv run pcli build portfolio --tags web3`: PASS
- Non-LLM commands pass without `ANTHROPIC_API_KEY`: PASS
- LLM build flags fall back without API key; `llm tailor` errors clearly without key/cache: PASS
- Invalid `--tone` / `--lang`: PASS
- Invalid `--layout`: PASS
- Non-positive resume `--max-items`: PASS
- Non-positive portfolio `--max-items`: FAIL

## Automatic Checks

- `uv run pytest -v`: PASS, 134 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli --help`: PASS
- `uv run pcli build resume --help`: PASS
- `uv run pcli build portfolio --help`: PASS
- `uv run pcli preset --help`: PASS
- `uv run pcli llm --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run pcli build resume --preset bok-interview`: PASS
- `uv run pcli build portfolio --tags web3`: PASS

## Notes

- `.gitignore` now no longer ignores `.review/`, which matches the project workflow decision to keep review artifacts in git.
- Because of that change, several older `.review/*` files are now visible as untracked. They should be either added intentionally or explicitly ignored if they are local-only artifacts.
- Pre-existing untracked files remain: `.claude-flow/`, `.mcp.json`, `CLAUDE.md`.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Add `--max-items` guard to `cmd_build_portfolio`
- `scripts/pcli.py`: added `if max_items is not None and max_items < 1: raise typer.BadParameter(...)` after preset/default resolution in `cmd_build_portfolio` (mirrors the resume guard exactly)
- `tests/test_build_dry_run.py`: added `test_portfolio_max_items_zero_rejected` and `test_portfolio_max_items_negative_rejected`

RESOLVED: ISSUE-2 — "No cards selected" exits 1 in both build commands
- `scripts/pcli.py` line ~401 (`cmd_build_resume`): `raise typer.Exit(0)` → `raise typer.Exit(1)`
- `scripts/pcli.py` line ~591 (`cmd_build_portfolio`): `raise typer.Exit(0)` → `raise typer.Exit(1)`
- Confirmed no build tests were asserting `exit_code == 0` for empty selection (only `test_ls_type_filter` uses `ls` command, not affected)

자동 체크: pytest 136/136 ✅ / ruff check ✅ / ruff format ✅
