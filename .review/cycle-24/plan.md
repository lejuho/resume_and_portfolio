# Review Artifact Hygiene Plan

Branch: feature/cycle-24-artifact-hygiene

## Summary

Recent cycles produced correct code, but local cycle-operation artifacts began to mix into
working trees: `.read-counter` files and cross-cycle advisor-feedback copies appeared beside
real cycle artifacts. Cycle 24 prevents accidental staging of non-canonical review/advisor
artifacts and makes cycle completion checks clearer.

Goal: keep `.review/cycle-N/` auditable by ensuring each cycle contains only its own plan,
status, reviews, and advisor steps.

## Input/Output Specification

- Input:
  - Existing `.review/cycle-*` directories.
  - Existing workflow rules in `AGENTS.md`.
  - Existing git ignore configuration.
  - Existing test/lint command set.
- Output:
  - Ignore rules prevent local `.read-counter` files from appearing as untracked changes.
  - Workflow docs explicitly forbid cross-cycle advisor-feedback duplication.
  - A small validation/check script or test catches obvious cross-cycle advisor artifact
    contamination before merge.
  - Cycle completion instructions include a stage-review checklist that excludes local skills,
    lock files, read counters, and unrelated cross-cycle notes.
- Failure:
  - Hygiene check fails or warns clearly when an advisor-feedback file under `cycle-N` claims
    it belongs to another cycle or is labeled as a cross-reference copy.

## Key Changes

- Git hygiene: update `.gitignore` for `.review/**/.read-counter`.
- Workflow docs: update `AGENTS.md` Review/Advisor sections with:
  - advisor-feedback files belong only to the current cycle step;
  - cross-cycle references should link to the original artifact, not copy it;
  - merge staging must exclude `.read-counter`, local skill/plugin files, and unrelated
    untracked artifacts.
- Validation: add a lightweight script or pytest coverage for `.review/cycle-*` advisor
  artifacts.
  - Prefer a Python test if it naturally fits the current test suite.
  - Keep checks deterministic and local; no network or external tools.
- Cycle artifacts: add normal Cycle 24 review/status artifacts only through the standard flow.

## Sprint Contract

- Pass criteria:
  - `.read-counter` files under `.review/` are ignored by git.
  - `AGENTS.md` explicitly documents no cross-cycle advisor-feedback duplication.
  - Hygiene check detects advisor files whose heading or body indicates they are
    "Session Cross-Reference" or belong to a different cycle directory.
  - Hygiene check allows valid existing advisor-feedback files.
  - Running `git status --short` after implementation does not show newly ignored
    `.review/**/.read-counter` files.
  - Existing Cycle 21-23 tests remain green.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - `uv run python scripts/evaluate_studio_grounding.py --dry-run`
- Test cases:
  - Valid advisor-feedback fixture passes.
  - Cross-reference advisor-feedback fixture fails.
  - Wrong-cycle advisor-feedback fixture fails.
  - `.gitignore` contains the read-counter ignore rule.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates

- Existing historical cycles may have missing advisor-feedback files; the new check should not
  require every old step to exist unless already part of current workflow.
- Review files may legitimately mention older cycles while analyzing regressions; the hygiene
  rule should target advisor-feedback copies, not review prose.
- A valid advisor note may quote a path from another cycle; the check should reject explicit
  cross-reference artifacts, not every path mention.

## Simpler Alternative

Only add `.read-counter` to `.gitignore`. This removes some noise but does not prevent
cross-cycle advisor copies from being staged, which was the actual merge-risk observed in
Cycle 23. The chosen approach keeps scope small while protecting the review trail.

## Assumptions

- `AGENTS.md` is the source of truth for cycle workflow and can be updated in this cycle.
- `.read-counter` files are local hook/session artifacts and should never be committed.
- Local skill/plugin files such as `.agents/` and `skills-lock.json` are outside this project
  cycle unless a future cycle explicitly scopes them.
- A source/test-level hygiene check is enough; no git hook installation is required.

## Review Guidance

### Enumeration Needed

Review existing cycle artifacts:

- Search: `rg -n "Session Cross-Reference|Cycle:|advisor-feedback|read-counter|RESOLVED|stage" AGENTS.md .review tests scripts .gitignore`
- Enumerate advisor files:
  - `Get-ChildItem -Recurse .review -Filter step-*.md`

Review ignore status:

- Verify `.review/cycle-*/.read-counter` does not appear in `git status --short` after the
  ignore rule is applied.

### Verification Method Guide

- Unit tests are sufficient for parsing/validating advisor-feedback hygiene rules.
- `git status --short` inspection is required to verify ignore behavior.
- Do not delete user/local untracked files unless explicitly requested; ignore rules should
  hide future status noise without destructive cleanup.
- Do not rewrite historical review/advisor files outside this cycle unless a test cannot be
  made compatible with valid history.
