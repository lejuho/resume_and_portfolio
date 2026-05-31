# Advisor Feedback: Cycle 25 Step-001 — Application Writing Export Approach

Type: Approach check
Scope: scripts/templates/studio.html, scripts/static/studio.js, tests/test_cycle25.py,
       docs/acceptance-studio.md

## Query

Packet format (include/exclude AI guidance); storage variable choice; export mechanism;
export button placement; test strategy for blind-hiring and no-persistence guarantees.

## Advisor Guidance

1. Init `_appLastPreview = null` (module-level, beside `_appDraftText`); set inside `renderAppPreview`.
2. `_buildHandoffPacket(preview)` pure fn returns string; include AI guidance under explicit
   `ADVISORY (AI-generated, verify):` header — labeled, not excluded.
3. Packet reads `selected_cards[].display_title`/safe labels only, never `_appCards`/raw evidence.
4. Export: `Blob`+`createObjectURL`+`<a download>` in try → catch falls back to
   `navigator.clipboard.writeText(packet)`; render packet into new `<pre id="st-app-export-out">`
   below button (no alert).
5. Button `st-app-export-btn`, `hidden=false` in `renderAppPreview`, beside copy btn.
6. Tests: JS source-inspection (reads `display_title`, opaque refs) + Python asserting no
   `application-packet` route, `application_preview_does_not_create_card_file` green.

## Decision

Applied all six guidance points.

## Sonnet Response

- 적용: 모든 6개 항목 적용.
- 무시: 없음.
