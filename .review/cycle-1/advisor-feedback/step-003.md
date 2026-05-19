# Advisor Feedback — Step 003

**Type:** Approach check
**Module:** review-v1.md BLOCKED issues (ISSUE-1, ISSUE-2, ISSUE-3)
**Date:** 2026-05-19

## Question

review-v1.md 3개 BLOCKED 이슈 수정 방향 검토:
- ISSUE-1: --until 월 경계 버그
- ISSUE-2: show filename slug 미지원
- ISSUE-3: validate <slug> 파싱 실패 카드 미탐지

## Advisor Response

**ISSUE-1** — Direction B (last day of month):
1. `calendar.monthrange(y,m)[1]` → last day
2. `until` filter: `<= until_end`
3. `since`는 기존 first-day 유지

**ISSUE-2** — get() 2단계 lookup:
1. Loop 1: exact `card.id == slug`
2. Loop 2 fallback: `card._source_path.stem == slug`
3. No partial match (prior Advisor 준수)

**ISSUE-3** — Root cause: `repo.get(slug)` miss 시 `repo.errors`에서 `e.path.stem`이 slug를 끝에 포함하는 에러를 직접 스캔.
1. get() miss → errors에서 stem 끝 일치 탐색
2. 매칭 에러 있으면 출력 후 Exit(1)
3. 없으면 "Card not found" Exit(1)

## Applied

- APPLY: ISSUE-1 — calendar.monthrange last-day approach
- APPLY: ISSUE-2 — get() filename stem fallback (exact only)
- APPLY: ISSUE-3 — validate errors scan on get() miss
