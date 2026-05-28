# Codex Review v6

## Verdict
BLOCKED

## Findings

### ISSUE-8 [HIGH] Blind-hiring exposes provider identity prose through advisory metadata fields
- Location: `scripts/dashboard.py:988-1030`, `scripts/static/studio.js:406-411`,
  `scripts/static/studio.js:429-438`
- Analysis: The v5 fix filters `ai_guidance` only. In a `blind_hiring=true` request over a
  clean `Auth Service` card, an advisory response with
  `question_intent="Assess Seoul National University graduate background"`,
  `competency_target="Born in Busan leadership"`, and
  `missing_info[0].message="Confirm university alumni history."` was returned unchanged.
  The Studio UI renders each of these provider-owned fields visibly.
- Impact: Amendment v1 requires excluded identity/background content to be absent anywhere
  in the returned/rendered preview. Guidance screening satisfies the narrower v5 finding but
  does not satisfy that trust-boundary contract.
- Fix direction: Apply the blind-hiring screening policy to every provider-derived visible
  string before response serialization, including interpretation and missing-information
  text, or replace flagged values with server-owned safe wording. Add an adversarial route
  test for every rendered advisory surface.

### ISSUE-9 [HIGH] Blind-hiring transmits identity text stored outside card title and summary
- Location: `scripts/dashboard.py:389-423`, `scripts/dashboard.py:943-950`
- Analysis: `_build_fact_ledger()` decides whether a card is identity-flagged by searching
  only `title` and `summary`, then appends `metrics` and evidence URL text without screening.
  A card titled `Payment Service` with safe summary and metric
  `Seoul National University graduate led delivery` produced a ledger containing that metric
  and passed it to `application_preview_llm()` under `blind_hiring=true`.
- Impact: Excluded card content reaches the provider prompt and the returned `fact_ledger`,
  failing the amended pre-provider boundary and visible-output requirements.
- Fix direction: Build the blind-hiring ledger by filtering or excluding identity-bearing
  text across every transmitted/displayed card field, including metrics and evidence.
  Add fixtures where only a metric or evidence value is flagged and assert the provider input
  and preview contain no excluded text.

## Previous Issue Status

- ISSUE-1: RESOLVED - summary-only advisory selection is expanded with the represented
  activity fact before composing and returning provenance.
- ISSUE-2: RESOLVED - provider identity text in `ai_guidance` is withheld with
  `BLIND_HIRING_GUIDANCE_REDACTED`; ISSUE-8 identifies different unfiltered visible fields.
- ISSUE-3: RESOLVED - fallback reason rendering and malformed classification remain present.
- ISSUE-4: RESOLVED - selected-card and assumption UI blocks remain present.
- ISSUE-5: RESOLVED - initial Cycle 21 documentation changes remain present.
- ISSUE-6: RESOLVED - cache identity now includes the full fact ledger content.
- ISSUE-7: RESOLVED - amended contract documentation is present in all three required files.

## Regression Check

The review-v5 fixes resolve provenance expansion, `ai_guidance` screening, cache separation,
and documentation alignment on their covered paths. Independent blind-hiring enumeration
found additional transmitted and rendered identity surfaces not protected by that change.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Provider prose cannot enter copyable `answer_draft` | PASS | Advisory-only route still composes `answer_draft` server-side. |
| Verified draft carries accurate `server_composed` ledger provenance | PASS | Selection is expanded to activity facts; targeted test passes. |
| Unknown/unselected provider IDs cannot influence verified draft | PASS | Validation/fallback behavior remains covered and green. |
| Blind-hiring excludes identity content from provider input and all preview surfaces | FAIL | Advisory metadata leak in ISSUE-8; metric transmission leak in ISSUE-9. |
| AI guidance is separated from copy and screened under blind hiring | PASS | Separate UI section and guidance redaction test pass. |
| Advisory cache is isolated by ledger content | PASS | Full ledger participates in key payload; separation test passes. |
| Required documentation aligns with verified-draft contract | PASS | Requirements and acceptance/test-case documents were updated. |
| Existing fallback, no-persistence, dashboard, resume, and portfolio flows remain green | PASS | Automatic checks below pass. |

## Automatic Checks

- `uv run pytest -v`: PASS (`448 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS
- Summary-only selected-facts provenance scenario: PASS (covered by executed test suite)
- Cross-ledger cache isolation scenario: PASS (covered by executed test suite)
- Blind-hiring provider metadata adversarial reproduction: FAIL
  (`question_intent`, `competency_target`, and `missing_info.message` returned identity text)
- Blind-hiring metric-only identity adversarial reproduction: FAIL
  (identity-bearing metric reached `fact_ledger` and provider input)

## Changes Outside Plan

No unrelated implementation scope expansion identified. Amendment v2 and advisor
`step-001.md` are authorized escalation artifacts. The hook-owned `status.txt=escalated`
working-tree state and untracked `.read-counter` files are excluded from implementation
findings.

---

## RESOLVED

### Issue Classification
- ISSUE-8: APPLY
- ISSUE-9: APPLY

### Applied

RESOLVED: ISSUE-8 — Blind-hiring advisory metadata surfaces screened before response serialization
- `scripts/dashboard.py` — In `api_studio_application_preview` LLM path: extract `_question_intent` and `_competency_target` from advisory before `if _blind:` block; screen both with `_IDENTITY_RE`; replace flagged values with server-owned safe wording. Screen each `missing_info[].message`; replace flagged messages with `"Content withheld under blind-hiring policy."` while preserving the original `code` for traceability. Emit `BLIND_HIRING_ADVISORY_REDACTED` in `missing_info` when any advisory field was redacted.
- `tests/test_cycle21.py` — Added `test_blind_hiring_question_intent_identity_withheld`, `test_blind_hiring_competency_target_identity_withheld`, `test_blind_hiring_missing_info_message_identity_withheld`.

RESOLVED: ISSUE-9 — Blind-hiring fact ledger screens metrics and evidence, not only title/summary
- `scripts/dashboard.py` — Changed `_build_fact_ledger` signature from `-> tuple[list[dict], bool]` to `-> tuple[list[dict], bool, bool]` returning `(ledger, card_excluded, field_redacted)`. Added `_IDENTITY_RE` check for each metric and evidence URL entry when `blind_hiring=True`; flagged entries are skipped and `field_redacted=True` set. Updated `_mock_application_preview` to unpack 3-tuple and derive `identity_flagged = card_excluded or field_redacted`. Updated `api_studio_application_preview` to use `_card_excluded` (not `field_redacted`) for LLM skip; added `BLIND_HIRING_PERSONAL_IDENTIFIERS` to LLM path response when `_field_redacted`. Updated `BLIND_HIRING_PERSONAL_IDENTIFIERS` message to say "Card content" (not "Card title or summary") to accurately reflect field-level exclusion.
- `tests/test_cycle21.py` — Added `_IDENTITY_METRIC_MDX`, `_IDENTITY_EVIDENCE_MDX` fixtures and four tests: `test_blind_hiring_metric_identity_excluded_from_ledger_mock`, `test_blind_hiring_metric_identity_excluded_from_llm_input`, `test_blind_hiring_evidence_identity_excluded_from_ledger_mock`, `test_blind_hiring_evidence_identity_excluded_from_llm_input`.

자동 체크:
- `uv run pytest -v`: ✅ 455 passed (448 → +7 new ISSUE-8/9 tests)
- `uv run ruff check scripts tests`: ✅
- `uv run ruff format --check scripts tests`: ✅
- `uv run pcli validate`: ✅
- `uv run pcli build resume --dry-run`: ✅
- `uv run pcli build portfolio --dry-run`: ✅
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: ✅
- Blind-hiring advisory adversarial reproduction (question_intent, competency_target, missing_info.message): ✅ PASS
- Blind-hiring metric-only identity adversarial reproduction: ✅ PASS
