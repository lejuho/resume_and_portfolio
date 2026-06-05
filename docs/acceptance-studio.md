# Career Studio Acceptance Evidence

Status: execution checklist for Studio, Application Writing (through Cycle 26), and Workspace (Cycles 27–30); last reviewed Cycle 31 audit (2026-06-05)
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
| 7 | Blind-hiring: flagged card | Select a card whose title or summary contains education/background text; enable Blind Hiring. | Per-field screening: flagged title/summary excluded; card still appears if it has a safe metric or evidence fact, using `Evidence C1` as display label and opaque ref `C1` in provider payload and preview. `BLIND_HIRING_PERSONAL_IDENTIFIERS` in missing info. If all selected cards have no usable field, HTTP 422 is returned before any provider call. Canonical card ID absent from `fact_ledger`, `selected_cards`, and serialized preview JSON. |  |
| 8 | Blind-hiring: advisory sanitizer | Configure a provider; select a non-flagged card; enable Blind Hiring; generate with a provider response that contains identity/background text in `question_intent`, `competency_target`, `missing_info[].message`, and `ai_guidance[]`. | All four fields are screened by `_sanitize_advisory`: identity-bearing `question_intent` / `competency_target` / `missing_info[].message` values are replaced with "withheld" sentinel strings and `BLIND_HIRING_ADVISORY_REDACTED` appears in `missing_info`; identity-bearing `ai_guidance` items are dropped and `BLIND_HIRING_GUIDANCE_REDACTED` appears in `missing_info`. No identity/background phrase appears in any advisory visible field of the returned preview. |  |
| 9 | Selection rationale | Generate any preview. | `selected_cards` section shows each card and its `selection_reason`; `selected_facts` IDs trace to activity text in the draft. |  |
| 10 | Fallback reason (mock) | Run without a configured provider. | `Source: Mock — not_configured` is shown in the application panel. |  |
| 11 | No card created | Generate a cover letter or answer preview. | Card count in Dashboard does not increase. |  |
| 12 | Copy action | Click Copy to clipboard after generating. | Verified draft text is copied; guidance section text is not included; button briefly shows "Copied!". |  |
| 13 | Refine fallback reason | Run without a provider; generate a Career Memory refine. | `Source: Mock — not_configured` appears below the refine preview. |  |
| 14 | Export handoff packet | Generate a preview; click "Export handoff packet". | A plain-text packet is downloaded (or copied as fallback) containing: output type, target context used, verified draft, evidence summary using safe display labels (opaque refs in blind-hiring mode), and AI guidance clearly labeled "ADVISORY". The existing "Copy Verified draft" button behavior is unchanged. No new card is created. Before preview generation the export button is hidden. |  |

## Application Writing Improvements (Cycles 22–23 Implemented)

No additional manual acceptance flows are required for Cycles 22–23; they improved existing
behavior (Studio UI smoke tests, selector metadata, empty/error labels, copy-button label
consistency) without adding a new user-visible workflow. The automated regression suites in
`tests/test_cycle22.py` and `tests/test_cycle23.py` provide evidence.

## Workspace Acceptance (Cycles 27–30 Implemented)

Start the local application:

```bash
uv run pcli dashboard --port 5097
```

Then open `http://127.0.0.1:5097/workspace`.

### Automated Baseline (Workspace)

| Criterion | Command | Result | Notes |
|---|---|---|---|
| Workspace route tests | `uv run pytest tests/test_cycle27.py tests/test_cycle28.py tests/test_cycle29.py tests/test_cycle30.py -v` | | |
| Full suite | `uv run pytest -v` | | |
| Lint / format | `uv run ruff check scripts tests && uv run ruff format --check scripts tests` | | |

### Manual Workspace Flow

| # | Scenario | Action | Expected Result | Result / Notes |
|---:|---|---|---|---|
| 1 | Route independence | Open `/workspace`, then `/studio`, then `/dashboard`. | All three routes are available and independently navigable; no route replaces another. | |
| 2 | Card loading | Open `/workspace` with live cards in the repo. | Left pane shows "N live cards" and renders a card item for each with pill, title, summary (clamped), and metadata. | |
| 3 | Empty card list | Open `/workspace` with no live cards. | Left pane shows "No live cards found. Mark cards as Live in Dashboard first." | |
| 4 | Card selection | Check a card checkbox. | Card item receives `ws-card-selected` tint/border; coverage gap message updates. | |
| 5 | Fit signal — target entry | Select a card; type a role or question into any target field. | Coverage value updates to a percentage; matched terms appear below the gap message when overlap exists. | |
| 6 | Fit signal — no match | Select a card; type unrelated words with no keyword overlap. | Coverage value shows 0%; gap message: "No matching terms found. Add relevant keywords to the target." | |
| 7 | Fit signal — missing target | Select a card; leave all target fields empty. | Coverage value shows "—"; gap message: "Add a target role or question to calculate fit." | |
| 8 | Card disclosure — long summary | Select a card whose summary exceeds 2 lines when rendered. | "Show full summary" button is visible below the clamped text. | |
| 9 | Card disclosure — expand | Click "Show full summary". | Full summary is revealed; button text changes to "Collapse summary". | |
| 10 | Card disclosure — collapse | Click "Collapse summary". | Summary is re-clamped to 2 lines. | |
| 11 | Disclosure does not toggle selection | Click "Show full summary" while a card is not selected. | Checkbox state is unchanged after disclosure click. | |
| 12 | Preview generation | Select a card; fill in organization and role; click "Generate preview". | Preview output appears; no new card is created in the dashboard. | |
| 13 | Light / dark toggle | Click "Dark mode" button in header. | Workspace switches to dark palette; button text changes to "Light mode"; preference is stored. | |
| 14 | Dark mode — OS preference | Set OS to dark mode with no stored preference. | Workspace adopts dark palette automatically on load. | |
| 15 | Dark mode — override OS | Set OS to dark mode; click "Light mode" button. | Workspace stays light; preference persists on refresh. | |
| 16 | Keyboard focus | Tab through the page. | All interactive controls (checkboxes, target fields, generate button, theme toggle, disclosure buttons) receive a visible focus ring. | |
| 17 | Long title / summary containment | Use or create a card with a very long title and long summary. | Title wraps without overflowing the left pane; summary is clamped and does not push layout horizontally. | |

### Provider / No-Persistence Checks (Workspace)

| # | Scenario | Action | Expected Result | Result / Notes |
|---:|---|---|---|---|
| 1 | No card created by preview | Generate a preview with live cards selected. | Card file count in `cards/` is unchanged after generation. | |
| 2 | Preview uses existing endpoint | Inspect network request during generation. | `POST /api/studio/application-preview` is called with `output_type`, `card_ids`, `target_context`; no new Workspace-specific backend endpoint is used. | |
| 3 | Mock mode | Run without a configured provider. | Preview shows provider fallback reason; no error is thrown. | SKIP if mock-only environment |

## Sign-Off

```text
Automated baseline: PASS / FAIL
Studio workflow: PASS / FAIL
Provider/privacy workflow: PASS / FAIL / SKIP (mock-only)
Output quality: PASS / FAIL / PENDING
Workspace automated: PASS / FAIL
Workspace manual flow: PASS / FAIL / PENDING
Workspace browser checks (dark mode, keyboard, containment): PASS / FAIL / PENDING
Reviewer notes:
```
