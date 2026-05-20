# Card-Based Portfolio/Resume Builder

Career activity를 card 단위 MDX 파일로 관리하고 PDF resume / PPTX portfolio를 CLI로 생성합니다.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- [Typst ≥ 0.11](https://github.com/typst/typst/releases) — PDF 생성 시 필요 (dry-run은 불필요)
- `ANTHROPIC_API_KEY` — optional, LLM tailoring 기능 사용 시만 필요

## 5-Minute Quickstart

```bash
# 1. 의존성 설치
uv sync

# 2. 프로필 설정
cp profile.example.yaml profile.yaml
# profile.yaml 편집 (이름, 연락처, 요약)

# 3. 카드 생성
uv run pcli new hackathon my-hackathon --title "ETHGlobal Bangkok" --start 2026-05-01

# 4. 검증
uv run pcli validate

# 5. Resume dry-run (Typst 없이 카드 선택 확인)
uv run pcli build resume --dry-run

# 6. Resume PDF 생성
uv run pcli build resume

# 7. Portfolio PPTX 생성
uv run pcli build portfolio --tags web3
```

## Output 경로

| 아티팩트 | 경로 |
|---------|------|
| Resume PDF | `output/resumes/resume-YYYYMMDD-HHMM.pdf` |
| Portfolio PPTX | `output/portfolios/portfolio-YYYYMMDD-HHMM.pptx` |
| Build context | `.build/resume-data.json` |
| LLM cache | `.cache/llm/<sha256>.json` |

## 주요 명령어

```bash
# 카드 관리
uv run pcli new <type> <slug> [--title <title>] [--start YYYY-MM-DD]
uv run pcli ls [--type <type>] [--tag <tag>] [--since YYYY-MM]
uv run pcli show <id>
uv run pcli validate [<id>]

# Resume 빌드
uv run pcli build resume [--template default|bok] [--lang en|ko] [--max-items N]
uv run pcli build resume --tags web3 --tone formal --dry-run
uv run pcli build resume --cards id1,id2 --out output/custom.pdf

# Portfolio 빌드
uv run pcli build portfolio [--layout one-per-card|grouped-by-type|timeline]
uv run pcli build portfolio --tags web3 --max-items 8

# Preset 관리
uv run pcli preset save <name>       # 최근 빌드 파라미터를 저장
uv run pcli preset run <name>        # 저장된 preset으로 빌드
uv run pcli build resume --preset bok-interview

# LLM tailoring (ANTHROPIC_API_KEY 필요)
uv run pcli build resume --jd ./jd.txt --tone formal [--show-llm-diff]
uv run pcli llm tailor --cards id1,id2 --jd ./jd.txt --tone technical
uv run pcli llm suggest --from ./notes.txt
```

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

## LLM Tailoring (선택 사항)

```bash
export ANTHROPIC_API_KEY=sk-ant-...

# JD 기반 카드 스코어링 + 요약 재작성 (in-memory, 원본 MDX 불변)
uv run pcli build resume --jd ./jd.txt --tone formal

# 스코어/재작성 diff 출력
uv run pcli build resume --jd ./jd.txt --tone formal --show-llm-diff

# 캐시 우회 (재호출 강제)
uv run pcli build resume --jd ./jd.txt --tone formal --no-cache
```

- LLM 결과는 `.cache/llm/<sha256>.json`에 캐시. 동일 입력 재사용.
- API 키 없거나 캐시 없으면 LLM 명령은 exit 2; 비-LLM 명령은 영향 없음.
- 원본 `cards/*.mdx` 파일은 절대 수정되지 않음.

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
evidence:
  - type: repo
    url: https://github.com/example/repo
---

(선택) 마크다운 본문 — narrative 없으면 여기서 fallback
```

## Verify v1

모든 자동화 체크와 수동 검증 항목은 [docs/acceptance-v1.md](docs/acceptance-v1.md)에 정의되어 있습니다.

```powershell
# PowerShell (Windows)
.\scripts\smoke.ps1

# bash (macOS/Linux)
bash scripts/smoke.sh
```

스크립트가 없거나 직접 확인하려면:

```bash
uv run pytest -v
uv run ruff check scripts tests templates
uv run pcli validate
uv run pcli build resume --dry-run
uv run pcli build portfolio --dry-run
uv run pcli build resume --preset bok-interview   # Typst 필요
uv run pcli build portfolio --tags web3
```

LLM tailoring 검증 (acceptance criterion 5):
- `tests/fixtures/fake-jd.txt`를 사용해 dry-run으로 카드 선별 확인 가능 (`--dry-run` 추가)
- 실제 rewrite + PDF 반영 확인은 `ANTHROPIC_API_KEY` 필요

### 출력 경로 및 Git 추적 정책

| 항목 | 경로 | Git |
|------|------|-----|
| Resume PDF | `output/resumes/resume-YYYYMMDD-HHMM.pdf` | 무시 (`output/` gitignored) |
| Portfolio PPTX | `output/portfolios/portfolio-YYYYMMDD-HHMM.pptx` | 무시 |
| LLM 캐시 | `.cache/llm/<sha256>.json` | 무시 |
| Build 컨텍스트 | `.build/resume-data.json` | 무시 |
| Cycle 리뷰 기록 | `.review/` | **추적됨** (사이클 히스토리 보존) |
