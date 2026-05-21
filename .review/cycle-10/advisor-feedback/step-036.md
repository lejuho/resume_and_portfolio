# Step 036 — Cycle-10 Dashboard Detail Editing Approach check

Cycle: 10
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Client-side parsing (split/strip/filter in JS for tags) — keeps server schema-strict.
2. Nested dicts/lists serialize fine via `frontmatter.dumps()` (PyYAML handles them).
3. Per-visual `Path.exists()` on GET is fine for local MVP — O(n), n small.
4. Split dashboard.html >500 lines: extract authoring JS to `scripts/static/dashboard.js`. Enforces 500-line rule and isolates testable logic.
5. Add `visual_hints` only when `visuals` key exists in fields; skip otherwise.
6. Order PUT tests: valid-path first, then 422 cases verifying file unchanged.

## Sonnet Response
- 진행: `scripts/static/dashboard.js` 신규 생성 (기존 JS + 신규 authoring detail 함수).
- 진행: `dashboard.html` → HTML 구조 + `<script src>` + 최소 inline script만 유지.
- 진행: `dashboard.py` → `static_folder="static"` + GET에 `visual_hints` 추가.
- 진행: PUT tests for tags/metrics/evidence/visuals.
- 구현 시작.
