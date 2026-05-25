# Codex Review v2

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] Provenance enforcement does not cover the generated answer or displayed target context
- Location: `scripts/llm.py:806-870`
- Analysis: The fix correctly rebuilds `personal_facts` and `selected_cards` from requested
  cards, but still returns LLM/cache-provided `answer_draft`, `target_context_used`, and
  `selection_reason` without grounding validation. Reproduction with the single card
  `Auth Service` and question `challenge` yields clean server facts while still returning
  `target_context_used=["Organization: Fabricated Corp"]` and
  `answer_draft="As CEO, I increased revenue 999% at Fabricated Corp."`.
- Impact: The text the user actually copies into an application can still invent a personal
  role, metric, or organization fact. The single-trust-source and source-separation
  requirements remain unmet even though the adjacent evidence panel looks valid.
- Fix direction: Construct `target_context_used` server-side from the submitted context and
  do not accept fabricated selection rationale as evidence. For `answer_draft`, introduce a
  grounding guard appropriate to this feature: reject/fallback when the structured result
  contains claims not supported by the authoritative fact/context bundle, or constrain the
  generated output to claim units that can be verified before display. Extend the adversarial
  regression test to assert the final answer and displayed context cannot preserve the
  fabricated `CEO`, `999%`, or organization statements.

### ISSUE-2 [MEDIUM] Blind-hiring redaction is applied only to mock previews, not LLM previews
- Location: `scripts/dashboard.py:716-830`, `scripts/llm.py:736-870`
- Analysis: `_mock_application_preview()` filters flagged title/summary text, but
  `application_preview_llm()` independently rebuilds `personal_facts` without using the
  blind-hiring filter. With `blind_hiring=true` and a card titled
  `Seoul National University Graduate` whose summary contains `Born in Busan`, the LLM path
  returns both identifiers in `personal_facts`.
- Impact: Enabling the AI provider disables the privacy behavior the UI promises for
  blind-hiring applications. The requirement and updated documentation describe the
  restriction as implemented, but it is not implemented on the live path.
- Fix direction: Factor authoritative fact construction/redaction into one shared helper used
  by mock and LLM paths, and add an LLM-path test using the identity fixture with
  `blind_hiring=true`.

## Previous Issue Status

- ISSUE-1: UNRESOLVED - card metadata is authoritative now, but unsupported claims remain in
  the displayed/copied draft and context.
- ISSUE-2: UNRESOLVED - deterministic mock is corrected, but enabled-LLM behavior bypasses
  the same blind-hiring guarantee.
- ISSUE-3: RESOLVED - fallback reason rendering and malformed classification are present.
- ISSUE-4: RESOLVED - selection rationale and assumptions now render in the application UI.
- ISSUE-5: RESOLVED - specification, test-case, and acceptance documents were updated.

## Regression Check

No unrelated regression was found. The two blocking findings are incomplete enforcement of the
previously reported safety boundaries across the live LLM path.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Separate application-writing preview in `/studio` | PASS | Template and JS hooks present. |
| Deterministic cover letter and answer from selected live cards/context | PASS | Mock handling and blind-hiring tests now cover deterministic output. |
| Personal facts only from selected cards and visibly separated context | FAIL | LLM answer/context still accepts fabricated content; ISSUE-1. |
| Question/competency interpretation and character compliance | PASS | Existing and added tests pass. |
| Blind-hiring prevention in deterministic output and LLM contract | FAIL | Live-path response facts bypass filtering; ISSUE-2. |
| Visible safe fallback reasons | PASS | Rendering and malformed classification added. |
| Existing flows do not regress | PASS | Automated regression checks pass. |
| Application previews are not persisted | PASS | Existing no-write test passes. |

## Automatic Checks

- `uv run pytest -v`: PASS (`436 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

No scope creep identified. Untracked `.read-counter` files remain excluded from review changes.
