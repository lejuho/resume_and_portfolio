# Advisor Feedback: Cycle 32 Step-002 — Browser Tests Completion

Type: Completion check
Scope: tests/browser/conftest.py, tests/browser/test_workspace_browser.py,
       pyproject.toml, .gitignore, docs/test-cases.md, docs/acceptance-studio.md,
       requirements-dashboard.md (D-018)

## Completion Check (after implementation)

Changes applied:
1. `pyproject.toml`: `playwright>=1.49` and `pytest-playwright>=0.6` added to dev group.
2. `tests/browser/__init__.py`: empty package marker.
3. `tests/browser/conftest.py`: session-scoped ephemeral Flask server via
   `werkzeug.serving.make_server("127.0.0.1", 0, app)`. `monkeypatch_session` patches
   `dash_mod.REPO_ROOT` to `live_repo` before server start. 2 live card fixtures
   (auth-service short summary; search-platform 178-char `>-` scalar, `type: other` evidence)
   + 1 draft excluded by live filter. `ws_page` fixture with 5 s timeout guards on
   `.ws-card-item` and card-count wait.
4. `tests/browser/test_workspace_browser.py`: 22 tests covering TC-WS-010 through TC-WS-019
   plus containment, live-card filter, preview+no-persistence. All 22 pass.
5. `.gitignore`: `.playwright/`, `test-results/`, `playwright-report/` added defensively.
6. `docs/test-cases.md`: TC-WS-010 through TC-WS-019 evidence-strength updated to
   "Browser (Cycle 32)"; TC-WS-012 documents headless CSS pseudo-class limitation.
7. `docs/acceptance-studio.md`: browser test command added to automated Workspace baseline.
8. `requirements-dashboard.md`: D-018 decision added (browser integration driver boundary).

Regression verification:
1. Pre-existing 9 google.genai failures confirmed on base branch via git stash run.
   625 passed (612 + 22 browser) + 9 pre-existing. No new failures introduced. ✓
2. `monkeypatch_session.undo()` in yield-fixture teardown restores `REPO_ROOT` reliably
   even on test panic — pytest finalizers always run. ✓
3. No playwright binary artifacts in repo — `.playwright/` and `test-results/` now in
   `.gitignore`; `git status` clean. ✓

## Advisor Verdict

PASS — residual items applied: gitignore entries added, timeout guards on ws_page fixture.

## Sonnet Response

- 적용: 3가지 regression concern 확인. gitignore 방어적 추가, ws_page timeout guard 5s 적용.
- 무시: 없음.
