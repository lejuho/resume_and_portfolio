# Application Writing Export / Handoff Plan

Branch: feature/cycle-25-application-writing-export

## Summary
Cycle 21 introduced the Application Writing preview, Cycle 23 clarified the verified-draft
copy flow, and Cycle 24 hardened review artifact hygiene. The remaining user-facing gap is
handoff: after generating a verified draft, the user can copy only the draft text, but cannot
export a complete, reviewable application packet containing the draft, target context, and
evidence summary.

This cycle adds a non-persistent export/handoff affordance for Application Writing. It must
help the user carry the generated preview outside Studio without creating or mutating Career
Memory cards.

## Input/Output Spec
- Input:
  - Existing Studio Application Writing preview state returned by
    `POST /api/studio/application-preview`.
  - Existing browser-side generated preview fields:
    - `answer_draft`
    - `output_type`
    - `target_context_used`
    - `fact_ledger`
    - `selected_cards`
    - `warnings`
    - `draft_provenance`
    - `refine_source` / `fallback_reason`
- Output:
  - Normal:
    - User can export or copy a handoff packet from the current preview.
    - Packet contains the verified draft plus non-mutating context/evidence metadata.
    - Packet preserves blind-hiring opaque refs and safe labels.
    - Packet does not include AI guidance in the same copy path as the verified draft unless
      clearly labeled as advisory and not part of the submitted answer.
  - Failure:
    - If no preview has been generated, export action is hidden or disabled.
    - If browser download APIs are unavailable, the UI falls back to copying a packet or shows
      a safe actionable error.

## Key Changes
- Frontend:
  - Update `scripts/templates/studio.html` to add an Application Writing handoff/export
    control near the existing verified draft copy action.
  - Update `scripts/static/studio.js` to retain the last successful application preview in
    browser memory and build a deterministic plain-text handoff packet from sanitized preview
    fields.
  - Keep the existing `Copy Verified draft to clipboard` behavior unchanged.
  - Do not add any card-save, card-create, or raw-memory write flow.
- Backend:
  - No new provider call.
  - No persistence endpoint unless implementation proves browser-only export is insufficient.
  - If a backend endpoint is added, it must accept only the already sanitized preview payload
    and return a transient rendered artifact without writing to `cards/`.
- Tests:
  - Add focused source/API tests for the export control, packet composition contract, and
    no-persistence guarantee.
  - Preserve existing Application Writing tests from cycles 21-23.
- Docs:
  - Update `docs/acceptance-studio.md` Application Writing acceptance rows to include the
    handoff/export behavior.

## Sprint Contract
- Passing criteria:
  - A generated Application Writing preview exposes a clear export/handoff action.
  - The existing verified-draft copy button still copies only `answer_draft`.
  - The export packet includes:
    - output type
    - target context used
    - verified draft
    - selected evidence summary from safe preview fields
    - warnings and source/fallback metadata when present
  - Blind-hiring export uses opaque card refs and safe display labels only.
  - AI guidance is excluded from the draft copy path and, if exported, is clearly labeled as
    advisory rather than submitted answer text.
  - Application Writing export creates no new card and mutates no existing card.
- Automatic checks:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests`
  - `uv run ruff format --check scripts tests`
  - `uv run pcli validate`
- Test cases:
  - Source/DOM contract: Studio HTML exposes the handoff/export button and explanatory copy.
  - JS contract: export packet builder reads from the last successful preview and not from raw
    live-card state.
  - Copy separation: existing draft-copy path still writes only `_appDraftText`.
  - Blind-hiring: packet text contains opaque refs such as `C1`, and does not contain protected
    canonical card IDs from sanitized preview fixtures.
  - No-persistence: generating/exporting a packet does not create files under `cards/`.
  - Empty state: export action is unavailable or safe-error-only before preview generation.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates
- Browser lacks `Blob`, `URL.createObjectURL`, or clipboard support.
- Preview is regenerated after export; export must use the latest successful preview only.
- Warning/advisory fields contain unexpected non-string values from future API changes.

## Simpler Alternative
Only keep the existing verified-draft copy button and ask users to manually copy evidence
metadata from the page. This is not selected because it loses provenance during handoff and
makes blind-hiring-safe evidence references easy to omit or miscopy.

## Assumptions
- A browser-only plain-text export is sufficient for this cycle; PDF/DOCX generation is out of
  scope.
- Exported packet is a handoff artifact, not canonical project data.
- Application Writing remains preview-only and must not write target context, generated draft,
  or export packets into Career Memory cards.
- Existing preview response is already sanitized by the server boundary added in Cycle 21.

## Review Guidance
### Enumeration Needed
Review every Application Writing path that can copy, export, render, or persist generated text:

```bash
rg -n "Application Writing|application-preview|answer_draft|ai_guidance|copyAppDraft|clipboard|download|Blob|cards/" scripts tests docs
```

Expected surfaces:
- `scripts/templates/studio.html`
- `scripts/static/studio.js`
- `scripts/dashboard.py` only if backend support is added
- `tests/test_cycle21.py`
- `tests/test_cycle22.py`
- `tests/test_cycle23.py`
- new `tests/test_cycle25.py`
- `docs/acceptance-studio.md`

### Verification Method Guide
- UI hook/copy checks:
  - Static HTML/JS source tests are sufficient for DOM IDs, button labels, explanatory copy,
    and draft-copy separation.
- Export packet composition:
  - Source tests are acceptable if packet builder is deterministic and visible in
    `studio.js`.
  - Prefer a direct JS-source contract test over fragile browser automation in this cycle.
- No-persistence:
  - API/file-system test is required if any backend endpoint is added.
  - If implementation stays browser-only, assert no new backend route and preserve existing
    `application_preview_does_not_create_card_file` behavior.
- Blind-hiring export:
  - Must use adversarial sanitized preview fixture or source contract showing packet builder
    consumes preview `fact_ledger`/`selected_cards`, not raw `/api/cards` records.
