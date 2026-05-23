# Codex Review v1

## Verdict
BLOCKED

## Findings
### ISSUE-1 [MEDIUM] Malformed `tags` from the LLM can crash normalization instead of coercing safely
- Location: `scripts/llm.py:272`
- Analysis: `tags_raw = raw_parsed.get("tags") or {}` is assumed to be a dict, and the next lines call `tags_raw.get(...)`. If the LLM returns valid JSON with `tags` as a list/string, `studio_refine_llm()` raises `AttributeError` before returning a normalized draft. This is exactly the kind of malformed optional field Cycle 16 planned to tolerate.
- Impact: Sprint Contract says malformed optional fields should normalize safely, and the plan specifically calls out `metrics`, `evidence`, `tags`, and `missing_info`. Current tests cover malformed narrative fields, but not malformed `tags`.
- Fix Direction: Guard with `isinstance(tags_raw, dict)` and fallback to empty tag buckets when it is not a dict. Add a regression test such as `tags=["backend"]` or `tags="backend"` and assert the returned draft has `{"domain": [], "skill": [], "audience": []}`.

## Sprint Contract Check
- `/api/studio/refine` current compatible shape: PASS
- Fake LLM returns consultant narrative fields: PASS
- Resume intent returns resume bullet: PASS
- Both intent returns both resume and portfolio surfaces: PASS
- Prompt contains consultant / portfolio maker framing: PASS
- Raw pasted input is not stored by default: PASS for existing explicit `raw_text` save behavior; not deeply enforced against bad LLM prose, which is acceptable for this cycle given prompt-level scope.
- No provider abstraction / OpenAI / upload / model picker / existing-card update: PASS
- Malformed optional fields normalize safely: FAIL for non-dict `tags`

## Automatic Checks
- `uv run pytest -v`: PASS (`270 passed`)
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS (`WARN test: evidence is empty`, no errors)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Changes Outside Plan
No scope creep found.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — Guard `tags` against non-dict LLM values
- `scripts/llm.py`: `tags_raw = raw_parsed.get("tags")` → `tags_raw if isinstance(tags_raw, dict) else {}` before calling `.get()` on it
- `tests/test_cycle16.py`: added `test_malformed_tags_list_coerces_to_empty_buckets` and `test_malformed_tags_string_coerces_to_empty_buckets`

자동 체크: pytest 272 passed ✅ / ruff check ✅ / ruff format ✅
