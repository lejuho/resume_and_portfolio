# Step 041 — Cycle-11 Studio MVP Completion check

Cycle: 11
Pass: 1
Files Changed: scripts/dashboard.py, scripts/templates/studio.html, scripts/static/studio.js, tests/test_studio.py

## Advisor Verdict
OK (with 3 concerns checked)

## Advisor Feedback
1. Regression #1: grep tests/routes for fm.Post(metadata=); confirm no test asserts old nesting. Check other fm.Post call sites.
2. Regression #2: grep tests for /dashboard; confirm no test asserts 404 pre-cycle. Verify index() query-param handling unchanged.
3. Regression #3 (critical): Add cross-month collision guard in api_studio_save (reuse cycle-9 uniqueness check), or document gap as DEFER.

## Sonnet Response
- Concern #1 CLEAR: both fm.Post call sites (api_card_create:206, api_studio_save:512) now use content= only, then post.metadata = meta. No test references old nesting.
- Concern #2 CLEAR: no existing test ever asserts 404 on /dashboard; alias delegates to index() unchanged. Studio test verifies /dashboard link presence and 200 response.
- Concern #3 CLEAR: api_studio_save already uses cards_dir.glob("????-??-{card_id}.mdx") at line 496 — same cross-month guard from cycle-9. test_studio_save_duplicate_id_rejected covers this.
- fm.Post nesting bug also fixed in api_card_create (was writing metadata nested under 'metadata:' key in YAML; no existing test caught this because none reloaded CardRepo after POST).
- 212 tests pass, ruff clean, pcli validate clean.
