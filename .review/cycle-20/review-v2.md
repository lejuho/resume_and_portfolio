# Codex Review v2

## Verdict

BLOCKED

## Findings

### ISSUE-1 [HIGH] Undated LLM drafts still persist today's date as if it were a source fact

- Location: `scripts/llm.py:597-615`, `scripts/dashboard.py:627-641`,
  `tests/test_cycle20.py:489-502`
- Analysis: The fix adds `MISSING_PERIOD`, but the LLM draft still receives
  `period_start = date.today()` whenever raw input has no date. `/api/studio/save` then
  writes `draft.period_start` directly into the canonical card. The new test verifies only
  that the warning exists; it does not verify that an unconfirmed placeholder cannot be
  saved as a factual period.
- Impact: The core grounded-writing contract remains violated: an absent source date becomes
  a durable claimed date merely because the user saves the reviewed prose.
- Fix Direction: Do not expose a saveable factual `period_start` for an undated LLM draft.
  Require explicit period confirmation before save, or carry an explicit uncertainty flag
  that makes save reject/require edited date. Add an end-to-end refine-then-save test for
  undated input.

### ISSUE-6 [HIGH] Prompt-contract change reuses pre-grounding LLM cache entries

- Location: `scripts/llm.py:17`, `scripts/llm.py:522`
- Analysis: `_STUDIO_REFINE_PROMPT` and output expectations changed substantially, but
  `_SCHEMA_VER` remains `2`, which is included in the existing `studio_refine` cache key.
  Any cached Cycle 16-19 response for the same provider/model/intent/raw text is accepted
  without running the new grounded prompt or Google schema. Such a cached response can lack
  `source_facts` and `assumptions` or retain text produced under the older, less restrictive
  prompt.
- Impact: For inputs the user has already tried, Cycle 20 can silently show and save
  ungrounded legacy output while appearing to provide the new grounded workflow.
- Fix Direction: Invalidate prior Studio refine cache entries by increasing the prompt/schema
  cache version or adding a grounded contract version to the `studio_refine` payload. Add a
  regression test proving legacy cached responses are not reused for the new contract.

### ISSUE-7 [MEDIUM] Evaluator checkpoint stores raw provider exception text despite safe-category requirement

- Location: `scripts/evaluate_studio_grounding.py:157-164`
- Analysis: `_safe_error_category()` was added, but checkpoint output still includes
  `"error": str(exc)[:200]`. If a client or wrapper includes credential material in an
  exception string, the developer-only evaluator writes it under `output/evaluations/`.
  This is inconsistent with the documented server-side key handling policy and with the
  purpose of recording a safe error category.
- Impact: A research/evaluation run can persist provider secrets or sensitive error details
  to disk.
- Fix Direction: Write only safe categorized messages/codes to checkpoint JSON; retain raw
  exceptions only transiently for local stderr if explicitly sanitized. Add a test with a
  sentinel key string that must not appear in written output.

### ISSUE-8 [LOW] Korean team-marker expansion falsely classifies organization names such as `우리은행`

- Location: `scripts/dashboard.py:374-391`
- Analysis: The Korean markers are matched as unrestricted substrings. For example,
  `_mock_refine("우리은행 데이터 분석 프로젝트를 수행했습니다.", "both")` produces
  `CONTRIBUTION_UNCLEAR` because `우리` is inside the organization name, even though no
  teamwork is described.
- Impact: Track K users can receive confusing contribution warnings for ordinary employer
  names.
- Fix Direction: Narrow Korean teamwork detection to explicit collaboration phrases or add
  an exclusion/control test for organization names such as `우리은행`.

## Previous Issue Status

| Previous Issue | Status | Notes |
|---|---|---|
| ISSUE-1 | UNRESOLVED | Warning added, but unconfirmed current date remains saveable. |
| ISSUE-2 | RESOLVED WITH REGRESSION | Korean team input is detected; broad `우리` matching introduces ISSUE-8. |
| ISSUE-3 | RESOLVED | The stable `<ul>` node is preserved across empty/populated renders. |
| ISSUE-4 | RESOLVED | Google configuration now includes an explicit grounded response schema. |
| ISSUE-5 | PARTIALLY RESOLVED | Token fields and provider override are added; persisted raw error text is ISSUE-7. |
| user-direction-001 | RESOLVED | Studio grounded prompt is procedural rather than persona-led. |

## Regression Check

- New cache compatibility risk: changed grounding contract does not invalidate old LLM
  refinement caches (ISSUE-6).
- New privacy risk in evaluation output: safe categorization was added alongside persisted
  raw error text (ISSUE-7).
- Korean detection expansion introduces a false-positive organization-name case (ISSUE-8).

## Sprint Contract Check

| Contract Item | Result | Evidence |
|---|---|---|
| Preview exposes supported facts and assumptions for mock and LLM flows | PASS for fresh responses | UI rerender fix and schema/normalization are present. Legacy cached responses remain a blocker under ISSUE-6. |
| No unsupported metrics/dates/ownership in grounded flow | FAIL | Undated LLM draft can save today's date (ISSUE-1). |
| Google uses structured response configuration and safe fallback | PASS | `response_schema=_GROUNDED_DRAFT_SCHEMA` is now applied. |
| Save excludes raw input and preview annotation fields | PASS | Existing persistence exclusion remains covered. |
| Existing dashboard/provider/build behavior does not regress | PASS | Automated regression suite passes. |
| Evaluation is synthetic-only, checkpointed, quota bounded, and safe | FAIL | Raw exception text is persisted (ISSUE-7). |
| Prompt follows method-grounded direction | PASS | Persona-led Studio instruction was replaced by an evidence-grounded workflow. |

## Automatic Checks

- `uv run pytest -v`: PASS (`365 passed`, with 5 evaluator `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS with existing warning for missing evidence on card `test`
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

- No material feature scope expansion found.
- `.review/cycle-20/.read-counter` remains untracked and outside the reviewed diff.

---

## RESOLVED

### Issue Classification
- ISSUE-1 (v2 restatement): APPLY
- ISSUE-6: APPLY
- ISSUE-7: APPLY
- ISSUE-8: APPLY

### Applied

RESOLVED: ISSUE-1 (v2) — undated LLM draft sets period_start=None; save rejects without confirmed date
- `scripts/llm.py` `studio_refine_llm()`: undated input now sets `period_start = None` (previously `str(date.today())`).
- `scripts/dashboard.py` `api_studio_save()`: added guard — if `draft.period_start` is falsy, return 422 with message "draft.period_start is required".
- `tests/test_cycle20.py`: added `test_llm_undated_draft_has_null_period_start`, `test_save_rejects_undated_draft`, `test_save_accepts_undated_draft_when_period_filled`.
- Cascading test isolation fixes: `test_cycle17::test_refine_placeholder_key_falls_back_to_mock`, `test_studio::test_refine_returns_missing_info_structured`, `test_studio::test_studio_save_does_not_persist_raw_body` — added `delenv` for `AI_PROVIDER`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`.
- `test_llm_studio.py` save-flow tests: added date to raw text (`2024-01`) so period_start resolves correctly.
자동 check: pytest ✅ (372 passed)

RESOLVED: ISSUE-6 — cache key includes grounded_ver to invalidate pre-cycle-20 studio_refine entries
- `scripts/llm.py`: added `"grounded_ver": 1` to studio_refine cache payload; old entries (lacking this key) produce a different SHA-256 key and are never served.
- `tests/test_cycle20.py`: `test_studio_refine_cache_payload_contains_grounded_ver` asserts new and old payload keys differ.
자동 check: pytest ✅

RESOLVED: ISSUE-7 — evaluator checkpoint no longer persists raw exception text
- `scripts/evaluate_studio_grounding.py`: removed `"error": str(exc)[:200]` from checkpoint record; raw message printed to stderr only.
- `tests/test_cycle20.py`: `test_evaluator_checkpoint_does_not_persist_raw_error` asserts sentinel credential string absent from written JSON.
자동 check: pytest ✅

RESOLVED: ISSUE-8 — Korean 우리 restricted to pronoun context via lookahead
- `scripts/dashboard.py` `_TEAM_RE`: `우리` now matched only when followed by `[\s가는도와의팀들]` or end of string; compound nouns like `우리은행` no longer trigger `CONTRIBUTION_UNCLEAR`.
- `tests/test_cycle20.py`: `test_mock_org_name_uri_does_not_trigger_contribution_unclear` and `test_mock_uri_pronoun_still_triggers_contribution_unclear` added.
자동 check: pytest ✅ (372 passed), ruff ✅
