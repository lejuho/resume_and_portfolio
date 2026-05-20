# Step 028 — Cycle-8 Dashboard UX Polish Approach check

Cycle: 8
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Output path parsing: grep regex `r"output[/\\](resumes|portfolios)[/\\]\S+\.(pdf|pptx)"` from stdout. Don't refactor pcli.py output now.
2. Copy-to-clipboard: use `navigator.clipboard.writeText()` with `document.execCommand('copy')` fallback via hidden textarea. localhost satisfies secure context.
3. Selected chips: add `<div id="sel-chips">` row above build buttons inside existing action panel. Preserve single-panel mental model.
4. `/api/build` new fields: `output_path`, `target`, `dry_run`, `selected_ids` — safe to echo. Update test schema assertions.

## Sonnet Response
- 진행: output path regex 파싱 함수 `_parse_output_path()` 추가 예정.
- 진행: /api/build 응답에 `output_path`, `target`, `dry_run`, `selected_ids` 포함.
- 진행: `#sel-ids` → `#sel-chips` (chip + remove button) 교체.
- 진행: copy 버튼, collapsible raw log (`<details>`), layout polish.
- 구현 시작.
