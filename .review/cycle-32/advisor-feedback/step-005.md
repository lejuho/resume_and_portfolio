# Advisor Feedback: Cycle 32 Step-005 — review-v2 Fix Approach

Type: Approach check
Scope: ISSUE-1 and ISSUE-3 from .review/cycle-32/review-v2.md

## Questions posed

1. ISSUE-1: Add "google-genai>=1.0" to [dependency-groups] dev so plain "uv sync" installs it.
   google-genai would then appear in both llm extra and dev group. Risk: uv.lock conflict or
   duplication warning?
2. ISSUE-3: Switch test_keyboard_tab_sequence_reaches_controls to narrow_ws_page (disclosure
   visible). Start from document.body.focus() then Tab loop ≤50 iterations. Assert all 5:
   theme-toggle, checkbox, target-field, disclosure (aria-expanded attr), generate-btn.
   Risk: body.focus() Tab start; disclosure button tab participation when visible.

## Advisor Response (Opus)

1. Add "google-genai>=1.0" to [dependency-groups] dev. Run uv lock then uv sync — no conflict;
   extra+group sharing one package is normal in uv, lockfile dedups, no duplication warning.
   Verify uv sync (no extras) imports google.genai.
2. Switch to narrow_ws_page (disclosure visible/focusable). Replace programmatic focus with
   page.evaluate("() => document.body.focus()"); first Tab then enters DOM order from top —
   valid start. Loop ≤50; visible disclosure button is a real <button>, so it participates in
   tab order; assert all 5 via id/type/aria-expanded.

## Sonnet Response

- 적용: 2가지 접근법 확인. uv dev+extra 중복은 정상 동작, body.focus() + Tab 유효 시작점,
  narrow_ws_page에서 disclosure button tab 참여.
- 무시: 없음.
