# Step 043 — Cycle-12 Studio Editable Preview Approach check

Cycle: 12
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Editable fields: plain <input> for title, <textarea> for summary/resume_bullet/portfolio_body. No contenteditable.
2. Source chips: detect from raw textarea, update on input event with ~200ms debounce.
3. Edited field persistence tests: POST directly to /api/studio/save with custom draft (not via refine). Isolates persistence assertion.
4. Build action test: test HTML hooks exist + save response wires selected_ids to build call. Skip re-testing /api/build (covered in test_dashboard.py).
5. Collect edited values from fields in save() before POST; verify each field round-trips to frontmatter/body/narrative slot.

## Sonnet Response
- input for title, textarea for summary/resume_bullet/portfolio_body.
- Chips on raw input event with 200ms debounce.
- Persistence tests POST directly to /api/studio/save with custom draft.
- Build test: HTML hooks + selected_ids wiring only.
- 구현 시작.
