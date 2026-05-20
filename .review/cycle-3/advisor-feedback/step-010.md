# Step 010 — Cycle-3 Phase 3 implementation completion

Cycle: 3
Pass: 1
Files Changed: scripts/preset.py, scripts/select.py, scripts/pcli.py, templates/portfolio/default.py,
               templates/resume/bok.typ, presets/*.yaml, tests/test_preset.py, tests/test_cli.py

## Advisor Verdict
NEEDS_REVIEW

## Advisor Feedback
1. CliRunner re-invocation in preset run is fragile: spawns fresh Typer context that won't inherit
   pytest's monkeypatched REPO_ROOT. Refactor to call build function directly.
2. dry-run leniency hides CI regressions for bok validation. Add --strict / CI=true detection to
   escalate warning to error.
3. Wrong order: exclude_ids applied after max_items slice. Apply exclude_ids BEFORE max_items so
   cap reflects user's intended count.

## Sonnet Response
- 적용 (1): Refactor cmd_preset_run to call cmd_build_portfolio/cmd_build_resume directly as Python
  functions (Typer decorators don't wrap the function, it's still callable). Avoids CliRunner nesting.
- 무시 (2): --strict/CI detection deferred. Not in sprint contract; dry-run warning behavior is
  acceptable for current scope. Can be added in a future cycle.
- 적용 (3): Fix select.py to apply exclude_ids before max_items slicing.
