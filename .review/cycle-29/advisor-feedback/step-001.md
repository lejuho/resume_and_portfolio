# Advisor Feedback: Cycle 29 Step-001 — Dark Polish Approach

Type: Approach check
Scope: scripts/templates/workspace.html, tests/test_cycle29.py

## Query

Remaining hard-coded one-offs before dark block, focus-visible placement, dark accent value.

## Advisor Guidance

1. Tokenize remaining one-offs first (`#4a5568` → `--ws-coverage-muted` token, input border
   `rgba(0, 0, 0, .12)` → `--ws-border-strong` token); review will flag them when adding dark block.
2. Use `.ws-card-item input[type="checkbox"]:focus-visible` for focus ring; `:focus-within` is
   too broad and won't show on keyboard-tab to the checkbox itself.
3. Lighten `--ws-accent` in dark (e.g. `#6aa8e8`); dark backgrounds drop saturated-blue contrast
   below WCAG AA with identical value. Also adjust tint/border alpha.

## Decision

Applied all three guidance points.

## Sonnet Response

- 적용: 1, 2, 3 모두 적용.
- 무시: 없음.
