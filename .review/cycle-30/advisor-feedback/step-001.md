# Advisor Feedback: Cycle 30 Step-001 — Fit Signals Approach

Type: Approach check
Scope: scripts/static/workspace.js, scripts/templates/workspace.html,
       tests/test_cycle30.py

## Query

Tokenization granularity, coverage formula, listener wiring location.

## Advisor Guidance

1. Tokenization: split on non-word boundaries, lowercase, keep tokens where `len>2 &&
   !stopWord`. Strip protocol/`www.` from URLs and keep meaningful domain words
   (`github`, `vercel`) as tokens, but drop TLDs (`com`, `io`, `dev`) via stopword list.
2. Coverage formula: use target-coverage `|T ∩ C| / |T| * 100`, not Jaccard. Jaccard
   unfairly penalizes cards with rich evidence; plan asks "how much of the target is
   covered."
3. Listener wiring: separate `_wsWireTargetListeners()` called from init block, not
   inside `loadWorkspaceCards()`. Static target fields exist at DOMContentLoaded so no
   late-render miss.

## Decision

Applied all three guidance points.

## Sonnet Response

- 적용: 1, 2, 3 모두 적용.
- 무시: 없음.
