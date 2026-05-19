# Advisor Feedback — Step 002

**Type:** Completion check
**Module:** phase-1 Card-Based Portfolio CLI (all scripts)
**Date:** 2026-05-19

## Question

Completion check: phase-1 구현 완료.
회귀 우려 지점:
1. CardRepo.get() partial match fallback 모호성
2. object.__setattr__로 _body/_source_path 주입 → frozen 취약
3. pcli validate slug 필터 path substring → false positive 가능

## Advisor Response

1. CardRepo.get() partial match fallback 제거 — exact id 매칭만 허용
2. _body/_source_path를 PrivateAttr로 선언, object.__setattr__ 우회 제거
3. validate 필터링: path substring 폐기 → card.id == slug 또는 source_path.stem 정확 비교
4. 회귀 테스트 추가 — get() 모호 substring, validate false-positive 케이스

## Applied

- APPLY: CardRepo.get() exact id match only
- APPLY: PrivateAttr for _body/_source_path
- APPLY: validate slug filter: exact id/stem match
- APPLY: regression tests added
