# Step 020 — Cycle-6 review-v1 fix Approach check

Cycle: 6
Pass: 2
Files Changed: docs/acceptance-v1.md, scripts/smoke.ps1, scripts/smoke.sh, README.md

## Advisor Verdict
OK

## Advisor Feedback
1. ISSUE-1: Update path to `tests/fixtures/fake-jd.txt` in acceptance-v1.md. Add README note: fixture works for `--dry-run`; live rewrite needs `ANTHROPIC_API_KEY`. No symlink/copy (avoids duplication and Windows friction).
2. ISSUE-2 (smoke.ps1): Keep `$typstAvailable` for resume gate only. Portfolio runs unconditionally.
3. ISSUE-2 (smoke.sh): Mirror — gate resume on `command -v typst`; portfolio always runs.
4. Verify both smokes still exit non-zero on portfolio failure.
5. Run smoke locally (Typst absent path) to confirm portfolio executes.

## Sonnet Response
- 적용 (1): acceptance-v1.md 경로 → tests/fixtures/fake-jd.txt. Manual 섹션도 동일하게 업데이트. README에 LLM tailoring 검증 노트 추가.
- 적용 (2)/(3): smoke.ps1 + smoke.sh 모두 resume만 Typst 게이트, portfolio는 항상 실행.
- 확인 (4)/(5): pytest 136/136 pass, ruff clean, portfolio build PASS.
