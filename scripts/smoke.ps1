# smoke.ps1 — v1 release readiness smoke test (PowerShell)
# Run from repo root: .\scripts\smoke.ps1
# Requires: uv, Python 3.11+
# Optional: typst (PDF builds skipped if absent)

$ErrorActionPreference = "Stop"
$pass = 0
$fail = 0
$skip = 0

function Step($label, $cmd) {
    Write-Host "`n==> $label" -ForegroundColor Cyan
    try {
        Invoke-Expression $cmd
        if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
        Write-Host "    PASS" -ForegroundColor Green
        $script:pass++
    } catch {
        Write-Host "    FAIL: $_" -ForegroundColor Red
        $script:fail++
    }
}

function SkipStep($label, $reason) {
    Write-Host "`n==> $label" -ForegroundColor Cyan
    Write-Host "    SKIP: $reason" -ForegroundColor Yellow
    $script:skip++
}

# Check Typst
$typstAvailable = $null -ne (Get-Command typst -ErrorAction SilentlyContinue)
if (-not $typstAvailable) {
    Write-Host "`n[INFO] typst not found — resume PDF build will be skipped." -ForegroundColor Yellow
}

Write-Host "`n=== pcli v1 Smoke Test ===" -ForegroundColor White

Step "pytest"                          "uv run pytest -v"
Step "ruff check"                      "uv run ruff check scripts tests templates"
Step "ruff format --check"             "uv run ruff format --check scripts tests templates"
Step "pcli validate"                   "uv run pcli validate"
Step "pcli --help"                     "uv run pcli --help"
Step "build resume --help"             "uv run pcli build resume --help"
Step "build portfolio --help"          "uv run pcli build portfolio --help"
Step "build resume --dry-run"          "uv run pcli build resume --dry-run"
Step "build portfolio --dry-run"       "uv run pcli build portfolio --dry-run"

if ($typstAvailable) {
    Step "build resume --preset bok-interview" "uv run pcli build resume --preset bok-interview"
} else {
    SkipStep "build resume --preset bok-interview" "typst not installed"
}

Step "build portfolio --tags web3" "uv run pcli build portfolio --tags web3"

# Verify no artifacts staged
Write-Host "`n==> git status (no staged artifacts)" -ForegroundColor Cyan
$staged = git diff --cached --name-only 2>&1
$artifacts = $staged | Where-Object { $_ -match "\.(pdf|pptx)$" }
if ($artifacts) {
    Write-Host "    FAIL: staged artifacts found: $artifacts" -ForegroundColor Red
    $fail++
} else {
    Write-Host "    PASS" -ForegroundColor Green
    $pass++
}

Write-Host "`n=== Results: $pass passed, $fail failed, $skip skipped ===" -ForegroundColor White
if ($fail -gt 0) { exit 1 }
