# Advisor Feedback: Cycle 28 Step-002 — Design Token Alignment Completion

Type: Completion check
Scope: scripts/templates/workspace.html, scripts/static/workspace.js,
       tests/test_cycle28.py

## Completion Check (after implementation)

Changes applied:
1. `workspace.html`: `:root` block defines `--ws-bg`, `--ws-surface`, `--ws-text`,
   `--ws-text-muted`, `--ws-accent`, `--ws-border`, `--ws-border-thin`,
   `--ws-radius-md`, `--ws-radius-lg`. Hard-coded repeated values replaced with
   token variables throughout.
2. `workspace.html`: all `font-weight: 600` removed; changed to 500 in
   `.ws-pane-title`, `.ws-section h3`, `.ws-coverage-label`, `.ws-coverage-value`.
3. `workspace.js`: card markup emits `ws-card-pill`, `ws-card-title`,
   `ws-card-context`, `ws-card-meta`. Card body uses a sibling
   `<label class="ws-card-body" for="...">` — checkbox is a preceding sibling `<input>`
   linked via `for=` id attribute, not label-wrapping (see step-001 deviation note).
4. `workspace.js`: `_wsOnCardToggle(cb)` receives checkbox element, finds
   `.closest(".ws-card-item")`, toggles `ws-card-selected` class.
5. `tests/test_cycle28.py`: 17 tests covering token definitions (5),
   font-weight/case compliance (3), card markup classes (4), selected-state (1),
   Cycle 27 preservation (4).

Regression verification:
1. Cycle 27 tests never assert `ws-card-title`/`ws-card-meta`; all JS source
   contracts (`Array.isArray`, `status === "live"`, no `data.cards`, no `studio.js`,
   no `st-app-`) still hold. ✓
2. `window._wsOnCardToggle = _wsOnCardToggle` exposure unchanged; `(cb)` signature
   with `onchange="_wsOnCardToggle(this)"` works correctly. ✓
3. `ws-card-body` is an untested structural addition — acceptable by plan. ✓
4. 564 total tests pass, ruff check ✓, ruff format ✓, pcli validate ✓. ✓

## Advisor Verdict

PASS

## Sonnet Response

- 적용: 모든 3개 regression concern 확인 완료.
- 무시: 없음.
