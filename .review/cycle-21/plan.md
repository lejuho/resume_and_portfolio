# Cycle 21 Plan: Application Writing Harness Preview

Branch: `feature/cycle-21-application-writing-harness`

## Summary

Cycle 20 has verified the grounded Resume / Portfolio / Both preview contract:
supported facts, assumptions, and missing information remain inspectable before save, and
mock or LLM paths do not persist invented dates.

Cycle 21 adds the next distinct transformation required by
`requirements-dashboard.md` section 8.6 and D-009:

```text
approved career cards + supplied application context
  -> grounded cover-letter or question-answer preview
  -> human review and copy/use outside canonical card storage
```

This is not another raw-material-to-card flow. Canonical cards remain the only personal
fact source; organization, role, job description, question, competency, length rule, and
blind-hiring instruction are target context supplied by the user for the current draft.

The cycle also makes existing and new LLM-to-mock fallback transparent by displaying a safe
fallback reason when an attempted provider call fails, including quota/rate-limit cases.

## Documentation Discovery And Allowed APIs

Sources read before planning:

- `requirements-dashboard.md` sections 8.4-8.7 and D-006-D-009: grounded fact boundary,
  target-context separation, output requirements, and provider status semantics.
- `docs/research/consultant-workflow-model.md` following-cycle recommendation: application
  writing requires selected cards, target context, question interpretation, selection reason,
  character-count compliance, and blind-hiring restrictions.
- `docs/test-cases.md` `PT-APP-001` through `PT-APP-006`: planned requirement cases to turn
  into executable coverage.
- `docs/acceptance-studio.md`: current Studio and provider/privacy manual flow structure.
- `scripts/dashboard.py`: existing Flask endpoints `/api/cards`, `/api/studio/refine`,
  `/api/studio/save`, `/api/studio/ai-check`, and safe mock fallback pattern.
- `scripts/llm.py`: `resolve_provider_config()`, `studio_refine_llm()`,
  `_GROUNDED_DRAFT_SCHEMA`, structured Google generation, and safe connection error codes.
- `scripts/templates/studio.html` and `scripts/static/studio.js`: current intent controls,
  preview rendering, grounding lists, and provider-source display.

Allowed implementation patterns:

- Add a dedicated Flask JSON endpoint alongside the existing Studio endpoints.
- Load selected cards through existing repository/card serialization patterns; do not parse
  MDX ad hoc in the application-writing handler.
- Add a separate grounded LLM prompt/schema/helper modeled on `studio_refine_llm()` and the
  existing Google structured-output configuration.
- Use the existing deterministic mock approach for offline/testable output.
- Reuse safe classified provider error values; never pass provider exception messages or keys
  to the browser.

Anti-pattern guards:

- Do not extend `/api/studio/save` to store cover letters or question answers as career cards.
- Do not send raw card files, unselected cards, or private key values to the frontend/provider.
- Do not treat organization claims or motivation as personal facts.
- Do not reuse resume/portfolio prose as an unstructured answer-generation shortcut.
- Do not add a second LLM call, retrieval layer, provider, renderer, or persistent application
  document store in this cycle.

## Input / Output Specification

### New Endpoint

`POST /api/studio/application-preview`

Request:

```json
{
  "output_type": "cover_letter | application_answer",
  "card_ids": ["approved-card-id"],
  "target_context": {
    "organization": "string",
    "role": "string",
    "job_description": "string",
    "question": "string",
    "competency": "string",
    "character_limit": 1000,
    "blind_hiring": true
  }
}
```

Rules:

- `card_ids` is required, must be non-empty, and may select only existing `live` cards in
  this MVP. Draft cards remain editable in the admin dashboard and must be marked live before
  being used as approved evidence.
- `output_type=cover_letter` requires at least one meaningful target field among
  `organization`, `role`, or `job_description`.
- `output_type=application_answer` requires `question`; `character_limit` is optional but,
  when supplied, must be an integer from `1` through `5000`.
- `blind_hiring` defaults to `false`; when true, generated output must exclude unnecessary
  personal-background identifiers and `missing_info` should warn if the target instruction
  needs user review.

Successful response:

```json
{
  "ok": true,
  "preview": {
    "output_type": "application_answer",
    "question_intent": "string",
    "competency_target": "string",
    "selected_cards": [
      { "id": "card-id", "title": "Title", "selection_reason": "string" }
    ],
    "personal_facts": ["fact derived only from selected cards"],
    "target_context_used": ["statement derived only from supplied target_context"],
    "assumptions": ["item requiring user confirmation"],
    "missing_info": [{ "code": "string", "message": "string" }],
    "answer_draft": "string",
    "character_count": 123,
    "character_limit": 1000,
    "within_limit": true,
    "refine_source": "mock | llm",
    "fallback_reason": null
  }
}
```

Behavior:

- `personal_facts` is derived from selected canonical cards only.
- `target_context_used` is derived from request context only.
- Generated drafts must not invent personal metrics, roles, evidence, organization facts, or
  motivation not supported by those two governed input layers.
- For `application_answer`, preview exposes interpreted question intent and character-count
  compliance. For `cover_letter`, `question_intent` may be empty while
  `competency_target`/fit focus is exposed when derivable.
- Output is preview-only in this cycle: no card mutation and no application-document save.

Validation failures:

- HTTP 400: invalid `output_type`, empty `card_ids`, missing required target context,
  invalid `character_limit`.
- HTTP 404: requested card ID not found.
- HTTP 422: selected card exists but is not `live`, or supplied input cannot safely produce
  an application preview.

### Existing Refine Endpoint Extended

`POST /api/studio/refine` remains backward compatible and may add:

```json
{
  "draft": {
    "refine_source": "mock",
    "fallback_reason": "quota_or_rate_limit | auth_failed | network_error | provider_error | malformed_response | not_configured | unsupported_provider | null"
  }
}
```

The new application endpoint returns the same safe `refine_source` and `fallback_reason`
semantics. `fallback_reason` is shown only as a safe user-facing explanation; raw provider
messages and secrets never leave the backend.

## Key Changes

- Documentation: update `requirements-dashboard.md`, `docs/test-cases.md`, and
  `docs/acceptance-studio.md` to mark Cycle 20 grounded behavior implemented, specify the new
  application-preview surface, and record safe fallback-reason visibility.
- Backend selection: extend `scripts/dashboard.py` with an application-preview endpoint and
  shared selected-live-card loading/validation for application evidence.
- Backend mock: add deterministic cover-letter and application-answer mock generation using
  selected card facts and supplied target context separately, including limit and blind-hiring
  handling.
- Backend LLM: extend `scripts/llm.py` with a method-grounded application-writing prompt and
  structured schema/helper for a single provider call; preserve Google structured output and
  existing provider configuration.
- Backend fallback transparency: classify safe LLM refinement failure reasons for both the
  existing refine endpoint and new application-preview endpoint without exposing raw errors.
- Frontend: extend `scripts/templates/studio.html` and `scripts/static/studio.js` with a
  distinct Application Writing panel containing live-card selection, output-type control,
  target-context inputs, preview blocks, character status, copy action, and safe fallback
  notice. Do not turn application drafts into the existing card-save interaction.
- Tests: add focused endpoint, mock, LLM/schema, provider-fallback, UI-hook, grounding,
  character-boundary, and regression tests.

## Sprint Contract

### Passing Criteria

- `/studio` retains raw career capture and additionally supports a visibly separate
  application-writing preview flow.
- The application flow can generate deterministic `cover_letter` and `application_answer`
  previews from selected existing `live` cards plus supplied target context.
- Personal facts are sourced only from selected cards; organization/question framing is sourced
  only from target context, and the preview shows those sources separately.
- Application-answer output exposes question/competency interpretation and character-count
  compliance for provided limits.
- Blind-hiring mode prevents unnecessary identity/background claims in deterministic output and
  instructs the LLM contract to do the same.
- Live LLM output uses a method-grounded structured one-shot contract; failures safely fall
  back to mock with a visible, non-secret `fallback_reason`.
- Existing raw capture, draft card save, dashboard, provider check, resume build, and portfolio
  build flows do not regress.
- Application previews are not persisted to canonical cards or a new storage subsystem.

### Automatic Checks

```bash
uv run pytest -v
uv run ruff check scripts tests
uv run ruff format --check scripts tests
uv run pcli validate
uv run pcli build resume --dry-run
uv run pcli build portfolio --dry-run
uv run python scripts/evaluate_studio_grounding.py --dry-run
```

### Test Cases

- Routing/UI: `/studio` contains separate application-writing hooks, live-card selector,
  output-type switch, target context fields, preview sections, count state, and copy action.
- Validation: reject invalid output type, empty selection, missing question for
  `application_answer`, invalid `character_limit` boundaries (`0`, `1`, `5000`, `5001`),
  missing card, and draft-only card selection.
- Mock output: `cover_letter` and `application_answer` preview fields are deterministic and
  keep `personal_facts` separate from `target_context_used`.
- Selection: multiple live cards return selected IDs/titles and evidence-based selection
  reasons without importing unselected-card facts.
- Grounding: adding target context may change fit framing but must not change personal facts;
  no unsupported organization motivation is emitted when organization/JD context is absent.
- Question flow: competency interpretation is exposed; response count and within-limit status
  are correct at length boundaries.
- Blind hiring: supplied restriction prevents or flags prohibited identity/background claims.
- Provider: Google structured schema is used for application preview; safe mock fallback shows
  `fallback_reason=quota_or_rate_limit`, `auth_failed`, malformed response, and not-configured
  cases without key leakage.
- Regression: current Resume / Portfolio / Both refine/save behavior and existing AI check
  tests remain green.

### Manual Acceptance

- Start `uv run pcli dashboard --port 5097` and open `/studio`.
- Confirm existing raw-memory capture remains usable and visually separate from Application
  Writing.
- Select one or more live cards, enter a Korean organization/role context, generate a
  자기소개서 preview, and confirm visible separation of card facts and target context.
- Enter an exact application question and character limit, generate an answer preview, and
  confirm question interpretation and character compliance.
- Run once without a configured provider and once, if quota permits, with Google enabled;
  confirm `Source: Mock` versus `Source: LLM`, and confirm a safe fallback reason is shown
  after a controlled provider failure.
- Confirm no new card is created by generating application-writing previews.

### Gas Limit

N/A

### Slither Pass

N/A

## Missing Edge Case Candidates

- One selected card includes personally identifying or confidential client detail while
  `blind_hiring=true`; the first pass may need a stronger field-level redaction policy.
- A character limit is defined in Korean characters while a later target interprets byte or
  whitespace-excluded length; this cycle uses Python/JavaScript character count only.
- A valid live card contains weak or irrelevant evidence for the exact question; deterministic
  selection can explain use or missing fit but cannot certify recruiter quality.

## Simpler Alternative

Add `cover_letter` and `application_answer` radio buttons to the existing raw-text refine
request and generate prose directly from pasted notes.

This is not selected because it would violate D-009: application claims must be grounded in
approved canonical cards, while target/job/question context must remain a separate governed
source rather than being blended into a new raw card draft.

## Assumptions

- Cycle 20 is merged to local `main` and provides the supported-facts/assumptions UI and
  structured Google prompt pattern to reuse.
- Existing cards with `status: live` represent approved evidence for this MVP; using draft
  cards in applications is deferred.
- Application-writing drafts are useful as reviewed/copyable previews before export or
  persistence is designed; DOCX/PDF submission rendering is out of scope.
- The endpoint processes only selected card content and user-supplied target context in memory;
  no application target context or generated prose is written by default.
- Safe fallback-reason visibility is included because the user has already encountered the
  distinction between configured AI, live connectivity, and mock fallback under quota failure.

## Review Guidance

### Enumeration Required

- Enumerate every application-writing path and confirm no generated application material is
  persisted as a canonical card:

```bash
rg -n "application-preview|cover_letter|application_answer|answer_draft|api_studio_save|_write_card_atomic|CardRepo|card_ids" scripts tests
```

Expected review targets: new endpoint, mock/LLM helper, Studio UI request/render flow, existing
save endpoint, and application tests.

- Enumerate personal-fact and target-context boundary handling:

```bash
rg -n "personal_facts|target_context_used|selected_cards|selection_reason|organization|job_description|question|competency|blind_hiring|character_limit" scripts tests
```

Expected result: selected card material is passed through a separately named field from
user-provided target context in both mock and LLM contracts.

- Enumerate fallback-reason and secret-handling paths:

```bash
rg -n "refine_source|fallback_reason|quota_or_rate_limit|auth_failed|malformed_response|api_key|except Exception|LLMError|_classify_exc" scripts tests
```

Expected result: existing refine and new application preview report only safe reasons; no raw
provider exception enters JSON or visible browser text.

### Verification Method

- Flask client/unit tests are sufficient for input validation, live-card selection, no-write
  behavior, deterministic mock shape, safe fallback-reason contract, and UI hooks.
- Schema/config mock tests are sufficient to assert that the Google structured-output call is
  requested, but not to prove live provider compatibility.
- A bounded live Google preview is optional when quota is available and must use non-sensitive
  cards/context; record it in `docs/acceptance-studio.md`.
- Factual and blind-hiring quality require scenario review against the separated
  `personal_facts` and `target_context_used` preview, not only schema assertions.

---

## Escalation Amendment v1: Verified Draft Composition

Status: User-approved after `review-v3.md` triggered Same-Issue Stagnation.

This amendment overrides any conflicting application-writing design above. The initial
approach incorrectly treated LLM-generated prose as copyable after partial post-generation
checks. Reviews v1-v3 demonstrated that deny-list and regex guards cannot establish that free
prose contains only approved career facts or respects blind-hiring restrictions.

### Revised Trust Model

```text
selected live cards
  -> server-owned fact ledger and blind-hiring redaction
  -> LLM may select fact IDs, interpret the question, and suggest missing information
  -> server validates returned IDs
  -> server composes the copyable answer_draft only from validated facts and target context
  -> UI shows verified draft separately from non-copyable AI guidance
```

- Canonical cards remain the only source of personal factual claims.
- Target context remains a separate user-supplied source for organization, role, question,
  competency, and job-description framing.
- LLM output is advisory unless it references server-authoritative IDs and is used through
  deterministic server composition.
- The server must not display or make copyable any free-form LLM prose as `answer_draft`.
- Regex/keyword detection may remain as defense-in-depth or a warning tool, but must not be
  the trust boundary for answer acceptance.

### Revised Input / Output Specification

The endpoint and request body remain unchanged:

`POST /api/studio/application-preview`

Successful preview retains `answer_draft` for UI compatibility, but its contract changes:

```json
{
  "ok": true,
  "preview": {
    "output_type": "application_answer",
    "fact_ledger": [
      {
        "id": "F1",
        "kind": "activity | summary | metric | evidence",
        "text": "server-owned approved text",
        "source_card_id": "card-id"
      }
    ],
    "selected_facts": ["F1"],
    "selected_cards": [
      {
        "id": "card-id",
        "display_title": "safe title or Evidence 1",
        "selection_reason": "server-derived safe rationale"
      }
    ],
    "target_context_used": ["server-built target context item"],
    "question_intent": "LLM or mock interpretation",
    "competency_target": "LLM or mock interpretation",
    "answer_draft": "server-composed copyable draft",
    "draft_provenance": "server_composed",
    "ai_guidance": ["non-copyable suggestion requiring user judgment"],
    "assumptions": ["item requiring user confirmation"],
    "missing_info": [],
    "character_count": 100,
    "character_limit": 1000,
    "within_limit": true,
    "refine_source": "llm | mock",
    "fallback_reason": null
  }
}
```

Required behavior:

- `fact_ledger` is created by the server from selected live cards, never accepted from LLM.
- The LLM may return `selected_fact_ids`; unknown IDs are discarded, and an unusable
  selection falls back to deterministic safe selection.
- `answer_draft` is composed by server-owned templates from selected ledger entries and
  submitted target context only. Provider prose cannot populate this field.
- `ai_guidance` is optional advisory text and must be visually labeled as not part of the
  verified/copyable answer.
- Character-limit enforcement applies to the server-composed `answer_draft`.
- Application previews remain in-memory only and are not saved as cards or documents.

### Blind-Hiring Policy

When `blind_hiring=true`, protection is applied before any LLM request and across every
visible output surface:

- Filter or anonymize identity/background-bearing card title and summary before constructing
  the fact ledger or provider prompt.
- Do not send excluded identity/background text to the provider.
- Do not render excluded text in `fact_ledger`, `selected_cards`, `selection_reason`,
  `answer_draft`, or `ai_guidance`.
- Render safe labels such as `Evidence 1` for selected cards whose original display title was
  excluded.
- Emit `BLIND_HIRING_PERSONAL_IDENTIFIERS` when content is excluded.
- If provider guidance contains excluded terms despite redacted input, discard that guidance
  and expose a safe confirmation warning; the verified draft remains server-composed.

### Revised Key Changes

- Backend fact ledger: factor a single server helper that loads selected card facts, creates
  stable fact IDs, and applies blind-hiring redaction before both mock and LLM paths.
- Backend LLM contract: replace LLM `answer_draft` generation with structured advisory output:
  selected fact IDs, question/competency interpretation, missing information, and optional
  guidance. Reject or ignore unknown fact IDs.
- Backend draft composition: replace `_has_ungrounded_claims()` as the acceptance mechanism
  with deterministic composition of `answer_draft` from validated ledger/context units.
- Frontend: label the copyable response as `Verified draft`; show `AI guidance` separately
  without routing it through the copy action. Render safe selected-card labels in
  blind-hiring mode.
- Documentation: update `requirements-dashboard.md`, `docs/test-cases.md`, and
  `docs/acceptance-studio.md` to describe server-composed drafts and advisory-only LLM text,
  superseding any statement that implies free LLM answer prose is accepted after filtering.

### Revised Sprint Contract

Passing criteria:

- A provider or cache response containing arbitrary free prose cannot place that prose into
  the copyable `answer_draft`.
- The copyable `answer_draft` is always marked `draft_provenance=server_composed` and can be
  traced to selected ledger facts plus submitted target context.
- Unknown or unselected LLM `selected_fact_ids` cannot influence the verified draft.
- Blind-hiring mode prevents excluded identity/background content from reaching the provider
  prompt or appearing anywhere in the returned/rendered preview.
- `ai_guidance`, when present, is separated from the copy action and cannot be mistaken for
  verified submission text.
- Existing fallback visibility, no-persistence behavior, dashboard, resume build, and
  portfolio build remain green.

Required tests:

- Adversarial provider result containing qualitative invention such as
  `I founded Fabricated Corp and led its global expansion.` does not appear in
  `answer_draft`; the verified draft is server-composed.
- Provider result returning unknown or unselected fact IDs is ignored or safely falls back.
- Identical approved ledger facts yield stable server-composed draft content in mock and LLM
  paths, apart from visible advisory/interpretation metadata.
- Blind-hiring fixture with education/background identifiers verifies they are absent from
  provider prompt, facts, selected-card display/rationale, answer draft, and guidance.
- UI test verifies copy action targets only verified draft and guidance is shown in a
  separate non-copyable section.
- Existing Cycle 21 endpoint validation, fallback, no-write, and application UI tests remain
  green, updated where the superseded response semantics require it.

### Revised Review Guidance

Cycle Reviewer must verify the trust boundary by searching for every code path that can assign
or render copyable answer text:

```bash
rg -n "answer_draft|draft_provenance|ai_guidance|selected_fact|fact_ledger|clipboard|copy" scripts tests
```

Expected result: `answer_draft` is composed from validated server values only. Provider or
cache payload fields must never be copied directly into the verified-draft field.

Review blind-hiring across all visible and transmitted surfaces:

```bash
rg -n "blind_hiring|IDENTITY|fact_ledger|selected_cards|selection_reason|answer_draft|ai_guidance|prompt" scripts tests
```

Expected result: redaction occurs before prompt construction and is reused for every rendered
field, rather than being patched independently after generation.

Mock shape or schema tests alone are insufficient for these revised safety criteria.
Adversarial route tests are required.
