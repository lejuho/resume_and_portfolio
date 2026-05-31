# Codex Review v1

## Verdict
BLOCKED

## Findings
### ISSUE-1 [HIGH] Cycle 26 contains a cross-cycle advisor-feedback copy for Cycle 25 work
- Location: `.review/cycle-26/advisor-feedback/step-003.md:1`
- Analysis: The file is stored under Cycle 26, but its title and content identify it as a
  "Session Account: Cycle 25 ISSUE-1 Fix" and point to the primary artifact at
  `.review/cycle-25/advisor-feedback/step-003.md`. Cycle 24 added a workflow hygiene rule:
  advisor-feedback files belong only to the current cycle step, and cross-cycle references
  should link to the original artifact rather than copying or re-accounting for it in the
  current cycle directory.
- Impact: This violates the artifact hygiene baseline before merge. It also weakens the
  reviewer trail: Cycle 26 appears to have an extra step that was actually Cycle 25 resolution
  work.
- Fix direction: Remove `.review/cycle-26/advisor-feedback/step-003.md` from Cycle 26. Do not
  replace it with another copied "session account" file. If Cycle 26 needs to mention the Cycle
  25 reset baseline, reference `.review/cycle-25/advisor-feedback/step-003.md` from review or
  implementation notes only. Also consider strengthening `tests/test_cycle24.py` so real-tree
  advisor hygiene rejects advisor files under `cycle-N` that name or point to a different
  cycle's primary advisor artifact.

## Sprint Contract Check
| Contract Item | Status | Notes |
| --- | --- | --- |
| `cover_letter` and `application_answer` packet templates are visibly distinct | PASS | `_packetTitle()` emits distinct titles for both output types. |
| Character count and character limit appear when present | PASS | `Draft Metadata` includes count+limit when `character_limit` exists, and count-only branch otherwise. |
| Draft metadata includes provenance and source/fallback values | PASS | `_buildHandoffPacket()` reads `draft_provenance`, `refine_source`, and `fallback_reason` from preview. |
| Evidence summary remains derived from sanitized preview fields, not raw `_appCards` | PASS | Evidence loop reads `selected_cards` display fields; no `_appCards` reference in builder. |
| Blind-hiring export remains free of canonical IDs/protected markers | PASS | No new raw-card read path introduced; Cycle 25 opaque selected-card tests remain green. |
| AI guidance remains advisory and outside verified draft | PASS | Guidance remains under an `ADVISORY` section. |
| Cycle 25 stale-state reset remains unchanged | PASS | Cycle 25 reset tests pass. |
| No card file is created or mutated by preview/export | PASS | No backend/persistence changes; Cycle 25 no-persistence tests pass. |
| Review artifact hygiene | FAIL | ISSUE-1: Cycle 26 advisor-feedback includes copied Cycle 25 session account. |

## Automatic Checks
- `uv run pytest tests/test_cycle24.py tests/test_cycle25.py tests/test_cycle26.py -v`: PASS — 41 passed
- `uv run pytest -v`: PASS — 524 passed, 7 existing `datetime.utcnow()` deprecation warnings
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS — 33 files already formatted
- `uv run pcli validate`: PASS — existing warning: `test: evidence is empty`

## Changes Outside Plan
The code changes are within plan. The extra Cycle 26 advisor-feedback session account for Cycle
25 work is outside the cycle's artifact boundary and must be removed before merge.

---

## RESOLVED

### Issue Classification

- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — Remove `.review/cycle-26/advisor-feedback/step-003.md`

- Deleted `step-003.md` from `.review/cycle-26/advisor-feedback/`. It was a session-account
  copy of Cycle 25 ISSUE-1 fix work and violated the Cycle 24 artifact hygiene rule: advisor
  files belong only to the current cycle step; cross-cycle references use path links only.
- Not replaced. Cycle 25 reset baseline is referenced by path at
  `.review/cycle-25/advisor-feedback/step-003.md` if needed.
- Remaining cycle-26 advisor steps: `step-001.md` (approach), `step-002.md` (completion),
  `step-004.md` (approach agent internal verification account — cycle-26 scope only).

자동 체크: pytest ✅ 524 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅
