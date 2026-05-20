# Phase 4 LLM Tailoring Plan

Branch: feature/cycle-4-llm-tailoring
Cycle: 4
Created: 2026-05-20

## Summary

Implement Phase 4 from `requirements.md`: optional Anthropic-powered card scoring, summary rewrite, JD-driven resume tailoring, and card draft suggestion. This cycle must preserve the core principle that all non-LLM commands work without an API key.

Scope is limited to the optional LLM layer and its CLI/build integration. No dashboard UI, ingestion automation, ATS optimization, or additional template design work is included.

## 입력/출력 명세

- 입력:
  - selected and validated `cards/*.mdx`
  - `profile.yaml` or `profile.example.yaml`
  - JD text via `--jd <path>` or `--jd -`
  - optional `--tone formal|founder|technical`
  - `ANTHROPIC_API_KEY` env var for live LLM calls
- 출력:
  - 정상:
    - `uv run pcli build resume --jd ./fake-jd.txt --tone formal` scores cards, rewrites summaries in memory, and builds a PDF
    - `uv run pcli llm tailor --cards <ids> --jd <path>` prints scored/re-written output without building
    - `uv run pcli llm suggest --from <file>` prints a frontmatter draft YAML dict
    - LLM responses are cached under `.cache/llm/<sha256>.json`
    - verbose mode prints card scores and rewrite diffs
  - 실패/폴백:
    - No `ANTHROPIC_API_KEY` with an LLM command exits non-zero with a clear message unless a valid cache hit exists
    - LLM API failure uses cache if available; otherwise resume build falls back to non-LLM summaries with a warning
    - Original `cards/*.mdx` files are never modified by LLM rewrites

## Key Changes

- LLM module
  - Add `scripts/llm.py` with `score_cards`, `rewrite_summary`, and `suggest_card_from_text`.
  - Use Anthropic SDK only when an LLM feature is invoked.
  - Add deterministic cache keys using SHA-256 over task name, model, card/input payload, JD text, tone, and language.
  - Store cache files under `.cache/llm/`.
- Resume build integration
  - Add `--jd <path|->`, `--tone formal|founder|technical`, and `--show-llm-diff` to `pcli build resume`.
  - When `--jd` is provided, score cards before `max_items` final selection.
  - When `--jd` or `--tone` is provided, rewrite selected card summaries in memory only.
  - Include score/reason/rewrite metadata in `.build/resume-data.json` under `meta.llm` or equivalent.
- LLM CLI commands
  - Add `pcli llm tailor --cards <ids> --jd <path> [--tone <tone>] [--lang ko|en]`.
  - Add `pcli llm suggest --from <file>`.
  - Add help output for the `llm` command group.
- Tests and fakes
  - Design the Anthropic wrapper so tests can inject a fake client or monkeypatch one function.
  - Do not require network/API key in automated tests.

## Sprint Contract

- 통과 기준:
  - Existing non-LLM commands pass without `ANTHROPIC_API_KEY`.
  - `uv run pcli build resume --jd ./fake-jd.txt --tone formal --dry-run` shows LLM intent or uses fake/cache in tests.
  - `uv run pcli build resume --jd ./fake-jd.txt --tone formal` builds a PDF when API key or cache/fake is available.
  - `uv run pcli llm tailor --cards pocavault-seoulana,chainlens-launch --jd ./fake-jd.txt` prints score/rewrite output.
  - `uv run pcli llm suggest --from ./notes.txt` prints valid YAML-like frontmatter draft.
  - `.cache/llm/<sha>.json` is created on successful LLM calls and reused on identical inputs.
  - Card MDX files remain unchanged after LLM commands.
- 자동 체크:
  - `uv run pytest -v`
  - `uv run ruff check scripts tests templates`
  - `uv run ruff format --check scripts tests templates`
  - `uv run pcli validate`
  - `uv run pcli build resume --dry-run`
  - `uv run pcli build portfolio --dry-run`
  - `uv run pcli llm tailor --cards pocavault-seoulana --jd tests/fixtures/fake-jd.txt` with fake/cache path in tests
- 테스트 케이스:
  - Cache key stability and cache hit reuse.
  - Missing API key behavior for LLM commands.
  - API failure fallback to cache.
  - Resume build applies rewritten summaries in memory and does not edit MDX.
  - `--jd -` reads stdin.
  - `llm suggest` returns required card frontmatter fields.
  - `--show-llm-diff` / `--verbose` exposes rewrites.
- gas 한도: N/A
- slither 통과: N/A

## 누락된 엣지 케이스 후보 3개

- JD text is empty or points to a missing file.
- LLM returns malformed JSON/YAML or omits a required score/rewrite field.
- Cached response was produced for an old prompt/schema version and should not be reused accidentally.

## 더 단순한 대안 1개

Only implement `llm tailor` as a standalone command and defer build integration. Rejected because Phase 4 Definition of Done explicitly requires `--jd` end-to-end in resume builds.

## Assumptions

- Default model is `claude-sonnet-4-6` unless the installed Anthropic SDK or API rejects it; model should be configurable in one constant.
- Automated tests use fake LLM responses and must not call the network.
- `--tone` without `--jd` rewrites selected summaries using the tone instruction but skips card scoring.
- `--jd` scoring happens before final `max_items` cut; explicit `--cards` constrains the scoring pool.
- `summary_ko` is rewritten only when `--lang ko`; otherwise `summary` is rewritten.
- Cache schema includes a version string so future prompt changes invalidate old cache entries.

## Review Guidance

### Enumeration 필요 항목

- LLM command surface
  - 검색: `rg "llm|tailor|suggest|jd|tone|show-llm-diff" scripts tests`
  - 예상 결과: build resume options, `pcli llm` commands, and tests exist.
- Cache behavior
  - 검색: `rg "sha256|\\.cache/llm|cache" scripts tests`
  - 예상 결과: deterministic cache read/write and hit tests exist.
- No source mutation
  - 검색: `rg "write_text|open\\(.*w|Set-Content" scripts`
  - 예상 결과: LLM code writes cache/build artifacts only, not `cards/*.mdx`.

### 검증 방식 가이드

- "No API key still allows non-LLM":
  - Clear `ANTHROPIC_API_KEY` and run validate/resume dry-run/portfolio dry-run.
- "LLM build is in-memory":
  - Test by hashing card files before and after a fake LLM build.
- "Cache works":
  - First fake call writes cache; second identical call should not invoke fake client.
- "Malformed LLM output":
  - Test parser error yields clear warning/error and does not corrupt outputs.
