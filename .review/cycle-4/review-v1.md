# Codex Review v1

## Verdict

BLOCKED

Cycle 4 is close, but the final resume build context does not retain LLM metadata. This breaks the plan requirement to include score/rewrite metadata under `.build/resume-data.json` and leaves no build artifact trace of which LLM scores or rewrites were applied.

## Findings

### 1. BLOCKER: `meta.llm` is written before render, then overwritten

- Files:
  - `scripts/pcli.py:486`
  - `scripts/render_resume.py:73`
- Problem:
  - `cmd_build_resume` writes `.build/resume-data.json` with only `{"meta": {"llm": ...}}`.
  - Immediately after that, it calls `build_resume(...)`.
  - `build_resume` reconstructs the full context and rewrites `.build/resume-data.json`, replacing the previous file with a `meta` object that only contains `generated_at`, `template`, `lang`, and `card_count`.
- Reproduction:
  - Ran `uv run pcli build resume --jd tests\fixtures\fake-jd.txt --tone formal --max-items 1 --verbose`.
  - Build completed via no-key fallback.
  - Checked `.build\resume-data.json`; it contained `generated_at` and `card_count`, but no `llm`, `scores`, or `rewrites`.
- Expected:
  - Final `.build/resume-data.json` should contain normal resume context plus `meta.llm`.
- Suggested fix:
  - Pass `llm_meta` into `build_resume`, or add a generic `extra_meta` parameter to `build_resume` and merge it into `context["meta"]` before writing JSON.
  - Add a test that runs a fake/cached LLM resume build and asserts `.build/resume-data.json["meta"]["llm"]` exists.

## Sprint Contract Check

- Existing non-LLM commands pass without `ANTHROPIC_API_KEY`: PASS
- `build resume --jd ... --tone ... --dry-run` shows LLM intent: PASS
- `build resume --jd ... --tone ...` falls back to non-LLM summaries when no key/cache: PASS
- `llm tailor` without API key/cache exits non-zero with clear error: PASS
- Cache/module/test structure exists: PASS
- Source MDX mutation was not observed: PASS
- Final `.build/resume-data.json` includes `meta.llm`: FAIL

## Automatic Checks

- `uv run pytest -v`: PASS, 119 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run pcli build resume --jd tests\fixtures\fake-jd.txt --tone formal --dry-run`: PASS
- `uv run pcli llm tailor --cards pocavault-seoulana --jd tests\fixtures\fake-jd.txt --no-cache`: expected non-zero without API key/cache; got clear `ANTHROPIC_API_KEY is not set`

## Notes

- Current git status only shows pre-existing untracked files: `.claude-flow/`, `.mcp.json`, `CLAUDE.md`.
- A resume PDF was generated during verification under `output/resumes/`; output artifacts appear ignored and did not show in git status.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY

RESOLVED: ISSUE-1 — LLM meta now persisted in final resume-data.json
- `scripts/render_resume.py`: added `extra_meta: Optional[dict] = None` to `build_resume`; merged via `{**meta, **extra_meta}` before JSON write — prevents key-collision silent overwrite.
- `scripts/pcli.py`: removed pre-write block; passes `extra_meta={"llm": llm_meta}` directly to `build_resume`. Single write path, no race.
- `tests/test_cli.py`: added `test_build_resume_llm_meta_persisted_in_resume_data_json` — mocks typst + subprocess + LLM client; asserts `meta.llm.scores` and `meta.llm.rewrites` present in `.build/resume-data.json`.

자동 체크: pytest ✅ 120 passed / ruff check ✅ / ruff format ✅
