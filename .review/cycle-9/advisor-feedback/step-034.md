# Step 034 — Cycle-9 review-v1 Approach check

Cycle: 9
Pass: 2 (review-v1 fixes)
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. ISSUE-1: Glob check in route handler (`api_card_create`), not in `_new_card_path()`. Path helper stays pure.
2. ISSUE-1: `any(cards_dir.glob(f"????-??-{card_id}.mdx"))` for short-circuit; 409 with clear message.
3. ISSUE-2: Explicitly reject mismatched `fields.id` with 400. Silent strip hides client bugs.
4. ISSUE-2: Check before merge loop — fail fast.
5. Test 3 (matching id in PUT): accept; merged dict already has the correct id.
6. Run all 3 new tests + existing suite before RESOLVED append.

## Sonnet Response
- Communication Bridge: ISSUE-1 APPLY, ISSUE-2 APPLY.
- 구현: api_card_create에 glob 선검사 추가, api_card_update에 id 보호 추가.
- 구현 시작.
