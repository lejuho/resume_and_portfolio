# Codex Review v3

## Verdict

BLOCKED

## Findings

### ISSUE-9 [HIGH] Mock fallback still makes an undated activity saveable with today's date

- Location: `scripts/dashboard.py:382-475`, `scripts/dashboard.py:616-681`
- Analysis: The LLM path now leaves an absent period unset, but `_mock_refine()` still assigns
  `str(_date.today())` when the input has no date and returns that value in `draft.period_start`.
  The save endpoint accepts any non-empty `period_start`, so the mock fallback can persist the
  generated current date as canonical card data. Direct reproduction on May 25, 2026 returned
  `period_start: "2026-05-25"` for `"Undated project notes with no factual date."` while also
  returning `MISSING_PERIOD`.
- Impact: Cycle 20 requires the grounded mock and LLM flows not to introduce dates absent from
  the user's source material. The fallback path still creates a durable unsupported fact, and
  it is the path users receive when no live provider is configured or an LLM call fails.
- Fix Direction: Make undated mock drafts return `period_start: null`, consistent with the LLM
  path, and require the user to confirm a date before save. Add a mock refine-then-save
  regression test for undated input.

### ISSUE-7 [MEDIUM] Evaluator no longer writes raw errors to JSON but still prints credentials verbatim

- Location: `scripts/evaluate_studio_grounding.py:156-165`
- Analysis: The checkpoint record now contains only `safe_error_category`, resolving its
  on-disk leak. However, the exception string is newly printed to stderr without sanitization:
  `print(f"  [err] {str(exc)[:200]}", file=sys.stderr)`. Calling `_run_call()` with
  `Exception("Auth failed: SECRET_CREDENTIAL_12345")` prints that sentinel string verbatim.
- Impact: The evaluation tool's provider-error handling still leaks credential-bearing text
  in user-visible logs, contrary to its safe-error contract.
- Fix Direction: Print only the safe category and a fixed safe message, or redact credential
  material before emitting diagnostic text. Extend the test to assert captured stderr does
  not contain a sentinel secret.

## Previous Issue Status

| Previous Issue | Status | Notes |
|---|---|---|
| ISSUE-1 | RESOLVED FOR LLM FLOW | Undated LLM drafts now have no saveable period; mock equivalent remains ISSUE-9. |
| ISSUE-6 | RESOLVED | `grounded_ver` changes the Studio cache key and invalidates legacy entries. |
| ISSUE-7 | UNRESOLVED | Checkpoint is safe, but stderr output remains unsanitized. |
| ISSUE-8 | RESOLVED | `우리은행` no longer triggers the team-contribution warning; pronoun usage remains detected. |

## Regression Check

- The save guard works for undated LLM responses but does not protect the mock fallback because
  the fallback supplies a generated non-empty date (ISSUE-9).
- Error persistence was narrowed, but the added stderr diagnostic exposes the same raw value
  outside the checkpoint (ISSUE-7).

## Sprint Contract Check

| Contract Item | Result | Evidence |
|---|---|---|
| Preview exposes supported facts and assumptions for mock and LLM flows | PASS | Existing Cycle 20 tests pass for both paths. |
| No unsupported metrics/dates/ownership in grounded flow | FAIL | Mock fallback inserts today's date for undated input (ISSUE-9). |
| Google uses structured response configuration and safe fallback | PASS | Structured schema configuration remains covered. |
| Save excludes raw input and preview annotation fields | PASS | Persistence exclusion tests pass. |
| Existing dashboard/provider/build behavior does not regress | PASS | Full regression suite and dry-run builds pass. |
| Evaluation is synthetic-only, checkpointed, quota bounded, and safe | FAIL | Raw stderr error output can reveal a credential string (ISSUE-7). |
| Prompt follows method-grounded direction | PASS | Studio product prompt remains procedural rather than persona-led. |

## Automatic Checks

- `uv run pytest -v`: PASS (`372 passed`, 6 `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS with existing missing-evidence warning for card `test`
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

- No material feature scope expansion found in the remediation changes.
- `.review/cycle-20/.read-counter` remains untracked and outside this review.

---

## RESOLVED

### Issue Classification
- ISSUE-9: APPLY
- ISSUE-7 (v3 continuation): APPLY

### Applied

RESOLVED: ISSUE-9 — mock fallback now returns period_start=None for undated input
- `scripts/dashboard.py` `_mock_refine()`: changed `period_start = str(_date.today())` to `period_start = None` when no date detected in raw text; consistent with LLM path.
- `tests/test_cycle20.py`: `test_mock_undated_draft_has_null_period_start`, `test_mock_save_rejects_undated_draft` added.
- `tests/test_studio.py::test_studio_save_does_not_persist_raw_body`: added `2024-01` to raw text so mock returns a valid period_start.
자동 check: pytest ✅ (375 passed)

RESOLVED: ISSUE-7 (v3) — stderr no longer prints raw exception message
- `scripts/evaluate_studio_grounding.py`: `print(f"  [err] {str(exc)[:200]}")` replaced with `print(f"  [err] category={_safe_error_category(exc)}")` — raw exception text never reaches stderr.
- `tests/test_cycle20.py`: `test_evaluator_stderr_does_not_print_raw_error` added; asserts sentinel string absent from both stdout and stderr.
자동 check: pytest ✅ (375 passed), ruff ✅
