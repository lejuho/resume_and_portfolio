# Post-v1 Dashboard Requirements

Status: draft for Cycle 11+
Owner: solo local user
Related:

- `requirements.md` — CLI v1 requirements
- `docs/design-system-studio.md` — Career Studio design system
- `docs/test-cases.md` — product test case specification
- `.review/midpoint-quality-audit/report-v1.md` — midpoint quality audit

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

The product has two dashboard surfaces with different jobs.

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

- creates or updates a canonical card
- defaults new cards to `draft`
- must pass card validation
- must not silently overwrite an existing card
- must preserve existing write-safety rules

### 5.7 Output Generation

Studio should connect the saved/selected card to existing output generation.

Initial acceptable behavior:

- after save, offer "build resume", "build portfolio", or "open in dashboard"
- reuse existing CLI/dashboard build machinery

Studio does not need a separate renderer.

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

## 12. Cycle 11 Decisions

These decisions are fixed for the first Studio implementation cycle.

### D-001: Studio AI fallback behavior

If no `ANTHROPIC_API_KEY` is available, `/studio` must use a deterministic demo/mock refinement path.

Rationale:

- keeps UI development testable
- avoids making the first Studio cycle dependent on live API configuration
- preserves the review-before-save workflow

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
