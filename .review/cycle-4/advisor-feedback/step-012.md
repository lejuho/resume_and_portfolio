# Step 012 — Cycle-4 LLM tailoring Approach check

Cycle: 4
Pass: 1
Files Changed: scripts/llm.py, scripts/pcli.py, tests/test_llm.py, tests/fixtures/fake-jd.txt

## Advisor Verdict
OK

## Advisor Feedback
1. Two separate calls for score vs rewrite. Different output schemas; combining complicates retry/cache invalidation when only tone changes. Cache score independent of tone.
2. model_copy(update={"summary": ...}) is correct. Never mutate source Card; resume-data.json reflects rewrite, source YAML untouched.
3. llm_app = typer.Typer(), app.add_typer(llm_app, name="llm") — same pattern as preset_app. Exit code 2 for missing key + cache miss; distinguish from runtime errors.
4. Add --no-cache flag for forced refresh; cache key must include tone and lang in payload.

## Sonnet Response
- 적용 (1): Two separate functions score_cards / rewrite_summary with independent cache keys. Score key excludes tone; rewrite key includes tone and lang.
- 적용 (2): model_copy(update=...) for in-memory rewrite. No mdx mutation.
- 적용 (3): llm_app pattern matching preset_app. exit(2) for no key + cache miss.
- 적용 (4): --no-cache flag on build resume + llm tailor. Cache key includes tone+lang for rewrite.
