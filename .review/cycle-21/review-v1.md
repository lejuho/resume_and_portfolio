# Codex Review v1

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] LLM preview trusts unsupported personal claims and unselected cards
- Location: `scripts/llm.py:713-843`, `scripts/dashboard.py:850-868`
- Analysis: `application_preview_llm()` accepts `personal_facts`, `selected_cards`, and
  `answer_draft` from either the provider response or cache and returns them unchanged. The
  JSON schema verifies response shape only; it does not prove that facts or selected IDs came
  from the requested live cards. A cached response containing `Metric: increased revenue
  999%`, `Role: CEO`, and `selected_cards=[{"id":"not-selected", ...}]` is returned intact
  for a request whose only card is `auth-service`.
- Impact: The core source-of-truth boundary is broken on the live path. The application draft
  can present invented personal achievements or silently substitute evidence outside the
  user's approved card selection, violating the Sprint Contract and D-009.
- Fix direction: Build authoritative selected-card metadata and extractable personal facts
  server-side from the requested cards. Do not trust LLM/cache values for provenance fields;
  validate or replace them, and reject/fallback on unsupported card IDs or claims. Add a
  regression test using an adversarial provider/cache response with fabricated facts and an
  unselected ID.

### ISSUE-2 [MEDIUM] Blind-hiring mode emits identity/background content in deterministic output
- Location: `scripts/dashboard.py:709-803`
- Analysis: When `blind_hiring=true`, the mock path adds only a generic
  `BLIND_HIRING_REVIEW` prompt. It still copies every selected card title and summary into
  `personal_facts` and the answer. For example, a card titled `Seoul National University
  Graduate` with summary `Born in Busan; led an analytics migration.` appears verbatim in the
  blind-hiring preview.
- Impact: The passing criterion that deterministic output prevent unnecessary
  identity/background claims is not met. A user selecting blind-hiring may submit precisely
  the information the control is meant to avoid.
- Fix direction: Implement a conservative deterministic redaction/exclusion rule for
  identity/background material, or block generation and request user editing when such text
  is present. Cover it with explicit identity/background fixture tests.

### ISSUE-3 [MEDIUM] Safe fallback transparency is incomplete and malformed responses are misclassified
- Location: `scripts/dashboard.py:602-620`, `scripts/dashboard.py:855-867`,
  `scripts/static/studio.js:120-160`, `scripts/static/studio.js:423-436`,
  `scripts/templates/studio.html:153`
- Analysis: The existing raw-capture refine endpoint now returns `draft.fallback_reason`, but
  `renderPreview()` only displays `Source: Mock` and never exposes the reason. Separately,
  `_classify_exc(LLMError("Malformed application_preview response"))` resolves to
  `provider_error`, not the planned `malformed_response`. The application panel renders a
  fallback notice, but it cannot provide the required malformed-response reason.
- Impact: The user still cannot tell whether normal Studio generation used mock because of a
  quota/auth/parse problem, and one explicitly promised safe reason is not implemented.
- Fix direction: Render the safe fallback reason for the existing refine panel as well as the
  application panel, classify malformed structured responses distinctly, and add endpoint
  plus frontend-hook tests for both flows.

### ISSUE-4 [MEDIUM] Application review UI hides selection rationale and assumptions
- Location: `scripts/static/studio.js:379-437`, `scripts/templates/studio.html:210-229`
- Analysis: The endpoint returns `selected_cards[].selection_reason` and `assumptions`, but
  the new panel renders only personal facts, target context, missing information, and the
  drafted answer. In particular, a truncation assumption produced by the mock path is never
  visible in the browser.
- Impact: The human-review stage cannot inspect why cards were chosen or which qualifications
  need confirmation before copying an application answer, despite those fields being part of
  the public response contract.
- Fix direction: Add visible selected-card/rationale and assumptions blocks to the panel and
  test their render hooks.

### ISSUE-5 [LOW] Required specification and acceptance updates are missing
- Location: `.review/cycle-21/plan.md:167-169`, `requirements-dashboard.md:3`,
  `docs/acceptance-studio.md:3`, `docs/test-cases.md:185-201`
- Analysis: The implementation commit changes code and tests, but does not update any of the
  three documents named in Key Changes. Requirements and acceptance still describe the
  application-writing behavior as future/planned rather than the implemented endpoint and
  fallback behavior.
- Impact: The product trace and manual acceptance record no longer describe the user-facing
  feature being implemented in this cycle.
- Fix direction: Update the requirement status/API surface, promote or map the applicable
  planned test cases, and add application-writing/fallback manual acceptance steps.

## Sprint Contract Check

| Contract item | Result | Evidence |
| --- | --- | --- |
| Separate application-writing preview in `/studio` | PASS | Template and JS hooks added. |
| Deterministic cover letter and answer from selected live cards/context | PARTIAL | Endpoint exists; blind-hiring deterministic output fails ISSUE-2. |
| Personal facts only from selected cards and visibly separated context | FAIL | LLM path fails ISSUE-1. |
| Question/competency interpretation and character compliance | PASS | Response fields and focused tests present. |
| Blind-hiring prevention in deterministic output | FAIL | ISSUE-2. |
| Method-grounded LLM flow with visible safe fallback reasons | FAIL | ISSUE-3. |
| Existing flows do not regress | PASS | Automated regression checks pass. |
| Application previews are not persisted | PASS | Route is preview-only and tests cover no card creation. |

## Automatic Checks

- `uv run pytest -v`: PASS (`426 passed`, 7 existing `datetime.utcnow()` deprecation warnings)
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS (existing warning: card `test` has no evidence)
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS
- `uv run python scripts/evaluate_studio_grounding.py --dry-run`: PASS

## Changes Outside Plan

No unintended implementation scope expansion identified. Untracked `.read-counter` files were
present and excluded from review changes.
