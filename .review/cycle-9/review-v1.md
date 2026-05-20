# Codex Review v1

## Verdict

BLOCKED

Cycle 9 authoring MVP is implemented and the existing automated suite passes, but the new write path currently allows card identity invariants to be broken. Because cards are file-backed and `id` uniqueness / filename matching are core schema rules, this should be fixed before merge.

## Findings

### 1. Duplicate card IDs can be created in a different month

Severity: High

In `scripts/dashboard.py:168`, duplicate detection only checks whether the exact computed target path exists:

```python
if target.exists():
    return jsonify({"ok": False, "error": f"card {card_id!r} already exists"}), 409
```

This rejects `2026-05-sample-card.mdx` only when the new card also computes to `2026-05-sample-card.mdx`. It does not reject the same `id` under another month, for example `2026-06-sample-card.mdx`.

Reproduced with Flask test client:

```text
POST /api/cards
id=sample-card
period_start=2026-06-01

=> 201 {'id': 'sample-card', 'ok': True, 'path': 'cards\\2026-06-sample-card.mdx'}
files: ['2026-05-sample-card.mdx', '2026-06-sample-card.mdx']
```

This violates the repo rule that card IDs are unique. It also means a dashboard-created card can immediately make `pcli validate` fail for the repo.

Recommended fix:

- Check `cards/????-??-{card_id}.mdx` before writing, not only `target.exists()`.
- Add a regression test where an existing ID is created with a different `period_start` month and must return `409`.

### 2. PUT can change `id`, creating filename/frontmatter mismatch

Severity: High

In `scripts/dashboard.py:217`, all incoming fields are blindly merged into existing frontmatter:

```python
for k, v in incoming_fields.items():
    merged[k] = v
```

Because `id` is not protected, this request succeeds:

```text
PUT /api/cards/sample-card
fields.id=renamed-card

=> 200 {'id': 'sample-card', 'ok': True, 'path': 'cards\\2026-05-sample-card.mdx'}
```

The resulting file is still named `2026-05-sample-card.mdx`, but its frontmatter starts with `id: renamed-card`. That violates the filename/id subset rule and can break lookup/validation behavior.

Recommended fix:

- Reject updates where `incoming_fields["id"]` exists and differs from `card_id`.
- Prefer making `id` immutable in Cycle 9. Rename/move can be a later explicit operation.
- Add a regression test that `PUT /api/cards/<id>` with a different `fields.id` returns `400` or `422` and leaves the file unchanged.

## Checks

- `uv run pytest -v`: PASS, 180 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Notes

- The dashboard UI hooks and baseline create/edit endpoints are present.
- Existing build/read-only dashboard behavior appears intact.
- I did not run browser visual QA in this pass; the blockers above are API/data-integrity issues.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Duplicate card ID across months rejected via glob pre-check
- `api_card_create`: added `any(cards_dir.glob(f"????-??-{card_id}.mdx"))` check before `_write_card_atomic()`. Returns 409 for any existing month variant.
- Regression test: `test_create_card_duplicate_id_different_month` — POST with `id=sample-card, period_start=2026-06-01` → 409, `2026-06-sample-card.mdx` not created.
- Note: `card_id` validated by `_KEBAB_RE` before glob, so no glob metachar injection possible.

RESOLVED: ISSUE-2 — PUT id rename rejected; id is now immutable
- `api_card_update`: added guard before merge loop — `if "id" in incoming_fields and incoming_fields["id"] != card_id: return 400`.
- Regression tests:
  - `test_update_card_id_change_rejected` — PUT `fields.id="renamed-card"` → 400, file unchanged.
  - `test_update_card_same_id_accepted` — PUT `fields.id="sample-card"` (same) → 200.

자동 체크: 183/183 tests pass ✅ / ruff clean ✅
