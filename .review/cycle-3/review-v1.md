# Codex Review v1

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] `bok-interview` preset cannot produce the required PDF with the real card set
- 위치: `presets/bok-interview.yaml:1`, `scripts/pcli.py:368`
- 분석: The Cycle 3 Sprint Contract requires `uv run pcli build resume --preset bok-interview` to produce a PDF. The preset currently selects all live cards because its filters are effectively empty, and at least `consensus-miami-talk` has no `summary_ko`. The CLI correctly enforces `summary_ko` for `bok`, so the build exits before Typst.
- 재현: `uv run pcli build resume --preset bok-interview --out output\resumes\review-cycle3-bok.pdf` exits `1` with `Missing summary_ko: consensus-miami-talk`.
- 영향: The headline Phase 3 resume preset is not usable against the actual repository data, so the Sprint Contract item "build resume --preset bok-interview produces a PDF" is not met.
- 수정 방향: Either narrow `bok-interview.yaml` to cards that have `summary_ko` or add `summary_ko` to all cards selected by that preset. Keep the pre-Typst failure for genuinely invalid future `bok` selections.

### ISSUE-2 [MEDIUM] Preset filters do not support the YAML list format specified in requirements
- 위치: `scripts/preset.py:55`, `scripts/select.py:61`
- 분석: Requirements show preset filters as YAML lists, for example `tags: [solana, web3]` and `types: [role, project, paper, course]`. `load_preset()` stores `filters.tags` / `filters.types` exactly as loaded. `filter_cards()` then expects comma-separated strings and calls `.split(",")`. A list-valued preset filter will therefore fail at runtime instead of matching cards.
- 영향: This violates the public preset format and makes user-authored presets following `requirements.md` break. It also weakens "Preset load/merge with CLI override" because only the implementation-specific string form is safe.
- 수정 방향: Normalize preset `filters.tags` and `filters.types` at load time: accept either list or comma-separated string and convert to the existing comma-separated string contract, or update `filter_cards()` to accept both shapes.

### ISSUE-3 [LOW] `preset save smoke-test` leaves a sample preset in the real presets directory during review/use
- 위치: `scripts/preset.py:98`
- 분석: `pcli preset save <name>` writes directly to `presets/<name>.yaml`. That is expected behavior, but the Sprint Contract's smoke command uses `smoke-test`, which can leave a tracked project preset behind during validation if the user does not remove it manually.
- 영향: This is not a runtime bug, but it creates project metadata churn during acceptance checks. It is especially noticeable because generated artifacts are ignored, but generated preset YAML is not.
- 수정 방향: Keep command behavior, but document cleanup in review/acceptance steps or use a clearly disposable name in tests. Do not change `preset save` semantics unless the product wants saved presets to be explicit user data only.

## Sprint Contract Check
- `uv run pcli build resume --preset bok-interview --dry-run`: PASS, but warns about missing `summary_ko`
- `uv run pcli build resume --preset bok-interview`: BLOCKED by ISSUE-1
- `uv run pcli build portfolio --preset colosseum`: PASS
- `uv run pcli preset run colosseum`: PASS
- `uv run pcli build portfolio --layout grouped-by-type --dry-run`: PASS
- `uv run pcli build portfolio --layout timeline --dry-run`: PASS
- `uv run pcli preset save smoke-test`: PASS, with cleanup caveat in ISSUE-3
- Existing Phase 1/2 commands without presets: PASS by automated test suite

## Automatic Checks
- `uv run pytest -v`: PASS, 93 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli build resume --preset bok-interview --dry-run`: PASS with warning
- `uv run pcli build portfolio --preset colosseum --dry-run`: PASS
- `uv run pcli build portfolio --layout grouped-by-type --out output\portfolios\review-cycle3-grouped.pptx`: PASS
- `uv run pcli build portfolio --layout timeline --out output\portfolios\review-cycle3-timeline.pptx`: PASS
- `uv run pcli preset run colosseum --out output\portfolios\review-cycle3-preset-run.pptx`: PASS

## Changes Outside Plan
- No LLM, dashboard, or web UI implementation was found.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY
- ISSUE-3: APPLY

RESOLVED: ISSUE-1 — bok-interview preset narrowed to cards with summary_ko
- `presets/bok-interview.yaml`: replaced null filters + max_items with explicit `include_cards: [chainlens-launch, solana-colosseum, pocavault-seoulana]` — the three live cards that have summary_ko.

RESOLVED: ISSUE-2 — Preset filter normalization for YAML list format
- `scripts/preset.py`: added `_normalize_filter()` helper; `load_preset()` now passes `filters.tags` and `filters.types` through it. List → comma-join, str → passthrough, None → None.
- `tests/test_preset.py`: added `test_load_preset_filters_list_format` and `test_load_preset_filters_string_format`.

RESOLVED: ISSUE-3 — Removed accidental smoke-test preset artifact
- `git rm presets/smoke-test.yaml` — no references found; file was a test artifact from acceptance validation.

자동 체크: pytest ✅ 95 passed / ruff check ✅ / ruff format ✅
