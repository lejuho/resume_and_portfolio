# Card-Based Portfolio/Resume Builder

Career activity를 card 단위 MDX 파일로 관리하고 PDF resume / PPTX portfolio를 CLI로 생성합니다.

## Phase 1 Quickstart

### 1. 환경 설정

```bash
# Python 3.11+, uv 필요
uv sync
```

### 2. Profile 설정

```bash
cp profile.example.yaml profile.yaml
# profile.yaml 편집 (이름, 연락처, 요약)
```

### 3. 기본 명령어

```bash
# 새 카드 생성
uv run pcli new hackathon my-project --title "My Project" --start 2026-05-01

# 카드 목록 보기
uv run pcli ls

# 카드 유효성 검사
uv run pcli validate

# 특정 카드 상세 보기
uv run pcli show my-project

# resume 빌드 (dry-run)
uv run pcli build resume --dry-run

# resume PDF 생성 (Typst 필요: https://typst.app)
uv run pcli build resume
```

### 4. Typst 설치 (PDF 생성 시 필요)

- Windows: [typst releases](https://github.com/typst/typst/releases)에서 다운로드 후 PATH 추가
- macOS: `brew install typst`

## Card 형식

`cards/<YYYY-MM>-<slug>.mdx` 파일 생성:

```yaml
---
id: my-project
title: My Project
type: hackathon
period:
  start: 2026-05-01
status: live
tags:
  domain: [web3]
  skill: [python]
summary: "한 줄 resume bullet (200자 이하)"
---

(선택) 마크다운 본문 — narrative가 없으면 여기서 fallback
```

## Card Type 목록

`project` | `talk` | `paper` | `hackathon` | `role` | `award` | `writing` | `course` | `community`
