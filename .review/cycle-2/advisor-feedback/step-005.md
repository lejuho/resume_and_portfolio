---
cycle: 2
step: "005"
type: approach
---

## Approach check: cycle-2 review fixes — ISSUE-1, ISSUE-2, ISSUE-3

### Advisor response (≤100 words)

1. Skip-context flag is right; cleaner: drop disk validation from card.py entirely, model only
   validates path syntax. Visual existence = renderer concern + one post-load scan in CardRepo.
   `portfolio_mode` then only toggles whether scan emits warnings vs errors.
2. Use Typer enum/`Literal` constraint — rejects bad input before any dry-run logic,
   self-documents, frees `build_portfolio()` from the check. Keep one assert in `build_portfolio()`
   as defense-in-depth.
3. Change the single source of truth. If `pcli.py` computes its own default, fix there and have
   render_*.py accept the passed path; avoid duplicate timestamp/dir logic in two places.

### Applied decisions

- ISSUE-1: Remove `check_visuals_exist` model_validator from `Card`. Move disk check to
  `CardRepo._load()` post-append. `portfolio_mode=True` → no error added (renderer handles via
  placeholder); `portfolio_mode=False` → ValidationError added to errors (card still in cards).
- ISSUE-2: Simple `if layout not in SUPPORTED_LAYOUTS` guard before dry-run in
  `cmd_build_portfolio`, keep assert in `build_portfolio()` as defense-in-depth.
- ISSUE-3: Fix defaults in `pcli.py` (single source); update render_*.py defaults to match.
