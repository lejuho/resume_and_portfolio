# Step 015 — Cycle-5 polish + acceptance Approach check

Cycle: 5
Pass: 1
Files Changed: scripts/pcli.py, .gitignore, README.md, tests/test_build_dry_run.py, tests/test_cli.py

## Advisor Verdict
OK

## Advisor Feedback
1. Validation: runtime guard is correct. Add VALID_TONES/VALID_LANGS frozensets at module level; use typer.BadParameter (not exit 1) for consistent Typer error format.
2. Dry-run test: add tests/test_build_dry_run.py. Assert no .pdf/.pptx in tmp output dir post-invoke.
3. .gitignore: confirm output/, .cache/, .build/, profile.yaml, *.pdf, *.pptx, __pycache__/. Append missing.
4. README: include Requirements (typst >=0.11, Python 3.11+, uv, optional ANTHROPIC_API_KEY). Quickstart, commands table, output paths, presets, LLM optional.

## Sonnet Response
- 적용 (1): VALID_TONES/VALID_LANGS frozensets + typer.BadParameter
- 적용 (2): tests/test_build_dry_run.py 신규
- 적용 (3): .gitignore 누락 항목 추가
- 적용 (4): README.md v1 quickstart 재작성
