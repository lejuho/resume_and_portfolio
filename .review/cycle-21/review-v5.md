# Codex Review v5

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] `selected_facts` does not describe the facts used in the verified draft
- Location: `scripts/dashboard.py:960-1002`
- Analysis: The route validates the provider-selected IDs, but `_compose_answer_draft()` can
  silently switch back to all activity entries when the selected ledger contains only a
  summary, metric, or evidence entry. Reproduction with the `Auth Service` ledger and
  advisory selection `["F2"]` (the summary fact) returned
  `selected_facts=["F2"]` while `answer_draft` contained `Auth Service`, the unselected
  `F1` activity fact; `selected_cards` was empty.
- Impact: Although draft prose is server-composed, the reported provenance cannot trace the
  text actually shown and copied. This fails the amended contract that the verified draft be
  composed from validated selected ledger facts and expose accurate provenance.
- Fix direction: Make composition consume the validated selected ledger entries directly, or
  explicitly expand the selection with every additional ledger fact used by the template
  before returning `selected_facts` and `selected_cards`. Add summary-only and metric-only
  selection tests asserting every factual string in the draft is represented in provenance.

### ISSUE-2 [HIGH] Blind-hiring still exposes provider-generated identity guidance
- Location: `scripts/dashboard.py:942-1012`, `scripts/static/studio.js:397-400`
- Analysis: The fix correctly avoids calling the provider when a selected card is flagged,
  but a blind-hiring request over a non-flagged card can still call the provider. The route
  accepts all returned `ai_guidance` strings without applying `_IDENTITY_RE` or a warning
  fallback. Reproduction using a clean `Auth Service` card with `blind_hiring=true` and
  advisory guidance `Born in Busan; Seoul National University graduate.` returned that text
  in `preview.ai_guidance`, which the UI renders.
- Impact: The amended policy explicitly requires discarded provider guidance and a safe
  warning if excluded identity/background content is returned despite redacted input.
  Blind-hiring remains incomplete on a visible output surface.
- Fix direction: Under blind-hiring, screen advisory visible fields at least including
  `ai_guidance` before constructing the preview, discard flagged guidance, and add a safe
  missing-info warning. Cover a clean-input/provider-hallucinated-identity route test.

### ISSUE-6 [MEDIUM] Advisory cache entries are reused across different fact ledgers
- Location: `scripts/llm.py:726-748`
- Analysis: The new cache payload includes only stable positional `fact_ids` such as `F1`
  and `F2`, not the ledger texts or source card identifiers that determine the prompt.
  Reproduction first requested guidance for ledger `F1 = Auth Service`, then requested the
  same question for `F1 = Payments Platform`; the second request made no provider call and
  returned cached guidance `Discuss Auth Service impact.`.
- Impact: Advisory text and selected-fact choices can describe a different career card than
  the preview being generated. This can expose stale unrelated material and makes the LLM
  guidance untrustworthy even though the copyable draft remains server-composed.
- Fix direction: Include the redacted ledger content or a deterministic hash of its full
  serialized entries in the cache-key payload, and add a cache-separation test for two
  different ledgers with identical positional IDs.

### ISSUE-7 [LOW] User-facing documentation still describes the superseded response contract
- Location: `requirements-dashboard.md:610-622`, `docs/acceptance-studio.md:90-101`,
  `docs/test-cases.md:185-201`
- Analysis: The amendment requires documentation updates for the verified draft, advisory
  guidance, provenance ledger, and pre-provider blind-hiring boundary. The implementation
  commit changes no documentation; requirements still describe only `personal_facts` and
  overridden provenance, while manual acceptance still says simply to copy "Draft text."
- Impact: Acceptance does not exercise the new trust boundary and the published behavior no
  longer matches the API/UI introduced by this implementation.
- Fix direction: Update requirement status and acceptance/test-case wording to require
  `draft_provenance=server_composed`, visible non-copyable guidance, ledger traceability, and
  blind-hiring provider-boundary verification.

## Previous Issue Status

- ISSUE-1: UNRESOLVED - fact ledger and verified-draft fields now exist, but the returned
  selection provenance is not guaranteed to match facts used in the copyable draft.
- ISSUE-2: UNRESOLVED - original flagged card text is no longer transmitted, but
  provider-generated identity text is still rendered during blind-hiring flows.
- ISSUE-3: RESOLVED - fallback reason rendering and malformed classification remain present.
- ISSUE-4: RESOLVED - selected-card and assumption UI blocks remain present.
- ISSUE-5: RESOLVED - initial Cycle 21 documentation changes remain present.
- ISSUE-6: NEW - advisory cache identity does not include ledger content.
- ISSUE-7: NEW - amendment documentation changes were omitted.

## Regression Check

The v4 fix substantially improves the trust boundary: `answer_draft` is composed on the
server, the advisory schema no longer asks the provider for copyable prose, and flagged
selected card titles/summaries are withheld before a provider call. The findings above cover
remaining amended-contract failures and newly introduced cache behavior.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Provider prose cannot enter copyable `answer_draft` | PASS | Advisory-only provider contract and server composition are implemented. |
| Verified draft carries accurate `server_composed` ledger provenance | FAIL | Selected summary-only reproduction uses unselected activity text; ISSUE-1. |
| Unknown/unselected provider IDs cannot influence verified draft | PASS | Unknown IDs are discarded and tests cover deterministic fallback. |
| Blind-hiring excludes identity content before provider transmission and from preview | FAIL | Provider-generated identity guidance renders in blind mode; ISSUE-2. |
| AI guidance is visually separate from the copy action | PASS | Dedicated guidance section and verified-draft label exist. |
| Existing fallback, no-persistence, dashboard, resume, and portfolio flows remain green | PASS | Automatic checks pass. |

## Automatic Checks

- `uv run pytest -v`: PASS (`445 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS
- Blind-hiring generated-guidance reproduction: FAIL
  (`Born in Busan; Seoul National University graduate.` was returned in `ai_guidance`)
- Selected-summary provenance reproduction: FAIL
  (`selected_facts=["F2"]`, but draft used unselected `F1` activity text)
- Cross-ledger advisory cache reproduction: FAIL
  (the `Payments Platform` request reused `Auth Service` guidance without a provider call)

## Changes Outside Plan

No unrelated implementation scope expansion identified. The revised-plan documentation
updates are missing as described in ISSUE-7. Untracked `.read-counter` files remain excluded
from review changes.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY
- ISSUE-6: APPLY
- ISSUE-7: APPLY

### Applied

RESOLVED: ISSUE-1 — selected_facts expanded to include activity fact of every represented card
- `scripts/dashboard.py`: After filtering advisory IDs, collect represented `source_card_id`s
  and union in every activity-kind entry for those cards. `sel_ids` ordering follows ledger
  order. Fallback to all ledger facts when no valid advisory IDs returned.
- Added `test_selected_facts_expands_to_include_activity_for_summary_selection`: LLM selects
  only summary ID → `selected_facts` must contain at least one activity ID.

RESOLVED: ISSUE-2 — blind-hiring guidance screening applied post-provider
- `scripts/dashboard.py`: Under `blind_hiring=True`, filter `_ai_guidance` list through
  `_IDENTITY_RE`; withheld strings trigger `BLIND_HIRING_GUIDANCE_REDACTED` missing-info entry.
- Added `test_blind_hiring_provider_guidance_identity_withheld`: LLM returns identity phrase
  in guidance → phrase absent from preview, warning code present.

RESOLVED: ISSUE-6 — advisory cache key includes full ledger content
- `scripts/llm.py`: Cache payload field changed from `"fact_ids": [e["id"] for e in ...]`
  to `"fact_ledger": fact_ledger` (full dicts). Same positional ID with different card text
  now produces a different cache key.
- Added `test_advisory_cache_separates_different_ledgers`: two single-entry ledgers sharing
  `F1` but different `text`/`source_card_id` produce different `_cache_key` values.

RESOLVED: ISSUE-7 — documentation updated to amended contract
- `requirements-dashboard.md:610-622`: D-009 status paragraph updated to describe
  fact_ledger, advisory-only LLM contract, draft_provenance, blind-hiring pre-provider check.
- `docs/test-cases.md` PT-APP-001–006: expected results updated for server_composed provenance,
  fact_ledger fields, advisory separation.
- `docs/acceptance-studio.md` rows 3–12: acceptance scenarios updated for verified draft label,
  AI guidance section, provider skip under blind-hiring, guidance screening.

자동 체크: pytest 72 passed ✅ / ruff check ✅ / ruff format ✅
