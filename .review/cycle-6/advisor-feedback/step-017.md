# Step 017 — Cycle-6 Approach check

Cycle: 6
Pass: 1
Files Changed: docs/acceptance-v1.md (new), scripts/smoke.ps1 (new), scripts/smoke.sh (new), README.md

## Advisor Verdict
OK

## Advisor Feedback
1. acceptance-v1.md: table per criterion (ID, Description, How-to-verify, Command, Manual?, Result). Mark 1/4/5 as Manual: Yes + dedicated Manual Verification section.
2. Two scripts: smoke.ps1 (primary) + smoke.sh (parity). Both: check Typst upfront, skip with [SKIP] message, exit 0. Fail-fast on non-Typst errors.
3. README: append "## Verify v1" section only. Reference docs/acceptance-v1.md + scripts. One-line note on output/ vs .review/.

## Sonnet Response
- 적용 (1): acceptance-v1.md 생성, 7개 기준 모두 테이블 + manual notes 포함.
- 적용 (2): smoke.ps1 + smoke.sh 생성, typst guard 포함.
- 적용 (3): README 끝에 "## Verify v1" 섹션만 추가.
