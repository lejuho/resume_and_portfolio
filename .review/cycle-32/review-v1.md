# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [HIGH] Declared clean setup makes the full suite fail

- Location: `.review/cycle-32/plan.md:140`, `pyproject.toml:39`,
  `tests/test_cycle18.py:124`, `tests/test_cycle19.py:38`, `tests/test_cycle21.py:603`
- Analysis: The Sprint Contract starts with `uv sync` and later requires
  `uv run pytest -v`. A clean `uv sync` installs the default dev group but removes the optional
  `llm` extra, including `google-genai`. The required full suite then fails nine tests with
  `ModuleNotFoundError: No module named 'google'`. This was reproduced directly:
  `uv sync; uv run pytest tests/test_cycle18.py tests/test_cycle19.py tests/test_cycle21.py -q`
  produced 9 failures. `uv run --extra llm pytest -q` passes all 634 tests, confirming this is
  an environment/test contract problem rather than a product regression.
- Impact: The mandatory full check is red from the documented setup. The implementation cannot
  be merged while treating those failures as pre-existing because Cycle 32 explicitly changes
  dependency setup and requires a reproducible full-suite command.
- Fix direction: Make the test environment contract include the existing `llm` extra, for
  example `uv sync --extra llm` and `uv run --extra llm pytest ...`, and update all Cycle 32
  commands/docs consistently. Alternatively make all unconditionally imported test SDKs dev
  dependencies, but avoid unrelated dependency duplication. Re-run from a clean sync.

### ISSUE-2 [HIGH] Session-scoped monkeypatch leaks repository and provider state into the full suite

- Location: `tests/browser/conftest.py:70`, `tests/browser/conftest.py:82`,
  `tests/browser/conftest.py:109`
- Analysis: `live_repo`, `server`, and `monkeypatch_session` are session-scoped. The server
  fixture patches the module-global `dash_mod.REPO_ROOT` and deletes provider environment
  variables, but `mp.undo()` and server shutdown do not run until the entire pytest session ends.
  Because `tests/browser` executes before the remaining test modules, subsequent non-browser
  tests run while the Workspace server is alive and the dashboard global still points at the
  browser fixture repository.
- Impact: Browser integration tests are not isolated and can mask or cause failures elsewhere.
  This violates the Sprint Contract's cleanup requirement and makes full-suite results
  order-dependent.
- Fix direction: Scope the repository patch, provider isolation, and server lifetime to the
  browser module (or a narrower fixture scope). Use `try/finally` around server shutdown/join and
  monkeypatch restoration. Ensure the original `REPO_ROOT` and environment are restored before
  the next non-browser test module starts. Also close manually created browser contexts in
  `finally` or a fixture.

### ISSUE-3 [MEDIUM] TC-WS-013 browser evidence does not test keyboard navigation

- Location: `tests/browser/test_workspace_browser.py:103`,
  `docs/test-cases.md:234`
- Analysis: The product test case says “Keyboard tab,” and the Sprint Contract requires Tab
  navigation and accessible relationships. The tests call Playwright `.focus()` directly on each
  element. Programmatic focus proves focusability but does not prove keyboard tab order,
  reachability, accessible names, `aria-controls`, or promised focus treatment.
- Impact: `docs/test-cases.md` upgrades TC-WS-013 to “Browser (Cycle 32)” with a stronger claim
  than the executable evidence supports.
- Fix direction: Drive focus with keyboard `Tab` presses from a known starting point and assert
  the expected sequence. Add accessible-name/ARIA assertions for checkbox labels, disclosure,
  and theme toggle. Keep custom-outline verification source/manual where browser-computed evidence
  is not reliable.

### ISSUE-4 [MEDIUM] The “all five target fields” test exercises only the job-description field

- Location: `tests/browser/test_workspace_browser.py:167`, `docs/test-cases.md:237`
- Analysis: The test clears all five fields, then fills only `#ws-jd` and checks for any
  percentage. It does not independently prove that organization, role, question, and competency
  input events trigger recomputation.
- Impact: TC-WS-016 is marked browser-execution verified for all five target listeners without
  corresponding behavior evidence.
- Fix direction: Parameterize over all five field IDs. For each isolated case, establish a clean
  state, fill matching text into that field, and assert coverage changes from the pre-input
  state.

### ISSUE-5 [MEDIUM] Disclosure coverage can skip and bypasses the real visibility gate

- Location: `tests/browser/test_workspace_browser.py:186`,
  `tests/browser/test_workspace_browser.py:201`, `.review/cycle-32/plan.md:235`
- Analysis: The natural-overflow test calls `pytest.skip()` when geometry does not overflow,
  despite the explicit zero-skips merge condition. The expand/collapse tests then force
  `el.hidden = false`, bypassing the production truncation/visibility gate they are meant to
  validate.
- Impact: A layout/environment regression can be converted into a skip, and the remaining tests
  can pass after mutating the DOM into a state the application did not produce. TC-WS-017–019
  are therefore overstated as fully browser verified.
- Fix direction: Use a deterministic narrow viewport and sufficiently long fixture so overflow
  is guaranteed, assert the real button becomes visible with zero skips, and exercise
  expand/collapse/no-selection-side-effect without forcing `hidden`.

### ISSUE-6 [MEDIUM] Preview browser test does not assert the request payload contract

- Location: `tests/browser/test_workspace_browser.py:268`,
  `.review/cycle-32/plan.md:95`
- Analysis: The test verifies rendered output and unchanged card count but never captures the
  `/api/studio/application-preview` request. It therefore does not prove the required existing
  payload shape (`output_type`, `card_ids`, `target_context`) through the browser path.
- Impact: One of the planned end-to-end contracts remains covered only by the older source
  inspection test.
- Fix direction: Capture or intercept the real request while still allowing it to reach Flask,
  assert method/path and parsed JSON shape/selected card IDs, then verify the mock response and
  no-persistence behavior.

## Sprint Contract Check

| Contract Item | Status | Notes |
|---|---|---|
| Playwright dev dependency and lock update | PASS | Only Playwright-related packages added to the lock diff. |
| Real ephemeral Flask server | PASS | `make_server` uses an ephemeral localhost port. |
| Temporary card repository | PASS | Browser fixtures write under `tmp_path_factory`. |
| No live provider | PARTIAL | Variables are cleared, but session scope leaks into unrelated tests (ISSUE-2). |
| TC-WS-010–019 executable or explicitly manual | FAIL | ISSUE-3–5 overstate executable evidence. |
| Live-card rendering and selection | PASS | Real DOM/browser assertions pass. |
| Fit recomputation across all inputs | FAIL | ISSUE-4. |
| Disclosure with zero skips and real visibility | FAIL | ISSUE-5. |
| Theme persistence and OS override | PASS | Browser execution covers both. |
| Keyboard/accessibility relationships | FAIL | ISSUE-3. |
| Long-text containment | PASS | Browser geometry assertion passes. |
| Preview payload, render, and no persistence | PARTIAL | Render/no-persistence pass; payload missing (ISSUE-6). |
| Resource/global cleanup | FAIL | ISSUE-2. |
| Existing routes/tests remain green | FAIL | ISSUE-1: required full suite fails after clean setup. |
| No product code changes | PASS | Changes are test infrastructure, dependencies, ignore rules, and docs. |

## Automatic Checks

- `uv run pytest tests/browser/test_workspace_browser.py -v`: PASS — 22 passed
- `uv sync; uv run pytest tests/test_cycle18.py tests/test_cycle19.py tests/test_cycle21.py -q`:
  FAIL — 9 failed, 124 passed (`google` SDK missing)
- `uv run pytest -v`: FAIL — 9 failed, 625 passed, 7 warnings
- `uv run --extra llm pytest -q`: PASS — 634 passed, 7 warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 40 files formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`
- `git diff --check`: PASS

## Changes Outside Plan

No product feature scope creep found. The dependency/test setup does not yet satisfy the plan's
own reproducibility and isolation contracts.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY
- ISSUE-3: APPLY
- ISSUE-4: APPLY
- ISSUE-5: APPLY
- ISSUE-6: APPLY

### Applied

RESOLVED: ISSUE-1 — Add `uv sync --extra llm` to acceptance-studio.md both baseline tables
- `docs/acceptance-studio.md`: "Dependency sync" row added to Automated Baseline and Workspace
  Automated Baseline sections with note "Required before full suite; includes google-genai".

RESOLVED: ISSUE-2 — Fix session-scope leak via module-scope server + monkeypatch
- `tests/browser/conftest.py`: `monkeypatch_session` renamed `monkeypatch_module`, scope changed
  to `"module"`. `server` fixture changed to scope `"module"` with `try/finally` teardown.
  pytest guarantees module fixture teardown before next module's setup — REPO_ROOT and env vars
  are restored before test_cycle*.py runs.

RESOLVED: ISSUE-3 — Replace direct .focus() with Tab navigation + ARIA assertions
- `tests/browser/test_workspace_browser.py`: 4 old `.focus()` tests replaced with
  `test_keyboard_tab_sequence_reaches_controls` (Tab loop from #ws-theme-toggle, superset assert
  on {checkbox, target-field, generate-btn}) + `test_checkbox_accessible_name_from_label` +
  `test_disclosure_button_aria_controls` + `test_theme_toggle_has_visible_label`.

RESOLVED: ISSUE-4 — Parametrize TC-WS-016 over all 5 target fields
- `tests/browser/test_workspace_browser.py`: `test_all_five_target_fields_trigger_coverage`
  replaced with `@pytest.mark.parametrize("field_id", [...])` over all 5 IDs; each iteration
  gets a fresh `ws_page` context and fills only the named field before asserting coverage > 0%.

RESOLVED: ISSUE-5 — Deterministic disclosure via narrow_ws_page; zero skips, no DOM mutation
- `tests/browser/conftest.py`: `narrow_ws_page` fixture added (320 px viewport, fresh context,
  try/finally context.close). Headless Chromium line-clamp at 320 px guarantees
  scrollHeight > clientHeight for the 178-char fixture summary.
- `tests/browser/test_workspace_browser.py`: all 4 disclosure tests converted to
  `narrow_ws_page`; `pytest.skip` removed; `btn.evaluate("el.hidden=false")` removed.

RESOLVED: ISSUE-6 — Assert preview request payload shape in browser test
- `tests/browser/test_workspace_browser.py`: `test_preview_renders_and_no_card_created`
  replaced with `test_preview_payload_and_no_persistence`; passive `page.on("request", handler)`
  captures POST body before any assert; asserts `output_type`, `card_ids`, `target_context`
  present and `auth-service` in `card_ids`. Flask endpoint still handles request (not intercepted).

자동 체크:
- `uv run pytest tests/browser/test_workspace_browser.py -v`: 26 passed ✅
- `uv run --extra llm pytest -q`: 638 passed, 0 failed ✅
- `uv run ruff check scripts tests`: clean ✅
- `uv run ruff format --check scripts tests`: clean ✅
