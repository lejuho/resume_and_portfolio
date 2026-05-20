# Step 009 — Cycle-3 Phase 3 implementation approach

Cycle: 3
Pass: 1
Files Changed: (not yet — approach only)

## Advisor Verdict
PASS

## Advisor Feedback
1. Sentinel-as-unset is correct. Use `None` for Optional; for `max_items`, default the Typer
   param to `None` and resolve to 12 only after preset merge. Precedence: CLI > preset > built-in
   default.
2. Hard fail. Collect ALL missing cards first, then exit 1 with single error listing every
   offender (not first-fail). Better DX than fix-one-rerun loop.
3. Dispatcher in same file. Add `render(layout=...)` dispatching to private
   `_render_default/_grouped/_timeline`. Extract shared helpers (cover, closing, card_slide)
   to module top. Keeps single import path; matches plan wording.
   Caveat: if any `_render_*` exceeds ~150 LOC, split into separate files with dispatcher.

## Sonnet Response
- 적용: None-sentinel for CLI overrides; max_items defaults to None in Typer, resolved post-merge.
  Hard fail collecting all missing summary_ko cards before exit. Dispatcher pattern in default.py.
- 무시: n/a
