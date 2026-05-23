# Codex Review v2

## Verdict
READY_TO_MERGE

## Findings
No blocking findings.

## Previous Issue Status
- No previous blocking issues. User-reported UX issue addressed after v1: placeholder keys were treated as configured and the UI said `AI: connected`.

## Regression Check
- PASS: `your_key_here` and common placeholder values are no longer treated as configured API keys.
- PASS: Studio refine does not attempt LLM when only a placeholder key is configured; it falls back to mock.
- PASS: UI now says `AI: configured` instead of `AI: connected`, avoiding a false live-connectivity claim.
- PASS: Existing provider/model config behavior remains intact.

## Sprint Contract Check
- Existing Anthropic Studio refine path remains functional: PASS
- Existing CLI LLM helpers still raise clear errors when no usable key is configured: PASS
- `/api/studio/ai-status` never returns API key text: PASS
- `AI_PROVIDER=anthropic` and unset `AI_PROVIDER` behave the same: PASS
- `AI_API_KEY` remains accepted as a generic local alias: PASS
- `AI_MODEL` can override displayed/requested model: PASS
- Unsupported provider values do not crash `/api/studio/refine`; Studio falls back to mock: PASS
- No OpenAI SDK, provider router implementation, model picker UI, frontend key entry, or live credential validation call added: PASS

## Automatic Checks
- `uv run pytest -v`: PASS (`292 passed`)
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS (`WARN test: evidence is empty`, no errors)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Changes Outside Plan
- Placeholder key detection and less-assertive UI wording were added in response to user feedback. This stays within Cycle 17 provider-status scope.

## Notes
- This still does not perform a live API credential check on page load. That should be a separate explicit action or next-cycle endpoint because it has latency/cost/rate-limit implications.
