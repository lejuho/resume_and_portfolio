# Career Studio Acceptance Evidence

Status: execution checklist for Studio through Cycle 19 and future grounded drafting  
Related requirements: `requirements-dashboard.md`  
Related test specification: `docs/test-cases.md`

## Environment Record

```text
Date:
Runner:
Branch/commit:
Port:
AI provider: mock / anthropic / google
AI model (if configured):
Key status: not configured / configured (never record key value)
```

## Automated Baseline

| Criterion | Command | Result | Notes |
|---|---|---|---|
| Python tests | `uv run pytest -v` |  |  |
| Lint | `uv run ruff check scripts tests` |  |  |
| Format check | `uv run ruff format --check scripts tests` |  |  |
| Card validity | `uv run pcli validate` |  |  |
| Resume smoke | `uv run pcli build resume --dry-run` |  |  |
| Portfolio smoke | `uv run pcli build portfolio --dry-run` |  |  |

## Manual Studio Flow

Start the local application:

```bash
uv run pcli dashboard --port 5097
```

| # | Scenario | Action | Expected Result | Result / Notes |
|---:|---|---|---|---|
| 1 | Routes | Open `/studio`, then `/dashboard`. | Studio is creation-first; dashboard remains the exact-edit/admin surface. |  |
| 2 | Mock capture | With no configured provider, paste a non-sensitive activity and select `Both`. | Preview is generated with `mock` source and missing-info prompts where evidence is absent. |  |
| 3 | Review before save | Edit summary, resume bullet, or portfolio narrative before saving. | Changes are reviewable and not written until save is clicked. |  |
| 4 | Draft save | Save the reviewed preview. | New canonical card is created as `draft`; raw pasted text is not stored by default. |  |
| 5 | Admin handoff | Open the saved draft in `/dashboard`. | Saved fields/body are visible and exactly editable. |  |
| 6 | Output handoff | Select approved material and build or dry-run outputs. | Existing resume/portfolio flow operates on selected cards. |  |

## Provider And Privacy Flow

| # | Scenario | Action | Expected Result | Result / Notes |
|---:|---|---|---|---|
| 1 | Placeholder or absent key | Start with no usable key. | Header shows mock/unconfigured rather than connected. |  |
| 2 | Configured key | Set a provider-specific key in local `.env`, restart server, open Studio. | Header reports configuration only; key value is never rendered. |  |
| 3 | Live check success | Click `Check AI connection`. | Provider/model connection is confirmed only after the live call succeeds. |  |
| 4 | Live check failure | Use an invalid key or unavailable quota in a controlled run. | Safe auth/quota/network/provider feedback is shown without secret leakage. |  |
| 5 | LLM preview | Submit non-sensitive input after successful connection. | Preview states `llm` source and still requires explicit save. |  |

## Output Quality Review

Use one real, non-confidential activity for each track. Do not paste sensitive employer or
client information into a live provider unless disclosure is acceptable.

| Dimension | Track K: Korean formal application | Track G: Global tech/Web3 portfolio | Result / Notes |
|---|---|---|---|
| Facts | All asserted dates/results/roles are source-supported. | All asserted dates/results/roles are source-supported. |  |
| Output fit | Formal, compact, field-ready resume statement. | Resume bullet plus readable problem/approach/outcome/insight narrative. |  |
| Contribution | Individual responsibility is clear. | Individual versus team work is clear. |  |
| Evidence | Metric/link absence becomes a question, not an invention. | Demo/repo/visual absence becomes a question, not an invention. |  |
| Artifact result | Resume output is reviewable. | PPTX narrative and layout are reviewable. |  |

## Future Grounded-Harness Acceptance

These rows apply after the planned grounded drafting implementation.

| Criterion | Evidence Required | Result / Notes |
|---|---|---|
| Source facts visible before save | Preview exposes supported facts separately from prose. |  |
| Assumptions reviewable | Unsupported interpretations are presented as confirmation items. |  |
| No invented metrics | A metric-free fixture produces no numeric outcome claim. |  |
| Intent consistency | Resume and portfolio drafts preserve identical underlying facts. |  |
| Measured efficiency | Harness evaluation records token and latency results for chosen candidate. |  |

## Sign-Off

```text
Automated baseline: PASS / FAIL
Studio workflow: PASS / FAIL
Provider/privacy workflow: PASS / FAIL / SKIP (mock-only)
Output quality: PASS / FAIL / PENDING
Reviewer notes:
```
