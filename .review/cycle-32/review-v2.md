# Codex Review v2

## Verdict

BLOCKED

## Findings

### ISSUE-1 [HIGH] The plan's clean setup contract still removes required LLM test dependencies

- Location: `.review/cycle-32/plan.md:140`, `pyproject.toml:39`,
  `docs/acceptance-studio.md:23`
- Analysis: The acceptance document now says `uv sync --extra llm`, but the controlling Sprint
  Contract still requires plain `uv sync` followed by the full suite. The dependency declaration
  is unchanged: Google SDKs remain optional under the `llm` extra. Re-running plain `uv sync`
  removed `google-genai`; the targeted Google tests then failed with
  `ModuleNotFoundError: No module named 'google'`.
- Impact: The required clean setup and full-suite sequence remains non-reproducible. Updating a
  secondary acceptance document does not resolve the plan contract that the reviewer must verify.
- Fix direction: Resolve the contract through an approved escalation amendment. Either amend the
  Cycle 32 automatic checks to use `uv sync --extra llm` consistently, or include the SDKs needed
  by unconditional tests in the default test environment. Then execute the amended sequence from
  a clean sync.

### ISSUE-3 [MEDIUM] Keyboard coverage still omits two controls required by the plan

- Location: `.review/cycle-32/plan.md:80`,
  `tests/browser/test_workspace_browser.py:105`,
  `docs/acceptance-studio.md:152`
- Analysis: The revised test programmatically focuses `#ws-theme-toggle`, then records only a
  checkbox, any target field, and the Generate button. It does not prove that Tab navigation can
  reach the theme toggle itself or a visible disclosure button. Separate tests only check that
  those controls have text or `aria-controls`; they do not test keyboard reachability.
- Impact: The Sprint Contract explicitly requires Tab navigation to reach the theme toggle,
  checkbox, target fields, disclosure, and Generate button. The acceptance checklist makes the
  same all-interactive-controls claim, so TC-WS-013 remains only partially verified.
- Fix direction: Start from a neutral document focus, drive only `Tab`/`Shift+Tab`, and assert
  focus reaches all five required control categories. Use the deterministic narrow viewport so
  the disclosure button is visible and participates in the tab sequence.

## Previous Issue Status

- ISSUE-1: UNRESOLVED
- ISSUE-2: RESOLVED
- ISSUE-3: UNRESOLVED
- ISSUE-4: RESOLVED
- ISSUE-5: RESOLVED
- ISSUE-6: RESOLVED

## Regression Check

No product regression found. Module-scoped server/provider cleanup works in full-suite order, all
five target fields recompute coverage, disclosure tests execute without skips or DOM visibility
mutation, and the preview request payload reaches the real Flask endpoint.

## Sprint Contract Check

| Contract Item | Status | Notes |
|---|---|---|
| Playwright dev dependency and lock update | PASS | Playwright tooling is declared and locked. |
| Real ephemeral Flask server | PASS | Module-scoped Werkzeug server uses an ephemeral port. |
| Temporary repository and no live provider | PASS | Temporary cards and provider-key clearing are isolated and restored. |
| TC-WS-010–019 executable/manual accounting | PARTIAL | TC-WS-013 keyboard reachability remains incomplete. |
| Live-card rendering, selection, and fit | PASS | Browser execution covers rendering and all five target inputs. |
| Disclosure with zero skips and real visibility | PASS | Narrow viewport produces natural overflow; no forced visibility. |
| Theme persistence and OS override | PASS | Browser execution covers storage, reload, and explicit override. |
| Keyboard/accessibility relationships | FAIL | ISSUE-3. |
| Long-text containment | PASS | Browser geometry assertion passes. |
| Preview payload/render and no persistence | PASS | Passive request capture and filesystem count assertion pass. |
| Resource/global cleanup | PASS | Full suite passes after browser tests in collection order. |
| Clean setup and full-suite reproducibility | FAIL | ISSUE-1. |
| No product-code changes | PASS | No `scripts/` product source changed. |

## Automatic Checks

- `uv sync --extra llm`: PASS
- `uv run pytest tests/browser/test_workspace_browser.py -v`: PASS — 26 passed, 0 skipped
- `uv run pytest tests/test_cycle27.py tests/test_cycle28.py tests/test_cycle29.py tests/test_cycle30.py -v`:
  PASS — 88 passed
- `uv run pytest -v`: PASS after extra-enabled sync — 638 passed, 7 existing warnings
- `uv sync; uv run pytest <Google SDK tests> -q`: FAIL — 2 failed because `google` is absent
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 40 files formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`
- `git diff --check`: PASS

## Changes Outside Plan

No product feature scope creep found. The remaining blockers are incomplete resolution of the
existing environment contract and keyboard-navigation finding.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-3: APPLY

### Applied

RESOLVED: ISSUE-1 — Add google-genai to [dependency-groups] dev; plain uv sync now sufficient
- `pyproject.toml`: "google-genai>=1.0" added to `[dependency-groups] dev`.
- `uv.lock`: regenerated via `uv lock && uv sync`. uv deduplicates google-genai across dev
  group and llm extra; anthropic stays llm-extra-only (no leak).
- Verification: plain `uv sync` (no --extra llm) → `google.genai` importable; 133 Google SDK
  tests pass; plan.md Sprint Contract sequence `uv sync; uv run pytest -v` works as written.

RESOLVED: ISSUE-3 — Tab navigation from neutral focus reaches all 5 required control categories
- `tests/browser/test_workspace_browser.py`: test_keyboard_tab_sequence_reaches_controls
  switched to `narrow_ws_page` (disclosure naturally visible). Programmatic
  `.focus("#ws-theme-toggle")` replaced with `document.body.focus()` (neutral start).
  Loop extended to 50 iterations. Asserts all 5 categories: theme-toggle, checkbox,
  target-field, disclosure (aria-expanded attr), generate-btn.

자동 체크:
- `uv sync; uv run pytest -q`: 638 passed, 0 failed ✅
- `uv run pytest tests/browser/test_workspace_browser.py -v`: 26 passed, 0 skipped ✅
- `uv run ruff check scripts tests`: clean ✅
- `uv run ruff format --check scripts tests`: clean ✅
