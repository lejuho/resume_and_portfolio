# Codex Review v4

## Verdict

BLOCKED

## Findings

### ISSUE-10 [LOW] Undated mock preview still tells the user a current-date assumption was made

- Location: `scripts/dashboard.py:407-435`
- Analysis: The remediation correctly changes an undated mock draft to
  `period_start = None`, but leaves the old annotation
  `"Project period assumed to be current date."` in `draft.assumptions`.
  Direct reproduction returns both `period_start: None` and that assumption for
  `"Undated project notes with no factual date."`.
- Impact: The saved fact boundary is now safe, but the new grounding preview is
  internally contradictory: it reports an inference that the system deliberately
  stopped making. This weakens the review surface whose purpose is to distinguish
  supported facts from items needing confirmation.
- Fix Direction: Replace the stale assumption with a truthful confirmation item,
  such as `"Project period is not provided and needs confirmation."`, or rely on
  the existing `MISSING_PERIOD` question and omit the assumption. Add an assertion
  that an undated mock preview does not state that current date was assumed.

## Previous Issue Status

| Previous Issue | Status | Notes |
|---|---|---|
| ISSUE-1 / ISSUE-9 | RESOLVED | Both LLM and mock undated paths now return no saveable period; save rejects until a date is supplied. |
| ISSUE-6 | RESOLVED | Grounded cache version invalidates pre-grounding Studio responses. |
| ISSUE-7 | RESOLVED | Evaluator checkpoint and stderr no longer emit raw sentinel credential values. |
| ISSUE-8 | RESOLVED | Korean organization-name false positive remains corrected. |

## Regression Check

- One explanatory string from the removed current-date fallback remains visible in
  the mock preview (ISSUE-10).

## Sprint Contract Check

| Contract Item | Result | Evidence |
|---|---|---|
| Preview exposes supported facts and assumptions for mock and LLM flows | FAIL | Mock assumptions describe a date inference no longer made (ISSUE-10). |
| No unsupported metrics/dates/ownership in saved grounded flow | PASS | Undated mock/LLM save paths reject missing periods. |
| Google uses structured response configuration and safe fallback | PASS | Existing schema and fallback tests pass. |
| Save excludes raw input and preview annotation fields | PASS | Persistence exclusion tests pass. |
| Existing dashboard/provider/build behavior does not regress | PASS | Full regression suite and dry-run builds pass. |
| Evaluation is synthetic-only, checkpointed, quota bounded, and safe | PASS | Raw error text no longer appears in checkpoint or stderr. |
| Prompt follows method-grounded direction | PASS | Product prompt remains procedural rather than persona-led. |

## Automatic Checks

- `uv run pytest -v`: PASS (`375 passed`, 7 `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS with existing missing-evidence warning for card `test`
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

- No material feature scope expansion found in the remediation changes.
- `.review/cycle-20/.read-counter` remains untracked and outside this review.
