# Step 014 — Cycle-4 review-v1 fix Approach check

Cycle: 4
Pass: 2
Files Changed: scripts/render_resume.py, scripts/pcli.py, tests/test_cli.py

## Advisor Verdict
OK

## Advisor Feedback
1. Approach is sound — single source of truth (build_resume) avoids the double-write race.
2. dict.update shallow-merges: meta["llm"] set wholesale to the nested dict. Fine since adding a new top-level "llm" key, not merging into existing nested meta.
3. Risk: extra_meta could silently overwrite generated_at/template/lang. Guard: use {**context["meta"], **extra_meta} to make intent explicit.
4. Test plan is good.

## Sonnet Response
- 적용: render_resume.py에 extra_meta 파라미터 추가, context["meta"] = {**context["meta"], **extra_meta}로 병합.
- 적용: pcli.py에서 pre-write 블록 제거, build_resume에 extra_meta=llm_meta 전달.
- 적용: 테스트 추가 — typst/shutil.which 모킹, 가짜 LLM 빌드 후 resume-data.json에 meta.llm 존재 확인.
