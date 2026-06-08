# Advisor Feedback: Cycle 32 Step-004 — review-v1 Fixes Completion

Type: Completion check
Scope: docs/acceptance-studio.md, tests/browser/conftest.py,
       tests/browser/test_workspace_browser.py, docs/test-cases.md

## Changes Applied

1. `docs/acceptance-studio.md`: Added "Dependency sync: uv sync --extra llm" row to both
   Automated Baseline tables (main + Workspace section). Resolves ISSUE-1.
2. `tests/browser/conftest.py`: monkeypatch_session → monkeypatch_module (scope="module");
   server → scope="module" with try/finally teardown; narrow_ws_page fixture added (320px
   viewport, fresh context, try/finally context.close). Resolves ISSUE-2 and ISSUE-5.
3. `tests/browser/test_workspace_browser.py`:
   - TC-WS-013: 4 .focus() tests replaced with test_keyboard_tab_sequence_reaches_controls
     (Tab loop, set superset assert) + 3 ARIA tests. Resolves ISSUE-3.
   - TC-WS-016: parametrize over all 5 field IDs (was single field). Resolves ISSUE-4.
   - TC-WS-017/018/019: all disclosure tests use narrow_ws_page; no pytest.skip; no
     btn.evaluate("el.hidden=false"). Resolves ISSUE-5.
   - Preview: test_preview_payload_and_no_persistence captures request via page.on("request")
     and asserts output_type/card_ids/target_context. Resolves ISSUE-6.
4. `docs/test-cases.md`: TC-WS-013 evidence → "Browser (Cycle 32): Tab nav + ARIA";
   TC-WS-017 evidence notes 320px deterministic, zero skips; TC-WS-020 → "Browser (Cycle 32)".

## Test Results

- `uv run pytest tests/browser/test_workspace_browser.py -v`: 26 passed (was 22; +4 from
  5-field parametrize).
- `uv run --extra llm pytest -q`: 638 passed, 0 failed, 7 warnings. No regressions.
- `uv run ruff check scripts tests`: clean.
- `uv run ruff format --check scripts tests`: 40 files already formatted.

## Advisor Verdict (Opus)

PASS — all three regression concerns verified safe:
1. Module teardown ordering: pytest guarantees module fixture teardown before next module's
   setup — no cross-module REPO_ROOT leak.
2. narrow_ws_page finally: context.close() runs even on mid-test raise — no context leak.
3. page.on("request") timing: handler registered before goto; request fired during button
   click and awaited by out.wait_for before asserts — no post-assert race.

## Sonnet Response

- 적용: 3가지 regression concern 모두 safe 확인.
- 무시: 없음.
