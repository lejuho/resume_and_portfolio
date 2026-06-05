# Post-v1 Dashboard Requirements

Status: implemented baseline through Cycle 30; Cycle 31 quality/spec audit complete
Last reviewed: 2026-06-05 (Cycle 31 quality-spec audit)
Owner: solo local user
Related:

- `requirements.md` — CLI v1 requirements
- `docs/design-system-studio.md` — Career Studio design system
- `docs/test-cases.md` — product test case specification
- `.review/midpoint-quality-audit/report-v1.md` — midpoint quality audit
- `docs/research/career-output-methodology.md` — output-track rubric and evidence matrix
- `docs/research/consultant-workflow-model.md` — AI/human workflow boundary
- `docs/research/llm-harness-evaluation.md` — prompt and token evaluation

## 1. Purpose

The dashboard layer exists to make the card-based resume and portfolio builder usable as a lightweight personal career workspace.

The desired service is:

> A personal career-memory system where the user can insert and manage career material in many forms, then automatically generate resumes and portfolios from selected history.

The dashboard should reduce complexity by keeping one canonical data source:

```text
raw career material -> refined career card -> resume / portfolio / other outputs
```

The user should not need to repeatedly rewrite the same experience for each output format.

## 2. Product Surfaces

The product has three surfaces with different jobs.

### 2.1 Admin Dashboard

Route:

```text
/dashboard
```

Current role:

- structured card inspection
- exact field editing
- filtering and selection
- build console for resume/portfolio
- validation-oriented source management

This surface may feel more database-like. That is acceptable because it is the precision/admin surface.

### 2.2 Career Studio

Route:

```text
/studio
```

Intended role:

- loose capture of raw activity material
- AI-assisted refinement
- output-targeted preview
- human review
- save as canonical card
- connect to resume/portfolio generation

Career Studio should be the lighter, creation-first experience. It should feel closer to Gamma + LinkedIn + resume builder than to a database admin tool.

### 2.3 Workspace

Route:

```text
/workspace
```

Implemented role (Cycles 27–30):

- live card evidence selection for application writing
- target context entry (organization, role, question, competency, job description)
- client-side deterministic fit signal (keyword overlap between target text and selected cards)
- application writing preview generation (reuses `/api/studio/application-preview`)
- no card creation, mutation, or persistence

Design reference: `docs/design-system-workspace.md`

The Workspace is a parallel experimental surface. It does not replace `/studio`; both routes
remain independently navigable. The Workspace's current fit-signal behavior is deterministic
client-side keyword matching only; LLM-based theme extraction, set-coverage matching, and
recommendation are future capabilities documented in `docs/design-system-workspace.md §8`.

## 3. Core Principles

### 3.1 One Source Of Truth

All durable activity data must eventually become canonical local card files:

```text
cards/<YYYY-MM>-<id>.mdx
```

The dashboard may present a lighter interface, but it should not create a second durable data model.

### 3.2 Loose Input, Structured Output

Users may provide raw input in many forms:

- freeform text
- project notes
- hackathon recap
- talk/writing notes
- links
- repo URLs
- image or asset references
- metrics
- rough reflections

The system should help transform this material into structured cards and output-specific narratives.

### 3.3 AI Refines, Human Approves

AI may:

- classify activity type
- propose a title
- extract period/date hints
- suggest tags
- suggest metrics
- extract evidence links
- write resume bullets
- write portfolio narrative blocks
- identify missing information

AI must not silently write or overwrite canonical card files.

Default flow:

```text
raw input -> AI draft -> human review/edit -> save card -> generate output
```

### 3.4 Output Intent Matters

The system should transform the same activity differently depending on target output.

Resume output should emphasize:

- concise bullet points
- action/result phrasing
- measurable outcomes
- role clarity
- technology and domain relevance

Portfolio output should emphasize:

- problem recognition
- problem definition/framing
- approach
- decisions and tradeoffs
- outcome
- insight

### 3.5 Local-Only, Solo Use

The dashboard is a local-first solo tool.

Assumptions:

- no multi-user support
- no authentication requirement for local default use
- no cloud sync
- no real-time collaboration
- no server deployment requirement

The default host should remain local/private.

## 4. Current Confirmed Functionality

The existing dashboard implementation already supports:

- local Flask dashboard startup through `uv run pcli dashboard`
- card list display
- type/status/tag/search filtering
- selected-card workflow
- resume/portfolio dry-run from selected cards
- resume/portfolio build from selected cards
- command/output/raw-log result display
- copyable command and output path
- new draft card creation
- existing card editing
- structured editing for:
  - tags
  - metrics
  - evidence
  - visuals
  - markdown body/narrative
- card write safety checks:
  - duplicate IDs rejected
  - ID is immutable in edit flow
  - invalid schema edits rejected
  - invalid visual paths rejected
  - absolute visual paths rejected
  - traversal visual paths rejected
  - invalid edits leave original file unchanged

Career Studio implementation through Cycle 19 also supports:

- separate `/studio` capture and preview surface
- deterministic mock refinement when no supported configured provider is available
- optional LLM-backed refinement with `refine_source` shown in the UI
- consultant-oriented draft fields for portfolio narrative
- editable preview before saving a new `draft` card
- post-save handoff to existing build/dashboard workflows
- provider resolution for `anthropic` and `google`
- generic `AI_API_KEY` alias plus provider-specific key variables
- configuration-only `/api/studio/ai-status` response that does not claim live connectivity
- explicit, user-triggered `/api/studio/ai-check` live connection verification
- Google Gemini default model `gemini-2.5-flash` when `AI_PROVIDER=google`

This surface is useful, but its current feel is admin-heavy and should not be the primary creative capture UX.

## 5. Career Studio Requirements

### 5.1 Studio Entry

The user must be able to open a separate Studio route:

```text
uv run pcli dashboard
http://127.0.0.1:<port>/studio
```

The existing `/dashboard` route must continue to work.

### 5.2 Raw Capture

Studio must provide a large, low-friction input area for raw career material.

The input should support at minimum:

- freeform text
- pasted URLs
- rough bullet notes

The first Studio cycle does not need full file upload or rich embeds.

### 5.3 Output Intent Selection

Studio must let the user choose the intended transformation target.

Initial options:

- Resume
- Portfolio
- Both

The selected intent controls what the AI draft emphasizes.

### 5.4 AI Draft Generation

Studio should generate a structured draft from raw input.

The draft should include:

- proposed card title
- proposed type
- date or date uncertainty
- resume bullet
- portfolio narrative
- tags
- metrics
- evidence candidates
- missing information prompts

The first implementation may use a fake/mock client if live LLM integration is not ready for the UI.

### 5.5 Preview Before Save

Studio must show a reviewable draft before saving.

The preview must make clear:

- what was inferred
- what is missing
- what will be saved
- what is resume-specific
- what is portfolio-specific

### 5.6 Save As Draft Card

The user must explicitly approve saving.

Save behavior:

- creates a new canonical card in the current Studio implementation
- defaults new cards to `draft`
- must pass card validation
- must not silently overwrite an existing card
- must preserve existing write-safety rules

Updating an existing card from Studio remains out of scope until explicitly designed; exact
editing remains available in `/dashboard`.

### 5.7 Output Generation

Studio should connect the saved/selected card to existing output generation.

Initial acceptable behavior:

- after save, offer "build resume", "build portfolio", or "open in dashboard"
- reuse existing CLI/dashboard build machinery

Studio does not need a separate renderer.

### 5.8 Current Studio API Surface

Implemented local API endpoints:

| Endpoint | Purpose | Key behavior |
|---|---|---|
| `GET /api/studio/ai-status` | display configuration state | Reports configured/mock mode without making a live request or exposing keys. |
| `POST /api/studio/ai-check` | optional connection test | Makes a minimal provider request only after user action and returns safe error categories. |
| `POST /api/studio/refine` | draft generation | Uses supported configured LLM when possible and otherwise returns deterministic mock output. |
| `POST /api/studio/save` | canonical persistence | Creates a new draft card after explicit action; raw pasted text is not saved by default. |

## 6. Admin Dashboard Requirements

The admin dashboard remains the exact-editing and build console.

It must continue to support:

- list cards
- filter/search
- select cards
- build resume/portfolio
- create draft card
- edit card fields
- reject invalid edits
- avoid source mutations during build actions

Admin dashboard may remain denser and more structured than Studio.

## 7. Data And Validation Requirements

### 7.1 Canonical Storage

Durable card data must be stored as MDX under `cards/`.

### 7.2 Write Scope

Dashboard write paths may write only intended card files unless a future requirement explicitly adds asset upload or preset editing.

### 7.3 ID Policy

Card IDs are immutable after creation.

Rename/move is out of scope until explicitly designed.

### 7.4 Visual Path Policy

Visual references saved from the dashboard must be:

- relative
- repo-contained
- existing at save time

Preferred location:

```text
assets/
```

Absolute paths and traversal paths must be rejected.

### 7.5 Invalid Save Policy

Invalid saves must:

- return a clear error
- leave the original card unchanged
- not partially write invalid MDX

## 8. AI Requirements

### 8.1 Optional But Central To Studio UX

LLM/API integration remains optional at the project level, but Studio's intended UX depends on AI refinement.

When an API key is absent, Studio should still be testable with:

- fake client
- mock response
- local deterministic demo response

Supported provider configuration as implemented:

| Provider | `AI_PROVIDER` | Provider-specific key | Default model |
|---|---|---|---|
| Anthropic | `anthropic` or unset | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| Google Gemini | `google` | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | `gemini-2.5-flash` |

`AI_API_KEY` may act as a fallback alias. Keys must remain server-side and must never be
included in status, error, cache, or saved card data.

### 8.2 Non-Mutation

AI output must be preview-only until the user explicitly saves.

### 8.3 Missing Information

AI should not pretend uncertain data is known.

It should surface missing prompts such as:

- date unclear
- metric missing
- evidence link missing
- visibility unclear
- role unclear

### 8.4 Grounded Drafting Quality

Research basis: `docs/research/career-output-methodology.md` and
`docs/research/consultant-workflow-model.md`.

For future grounded refinement, generated material must distinguish:

- facts directly supported by the raw source;
- assumptions or interpretations requiring user confirmation;
- missing information that would improve credibility;
- resume-specific and portfolio-specific drafts.

Normative safety requirements:

- The AI must not invent a date, metric, technology, evidence link, personal role, or
  outcome that is absent from the source input.
- A team result may not be claimed as individual ownership unless supported by input.
- Uncertainty must be presented for human review rather than silently incorporated into a
  saved claim.
- Refined output remains preview-only until explicit save.

### 8.5 Output Quality By Intent

Two initial reader tracks guide quality evaluation:

| Track | Resume emphasis | Portfolio emphasis |
|---|---|---|
| K - Korean formal application | concise, formal, verifiable job-relevant statement | optional supporting project detail only when applicable to the application |
| G - Global tech/Web3 builder | verified contribution and relevant technical result | problem, framing, approach/decision, outcome/evidence, and insight |

These tracks inform future presets and evaluation rubrics; they do not change card storage.

### 8.6 Application Writing Outputs (Implemented through Cycle 26)

**Status (Cycles 21–26 implemented):** The application writing harness, UX refinements, and
export/packet features described below are live. See D-009 (Cycle 21), D-010 (Cycles 22–23),
D-011 (Cycle 25), and D-012 (Cycle 26) for decision records.

Studio's output intent model extends with application writing:

- `cover_letter` / 자기소개서
- `application_answer` / supplied-question response

These outputs use two separately governed evidence sources:

| Source layer | Contains | Claim policy |
|---|---|---|
| Personal fact source | approved career cards and their evidence | Personal experience, role, result, metric, and skill claims must be grounded here. |
| Target context source | user-provided job description, organization context, question, character limit, and evaluation competency | Organization/role fit and question-response framing must be grounded here. |

Application writing differs from resume and portfolio generation:

| Output | Primary transformation |
|---|---|
| Resume | compress verified evidence for rapid screening |
| Portfolio | explain selected evidence through problem, decision, outcome, and insight |
| Cover letter / 자기소개서 | connect selected personal evidence to a specific role or organization and explain contribution/motivation |
| Application answer | answer one evaluation question using the best-supported episode under its length and competency constraints |

Future application-writing preview must expose:

- interpreted question intent or evaluated competency;
- selected card IDs and the reason each was selected;
- personal facts used from cards;
- supplied target-context statements used;
- assumptions and missing information;
- draft answer and character-count compliance.

It must not generate personal facts outside cards or invent organization-specific motivation
that was not supplied or explicitly confirmed by the user.

### 8.7 Efficiency And Evaluation

- Prompt-harness changes must be compared on factual grounding, parse reliability, output
  usability, latency, and input/output token counts.
- For Google Gemini evaluation, token measurement should use provider response usage
  metadata and structured output capability where adopted.
- Context caching must not be added merely by assumption; it should be used only when
  measured common prompt context is large and repeated enough to justify it.

## 9. Design Requirements

Studio should follow `docs/design-system-studio.md`.

Required design direction:

- light creation-first workspace
- large capture surface
- output intent controls
- generated preview blocks
- compact memory/output rails
- no dense table as first experience

The admin dashboard may keep its current utilitarian style.

## 10. Out Of Scope

For the next Studio cycle, these remain out of scope:

- cloud sync
- authentication
- multi-user collaboration
- GitHub auto-ingestion
- drag-and-drop asset upload
- automatic AI writes without review
- Git commit/push from dashboard
- full rich markdown editor
- public hosted web app

## 11. Acceptance Criteria

### 11.1 Studio MVP

- User can open `/studio`.
- User can paste messy activity text into a large input.
- User can choose Resume / Portfolio / Both.
- User can generate a structured draft preview.
- Preview includes resume bullet when resume intent is selected.
- Preview includes portfolio narrative blocks when portfolio intent is selected.
- Preview shows missing information prompts.
- User can save reviewed draft as a card.
- Saved card passes `uv run pcli validate`.
- Existing `/dashboard` still works.

### 11.2 Admin Dashboard Regression

- `/dashboard` opens.
- Card list/filter/select still works.
- Resume/portfolio dry-run still works.
- Resume/portfolio build action still returns structured result.
- Invalid card edits are rejected.
- Build actions do not mutate card files.

## 12. Historical Cycle 11 Decisions

These decisions are fixed for the first Studio implementation cycle.

### D-001: Studio AI fallback behavior

If no configured supported AI provider is available, `/studio` must use a deterministic
demo/mock refinement path.

Rationale:

- keeps UI development testable
- avoids making the first Studio cycle dependent on live API configuration
- preserves the review-before-save workflow

Updated by Cycles 17-19: a configured provider is resolved through `AI_PROVIDER` and its
server-side key; provider configuration and live connection verification are distinct states.

### D-002: First Studio save behavior

The first Studio MVP must create new draft cards only.

Updating an existing selected card from Studio is out of scope for Cycle 11. Existing card editing remains available in `/dashboard`.

### D-003: Raw input persistence

Studio must save refined narrative into the canonical card body.

Raw pasted input should not be stored in the canonical card by default. A future cycle may add an explicit "include raw notes" option or a separate source-memory store.

### D-004: Visual input in Studio MVP

Studio MVP should not implement image upload or asset picking.

Visual input is out of scope for Cycle 11 unless represented as plain text in the raw input and surfaced only as a missing-info prompt. Asset path editing remains available in `/dashboard`.

### D-005: Route naming

The light creation experience route is:

```text
/studio
```

Rationale:

- covers capture, refinement, preview, and output preparation
- distinct from the existing admin `/dashboard`

## 13. Post-Cycle 19 Decisions

### D-006: Provider-neutral Studio configuration

Studio must not assume Anthropic as the only live provider. Provider configuration is selected
server-side and currently supports Anthropic and Google Gemini.

### D-007: Configuration is not connectivity

The lightweight status indicator reports whether configuration appears present. A live
connection request is user-triggered separately and may fail because of authentication, quota,
rate limiting, networking, or provider errors.

### D-008: Next harness direction

Cycle 20 should implement grounded preview behavior before expanding generative polish:
source facts, assumptions, meaningful follow-up questions, and intent-specific drafts should
be inspectable before save. The chosen prompt strategy must be supported by the research
evaluation document rather than assumed.

### D-009: Application writing follows grounded preview

After Cycle 20 verifies the grounded preview contract, the next feature cycle should add
application-writing harness capability for 자기소개서 and supplied-question answers.

It must treat cards as the only source for personal factual claims and treat user-supplied
job/organization/question context as a separate source for tailoring. Resume and portfolio
generation remain separate transformations rather than being reused as generic long-form prose.

**Status (Cycle 21 implemented — Escalation Amendment v1 applied):**
`POST /api/studio/application-preview` is live with a verified-draft trust model.

- Accepts `output_type` (cover_letter | application_answer), `card_ids` (live cards only),
  and `target_context` (organization, role, job_description, question, competency,
  character_limit, blind_hiring).
- Server builds a `fact_ledger` from selected cards before any provider call; each entry
  carries a stable ID (F1, F2…), kind (activity | summary | metric | evidence), text, and
  source_card_id. In blind-hiring mode the provider receives sanitized ledger entries with
  opaque `source_card_id` references (`C1`, `C2`…) and identity-screened text; in non-blind
  mode the provider receives full ledger text and canonical card IDs.
- Provider returns advisory output only: `selected_fact_ids`, `question_intent`,
  `competency_target`, `missing_info`, `ai_guidance`. Provider prose cannot enter `answer_draft`.
- `answer_draft` is server-composed from validated ledger activity facts and submitted
  `target_context`; it carries `draft_provenance=server_composed`. `selected_facts` lists the
  exact ledger IDs used, including expanded activity facts for any selected card.
- `ai_guidance` is non-copyable advisory text shown in a separate UI section; under
  `blind_hiring=true`, identity/background guidance is withheld and
  `BLIND_HIRING_GUIDANCE_REDACTED` is emitted.
- Blind-hiring unified projection (Amendment v3): `_build_safe_projection` screens each card
  field (title, summary, metric, evidence) independently against identity/background regex.
  Flagged fields are excluded; clean fields on the same card are retained. Identity-only card
  titles use a safe display label (`Evidence C1`); canonical card IDs are replaced with opaque
  references (`C1`, `C2`…) in all provider payloads and rendered preview fields.
  If at least one usable field survives, preview generation continues with
  `BLIND_HIRING_PERSONAL_IDENTIFIERS` in `missing_info`. If no usable field remains across all
  selected cards, the endpoint returns HTTP 422 before any provider call.
  Provider advisory is sanitized via `_sanitize_advisory` covering `question_intent`,
  `competency_target`, `missing_info[].message`, and `ai_guidance[]`. Identity-bearing
  `competency` from `target_context` is not asserted as an applicant fact in `answer_draft`.
- Safe fallback reasons: `not_configured`, `quota_or_rate_limit`, `auth_failed`,
  `network_error`, `malformed_response`, `provider_error`.
- Application previews are not persisted as canonical cards.

## 14. Post-Cycle 21 Decisions

### D-010: Application Writing UX Improvements (Cycles 22–23)

Cycles 22 and 23 improved the Application Writing UX without changing generation policy.

- Cycle 22 added Studio UI contract smoke tests to catch frontend/backend response-shape
  mismatches (e.g. the Cycle 21 `/api/cards` array-vs-object regression).
- Cycle 23 improved Application Writing UX: richer live-card selector metadata, clearer
  empty/error states, and sharper "Verified Draft" vs. "AI Guidance" labeling. Copy button
  post-reset label consistency was confirmed as a separate sub-issue and fixed.
- Neither cycle changed generation policy, provider behavior, or card persistence.

### D-011: Export Without Persistence (Cycle 25)

Application Writing export is browser-only. A plain-text handoff packet is assembled
client-side from the most recent preview response and offered as a file download or clipboard
fallback. No new card is created and no new backend endpoint is added. The copy/export reset
helper `_resetAppHandoffState()` ensures stale state is cleared on failed regeneration.

The packet contains: output-type-specific title, target context used, verified draft, evidence
summary (using safe display labels in blind-hiring mode), and AI guidance clearly labeled
"ADVISORY".

### D-012: Packet Quality (Cycle 26)

The exported packet format was improved:

- Output-type-specific title (`_packetTitle`).
- Draft Metadata section with character count, character limit, and provenance.
- Non-string safety coercion (`_packetSafeText`) for all evidence fields.

### D-013: Workspace Route Shell (Cycle 27)

A parallel `/workspace` route was added. It does not replace `/studio`. The route renders
`workspace.html` and exposes the two-pane layout shell (evidence cards left, target/output
right). Both `/studio` and `/workspace` remain independently accessible from `/dashboard`.

### D-014: Workspace Design Tokens (Cycle 28)

All *repeated* Workspace color, radius, and border values are defined as CSS custom properties
in a `:root` block. The token registry is maintained in `docs/design-system-workspace.md`.
Font weights are limited to 400/500; `text-transform: uppercase` is prohibited. The source
test `test_workspace_html_no_raw_rgba_accent_outside_root` enforces that raw accent color
values appear only inside the `:root` definition.

One documented exception: the Generate button foreground uses `color: #fff` — a single-use
value, not a repeated role. The custom focus ring for that button is also absent; both are
tracked in DEBT-006 of the Cycle 31 audit report.

### D-015: Workspace Dark Mode and Polish (Cycle 29)

Workspace supports OS-level dark mode via `@media (prefers-color-scheme: dark)` and a
`localStorage`-backed manual theme toggle (`data-ws-theme` attribute on `<html>`). The
manual preference takes priority over OS preference. Card hover, selected, and focus-visible
states are token-driven in both modes.

### D-016: Workspace Fit Signals (Cycle 30)

The Workspace coverage panel computes a deterministic client-side fit percentage:

```
pct = |target_tokens ∩ card_tokens| / |target_tokens| × 100
```

Target tokens: lowercased, split on non-word boundaries, filtered by stop-word set (including
TLDs), length > 2.
Card tokens: same tokenization applied to title + summary + type + metrics + evidence
URL/text across all selected live cards.

The panel updates on card selection change and on input to any target field. Up to 6 matched
terms are displayed. The fit signal is advisory only and does not alter provider payload or
generated drafts. Future LLM-based theme extraction (S1) and set-coverage matching (S2) are
not yet implemented; see `docs/design-system-workspace.md §8`.

### D-017: Workspace Card Disclosure (Cycle 30 / Concurrent)

Card summaries are clamped to 2 lines via `-webkit-line-clamp: 2`. A "Show full summary"
disclosure button (`ws-card-more`) is revealed only when rendered summary height exceeds the
clamp threshold. The button calls `event.stopPropagation()` to prevent toggling card
selection. Expanding adds `ws-card-context-expanded` class; collapsing removes it.
