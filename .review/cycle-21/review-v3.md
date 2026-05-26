# Codex Review v3

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] Regex guard still permits fabricated narrative claims in copyable LLM output
- Location: `scripts/dashboard.py:436-445`, `scripts/dashboard.py:918-944`,
  `scripts/llm.py:840-883`
- Analysis: `_has_ungrounded_claims()` checks only new numeric tokens and a small set of
  C-suite titles. It does not validate ordinary personal or organization claims in the text
  the user copies. With the selected card `Auth Service` (`Rebuilt auth service.`) and no
  organization context, an LLM result whose answer is
  `I founded Fabricated Corp and led its global expansion.` is returned with
  `refine_source=llm` rather than falling back. This contains no number or listed C-suite
  title, so the guard cannot see it.
- Impact: The application answer remains able to invent career facts and employer claims
  outside canonical cards and supplied target context. The central grounded-writing contract
  is still not enforced.
- Fix direction: Do not model factual grounding as a keyword deny-list. Use a representation
  where output claims are either composed from authoritative server-provided fact/context
  units or returned with explicit source bindings that the server can validate before display.
  Any unbound narrative claim must be withheld or clearly require user confirmation. Add tests
  for qualitative fabrications, invented organization relationships, and claims that reuse
  numbers appearing only in job/question context.

### ISSUE-2 [HIGH] Blind-hiring protection still leaks identity text in live answer and selected-card UI
- Location: `scripts/dashboard.py:389-415`, `scripts/dashboard.py:918-938`,
  `scripts/llm.py:831-883`, `scripts/static/studio.js:386-395`
- Analysis: The route overwrites `personal_facts` with redacted facts, but does not redact or
  reject `answer_draft` or `selected_cards`. With blind hiring enabled for a card titled
  `Seoul National University Graduate` whose summary includes `Born in Busan`, a live-path
  LLM response containing the same identifiers remains `refine_source=llm`; its draft and
  the rendered selected-card title/reason still expose those identifiers.
- Impact: The application can reveal prohibited background information precisely when the
  user has requested blind-hiring protection. Redacting only the facts list creates a false
  sense of safety.
- Fix direction: Apply blind-hiring treatment to every visible/output field, including
  answer text and selected-card rationale/title, or block the preview pending user-safe
  replacement. Add LLM-path tests asserting identifiers are absent from `answer_draft` and
  `selected_cards`, not only `personal_facts`.

## Previous Issue Status

- ISSUE-1: UNRESOLVED - server-built context fields are improved, but generated prose remains
  ungrounded outside two regex categories.
- ISSUE-2: UNRESOLVED - the facts panel is redacted, but live answer/card display still leaks
  blind-hiring identifiers.
- ISSUE-3: RESOLVED.
- ISSUE-4: RESOLVED.
- ISSUE-5: RESOLVED.

## Regression Check

No unrelated regression found. The newly introduced guard is incomplete for the exact safety
boundary it was intended to close.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Separate application-writing preview in `/studio` | PASS | UI surface remains present. |
| Deterministic preview behavior | PASS | Mock flow and tests pass. |
| Personal claims and context grounded only in approved sources | FAIL | ISSUE-1 reproduction. |
| Question/competency and character feedback | PASS | Tests pass. |
| Blind-hiring restriction | FAIL | ISSUE-2 reproduction on LLM path. |
| Safe fallback visibility | PASS | Previous issue remains resolved. |
| Existing flows do not regress | PASS | Automatic checks pass. |
| Application previews are not persisted | PASS | No persistence regression observed. |

## Automatic Checks

- `uv run pytest -v`: PASS (`438 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Issue-Velocity Cap

`ISSUE-1` remains unresolved through v1, v2, and v3. The Same-Issue Stagnation trigger is
reached; `status.txt` is set to `escalated` so the grounding approach can be reconsidered
before another implementation pass.

## Changes Outside Plan

No scope creep identified. Untracked `.read-counter` files remain excluded from review changes.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Replace regex grounding guard with server-composed answer draft
- `scripts/dashboard.py`: Removed `_has_ungrounded_claims()`. Added `_compose_answer_draft(output_type, safe_titles, tc)` that builds answer text exclusively from server-authoritative card titles and submitted `target_context` fields.
- `scripts/dashboard.py`: `_mock_application_preview()` now calls `_compose_answer_draft()` instead of inlining the draft composition, eliminating duplication.
- `scripts/dashboard.py`: Route LLM success path now calls `_compose_answer_draft()` server-side and overwrites `answer_draft`, `character_count`, `character_limit`, `within_limit` in the LLM result. LLM prose never reaches the client.
- `tests/test_cycle21.py`: Removed `test_adversarial_llm_answer_triggers_grounding_fallback` (tested the now-removed regex guard). Added `test_llm_path_qualitative_fabrication_absent_from_answer` (qualitative invented narrative absent from answer) and `test_llm_path_answer_composed_from_card_facts_only` (answer contains real card title, not LLM-invented content).
- 자동 체크: pytest 439 ✅ / ruff check ✅ / ruff format ✅

RESOLVED: ISSUE-2 — Blind-hiring identity triggers full mock fallback; selected_cards also redacted
- `scripts/dashboard.py`: Route LLM success path: when `_id_flagged` is True, sets `fallback_reason = None` and falls through to the mock path instead of overriding fields and returning LLM output. This ensures answer_draft, selected_cards, and all other output fields are produced by the mock (which correctly applies redaction).
- `scripts/dashboard.py`: `_mock_application_preview()` now excludes identity-flagged cards from `selected_cards_info` when `blind_hiring=True`, preventing card title and selection_reason from exposing education/background identifiers.
- `tests/test_cycle21.py`: Updated `test_llm_path_blind_hiring_identity_excluded_by_route` to assert `refine_source == "mock"`, that answer_draft and selected_cards titles/reasons are clean of identity content, and that `BLIND_HIRING_PERSONAL_IDENTIFIERS` code is present.
- 자동 체크: pytest 439 ✅
