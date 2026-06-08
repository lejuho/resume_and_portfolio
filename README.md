# Card-Based Portfolio/Resume Builder

Career activity를 `cards/*.mdx`로 관리하고 Resume PDF, Portfolio PPTX, 자기소개서/지원서
초안을 생성하는 로컬 도구입니다. CLI와 브라우저 UI를 함께 제공합니다.

## 주요 기능

- **Career cards**: 프로젝트, 해커톤, 역할, 발표, 수상 등 경력을 MDX 카드로 관리
- **Resume builder**: 카드 필터링, preset, JD 기반 tailoring 후 Typst PDF 생성
- **Portfolio builder**: 카드와 visual asset을 이용해 PPTX 생성
- **Dashboard**: 카드 조회, 생성, 상세 편집, 검증, build 실행
- **Career Studio**: 메모를 구조화된 Career Memory 카드 초안으로 변환하고 명시적으로 저장
- **Application Writing**: Live 카드만 근거로 cover letter 또는 지원 문항 답변 preview 생성
- **Workspace**: 카드 선택, target context, fit coverage, preview를 한 화면에서 처리
- **LLM providers**: Anthropic 또는 Google Gemini 선택 지원, 미설정 시 deterministic mock 사용
- **Privacy controls**: Blind Hiring projection, provider/preview identity redaction, 원본 카드 불변

모든 데이터는 로컬 파일에 저장됩니다. AI 결과는 preview 또는 in-memory tailoring에만
사용되며 원본 `cards/*.mdx`를 자동 수정하지 않습니다.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- [Typst >= 0.11](https://github.com/typst/typst/releases): Resume PDF 생성 시 필요
- 선택 사항:
  - `ANTHROPIC_API_KEY`: Anthropic 사용
  - `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY`: Google Gemini 사용

```bash
# 기본 개발/테스트 환경
uv sync

# Anthropic까지 포함한 전체 LLM 환경
uv sync --extra llm
```

## 5-Minute Quickstart

```bash
# 1. 의존성 설치
uv sync

# 2. 프로필 설정
cp profile.example.yaml profile.yaml
# profile.yaml 편집

# 3. 카드 생성
uv run pcli new hackathon my-hackathon \
  --title "ETHGlobal Bangkok" --start 2026-05-01

# 4. 검증
uv run pcli validate

# 5. 빌드
uv run pcli build resume --dry-run
uv run pcli build resume
uv run pcli build portfolio --tags web3

# 6. Web UI 실행
uv run pcli dashboard --port 5000
```

브라우저:

| 화면 | URL | 역할 |
|---|---|---|
| Dashboard | `http://127.0.0.1:5000/dashboard` | 카드 관리, 정밀 편집, build |
| Studio | `http://127.0.0.1:5000/studio` | Career Memory 생성, Application Writing |
| Workspace | `http://127.0.0.1:5000/workspace` | 카드 선택부터 지원 문서 preview까지 통합 작업 |

`/`도 Dashboard를 표시합니다. 서버 기본값은 `127.0.0.1:5000`이며 `--host`, `--port`,
`--debug`로 변경할 수 있습니다.

## Web UI

### Dashboard

- 카드 목록 필터링 및 상세 조회
- Draft 카드 생성과 기존 카드 편집
- tags, metrics, evidence, visuals, narrative 편집
- Resume/Portfolio build 실행과 결과 경로 확인
- Studio와 Workspace 이동

### Career Studio

**Career Memory**

1. 경력 메모를 입력
2. Resume, Portfolio 또는 Both intent 선택
3. mock/LLM preview와 missing information 확인
4. 편집 후 Draft 카드로 명시적 저장

원본 메모는 카드에 저장되지 않으며, 저장 전까지 파일 변경이 없습니다.

**Application Writing**

- Dashboard에서 `Live`로 승인된 카드만 evidence로 선택
- Organization, role, question/prompt, competency, job description 입력
- Cover letter 또는 application answer 생성
- Verified draft, evidence ledger, missing information, warnings, AI guidance 분리 표시
- Verified draft만 clipboard에 복사
- Draft, evidence, provenance, warnings, guidance가 구분된
  `application-handoff.txt` export
- Preview/export는 Career Memory 카드나 별도 backend record를 생성하지 않음

`Blind hiring` 활성화 시 card/provider에서 유래한 identity/background content를
server-owned safe projection에서 제거합니다. Provider와 preview에는 opaque card reference를
사용하며, 안전한 evidence가 하나도 남지 않으면 HTTP `422`로 중단합니다.

### Workspace

Studio를 대체하지 않는 별도 통합 화면입니다.

- Live card 목록과 selected state
- 긴 card summary 2줄 clamp 및 `Show full summary` disclosure
- Organization, role, question, competency, job description 입력
- 선택 evidence와 target text의 theme coverage 및 matched terms 표시
- Cover letter/Application answer preview
- Blind Hiring 지원
- OS dark mode 감지 및 수동 Light/Dark preference 저장
- 키보드 focus와 ARIA 관계 지원

Workspace는 기존 `POST /api/studio/application-preview`를 재사용하며 카드를 수정하거나
새로 저장하지 않습니다.

## 주요 CLI 명령어

```bash
# 카드 관리
uv run pcli new <type> <slug> [--title <title>] [--start YYYY-MM-DD]
uv run pcli ls [--type <type>] [--tag <tag>] [--since YYYY-MM]
uv run pcli show <id>
uv run pcli validate [<id>]
uv run pcli validate --strict

# Resume
uv run pcli build resume [--template default|bok] [--lang en|ko]
uv run pcli build resume --tags web3 --tone formal --dry-run
uv run pcli build resume --cards id1,id2 --out output/custom.pdf

# Portfolio
uv run pcli build portfolio [--layout one-per-card|grouped-by-type|timeline]
uv run pcli build portfolio --tags web3 --max-items 8

# Preset
uv run pcli preset save <name>
uv run pcli preset run <name>
uv run pcli build resume --preset bok-interview

# LLM
uv run pcli build resume --jd ./jd.txt --tone formal --show-llm-diff
uv run pcli llm tailor --cards id1,id2 --jd ./jd.txt --tone technical
uv run pcli llm suggest --from ./notes.txt

# Web server
uv run pcli dashboard [--host 127.0.0.1] [--port 5000] [--debug]
```

## AI Provider 설정

`.env` 또는 shell 환경 변수를 사용할 수 있습니다.

```bash
# Anthropic
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
# 기본 model: claude-sonnet-4-6

# Google Gemini
AI_PROVIDER=google
GOOGLE_API_KEY=...
# 또는 GEMINI_API_KEY
# 기본 model: gemini-2.5-flash

# 선택 model override
AI_MODEL=...
```

- `AI_PROVIDER` 미설정 시 Anthropic이 기본 provider입니다.
- 유효한 key가 없으면 Studio/Application Writing은 deterministic mock으로 동작합니다.
- Studio의 AI status는 설정 여부만 표시합니다.
- 실제 연결 확인은 사용자가 `Check connection`을 실행할 때만 수행합니다.
- API key와 raw provider error는 응답이나 저장 파일에 노출하지 않습니다.
- LLM cache는 `.cache/llm/<sha256>.json`에 저장됩니다.

## Preset 예시

```yaml
# presets/bok-interview.yaml
target: resume
template: bok
lang: ko
include_cards:
  - chainlens-launch
  - solana-colosseum
```

```bash
uv run pcli build resume --preset bok-interview
uv run pcli preset run bok-interview
```

## Card 형식

```yaml
---
id: my-project
title: My Project
type: hackathon          # project|talk|paper|hackathon|role|award|writing|course|community
period:
  start: 2026-05-01
status: live             # live|draft|archived
tags:
  domain: [web3]
  skill: [solidity, python]
  audience: []
summary: "한 줄 resume bullet (200자 이하)"
summary_ko: "한국어 요약 (bok 템플릿 필수)"
metrics:
  - "40% latency reduction"
evidence:
  - type: repo
    url: https://github.com/example/repo
visuals:
  - path: assets/example.png
    role: hero
---

(선택) Markdown narrative. 별도 narrative가 없으면 본문을 fallback으로 사용합니다.
```

## Output 경로

| 아티팩트 | 경로 | Git |
|---|---|---|
| Resume PDF | `output/resumes/resume-YYYYMMDD-HHMM.pdf` | ignored |
| Portfolio PPTX | `output/portfolios/portfolio-YYYYMMDD-HHMM.pptx` | ignored |
| Build context | `.build/resume-data.json` | ignored |
| LLM cache | `.cache/llm/<sha256>.json` | ignored |
| Application handoff | 브라우저 download `application-handoff.txt` | 저장 선택 시만 생성 |
| Cycle review 기록 | `.review/` | tracked |

## Verify

```bash
# 전체 검증
uv sync
uv run pytest -v
uv run ruff check scripts tests
uv run ruff format --check scripts tests
uv run pcli validate

# Workspace 실제 브라우저 통합 테스트
uv run playwright install chromium   # 최초 1회
uv run pytest tests/browser/test_workspace_browser.py -v

# Build smoke checks
uv run pcli build resume --dry-run
uv run pcli build portfolio --dry-run
```

수동 검증과 요구사항 추적:

- [Studio/Workspace acceptance](docs/acceptance-studio.md)
- [전체 test cases](docs/test-cases.md)
- [Dashboard/Studio/Workspace requirements](requirements-dashboard.md)
- [v1 acceptance](docs/acceptance-v1.md)

## 설계 원칙

- `cards/*.mdx`가 career data의 single source of truth
- LLM은 원본 카드를 자동 수정하지 않음
- Preview는 persistence가 아님
- Application Writing은 선택된 Live card evidence에 근거
- Blind Hiring 경계 밖으로 보호 content를 전달하지 않음
- `/studio`와 `/workspace`는 병존하며 `/dashboard`의 관리 기능을 대체하지 않음
