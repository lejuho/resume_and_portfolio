# Codex Review v1

## Verdict

BLOCKED

Cycle 6 mostly does what the release-readiness plan asked for: it adds an acceptance evidence document, PowerShell/bash smoke scripts, README verification notes, and the PowerShell smoke path passes in the local environment. One release-readiness blocker remains: the documented LLM acceptance command references a JD file that does not exist in the repository.

## Findings

### 1. BLOCKER: v1 acceptance criterion 5 documents a non-existent JD path

- File: `docs/acceptance-v1.md:15`
- Current documented command:
  - `uv run pcli build resume --jd ./fake-jd.txt --tone formal`
- Current repo state:
  - `fake-jd.txt`: missing
  - `tests/fixtures/fake-jd.txt`: exists
- Reproduction:
  - `uv run pcli build resume --jd .\fake-jd.txt --tone formal --dry-run`
  - Result: `JD error: JD file not found: '.\\fake-jd.txt'`
- Why this matters:
  - Cycle 6's purpose is repeatable release/acceptance evidence.
  - Acceptance criterion 5 cannot be followed as written, even before considering whether `ANTHROPIC_API_KEY` is set.
- Suggested fix:
  - Either add a root-level `fake-jd.txt` sample file, or update `docs/acceptance-v1.md` to use `tests/fixtures/fake-jd.txt`.
  - Prefer also adding a README note that the fixture path can be used for dry-run/fallback verification, while live rewrite verification still requires `ANTHROPIC_API_KEY`.

### 2. MEDIUM: smoke scripts skip portfolio build when Typst is missing

- Files:
  - `scripts/smoke.ps1`
  - `scripts/smoke.sh`
- Current behavior:
  - If Typst is absent, both `build resume --preset bok-interview` and `build portfolio --tags web3` are skipped.
- Why this matters:
  - Portfolio PPTX generation uses `python-pptx`, not Typst.
  - On a fresh machine without Typst, the smoke script should still verify the PPTX path.
- Suggested fix:
  - Gate only the resume PDF build on Typst.
  - Always run `uv run pcli build portfolio --tags web3`.

## Sprint Contract Check

- Acceptance evidence doc exists and maps to seven criteria: PARTIAL, criterion 5 command is not runnable as written
- Smoke workflow can run from PowerShell: PASS
- README references acceptance evidence: PASS
- Smoke commands produce PDF/PPTX artifacts in ignored output directories: PASS on this machine
- No generated PDF/PPTX/cache/build artifacts staged: PASS
- `.review/cycle-6/status.txt` remains `in_progress`: PASS

## Automatic Checks

- `powershell -ExecutionPolicy Bypass -File .\scripts\smoke.ps1`: PASS when run with normal filesystem/cache permissions, 12 passed / 0 failed / 0 skipped
- `uv run pytest -v`: PASS, 136 tests
- `uv run ruff check scripts tests templates`: PASS
- `uv run ruff format --check scripts tests templates`: PASS via smoke script
- `uv run pcli validate`: PASS via smoke script
- `uv run pcli build resume --dry-run`: PASS via smoke script
- `uv run pcli build portfolio --dry-run`: PASS via smoke script
- `uv run pcli build resume --preset bok-interview`: PASS via smoke script
- `uv run pcli build portfolio --tags web3`: PASS via smoke script

## Notes

- `bash scripts/smoke.sh` could not be validated in this Windows environment because `bash` resolved to WSL and no WSL distribution is installed. The Cycle 6 plan prioritizes PowerShell on Windows, so this is not considered blocking.
- Current uncommitted/untracked items observed during review:
  - modified `.gitignore`
  - modified `.review/cycle-2/.read-counter`
  - untracked `.review/cycle-6/plan.md`
  - untracked `.review/cycle-6/status.txt`
  - untracked `.review/cycle-6/review-v1.md`

---

## RESOLVED

### Issue Classification
- ISSUE-1: APPLY
- ISSUE-2: APPLY

### Applied

RESOLVED: ISSUE-1 — Fix non-existent JD path in acceptance-v1.md
- `docs/acceptance-v1.md`: criterion 5 command updated from `./fake-jd.txt` → `tests/fixtures/fake-jd.txt`; manual verification note updated to match
- `README.md`: added LLM tailoring verification note — fixture usable for `--dry-run`, real rewrite requires `ANTHROPIC_API_KEY`

RESOLVED: ISSUE-2 — Portfolio build no longer gated on Typst in smoke scripts
- `scripts/smoke.ps1`: portfolio step moved out of Typst guard block; runs unconditionally
- `scripts/smoke.sh`: same change, portfolio always runs

자동 체크: pytest 136/136 ✅ / ruff check ✅ / build portfolio --tags web3 ✅
