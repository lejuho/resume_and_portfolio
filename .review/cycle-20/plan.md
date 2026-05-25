# Cycle 20 Plan: Grounded Studio Preview

Branch: `feature/cycle-20-grounded-studio-preview`

## Summary

The research audit found that Studio can produce resume and portfolio drafts, but it does
not yet make factual grounding inspectable before save. It also found one live Gemini case
where the existing prompt-only JSON response failed to parse while a schema-constrained
grounded response parsed successfully.

Cycle 20 implements the smallest grounded drafting vertical slice for the existing
Resume / Portfolio / Both flow:

```text
raw career material -> supported facts and assumptions -> intent-specific draft -> human save
```

This cycle extends `requirements-dashboard.md` sections 8.4-8.5, 8.7 and D-008. It does
not implement 자기소개서 or application-question answers; those remain the following cycle
under D-009.

## Input / Output Specification

### Existing Endpoint Extended

`POST /api/studio/refine`

Input remains:

```json
{
  "raw_text": "string",
  "intent": "resume | portfolio | both"
}
```

Successful response remains backward-compatible and adds preview-only grounding fields inside
`draft`:

```json
{
  "ok": true,
  "draft": {
    "id": "string",
    "title": "string",
    "type": "project | talk | paper | hackathon | role | award | writing | course | community",
    "period_start": "YYYY-MM-DD",
    "status": "draft",
    "visibility": "public",
    "summary": "string",
    "source_facts": ["fact directly supported by raw input"],
    "assumptions": ["interpretation requiring user confirmation"],
    "resume_bullet": "string when intent includes resume",
    "portfolio_body": "markdown when intent includes portfolio",
    "tags": { "domain": [], "skill": [], "audience": [] },
    "metrics": [],
    "evidence": [],
    "refine_source": "mock | llm"
  },
  "missing_info": [
    { "code": "string", "message": "question for missing support" }
  ]
}
```

Behavior:

- `source_facts` contains factual items supported by `raw_text`; it is always present.
- `assumptions` contains useful but unverified interpretation; it is always present and may
  be empty.
- `missing_info` remains the question surface and must include role/contribution uncertainty
  when team ownership is unclear.
- Resume and portfolio drafts must not introduce numerical achievements, dates, tools,
  evidence URLs, or sole-ownership claims absent from the input.
- Existing errors for empty input and invalid intent remain unchanged.
- Provider failure still falls back safely to deterministic mock behavior.

### Persistence Boundary

`POST /api/studio/save` remains create-only and does not persist `source_facts` or
`assumptions` by default. It persists only the user-reviewed canonical card fields and
approved draft narrative as it does today. Raw input remains non-persistent.

### Internal Evaluation Command

Add a developer-only, non-UI evaluation command:

```bash
uv run python scripts/evaluate_studio_grounding.py --dry-run
uv run python scripts/evaluate_studio_grounding.py --live --provider google --max-calls 12
```

Behavior:

- Uses bundled synthetic fixtures only; no real card or private text input.
- Compares current baseline and grounded one-shot candidates only; staged two-call drafting
  stays out of scope.
- `--dry-run` prints fixture/call count and makes no provider request.
- `--live` requires configured provider credentials, records per-call parse result,
  unsupported-numeric heuristic, input/output/total tokens, latency, and safe error category.
- Writes checkpoint results after every completed call under
  `output/evaluations/studio-grounding-<timestamp>.json`.
- Stops when `--max-calls` is reached or a quota/rate-limit response occurs; it must not retry
  quota failures automatically.

## Key Changes

- Backend / LLM: extend the Studio refinement normalization and grounded prompt contract;
  provide schema-constrained JSON generation for Google Gemini and robustly accept
  provider-returned JSON for supported live paths while preserving safe mock fallback.
- Backend / mock: make deterministic preview return `source_facts` and `assumptions`; remove
  unsupported result phrasing from metric-free resume drafts and surface missing evidence or
  unclear contribution through questions.
- Frontend / Studio: render separate `Supported facts` and `Needs confirmation` preview
  sections, with empty/needs-review states that make these preview annotations visibly
  different from saved narrative.
- Persistence: keep `source_facts`, `assumptions`, and raw source text out of saved MDX unless
  a later requirement explicitly adds source-memory persistence.
- Evaluation: add synthetic two-track fixtures and the quota-aware evaluation command for
  baseline-versus-grounded token/reliability measurement.
- Documentation: update Studio acceptance evidence only as needed to name the new preview
  fields and the safe live-evaluation procedure; do not expand into application-writing UI.

## Sprint Contract

- Passing behavior:
  - Studio preview always exposes supported facts and assumptions for mock and LLM flows.
  - Metric-free or ownership-ambiguous input is not turned into an unsupported result or
    sole-ownership claim by the deterministic flow.
  - Google live refinement uses structured response configuration where available and
    malformed/live failures still resolve through the existing safe fallback behavior.
  - Saving a preview does not persist raw input, `source_facts`, or `assumptions`.
  - Existing dashboard, provider check, resume build, and portfolio build behavior does not
    regress.
  - Evaluation command is synthetic-only, checkpointed, and quota bounded.
- Automatic checks:

```bash
uv run pytest -v
uv run ruff check scripts tests
uv run ruff format --check scripts tests
uv run pcli validate
uv run pcli build resume --dry-run
uv run pcli build portfolio --dry-run
uv run python scripts/evaluate_studio_grounding.py --dry-run
```

- Test cases:
  - API: refine output includes empty or populated `source_facts` and `assumptions` for
    `resume`, `portfolio`, and `both`.
  - Grounding: metric-free input produces no numeric/outcome claim; provided metric is
    preserved; team ambiguity creates a contribution follow-up rather than sole attribution.
  - Metamorphic: adding an evidence URL satisfies the evidence gap without changing unrelated
    source facts; resume and portfolio intents preserve shared factual values.
  - Provider: Google structured response configuration is requested; malformed or provider
    error paths fall back without leaking credentials.
  - UI: Studio contains and renders supported-facts and needs-confirmation sections.
  - Persistence: saving edited draft does not store raw input or preview-only annotation
    fields in MDX.
  - Evaluation: dry-run makes no provider call; live fake-client run checkpoints output and
    stops at max calls/quota category.
- Manual acceptance:
  - Generate a mock preview from a metric-free team activity and confirm questions are shown
    instead of fabricated outcomes.
  - When quota is available, run a bounded Google evaluation with synthetic fixtures and
    record the generated result path in `docs/acceptance-studio.md`.
  - Run one non-sensitive Track K and one Track G Studio preview and review them against
    `docs/research/career-output-methodology.md`.
- gas limit: N/A
- slither pass: N/A

## Missing Edge Case Candidates

- Raw text contains numbers that are dates or technology versions, not performance metrics;
  the draft must not relabel them as impact.
- A source mentions a team outcome and a personal task in separate sentences; contribution
  must not be overstated while still retaining the supported personal action.
- Live provider returns valid JSON matching syntax but semantically unsupported claims;
  schema validation alone is insufficient and evaluation/manual review remains required.

## Simpler Alternative

Only add `source_facts` and `assumptions` labels to the existing prompt and UI, without
structured provider output or the bounded evaluation command.

This is not selected because the audit already observed a live parse failure from prompt-only
JSON and because token/grounding decisions would remain impossible to reproduce safely under
quota limits.

## Assumptions

- The existing card schema remains unchanged; grounding annotations are preview metadata, not
  canonical card fields.
- Google Gemini is the measured provider for evaluation because it is currently configured,
  while Anthropic remains supported by existing runtime behavior.
- Native structured output is required for Google when available; other providers may rely on
  the grounded JSON prompt plus current normalization/fallback contract.
- Live quality evaluation is optional when provider quota is unavailable; deterministic tests
  and dry-run evaluation are required for cycle completion.
- Application Writing Harness outputs (`cover_letter`, `application_answer`) and all target
  context inputs are explicitly deferred to the next cycle.

## Review Guidance

### Enumeration Required

- Enumerate every Studio response and persistence path that could accidentally save preview
  metadata or raw input:

```bash
rg -n "api_studio_refine|api_studio_save|source_facts|assumptions|raw_text|portfolio_body|resume_bullet" scripts tests
```

Expected paths include mock refine, LLM refine, save endpoint, Studio JS render/save payload,
and their tests.

- Enumerate all provider dispatch and error/fallback paths affected by structured output:

```bash
rg -n "_call|studio_refine_llm|resolve_provider_config|google|anthropic|fallback|ai-check|LLMError" scripts tests
```

Expected areas include existing Anthropic compatibility, Google generation, connection check,
malformed-response fallback, and new evaluator calls.

### Verification Method

- Mock-based unit/integration tests are sufficient for API contract, persistence non-mutation,
  frontend hooks, provider dispatch/configuration, and evaluator checkpoint/stop behavior.
- Mock tests are not sufficient to prove provider structured-output compatibility; when quota
  is available, run the bounded synthetic Google evaluator and record output as manual
  acceptance evidence.
- Schema or parser tests are not sufficient to prove factual quality; inspect Track K and
  Track G synthetic/approved previews against the research rubric, and treat unsupported
  factual claims as a blocking defect.
