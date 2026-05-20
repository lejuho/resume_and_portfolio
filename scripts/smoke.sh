#!/usr/bin/env bash
# smoke.sh — v1 release readiness smoke test (bash)
# Run from repo root: bash scripts/smoke.sh
# Requires: uv, Python 3.11+
# Optional: typst (PDF builds skipped if absent)

set -euo pipefail
pass=0; fail=0; skip=0

step() {
    local label="$1"; shift
    printf '\n==> %s\n' "$label"
    if "$@"; then
        printf '    PASS\n'
        pass=$((pass + 1))
    else
        printf '    FAIL\n'
        fail=$((fail + 1))
    fi
}

skip_step() {
    local label="$1" reason="$2"
    printf '\n==> %s\n    SKIP: %s\n' "$label" "$reason"
    skip=$((skip + 1))
}

if command -v typst &>/dev/null; then
    TYPST=true
else
    printf '\n[INFO] typst not found — resume PDF build will be skipped.\n'
    TYPST=false
fi

printf '\n=== pcli v1 Smoke Test ===\n'

step "pytest"                       uv run pytest -v
step "ruff check"                   uv run ruff check scripts tests templates
step "ruff format --check"          uv run ruff format --check scripts tests templates
step "pcli validate"                uv run pcli validate
step "pcli --help"                  uv run pcli --help
step "build resume --help"          uv run pcli build resume --help
step "build portfolio --help"       uv run pcli build portfolio --help
step "build resume --dry-run"       uv run pcli build resume --dry-run
step "build portfolio --dry-run"    uv run pcli build portfolio --dry-run

if $TYPST; then
    step "build resume --preset bok-interview" uv run pcli build resume --preset bok-interview
else
    skip_step "build resume --preset bok-interview" "typst not installed"
fi

step "build portfolio --tags web3" uv run pcli build portfolio --tags web3

printf '\n==> git status (no staged artifacts)\n'
if git diff --cached --name-only | grep -qE '\.(pdf|pptx)$'; then
    printf '    FAIL: staged artifacts found\n'
    fail=$((fail + 1))
else
    printf '    PASS\n'
    pass=$((pass + 1))
fi

printf '\n=== Results: %d passed, %d failed, %d skipped ===\n' "$pass" "$fail" "$skip"
[[ $fail -eq 0 ]]
