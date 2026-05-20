# v1 Acceptance Evidence

> Record results here after running the smoke commands.
> Automated criteria: run `scripts/smoke.ps1` (or `smoke.sh`).
> Manual criteria: fill in the notes column after visual inspection.

## Acceptance Criteria

| # | Criterion | Verify Method | Command / Path | Manual? | Result |
|---|-----------|---------------|----------------|---------|--------|
| 1 | 실제 활동 card 10개 작성 가능 (스키마 직관적) | `cards/` 목록 확인 + validate pass | `uv run pcli ls` then count | Yes | |
| 2 | `pcli validate` 모두 pass | Exit code 0, no errors | `uv run pcli validate` | No | |
| 3 | `pcli build resume --preset bok-interview` → 5초 이내 PDF 생성 | 생성된 PDF 경로 + 소요 시간 기록 | `uv run pcli build resume --preset bok-interview` | Partial (visual) | |
| 4 | `pcli build portfolio --tags web3` → 10초 이내 PPTX, Keynote/PowerPoint 정상 오픈 | 생성된 PPTX 파일 + 시각적 확인 | `uv run pcli build portfolio --tags web3` | Yes | |
| 5 | `--jd ./fake-jd.txt --tone formal` → LLM rewrite PDF 반영 | PDF 내 요약문이 JD 기반으로 변경됨 확인 | `uv run pcli build resume --jd ./fake-jd.txt --tone formal` (requires `ANTHROPIC_API_KEY`) | Yes | |
| 6 | 모든 command `--help` 사용법 표시 | smoke script가 자동 확인 | `uv run pcli --help` (+ sub-commands) | No | |
| 7 | README quickstart 5분 안에 첫 PDF 생성 가능 | README 검토 + 실제 따라하기 | `README.md` quickstart 섹션 | Yes | |

## Smoke Run Log

> Fill in after running `scripts/smoke.ps1` or `scripts/smoke.sh`.

```
Date: _______________
Runner: _______________
Typst installed: Yes / No   version: _______________
ANTHROPIC_API_KEY set: Yes / No

pytest:               PASS / FAIL   (_____ tests)
ruff check:           PASS / FAIL
ruff format --check:  PASS / FAIL
pcli validate:        PASS / FAIL
build resume --dry-run:     PASS / FAIL
build portfolio --dry-run:  PASS / FAIL
build resume --preset bok-interview:      PASS / FAIL / SKIP (no typst)
build portfolio --tags web3:              PASS / FAIL / SKIP (no typst)
git status --short (no staged artifacts): PASS / FAIL
```

## Manual Verification Notes

### Criterion 1 — Card count
- Cards in `cards/`: ___
- All pass validate: Yes / No

### Criterion 3 — Resume PDF (bok-interview preset)
- PDF path: `output/resumes/_______________`
- Build time: ___ s  (target: ≤ 5 s)
- Visual: 1 page confirmed: Yes / No
- Korean font rendered: Yes / No

### Criterion 4 — Portfolio PPTX (web3 filter)
- PPTX path: `output/portfolios/_______________`
- Build time: ___ s  (target: ≤ 10 s)
- Opened in Keynote / PowerPoint: Yes / No
- Slide count: ___
- Cover slide correct: Yes / No

### Criterion 5 — LLM tailoring
- JD file used: `fake-jd.txt`
- Tone: formal
- PDF generated: Yes / No
- Summary diff visible (`--show-llm-diff`): Yes / No
- Rewritten summaries in PDF: Yes / No

### Criterion 7 — README quickstart
- Followed steps 1-6 in README: Yes / No
- First PDF produced under 5 min: Yes / No
- Notes: _______________

## Overall Result

- [ ] All automated criteria pass
- [ ] All manual criteria verified
- [ ] v1 accepted
