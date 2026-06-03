# Advisor Feedback: Cycle 27 Step-001 — Workspace Route Shell Approach

Type: Approach check
Scope: scripts/dashboard.py, scripts/templates/workspace.html, scripts/static/workspace.js,
       scripts/templates/dashboard.html, tests/test_cycle27.py

## Query

Dashboard link placement, DOM id namespace, coverage panel strategy, preview integration
depth, workspace.js structure.

## Advisor Guidance

1. Add `/workspace` link in dashboard.html alongside existing `/studio` — additive only.
2. All DOM ids prefixed `ws-` (e.g. `ws-card-list`) — zero overlap with `st-*` studio ids.
3. `ws-coverage-panel` div with static placeholder `0 / 0 themes matched` — no live logic.
4. Include `ws-generate-btn` + `ws-preview-out` hooks; skip application-preview wiring (shell-first).
5. `loadWorkspaceCards()` with `Array.isArray` guard + `filter(status === "live")`; one
   `generateWorkspacePreview()` stub; no studio.js imports.

## Decision

Applied all five guidance points with one deviation (see correction below).

## Sonnet Response

- 적용: 1, 2, 3, 5 항목 적용.
- 무시: 4번 항목의 "skip application-preview wiring" 부분.
- 수정 (ISSUE-2 해결): Cycle 27 plan은 "Workspace may call the existing
  /api/studio/application-preview endpoint" 및 "shell-first is acceptable"을 모두
  허용했다. 어드바이저 guidance는 "skip" 권고였으나, plan의 명시적 허용 범위 내에서
  generateWorkspacePreview()가 /api/studio/application-preview를 최소 수준으로
  호출하도록 구현했다. 이 deviation을 당시 step에 기록하지 않은 것이 ISSUE-2의 원인.
  plan이 허용한 범위이므로 구현 자체는 scope 위반이 아니나, 어드바이저 guidance에서
  벗어난 결정은 명시적으로 기록되었어야 했다.
