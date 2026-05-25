# Codex Review v5

## Verdict

READY_TO_MERGE

## Findings

No blocking findings.

## Previous Issue Status

| Previous Issue | Status | Notes |
|---|---|---|
| ISSUE-1 / ISSUE-9 | RESOLVED | Undated LLM and mock paths return `period_start: null`; save rejects until the user supplies a period. |
| ISSUE-6 | RESOLVED | The grounded contract cache key invalidates legacy Studio responses. |
| ISSUE-7 | RESOLVED | Evaluation output and stderr emit only safe error categorization, not raw sentinel credential text. |
| ISSUE-8 | RESOLVED | Korean organization names such as `우리은행` do not create contribution false positives. |
| ISSUE-10 | RESOLVED | Undated mock preview now states that its period requires confirmation rather than claiming a current-date assumption. |

## Regression Check

No new behavioral regressions found in the remediation diff. The direct mock reproduction now
returns `period_start: null` with a confirmation-needed assumption, and the evaluator error
reproduction reports only `category=auth_failed`.

## Sprint Contract Check

| Contract Item | Result | Evidence |
|---|---|---|
| Preview exposes supported facts and assumptions for mock and LLM flows | PASS | Mock and LLM response tests, including undated preview semantics, pass. |
| No unsupported metrics/dates/ownership in grounded flow | PASS | Undated draft save is rejected in both provider and fallback paths; grounding tests pass. |
| Google uses structured response configuration and safe fallback | PASS | Structured schema and malformed/error fallback coverage passes. |
| Save excludes raw input and preview annotation fields | PASS | Persistence boundary regression tests pass. |
| Existing dashboard/provider/build behavior does not regress | PASS | Full test suite and CLI build dry runs pass. |
| Evaluation is synthetic-only, checkpointed, quota bounded, and safe | PASS | Dry-run and evaluation safety/stop/checkpoint tests pass. |
| Prompt follows method-grounded direction | PASS | Procedure-based prompt tests pass without persona wording. |

## Automatic Checks

- `uv run pytest -v`: PASS (`376 passed`, 7 non-blocking `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS with existing missing-evidence warning for card `test`
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

- No material scope expansion found.
- `.review/cycle-20/.read-counter` remains untracked and outside this review.

## Residual Risk

- Live Google quality comparison remains quota-dependent and is manual acceptance evidence, as
  allowed by the plan.
- `datetime.utcnow()` deprecation warnings in the evaluation script are non-blocking maintenance
  work for a subsequent cleanup.
