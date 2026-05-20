# Step 022 — Cycle-6 review-v2 fix Approach check

Cycle: 6
Pass: 3
Files Changed: scripts/smoke.sh, scripts/smoke.ps1

## Advisor Verdict
OK

## Advisor Feedback
1. Use `pass=$((pass + 1))` — POSIX-compliant assignment form. Works identically in bash 3.2 through 5.x, plus dash/zsh.
2. `((++pass))` works in bash 3+ but is a bash-ism; less portable.
3. Apply `$((var + 1))` form to all four counters: pass, fail, skip, and staged-artifacts counter.
4. For ISSUE-2, change both smoke.sh:31 and smoke.ps1:33 message to "resume PDF build will be skipped."
5. Verify: run `bash scripts/smoke.sh`; confirm PASS counter increments past 1.

## Sonnet Response
- 적용 (1)/(3): smoke.sh의 모든 `((var++))` → `var=$((var + 1))` (step, skip_step, staged-artifacts 3개소).
- 적용 (4): smoke.sh + smoke.ps1 메시지 수정.
- 확인 (5): Windows 환경에서 bash(WSL) 미설치로 직접 실행 불가; grep이 if 조건 내에 있어 set -e 면제 확인.
