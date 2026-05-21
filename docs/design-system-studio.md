# Career Studio Design System

Status: draft
Audience: post-v1 dashboard / `/studio` implementation

## Product Positioning

Career Studio is a lighter, creation-first interface for turning messy personal career material into reusable career cards and generated outputs.

The current dashboard is an admin console for exact card inspection and editing. Career Studio should feel like a guided creative workspace:

- Gamma-like generation and preview flow
- LinkedIn-like career credibility and timeline context
- Resume-builder-like output targeting
- Single-source-of-truth simplicity through existing card files

The user should not feel like they are maintaining a database. They should feel like they are dropping raw career memory into a focused assistant that helps them turn it into resumes, portfolios, bios, and decks.

## Design Principles

### 1. Input Is Loose, Output Is Structured

Users can paste raw notes, links, project fragments, talk descriptions, screenshots, or rough reflections.

The system performs the structuring:

- title
- type
- period
- tags
- metrics
- evidence
- resume bullet
- portfolio narrative
- missing information prompts

The UI should expose structure only after the user asks the system to refine the raw input.

### 2. The Card Schema Is Internal

The canonical card schema remains valuable, but Studio should not lead with schema fields.

Preferred language:

- "Career Memory"
- "Draft"
- "Refine"
- "Output target"
- "Save as card"

Avoid leading with:

- "database"
- "frontmatter"
- "schema"
- "record"
- "CRUD"

### 3. Human Approves, AI Does Not Silently Commit

AI can suggest, rewrite, classify, and structure. It should not silently modify source cards.

Default flow:

```text
raw input -> AI draft -> human review -> save card -> generate output
```

### 4. Output Intent Drives the Shape

The same activity should become different material depending on the output target.

Resume mode:

- concise bullet
- action/result framing
- measurable outcomes
- role and technology clarity

Portfolio mode:

- problem recognition
- definition and framing
- approach
- decisions and tradeoffs
- outcome
- insight

Both mode:

- generate both surfaces from the same underlying activity
- show differences clearly

### 5. The Interface Should Feel Light

Avoid dense tables as the first experience.

Prefer:

- a large capture surface
- simple target controls
- generated preview blocks
- compact memory rail
- clear save/build actions

The existing `/dashboard` can keep the dense admin style.

## Benchmark References

| Reference | Borrow | Avoid |
|---|---|---|
| Gamma | generation-first flow, deck-like preview, light creative workspace | over-marketing the UI or hiding source data too much |
| LinkedIn | credible career chronology, recognizable role/activity framing | social feed noise and engagement UI |
| Rezi / Teal / Kickresume | resume targeting, bullet refinement, job-oriented feedback | ATS-heavy anxiety or form overload |
| Notion AI | raw note to structured summary | blank-page ambiguity |
| Read.cv / Polywork | portfolio-friendly activity cards | overly decorative profile page |

## Information Architecture

Studio should be a separate route from the admin dashboard:

```text
/dashboard   exact card table, admin editing, build console
/studio      raw capture, AI refine, draft preview, output intent
```

Recommended first-screen layout:

```text
Left rail: Career Memory
- recent cards
- drafts/live filter
- search
- source snippets

Center: Capture / Refine
- large raw input
- source chips
- intent switch
- refine button
- generated draft preview

Right rail: Output Targets
- Resume
- Portfolio
- LinkedIn summary
- Bio
- Deck narrative
```

Desktop-first is acceptable for the next cycle.

## Visual Language

### Overall Feel

Studio should feel calm, capable, and editorial. It should be softer than the current dark admin dashboard but still work-focused.

Target adjectives:

- light
- credible
- focused
- creative
- reviewable
- low-friction

Avoid:

- database admin
- analytics dashboard overload
- marketing landing page
- decorative gradient blobs
- playful toy-like UI

### Color

Recommended palette:

| Role | Color | Usage |
|---|---|---|
| Canvas | `#F7F7F4` | page background |
| Surface | `#FFFFFF` | capture and preview regions |
| Border | `#DAD7CF` | subtle separators |
| Text | `#1F2523` | primary text |
| Muted text | `#6B716D` | secondary labels |
| Primary | `#1F4E79` | main actions, selected output target |
| Accent | `#18A999` | AI/refine success accents, sparingly |
| Draft | `#B7791F` | draft status |
| Ready | `#287D3C` | saved/valid status |
| Risk | `#B42318` | validation errors |

Do not let the UI become a one-note blue product. Use blue as a trust/action color and green/mint only as an accent.

### Typography

Use system fonts unless the app already has a stronger reason to add a font dependency.

Suggested stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Guidelines:

- No viewport-scaled type.
- Letter spacing should generally be `0`.
- Use compact but readable labels.
- Large type is reserved for the primary capture prompt and generated output headings.
- Tables, if present, stay secondary.

### Shape And Density

- Card radius: 8px or less.
- Buttons: compact, predictable.
- Avoid cards inside cards.
- Use full-height panels or simple bordered regions instead of decorative nested containers.
- Keep the capture textarea visually generous.

## Core Components

### CaptureBox

Primary raw input surface.

Contains:

- large textarea
- optional pasted links
- source chips
- light placeholder examples

Placeholder tone:

```text
Paste a project note, talk recap, hackathon story, repo link, or messy career memory...
```

### SourceChip

Shows the kind of input the user provided.

Examples:

- Memo
- GitHub
- Link
- Image
- Talk
- Hackathon
- Role

### IntentSwitch

Segmented control:

- Resume
- Portfolio
- Both

The selected intent changes the generated preview emphasis.

### RefinePreview

Shows AI-produced structure before saving.

Sections:

- title
- detected type/date
- resume bullet
- portfolio narrative
- tags
- evidence
- missing info

### StoryBlock

Used inside portfolio preview.

Default blocks:

- Problem
- Framing
- Approach
- Decisions
- Outcome
- Insight

### OutputRail

Shows available outputs and readiness state.

Targets:

- Resume
- Portfolio
- LinkedIn summary
- Short bio
- Deck narrative

Each target can show:

- ready
- needs info
- not generated

### ConfidenceBadge

Shows whether a field is confident or needs human review.

Examples:

- confident
- inferred
- needs date
- needs metric
- needs link

### SaveDraftButton

Commits reviewed draft into canonical card storage.

Label options:

- Save as draft card
- Update card

Avoid:

- Commit
- Insert row
- Submit record

## AI Draft Shape

The AI result should be reviewable and explicit.

Example:

```text
Resume bullet
Built a Solana-based photocard RWA marketplace in a 5-hour hackathon sprint, using Metaplex Core and USDC settlement to test whether the registry itself could be the product.

Portfolio narrative
Problem:
K-pop photocards have strong collector demand but weak provenance and fragmented marketplace trust.

Approach:
Built a lightweight marketplace prototype where ownership registry and settlement flow became the core product.

Decision:
Used Metaplex Core for asset representation and focused on registry credibility over marketplace breadth.

Outcome:
Produced a working solo prototype within the hackathon window.

Insight:
For collectible RWAs, the trust registry can be more valuable than a traditional marketplace wrapper.

Missing info:
- Was there a demo link?
- Any judge/user feedback?
- Should this be public or private?
```

## Interaction Rules

- Refinement creates a draft preview, not a saved card.
- Save requires explicit user action.
- If required card fields are missing, show missing info rather than blocking the whole experience too early.
- If generated fields are uncertain, mark them as inferred.
- The user can edit generated text before saving.
- After saving, offer actions:
  - build resume
  - build portfolio
  - open in admin dashboard

## Relationship To Existing Dashboard

The current dashboard remains useful as an admin surface.

| Route | Role | Primary user action |
|---|---|---|
| `/dashboard` | structured admin console | inspect, filter, exact-edit, build |
| `/studio` | light creation workspace | capture, refine, review, save |

Do not remove the existing dashboard during Studio experiments.

## Accessibility And Responsiveness

Cycle 11 may be desktop-first, but should still preserve:

- readable contrast
- keyboard focus outlines
- labels tied to inputs
- no text overflow in buttons
- panels that scroll independently without hiding primary actions

## Cycle 11 MVP Scope Recommendation

Minimum viable Studio:

- `/studio` route
- soft-neutral visual shell
- large raw input
- intent switch: Resume / Portfolio / Both
- mock or fake-client AI refinement path
- generated draft preview
- missing info section
- save as draft card using existing safe card write path
- link back to `/dashboard`

Out of scope for first Studio cycle:

- image upload
- drag-and-drop asset management
- live collaborative editing
- full markdown editor
- Git commit/push actions
- automatic AI writes without review

## Acceptance Criteria For First Studio Cycle

- User can open `/studio`.
- User can paste messy activity text into a large input.
- User can choose output intent.
- User can generate a structured preview.
- Preview clearly separates resume bullet and portfolio narrative when relevant.
- Preview shows missing info prompts.
- User can save reviewed content as a draft card.
- Saved card passes `pcli validate`.
- Existing `/dashboard` still works.
