# Codex Review v3

## Verdict

BLOCKED

## Findings

### ISSUE-7 [MEDIUM] Clean-sync fix expands the dependency scope without an approved amendment

- Location: `.review/cycle-32/plan.md:43`, `.review/cycle-32/plan.md:45`,
  `pyproject.toml:45`, `.review/cycle-32/review-v2.md:23`
- Analysis: Adding `google-genai` to the default dev group makes the documented plain
  `uv sync` sequence pass, but Cycle 32 authorizes adding Playwright tooling and says the lock
  update is for that dependency addition only. Review v2 also required an approved escalation
  amendment before changing the environment contract. No amendment was appended to `plan.md`;
  the executor changed the critical dependency manifest directly.
- Impact: The implementation now satisfies the test commands but violates the cycle's dependency
  and scope contract. It also changes the default developer installation policy for an existing
  optional provider SDK, which is a project-level decision beyond browser-test infrastructure.
- Fix direction: Obtain an explicit escalation decision and append a narrow amendment approving
  one of these contracts: make `google-genai` a default dev test dependency, or retain it as an
  optional dependency and change Cycle 32's clean/full-suite commands to `uv sync --extra llm`.
  Then align `plan.md`, `pyproject.toml`, lock metadata, and acceptance documentation to the
  chosen policy.

## Previous Issue Status

- ISSUE-1: RESOLVED
- ISSUE-2: RESOLVED
- ISSUE-3: RESOLVED
- ISSUE-4: RESOLVED
- ISSUE-5: RESOLVED
- ISSUE-6: RESOLVED

## Regression Check

No behavioral regression found. Plain `uv sync` now supports the Google SDK tests, real Tab
navigation reaches all five required control categories, and the full suite passes.

## Sprint Contract Check

| Contract Item | Status | Notes |
|---|---|---|
| Playwright dev dependency and lock update | PARTIAL | Playwright is correct; unapproved `google-genai` dev promotion exceeds scope. |
| Real ephemeral Flask server | PASS | Server uses a temporary repository and ephemeral port. |
| TC-WS-010–019 evidence | PASS | Browser coverage is executable or explicitly source-only. |
| Keyboard/accessibility relationships | PASS | Neutral-focus Tab traversal reaches all five required categories. |
| Preview payload/render and no persistence | PASS | Real request and filesystem assertions pass. |
| Resource/global cleanup | PASS | Full-suite order remains green. |
| Plain clean setup and full suite | PASS | `uv sync` followed by tests succeeds. |
| No unapproved dependency/scope change | FAIL | ISSUE-7. |
| No product-code changes | PASS | No product source changed. |

## Automatic Checks

- `uv sync`: PASS
- `uv run pytest tests/browser/test_workspace_browser.py -v`: PASS — 26 passed, 0 skipped
- `uv run pytest tests/test_cycle18.py tests/test_cycle19.py tests/test_cycle21.py -q`:
  PASS — 133 passed
- `uv run pytest -v`: PASS — 638 passed, 7 existing warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 40 files formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`
- `git diff --check`: PASS

## Changes Outside Plan

`google-genai` was promoted from the optional `llm` extra into the default dev group without the
required escalation amendment. No other scope creep was found.

---

## RESOLVED

### Issue Classification
- ISSUE-7: APPLY

### Applied

RESOLVED: ISSUE-7 — Append escalation amendment to plan.md; correct acceptance-studio.md
- `.review/cycle-32/plan.md`: `## Amendment — Dependency Contract` section appended at EOF
  after `---` separator. Documents: authorization (review-v3 BLOCKED), decision (google-genai
  in dev group), rationale (Sprint Contract says `uv sync`; test_cycle18.py and test_cycle19.py
  unconditionally import `from google import genai`; plain sync without google-genai contradicts
  the existing Sprint Contract), alignment (pyproject.toml dev group, uv.lock, acceptance docs).
  Rationale corrected per Advisor: `from google import genai` (not `google.generativeai`);
  cycle18/cycle19 only (not cycle21).
- `docs/acceptance-studio.md`: two "Dependency sync" rows reverted from `uv sync --extra llm`
  to `uv sync`; explanatory note clarifies `--extra llm` is for anthropic-dependent features only.
- `pyproject.toml` / `uv.lock`: unchanged (google-genai in dev group already from review-v2).

자동 체크:
- `uv sync; uv run pytest -q`: 638 passed, 0 failed ✅
- `uv run pytest tests/browser/test_workspace_browser.py -v`: 26 passed, 0 skipped ✅
- `uv run ruff check scripts tests`: clean ✅
- `uv run ruff format --check scripts tests`: clean ✅
