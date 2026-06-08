# Workspace Browser Integration Test Driver Plan

Branch: feature/cycle-32-workspace-browser-tests

## Summary

Cycle 31 confirmed that backend/API integration is well covered, but Workspace JavaScript
interactions are mostly verified through source-string assertions. There is no executable browser
driver covering the chain:

```text
browser -> workspace.js -> Flask API -> temporary card repository
```

Cycle 32 adds that missing integration layer with Python Playwright and pytest. The tests run the
real Flask application against a temporary repository and exercise the real Workspace DOM and
JavaScript. Existing source-contract tests remain as fast regression guards.

This is test infrastructure and evidence strengthening only. It must not redesign Workspace,
change generation behavior, add persistence, or implement theme coverage/recommendations.

## Input/Output Specification

- Input:
  - Existing Flask `app` and `/workspace`, `/api/cards`,
    `/api/studio/application-preview` contracts.
  - Existing `workspace.html` and `workspace.js`.
  - Test-owned live-card fixtures under `tmp_path`, including long-text and matching-keyword
    cases.
  - A locally installed Playwright Chromium binary.
- Normal output:
  - Browser tests open a real ephemeral localhost server.
  - Tests execute card loading, selection, fit recomputation, disclosure, theme persistence,
    keyboard focus, containment, and preview request behavior through the DOM.
  - Tests leave canonical `cards/` and source files unchanged.
  - Browser tests produce deterministic pass/fail evidence and close the Cycle 31
    source-inspection gap for TC-WS-010 through TC-WS-019 where feasible.
- Failure:
  - Missing Playwright package or Chromium binary fails the dedicated browser preflight with an
    actionable installation command; it must not be reported as a behavior pass.
  - A server thread/port startup failure fails the fixture and always attempts cleanup.
  - Browser tests must not call a live AI provider; provider configuration is cleared or the
    application-preview call is safely intercepted only where the UI behavior does not require
    backend generation.

## Key Changes

- Explicit test tooling — `pyproject.toml`, `uv.lock`
  - Add `playwright` to the dev dependency group.
  - Updating `uv.lock` is explicitly authorized for this dependency addition only.
  - Do not add Node/npm tooling or a second lockfile.
  - Document one-time browser setup:
    `uv run playwright install chromium`.
- Browser fixtures — `tests/browser/conftest.py` or an equivalent focused helper
  - Build a temporary card repository with deterministic live fixtures.
  - Monkeypatch `scripts.dashboard.REPO_ROOT` before starting the server.
  - Start the real Flask app through Werkzeug `make_server` on `127.0.0.1` with an ephemeral
    port in a background thread.
  - Yield a base URL and guarantee shutdown/join cleanup.
  - Launch a fresh Chromium browser/context per appropriate test scope with no user profile,
    cookies, provider keys, or external network dependency.
  - Capture a screenshot/trace on failure when practical without committing generated artifacts.
- Executable behavior tests — `tests/browser/test_workspace_browser.py`
  - Card loading:
    - bare-array `/api/cards` response renders only live cards;
    - count and card labels are visible.
  - Selection and fit:
    - target input events plus checkbox selection update percentage and matched terms;
    - missing target, missing selection, and no-match messages are verified;
    - unchecking recomputes state.
  - Disclosure:
    - constrained viewport and long summary reveal `Show full summary`;
    - expand/collapse changes rendered state and button label;
    - disclosure click does not change checkbox state.
  - Theme:
    - manual dark toggle sets `data-ws-theme` and `localStorage`;
    - preference survives reload;
    - explicit light preference overrides a dark emulated OS scheme.
  - Keyboard/accessibility:
    - Tab navigation reaches theme toggle, card checkbox, target fields, disclosure when
      present, and Generate button;
    - checkbox/disclosure controls have accessible names and expected ARIA relationships;
    - custom focus styles are asserted only where the design specification promises them.
  - Containment:
    - long title/summary do not create horizontal overflow in the left pane/card container;
    - collapsed summary height is lower than expanded height.
  - Preview:
    - selecting a live card and filling required context sends the existing
      `/api/studio/application-preview` payload shape;
    - successful mock preview renders;
    - card file count is unchanged.
- Existing tests
  - Keep Cycle 27-30 source tests unless a browser test makes a specific assertion genuinely
    redundant and removal is justified in the advisor record.
  - Do not weaken bare-array, live-filter, no-`data.cards`, no-persistence, blind-hiring, or
    Studio regression coverage.
- Documentation
  - Update `docs/test-cases.md` evidence-strength cells for cases now covered by browser
    execution.
  - Update `docs/acceptance-studio.md` automated Workspace command and browser evidence status.
  - Do not modify the historical `.review/cycle-31/report-v1.md`; add gap-closure evidence only
    to Cycle 32 artifacts and current product/test documentation.
  - Add D-018 or equivalent current decision to `requirements-dashboard.md`: Workspace browser
    integration driver and its boundary.
- Product code:
  - No planned product-code changes.
  - If executable tests reveal a real defect, stop and report it in review rather than silently
    expanding this test-infrastructure cycle. A minimal testability hook requires explicit plan
    amendment.

## Sprint Contract

- Python Playwright is declared as a dev dependency; `uv.lock` changes only as required by that
  dependency.
- A documented preflight command installs Chromium:
  `uv run playwright install chromium`.
- Browser tests use a real ephemeral Flask server and a real temporary filesystem repository.
- No browser test reads or writes the user's canonical `cards/`.
- No browser test uses user cookies, an existing browser profile, or a live provider key.
- TC-WS-010 through TC-WS-019 are each:
  - covered by executable browser evidence, or
  - explicitly left manual with a concrete technical reason.
- Browser tests verify at minimum:
  - live-card rendering;
  - selected-state and fit recomputation;
  - disclosure expand/collapse and no selection side effect;
  - theme persistence and OS override;
  - keyboard focus/accessibility relationships;
  - long-text horizontal containment;
  - preview payload/render and no card persistence.
- Existing `/dashboard`, `/studio`, and `/workspace` routes remain HTTP 200.
- Existing source-contract and API tests remain green.
- Browser/server resources are cleaned up after success and failure.
- Generated screenshots/traces/cache files are ignored or written under temporary directories;
  no binary test artifacts are committed.
- Product requirements, test cases, and acceptance evidence identify browser execution
  separately from source inspection.
- No product feature, schema, provider, cache, card mutation, or generation change is added.
- Automatic checks:
  - `uv sync`
  - `uv run playwright install chromium` (environment setup)
  - `uv run pytest tests/browser/test_workspace_browser.py -v`
  - `uv run pytest tests/test_cycle27.py tests/test_cycle28.py tests/test_cycle29.py tests/test_cycle30.py -v`
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Manual fallback:
  - If Chromium installation is blocked by the environment, record the exact setup blocker and
    do not mark TC-WS-010–019 automated.
- gas limit: N/A
- slither pass: N/A

## Three Candidate Missing Edge Cases

- Server teardown after an assertion failure must release the ephemeral port and thread so a
  later test can start cleanly.
- Font/rendering differences may make exact pixel or line-height assertions flaky; containment
  should use invariant geometry such as `scrollWidth <= clientWidth`, not screenshots or fixed
  pixel snapshots.
- `localStorage` can leak between tests when contexts are reused; theme tests need explicit
  context isolation or storage cleanup.

## One Simpler Alternative

Continue using Flask/static-source assertions and perform occasional manual browser checks. This
requires no dependency, but it cannot execute input events, DOM state transitions, storage
persistence, or geometry. Cycle 31 identified that as the main quality gap, so the alternative
is rejected.

## Assumptions

- Python Playwright supports the current Python 3.11+ target and Windows development
  environment.
- The implementation environment can install the Chromium runtime or can obtain explicit user
  approval for the download.
- Werkzeug `make_server` can host the existing Flask application in a test thread without
  changing production code.
- Workspace behavior remains deterministic and mock/provider-free when AI environment variables
  are cleared.
- The preserved deterministic theme-coverage plan is deferred to Cycle 33 after this
  infrastructure cycle; it has no architectural dependency on Cycle 32 but will benefit from
  the new executable driver.

## Review Guidance

### Enumeration Required

- Enumerate every browser test and map it to TC-WS IDs:
  - Search:
    `rg -n "def test_|TC-WS-" tests/browser docs/test-cases.md`
  - Expected: TC-WS-010 through TC-WS-019 have explicit executable/manual status.
- Enumerate all server/browser lifecycle fixtures:
  - Search:
    `rg -n "make_server|Thread|shutdown|join|sync_playwright|chromium|browser\\.close|context\\.close" tests/browser`
  - Verify cleanup exists on every fixture exit path.
- Enumerate repository-root monkeypatching and card writes:
  - Search:
    `rg -n "REPO_ROOT|tmp_path|cards|write_text|frontmatter" tests/browser`
  - Expected: writes are contained under `tmp_path`; no canonical repo path is used.
- Enumerate provider/environment isolation:
  - Search:
    `rg -n "AI_PROVIDER|ANTHROPIC_API_KEY|GOOGLE_API_KEY|GEMINI_API_KEY|AI_API_KEY" tests/browser`
  - Expected: provider variables are cleared; no live key dependency.
- Enumerate dependency/config changes:
  - Inspect `pyproject.toml` and `uv.lock`.
  - Expected: only Playwright-related dependency resolution; no unrelated upgrades when
    avoidable.
- Enumerate product code changes:
  - `git diff --name-only <cycle-base>...HEAD`
  - Expected product files under `scripts/` and templates/static are unchanged unless an approved
    amendment exists.

### Verification Method Guide

- DOM interaction:
  - Source-string assertions are insufficient. Use Playwright locators and assert visible text,
    checked state, attributes, storage, and rendered geometry after real events.
- API/payload:
  - Browser network interception can assert request shape, but at least one preview case should
    reach the real Flask endpoint with mock provider mode.
- No persistence:
  - Compare temporary card file count/content before and after browser preview; DOM-only evidence
    is insufficient.
- Theme persistence:
  - Reload within the same isolated browser context and verify both `localStorage` and the root
    theme attribute.
- Accessibility:
  - Locator accessibility names and focus progression are sufficient for control wiring.
    Color contrast remains manual unless a dedicated analyzer is explicitly added.
- Containment:
  - Use browser-computed geometry; screenshots or CSS-source presence alone are insufficient.
- Browser availability:
  - A skipped or uninstalled browser test is not a pass. The dedicated browser command must show
    executed tests with zero skips for READY_TO_MERGE.

---

## Amendment — Dependency Contract (approved by user 2026-06-08)

**Authorization**: Explicit user approval received 2026-06-08. The user stated:
"승인한다, 아까는 구현자에게 내가 직접 승인을 했던거다." This approves retaining
`google-genai>=1.0` in the default dev dependency group along with the matching
`pyproject.toml`/`uv.lock` changes. Corrected per review-v6 ISSUE-7: prior citations
("Cycle 32 escalation override 승인...") were executor instruction text, not user speech.

**Scope**: `[dependency-groups] dev` in `pyproject.toml` and `uv.lock`.

**Decision**: Include `google-genai>=1.0` in `[dependency-groups] dev` (default dev group).

**Rationale**: The Cycle 32 Sprint Contract (above) requires `uv sync` followed by the full
test suite. `tests/test_cycle18.py` and `tests/test_cycle19.py` unconditionally import
`from google import genai`. These tests are part of the unconditional suite and require the
Google SDK to be present after a plain `uv sync`. Retaining google-genai in the `llm` extra
only would make the Sprint Contract's own `uv sync; uv run pytest -v` sequence fail — an
internal contradiction. Adding google-genai to the dev group is the narrowest change that
resolves this contradiction without altering the documented clean-setup command.

**Alignment**:
- `pyproject.toml`: `google-genai>=1.0` added to `[dependency-groups] dev`.
- `uv.lock`: regenerated; deduplicates google-genai across dev group and llm extra.
- `docs/acceptance-studio.md`: Dependency sync row reverted to `uv sync`; note added that
  `--extra llm` is needed only for anthropic-dependent LLM features.
- The `llm` extra is unchanged and continues to declare both `anthropic` and `google-genai`
  for production deployments that use the full LLM stack.
