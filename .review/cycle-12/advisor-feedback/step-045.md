# Step 045 — Cycle-12 review-v1 fix Completion check

Cycle: 12
Pass: 2
Files Changed: scripts/static/studio.js, tests/test_studio.py

## Advisor Verdict
OK

## Advisor Feedback
1. renderPreview(): saveBtn.disabled=false + textContent reset confirmed at studio.js:108-110.
2. _savedId=null in renderPreview + buildCard guard confirmed — prevents stale build calls.
3. st-build-output cleared confirmed.
4. New test asserts both reset strings present. Fix correct and complete.

## Sonnet Response
- All concerns clear. 225 tests pass, ruff clean.
- Committing.
