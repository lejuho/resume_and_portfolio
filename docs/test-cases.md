# Product Test Case Specification

This document is the product-level test case specification for the card-based resume and portfolio builder. It maps product behavior to maintainable test cases rather than listing every individual pytest function.

## Automated Test Cases

| 고유번호 | 테스트 대상 | 테스트 조건 | 테스트 데이터 | 예상 결과 | 기법 |
|---|---|---|---|---|---|
| TC-CARD-001 | Card ID validation | Card model receives valid kebab-case ID | `my-project-1` | Validation succeeds. | 동등분할 |
| TC-CARD-002 | Card ID validation | Card model receives invalid ID formats | `MyProject`, `my_project`, `my project`, `123-`, `-abc` | Validation fails. | 동등분할 |
| TC-CARD-003 | Summary length validation | English summary is within limit | Summary <= 200 chars | Validation succeeds. | 경곗값분석 |
| TC-CARD-004 | Summary length validation | English summary exceeds limit | Summary > 200 chars | Validation fails. | 경곗값분석 |
| TC-CARD-005 | Korean summary validation | Korean summary is within limit | `summary_ko` <= 250 chars | Validation succeeds. | 경곗값분석 |
| TC-CARD-006 | Korean summary validation | Korean summary exceeds limit | `summary_ko` > 250 chars | Validation fails. | 경곗값분석 |
| TC-CARD-007 | Card type validation | Card uses supported type enum | `project`, `hackathon`, `talk`, etc. | Validation succeeds. | 동등분할 |
| TC-CARD-008 | Card type validation | Card uses unsupported type | `invalid_type` | Validation fails. | 동등분할 |
| TC-CARD-009 | Visual path validation | Normal validation mode loads card with missing visual path | `visuals[].path=assets/missing.png` | Repo reports validation error. | 동등분할 |
| TC-CARD-010 | Portfolio visual tolerance | Portfolio mode loads card with missing visual path | Same missing visual card | Missing visual is tolerated for portfolio rendering. | 동등분할 |
| TC-CARD-011 | Visual path validation | Card references existing asset | Existing path under temp repo | Validation succeeds. | 동등분할 |
| TC-CARD-012 | Warning generation | Live card has no evidence | `evidence=[]` | Warning is recorded, not fatal. | 경곗값분석 |
| TC-CARD-013 | Warning generation | Card has too many metrics | More than 5 metrics | Warning is recorded, not fatal. | 경곗값분석 |
| TC-CARD-014 | Warning generation | Live card narrative is too short | `status=live`, short narrative | Warning is recorded. | 경곗값분석 |
| TC-CARD-015 | Narrative fallback | Frontmatter narrative is absent and MDX body exists | Markdown body text | Body is used as effective narrative. | 기능 테스트 |
| TC-CARD-016 | Narrative precedence | Frontmatter narrative and MDX body both exist | Both fields present | Frontmatter narrative is preferred. | 기능 테스트 |
| TC-CARD-017 | Card parsing | Valid MDX file is parsed | `cards/YYYY-MM-id.mdx` with matching `id` | Card object is created. | 오류추정 |
| TC-CARD-018 | Filename/id consistency | Filename does not contain frontmatter ID | `2026-05-other.mdx`, `id: sample` | Repo reports validation error. | 오류추정 |
| TC-CARD-019 | Duplicate ID detection | Repo contains two cards with same `id` | Two MDX files with identical ID | Repo reports duplicate ID error. | 오류추정 |
| TC-CARD-020 | Card lookup | Repo looks up existing card by ID | Existing `sample-card` | Matching card is returned. | 오류추정 |
| TC-CARD-021 | Card lookup false-positive prevention | Repo lookup receives suffix-like ID | Files with similar suffixes | Exact intended card is returned; partial match is not accepted. | 오류추정 |
| TC-SEL-001 | Default selection | No status filter is supplied | Mixed live/draft/archived cards | Only live cards are selected by default. | 동등분할 |
| TC-SEL-002 | Status filtering | Status filter includes archived | `status=archived` | Archived cards are included as requested. | 동등분할 |
| TC-SEL-003 | Multi-status filtering | Multiple statuses are supplied | `status=live,draft` | Cards matching either status are selected. | 동등분할 |
| TC-SEL-004 | Type filtering | Single type is supplied | `type=project` | Only matching type is selected. | 동등분할 |
| TC-SEL-005 | Multi-type filtering | Multiple types are supplied | `type=project,hackathon` | Cards matching any supplied type are selected. | 동등분할 |
| TC-SEL-006 | Domain tag filtering | Tag exists in `tags.domain` | `tag=web3` | Matching cards are selected. | 동등분할 |
| TC-SEL-007 | Skill tag filtering | Tag exists in `tags.skill` | `tag=python` | Matching cards are selected. | 동등분할 |
| TC-SEL-008 | Audience tag filtering | Tag exists in `tags.audience` | `tag=recruiter` | Matching cards are selected. | 동등분할 |
| TC-SEL-009 | Tag OR filtering | Multiple tags are supplied | `tag=web3,python` | Cards matching any tag are selected. | 동등분할 |
| TC-SEL-010 | Tag no-match behavior | Tag does not exist | `tag=nonexistent` | No cards are selected. | 동등분할 |
| TC-SEL-011 | Since filtering | Lower date bound is supplied | `since=2026-01` | Only cards on/after bound are selected. | 경곗값분석 |
| TC-SEL-012 | Until filtering | Upper date bound is supplied | `until=2026-05` | Cards in or before target month are selected. | 경곗값분석 |
| TC-SEL-013 | Until month inclusivity | Date is first or last day of until month | `until=2026-05` | Cards within that whole month are included. | 경곗값분석 |
| TC-SEL-014 | Date descending sort | Sort mode is date-desc | Mixed card dates | Newest cards appear first. | 동등분할 |
| TC-SEL-015 | Date ascending sort | Sort mode is date-asc | Mixed card dates | Oldest cards appear first. | 동등분할 |
| TC-SEL-016 | Title sort | Sort mode is title | Mixed titles | Cards are ordered by title. | 동등분할 |
| TC-SEL-017 | Max items | Max item limit is supplied | `max_items=2` | Result is truncated to the limit. | 경곗값분석 |
| TC-SEL-018 | Explicit card selection | Explicit IDs are supplied with filters | `cards=id1,id2` and conflicting filters | Explicit IDs bypass filters and preserve order. | 동등분할 |
| TC-CLI-001 | Root help | User requests CLI help | `uv run pcli --help` | Help shows main command list. | 시나리오 |
| TC-CLI-002 | Subcommand help | User requests command help | `new`, `validate`, `ls`, `show`, `build resume`, `build portfolio`, `llm`, `preset` | Each command prints usage and exits successfully. | 시나리오 |
| TC-CLI-003 | New card creation | User creates valid card | `pcli new hackathon my-card --title ... --start ...` | New MDX file is created with expected filename. | 시나리오 |
| TC-CLI-004 | New invalid type | User creates card with unsupported type | `pcli new invalid my-card` | Command fails. | 시나리오 |
| TC-CLI-005 | New invalid slug | User creates card with invalid slug | `My Card` | Command fails. | 시나리오 |
| TC-CLI-006 | New duplicate slug | User creates duplicate card | Existing ID | Command fails without overwrite. | 시나리오 |
| TC-CLI-007 | Validate success | Repo has valid cards | Current card set | Command exits 0. | 시나리오 |
| TC-CLI-008 | Validate failure | Repo has invalid card | Broken temp card | Command exits non-zero and reports error. | 시나리오 |
| TC-CLI-009 | List cards | User lists cards | Valid repo | Rich table contains expected cards. | 시나리오 |
| TC-CLI-010 | List with type filter | User filters list by type | `--type hackathon` | Only matching cards are shown. | 시나리오 |
| TC-CLI-011 | Show existing card | User shows known ID or filename stem | Existing card ID/stem | Card details are printed. | 시나리오 |
| TC-CLI-012 | Show missing card | User shows unknown card | Missing ID | Command fails with not found. | 시나리오 |
| TC-BUILD-001 | Resume dry-run | User runs resume dry-run | `pcli build resume --dry-run` | Selected cards are printed and no PDF is created. | 경곗값분석 |
| TC-BUILD-002 | Portfolio dry-run | User runs portfolio dry-run | `pcli build portfolio --dry-run` | Selected cards are printed and no PPTX is created. | 경곗값분석 |
| TC-BUILD-003 | Build option validation | Invalid tone is supplied | `--tone invalid` | Command fails. | 경곗값분석 |
| TC-BUILD-004 | Build option validation | Invalid language is supplied | `--lang invalid` | Command fails. | 경곗값분석 |
| TC-BUILD-005 | Build option validation | Invalid max item value is supplied | `--max-items 0` or negative | Command fails. | 경곗값분석 |
| TC-BUILD-006 | Portfolio layout validation | Unsupported layout is supplied | `--layout invalid` | Command fails. | 동등분할 |
| TC-BUILD-007 | Portfolio PPTX creation | User builds portfolio | Valid cards and output path | PPTX file is created. | 기능 테스트 |
| TC-BUILD-008 | Portfolio missing visual fallback | Portfolio build includes missing visual | Missing visual reference in portfolio mode | Build succeeds with placeholder behavior. | 기능 테스트 |
| TC-BUILD-009 | Portfolio default output path | User builds without `--out` | `pcli build portfolio` | PPTX is written under `output/portfolios/`. | 기능 테스트 |
| TC-BUILD-010 | Explicit cards in portfolio | User passes `--cards` plus filters | Explicit IDs and conflicting filters | Explicit cards are used. | 기능 테스트 |
| TC-PRESET-001 | Preset loading | Existing preset is loaded | `presets/bok-interview.yaml` | Preset object is returned. | 상태전이 |
| TC-PRESET-002 | Missing preset | Unknown preset is requested | Missing preset name | Command/helper fails clearly. | 상태전이 |
| TC-PRESET-003 | Missing preset target | Preset has no `target` | Malformed YAML | Load/run fails. | 상태전이 |
| TC-PRESET-004 | Include/exclude behavior | Preset has include and exclude cards | Preset YAML | Selection respects include/exclude semantics. | 상태전이 |
| TC-PRESET-005 | List-format filters | Preset uses YAML list filters | `tags: [web3]`, `types: [hackathon]` | Filters are normalized and applied. | 동등분할 |
| TC-PRESET-006 | String-format filters | Preset uses comma-separated filters | `tags: web3,solana` | Filters are applied. | 동등분할 |
| TC-PRESET-007 | Exclude with explicit IDs | Explicit IDs include excluded card | Explicit + exclude list | Excluded cards are removed where preset semantics require. | 상태전이 |
| TC-PRESET-008 | Preset save | Last build args are saved | `pcli preset save name` | YAML preset is written. | 상태전이 |
| TC-PRESET-009 | Preset save without cache | No last-build cache exists | Save command | Command fails clearly. | 상태전이 |
| TC-PRESET-010 | BOK summary requirement | BOK preset selects card without `summary_ko` | Missing Korean summary | Build fails before Typst. | 시나리오 |
| TC-PRESET-011 | BOK valid selection | BOK preset selects cards with `summary_ko` | Valid BOK cards | Build/dry-run succeeds. | 시나리오 |
| TC-PRESET-012 | Portfolio grouped layout | Preset or command uses grouped layout | `layout=grouped-by-type` | PPTX/dry-run succeeds. | 시나리오 |
| TC-PRESET-013 | Portfolio timeline layout | Preset or command uses timeline layout | `layout=timeline` | PPTX/dry-run succeeds. | 시나리오 |
| TC-PRESET-014 | Preset run | User runs portfolio preset | `pcli preset run colosseum` | Target build command succeeds. | 시나리오 |
| TC-LLM-001 | Cache key stability | Same input is hashed twice | Same request payload | Same cache key is produced. | 기능 테스트 |
| TC-LLM-002 | Cache key variation | Input content changes | Different prompt/card/JD | Different cache key is produced. | 기능 테스트 |
| TC-LLM-003 | Cache read/write | Valid cache file is written and read | Temp cache dir | Cached response round-trips. | 상태전이 |
| TC-LLM-004 | Missing cache | Cache file does not exist | Unknown key | Cache read returns none. | 오류추정 |
| TC-LLM-005 | Corrupt cache | Cache file is invalid JSON | Corrupt file | Cache read returns none safely. | 오류추정 |
| TC-LLM-006 | Card scoring | Fake LLM returns scores | Fake client response | Cards are sorted by score descending. | 상태전이 |
| TC-LLM-007 | Card scoring cache | Same scoring request runs twice | Cache enabled | Second call uses cache. | 상태전이 |
| TC-LLM-008 | No-cache behavior | Scoring request disables cache | `--no-cache` equivalent | Client is called again. | 상태전이 |
| TC-LLM-009 | Malformed scoring response | LLM returns invalid JSON/shape | Fake malformed response | Error is raised. | 오류추정 |
| TC-LLM-010 | Summary rewrite | Fake LLM rewrites summary | Card + JD + tone | Rewritten string is returned. | 상태전이 |
| TC-LLM-011 | Rewrite cache | Same rewrite request runs twice | Cache enabled | Second call uses cache. | 상태전이 |
| TC-LLM-012 | Rewrite tone variation | Tone changes | `formal` vs `technical` | Cache key/output path differs. | 기능 테스트 |
| TC-LLM-013 | Non-mutating rewrite | Rewrite is performed | Source card object | Original card is not mutated. | 기능 테스트 |
| TC-LLM-014 | Korean rewrite source | `lang=ko` is requested | Card with `summary_ko` | Korean summary is used as source. | 기능 테스트 |
| TC-LLM-015 | Suggest card | Fake LLM suggests frontmatter | Source note file | Required draft fields are returned. | 오류추정 |
| TC-LLM-016 | Suggest malformed response | LLM returns invalid suggestion | Fake malformed response | Error is raised. | 오류추정 |
| TC-LLM-017 | Missing API key | Live client is requested without key | No `ANTHROPIC_API_KEY` | Clear error is raised. | 오류추정 |
| TC-LLM-018 | Build resume with LLM metadata | Resume build uses LLM fake client | JD fixture + fake client | Resume data JSON includes LLM metadata. | 기능 테스트 |
| TC-DASH-001 | Dashboard index | Browser/API requests `/` | Test client | HTTP 200 and page contains card data. | 동등분할 |
| TC-DASH-002 | Dashboard card API | Client requests `/api/cards` | Valid repo | JSON list contains expected card shape. | 동등분할 |
| TC-DASH-003 | Dashboard filters | Client filters by type/status | Query params | JSON result respects filters. | 동등분할 |
| TC-DASH-004 | Dashboard build dry-run | Client posts selected IDs | `/api/build`, `dry_run=true` | Command includes `--cards` and `--dry-run`. | 동등분할 |
| TC-DASH-005 | Dashboard real build command | Client posts dry_run false | `/api/build`, `dry_run=false` | Command omits `--dry-run`. | 동등분할 |
| TC-DASH-006 | Dashboard build failure | Subprocess returns failure | Mocked failed subprocess | Structured JSON includes `ok=false`, exit code, stderr. | 동등분할 |
| TC-DASH-007 | Invalid build target | Client posts unsupported target | `target=hack` | HTTP 400 and structured error. | 동등분할 |
| TC-DASH-008 | Build mutation safety | Dashboard build is triggered | Existing MDX file | Source card file remains unchanged. | 회귀/오류추정 |
| TC-DASH-009 | Build result schema | Build API returns response | Mocked success | JSON includes `ok`, `exit_code`, `stdout`, `stderr`, `command`, `output_path`, `target`, `dry_run`, `selected_ids`. | 동등분할 |
| TC-DASH-010 | Selected ID ordering | Client posts ordered selected IDs | `["card-b","card-a","card-c"]` | Response and command preserve order. | 회귀/오류추정 |
| TC-DASH-011 | Output path parsing | Build stdout contains resume path | `output/resumes/file.pdf` | Parser returns output path. | 회귀/오류추정 |
| TC-DASH-012 | Output path parsing | Build stdout contains portfolio path | `output/portfolios/file.pptx` | Parser returns output path. | 회귀/오류추정 |
| TC-DASH-013 | Output path parsing | Build stdout uses Windows separators | `output\\resumes\\file.pdf` | Parser returns output path. | 회귀/오류추정 |
| TC-DASH-014 | Output path parsing | Dry-run stdout has no output file | `No files written` | Parser returns none. | 회귀/오류추정 |
| TC-DASH-015 | Output path parsing | Output path contains spaces or label | `Resume written: C:\some dir\...pdf` | Parser extracts path without label. | 회귀/오류추정 |
| TC-DASH-016 | Output path false positive | Error line mentions output folder and `.pdf` | Error message | Parser returns none. | 회귀/오류추정 |
| TC-DASH-017 | Get card detail | Client requests existing card | `/api/cards/sample-card` | JSON includes fields and body. | 동등분할 |
| TC-DASH-018 | Get missing card detail | Client requests unknown card | Missing ID | HTTP 404. | 동등분할 |
| TC-DASH-019 | Get invalid card ID | Client requests invalid ID | `INVALID_ID` | HTTP 400. | 동등분할 |
| TC-DASH-020 | Create card | Client posts valid new card | ID, title, type, start date, summary | New MDX file is written. | 동등분할 |
| TC-DASH-021 | Create defaults | Client creates card without status/visibility | Minimal valid create payload | Card defaults to `draft` and `public`. | 동등분할 |
| TC-DASH-022 | Create duplicate | Client creates existing ID | Duplicate ID same month | HTTP 409 and no overwrite. | 오류추정 |
| TC-DASH-023 | Create cross-month duplicate | Client creates existing ID with different month | Duplicate ID different `period_start` | HTTP 409 and no second file. | 회귀/오류추정 |
| TC-DASH-024 | Create invalid ID | Client creates invalid ID | `INVALID ID!` | HTTP 400. | 오류추정 |
| TC-DASH-025 | Create invalid type | Client creates unsupported type | `notavalidtype` | HTTP 422. | 오류추정 |
| TC-DASH-026 | Create traversal attempt | Client sends invalid start/path-like data | `period_start=../../../etc/passwd` | HTTP 400 and no file write. | 오류추정 |
| TC-DASH-027 | Update card basic fields | Client updates title/summary | Valid fields payload | Target MDX is updated. | 기능 테스트 |
| TC-DASH-028 | Update preserves fields | Client updates one field only | `summary` only | Other metadata remains present. | 오류추정 |
| TC-DASH-029 | Update invalid data | Client updates invalid type | `type=notvalid` | HTTP 422 and original file unchanged. | 오류추정 |
| TC-DASH-030 | Update missing card | Client updates unknown ID | Missing ID | HTTP 404. | 오류추정 |
| TC-DASH-031 | Update invalid URL ID | Client updates invalid ID | `INVALID_ID` | HTTP 400. | 오류추정 |
| TC-DASH-032 | ID immutability | Client tries to change `fields.id` | URL ID differs from body ID | HTTP 400 and original file unchanged. | 회귀/오류추정 |
| TC-DASH-033 | ID immutability no-op | Client sends same `fields.id` | URL ID equals body ID | Update succeeds. | 동등분할 |
| TC-DASH-034 | Dashboard UI hooks | Dashboard page renders authoring buttons | `/` | New/edit controls are present. | 시나리오 |
| TC-DASH-035 | Update tags | Client updates tag groups | Domain/skill/audience lists | YAML contains list values. | 시나리오 |
| TC-DASH-036 | Update metrics | Client updates metrics list | Metric strings | YAML contains metrics. | 시나리오 |
| TC-DASH-037 | Update evidence | Client updates evidence list | `type=repo`, URL | YAML contains evidence entry. | 시나리오 |
| TC-DASH-038 | Reject invalid evidence | Client sends unsupported evidence type | `type=invalid_type` | HTTP 422 and original file unchanged. | 동등분할 |
| TC-DASH-039 | Update visuals | Client updates visual reference | Existing `assets/hero.png` | Update succeeds and YAML contains visual. | 동등분할 |
| TC-DASH-040 | Reject invalid visual role | Client sends unsupported visual role | `role=invalid_role` | HTTP 422 and original file unchanged. | 오류추정 |
| TC-DASH-041 | Update body | Client updates markdown body | `# Narrative` body | MDX body is updated. | 오류추정 |
| TC-DASH-042 | Visual hints | Card detail includes visual references | Visual path missing from filesystem | JSON includes `visual_hints[path]=false`. | 오류추정 |
| TC-DASH-043 | Static JS | Client requests dashboard JS | `/static/dashboard.js` | HTTP 200 and JS content is served. | 오류추정 |
| TC-DASH-044 | Reject missing visual path on update | Client saves missing relative visual | `assets/missing.png` | HTTP 422 and original file unchanged. | 동등분할/오류추정 |
| TC-DASH-045 | Accept existing visual path on update | Client saves existing repo-local asset | `assets/hero.png` exists | HTTP 200. | 동등분할/오류추정 |
| TC-DASH-046 | New-card detail UX | New card form opens | Dashboard page | Detail hint exists; detail-only sections are not silently saved on create. | 동등분할/오류추정 |
| TC-DASH-047 | Reject absolute visual path | Client saves absolute path | Existing absolute path outside repo | HTTP 422 and original file unchanged. | 동등분할/오류추정 |
| TC-DASH-048 | Reject visual traversal path | Client saves path escaping repo | `../outside.png` | HTTP 422 and original file unchanged. | 동등분할/오류추정 |
| TC-PORT-001 | Portfolio missing visual rendering | Renderer receives card with missing visual | Card with missing visual path | Placeholder renders and deck creation succeeds. | 시나리오 |
| TC-PORT-002 | Portfolio narrative toggle | Renderer builds with `--no-narrative` | Card with narrative text | Narrative text is excluded from PPTX. | 시나리오 |
| TC-STUDIO-001 | Studio route | Client opens creation workspace | `GET /studio` | HTTP 200 and raw input, intent, preview, save, and dashboard-navigation hooks exist. | 시나리오 |
| TC-STUDIO-002 | Admin route regression | Client opens admin surface | `GET /dashboard` | HTTP 200 and existing dashboard remains available. | 회귀/시나리오 |
| TC-STUDIO-003 | Raw input validation | Refine receives empty or whitespace text | `POST /api/studio/refine` | HTTP 400 with clear input error. | 동등분할/경곗값분석 |
| TC-STUDIO-004 | Intent validation | Refine receives each supported or unsupported intent | `resume`, `portfolio`, `both`, `linkedin` | Supported intents expose their output surfaces; unsupported intent is rejected. | 동등분할 |
| TC-STUDIO-005 | Mock missing-information preview | No LLM key is configured and raw input lacks evidence | Bare activity note | Deterministic draft includes missing-info prompts and `refine_source=mock`. | 동등분할 |
| TC-STUDIO-006 | New draft persistence | User saves reviewed Studio draft | Valid refined draft | Canonical MDX is created as `draft` and passes card validation. | 상태전이 |
| TC-STUDIO-007 | Raw input privacy | Save request includes source raw text | Draft plus sentinel raw value | Saved MDX does not contain raw input unless a future explicit option exists. | 오류추정 |
| TC-STUDIO-008 | Duplicate draft ID | Refined title maps to existing slug | Save same draft twice | HTTP 409 and existing card is not overwritten. | 오류추정 |
| TC-STUDIO-009 | Editable preview handoff | User edits generated output before saving | Edited summary/body/bullet | Saved card contains approved edit and output actions use saved ID. | 상태전이 |
| TC-AI-001 | Environment loading safety | Server starts with local env file | `.env` or `.env.local` | Values load server-side without overwriting process vars or exposing secrets in UI. | 오류추정 |
| TC-AI-002 | Provider resolution | Provider/key combinations are configured | Anthropic, Google, aliases, model override | Correct provider/model/key precedence is applied without returning key value. | 결정테이블 |
| TC-AI-003 | Placeholder key detection | Configuration contains placeholder key | `your_key_here` | Status remains mock/unconfigured. | 동등분할 |
| TC-AI-004 | Configuration status semantics | Status endpoint is requested | `GET /api/studio/ai-status` | Reports configured state only; it does not claim live connectivity or leak keys. | 상태전이/오류추정 |
| TC-AI-005 | User-triggered live connection check | Provider call succeeds or fails | `POST /api/studio/ai-check` with fake provider | Success reports connected; failures map to safe error code without key leakage. | 결정테이블 |
| TC-AI-006 | Gemini adapter | Google provider is configured | Fake Google client response | Gemini refine/check paths return output using configured model. | 동등분할 |
| TC-AI-007 | LLM refine fallback | Configured refine call raises or returns malformed output | Fake LLM failure | Studio returns mock draft instead of failing the authoring workflow. | 오류추정 |

## Planned Grounded-Harness Test Cases

These cases follow the research audit but are not claims about the current implementation.
They should become automated or evaluated tests in the implementation cycle that changes the
prompt contract.

| 고유번호 | 테스트 대상 | 테스트 조건 | 테스트 데이터 | 예상 결과 | 기법 |
|---|---|---|---|---|---|
| PT-GROUND-001 | Unsupported metric prevention | Source note contains no number | Bare project note | No generated claim contains a numeric result; metric appears as missing question only. | 변형관계/오류추정 |
| PT-GROUND-002 | Fact preservation across intent | Same source is refined for resume and portfolio | One dated, measured activity | Both outputs preserve date, metric, evidence, and role consistently. | 변형관계 |
| PT-GROUND-003 | Team attribution uncertainty | Input mentions team result without personal responsibility | Team project note | Assumption/missing-info marks contribution unclear; no sole-ownership claim is produced. | 동등분할/오류추정 |
| PT-GROUND-004 | Evidence enrichment | Second input adds a URL to otherwise identical note | Note without/with repo URL | Evidence prompt is removed or satisfied without changing unrelated facts. | 변형관계 |
| PT-GROUND-005 | Track K quality rubric | Intent targets Korean formal application | Korean formal activity fixture | Draft is concise, formal, job-relevant, and factual under Track K rubric. | 시나리오/체크리스트 |
| PT-GROUND-006 | Track G portfolio rubric | Intent targets global tech/Web3 portfolio | Technical project fixture | Draft separates problem, contribution, decision, outcome/evidence, and insight. | 시나리오/체크리스트 |
| PT-GROUND-007 | Structured response reliability | LLM is called for benchmark corpus | 12 anonymized inputs | Parsed structured response succeeds for all evaluation calls. | 경곗값분석/통계적 평가 |
| PT-GROUND-008 | Harness efficiency comparison | Candidate prompts run on same corpus/model | Baseline, grounded one-shot, staged candidate | Token/latency/quality table is captured; selected candidate satisfies quality gate with lowest usable-draft token cost. | 비교평가 |
## Implemented Application Writing Test Cases (Cycle 21)

These cases were planned for the application-writing harness. Automated equivalents are
implemented in `tests/test_cycle21.py` as of Cycle 21.

| 고유번호 | 테스트 대상 | 테스트 조건 | 테스트 데이터 | 예상 결과 | 기법 |
|---|---|---|---|---|---|
| PT-APP-001 | Cover-letter source separation | Cover-letter output is generated | Approved cards plus supplied organization/JD context | Personal claims cite card facts only; organization/fit language uses supplied target context only. | 결정테이블/오류추정 |
| PT-APP-002 | Question interpretation | User supplies an application question | Collaboration, problem-solving, motivation, or ethics question | Preview exposes interpreted competency/question intent before answer draft. | 동등분할 |
| PT-APP-003 | Episode selection | Several cards could answer one question | Cards with different evidence strength | Preview identifies selected card(s) and a reason tied to the question. | 시나리오 |
| PT-APP-004 | Missing target context | User requests motivation/fit answer without organization or JD evidence | Card set plus motivation question only | Draft does not invent organization motivation; missing target context is requested. | 변형관계/오류추정 |
| PT-APP-005 | Character-count boundary | Answer has supplied minimum/maximum length | Below, at, and above character limit | Preview reports count/compliance and generated submission version respects the defined boundary. | 경곗값분석 |
| PT-APP-006 | Blind-hiring restriction | Target context forbids personal-background attributes | NCS-style application instruction plus cards | Draft excludes prohibited identity/background information not required for competency proof. | 결정테이블/시나리오 |

## Requirement Trace

| Requirement area | Requirement source | Automated cases | Manual/evaluation evidence |
|---|---|---|---|
| Card storage and CLI outputs | `requirements.md` | `TC-CARD-*`, `TC-SEL-*`, `TC-CLI-*`, `TC-BUILD-*`, `TC-PRESET-*` | `docs/acceptance-v1.md` |
| Admin dashboard | `requirements-dashboard.md` sections 2.1, 6, 7 | `TC-DASH-*` | `MT-DASH-*`; `docs/acceptance-studio.md` admin regression section |
| Studio capture, preview, save | `requirements-dashboard.md` section 5 | `TC-STUDIO-*` | `docs/acceptance-studio.md` |
| Optional LLM and provider configuration | `requirements-dashboard.md` section 8 and D-006/D-007 | `TC-LLM-*`, `TC-AI-*` | `docs/acceptance-studio.md` |
| Grounded intent-specific drafting | `requirements-dashboard.md` sections 8.4-8.5, 8.7 and D-008 | `PT-GROUND-*` (planned) | `docs/research/llm-harness-evaluation.md` |
| Application writing from canonical memory | `requirements-dashboard.md` section 8.6 and D-009 | `PT-APP-*` | `docs/acceptance-studio.md` Application Writing Acceptance (Cycle 21) |

## Manual Acceptance Test Cases

| 고유번호 | 테스트 대상 | 테스트 조건 | 테스트 데이터 | 예상 결과 | 기법 |
|---|---|---|---|---|---|
| MT-ACC-001 | Real card corpus | User reviews real card repository | Actual `cards/` directory | User can maintain real activity cards; target count and quality are acceptable. | 시나리오 |
| MT-ACC-002 | Resume PDF visual output | Typst is installed | `uv run pcli build resume --preset bok-interview` | PDF is generated within target time and visually fits expected resume layout. | 시나리오 |
| MT-ACC-003 | Portfolio PPTX visual output | PowerPoint/Keynote is available | `uv run pcli build portfolio --tags web3` | PPTX opens successfully and slides render without major overlap. | 시나리오 |
| MT-ACC-004 | LLM-tailored resume | `ANTHROPIC_API_KEY` is configured | `uv run pcli build resume --jd tests/fixtures/fake-jd.txt --tone formal --show-llm-diff` | Diff is visible and generated PDF reflects rewritten summaries. | 시나리오 |
| MT-ACC-005 | README quickstart | Fresh or clean local setup | README quickstart steps | First PDF can be produced within the intended onboarding window. | 시나리오 |
| MT-DASH-001 | Dashboard startup | Local machine can run Flask app | `uv run pcli dashboard --port <free-port>` | Dashboard starts and loads in browser. | 시나리오 |
| MT-DASH-002 | Dashboard browse/filter/select | Dashboard is running with real cards | Search, type/status/tag filters, selected cards | User can find and select intended cards. | 시나리오 |
| MT-DASH-003 | Dashboard build action | Dashboard is running | Resume/portfolio dry-run and build buttons | Build result panel shows command, status, raw log, and output path when applicable. | 시나리오 |
| MT-DASH-004 | Dashboard card creation | Dashboard is running | New draft card data | Draft card is created and appears in list after refresh. | 시나리오 |
| MT-DASH-005 | Dashboard detail editing | Existing draft/test card is open | Tags, metrics, evidence, visuals, body edits | Save succeeds, table refreshes, and `uv run pcli validate <id>` passes. | 시나리오 |
| MT-DASH-006 | Dashboard invalid edit safety | Existing draft/test card is open | Invalid type, invalid evidence, missing/absolute/traversal visual path | Save is rejected and original MDX remains unchanged. | 시나리오 |
| MT-STUDIO-001 | Studio creation flow | Local dashboard is running | Messy real activity text, `Both` intent | Preview appears, can be edited, saves as draft card, and is visible in admin dashboard. | 시나리오 |
| MT-STUDIO-002 | Mock versus AI source clarity | Provider is alternately unavailable and available | Same non-sensitive input | UI identifies mock or LLM source without representing configuration as verified connection. | 상태전이 |
| MT-STUDIO-003 | Live provider check | Google or Anthropic key is configured server-side | User clicks connection check | Success/failure feedback is clear and no key is exposed. | 시나리오/오류추정 |
| MT-STUDIO-004 | Resume and portfolio use of saved card | Draft is reviewed and promoted/selected as appropriate | Saved real card | Existing build flows produce intended PDF/PPTX without source corruption. | 상태전이 |

## Maintenance Notes

- Keep this file at the product behavior level. Add rows when new behavior is introduced or when a regression class is discovered.
- Keep pytest function names free to change; this document should track the externally meaningful behavior.
- Use `docs/acceptance-v1.md` and future dashboard acceptance documents for dated execution evidence.
