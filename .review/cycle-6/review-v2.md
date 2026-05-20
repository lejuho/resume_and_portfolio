# Codex Review v2

## Verdict

BLOCKED

The review-v1 issues are mostly resolved: the acceptance JD path now points to `tests/fixtures/fake-jd.txt`, and the PowerShell smoke script runs portfolio generation independently of Typst. The remaining blocker is in the bash smoke script: with `set -e`, the counter increments can terminate the script after the first successful step.

## Findings

### 1. BLOCKER: `scripts/smoke.sh` can exit after the first PASS under `set -e`

- File: `scripts/smoke.sh:15`, also `scripts/smoke.sh:18`, `scripts/smoke.sh:25`, `scripts/smoke.sh:58`, `scripts/smoke.sh:61`
- Problem:
  - The script uses `set -euo pipefail`.
  - Bash arithmetic commands return exit status 1 when the expression evaluates to 0.
  - On the first successful step, `pass=0`, so `((pass++))` evaluates to 0 and returns status 1.
  - Because `set -e` is active, the script can exit immediately after printing the first `PASS`.
- Why this matters:
  - Cycle 6 explicitly adds `smoke.sh` for bash/macOS/Linux parity.
  - The script is part of the release-readiness evidence path, so it should be reliable outside PowerShell.
- Suggested fix:
  - Replace post-increment arithmetic commands with non-failing forms:
    - `((++pass))`, `((++fail))`, `((++skip))`
    - or `pass=$((pass + 1))`, `fail=$((fail + 1))`, `skip=$((skip + 1))`
  - Apply the same pattern to the final staged-artifacts check.

### 2. LOW: Typst absence message still says PDF/PPTX builds are skipped

- Files:
  - `scripts/smoke.ps1:33`
  - `scripts/smoke.sh:31`
- Current text:
  - `typst not found — full PDF/PPTX builds will be skipped.`
- Current behavior:
  - Only the resume PDF build is skipped.
  - Portfolio PPTX always runs, which is correct.
- Suggested fix:
  - Change the message to `typst not found — resume PDF build will be skipped.`

## Fixed Since v1

- `docs/acceptance-v1.md` criterion 5 now uses `tests/fixtures/fake-jd.txt`.
- README explains that the fixture can be used for dry-run verification and live rewrite requires `ANTHROPIC_API_KEY`.
- `scripts/smoke.ps1` and `scripts/smoke.sh` now run `build portfolio --tags web3` outside the Typst gate.

## Sprint Contract Check

- Acceptance evidence doc exists and maps to seven criteria: PASS
- Criterion 5 command is runnable for dry-run/fallback path: PASS
- Smoke workflow can run from PowerShell: PASS
- README references acceptance evidence: PASS
- Smoke commands produce PDF/PPTX artifacts in ignored output directories: PASS on PowerShell
- No generated PDF/PPTX/cache/build artifacts staged: PASS
- Bash smoke parity: FAIL

## Automatic Checks

- `powershell -ExecutionPolicy Bypass -File .\scripts\smoke.ps1`: PASS, 12 passed / 0 failed / 0 skipped
- `uv run pcli build resume --jd tests\fixtures\fake-jd.txt --tone formal --dry-run`: PASS
- `uv run pytest -v`: PASS, 136 tests
- `uv run ruff check scripts tests templates`: PASS

## Notes

- `bash scripts/smoke.sh` cannot be executed in this Windows environment because `bash` resolves to WSL and no distribution is installed. The blocker is based on bash `set -e` arithmetic semantics and the script source.
- Current uncommitted/untracked items observed:
  - modified `.gitignore`
  - modified `.review/cycle-2/.read-counter`
  - untracked `.review/cycle-6/plan.md`
  - untracked `.review/cycle-6/status.txt`
  - untracked `.review/cycle-6/review-v2.md`

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Replace `((var++))` with `var=$((var + 1))` in smoke.sh
- `scripts/smoke.sh`: all four arithmetic increments (pass/fail in step(), skip in skip_step(), pass/fail in staged-artifacts check) replaced with POSIX-safe `$((var + 1))` assignment form
- `grep -qE` inside `if` condition confirmed exempt from `set -e` — no additional change needed

RESOLVED: ISSUE-2 — Fix Typst absence message in both smoke scripts
- `scripts/smoke.ps1`: "full PDF/PPTX builds will be skipped" → "resume PDF build will be skipped"
- `scripts/smoke.sh`: same message fix

자동 체크: pytest 136/136 ✅ / ruff check ✅
