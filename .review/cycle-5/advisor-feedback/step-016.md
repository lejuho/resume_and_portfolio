# Step 016 — Cycle-5 review-v1 fix Approach check

Cycle: 5
Pass: 2
Files Changed: scripts/pcli.py, tests/test_build_dry_run.py

## Advisor Verdict
OK

## Advisor Feedback
1. ISSUE-1 OK. Mirror cmd_build_resume validation exactly (post-preset, pre-load). Add both tests (0 and -1).
2. ISSUE-2 OK. Switch both commands to Exit(1). Keep yellow message (signal, not error color).
3. Grep tests for "No cards selected" / Exit assertions before changing — update any exit_code==0 to ==1.
4. Run full pytest after both fixes; confirm no regression.

## Sonnet Response
- 적용 (1): cmd_build_portfolio에 max-items 검증 추가, 테스트 2개 추가.
- 적용 (2): 두 명령 모두 "No cards selected" → Exit(1). 관련 테스트 확인 후 업데이트.
