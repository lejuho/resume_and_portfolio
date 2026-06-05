# Ten-Cycle Requirements, Design, Test, And Quality Audit Plan

Branch: feature/cycle-31-quality-spec-audit

## Summary

Ten feature cycles have passed since the Cycle 20 methodology/specification audit. Cycles 21-26
expanded Application Writing and its export workflow, while Cycles 27-30 introduced the parallel
Workspace route, its design system, dark mode, card disclosure, and deterministic fit signals.

The implementation and automated suite are healthy, but the canonical product documents still
describe the Dashboard/Studio baseline as current through Cycle 19 or Cycle 20. Workspace behavior
is primarily specified in cycle plans and the untracked `landing.md` brief rather than in a
maintained requirement and design source.

This cycle performs a clean requirements/design/test/quality audit before further Workspace
features. It updates specifications and traceability, executes the full quality baseline, and
records product defects or design decisions as follow-up work. It does not add a product feature
or silently fix unrelated product behavior.

The deferred theme-coverage plan currently preserved on
`feature/cycle-31-theme-coverage-recommendations` becomes a Cycle 32 candidate after this audit;
its cycle number and branch mapping must be corrected when resumed.

## Input/Output Specification

- Inputs:
  - `requirements.md` and `requirements-dashboard.md`.
  - `docs/test-cases.md`, `docs/acceptance-v1.md`, `docs/acceptance-studio.md`, and
    `docs/design-system-studio.md`.
  - `landing.md` as an unstaged research/design brief, not as a canonical requirement.
  - Cycle 21-30 plans, reviews, statuses, and advisor records.
  - Current implementation under `scripts/`, templates, and static assets.
  - Current automated tests, including `tests/test_cycle21.py` through
    `tests/test_cycle30.py`.
- Normal outputs:
  - `.review/cycle-31/report-v1.md` with verdict, current product model, Cycle 21-30 requirement
    trace, design conformance findings, test coverage findings, quality baseline, risk register,
    and prioritized follow-up cycles.
  - `requirements-dashboard.md` updated from its Cycle 19/20 snapshot through Cycle 30.
  - `docs/test-cases.md` updated so every externally meaningful Cycle 21-30 behavior has a
    product-level test case or an explicit out-of-scope/deferred classification.
  - `docs/acceptance-studio.md` updated with current Application Writing and Workspace manual
    acceptance flows, while preserving historical evidence sections.
  - A canonical Workspace design specification under `docs/` that records implemented tokens,
    information architecture, interaction states, accessibility rules, and the boundary between
    implemented behavior and future `landing.md` direction.
  - Automated quality results and clearly recorded manual/browser limitations.
- Failure/defect output:
  - Any implementation defect found is assigned severity, evidence, affected requirement, and a
    proposed follow-up cycle.
  - High-severity defects that invalidate a current public workflow make the audit verdict
    `BLOCKED_FOR_FIX`.
  - Lower-severity debt does not trigger opportunistic product edits in this audit.

## Key Changes

- Audit report — `.review/cycle-31/report-v1.md`
  - Establish the baseline commit and audit date.
  - Enumerate Cycle 21-30 shipped behavior rather than sampling a few plans.
  - Build a trace matrix:
    requirement -> implementation surface -> automated evidence -> manual evidence -> gap.
  - Separate confirmed defects, specification drift, test-quality debt, and future product ideas.
  - Recommend whether the deferred theme-coverage cycle is ready, needs amendment, or should wait
    behind a defect/remediation cycle.
- Requirements — `requirements-dashboard.md`
  - Refresh status and last-reviewed metadata through Cycle 30.
  - Add/refresh Application Writing requirements for blind hiring, safe projection, advisory
    sanitization, preview provenance, copy/export, and packet formatting.
  - Add Workspace as a distinct product surface while preserving `/studio` and `/dashboard`
    roles.
  - Specify Workspace's current deterministic fit-signal boundary and non-persistence rules.
  - Distinguish implemented requirements from future theme extraction/tagging/recommendation.
  - Preserve `requirements.md` as the historical CLI v1 contract; clarify the post-v1 extension
    rather than rewriting history.
- Product test specification — `docs/test-cases.md`
  - Audit existing product cases against Cycle 21-30 plans and current tests.
  - Add missing behavior-level cases for Application Writing export/packet and Workspace route,
    card loading, design/theme states, disclosure, selection, and fit signals.
  - Use stable product behavior IDs; do not mirror pytest function names mechanically.
  - Mark each case automated, manual, or mixed and identify the evidence location.
- Acceptance evidence — `docs/acceptance-studio.md`
  - Refresh status wording and automated baseline commands.
  - Preserve Studio/Application Writing acceptance and add a separate Workspace flow.
  - Include light/dark mode, keyboard focus, long-text containment/disclosure, live-card loading,
    deterministic fit updates, preview handoff, and route separation.
  - Record execution results where feasible; leave external provider/live artifact checks clearly
    marked `SKIP` or `PENDING` with reason rather than implying success.
- Design specification — `docs/design-system-workspace.md`
  - Convert the implemented Workspace design contract into a maintained document.
  - Record semantic tokens, light/dark theme behavior, typography/casing/weight constraints,
    two-pane structure, evidence-card anatomy, selected/focus/hover states, long-text disclosure,
    responsive expectations, and accessibility requirements.
  - Include a conformance table for current implementation.
  - Keep future theme coverage, S0 research, S1 AI tagging, and advanced recommendation visibly
    labeled as future direction.
  - Reference `landing.md` as planning research only; do not stage or make it a hidden normative
    dependency.
- Test and quality audit
  - Enumerate all tests and map Cycle 21-30 public behavior to executable evidence.
  - Identify tests that only inspect source strings where behavior execution is required.
  - Identify duplicated assertions, stale tests, misleading names/comments, untested branches,
    and reliance on implementation details.
  - Add or improve tests only when closing a specification/test-evidence gap without changing
    product behavior. Product defects become follow-up findings.
  - Run the full automated baseline and relevant CLI dry-run/smoke checks.
  - Record existing warnings separately from failures and decide whether they warrant a later
    maintenance cycle.
- Workflow traceability
  - Verify Cycle 21-30 statuses/reviews are complete and advisor records obey cycle hygiene.
  - Do not modify historical review bodies or rewrite historical cycle artifacts.

## Sprint Contract

- Every Cycle 21-30 plan is represented in the audit trace, including test-only and process-only
  cycles.
- Every current public route (`/dashboard`, `/studio`, `/workspace`) has an explicit role and
  preserved relationship in requirements.
- Application Writing's current privacy/provenance/export contracts are documented through
  Cycle 26.
- Workspace's current route, API-array consumption, live filtering, design tokens, dark mode,
  card disclosure, selection, and deterministic fit signals are documented through Cycle 30.
- Future theme extraction/tagging/recommendation is not described as implemented.
- `docs/test-cases.md` provides product-level cases for all externally meaningful Cycle 21-30
  behavior and identifies automated/manual evidence.
- Test cases assert behavior where practical; source-inspection-only coverage is called out when
  it cannot prove runtime behavior.
- `docs/acceptance-studio.md` contains a separate, executable Workspace checklist.
- `docs/design-system-workspace.md` exists and distinguishes current conformance from future
  direction.
- The audit report contains:
  - baseline and method;
  - requirement trace;
  - design conformance;
  - test inventory and gap analysis;
  - automatic and manual check results;
  - defect/debt register with severity;
  - prioritized next-cycle recommendation.
- No product feature, backend route, persistence behavior, provider behavior, or card schema is
  added in this cycle.
- Historical `review-vN.md` bodies and past cycle records remain unchanged.
- Untracked `.agents/`, `landing.md`, and `skills-lock.json` remain unstaged.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pyright scripts/`
  - `uv run pcli validate`
  - `uv run pcli --help`
  - `uv run pcli dashboard --help`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
- Manual/browser checks:
  - `/dashboard`, `/studio`, and `/workspace` route smoke.
  - Workspace card load, selection, target input, fit update, preview, disclosure, light/dark,
    keyboard focus, and long-text containment.
  - Studio capture and Application Writing preview/export smoke using mock mode.
  - External provider checks may be skipped only with an explicit environment reason.
- gas limit: N/A
- slither pass: N/A

## Three Candidate Missing Edge Cases

- Documentation may claim a behavior is automated when the corresponding test only searches
  static source text; trace must classify evidence strength accurately.
- A cycle may be process/test-only and have no product requirement, but it must still appear in
  the trace as a quality-control requirement rather than being omitted.
- Manual acceptance may be impossible in the current browser/provider environment; the report
  must preserve `PENDING`/`SKIP` rather than converting missing evidence into a pass.

## One Simpler Alternative

Run the current test suite and update only document dates. This is faster but would preserve the
same structural drift: Workspace would remain specified mostly in cycle plans, product tests
would not be traced to requirements, and source-inspection tests could be mistaken for runtime
coverage. It is therefore rejected.

## Assumptions

- Cycle 21-30 merged reviews and their final statuses are authoritative historical evidence.
- `landing.md` is a useful design/research brief but remains untracked and non-canonical.
- The audit may add tests and documentation but will not alter user-facing implementation unless
  the user explicitly approves a follow-up fix cycle.
- Live Anthropic/Google checks and real PDF/PPTX visual review depend on local credentials and
  installed tools; unavailable checks must be recorded honestly.
- The previously prepared theme-coverage branch is not merged and can be re-planned as Cycle 32
  after this audit without rewriting its existing history.

## Review Guidance

### Enumeration Required

- Enumerate all Cycle 21-30 plans, final reviews, statuses, and advisor records:
  - PowerShell:
    `21..30 | ForEach-Object { Get-ChildItem ".review/cycle-$_" -File -Recurse }`
  - Expected: all ten cycles represented in the report; no cross-cycle advisor copies.
- Enumerate public routes and API endpoints:
  - Search:
    `rg -n "@app\\.route|@app\\.(get|post|put|patch|delete)" scripts/dashboard.py`
  - Classify each route under Dashboard, Studio, Workspace, shared API, or internal support.
- Enumerate frontend API consumers:
  - Search:
    `rg -n "fetch\\(|/api/" scripts/static scripts/templates`
  - Confirm documented request/response shapes match current code, especially bare-array
    `/api/cards`.
- Enumerate requirements and product test IDs:
  - Search:
    `rg -n "^(##|###)|\\b(PT|MT|D)-[A-Z0-9-]+" requirements-dashboard.md docs/test-cases.md docs/acceptance-studio.md`
  - Confirm no duplicate IDs and no implemented Cycle 21-30 behavior lacks a trace row.
- Enumerate Cycle 21-30 tests and classify evidence strength:
  - Search:
    `rg -n "^def test_|source|static/|application-preview|workspace|handoff|blind_hiring" tests/test_cycle2*.py tests/test_cycle30.py`
  - Classification: behavior execution, API integration, source inspection, or manual-only.
- Enumerate persistent writes and provider boundaries:
  - Search:
    `rg -n "write_text|write_bytes|frontmatter\\.dump|ANTHROPIC|GOOGLE|application_preview_llm|studio_refine_llm" scripts`
  - Confirm requirements still reflect source-of-truth, no-persistence preview, and optional AI.
- Enumerate design tokens and prohibited Workspace typography:
  - Search:
    `rg -n -- "--ws-|font-weight|text-transform|prefers-color-scheme|data-theme|Show full summary|Collapse summary" scripts/templates/workspace.html scripts/static/workspace.js`
  - Compare the complete token/state set with `docs/design-system-workspace.md`.

### Verification Method Guide

- Requirements-to-code trace:
  - Code/source enumeration plus focused API tests is sufficient for route and payload contracts.
  - A requirement is not `PASS` merely because a cycle review once passed; verify current code.
- JavaScript interaction behavior:
  - Static string assertions are insufficient for selection, disclosure, filtering, coverage
    recomputation, or export formatting. Require executable helper/DOM behavior evidence or mark
    the gap explicitly.
- Privacy and blind-hiring boundaries:
  - Full serialized payload/preview adversarial tests are required. Documentation or happy-path
    mocks alone are insufficient.
- Persistence boundaries:
  - API integration tests comparing card files/count before and after preview/export are
    sufficient for this local single-user architecture.
- Visual and accessibility claims:
  - Source checks can verify token/focus hooks but cannot prove readability, containment, or
    keyboard operation. Browser/manual evidence is required or must remain pending.
- CLI/PDF/PPTX behavior:
  - Dry-run checks prove selection/composition only. Real artifact rendering and visual quality
    must be classified separately in acceptance evidence.
