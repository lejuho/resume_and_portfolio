# Codex Review v2

## Verdict

BLOCKED

The v1 blockers are mostly addressed: missing relative visual paths are now rejected before write, and the create flow hides detail-only sections instead of silently dropping entered detail fields. However, the new visual-path validation still accepts existing absolute paths outside the repository, which defeats the intended local `assets/` reference model and can leave cards with non-portable visual references.

## Fixed Since v1

- `PUT /api/cards/<id>` now rejects missing relative visual paths with `422`.
- Rejected missing-visual updates leave the original file unchanged.
- New-card mode hides metrics/evidence/visual/body sections and shows a detail hint, avoiding silent detail-field loss during create.
- Regression tests were added for missing visual rejection, existing visual success, and the detail hint.

## Finding

### 1. Existing absolute visual paths outside the repo are accepted

Severity: High

The new visual existence check uses:

```python
if not (REPO_ROOT / v["path"]).exists():
    ...
```

On Windows and pathlib generally, if `v["path"]` is absolute, `REPO_ROOT / absolute_path` resolves to the absolute path, not a path under the repo. That means a user can save a visual reference to a file outside the project as long as it exists at save time.

Reproduced with Flask test client:

```text
missing-relative 422 {'error': 'visual path does not exist: assets/missing.png', 'ok': False}
unchanged True
repo-errors-after-reject []

outside-absolute 200 {'id': 'sample-card', 'ok': True, 'path': 'cards\\2026-05-sample-card.mdx'}
```

Impact:

- Cards can contain machine-specific absolute paths.
- The repo is no longer self-contained even though Cycle 10 scope says inputs are local assets under `assets/`.
- A card may validate on one machine but fail on another, or fail later after the outside file is moved/deleted.

Recommended fix:

- Reject absolute visual paths.
- Resolve the candidate path and require it to stay under `REPO_ROOT / "assets"` or at least under `REPO_ROOT`.
- Add regression tests:
  - absolute visual path outside repo returns `422` and leaves file unchanged
  - `../outside.png` traversal returns `422`
  - existing `assets/...` path still succeeds

## Checks

- `uv run pytest -v`: PASS, 195 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS on current real repo
- `uv run pcli dashboard --help`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build portfolio --dry-run`: PASS

## Notes

- Browser visual QA was not run in this pass.
- Existing Cycle 8/9 dashboard invariants still appear covered.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY

### Applied

RESOLVED: ISSUE-1 — absolute and traversal visual paths now rejected before write
- `scripts/dashboard.py`: replaced single existence check with three-guard sequence: (1) reject absolute paths, (2) reject paths that resolve outside REPO_ROOT, (3) reject non-existent paths; all three fire before `_write_card_atomic`, leaving file unchanged
- `tests/test_dashboard.py`: added `test_update_card_absolute_visual_path_rejected` (sys.executable → 422, file unchanged), `test_update_card_traversal_visual_path_rejected` (`../outside.png` → 422, file unchanged)
자동 체크: pytest 197 ✅ / ruff check ✅ / ruff format ✅
