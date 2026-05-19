# Codex Review v1

## Verdict
BLOCKED

## Findings

### ISSUE-1 [HIGH] `--until YYYY-MM` excludes most cards in the requested month
- 위치: `scripts/select.py:61`
- 분석: `_parse_ym()` converts `YYYY-MM` to the first day of that month, then the `until` filter keeps only cards with `period.start <= until_date`. This makes `--until 2026-04` include only cards starting on or before `2026-04-01`, excluding a valid April card like `pocavault-seoulana` (`2026-04-15`).
- 재현: `uv run pcli ls --until 2026-04` returns only the 2025 cards and omits `pocavault-seoulana`.
- 영향: Sprint Contract says `pcli ls` must support `--until`; requirements define `--until <YYYY-MM>` as a month filter, so users will expect the entire month to be included.
- 수정 방향: Treat `until` as month-inclusive. For example, compare `(year, month)` tuples, compute the first day of the next month and use `< next_month`, or compute the actual last day of the requested month.

### ISSUE-2 [MEDIUM] `pcli show` does not support filename slug lookup
- 위치: `scripts/pcli.py:264`, `scripts/card.py:237`
- 분석: The plan requires `show <slug>` to resolve "by id or filename slug", but `cmd_show()` calls `repo.get(slug)`, and `CardRepo.get()` only matches exact `card.id`. Passing the filename stem fails even when the card exists.
- 재현: `uv run pcli show 2026-05-pocavault-seoulana` exits `1` with `Card not found`.
- 영향: Sprint Contract line item for `show <slug>` is not met. This also makes the CLI less forgiving for users copying names directly from `cards/*.mdx`.
- 수정 방향: Either support both exact `id` and filename stem (`YYYY-MM-<id>`) in lookup, or tighten the plan/docs to say only card id is supported. Given the Sprint Contract, implementation should support both.

### ISSUE-3 [MEDIUM] `pcli validate <slug>` cannot target an invalid card with a valid id
- 위치: `scripts/pcli.py:128`, `scripts/card.py:237`
- 분석: `validate <slug>` first calls `repo.get(slug)`, but `repo.get()` only searches successfully parsed cards. If a card has a valid id but fails validation for another reason, such as a too-long summary, it is stored only in `repo.errors`; `validate <slug>` reports `Card not found` instead of showing that card's validation error.
- 영향: Requirements specify `pcli validate [<slug>]` for a specific card. The current implementation works for valid cards with warnings, but fails at the exact moment a user most needs targeted validation: when that specific card is broken.
- 수정 방향: When `slug` is provided, filter both loaded cards and validation errors by filename stem and/or parseable frontmatter id. Do not require the card to be fully valid before reporting its validation errors.

## Sprint Contract Check
- Repository bootstrap: PASS
- `uv run pcli --help` and Phase 1 command help: PASS
- `pcli new ...` creates a card stub: PASS by tests
- `pcli validate` catches error-level validation: PASS for all-card validation
- `pcli ls` filters: BLOCKED by ISSUE-1
- `pcli show <slug>` resolves by id or filename slug: BLOCKED by ISSUE-2
- `pcli build resume --dry-run`: PASS
- `pcli build resume` creates JSON and invokes Typst when installed: PARTIAL. `.build/resume-data.json` is written; local environment lacks `typst`, so PDF generation could not be completed here.
- API key absence does not break non-LLM commands: PASS for tested Phase 1 commands

## Automatic Checks
- `uv run pytest -v`: PASS, 61 tests
- `uv run ruff check scripts tests`: PASS
- `uv run ruff format --check scripts tests`: PASS
- `uv run pcli validate`: PASS
- `uv run pcli build resume --dry-run`: PASS
- `uv run pcli build resume --verbose`: FAIL in this environment because `typst` binary is not installed; JSON context was written before the external dependency failure.

## Changes Outside Plan
- No code outside the Phase 1 scope was found.

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY
- ISSUE-3: APPLY

### Applied

RESOLVED: ISSUE-1 — `--until YYYY-MM` 월 전체 포함으로 수정
- `scripts/select.py`: `_parse_ym_end()` 추가 — `calendar.monthrange(y, m)[1]`로 해당 월 마지막 날 계산
- `until` 필터를 `<= _parse_ym_end(until)` 로 변경 (이전: `<= first_day_of_month`)
- 회귀 테스트: `test_until_month_inclusive`, `test_until_first_day_of_month_included` 추가
자동 체크: pytest ✅ 66/66 / ruff ✅

RESOLVED: ISSUE-2 — `pcli show` filename stem 조회 지원
- `scripts/card.py CardRepo.get()`: 2차 fallback 추가 — `card._source_path.stem == slug` (exact filename stem 매칭)
- `pcli show 2026-05-pocavault-seoulana` 형태 조회 가능
- partial/substring match는 미적용 (이전 Advisor 결정 유지)
- 회귀 테스트: `test_card_repo_get_by_filename_stem`, `test_show_by_filename_stem` 추가
자동 체크: pytest ✅ 66/66 / ruff ✅

RESOLVED: ISSUE-3 — `pcli validate <slug>` 파싱 실패 카드 탐지
- `scripts/pcli.py cmd_validate()`: `repo.get(slug)` miss 시 `repo.errors`를 직접 스캔
- `e.path.stem == slug` or `e.path.stem.endswith(f"-{slug}")` 조건으로 대상 에러 필터
- 파싱 실패 카드도 slug로 타겟 가능
- 회귀 테스트: `test_validate_slug_broken_card` 추가
자동 체크: pytest ✅ 66/66 / ruff ✅
