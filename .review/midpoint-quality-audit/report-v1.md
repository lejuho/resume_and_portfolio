# Midpoint Quality Audit v1

Date: 2026-05-21
Branch: audit/midpoint-requirements-quality
Baseline: main after Cycle 10

## Verdict

The project is coherent and testable at its current scale. CLI v1 requirements from `requirements.md` are substantially implemented and repeatedly verified. Cycles 7-10 intentionally moved beyond the original v1 requirements into a local dashboard product line, so the main gap is not implementation drift inside CLI v1; it is that the newer dashboard behavior now needs its own explicit requirements model.

Recommended next action before Cycle 11:

1. Create a short `requirements-dashboard.md` or add a `Post-v1 Dashboard Requirements` section.
2. Add an acceptance evidence document for dashboard flows, mirroring `docs/acceptance-v1.md`.
3. Keep the cycle branch/review process, but add a requirement trace row to every future plan.

## Current Product Model

### Core model

- Source of truth: `cards/*.mdx`, `profile.yaml`, `presets/*.yaml`, local assets.
- CLI engine: stateless commands under `pcli`.
- Render outputs:
  - resume PDF under `output/resumes/`
  - portfolio PPTX under `output/portfolios/`
- Optional LLM layer:
  - cache-backed
  - disabled unless configured
  - non-mutating for source card files
- Dashboard:
  - local Flask app
  - browse/filter/select/build
  - create/edit cards
  - structured edit for tags, metrics, evidence, visuals, narrative/body

### Process model

- One implementation cycle per branch.
- Cycle artifacts are tracked under `.review/cycle-N/`.
- Review files record blockers and resolution.
- Cycle completion pattern:
  - implementation branch
  - validator review
  - fixes
  - `status.txt` -> `ready_to_merge`
  - merge to local `main`
  - next cycle branch

This is working well for incremental development. The main process improvement is traceability: each cycle plan should explicitly state which requirement source it modifies or extends.

## Requirement Trace

| Requirement Area | Source | Current Status | Notes |
|---|---|---:|---|
| Card files as source of truth | `requirements.md` sections 1, 3, 4 | PASS | Cards are MDX files; dashboard write paths preserve file-backed model. |
| CLI stateless behavior | `requirements.md` section 1 | PASS | Build commands derive state from repo files; output/cache/build dirs are ignored. |
| Schema validation | `requirements.md` section 4 | PASS | Pydantic model + repo-level checks exist; dashboard visual edit now guards invalid visual paths. |
| `pcli new/validate/ls/show` | `requirements.md` section 5 | PASS | Covered by tests. |
| Resume PDF build | Phase 1, sections 5, 7, 10 | PASS | Typst path issues were resolved earlier; dry-run and preset flows pass. |
| Portfolio PPTX build | Phase 2, section 8 | PASS | python-pptx renderer exists; missing visual fallback in portfolio path is covered. |
| Presets and variants | Phase 3, section 6 | PASS | Preset load/run/save, `bok`, grouped/timeline variants covered. |
| Optional LLM tailoring | Phase 4, section 9 | PASS with external dependency | Tests cover fake client/cache/error behavior; live API remains manual. |
| Polish and acceptance docs | Phase 5, sections 12, 13 | PARTIAL | Smoke scripts and acceptance doc exist; manual evidence fields are not filled. |
| Dashboard/web UI | explicitly out of scope for v1 | POST-V1 | Implemented in Cycles 7-10, but needs its own requirements document. |
| Dashboard card authoring | implicit post-v1 | PASS with missing formal spec | Implemented and heavily tested after Cycles 9-10. |

## Explicit vs Implicit Requirements

### Explicit requirements already represented

- CLI command surface and core options.
- Card schema and validation rules.
- Resume and portfolio artifact generation.
- Preset format and audience variants.
- Optional LLM behavior and caching.
- Error handling expectations for validation, Typst, missing assets, and LLM.
- v1 acceptance criteria.

### Requirements that are now implicit but should be made explicit

- Dashboard is local-only and trusted-user only.
- Dashboard write scope is limited to `cards/*.mdx`.
- Dashboard card `id` is immutable; rename/move is not supported.
- Dashboard visual references must be repo-relative and contained in the repo, preferably under `assets/`.
- Dashboard create flow is basic-first; detail fields are edited after creation.
- Browser/manual QA expectations for dashboard flows.
- Whether dashboard-generated formatting churn in MDX is acceptable.
- Whether post-v1 dashboard supersedes the original v1 "Dashboard out of scope" statement.

## Test And Quality Posture

### Current strengths

- Automated test count is healthy for this codebase size: 197 passing tests.
- Most risky branches have regression tests:
  - duplicate card IDs
  - immutable `id`
  - invalid edit leaves file unchanged
  - visual path existence and containment
  - build command selected ID ordering
  - output path parsing
- `ruff check` and `ruff format --check` pass.
- CLI smoke commands pass.
- Review process catches real data-integrity bugs.

### Current gaps

- Browser visual QA is usually noted as not run.
- `docs/acceptance-v1.md` remains a template; manual fields are not completed.
- Dashboard behavior has tests but not an acceptance checklist.
- No explicit architecture document explains the boundary between schema validation, repo validation, renderer tolerance, and dashboard validation.
- Some local junk directories exist from broken path handling; empty and untracked, but cleanup should be done.

## Risk Register

| Risk | Severity | Likelihood | Current Control | Suggested Improvement |
|---|---:|---:|---|---|
| Dashboard authoring corrupts or invalidates cards | High | Medium | Atomic write + validation tests | Add dashboard acceptance checklist and pre-write repo-level validation helper. |
| Requirement drift after v1 | Medium | High | Cycle plans and reviews | Add post-v1 dashboard requirements doc. |
| Manual artifact quality not verified | Medium | Medium | Acceptance template exists | Fill acceptance evidence with actual PDF/PPTX/manual dashboard notes. |
| MDX formatting churn from frontmatter round-trip | Medium | Medium | Git diff review | Decide acceptable formatting policy or preserve more formatting. |
| LLM live behavior under-tested | Medium | Medium | Fake client tests + cache tests | Add manual live LLM evidence section; keep optional. |
| Local-only dashboard becomes trusted too broadly | Medium | Low | Bound to local Flask by default | Document threat model: solo/local/trusted browser only. |
| Absolute/path traversal bugs | High | Low after Cycle 10 | Tests for cards and visuals | Centralize path containment helpers. |

## Maintenance Model

### Good boundaries to preserve

- `scripts/card.py`: schema and repository loading.
- `scripts/select.py`: pure filtering/sorting behavior.
- `scripts/pcli.py`: CLI command composition.
- `scripts/render_resume.py`, `templates/resume/*`: PDF pipeline.
- `templates/portfolio/*`, `scripts/render_portfolio.py`: PPTX pipeline.
- `scripts/dashboard.py` + `scripts/static/dashboard.js`: local dashboard/API.

### Refactor candidates

- Extract dashboard card update validation into a helper, for example:
  - `validate_card_update_for_dashboard(repo_root, card_id, fields)`.
- Centralize path containment checks:
  - card path containment
  - asset path containment
  - output path parsing, eventually replaced by structured build output.
- Split `tests/test_dashboard.py` once it becomes harder to scan:
  - `test_dashboard_build.py`
  - `test_dashboard_authoring.py`
  - `test_dashboard_detail_editing.py`

## Process Improvements

### Add a requirement trace block to every future cycle plan

Example:

```markdown
## Requirement Trace

- Extends: `requirements-dashboard.md` section X
- Preserves: `requirements.md` core principles
- Out of scope: ...
- Acceptance evidence: ...
```

### Add review severity definitions

- BLOCKER: violates stated sprint contract, corrupts source data, or breaks main command surface.
- HIGH: likely user-visible regression or invalid artifact.
- MEDIUM: confusing workflow, incomplete acceptance, portability issue.
- LOW: polish or documentation improvement.

### Add post-v1 dashboard acceptance doc

Suggested checklist:

- Start dashboard.
- Filter/search/select cards.
- Run resume/portfolio dry-run.
- Build real resume/portfolio and copy output path.
- Create draft card.
- Edit tags/metrics/evidence/visuals/body.
- Confirm invalid edits are rejected and files stay unchanged.
- Confirm `pcli validate` passes after dashboard edits.

## Verification Run

Commands run on 2026-05-21:

- `uv run pytest -q`: PASS, 197 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli --help`: PASS
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Recommended Next Cycle

Before another feature cycle, do a small documentation/quality cycle:

- Add `requirements-dashboard.md`.
- Add `docs/acceptance-dashboard.md`.
- Document the validation boundary and path containment policy.
- Clean the four empty malformed path directories from the repo root.

After that, choose the next product feature from a clearer dashboard requirements list.
