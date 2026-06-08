# Advisor Feedback: Cycle 32 Step-006 — review-v2 Fixes Completion

Type: Completion check
Scope: pyproject.toml, uv.lock, tests/browser/test_workspace_browser.py

## Changes Applied

1. `pyproject.toml`: "google-genai>=1.0" added to [dependency-groups] dev.
   `uv.lock` updated via `uv lock && uv sync`. google-genai appears in both llm extra and
   dev group; uv lockfile deduplicates correctly. Plain `uv sync` now installs google-genai
   and the Google SDK tests pass without --extra llm. Resolves ISSUE-1.
2. `tests/browser/test_workspace_browser.py`: test_keyboard_tab_sequence_reaches_controls
   converted from ws_page to narrow_ws_page (disclosure naturally visible); programmatic
   .focus("#ws-theme-toggle") replaced with document.body.focus() (neutral start); loop
   extended to 50; 5-category assertion: theme-toggle, checkbox, target-field, disclosure
   (aria-expanded attr), generate-btn. Resolves ISSUE-3.

## Test Results

- `uv sync` (plain, no extras): google.genai importable; 133 Google SDK tests pass.
- `uv run pytest tests/browser/test_workspace_browser.py -v`: 26 passed.
- `uv run pytest -q`: 638 passed, 0 failed, 7 warnings. No regressions.
- `uv run ruff check scripts tests`: clean.
- `uv run ruff format --check scripts tests`: 40 files already formatted.

## Advisor Verdict (Opus)

PASS — all three regression concerns verified safe:
1. anthropic stays llm-extra-only; plain uv sync does not install it. No dependency leak.
2. 320px viewport (narrow_ws_page) changes layout only, not DOM tab order. Disclosure
   reachable via Tab as expected.
3. document.body.focus() + first Tab enters DOM order from top on headless Chromium Windows.
   theme-toggle assertion passed.

## Sonnet Response

- 적용: 3가지 regression concern 모두 safe 확인.
- 무시: 없음.
