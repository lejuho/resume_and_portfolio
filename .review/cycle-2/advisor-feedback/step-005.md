# Step 005 — Cycle-2 ISSUE-1/2/3 fix approach

Cycle: 2
Pass: 2
Files Changed: scripts/card.py, scripts/pcli.py, scripts/render_portfolio.py, scripts/render_resume.py

## Advisor Verdict
PASS

## Advisor Feedback
1. Skip-context flag is right; cleaner: drop disk validation from card.py entirely, model only
   validates path syntax. Visual existence = renderer concern + one post-load scan in CardRepo.
   `portfolio_mode` then only toggles whether scan emits warnings vs errors.
2. Use Typer enum/`Literal` constraint — rejects bad input before any dry-run logic,
   self-documents, frees `build_portfolio()` from the check. Keep one assert in `build_portfolio()`
   as defense-in-depth.
3. Change the single source of truth. If `pcli.py` computes its own default, fix there and have
   render_*.py accept the passed path; avoid duplicate timestamp/dir logic in two places.

## Sonnet Response
- 적용: Remove check_visuals_exist from Card model; CardRepo post-load visual scan with
  portfolio_mode flag; layout guard before dry-run; subdirectory default output paths.
- 무시: Typer enum approach for layout (used simple frozenset check instead) — simpler,
  fewer moving parts, achieves same validation before dry-run.
