# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [HIGH] LLM grounded preview silently writes an unsupported current date

- Location: `scripts/llm.py:495`
- Analysis: `studio_refine_llm()` always sets `period_start` to `date.today()` instead of
  deriving it from supported source facts or marking it as uncertain. A fake grounded
  response containing `source_facts: ["Date: 2024-03"]` for input `Worked in 2024-03`
  produced `period_start: "2026-05-25"` during review. With undated input, today's date is
  likewise inserted without an assumption or `MISSING_PERIOD` guard.
- Impact: The preview can save a factually wrong date into a canonical card, violating the
  Sprint Contract rule that generated drafts must not introduce dates absent from input and
  defeating the purpose of grounded review.
- Fix Direction: Resolve `period_start` from a supported parsed date when present. When no
  source date exists, either represent the placeholder explicitly as uncertain in preview
  and missing-info before save, or require confirmation before persisting it. Add LLM-path
  tests for dated and undated input/save behavior.

### ISSUE-2 [MEDIUM] Deterministic Track K team input does not surface contribution uncertainty

- Location: `scripts/dashboard.py:374`, `scripts/dashboard.py:388`
- Analysis: `_TEAM_RE` detects only English team markers. Reviewing
  `_mock_refine("팀 프로젝트로 스마트 컨트랙트를 개발했습니다.", "both")` returns no
  `CONTRIBUTION_UNCLEAR` item and no team-contribution assumption, although the input states
  that this is team work. The new evaluator's Track K fixture uses the same Korean concept,
  but the deterministic tests cover only English `"Our team"`.
- Impact: Korean formal-application input, one of the two audit-defined tracks, bypasses a
  required grounding question and may proceed without clarifying personal contribution.
- Fix Direction: Cover Korean team/collaboration markers used in intended input, and add
  deterministic tests for Korean team text plus a Korean solo-control case.

### ISSUE-3 [MEDIUM] Empty grounding output breaks later preview renders in the same Studio session

- Location: `scripts/static/studio.js:253-265`
- Analysis: When `items` is empty, `_renderGroundingList()` replaces the `<ul>` identified by
  `st-facts-list` or `st-assumptions-list` with an un-IDed `<p>`. On the next refine action,
  `getElementById(listId)` returns `null`, the function exits, and newly available facts or
  assumptions can never appear until the page is reloaded.
- Impact: The user cannot reliably iterate from an incomplete preview to a grounded preview,
  which fails the review-before-save Studio workflow.
- Fix Direction: Preserve the stable list node and render/clear an empty-state child or
  separate empty-state element. Add a JS/browser-level regression covering empty first render
  followed by populated second render.

### ISSUE-4 [MEDIUM] Google path requests JSON MIME, not schema-constrained structured output

- Location: `scripts/llm.py:126-146`, `tests/test_cycle20.py:210-247`
- Analysis: The implementation sets only
  `GenerateContentConfig(response_mime_type="application/json")`; it does not supply
  `response_schema` or `response_json_schema`. The test verifies only that a boolean
  `response_json` flag reaches `_call()`, so it passes without testing the planned response
  shape constraint.
- Impact: The central reliability change from the audit is incomplete: Google may return
  syntactically valid JSON missing required grounding fields, leaving the preview dependent
  on empty defaults rather than an enforced structured contract.
- Fix Direction: Provide an explicit Google response schema for the grounded draft response
  and test that the schema/config is sent, including required `source_facts`,
  `assumptions`, `missing_info`, and intent-specific output behavior.

### ISSUE-5 [MEDIUM] The evaluator cannot produce the token-efficiency evidence required by the plan

- Location: `scripts/evaluate_studio_grounding.py:124-151`,
  `scripts/evaluate_studio_grounding.py:185-234`, `scripts/llm.py:126-151`
- Analysis: Evaluation output records `latency_s`, `output_chars`, and a numeric heuristic,
  but never records input/output/total tokens or a structured safe error category. `_call()`
  returns only response text and discards Gemini `usage_metadata`, so the specified token
  measurements cannot be generated. Additionally, `--provider` is applied with
  `os.environ.setdefault`, so an existing `AI_PROVIDER` can silently override the requested
  evaluation provider.
- Impact: The evaluator does not fulfill the token-efficiency and reproducibility purpose of
  this cycle and cannot support the later prompt-selection decision.
- Fix Direction: Preserve usage metadata for evaluator calls, write required token fields and
  classified errors to every checkpoint, ensure explicit CLI provider selection takes
  precedence for the evaluation run, and add assertions over the written JSON contract.

## Sprint Contract Check

| Contract Item | Result | Evidence |
|---|---|---|
| Preview exposes supported facts and assumptions for mock and LLM flows | PARTIAL | Fields are returned, but UI cannot rerender populated values after an empty render (ISSUE-3). |
| No unsupported metrics/dates/ownership in deterministic/grounded flow | FAIL | LLM path injects current date; Korean team ambiguity is not detected (ISSUE-1, ISSUE-2). |
| Google uses structured response configuration and safe fallback | FAIL | JSON MIME requested, no schema constraint implemented (ISSUE-4). |
| Save excludes raw input and preview annotation fields | PASS | Save path does not map `source_facts`/`assumptions`; tests cover exclusion. |
| Existing dashboard/provider/build behavior does not regress | PASS | Automated regression suite passed. |
| Evaluation is synthetic-only, checkpointed, quota bounded, and measures required evidence | FAIL | Synthetic/checkpoint/limit behavior exists; token and safe-category evidence is missing (ISSUE-5). |

## Automatic Checks

- `uv run pytest -v`: PASS (`355 passed`, with 3 `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS with existing warning for missing evidence on card `test`
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

- No material scope expansion found in committed implementation files.
- `.review/cycle-20/.read-counter` is currently untracked and is not part of the reviewed
  implementation diff.
