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

## Grounded Harness Acceptance (Cycle 20 Implemented)

| Criterion | Evidence Required | Result / Notes |
|---|---|---|
| Source facts visible before save | Preview exposes supported facts separately from prose. | Implemented: `source_facts` and `assumptions` rendered before Save button. |
| Assumptions reviewable | Unsupported interpretations are presented as confirmation items. | Implemented. |
| No invented metrics | A metric-free fixture produces no numeric outcome claim. | Enforced by grounded prompt and mock path. |
| Intent consistency | Resume and portfolio drafts preserve identical underlying facts. | LLM and mock paths both extract from raw text only. |
| Measured efficiency | Harness evaluation records token and latency results for chosen candidate. | `scripts/evaluate_studio_grounding.py --live` captures this. |

## Application Writing Acceptance (Cycle 21 Implemented)

Start the local application:

```bash
uv run pcli dashboard --port 5097
```

| # | Scenario | Action | Expected Result | Result / Notes |
|---:|---|---|---|---|
| 1 | Panel visibility | Open `/studio`. | Application Writing panel is visibly separate from raw Career Memory capture. |  |
| 2 | Live-card selector | Open the panel without any live cards. | "No live cards" placeholder is shown; generate is blocked. |  |
| 3 | Verified draft provenance | Select one live card; set organization and role; click Generate. | Preview shows `fact_ledger` entries from selected card; `draft_provenance=server_composed`; "Verified draft" label is visible above the copyable text. |  |
| 4 | Answer preview | Select a card; enter a question and character limit; click Generate. | `question_intent` is shown (advisory); `character_count` and `within_limit` reflect the server-composed draft. |  |
| 5 | Source separation | Add organization to an existing answer request. | `fact_ledger` entries from card are unchanged; org appears only in `target_context_used`. |  |
| 6 | AI guidance section | Generate with a provider configured. | "AI Guidance" section is visible and distinct from the verified draft; guidance text is not reachable via the Copy action. |  |
| 7 | Blind-hiring: flagged card | Select a card whose title or summary contains education/background text; enable Blind Hiring. | `BLIND_HIRING_PERSONAL_IDENTIFIERS` in missing info; flagged content absent from draft, `fact_ledger`, and `selected_cards`. Provider is not called (mock path used). |  |
| 8 | Blind-hiring: guidance screen | Configure a provider; select a non-flagged card; enable Blind Hiring; generate. | If guidance returns any identity/background phrase, it is absent from `ai_guidance` and `BLIND_HIRING_GUIDANCE_REDACTED` appears in missing info. |  |
| 9 | Selection rationale | Generate any preview. | `selected_cards` section shows each card and its `selection_reason`; `selected_facts` IDs trace to activity text in the draft. |  |
| 10 | Fallback reason (mock) | Run without a configured provider. | `Source: Mock — not_configured` is shown in the application panel. |  |
| 11 | No card created | Generate a cover letter or answer preview. | Card count in Dashboard does not increase. |  |
| 12 | Copy action | Click Copy to clipboard after generating. | Verified draft text is copied; guidance section text is not included; button briefly shows "Copied!". |  |
| 13 | Refine fallback reason | Run without a provider; generate a Career Memory refine. | `Source: Mock — not_configured` appears below the refine preview. |  |

## Sign-Off

```text
Automated baseline: PASS / FAIL
Studio workflow: PASS / FAIL
Provider/privacy workflow: PASS / FAIL / SKIP (mock-only)
Output quality: PASS / FAIL / PENDING
Reviewer notes:
```
