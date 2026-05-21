# Product Test Case Specification

This document is the product-level test case specification for the card-based resume and portfolio builder. It maps product behavior to maintainable test cases rather than listing every individual pytest function.

## Automated Test Cases

| 고유번호 | 테스트 대상 | 테스트 조건 | 테스트 데이터 | 예상 결과 |
|---|---|---|---|---|
| TC-CARD-001 | Card ID validation | Card model receives valid kebab-case ID | `my-project-1` | Validation succeeds. |
| TC-CARD-002 | Card ID validation | Card model receives invalid ID formats | `MyProject`, `my_project`, `my project`, `123-`, `-abc` | Validation fails. |
| TC-CARD-003 | Summary length validation | English summary is within limit | Summary <= 200 chars | Validation succeeds. |
| TC-CARD-004 | Summary length validation | English summary exceeds limit | Summary > 200 chars | Validation fails. |
| TC-CARD-005 | Korean summary validation | Korean summary is within limit | `summary_ko` <= 250 chars | Validation succeeds. |
| TC-CARD-006 | Korean summary validation | Korean summary exceeds limit | `summary_ko` > 250 chars | Validation fails. |
| TC-CARD-007 | Card type validation | Card uses supported type enum | `project`, `hackathon`, `talk`, etc. | Validation succeeds. |
| TC-CARD-008 | Card type validation | Card uses unsupported type | `invalid_type` | Validation fails. |
| TC-CARD-009 | Visual path validation | Normal validation mode loads card with missing visual path | `visuals[].path=assets/missing.png` | Repo reports validation error. |
| TC-CARD-010 | Portfolio visual tolerance | Portfolio mode loads card with missing visual path | Same missing visual card | Missing visual is tolerated for portfolio rendering. |
| TC-CARD-011 | Visual path validation | Card references existing asset | Existing path under temp repo | Validation succeeds. |
| TC-CARD-012 | Warning generation | Live card has no evidence | `evidence=[]` | Warning is recorded, not fatal. |
| TC-CARD-013 | Warning generation | Card has too many metrics | More than 5 metrics | Warning is recorded, not fatal. |
| TC-CARD-014 | Warning generation | Live card narrative is too short | `status=live`, short narrative | Warning is recorded. |
| TC-CARD-015 | Narrative fallback | Frontmatter narrative is absent and MDX body exists | Markdown body text | Body is used as effective narrative. |
| TC-CARD-016 | Narrative precedence | Frontmatter narrative and MDX body both exist | Both fields present | Frontmatter narrative is preferred. |
| TC-CARD-017 | Card parsing | Valid MDX file is parsed | `cards/YYYY-MM-id.mdx` with matching `id` | Card object is created. |
| TC-CARD-018 | Filename/id consistency | Filename does not contain frontmatter ID | `2026-05-other.mdx`, `id: sample` | Repo reports validation error. |
| TC-CARD-019 | Duplicate ID detection | Repo contains two cards with same `id` | Two MDX files with identical ID | Repo reports duplicate ID error. |
| TC-CARD-020 | Card lookup | Repo looks up existing card by ID | Existing `sample-card` | Matching card is returned. |
| TC-CARD-021 | Card lookup false-positive prevention | Repo lookup receives suffix-like ID | Files with similar suffixes | Exact intended card is returned; partial match is not accepted. |
| TC-SEL-001 | Default selection | No status filter is supplied | Mixed live/draft/archived cards | Only live cards are selected by default. |
| TC-SEL-002 | Status filtering | Status filter includes archived | `status=archived` | Archived cards are included as requested. |
| TC-SEL-003 | Multi-status filtering | Multiple statuses are supplied | `status=live,draft` | Cards matching either status are selected. |
| TC-SEL-004 | Type filtering | Single type is supplied | `type=project` | Only matching type is selected. |
| TC-SEL-005 | Multi-type filtering | Multiple types are supplied | `type=project,hackathon` | Cards matching any supplied type are selected. |
| TC-SEL-006 | Domain tag filtering | Tag exists in `tags.domain` | `tag=web3` | Matching cards are selected. |
| TC-SEL-007 | Skill tag filtering | Tag exists in `tags.skill` | `tag=python` | Matching cards are selected. |
| TC-SEL-008 | Audience tag filtering | Tag exists in `tags.audience` | `tag=recruiter` | Matching cards are selected. |
| TC-SEL-009 | Tag OR filtering | Multiple tags are supplied | `tag=web3,python` | Cards matching any tag are selected. |
| TC-SEL-010 | Tag no-match behavior | Tag does not exist | `tag=nonexistent` | No cards are selected. |
| TC-SEL-011 | Since filtering | Lower date bound is supplied | `since=2026-01` | Only cards on/after bound are selected. |
| TC-SEL-012 | Until filtering | Upper date bound is supplied | `until=2026-05` | Cards in or before target month are selected. |
| TC-SEL-013 | Until month inclusivity | Date is first or last day of until month | `until=2026-05` | Cards within that whole month are included. |
| TC-SEL-014 | Date descending sort | Sort mode is date-desc | Mixed card dates | Newest cards appear first. |
| TC-SEL-015 | Date ascending sort | Sort mode is date-asc | Mixed card dates | Oldest cards appear first. |
| TC-SEL-016 | Title sort | Sort mode is title | Mixed titles | Cards are ordered by title. |
| TC-SEL-017 | Max items | Max item limit is supplied | `max_items=2` | Result is truncated to the limit. |
| TC-SEL-018 | Explicit card selection | Explicit IDs are supplied with filters | `cards=id1,id2` and conflicting filters | Explicit IDs bypass filters and preserve order. |
| TC-CLI-001 | Root help | User requests CLI help | `uv run pcli --help` | Help shows main command list. |
| TC-CLI-002 | Subcommand help | User requests command help | `new`, `validate`, `ls`, `show`, `build resume`, `build portfolio`, `llm`, `preset` | Each command prints usage and exits successfully. |
| TC-CLI-003 | New card creation | User creates valid card | `pcli new hackathon my-card --title ... --start ...` | New MDX file is created with expected filename. |
| TC-CLI-004 | New invalid type | User creates card with unsupported type | `pcli new invalid my-card` | Command fails. |
| TC-CLI-005 | New invalid slug | User creates card with invalid slug | `My Card` | Command fails. |
| TC-CLI-006 | New duplicate slug | User creates duplicate card | Existing ID | Command fails without overwrite. |
| TC-CLI-007 | Validate success | Repo has valid cards | Current card set | Command exits 0. |
| TC-CLI-008 | Validate failure | Repo has invalid card | Broken temp card | Command exits non-zero and reports error. |
| TC-CLI-009 | List cards | User lists cards | Valid repo | Rich table contains expected cards. |
| TC-CLI-010 | List with type filter | User filters list by type | `--type hackathon` | Only matching cards are shown. |
| TC-CLI-011 | Show existing card | User shows known ID or filename stem | Existing card ID/stem | Card details are printed. |
| TC-CLI-012 | Show missing card | User shows unknown card | Missing ID | Command fails with not found. |
| TC-BUILD-001 | Resume dry-run | User runs resume dry-run | `pcli build resume --dry-run` | Selected cards are printed and no PDF is created. |
| TC-BUILD-002 | Portfolio dry-run | User runs portfolio dry-run | `pcli build portfolio --dry-run` | Selected cards are printed and no PPTX is created. |
| TC-BUILD-003 | Build option validation | Invalid tone is supplied | `--tone invalid` | Command fails. |
| TC-BUILD-004 | Build option validation | Invalid language is supplied | `--lang invalid` | Command fails. |
| TC-BUILD-005 | Build option validation | Invalid max item value is supplied | `--max-items 0` or negative | Command fails. |
| TC-BUILD-006 | Portfolio layout validation | Unsupported layout is supplied | `--layout invalid` | Command fails. |
| TC-BUILD-007 | Portfolio PPTX creation | User builds portfolio | Valid cards and output path | PPTX file is created. |
| TC-BUILD-008 | Portfolio missing visual fallback | Portfolio build includes missing visual | Missing visual reference in portfolio mode | Build succeeds with placeholder behavior. |
| TC-BUILD-009 | Portfolio default output path | User builds without `--out` | `pcli build portfolio` | PPTX is written under `output/portfolios/`. |
| TC-BUILD-010 | Explicit cards in portfolio | User passes `--cards` plus filters | Explicit IDs and conflicting filters | Explicit cards are used. |
| TC-PRESET-001 | Preset loading | Existing preset is loaded | `presets/bok-interview.yaml` | Preset object is returned. |
| TC-PRESET-002 | Missing preset | Unknown preset is requested | Missing preset name | Command/helper fails clearly. |
| TC-PRESET-003 | Missing preset target | Preset has no `target` | Malformed YAML | Load/run fails. |
| TC-PRESET-004 | Include/exclude behavior | Preset has include and exclude cards | Preset YAML | Selection respects include/exclude semantics. |
| TC-PRESET-005 | List-format filters | Preset uses YAML list filters | `tags: [web3]`, `types: [hackathon]` | Filters are normalized and applied. |
| TC-PRESET-006 | String-format filters | Preset uses comma-separated filters | `tags: web3,solana` | Filters are applied. |
| TC-PRESET-007 | Exclude with explicit IDs | Explicit IDs include excluded card | Explicit + exclude list | Excluded cards are removed where preset semantics require. |
| TC-PRESET-008 | Preset save | Last build args are saved | `pcli preset save name` | YAML preset is written. |
| TC-PRESET-009 | Preset save without cache | No last-build cache exists | Save command | Command fails clearly. |
| TC-PRESET-010 | BOK summary requirement | BOK preset selects card without `summary_ko` | Missing Korean summary | Build fails before Typst. |
| TC-PRESET-011 | BOK valid selection | BOK preset selects cards with `summary_ko` | Valid BOK cards | Build/dry-run succeeds. |
| TC-PRESET-012 | Portfolio grouped layout | Preset or command uses grouped layout | `layout=grouped-by-type` | PPTX/dry-run succeeds. |
| TC-PRESET-013 | Portfolio timeline layout | Preset or command uses timeline layout | `layout=timeline` | PPTX/dry-run succeeds. |
| TC-PRESET-014 | Preset run | User runs portfolio preset | `pcli preset run colosseum` | Target build command succeeds. |
| TC-LLM-001 | Cache key stability | Same input is hashed twice | Same request payload | Same cache key is produced. |
| TC-LLM-002 | Cache key variation | Input content changes | Different prompt/card/JD | Different cache key is produced. |
| TC-LLM-003 | Cache read/write | Valid cache file is written and read | Temp cache dir | Cached response round-trips. |
| TC-LLM-004 | Missing cache | Cache file does not exist | Unknown key | Cache read returns none. |
| TC-LLM-005 | Corrupt cache | Cache file is invalid JSON | Corrupt file | Cache read returns none safely. |
| TC-LLM-006 | Card scoring | Fake LLM returns scores | Fake client response | Cards are sorted by score descending. |
| TC-LLM-007 | Card scoring cache | Same scoring request runs twice | Cache enabled | Second call uses cache. |
| TC-LLM-008 | No-cache behavior | Scoring request disables cache | `--no-cache` equivalent | Client is called again. |
| TC-LLM-009 | Malformed scoring response | LLM returns invalid JSON/shape | Fake malformed response | Error is raised. |
| TC-LLM-010 | Summary rewrite | Fake LLM rewrites summary | Card + JD + tone | Rewritten string is returned. |
| TC-LLM-011 | Rewrite cache | Same rewrite request runs twice | Cache enabled | Second call uses cache. |
| TC-LLM-012 | Rewrite tone variation | Tone changes | `formal` vs `technical` | Cache key/output path differs. |
| TC-LLM-013 | Non-mutating rewrite | Rewrite is performed | Source card object | Original card is not mutated. |
| TC-LLM-014 | Korean rewrite source | `lang=ko` is requested | Card with `summary_ko` | Korean summary is used as source. |
| TC-LLM-015 | Suggest card | Fake LLM suggests frontmatter | Source note file | Required draft fields are returned. |
| TC-LLM-016 | Suggest malformed response | LLM returns invalid suggestion | Fake malformed response | Error is raised. |
| TC-LLM-017 | Missing API key | Live client is requested without key | No `ANTHROPIC_API_KEY` | Clear error is raised. |
| TC-LLM-018 | Build resume with LLM metadata | Resume build uses LLM fake client | JD fixture + fake client | Resume data JSON includes LLM metadata. |
| TC-DASH-001 | Dashboard index | Browser/API requests `/` | Test client | HTTP 200 and page contains card data. |
| TC-DASH-002 | Dashboard card API | Client requests `/api/cards` | Valid repo | JSON list contains expected card shape. |
| TC-DASH-003 | Dashboard filters | Client filters by type/status | Query params | JSON result respects filters. |
| TC-DASH-004 | Dashboard build dry-run | Client posts selected IDs | `/api/build`, `dry_run=true` | Command includes `--cards` and `--dry-run`. |
| TC-DASH-005 | Dashboard real build command | Client posts dry_run false | `/api/build`, `dry_run=false` | Command omits `--dry-run`. |
| TC-DASH-006 | Dashboard build failure | Subprocess returns failure | Mocked failed subprocess | Structured JSON includes `ok=false`, exit code, stderr. |
| TC-DASH-007 | Invalid build target | Client posts unsupported target | `target=hack` | HTTP 400 and structured error. |
| TC-DASH-008 | Build mutation safety | Dashboard build is triggered | Existing MDX file | Source card file remains unchanged. |
| TC-DASH-009 | Build result schema | Build API returns response | Mocked success | JSON includes `ok`, `exit_code`, `stdout`, `stderr`, `command`, `output_path`, `target`, `dry_run`, `selected_ids`. |
| TC-DASH-010 | Selected ID ordering | Client posts ordered selected IDs | `["card-b","card-a","card-c"]` | Response and command preserve order. |
| TC-DASH-011 | Output path parsing | Build stdout contains resume path | `output/resumes/file.pdf` | Parser returns output path. |
| TC-DASH-012 | Output path parsing | Build stdout contains portfolio path | `output/portfolios/file.pptx` | Parser returns output path. |
| TC-DASH-013 | Output path parsing | Build stdout uses Windows separators | `output\\resumes\\file.pdf` | Parser returns output path. |
| TC-DASH-014 | Output path parsing | Dry-run stdout has no output file | `No files written` | Parser returns none. |
| TC-DASH-015 | Output path parsing | Output path contains spaces or label | `Resume written: C:\some dir\...pdf` | Parser extracts path without label. |
| TC-DASH-016 | Output path false positive | Error line mentions output folder and `.pdf` | Error message | Parser returns none. |
| TC-DASH-017 | Get card detail | Client requests existing card | `/api/cards/sample-card` | JSON includes fields and body. |
| TC-DASH-018 | Get missing card detail | Client requests unknown card | Missing ID | HTTP 404. |
| TC-DASH-019 | Get invalid card ID | Client requests invalid ID | `INVALID_ID` | HTTP 400. |
| TC-DASH-020 | Create card | Client posts valid new card | ID, title, type, start date, summary | New MDX file is written. |
| TC-DASH-021 | Create defaults | Client creates card without status/visibility | Minimal valid create payload | Card defaults to `draft` and `public`. |
| TC-DASH-022 | Create duplicate | Client creates existing ID | Duplicate ID same month | HTTP 409 and no overwrite. |
| TC-DASH-023 | Create cross-month duplicate | Client creates existing ID with different month | Duplicate ID different `period_start` | HTTP 409 and no second file. |
| TC-DASH-024 | Create invalid ID | Client creates invalid ID | `INVALID ID!` | HTTP 400. |
| TC-DASH-025 | Create invalid type | Client creates unsupported type | `notavalidtype` | HTTP 422. |
| TC-DASH-026 | Create traversal attempt | Client sends invalid start/path-like data | `period_start=../../../etc/passwd` | HTTP 400 and no file write. |
| TC-DASH-027 | Update card basic fields | Client updates title/summary | Valid fields payload | Target MDX is updated. |
| TC-DASH-028 | Update preserves fields | Client updates one field only | `summary` only | Other metadata remains present. |
| TC-DASH-029 | Update invalid data | Client updates invalid type | `type=notvalid` | HTTP 422 and original file unchanged. |
| TC-DASH-030 | Update missing card | Client updates unknown ID | Missing ID | HTTP 404. |
| TC-DASH-031 | Update invalid URL ID | Client updates invalid ID | `INVALID_ID` | HTTP 400. |
| TC-DASH-032 | ID immutability | Client tries to change `fields.id` | URL ID differs from body ID | HTTP 400 and original file unchanged. |
| TC-DASH-033 | ID immutability no-op | Client sends same `fields.id` | URL ID equals body ID | Update succeeds. |
| TC-DASH-034 | Dashboard UI hooks | Dashboard page renders authoring buttons | `/` | New/edit controls are present. |
| TC-DASH-035 | Update tags | Client updates tag groups | Domain/skill/audience lists | YAML contains list values. |
| TC-DASH-036 | Update metrics | Client updates metrics list | Metric strings | YAML contains metrics. |
| TC-DASH-037 | Update evidence | Client updates evidence list | `type=repo`, URL | YAML contains evidence entry. |
| TC-DASH-038 | Reject invalid evidence | Client sends unsupported evidence type | `type=invalid_type` | HTTP 422 and original file unchanged. |
| TC-DASH-039 | Update visuals | Client updates visual reference | Existing `assets/hero.png` | Update succeeds and YAML contains visual. |
| TC-DASH-040 | Reject invalid visual role | Client sends unsupported visual role | `role=invalid_role` | HTTP 422 and original file unchanged. |
| TC-DASH-041 | Update body | Client updates markdown body | `# Narrative` body | MDX body is updated. |
| TC-DASH-042 | Visual hints | Card detail includes visual references | Visual path missing from filesystem | JSON includes `visual_hints[path]=false`. |
| TC-DASH-043 | Static JS | Client requests dashboard JS | `/static/dashboard.js` | HTTP 200 and JS content is served. |
| TC-DASH-044 | Reject missing visual path on update | Client saves missing relative visual | `assets/missing.png` | HTTP 422 and original file unchanged. |
| TC-DASH-045 | Accept existing visual path on update | Client saves existing repo-local asset | `assets/hero.png` exists | HTTP 200. |
| TC-DASH-046 | New-card detail UX | New card form opens | Dashboard page | Detail hint exists; detail-only sections are not silently saved on create. |
| TC-DASH-047 | Reject absolute visual path | Client saves absolute path | Existing absolute path outside repo | HTTP 422 and original file unchanged. |
| TC-DASH-048 | Reject visual traversal path | Client saves path escaping repo | `../outside.png` | HTTP 422 and original file unchanged. |
| TC-PORT-001 | Portfolio missing visual rendering | Renderer receives card with missing visual | Card with missing visual path | Placeholder renders and deck creation succeeds. |
| TC-PORT-002 | Portfolio narrative toggle | Renderer builds with `--no-narrative` | Card with narrative text | Narrative text is excluded from PPTX. |

## Manual Acceptance Test Cases

| 고유번호 | 테스트 대상 | 테스트 조건 | 테스트 데이터 | 예상 결과 |
|---|---|---|---|---|
| MT-ACC-001 | Real card corpus | User reviews real card repository | Actual `cards/` directory | User can maintain real activity cards; target count and quality are acceptable. |
| MT-ACC-002 | Resume PDF visual output | Typst is installed | `uv run pcli build resume --preset bok-interview` | PDF is generated within target time and visually fits expected resume layout. |
| MT-ACC-003 | Portfolio PPTX visual output | PowerPoint/Keynote is available | `uv run pcli build portfolio --tags web3` | PPTX opens successfully and slides render without major overlap. |
| MT-ACC-004 | LLM-tailored resume | `ANTHROPIC_API_KEY` is configured | `uv run pcli build resume --jd tests/fixtures/fake-jd.txt --tone formal --show-llm-diff` | Diff is visible and generated PDF reflects rewritten summaries. |
| MT-ACC-005 | README quickstart | Fresh or clean local setup | README quickstart steps | First PDF can be produced within the intended onboarding window. |
| MT-DASH-001 | Dashboard startup | Local machine can run Flask app | `uv run pcli dashboard --port <free-port>` | Dashboard starts and loads in browser. |
| MT-DASH-002 | Dashboard browse/filter/select | Dashboard is running with real cards | Search, type/status/tag filters, selected cards | User can find and select intended cards. |
| MT-DASH-003 | Dashboard build action | Dashboard is running | Resume/portfolio dry-run and build buttons | Build result panel shows command, status, raw log, and output path when applicable. |
| MT-DASH-004 | Dashboard card creation | Dashboard is running | New draft card data | Draft card is created and appears in list after refresh. |
| MT-DASH-005 | Dashboard detail editing | Existing draft/test card is open | Tags, metrics, evidence, visuals, body edits | Save succeeds, table refreshes, and `uv run pcli validate <id>` passes. |
| MT-DASH-006 | Dashboard invalid edit safety | Existing draft/test card is open | Invalid type, invalid evidence, missing/absolute/traversal visual path | Save is rejected and original MDX remains unchanged. |

## Maintenance Notes

- Keep this file at the product behavior level. Add rows when new behavior is introduced or when a regression class is discovered.
- Keep pytest function names free to change; this document should track the externally meaningful behavior.
- Use `docs/acceptance-v1.md` and future dashboard acceptance documents for dated execution evidence.
