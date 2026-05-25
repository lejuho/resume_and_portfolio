# User Direction 001: Replace Persona Prompting With Method-Grounded Drafting

Date: 2026-05-25  
Cycle: 20  
Applies after: `review-v1.md`

## User Clarification

The Studio refinement prompt should not rely primarily on role-play wording such as:

```text
You are a senior career consultant and portfolio narrative designer.
```

Instead, it should apply concrete, research-backed career-writing methods already selected in
the audit:

- resume drafting based on verified action, context, and result evidence;
- portfolio drafting based on problem, framing, approach/decision, outcome/evidence, and
  insight;
- consultant workflow based on evidence extraction, gap questioning, target-specific drafting,
  and human factual approval.

Sources already captured for this decision:

- `docs/research/career-output-methodology.md`
- `docs/research/consultant-workflow-model.md`
- `requirements-dashboard.md` sections 8.4-8.7 and D-008

## Required Change In The Current Fix Pass

- Rewrite the grounded Studio prompt so its primary instruction is a procedure and quality
  standard, not an expert persona.
- It may name the adopted method or evidence rubric, but must not imply that the model has
  independently consulted unnamed experts or external materials at generation time.
- The prompt must explicitly preserve the existing Cycle 20 grounding rules:
  - extract only supported facts from raw input;
  - isolate assumptions and questions needing confirmation;
  - do not invent dates, metrics, tools, evidence, individual ownership, or outcomes;
  - transform the same verified evidence differently for resume versus portfolio output;
  - keep human approval before persistence.

Suggested instruction style:

```text
Apply an evidence-grounded career-writing workflow.
First identify facts explicitly supported by the notes and unresolved gaps.
Then draft resume content using action/context/result only where supported, and portfolio
content using problem/framing/approach/outcome/insight only where supported.
Put unsupported interpretations in assumptions or missing_info, never in claimed facts.
```

## Verification

- Add or revise a prompt-contract test asserting that the prompt describes the grounded
  procedure and output-specific rubric.
- Remove or avoid a test that treats the consultant persona wording itself as a required
  quality property.
- This clarification is within Cycle 20 grounded-preview scope and does not add a new output
  intent or UI feature.
