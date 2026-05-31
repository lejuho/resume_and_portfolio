# Advisor Feedback — Cycle 26, Step 001

## Type
Approach check — Application Writing Packet Quality (`_buildHandoffPacket`).

## Question (judgment points)
1. Inline title switch vs `_packetTitle(output_type)` helper.
2. `Draft Metadata` emit-always vs only-when-present.
3. Non-string guard: `String(item)` vs `typeof item === "string" ? item : String(item)`.
4. Test strategy: eval vs source/snapshot substring assertions.
5. Advisor step file location.

## Advisor Response
1. `_packetTitle(output_type)` helper — single site, but isolates switch/fallback for testability.
2. Emit `Draft Metadata` only when ≥1 field present — avoids empty-section noise.
3. `typeof item === "string" ? item : String(item)` — explicit; shared helper for warnings + guidance.
4. Source/snapshot: assert literal substrings in function source — no eval; matches plan's stated sufficiency.
5. Save to `.review/cycle-26/advisor-feedback/step-001.md`.

## Decision / Application
- All five accepted as-is. No items ignored.
- Added `_packetTitle` and `_packetSafeText` helpers in `scripts/static/studio.js`.
- `Draft Metadata` built into a `meta[]` array, emitted only when non-empty.
- Character count/limit: both when limit present, count-only `else if` branch otherwise.
- Tests in `tests/test_cycle26.py` use source-substring (snapshot) assertions, no eval.

## Auto-checks
- `uv run pytest` ✅ (524 passed; cycle26 16, cycle25 20)
- `uv run ruff check scripts tests` ✅
- `uv run ruff format --check scripts tests` ✅
- `uv run pcli validate` ✅ (no errors)
