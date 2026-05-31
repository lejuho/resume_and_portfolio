# Application Writing Packet Quality Plan

Branch: feature/cycle-26-application-writing-packet-quality

## Summary
Cycle 25 added a browser-only Application Writing handoff export. The packet is functional,
but still generic: cover letters and application answers use the same layout, character-limit
metadata is not prominent, and the evidence/warning sections are not optimized for a human
review pass before submission.

This cycle improves the exported handoff packet's readability and review value without adding
persistence, provider calls, or new card mutation paths.

## Input/Output Spec
- Input:
  - Existing sanitized Application Writing preview object held in browser memory:
    - `output_type`
    - `answer_draft`
    - `target_context_used`
    - `selected_cards`
    - `fact_ledger`
    - `warnings`
    - `character_count`
    - `character_limit`
    - `draft_provenance`
    - `refine_source`
    - `fallback_reason`
    - `ai_guidance`
- Output:
  - Normal:
    - Exported plain-text packet uses a deterministic, readable template.
    - `cover_letter` and `application_answer` packets have distinct headings and context
      emphasis.
    - Character count and limit appear near the verified draft when available.
    - Evidence, warnings, source metadata, and advisory guidance are grouped clearly.
    - Blind-hiring mode continues to expose only safe labels and opaque evidence references.
  - Failure:
    - Existing Cycle 25 error-state reset behavior remains intact.
    - Export remains unavailable before a successful current preview.

## Key Changes
- Frontend:
  - Refactor `_buildHandoffPacket(preview)` in `scripts/static/studio.js` into small,
    deterministic formatting helpers if useful.
  - Add output-type-specific packet titles:
    - `cover_letter`: `Application Writing Handoff — Cover Letter`
    - `application_answer`: `Application Writing Handoff — Application Answer`
  - Add a compact `Draft Metadata` section containing:
    - draft provenance
    - source / fallback reason
    - character count and character limit if present
  - Improve `Target Context`, `Verified Draft`, `Evidence Used`, `Warnings`, and `Advisory`
    section labels for scanability.
  - Preserve browser-only export and existing copy behavior.
- Backend:
  - No backend changes expected.
  - Do not add persistence or provider calls.
- Tests:
  - Add focused packet-format source/snapshot tests in `tests/test_cycle26.py`.
  - Preserve Cycle 25 reset/no-persistence/copy-separation tests.
- Docs:
  - Update `docs/acceptance-studio.md` only if manual acceptance expectations need the clearer
    packet layout.

## Sprint Contract
- Passing criteria:
  - `cover_letter` and `application_answer` packet templates are visibly distinct.
  - Character count and character limit appear in export packet when present.
  - Draft metadata includes provenance and source/fallback values when present.
  - Evidence summary remains derived from sanitized preview fields, not raw `_appCards`.
  - Blind-hiring export remains free of canonical card IDs and protected card-derived markers.
  - AI guidance remains clearly labeled advisory and outside the verified draft section.
  - Export/copy stale-state reset behavior from Cycle 25 remains unchanged.
  - No card file is created or mutated by preview/export.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Test cases:
  - Packet builder contains distinct title strings for cover letter and application answer.
  - Packet builder emits `Draft Metadata`, `Character count`, and `Character limit`.
  - Packet builder emits source/fallback metadata only from preview fields.
  - Packet builder evidence loop uses `selected_cards` safe display fields and not `_appCards`.
  - Blind-hiring fixture/export contract contains opaque refs and excludes canonical card IDs.
  - Existing Cycle 25 tests still pass.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- `character_count` exists but `character_limit` is absent.
- `output_type` is missing or unknown due to future API change.
- `warnings` or `ai_guidance` contain non-string values from future provider adapters.

## Simpler Alternative
Leave the Cycle 25 packet as-is and rely on users to interpret the generic sections. This is
not selected because the packet is now the user's handoff artifact; unclear metadata or mixed
template language can cause submission mistakes even when the underlying preview is safe.

## Assumptions
- Plain text remains the only export format for this cycle.
- Snapshot/source tests are enough because the packet builder is deterministic and browser-only.
- Application Writing export is still a transient handoff artifact, not canonical memory.
- Cycle 25's stale-state reset is part of the baseline and must not regress.

## Review Guidance
### Enumeration Needed
Review every packet/copy/export surface:

```bash
rg -n "_buildHandoffPacket|exportAppPacket|copyAppDraft|_resetAppHandoffState|_appLastPreview|selected_cards|fact_ledger|character_count|character_limit" scripts/static scripts/templates tests docs
```

Expected surfaces:
- `scripts/static/studio.js`
- `scripts/templates/studio.html` only if UI copy changes
- `tests/test_cycle25.py`
- new `tests/test_cycle26.py`
- `docs/acceptance-studio.md` if manual acceptance changes

### Verification Method Guide
- Packet format:
  - Source/snapshot-style tests are sufficient if `_buildHandoffPacket()` remains deterministic
    and browser-only.
- Blind-hiring safety:
  - Must be verified against sanitized preview fields or source contract proving no raw
    `_appCards` read.
- No-persistence:
  - Existing backend/file-system tests are sufficient unless a backend endpoint is added.
  - If any backend code changes, add a file-system regression proving no `cards/` mutation.
- Stale-state reset:
  - Re-run Cycle 25 reset tests and verify `_showAppError()` still clears handoff state.
