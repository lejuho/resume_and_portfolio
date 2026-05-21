# Step 044 — Cycle-12 Studio Editable Preview Completion check

Cycle: 12
Pass: 1
Files Changed: scripts/templates/studio.html, scripts/static/studio.js, tests/test_studio.py

## Advisor Verdict
OK

## Advisor Feedback
1. st-save-btn uses hidden attribute instead of CSS display:none — no test checks display style. Safe.
2. .code → .mi-code rename: template and test aligned, no .code references remain.
3. renderPreview() JS-only change — no server impact.
4. selected_ids test and st-build-output present and aligned. 4/4 concerns clear.

## Sonnet Response
- All concerns clear. 224 tests pass, ruff clean.
- Cycle-12 complete.
