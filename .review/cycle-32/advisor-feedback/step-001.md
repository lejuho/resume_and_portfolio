# Advisor Feedback: Cycle 32 Step-001 — Browser Tests Approach

Type: Approach check
Scope: tests/browser/conftest.py, tests/browser/test_workspace_browser.py,
       pyproject.toml, docs/test-cases.md, docs/acceptance-studio.md,
       requirements-dashboard.md (D-018)

## Approach Check (before implementation)

Key judgment points:

1. **REPO_ROOT monkeypatch**: `monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)` before
   `make_server` is correct — Python globals resolve at call time, so patching the module
   attribute works for all usages in `dashboard.py`.

2. **Card load wait**: `wait_for_selector(".ws-card-item")` alone is racy vs
   `_wsUpdateCoverage` running after async fetch. Also wait for `.ws-card-count` to show
   non-zero text (e.g. `page.wait_for_function(...)`) to guarantee coverage calc ran.

3. **Disclosure geometry**: Do NOT depend on `-webkit-line-clamp` geometry in headless
   Chromium — flaky/font-dependent. Instead test `_wsToggleCardDetails` state toggle
   explicitly (check `aria-expanded` attribute and button text changes).

## Advisor Verdict

PROCEED — all three judgment points resolved.

## Sonnet Response

- 적용: monkeypatch 순서, card-count wait, disclosure 방식 3가지 결정 모두 수용.
- 무시: 없음.
