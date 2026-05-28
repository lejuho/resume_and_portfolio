# Advisor Feedback: Cycle 22 Step-001 — Studio UI Contract Smoke Tests

Type: Approach check + Completion check
Scope: tests/test_cycle22.py (new file)
Plan baseline: Cycle 22 plan.md — Studio UI contract smoke-test layer

## Approach Check (before implementation)

Query: test grouping (one per contract area vs monolithic); Group F justification; redundancy
with cycle-21 tests.

Key guidance received:
1. One test per group (A-F) — distinct failure signals; avoid bundling unrelated assertions.
2. Group F (API-level) justified: asserts new response fields `answer_draft`, `character_count`,
   `refine_source`, `selected_cards` shape. Cycle 21 covered endpoint URL + hook presence, not
   live JSON shape.
3. Drop redundancy: skip re-asserting endpoint URL string in B (cycle 21 has it) and
   `selected_cards` render hook string in C (cycle 21 has it). Assert only new DOM IDs and
   new JS behaviors.

Decision: Applied all three guidance points. 6 tests total.

## Completion Check (after implementation)

New file: `tests/test_cycle22.py`

Tests written:
- **A** `test_studio_js_load_app_cards_source_contract` — asserts `/api/cards` fetch URL,
  `st-app-card-selector` DOM target, `No live cards found` empty state, `Could not load cards`
  error state all present in JS source.
- **B** `test_studio_js_generate_preview_target_context_contract` — asserts all seven
  target-context DOM field IDs (`st-app-organization`, `st-app-role`, `st-app-question`,
  `st-app-competency`, `st-app-jd`, `st-app-charlimit`, `st-app-blind`) and JSON body keys
  (`target_context`, `card_ids`, `output_type`) present in JS source.
- **C** `test_studio_js_render_preview_draft_and_counts_contract` — asserts `answer_draft`,
  `_appDraftText`, `st-app-draft-text`, `st-app-missing-info`, `character_count`,
  `st-app-char-status` present in JS source.
- **D** `test_studio_js_copy_draft_separation_contract` — asserts
  `navigator.clipboard.writeText(_appDraftText)` (copy source is verified draft), `ai_guidance`
  rendered separately, `preview.answer_draft` assignment in JS source.
- **E** `test_studio_html_app_writing_hook_ids` — GET /studio; asserts seven key DOM IDs
  present in HTML (`st-app-card-selector`, `st-app-preview-btn`, `st-app-result`,
  `st-app-draft-text`, `st-app-copy-btn`, `st-app-missing-info`, `st-app-guidance-section`).
- **F** `test_studio_app_writing_preview_response_fields` — GET /api/cards to get live card id;
  POST to /api/studio/application-preview; asserts 200 + ok=True + `answer_draft` (str),
  `character_count` (int), `refine_source` in ("mock","llm"), `selected_cards` is list.

Sprint contract coverage:
- Selector contract (array-vs-object catch): A + existing cycle-21 guards ✓
- Submit contract (target context fields, JSON body): B ✓
- Render contract (draft, counts, missing-info): C ✓
- Copy separation (draft only, not guidance): D ✓
- HTML DOM hooks: E ✓
- API-level end-to-end response shape: F ✓

## Decision

PROCEED. 476 tests pass (470 → +6). All checks green.

Auto checks: pytest ✅ 476 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
