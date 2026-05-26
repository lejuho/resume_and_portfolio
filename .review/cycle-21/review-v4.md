# Codex Review v4

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] The amended verified-draft response and UI contract is not implemented
- Location: `scripts/llm.py:649-713`, `scripts/dashboard.py:840-853`,
  `scripts/templates/studio.html:231-237`, `scripts/static/studio.js:386-461`
- Analysis: The implementation does replace `answer_draft` on the route success path with
  server-composed text, but the amended contract is broader: it requires server-owned
  `fact_ledger`, validated `selected_facts`, `draft_provenance=server_composed`, and
  separately presented non-copyable `ai_guidance`. None of these fields or UI affordances
  exists in code or tests. The LLM schema and prompt still ask the provider to generate
  `answer_draft` prose, even though that field is later overwritten. In addition, non-blind
  `selected_cards[].selection_reason` remains provider-generated text rendered directly in
  the evidence section rather than server-derived rationale or separate guidance.
- Impact: The response cannot demonstrate provenance as specified, guidance cannot be
  distinguished from verified text, and the implementation does not satisfy the
  user-approved Escalation Amendment v1 contract.
- Fix direction: Replace the provider contract with advisory output keyed by server-issued
  fact IDs; compose and label the verified draft server-side; render guidance separately
  from the copy target; build displayed selection rationale from safe ledger values; cover
  the revised API shape and UI labels in tests.

### ISSUE-2 [HIGH] Blind-hiring identifiers are sent to the provider before the route falls back
- Location: `scripts/dashboard.py:900-918`, `scripts/llm.py:736-746`
- Analysis: The route invokes `application_preview_llm()` with the original selected cards
  before it evaluates `_build_card_facts(cards, blind_hiring=True)` and falls back to mock.
  `application_preview_llm()` constructs `card_facts_block` directly from each original card
  title and summary. An isolated reproduction with the card title
  `Seoul National University Graduate` and summary `Born in Busan; led analytics migration.`
  confirmed that both identifier strings are included in the provider prompt even when
  `blind_hiring=true`.
- Impact: The amended Blind-Hiring Policy requires identity/background-bearing text to be
  excluded before any LLM request. The UI output may be redacted, but private material has
  already crossed the provider boundary.
- Fix direction: Construct the redacted, server-owned fact ledger before provider invocation
  and pass only that ledger to the LLM helper. Add an assertion on captured provider prompt
  content, not merely on the returned preview.

## Previous Issue Status

- ISSUE-1: UNRESOLVED - `answer_draft` is now replaced server-side, but the revised
  fact-ledger/provenance/advisory contract is still absent.
- ISSUE-2: UNRESOLVED - response redaction improved, but identifiers still reach the
  provider before fallback under blind-hiring mode.
- ISSUE-3: RESOLVED - fallback reason rendering and malformed classification remain present.
- ISSUE-4: RESOLVED - selection and assumption UI blocks remain present.
- ISSUE-5: RESOLVED - the previously requested initial documentation updates remain present.

## Regression Check

The latest implementation closes the previously reproduced copyable free-prose injection:
non-blind `answer_draft` is now overwritten by `_compose_answer_draft()`. It does not
introduce an unrelated regression found by the automatic checks. The findings above are
incomplete implementation of the approved amendment and a remaining privacy boundary breach.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Provider prose cannot enter copyable `answer_draft` | PASS | Route replaces LLM draft with `_compose_answer_draft()`. |
| Copyable draft is marked `draft_provenance=server_composed` and traceable to a ledger | FAIL | Required provenance and ledger fields are absent; ISSUE-2. |
| Unknown/unselected `selected_fact_ids` cannot affect verified draft | FAIL | Fact-ID advisory contract is not implemented; ISSUE-2. |
| Blind-hiring content is excluded before provider transmission and from preview | FAIL | Raw card title/summary enter prompt before fallback; ISSUE-1. |
| `ai_guidance` is separate and non-copyable | FAIL | No guidance contract or UI exists; ISSUE-1. |
| Fallback visibility, no persistence, dashboard, resume, and portfolio flows remain green | PASS | Automatic checks pass. |

## Automatic Checks

- `uv run pytest -v`: PASS (`439 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS
- Captured-prompt reproduction with `blind_hiring=true`: FAIL
  (`Seoul National University` and `Born in Busan` were both present in provider prompt)

## Changes Outside Plan

No unrelated implementation scope expansion identified. Untracked `.read-counter` files
remain excluded from review changes.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Implement Escalation Amendment v1 verified-draft contract
- `scripts/llm.py`: Replaced `_APP_WRITING_SCHEMA` / `_APP_WRITING_PROMPT` with `_APP_ADVISORY_SCHEMA` / `_APP_ADVISORY_PROMPT`. Provider now returns advisory output only: `selected_fact_ids`, `question_intent`, `competency_target`, `missing_info`, `ai_guidance`. `application_preview_llm()` signature changed from `cards: list` to `fact_ledger: list` (pre-built, pre-redacted by server); returns `{"ok": True, "advisory": {...}}`.
- `scripts/dashboard.py`: Added `_build_fact_ledger(cards, blind_hiring)` — creates stable fact IDs (F1, F2…), applies blind-hiring redaction, returns `(ledger, identity_flagged)`. Added `_ledger_to_personal_facts()` and `_ledger_to_selected_cards()` helpers. `_mock_application_preview()` uses `_build_fact_ledger`; response now includes `fact_ledger`, `selected_facts`, `draft_provenance="server_composed"`, `ai_guidance=[]`, `selected_cards[].display_title`. Route LLM path validates `selected_fact_ids` against ledger, discards unknown IDs, composes `answer_draft` server-side from validated entries.
- `scripts/templates/studio.html`: Added `st-app-guidance-section` / `st-app-guidance-list` for advisory AI guidance (non-copyable). Draft labeled "Verified draft".
- `scripts/static/studio.js`: `renderAppPreview()` now renders `ai_guidance` in the guidance section and uses `display_title` for selected_cards.
- `tests/test_cycle21.py`: Updated `test_llm_app_preview_google_schema_used` and `test_app_writing_schema_has_required_fields` for advisory schema. Updated `test_llm_provenance_overrides_adversarial_llm_response` for new API. Updated `test_mock_has_selected_cards_field` and blind-hiring route test to use `display_title`. Added: `test_response_includes_fact_ledger_and_provenance`, `test_llm_path_unknown_fact_ids_discarded`, `test_llm_path_response_includes_new_fields`, `test_studio_html_has_app_guidance_section`, `test_studio_js_renders_ai_guidance_separately`.
- 자동 체크: pytest 445 ✅ / ruff check ✅ / ruff format ✅

RESOLVED: ISSUE-2 — Build fact ledger before provider call; skip LLM when identity flagged
- `scripts/dashboard.py`: Route now calls `_build_fact_ledger(cards, blind_hiring)` BEFORE any LLM invocation. If `_id_flagged=True`, the LLM call is skipped entirely (`can_try_llm and not _id_flagged` guard). Identity/background text never reaches the provider prompt.
- `tests/test_cycle21.py`: Added `test_blind_hiring_llm_not_called_when_identity_flagged` which asserts `application_preview_llm` is never called when `blind_hiring=True` with an identity card.
- 자동 체크: pytest 445 ✅
