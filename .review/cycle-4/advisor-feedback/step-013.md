# Step 013 — Cycle-4 LLM tailoring Completion check

Cycle: 4
Pass: 1
Files Changed: scripts/llm.py, scripts/pcli.py, tests/test_llm.py, tests/test_cli.py, tests/fixtures/fake-jd.txt

## Advisor Verdict
NEEDS_REVIEW

## Advisor Feedback
1. cmd_preset_run calls cmd_build_resume with explicit None for old optional args but omits new LLM params (jd, tone, show_llm_diff, no_cache).
2. Typer-decorated functions: omitted params default to OptionInfo wrappers, not None/False.
3. Bug: `if jd:` evaluates OptionInfo as truthy, unexpectedly triggering LLM path on preset run.
4. Fix: add jd=None, tone=None, show_llm_diff=False, no_cache=False to the cmd_build_resume call inside cmd_preset_run.

## Sonnet Response
- 적용: Add jd=None, tone=None, show_llm_diff=False, no_cache=False to cmd_preset_run's direct call to cmd_build_resume.
