# Card-Based Portfolio/Resume Builder — CLI v1 Requirements

> Hand-off document for planner agent. Executor는 이 spec을 기반으로 phase별 구현. Validator는 Acceptance Criteria로 검증.

---

## 1. 목표

Career activity를 **card 단위 mdx 파일**로 single source of truth에 저장하고, on-demand로 tailored **PDF resume** 및 **PPTX portfolio**를 CLI로 생성하는 도구.

### Core principles

- **Cards as files.** `cards/<slug>.mdx`. git이 version control 담당.
- **CLI는 stateless.** Repo가 모든 state. CLI 재실행해도 결과 동일.
- **Templates는 code.** Typst (resume) + python-pptx (portfolio). 디자인 변경 = code 변경.
- **LLM은 optional layer.** API key 없어도 모든 build command 동작해야 함.
- **Solo usage 전제.** Concurrency, auth, multi-tenancy 없음.

### Out of scope (v1)

- GitHub auto-ingestion (PR-merge → card 자동 생성)
- Dashboard / web UI
- Multi-user collaboration
- Asset CDN integration
- ATS optimization 자동화

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | Mac Mini M4 Pro 환경 |
| CLI framework | `typer` | `click` 기반, type hints 활용 |
| Schema | `pydantic` v2 | Card validation |
| MDX parsing | `python-frontmatter` | YAML frontmatter + markdown body |
| Resume render | `typst` (CLI binary) | brew install typst |
| Portfolio render | `python-pptx` | |
| Templating glue | `jinja2` | Typst data 주입 시 사용 (optional) |
| Terminal output | `rich` | Tables, progress, error formatting |
| LLM (optional) | `anthropic` SDK | Claude Sonnet 4.6 권장 |
| Config | YAML | preset, profile |

> LaTeX/pandoc은 사용하지 않음. Typst가 build 속도와 syntax 측면에서 압도적으로 유리.

---

## 3. Repository Structure

```
portfolio-cards/
├── cards/                          # card mdx 파일 (실제 data)
│   ├── 2026-05-pocavault.mdx
│   ├── 2026-05-consensus-miami.mdx
│   ├── 2026-04-chainlens-launch.mdx
│   └── ...
├── assets/                         # card에서 참조하는 이미지
│   └── pocavault/
│       ├── hero.png
│       └── architecture.png
├── templates/
│   ├── resume/
│   │   ├── default.typ
│   │   ├── bok.typ                 # 공공기관/한국 면접용 변형
│   │   ├── web3-en.typ             # 영문 Web3용 변형
│   │   └── _macros.typ
│   └── portfolio/
│       ├── default.py              # python-pptx renderer module
│       └── hackathon.py
├── presets/                        # 자주 쓰는 build config
│   ├── bok-interview.yaml
│   ├── colosseum.yaml
│   └── ethglobal.yaml
├── profile.yaml                    # 본인 basics (이름, contact, summary)
├── output/                         # build artifact (gitignored)
├── .cache/                         # LLM response cache (gitignored)
├── scripts/
│   ├── pcli.py                     # CLI entry (typer app)
│   ├── card.py                     # Card model + IO
│   ├── select.py                   # Filter + sort
│   ├── render_resume.py
│   ├── render_portfolio.py
│   └── llm.py                      # Claude integration (optional)
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 4. Card Schema

### 파일 위치

`cards/<YYYY-MM>-<slug>.mdx` — 파일명에 시작 월 prefix. `id`는 prefix 제외 slug.

### Frontmatter spec

```yaml
---
id: pocavault-seoulana                  # required, kebab-case, repo-unique
title: PocaVault                        # required
type: hackathon                         # required, enum (아래 참조)
period:
  start: 2026-04-15                     # required, ISO date
  end: 2026-04-15                       # optional, null이면 ongoing
status: live                            # draft | live | archived
visibility: public                      # public | private | sensitive
tags:
  domain: [web3, solana, rwa]
  skill: [nextjs, metaplex, tailwindv4, ipfs]
  audience: [web3, korean-market]
metrics:                                # optional, measurable만
  - "5 hours from blank repo to working marketplace"
  - "$0 infra cost (Vercel + Supabase free tier)"
summary: |                              # 1줄 resume bullet, ≤200자
  Built K-pop photocard RWA marketplace on Solana in 5 hours using
  Metaplex Core + Circle USDC; pivoted thesis to "registry IS the product".
summary_ko: |                           # optional, 한국어 변형
  5시간 만에 Solana 기반 K-pop 포토카드 RWA 마켓플레이스를 구축하고
  "레지스트리 자체가 제품"이라는 제품 명제로 피벗.
narrative: |                            # portfolio용 멀티 단락
  ## Context
  Seoulana hackathon, 5-hour solo sprint...
  ## Approach
  ...
  ## Outcome
  ...
visuals:
  - path: assets/pocavault/hero.png
    role: hero
  - path: assets/pocavault/architecture.png
    role: diagram
    caption: "2-step trust settlement model"
evidence:                               # 검증 가능한 pointer
  - type: repo
    url: https://github.com/lejuho/pocavault
  - type: deck
    url: https://...
  - type: writeup
    url: https://...
links:                                  # 외부 mention
  - label: Seoulana hackathon
    url: https://...
related: [chainlens-base-phase]         # 다른 card id
---

(optional markdown body — narrative가 비었으면 body를 narrative로 fallback)
```

### Type enum

`project` | `talk` | `paper` | `hackathon` | `role` | `award` | `writing` | `course` | `community`

### Validation rules (pydantic)

| Rule | Severity |
|---|---|
| `id` unique across repo | error |
| `id` matches kebab-case `^[a-z0-9]+(-[a-z0-9]+)*$` | error |
| `id` ⊂ filename (filename = `<YYYY-MM>-<id>.mdx`) | error |
| `period.start` 존재, ISO date | error |
| `type` ∈ enum | error |
| `summary` ≤ 200자 | error |
| `summary_ko` ≤ 250자 (if present) | error |
| `visuals[].path` 디스크에 존재 | error |
| `evidence` ≥ 1 | warning |
| `metrics` items ≤ 5 | warning |
| `narrative` ≥ 100자 (live status일 때) | warning |

### profile.yaml

```yaml
basics:
  name: 이주호 (Lejuho)
  label: Research Lead @ NinjaLabs · Founder @ ChainLens
  email: ...
  phone: ...
  location: Goyang-si, Korea
  url: https://...
  summary_en: |
    CS student at Hongik (graduating 2027 Feb), research lead at NinjaLabs,
    founder of ChainLens — verified onchain analytics API marketplace.
  summary_ko: |
    홍익대 컴공 (2027년 2월 졸업), NinjaLabs 리서치 리드,
    ChainLens (검증 가능한 온체인 분석 API 마켓플레이스) 창업자.
  profiles:
    - network: GitHub
      username: lejuho
      url: https://github.com/lejuho
    - network: X
      ...
education:
  - institution: Hongik University
    area: Computer Science
    studyType: Bachelor
    startDate: 2021-03
    endDate: 2027-02
```

> profile.yaml은 gitignore 옵션 가능 (sensitive contact 정보 분리).

---

## 5. CLI Commands

CLI 이름: `pcli` (portfolio CLI). entrypoint `scripts/pcli.py`.

### `pcli new <type> <slug> [--title <str>] [--start <date>]`

Stub card 생성. 파일명에 현재 월 자동 prefix.

```bash
pcli new hackathon ethglobal-tokyo --title "EthGlobal Tokyo" --start 2026-09-25
# → cards/2026-09-ethglobal-tokyo.mdx 생성
```

### `pcli validate [<slug>] [--strict]`

모든 card (또는 특정 slug) 검증. `--strict`는 warning도 error 취급. Exit code: 0 (ok) / 1 (error).

### `pcli ls [filters]`

필터링된 card list를 rich table로 출력.

Filters:
- `--type <t1,t2>`
- `--tag <t1,t2>` (domain/skill/audience 무관 OR match)
- `--since <YYYY-MM>` / `--until <YYYY-MM>`
- `--status <s1,s2>` (default: `live`)
- `--sort <date-desc|date-asc|title>` (default: `date-desc`)

### `pcli show <slug>`

Single card 전체 field pretty print.

### `pcli build resume [options]`

PDF resume 생성.

```bash
pcli build resume                       # default 템플릿, live cards 최대 12개
pcli build resume --preset bok-interview
pcli build resume --jd ./jd.txt --tone formal --lang ko
pcli build resume --cards pocavault-seoulana,chainlens-launch
```

Options:

| Flag | Default | Notes |
|---|---|---|
| `--template <name>` | `default` | `templates/resume/<name>.typ` |
| `--cards <ids>` | — | comma-separated, explicit 선택 (filter 무시) |
| `--preset <name>` | — | `presets/<name>.yaml` 로드, 다른 flag로 override 가능 |
| `--tags <t1,t2>` | — | OR match |
| `--types <t1,t2>` | all | enum filter |
| `--since <YYYY-MM>` | — | |
| `--max-items <N>` | 12 | filter 후 cut |
| `--lang <ko\|en>` | `en` | summary vs summary_ko 선택 |
| `--out <path>` | `output/resume-<ts>.pdf` | |
| `--jd <path\|->` | — | LLM tailoring 활성화 (옵셔널 dep) |
| `--tone <formal\|founder\|technical>` | — | LLM rewrite tone hint |
| `--dry-run` | false | 선택된 cards만 출력 |
| `--verbose` | false | LLM call, render step trace |

### `pcli build portfolio [options]`

PPTX portfolio 생성. resume options 대부분 공유 + 추가:

| Flag | Default | Notes |
|---|---|---|
| `--layout <one-per-card\|grouped-by-type\|timeline>` | `one-per-card` | |
| `--include-narrative / --no-narrative` | true | |
| `--cover-title <str>` | profile.basics.label | |
| `--cover-subtitle <str>` | 자동 (date + audience) | |

### `pcli preset save <name>`

직전 build 실행의 args를 `presets/<name>.yaml`로 저장.

### `pcli preset run <name>`

preset 로드 + 실행. preset에 `target: resume|portfolio` 필수.

### `pcli llm tailor --cards <ids> --jd <path>`

LLM rewrite 결과를 stdout으로 출력 (build 없이 diff 검토용).

### `pcli llm suggest --from <file>`

긴 텍스트 파일 (Consensus 발표 후기 메모 등) → frontmatter draft 제안.

---

## 6. Preset format

`presets/bok-interview.yaml`:

```yaml
target: resume                  # required: resume | portfolio
template: bok
lang: ko
tone: formal
filters:
  tags: [korean-market, regulatory, fintech]
  types: [role, project, paper, course]
  since: 2024-01
  max_items: 10
exclude_cards:
  - chainlens-base-phase
include_cards:                  # filter 무관 강제 포함
  - bok-cbdc-study
```

`presets/colosseum.yaml`:

```yaml
target: portfolio
template: default
layout: one-per-card
lang: en
filters:
  tags: [solana, web3]
  status: [live]
  max_items: 8
include_cards:
  - pocavault-seoulana
  - chainlens-solana-pivot
cover_title: "Lejuho — Solana Builder"
```

---

## 7. Resume Template (Typst)

### Approach

CLI가 selected cards를 **JSON** 으로 dump → `typst compile --input data-path=<json> template.typ output.pdf`. Typst의 `json()` reader로 data 로드.

### Default template structure

```
templates/resume/default.typ
  ├─ _macros.typ import
  ├─ Header: basics.name, label, contact row
  ├─ Summary paragraph (basics.summary)
  ├─ Experience section
  │   └─ for card in cards where type ∈ {role, project, hackathon}:
  │       period · title · summary · metrics bullets
  ├─ Talks & Writing section
  │   └─ for card in cards where type ∈ {talk, writing, paper}
  ├─ Education section (from profile.education)
  └─ Footer (generated-at note, optional)
```

### bok.yaml 변형 차이

- 한글 serif 폰트 (Pretendard Serif / Noto Serif KR)
- 학력 섹션 상단 배치
- 자격증·course 강조
- summary_ko 강제 사용 (없으면 build fail)

### Build invocation

```bash
typst compile \
  --input data-path=.build/resume-data.json \
  --input lang=ko \
  templates/resume/default.typ \
  output/resume-20260519-1430.pdf
```

---

## 8. Portfolio Template (python-pptx)

### Module contract

`templates/portfolio/default.py` exposes:

```python
def render(
    cards: list[Card],
    profile: Profile,
    options: PortfolioOptions,
    output_path: Path,
) -> None: ...
```

### Layout: one-per-card (default)

| Slide | Content |
|---|---|
| 1 | Cover (title, subtitle, date, profile name) |
| 2 | TOC (auto from cards list) |
| 3..N | Per-card: hero image (left 50%), title + period (top right), summary + narrative top 3 paragraphs (right), tag chips (bottom right), evidence links (footer) |
| N+1 | Closing (contact info from profile) |

### Layout: grouped-by-type

Type별 section divider slide → 해당 type의 cards → 다음 type.

### Layout: timeline

Cover → 연도별 timeline slide (모든 cards 점으로) → highlight cards (status=live & metrics 존재한 것만) one-per-card.

### Theme

`tags.audience` 첫 값 기반 자동 color scheme:
- `web3` → dark theme, accent #00FFA3 (Solana green) 또는 #6366F1
- `regulatory` / `korean-market` → conservative, navy + ivory
- 기본값 → neutral gray

---

## 9. LLM Layer (Optional)

`scripts/llm.py` 함수:

### `score_cards(cards, jd_text, model="claude-sonnet-4-6") -> list[(card_id, score, reason)]`

각 card를 JD relevance 0–10 점수 + 한 줄 reason. 결과 cache.

### `rewrite_summary(card, jd_text, tone, lang) -> str`

card.summary를 JD + tone에 맞게 rewrite. **원본 mdx는 절대 수정하지 않음**. Rewrite는 build 시 in-memory만 적용.

### `suggest_card_from_text(text) -> dict`

긴 텍스트 → frontmatter draft (YAML dict). `pcli llm suggest` 명령에서 사용.

### 원칙

- 모든 LLM 호출은 `.cache/llm/<sha256(input)>.json`에 캐시
- API key: `ANTHROPIC_API_KEY` env. 없으면 LLM flag 사용 시 명확한 error.
- LLM 결과는 항상 verbose log에 표시 (silent rewrite 금지)
- `--verbose` 또는 `--show-llm-diff`로 변경사항 가시화

---

## 10. Build Pipeline (resume 기준)

```
1. profile.yaml 로드 + validate
2. cards/*.mdx 모두 로드 + validate (fail fast)
3. Apply filters:
   - preset (있으면)
   - CLI flags (preset override)
   - 명시적 --cards가 있으면 filter 무시
4. 정렬: period desc (또는 preset.sort)
5. (if --jd) LLM score → top N
   else: max-items로 cut
6. (if --jd or --tone) LLM rewrite summaries (cached)
7. Build context dict:
   {
     "basics": profile.basics,
     "education": profile.education,
     "cards": [...],
     "meta": {"generated_at": ..., "template": ..., "lang": ..., "tone": ...}
   }
8. .build/resume-data.json 저장
9. typst compile 호출
10. output/resume-<timestamp>.pdf로 이동
11. Print: 파일 경로 + 선택된 cards 요약 + (LLM 사용 시) rewrite diff
```

Portfolio도 동일하되 step 9가 `render(...)` 함수 호출.

---

## 11. Error Handling

- Validation error: stderr에 card 파일명 + line number + 이유 출력 → exit 1
- Typst compile error: stderr에 raw typst error + 원본 mdx에서 추정되는 위치 → exit 2
- Missing asset: warning 출력 후 placeholder image로 대체 → exit 0 (build 성공)
- LLM API error: cache hit 가능하면 cache 사용, 아니면 LLM 없이 fallback → warning 출력
- 모든 error는 rich로 색상 + 컨텍스트와 함께 표시

---

## 12. Acceptance Criteria

v1 완료 기준:

1. 본인 실제 활동 card 10개를 `cards/`에 작성 가능 (스키마 작성이 직관적)
2. `pcli validate` 모두 pass
3. `pcli build resume --preset bok-interview` 실행 → **5초 이내**에 1페이지 PDF 생성
4. `pcli build portfolio --tags web3` 실행 → **10초 이내**에 PPTX 생성, Keynote에서 정상 오픈
5. `pcli build resume --jd ./fake-jd.txt --tone formal` 실행 → LLM이 card 선별 + summary rewrite한 결과가 PDF에 반영
6. 모든 command `--help`로 사용법 표시
7. README.md에 quickstart (5분 안에 첫 PDF 생성 가능)

---

## 13. Phasing for Executor

| Phase | Deliverable | Definition of done |
|---|---|---|
| 1 | Schema + CLI skeleton + `new/validate/ls/show` + Typst default resume + `build resume` (filter only, no LLM) | PDF 1장 생성됨 |
| 2 | python-pptx default portfolio + `build portfolio` | PPTX 1개 생성됨, Keynote 오픈됨 |
| 3 | Preset 시스템 + `bok` resume 변형 + portfolio layout variants | preset 2개 동작 |
| 4 | LLM score + rewrite + JD-driven tailoring + suggest | `--jd` flag end-to-end |
| 5 | Polish: caching, error UX, --dry-run, rich output, README | acceptance 7개 모두 통과 |

---

## 14. Open Questions (Planner가 결정)

1. **Card narrative 위치.** frontmatter `narrative` 필드 vs mdx body. → **권장: frontmatter** (parsing 일관성, 검증 가능). Body는 fallback.
2. **다국어 처리.** dual field (`summary` / `summary_ko`) vs separate cards. → **권장: dual field** + `--lang` flag.
3. **profile.yaml gitignore.** Sensitive contact 분리하면 share 가능. → **권장: 분리, 단 `profile.example.yaml` 제공**.
4. **Typst vs LaTeX.** → **Typst 강력 권장**. Build 속도 + syntax.
5. **Card asset hosting.** repo 직접 저장 vs Cloudinary. → v1은 repo 직접 (단순성). 100MB 넘으면 재고.

---

## 15. Repo bootstrap (executor 첫 작업)

```bash
mkdir portfolio-cards && cd portfolio-cards
git init
mkdir -p cards assets templates/resume templates/portfolio presets scripts output .cache .build
touch profile.example.yaml README.md
cat > .gitignore <<EOF
output/
.cache/
.build/
profile.yaml
.venv/
__pycache__/
*.pyc
EOF
uv init  # 또는 poetry init
uv add typer pydantic python-frontmatter python-pptx jinja2 rich
uv add --optional llm anthropic
brew install typst
```

---

## Notes for planner

- 본인의 multi-agent setup (planner/executor/validator) 활용 가능. 각 phase를 executor에 위임하고 validator가 acceptance criteria 검증.
- Context usage 25% 미만 유지를 위해 validator는 별도 sub-agent로 isolation.
- Phase 1 완료 시점에서 작성된 card 5개 + 생성된 PDF를 실제 검토해 schema 보완 (실제 사용자 = 본인).