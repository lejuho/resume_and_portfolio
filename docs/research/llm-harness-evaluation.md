# LLM Harness Evaluation: Grounding And Token Efficiency

Date: 2026-05-25  
Model under test: Google `gemini-2.5-flash`  
Status: partial pilot completed; full comparison blocked by configured free-tier daily quota.

## Objective

Choose the next Studio refinement contract using measured factual safety, parse reliability,
draft utility, latency, and token cost rather than prompt preference alone.

## Official API Findings

| Finding | Source | Consequence |
|---|---|---|
| Gemini structured output can generate JSON matching a supplied JSON Schema; semantic/business validation is still required. | [Google Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output) | A grounded Studio response should use structured output plus application validation, rather than prompt-only JSON formatting. |
| `usage_metadata` exposes input, output, and total token counts after `generate_content`. | [Google Tokens](https://ai.google.dev/gemini-api/docs/tokens) | Token measurement can be captured for every evaluation and later for optional telemetry. |
| Gemini 2.5 Flash context caching has a 1,024 input-token minimum and is aimed at repeated large common context. | [Google Context Caching](https://ai.google.dev/gemini-api/docs/caching) | Do not prioritize caching for short single-card refinement until measured prompt context repeatedly exceeds the threshold. |

## Candidate Contracts

| Candidate | Calls per draft | Description | Intended tradeoff |
|---|---:|---|---|
| Baseline | 1 | Existing Cycle 16 prompt requests consultant-style JSON through text instructions only. | Current behavior; richest current fields, no structured-output enforcement or explicit fact boundary. |
| Candidate A | 1 | Grounded one-shot response with `source_facts`, `assumptions`, `missing_info`, resume and portfolio surfaces, using JSON Schema response configuration. | Lowest additional latency while making review boundaries explicit. |
| Candidate B | 2 | Structured fact extraction followed by structured composition from extracted evidence. | Stronger separation in principle, but increased quota/token/latency and two failure points. |

## Evaluation Corpus

All pilot material is synthetic and contains no user's private history.

| Fixture | Track | Variation tested |
|---|---|---|
| `K1-bare` | K | Korean education-project note without date, metric, or evidence |
| `K2-measured` | K | Korean automation outcome with time reduction |
| `K3-ambiguous-team` | K | Team result with unclear personal scope |
| `G1-bare` | G | English Web3 prototype without measured result |
| `G2-evidence` | G | Technical latency improvement and demo URL |
| `G3-hackathon` | G | Timed build, teammate, and repository URL |

Planned pilot size was six fixtures by three candidate evaluations. Candidate B consumes two
provider calls, so the planned 18 candidate evaluations require 24 API requests. This
distinction must be applied to any future quota or budget cap.

## Measurement Procedure

- Fixed model and provider: configured Google `gemini-2.5-flash`.
- Fixed output intent: `both`.
- No card files or source material are persisted.
- Recorded metrics: JSON parse success, unsupported numerical claim heuristic, prompt token
  count, candidate output token count, total token count, and elapsed request time.
- Candidate A and B used schema-constrained structured output; baseline used the currently
  implemented prompt-only JSON request.
- Numeric heuristic is a safety smoke check only; a human rubric review is still required for
  claims such as unsupported audience or impact interpretation.

## Pilot Execution Result

The live provider connection succeeded. The initial pilot did not checkpoint intermediate
results and hit the per-minute free-tier limit. A paced/checkpointed retry then reached the
free-tier daily request limit:

```text
Quota metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
Model: gemini-2.5-flash
Daily free-tier request limit reported by API: 20
```

Successful live calls consumed before the daily limit:

| Calls | Purpose | Saved for analysis? |
|---:|---|---|
| 1 | connection check | no content output required |
| 16 | first unpaced pilot before quota interruption | no; runner did not checkpoint |
| 3 | paced retry: baseline, Candidate A, Candidate B extraction for `K1-bare` | baseline and Candidate A only; B composition could not run |

### Saved Comparable Measurements: `K1-bare`

| Candidate | Parse success | Unsupported numeric claim detected | Input tokens | Candidate output tokens | Total tokens | Latency |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | No | No | 488 | 997 | 3,225 | 13,211 ms |
| Candidate A | Yes | No | 132 | 366 | 1,616 | 7,831 ms |

Notes:

- Baseline returned JSON enclosed in markdown fences, which current `json.loads(raw.strip())`
  cannot parse. This is one live example of the reliability risk already implied by not
  using structured output.
- Candidate A returned schema-parseable JSON and separated `source_facts` and `assumptions`.
- Candidate A still surfaced an inferred educational objective inside `assumptions`; that is
  acceptable only if the UI makes confirmation explicit and does not persist it by default.
- Total token count exceeds prompt plus visible candidate-output token count in both calls,
  consistent with additional model usage being included by provider metadata. Cost evaluation
  must therefore use `total_token_count`, not only visible output size.
- A single comparable fixture is insufficient to claim general quality or efficiency
  superiority.

## Decision

### Cycle 20 implementation recommendation

Implement **Candidate A: grounded one-shot structured preview** as the first product change,
because it directly satisfies the research-derived human-review requirement and avoids the
known two-call quota/latency cost of staged composition.

Required contract additions:

- preview-only `source_facts`;
- preview-only `assumptions`;
- meaningful `missing_info` / follow-up questions;
- output-specific resume and portfolio draft text;
- provider structured-output configuration where supported, followed by existing application
  validation and safe fallback.

### What is not yet proven

Do not claim that Candidate A is the final optimal prompt or that it always uses fewer tokens.
The complete corpus comparison was blocked by provider quota. Candidate B remains a rejected
default for now, not a permanently rejected experiment.

## Completion Gate For Cycle 20

The implementation cycle should include deterministic tests for factual constraints and a
repeatable optional evaluation runner. Before declaring prompt quality accepted:

| Gate | Threshold |
|---|---|
| Unsupported claimed dates/metrics/roles/links in fixture review | 0 |
| Structured parse success across completed live evaluation calls | 100% |
| Track K and Track G rubric review | average at least 4/5 for selected candidate |
| Candidate selection | lowest usable-draft token cost among candidates passing quality gates |

Full live evaluation may run once billing/quota or a later-day allocation allows the planned
corpus, with call counts calculated by provider requests rather than candidate evaluations.

## Operational Findings

- A connection-check call consumes real request quota and should remain explicitly
  user-triggered.
- An evaluation runner must checkpoint every completed call and stop cleanly on quota errors.
- Free-tier limits make staged multi-call drafting costly for interactive local use.
- No API key or raw private material was written to repository documentation during this audit.
