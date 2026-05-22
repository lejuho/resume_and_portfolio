# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [HIGH] LLM summary normalization can return drafts that fail card validation

- Location: `scripts/llm.py:254`
- Analysis: `studio_refine_llm()` normalizes the LLM summary with `[:300]`, but the canonical `Card.summary` schema allows at most 200 characters. Because `/api/studio/save` writes `draft["summary"]` into card frontmatter and validates with `Card.model_validate`, an LLM response with a 201-300 character summary will refine successfully but fail at save time.
- Impact: Violates the Sprint Contract requirements that "Saved LLM-derived draft passes `CardRepo` validation" and that LLM output is validated/normalized before returning to the UI.
- Fix direction: Cap Studio LLM summary to 200 characters, matching the card schema. Add a fake-LLM test with an overlong summary that verifies the refine response summary is <= 200 and that the resulting draft can be saved.

### ISSUE-2 [MEDIUM] LLM evidence type is passed through without schema normalization

- Location: `scripts/llm.py:263`
- Analysis: `studio_refine_llm()` passes `e["type"]` through directly. The prompt asks for `repo|demo|other`, but LLMs can still return values outside the `Evidence.type` schema (`repo|deck|writeup|demo|article|other`). Those invalid values are returned to the UI and later rejected by `/api/studio/save`.
- Impact: Same normalization gap as ISSUE-1: a successful LLM refine can produce a draft that fails card validation. The plan explicitly says to validate/normalize LLM output before returning it.
- Fix direction: Add an evidence type whitelist matching `scripts.card.EVIDENCE_TYPE`; fallback unknown values to `other`. Add a fake-LLM test with an invalid evidence type and verify save still succeeds.

## Sprint Contract Check

- Existing `/studio` mock flow works without `ANTHROPIC_API_KEY`: PASS
- `/api/studio/refine` can return LLM-derived draft data through a fake client in tests: PASS
- Response shape remains compatible with existing Studio JS: PASS
- Malformed LLM output does not produce a 500: PASS
- Raw pasted input is still not persisted by default: PASS
- Saved LLM-derived draft passes `CardRepo` validation: FAIL for overlong summary / invalid evidence type
- No visual upload/path editing is introduced: PASS
- Existing dashboard and build behavior remains unchanged: PASS

## Automatic Checks

- `uv run pytest -v`: PASS
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS (warnings only, no errors)
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Changes Outside Plan

None found.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Cap LLM summary to 200 chars matching Card schema
- `scripts/llm.py:254`: changed `[:300]` → `[:200]`
- `tests/test_llm_studio.py`: added `test_refine_llm_overlong_summary_is_capped` (asserts `len(summary) <= 200`) and `test_refine_llm_overlong_summary_draft_saves` (save returns 201)

RESOLVED: ISSUE-2 — Add evidence type whitelist, fallback unknown types to "other"
- `scripts/llm.py`: added `_VALID_EVIDENCE_TYPES` frozenset matching `EVIDENCE_TYPE` in card.py; evidence normalization now checks membership, falls back to `"other"`
- `tests/test_llm_studio.py`: added `test_refine_llm_invalid_evidence_type_normalizes_to_other` and `test_refine_llm_invalid_evidence_type_draft_saves`

자동 체크: pytest 240 passed ✅ / ruff check ✅ / ruff format ✅
