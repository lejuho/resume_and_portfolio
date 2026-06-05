# Codex Review v1

## Verdict

BLOCKED

## Findings

### ISSUE-1 [MEDIUM] Test inventory counts are materially inaccurate

- Location: `.review/cycle-31/report-v1.md:76`
- Analysis: The report presents approximate per-file test counts as an audit inventory, but the
  values do not match the current files. Actual `def test_` counts are: Cycle 21 = 94, Cycle 22 =
  6, Cycle 23 = 7, Cycle 24 = 5, Cycle 25 = 22, Cycle 26 = 14, Cycle 27 = 23, Cycle 28 = 19,
  Cycle 29 = 21, and Cycle 30 = 25. The report instead records values such as Cycle 21 `~40`,
  Cycle 22 `~10`, Cycle 23 `~15`, Cycle 24 `~10`, and Cycle 30 `~19`.
- Impact: The cycle exists specifically to refresh test specifications and assess evidence
  quality. An inaccurate inventory makes the resulting gap analysis and quality baseline
  unreliable even though the full suite itself passes.
- Fix direction: Replace approximate counts with reproducible exact counts, record the counting
  method, and re-check each behavior/API/source classification against the actual tests. Avoid
  using approximate values in an audit report unless clearly labeled as a non-inventory sample.

### ISSUE-2 [MEDIUM] Workspace design conformance claims do not match the CSS

- Location: `docs/design-system-workspace.md:29`, `docs/design-system-workspace.md:127`,
  `requirements-dashboard.md:702`, `scripts/templates/workspace.html:145`
- Analysis: The design document says repeated colors are tokenized and states that the Generate
  button receives an accent focus outline via `.ws-theme-toggle:focus-visible`. That selector
  applies only to the theme toggle; there is no `.ws-generate-btn:focus-visible` rule. The
  requirements also say all Workspace color values are CSS custom properties, while the Generate
  button still uses raw `color: #fff` outside the token definitions.
- Impact: The new canonical Workspace design specification records behavior and conformance that
  the implementation does not provide. Reviewers and future cycles would treat missing focus
  styling and a token exception as already solved.
- Fix direction: Keep this audit documentation-only. Correct the documents to describe the
  current browser-default Generate-button focus behavior and explicitly permit/document the
  one-off white foreground exception. Alternatively, classify both as follow-up design debt;
  do not change product CSS in this audit without an escalation amendment.

### ISSUE-3 [MEDIUM] The next-cycle recommendation mischaracterizes the preserved plan

- Location: `.review/cycle-31/report-v1.md:194`
- Analysis: The report describes
  `feature/cycle-31-theme-coverage-recommendations` as an “LLM-based S1 tagging” plan. The
  preserved plan explicitly defers S0/S1 AI work and proposes manual required-theme input plus
  deterministic, in-memory text-derived matching with no persistent `themes` schema.
- Impact: The audit's main planning recommendation is based on a feature scope that is not the
  scope actually preserved in git. This can incorrectly delay or redesign the next cycle.
- Fix direction: Read the preserved branch plan directly and summarize it accurately. State
  separately whether browser behavior coverage should precede that deterministic plan, and give
  the evidence for that sequencing decision.

### ISSUE-4 [LOW] Acceptance status metadata remains stale

- Location: `docs/acceptance-studio.md:3`
- Analysis: The file still says it is an execution checklist “through Cycle 19 and future
  grounded drafting,” even though this cycle adds acceptance material through Cycle 30.
- Impact: The Sprint Contract required refreshed status wording, and readers cannot tell from the
  document header that Application Writing and Workspace acceptance are now included.
- Fix direction: Update the status/last-reviewed metadata to reflect coverage through Cycle 30
  and the Cycle 31 audit. Preserve historical acceptance sections.

## Sprint Contract Check

| Contract Item | Status | Notes |
|---|---|---|
| Cycle 21-30 represented in requirement trace | PASS | All ten cycles appear in the report. |
| `/dashboard`, `/studio`, `/workspace` roles explicit | PASS | Requirements section 2 now covers all three. |
| Application Writing documented through Cycle 26 | PASS | D-010 through D-012 added. |
| Workspace documented through Cycle 30 | PARTIAL | Coverage exists, but ISSUE-2 contains false conformance claims. |
| Future theme work not described as implemented | PASS | Current requirements/design mark it future. |
| Product-level test cases updated | PASS | Export and Workspace cases added with evidence-strength notes. |
| Accurate test inventory and gap analysis | FAIL | ISSUE-1. |
| Workspace acceptance checklist added | PASS | Manual and provider/no-persistence sections added. |
| Canonical Workspace design spec added | PARTIAL | File exists; ISSUE-2 requires correction. |
| Audit report has required sections | PASS | Baseline, trace, conformance, tests, checks, debt, recommendations present. |
| Next-cycle recommendation grounded in actual preserved plan | FAIL | ISSUE-3. |
| No product behavior changes | PASS | Only documentation/review artifacts changed. |
| Historical review bodies unchanged | PASS | No historical review edits found. |
| Local plugin/planning files remain unstaged | PASS | `.agents/`, `landing.md`, `skills-lock.json` remain untracked. |

## Automatic Checks

- `uv run pytest -v`: PASS — 612 passed, 7 existing `datetime.utcnow()` warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 37 files formatted
- `uv run pyright scripts/`: NOT RUN — executable not installed (`program not found`)
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`
- `uv run pcli --help`: PASS
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS — 4 cards selected
- `uv run pcli build portfolio --dry-run`: PASS — 4 cards selected
- Browser acceptance: PENDING — Browser connection failed with the current Windows sandbox
  process-initialization error; no browser result is claimed.

## Changes Outside Plan

No product scope creep found. Changes are limited to the planned requirements, test
specification, acceptance, design-system, audit, and advisor artifacts.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY
- ISSUE-3: APPLY
- ISSUE-4: APPLY

### Applied

RESOLVED: ISSUE-1 — Exact test counts and counting method in §4.1
- `report-v1.md §4.1`: Replaced ~N approximate counts with exact `def test_` counts (C21=94,
  C22=6, C23=7, C24=5, C25=22, C26=14, C27=23, C28=19, C29=21, C30=25). Added counting
  method note explaining 236 (C21-C30 sum) vs 612 (full-repo baseline).

RESOLVED: ISSUE-2 — Generate button focus and color:#fff documented as exceptions
- `docs/design-system-workspace.md §4`: Generate button focus row corrected to
  "Browser default focus outline — no `.ws-generate-btn:focus-visible` rule".
- `docs/design-system-workspace.md §7`: Conformance table row annotated with §8 reference.
- `docs/design-system-workspace.md §8`: New "Known Exceptions" section added documenting
  `color: #fff` (one-off, non-repeated value) and missing focus rule; both linked to DEBT-006.
- `report-v1.md §3`: "Card hover / selected / focus-visible states" row split into three rows;
  Generate button focus explicitly marked "browser default". DEBT-006 added to debt register.
- `requirements-dashboard.md D-014`: "All Workspace color values" → "All *repeated* Workspace
  color values"; exception note for `color: #fff` and DEBT-006 added.

RESOLVED: ISSUE-3 — Next-cycle recommendation corrected to reflect preserved plan
- `report-v1.md §9` "Conditionally Ready" section rewritten to describe the actual plan:
  manual required-themes input, deterministic `covered/required*100` formula, unselected-card
  recommendations, no S1 AI tagging, no backend mutation. Browser-test-first ordering removed
  (no evidence basis for that dependency).

RESOLVED: ISSUE-4 — Acceptance-studio.md status line updated
- `docs/acceptance-studio.md:3`: Status now reads "execution checklist for Studio, Application
  Writing (through Cycle 21), and Workspace (Cycles 27–30); last reviewed Cycle 31 audit
  (2026-06-05)".

자동 체크: pytest ✅ 612 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅
