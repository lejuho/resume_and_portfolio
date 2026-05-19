# Advisor Feedback — Step 004

**Type:** Completion check
**Module:** review-v1.md BLOCKED 3개 이슈 수정 완료
**Date:** 2026-05-19

## Question

변경 파일:
- scripts/select.py — `_parse_ym_end()` 추가, until 필터 month-inclusive
- scripts/card.py — `CardRepo.get()` id exact → stem fallback
- scripts/pcli.py — `cmd_validate()` errors 스캔 (stem endswith)

회귀 우려:
1. since/until 방향성 비대칭 (since first-day `>=`, until last-day `<=`)
2. get() dup-stem 충돌 가능성
3. `endswith(f"-{slug}")` false positive

## Advisor Response

**우려 1** — Non-issue. since=first-day `>=`, until=last-day `<=` → 양쪽 month-inclusive. 의도된 정합적 asymmetry. 조치 불필요.

**우려 2** — Non-issue. 중복 id는 `errors`로 가고 `cards`엔 미포함. `get()`은 valid card만 순회. 충돌 없음.

**우려 3** — REAL BUG. `validate other` → `2026-01-the-other.mdx` + `2026-01-my-other.mdx` 동시 매칭. 무관 카드 에러 오보고.

조치 단계:
1. `e.path.stem.endswith(f"-{slug}")` → `_filename_slug(e.path) == slug` 재사용 (card.py single source).
2. 정규식 분기 추가 대신 기존 함수 재사용으로 divergence 제거.
3. 테스트: 동일 slug-suffix 2개 카드 + 깨진 frontmatter, exact match만 보고되는지 검증.
4. line 146 exact-match path와 stem 로직 일관성 확인.

## Applied

- APPLY: 우려 3 — `cmd_validate` errors 스캔을 `_filename_slug` 재사용으로 교체
- REJECT: 우려 1 — 의도된 정합적 동작, 변경 불필요 (이유: month-inclusive 양 경계 의도대로 동작)
- REJECT: 우려 2 — 실제 충돌 없음, 변경 불필요 (이유: dup은 errors로 분리되어 get() 미도달)
