# Advisor Feedback: Cycle 32 Step-003 — review-v1 Fix Approach

Type: Approach check
Scope: ISSUE-1..6 from .review/cycle-32/review-v1.md

## Questions posed

1. ISSUE-2 session→module scope: server fixture scope="module" so teardown runs after browser
   module and before test_cycle*.py modules. live_repo stays session; monkeypatch_session renamed
   monkeypatch_module with scope="module". Risk: does pytest guarantee module teardown order is
   before next-module setup?
2. ISSUE-5 narrow viewport: add narrow_ws_page fixture (viewport 320px wide) to guarantee
   -webkit-line-clamp overflow without pytest.skip or btn.evaluate("el.hidden=false"). Risk:
   headless Chromium layout at 320px — does clientHeight still reflect 2-line clamp properly?
3. ISSUE-6 payload: page.on("request", handler) passive observer captures POST body while still
   allowing Flask to handle it. post_data parsed with json.loads. Risk: request event fires
   before post_data is populated?
4. ISSUE-3 Tab navigation: ws_page.keyboard.press("Tab") from #ws-theme-toggle focus, collect
   reached={checkbox, target-field, generate-btn}, assert all three found. Risk: unknown DOM order.

## Advisor Response (Opus)

1. live_repo session OK; module fixtures: pytest guarantees module teardown finalizes before next
   module's setup — order safe. Rename to monkeypatch_module, scope="module".
2. Verify 320px clamp: assert scrollHeight>clientHeight on clamped el, not viewport hiding.
   Headless Chromium honors line-clamp; add explicit width on container.
3. Capture POST via page.on("request"): post_data IS populated at request event (Playwright
   buffers it). Use request.post_data_json; passive, Flask still serves.
4. Tab nav: don't assume order; press Tab in loop (max ~15), collect focused ids into set,
   assert superset of the three. Avoids DOM-order coupling.

## Sonnet Response

- 적용: 4가지 접근법 확인. module scope teardown 순서 보장, 320px viewport line-clamp 검증,
  post_data_json 사용, Tab 루프 + set 수집 방식.
- 무시: 없음.
