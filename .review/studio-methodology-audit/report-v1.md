# Studio Methodology And Specification Audit v1

Date: 2026-05-25  
Branch: `audit/studio-methodology-requirements-refresh`  
Baseline: `main` after Cycle 19 (`13a18ed`)

## Verdict

`READY_FOR_CYCLE_20_PLANNING`, with one important constraint: Cycle 20 should implement a
grounded one-shot structured preview, not an unconstrained prompt-polish or multi-call
workflow.

The project works as a local career-memory product, but its requirements and product-level
test specification were behind implementation after Cycles 11-19. This audit updates that
documentation boundary and establishes a research-based quality model for the next harness.

## Audit Deliverables

| Deliverable | Result |
|---|---|
| Current-state trace and gap assessment | This report |
| Resume/portfolio evidence and two-track rubric | `docs/research/career-output-methodology.md` |
| Consultant workflow model | `docs/research/consultant-workflow-model.md` |
| Harness/token evaluation and recommendation | `docs/research/llm-harness-evaluation.md` |
| Updated post-v1 requirements | `requirements-dashboard.md` |
| Updated product test specification | `docs/test-cases.md` |
| Studio manual acceptance checklist | `docs/acceptance-studio.md` |

## Requirement Trace

| Requirement ID | Source | Implemented behavior | Automated test evidence | Manual evidence | Gap / action |
|---|---|---|---|---|---|
| CORE-SSOT | `requirements.md`; dashboard section 3 | Canonical cards remain file-backed MDX. | Card/dashboard/Studio save tests | v1 template; Studio checklist added | Fill dated manual results later. |
| CORE-OUTPUT | `requirements.md` | PDF resume and PPTX portfolio build flows exist. | Build/portfolio tests | `docs/acceptance-v1.md` | Existing acceptance fields remain unfilled. |
| ADMIN-UI | dashboard sections 2.1, 6, 7 | `/dashboard` browse, select, build, create/edit, safe visuals. | `tests/test_dashboard.py` | Studio checklist includes regression | Documented previously, retained. |
| STUDIO-CAPTURE | dashboard section 5 | `/studio`, raw input, intent, preview, new draft save, handoff. | `tests/test_studio.py` | Studio checklist added | Product test specification previously omitted rows; fixed. |
| STUDIO-LLM | dashboard section 8 | Mock fallback and optional live refine source. | `tests/test_llm_studio.py`, `tests/test_cycle14.py`, `tests/test_cycle16.py` | Studio checklist added | Quality oracle previously absent; planned cases added. |
| AI-CONFIG | dashboard D-006 | Anthropic and Google provider resolution; alias keys/model. | `tests/test_cycle17.py`, `tests/test_cycle18.py` | Provider checklist added | Requirements were Anthropic-only; fixed. |
| AI-CHECK | dashboard D-007 | Configured state differs from explicit live connection check. | `tests/test_cycle19.py` | Provider checklist added | Previously absent in requirements/tests spec; fixed. |
| AI-GROUND | dashboard sections 8.4-8.5, 8.7, D-008 | Not yet implemented. | `PT-GROUND-*` marked planned | Future grounded acceptance section | Recommended Cycle 20 scope. |

## Explicit Versus Missing Requirements

### Now explicit

- Admin dashboard and creation-first Studio have separate roles.
- Studio creates reviewed draft cards while preserving MDX as the single durable source.
- Supported AI providers and connection-status semantics are documented.
- Intent-specific quality is split between formal Korean application material and global
  tech/Web3 project presentation.
- Factual grounding, contribution attribution, human approval, and measurable evaluation are
  normative requirements for the next harness.

### Still deliberately unresolved

- Whether Track K should receive employer-specific preset variants beyond current BOK output.
- Whether later Studio should edit existing cards, store raw source material, or ingest files.
- Whether real Korean recruiter/mentor interviews change the Track K rubric.
- Whether Candidate B becomes worthwhile under larger quota or more complex source material.

### Newly fixed sequencing decision

- Cycle 20 remains grounded preview stabilization for resume/portfolio.
- The next feature cycle after that should add an Application Writing Harness for
  자기소개서 and supplied-question answers.
- Application writing must separate personal facts from cards and target context from
  user-supplied job/organization/question material.

## Research Conclusions

| Question | Finding | Confidence |
|---|---|---:|
| What should resume material emphasize? | Verified achievements, job relevance, and evidence of problem solving/contribution; quantify only when supported. | High for shared criteria; medium for Korean-specific presentation |
| What should portfolio material emphasize? | A selected project story needs problem, process/decision, outcome/evidence, and the user's role. | Medium; strongest for early-career/design-adjacent material |
| Should one shape serve every reader? | No. Formal application and global builder portfolio expectations should remain separate intent/preset tracks. | Medium-high |
| How should AI imitate a consultant? | Extract evidence, identify gaps, propose positioning, draft per target, then require human factual approval. | Medium-high |
| What harness direction is justified now? | Grounded one-shot structured preview is the appropriate next implementation; staged calls are premature. | Medium; live pilot incomplete due quota |

## Live Pilot Finding

A limited Gemini pilot was attempted with synthetic inputs only. The provider was configured
and connection check passed. The planned comparison could not complete because the configured
`gemini-2.5-flash` free tier returned an explicit daily limit of 20 successful requests.

The only saved like-for-like case found:

| Candidate | JSON parse | Total tokens | Latency |
|---|---:|---:|---:|
| Current prompt-only baseline | Fail (markdown fenced JSON) | 3,225 | 13.2 s |
| Grounded one-shot structured response | Pass | 1,616 | 7.8 s |

This is sufficient to expose a concrete baseline reliability risk and support structured output
as a Cycle 20 design choice. It is not sufficient to assert final quality superiority across
the corpus. See `docs/research/llm-harness-evaluation.md`.

## Risk Register

| Risk | Severity | Current control | Recommended next action |
|---|---:|---|---|
| Generated claims exceed source facts | High | Human review; mock/LLM source display | Cycle 20 grounded facts/assumptions contract and metamorphic tests. |
| Live LLM falls back silently after provider failure | Medium | Connection check and refine-source UI | Preserve explicit source; consider later refine failure notice. |
| Provider quota blocks interactive or evaluation flow | Medium | Safe mock fallback | Avoid default multi-call workflow; checkpoint evaluation runner. |
| Korean formal-output rubric is under-validated locally | Medium | Formal truthfulness requirement; BOK preset | Later review with Korean target application/reviewer samples. |
| Manual artifact quality remains undocumented | Medium | Acceptance templates | Execute and record `docs/acceptance-studio.md` after next visible behavior change. |
| Requirements drift behind incremental feature cycles | Medium | Cycle plans/reviews | Require requirement trace and test-spec update for new public surfaces. |

## Recommended Cycle 20 Scope

Implement only the grounded one-shot Studio preview contract:

- structured `source_facts`, `assumptions`, `missing_info`, and output-targeted drafts;
- non-invention and team-attribution safeguards;
- visible review treatment without persisting preview metadata by default;
- schema-backed provider output where supported plus safe validation/fallback;
- deterministic tests and an optional quota-aware evaluation runner.

Defer a staged two-call consultant pipeline, interviews, raw-source persistence, and new
dashboard authoring capabilities until that contract is verified.

## Recommended Following Cycle Scope

After Cycle 20 passes review, plan an Application Writing Harness cycle:

- add `cover_letter` / 자기소개서 and `application_answer` output intents;
- accept target context: organization, role/JD, exact question, competency cue, and character
  limit;
- select and justify supporting cards before generating a draft;
- show personal facts and target-context statements separately in preview;
- enforce no unsupported personal claims and no invented organization motivation;
- cover NCS/blind-hiring restrictions and character-limit boundaries in tests.
