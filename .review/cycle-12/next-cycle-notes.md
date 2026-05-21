# Next Cycle Notes: Studio UX Language + State Explanation

## Candidate Scope For Cycle 13

Add lightweight UI/UX explanation inside Studio and/or Dashboard so the user understands the product language without feeling like they are managing a database.

## UX Problems To Address

- `live`, `draft`, and `archived` are currently schema/status terms, but the UI does not explain what each state means.
- Studio introduces softer concepts like Career Memory, Draft, Refine, and Save as card, while Dashboard still exposes exact card/admin language.
- Missing info prompts are useful, but should feel like follow-up questions rather than validation errors.
- The user needs to understand that one saved card can later feed resume, portfolio, and other outputs.

## Suggested Microcopy / Terminology

- Career Memory: raw or refined activity material that may become a reusable card.
- Draft: saved but not yet ready for default resume/portfolio selection.
- Live: ready to be included in generated outputs by default.
- Archived: kept for history, hidden from normal output selection.
- Refine: turn loose input into a structured draft.
- Save as draft card: commit the reviewed draft into canonical local card storage.

## Suggested UI Changes

- Add a compact "What do statuses mean?" hint near Studio save or Dashboard status filter.
- Add small helper text after Studio save:
  - "Saved as Draft. Mark it Live in Dashboard when it is ready for normal output generation."
- Add status tooltips or inline labels:
  - Draft: "work in progress"
  - Live: "ready for output"
  - Archived: "kept but hidden"
- Prefer terms like "career memory", "draft", "refine", and "output" in Studio.
- Keep exact schema/admin terms mostly inside `/dashboard`.

## Acceptance Idea

- A new user can explain what Draft/Live/Archived mean after seeing the UI.
- Studio still feels light and creation-first, not like a form manual.
- Dashboard remains precise but gains enough labels to reduce confusion.
