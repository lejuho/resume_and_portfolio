# Cycle 31 Quality, Specification, and Test Audit Report

## Verdict: PASS

No workflow-invalidating defects found. Debt register and follow-up recommendations below.

---

## 1. Baseline

| Item | Value |
|---|---|
| Audit date | 2026-06-05 |
| Branch | `feature/cycle-31-quality-spec-audit` |
| Total automated tests | 612 |
| Test warnings | 7 (all `datetime.utcnow()` deprecation in `evaluate_studio_grounding.py`) |
| Lint | `ruff check`: PASS |
| Format | `ruff format --check`: PASS |
| Card validation | `pcli validate`: PASS (1 non-fatal warning: `test` card has empty evidence) |
| Resume dry-run | 4 cards selected; no PDF created |
| Portfolio dry-run | 4 cards selected for portfolio; no PPTX created |

---

## 2. Cycle 21–30 Requirement Trace

| Cycle | Branch | Status | Behavior | Req reference | Automated evidence | Gaps |
|---|---|---|---|---|---|---|
| 21 | `feature/cycle-21-application-writing-harness` | ready_to_merge | `POST /api/studio/application-preview`; fact ledger; blind-hiring redaction; server-composed draft | D-009 | `tests/test_cycle21.py` (PT-APP-001–006) | Browser acceptance PENDING |
| 22 | `feature/cycle-22-studio-ui-smoke-tests` | ready_to_merge | Studio UI contract smoke tests; `/api/cards` array shape regression | D-010 | `tests/test_cycle22.py` | No functional change; smoke only |
| 23 | `feature/cycle-23-application-writing-ux-polish` | ready_to_merge | Richer card selector metadata; empty/error labels; copy-button label consistency | D-010 | `tests/test_cycle23.py` | Browser acceptance PENDING |
| 24 | `feature/cycle-24-artifact-hygiene` | ready_to_merge | `.read-counter` gitignore; no-cross-cycle advisor hygiene; `test_real_tree_advisor_hygiene` | Process quality | `tests/test_cycle24.py` | No product behavior |
| 25 | `feature/cycle-25-application-writing-export` | ready_to_merge | Browser-only handoff export; `_resetAppHandoffState`; no persistence | D-011 | `tests/test_cycle25.py` (PT-APP-EXP-001–004) | Browser acceptance PENDING |
| 26 | `feature/cycle-26-application-writing-packet-quality` | ready_to_merge | `_packetTitle`; Draft Metadata; `_packetSafeText` | D-012 | `tests/test_cycle26.py` | Browser acceptance PENDING |
| 27 | `feature/cycle-27-workspace-route-shell` | ready_to_merge | `/workspace` route; two-pane shell; `workspace.js` IIFE | D-013 | `tests/test_cycle27.py` (TC-WS-001–005) | Browser acceptance PENDING |
| 28 | `feature/cycle-28-workspace-design-tokens` | ready_to_merge | `:root` token block; 400/500 weights; accent/surface tokenization; selected-state card | D-014 | `tests/test_cycle28.py` (TC-WS-006–011) | Browser acceptance PENDING |
| 29 | `feature/cycle-29-workspace-dark-polish` | ready_to_merge | OS dark media query; manual theme toggle; localStorage; hover/focus states | D-015 | `tests/test_cycle29.py` (TC-WS-009–013) | Browser acceptance PENDING |
| 30 | `feature/cycle-30-workspace-fit-signals` | ready_to_merge | `_wsTokenize`/`_wsCardTokens`/`_wsUpdateCoverage`; target listeners; card disclosure; coverage panel | D-016, D-017 | `tests/test_cycle30.py` (TC-WS-014–020) | Browser acceptance PENDING |

---

## 3. Design Conformance

Source: `docs/design-system-workspace.md §7`.

| Rule | Status | Evidence |
|---|---|---|
| Sentence case / no uppercase transform | ✅ PASS | Source test (Cycles 27–29) |
| No font-weight 600/700 | ✅ PASS | Source test (Cycle 28) |
| `:root` token block complete | ✅ PASS | Source test (Cycle 28) |
| Raw accent values absent outside `:root` | ✅ PASS | Source test (Cycle 28, ISSUE-1 fix) |
| Dark OS media query | ✅ PASS | Source test (Cycle 29) |
| Manual dark toggle + localStorage | ✅ PASS | Source test (Cycle 29 user addition) |
| Card hover / selected states | ✅ PASS | Source test (Cycle 29) |
| Checkbox focus ring (custom rule) | ✅ PASS | Source test (Cycle 29) |
| Generate button focus ring | ⚠ Browser default | No `.ws-generate-btn:focus-visible` rule; `.ws-theme-toggle:focus-visible` applies to theme toggle only — see DEBT-006 |
| Card disclosure (line-clamp + expand/collapse) | ✅ PASS | Source test (Cycle 30 user addition) |
| Overflow containment (`min-width: 0`, `overflow-wrap`) | ✅ PASS | Source test (Cycle 30) |
| Disclosure stops propagation | ✅ PASS | Source test (Cycle 30) |
| `--ws-coverage-muted` token (was hard-coded `#4a5568`) | ✅ PASS | Tokenized in Cycle 29 |
| `--ws-field-border` / `--ws-border-strong` token | ✅ PASS | Tokenized in Cycle 29 |
| WCAG AA contrast (dark mode) | ⏳ PENDING | Browser/manual check required |
| Keyboard navigation end-to-end | ⏳ PENDING | Browser/manual check required |

---

## 4. Test Inventory and Gap Analysis

### 4.1 Evidence Strength Classification

Counting method: `grep -c "^def test_" tests/test_cycleNN.py` on the working tree at this commit.
The ten-cycle sum (236) is less than the 612 full-suite total because other test files (e.g.,
shared helpers, non-cycle test modules) are not listed here.

| Test file | Count | Behavior-execution | API integration | Source-inspection | Notes |
|---|---|---|---|---|---|
| `test_cycle21.py` | 94 | ✅ | ✅ | ✅ | Blind-hiring serialization fully behavior-tested |
| `test_cycle22.py` | 6 | ✅ | ✅ | — | Route/response shape tests |
| `test_cycle23.py` | 7 | ✅ | ✅ | minimal | UX polish |
| `test_cycle24.py` | 5 | — | — | ✅ | Hygiene only; `test_real_tree_advisor_hygiene` walks real tree |
| `test_cycle25.py` | 22 | partial | ✅ | ✅ | No-persistence test is behavior; export flow is source-only |
| `test_cycle26.py` | 14 | — | — | ✅ | All source-inspection (packet format) |
| `test_cycle27.py` | 23 | ✅ | ✅ | ✅ | Route tests are behavior; JS source tests are source-only |
| `test_cycle28.py` | 19 | ✅ | ✅ | ✅ | Route regression behavior; token tests are source-only |
| `test_cycle29.py` | 21 | ✅ | ✅ | ✅ | Route regression behavior; dark-mode and JS tests are source-only |
| `test_cycle30.py` | 25 | ✅ | ✅ | ✅ | Route regression behavior; fit/disclosure are source-only |

### 4.2 Source-Inspection-Only Coverage (Known Gap)

The following behaviors are verified only by asserting CSS/JS string presence in the served
static files. They cannot prove runtime interaction without a browser test:

- Workspace fit-percentage computation (keyboard + real DOM)
- Card hover, selected, and focus-visible rendering
- Card disclosure expand/collapse toggle
- Disclosure click stopping propagation
- Theme toggle `localStorage` persistence across page loads
- Matched-terms rendering in `ws-coverage-terms`
- Long-text containment preventing horizontal overflow

**Risk:** Low. All source tests assert the implementation surface directly; the behaviors
are deterministic and small. Browser/manual verification is the gap, not implementation doubt.

### 4.3 No Duplicate Assertions Found

Cross-cycle regression tests (e.g., `Array.isArray(data)`, `status === "live"`, route 200s)
are intentionally repeated in each cycle file as isolation regression guards. This is
deliberate, not accidental duplication.

### 4.4 Test Quality Notes

- `test_cycle26.py` — 14 tests are all source-string assertions on `_buildHandoffPacket`.
  This is appropriate for a pure output-format cycle with no runtime state; the risk of
  false-pass is low since the function is only reached by the export path.
- `test_cycle24.py::test_real_tree_advisor_hygiene` — this test walks the real working tree,
  not a fixture. It is intentionally a live-hygiene check and must remain in the test suite.
- The `datetime.utcnow()` deprecation in `evaluate_studio_grounding.py` is a pre-existing
  warning from a benchmarking script. It does not affect product behavior.

---

## 5. Automated Quality Results

| Check | Result |
|---|---|
| `uv run pytest -v` | 612 passed, 7 warnings |
| `uv run ruff check scripts tests` | All checks passed |
| `uv run ruff format --check scripts tests` | All files formatted |
| `uv run pcli validate` | PASS (1 non-fatal: `test` card empty evidence) |
| `uv run pcli --help` | Commands: new, validate, ls, show, dashboard, build, preset, llm |
| `uv run pcli dashboard --help` | PASS |
| `uv run pcli build resume --dry-run` | 4 cards selected; no PDF created |
| `uv run pcli build portfolio --dry-run` | 4 cards selected; no PPTX created |
| `uv run pyright scripts/` | Not run — pyright not confirmed available in venv |

### Manual / Browser Checks

| Check | Result |
|---|---|
| `/dashboard` route smoke | PENDING — browser check not performed in this session |
| `/studio` route smoke | PENDING |
| `/workspace` route smoke | PENDING |
| Workspace card load, selection, target, fit, preview | PENDING |
| Workspace light/dark, keyboard, long-text | PENDING |
| Studio Application Writing preview/export (mock mode) | PENDING |
| External provider checks | SKIP — no live key in audit environment |

---

## 6. Defect / Debt Register

| ID | Severity | Type | Description | Affected requirement | Proposed follow-up |
|---|---|---|---|---|---|
| DEBT-001 | Low | Test quality | All Workspace JS interaction tests are source-inspection only; no browser-execution evidence for fit computation, disclosure, hover, theme persistence | TC-WS-010–019 | Add Playwright or similar browser test suite in a dedicated quality cycle |
| DEBT-002 | Low | Spec gap | `docs/design-system-workspace.md §7` notes WCAG AA contrast as PENDING; dark mode accent lightening was applied but not formally verified | `requirements-dashboard.md §9` | Manual contrast audit; consider accessibility cycle |
| DEBT-003 | Info | Process | The `evaluate_studio_grounding.py` script emits `datetime.utcnow()` deprecation warnings (Python 3.13). Not a blocker. | n/a | Maintenance cycle; replace with `datetime.now(UTC)` |
| DEBT-004 | Info | Spec gap | `docs/test-cases.md` TC-WS-017 through TC-WS-019 require browser verification; these are marked ⚠ but have no acceptance-date evidence | TC-WS-017–019 | Workspace manual acceptance run |
| DEBT-005 | Low | Spec drift | `requirements-dashboard.md §8.6` previously said "future" for Application Writing; Cycle 31 audit updated its status. Section still uses forward-looking phrasing in some sub-bullets. | D-009 | Minor wording cleanup in next requirements refresh |
| DEBT-006 | Low | Design gap | Generate button has no custom focus ring; `.ws-generate-btn:focus-visible` is absent. The foreground color `color: #fff` is a raw value outside `:root` (one-off; not a repeated-value violation). Both are documented exceptions. | D-014 | Add `--ws-btn-text` token and focus rule in Cycle 32 or a future design-polish cycle |

No HIGH or CRITICAL severity defects found. No current public workflow (`/dashboard`, `/studio`,
`/workspace`) is broken or invalidated.

---

## 7. Route and API Surface Audit

Routes in `scripts/dashboard.py` as of Cycle 30 baseline:

| Route | Method | Surface | Status |
|---|---|---|---|
| `/` | GET | Dashboard | Active |
| `/api/cards` | GET | Shared API | Active |
| `/api/cards/<card_id>` | GET | Shared API | Active |
| `/api/cards` | POST | Shared API | Active |
| `/api/cards/<card_id>` | PUT | Shared API | Active |
| `/api/build` | POST | Shared API | Active |
| `/dashboard` | GET | Admin Dashboard | Active |
| `/studio` | GET | Career Studio | Active |
| `/workspace` | GET | Workspace | Active — added Cycle 27 |
| `/api/studio/ai-status` | GET | Studio API | Active |
| `/api/studio/ai-check` | POST | Studio API | Active |
| `/api/studio/refine` | POST | Studio API | Active |
| `/api/studio/save` | POST | Studio API | Active |
| `/api/studio/application-preview` | POST | Application Writing API | Active — added Cycle 21 |

No undocumented mutation routes found for Workspace. No `/api/workspace` endpoint exists.

---

## 8. Specification Compliance Summary

| Document | Before Cycle 31 | After Cycle 31 |
|---|---|---|
| `requirements-dashboard.md` | Covered through Cycle 21 (D-009 only) | Updated through Cycle 30 (D-010–D-017); §2.3 Workspace added |
| `docs/test-cases.md` | Covered through Cycle 21 (`PT-APP-*`) | Added `PT-APP-EXP-*` (Cycles 25–26) and `TC-WS-001–020` (Cycles 27–30); trace table updated |
| `docs/acceptance-studio.md` | Covered through Cycle 21 (Application Writing Acceptance) | Added Workspace acceptance section (Cycles 27–30) |
| `docs/design-system-workspace.md` | Did not exist | Created; token registry, IA, interaction states, accessibility, conformance table, future-direction section |
| `docs/design-system-studio.md` | Covers Studio; no Workspace | Unchanged; Workspace design tracked separately |

---

## 9. Next-Cycle Recommendations

### Recommended: Cycle 32 — Workspace Browser Test Coverage

Convert TC-WS-010 through TC-WS-019 (currently source-inspection only) to Playwright or
similar browser-driven assertions. Specific targets:
- Fit-percentage computation with real DOM input events
- Card disclosure expand/collapse state
- Theme toggle `localStorage` persistence
- Long-text containment (no horizontal scroll)
- Keyboard focus-ring visibility on checkbox, buttons, inputs

### Conditionally Ready: Workspace Theme Coverage Feature (`feature/cycle-31-theme-coverage-recommendations`)

The preserved branch plan (`git show 2c2bf62 -- .review/cycle-31/plan.md`) defines a purely
deterministic, client-side cycle with no AI dependency:

- A **manual required-themes input** (comma-separated; trimmed, case-folded, de-duplicated).
- Coverage formula: `round(covered required theme count / required theme count * 100)`.
- Recommendations: unselected live cards covering ≥1 missing required theme, ranked by
  gap-coverage count descending then original live-card order.
- An `All` / `Recommended` filter that keeps selected cards visible.
- **No S0 research adapter, no S1 AI tagging, no persistent `themes` schema, no backend
  mutation.** S0/S1 work is explicitly deferred to a later cycle.

This cycle has no dependency on browser test coverage — it is client-side JS and can be
implemented and source-tested independently. The branch and cycle number should be updated
before resumption; the existing plan history does not need to be rewritten.

### Maintenance (Low Priority): `datetime.utcnow()` deprecation

Replace `datetime.utcnow()` with `datetime.now(datetime.timezone.utc)` in
`scripts/evaluate_studio_grounding.py` to eliminate the 7 deprecation warnings.
