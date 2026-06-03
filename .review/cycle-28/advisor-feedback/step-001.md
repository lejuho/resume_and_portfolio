# Advisor Feedback: Cycle 28 Step-001 — Design Token Alignment Approach

Type: Approach check
Scope: scripts/templates/workspace.html, scripts/static/workspace.js,
       tests/test_cycle28.py

## Query

`:root` token scope, card markup label pattern, selected-state toggle scope.

## Advisor Guidance

1. Define only the 5 plan-tested tokens (`--ws-accent`, `--ws-surface`, `--ws-border`,
   `--ws-radius-md`, `--ws-radius-lg`) in `:root`. Add spacing tokens only if cards/layout
   actually consume them; do not pre-declare unused `--ws-sp-*`.
2. Wrap card body in `<label class="ws-card-body">` containing checkbox + pill/title/context/meta.
   Label-wrapping gives a native click-to-toggle target; no JS needed for the toggle itself.
3. This cycle: add `ws-card-selected` class toggle in `_wsOnCardToggle()` plus existing
   gap-text update. Keep `ws-coverage-value` selected-count stub deferred to a later cycle.

## Decision

Applied guidance points 1 and 3. Point 2 applied with one deviation (see below).

## Sonnet Response

- 적용: 1, 3 항목 적용.
- 편차 (2번 항목): 어드바이저는 checkbox를 `<label class="ws-card-body">` 안에 포함하는
  label-wrapping 구조를 권고했다. 실제 구현에서는 checkbox를 sibling `<input>` 으로 두고
  `<label class="ws-card-body" for="ws-card-...">` 를 형제 요소로 배치했다.
  두 구조 모두 native click-to-toggle을 제공하며 기능적으로 동일하다.
  label-wrapping이 아닌 sibling input/label을 선택한 이유: `for=` 패턴은 id linkage가
  명시적이어서 접근성 확인이 쉽고, `onchange="_wsOnCardToggle(this)"` 에서 `this`가
  checkbox를 직접 가리켜 toggle 로직이 단순하다.
  이 deviation은 당시 step에 기록되지 않은 것이 ISSUE-2의 원인.
- 무시: 없음.
