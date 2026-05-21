# Codex Review v1

## Verdict

BLOCKED

Cycle 10 adds the intended detail editor surface and the existing automated suite passes, but the new visual editing path can save a card that immediately fails normal repository validation. Since the sprint contract says saved cards must remain valid and invalid detail edits must not partially overwrite the card, this should be fixed before merge.

## Findings

### 1. Missing visual paths are saved successfully and make the repo invalid

Severity: High

`PUT /api/cards/<id>` validates only the Pydantic `Card` model before writing:

```python
Card.model_validate(merged)
```

That schema accepts visual shape, but normal repo validation also checks visual file existence in non-portfolio mode. Because the dashboard update path does not run that repo-level visual existence check before `_write_card_atomic()`, a user can save:

```json
{
  "fields": {
    "visuals": [
      {"path": "assets/missing.png", "role": "hero", "caption": "Missing"}
    ]
  },
  "body": ""
}
```

Reproduced with Flask test client:

```text
put-missing-visual 200 {'id': 'sample-card', 'ok': True, 'path': 'cards\\2026-05-sample-card.mdx'}
repo-errors [ValidationError('... visual path does not exist: assets/missing.png')]
```

Impact:

- A successful dashboard save can make `uv run pcli validate` fail.
- This violates Cycle 10's plan:
  - "saved cards remain valid according to the existing schema"
  - "invalid detail edits are rejected without partially overwriting the card"
  - "User can edit visual references and see missing/existing status"

Recommended fix:

- Before writing updates that include `visuals`, reject paths whose resolved target does not exist under the repo.
- Keep portfolio build fallback behavior unchanged; this dashboard authoring path should not save invalid visual references silently.
- Add regression tests:
  - `PUT /api/cards/<id>` with missing visual path returns `422`.
  - Original file remains unchanged.
  - `PUT /api/cards/<id>` with an existing asset path succeeds.

### 2. New-card form shows detail fields but create drops them

Severity: Medium

The new-card UI clears and displays tags/metrics/evidence/visuals/body fields in `openNew()` (`scripts/static/dashboard.js:138`), but `saveCard()` sends only basic fields during create (`scripts/static/dashboard.js:235-242`):

```javascript
const body = {
  id,
  title,
  type,
  period_start,
  status,
  summary,
};
```

Any tags, metrics, evidence, visuals, or narrative entered before clicking Save are silently discarded.

Impact:

- Users can type detail data into visible controls and lose it on create.
- This is especially confusing because Cycle 10's visible UI suggests detail editing is available in the authoring panel.

Recommended fix:

- Either include the same detail fields in `POST /api/cards`, or hide/disable detail sections while creating a new card and show a clear "create first, then edit details" flow.
- Add a test or UI hook assertion for whichever behavior is chosen.

## Checks

- `uv run pytest -v`: PASS, 192 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS on current real repo
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Notes

- I did not run browser visual QA in this pass.
- Static JS is served correctly by Flask.
- Existing Cycle 8/9 invariants appear intact in the test suite.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — visual path existence enforced in PUT handler
- `scripts/dashboard.py`: added check after `Card.model_validate(merged)`, guarded by `if "visuals" in incoming_fields` so unrelated PUTs are not blocked by pre-existing invalid paths; returns 422 + leaves file unchanged on missing path
- `tests/test_dashboard.py`: added `test_update_card_missing_visual_path_rejected` (422, file unchanged), `test_update_card_existing_visual_path_succeeds` (200); updated `test_update_card_visuals` to create asset file before PUT
자동 체크: pytest 195 ✅ / ruff check ✅ / ruff format ✅

RESOLVED: ISSUE-2 — new-card form hides detail sections ("create first, then edit details")
- `scripts/templates/dashboard.html`: added `id` attrs to 3 dyn section divs, added `#af-detail-hint` div (hidden by default)
- `scripts/static/dashboard.js`: `openNew()` hides metrics/evidence/visuals/body sections + shows hint; `openEdit()` restores them
- `tests/test_dashboard.py`: added `test_dashboard_has_detail_hint` (checks `af-detail-hint` in GET / response)
자동 체크: pytest 195 ✅ / ruff check ✅ / ruff format ✅
