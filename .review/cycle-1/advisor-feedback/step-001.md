# Advisor Feedback — Step 001

**Type:** Approach check
**Module:** phase-1 Card-Based Portfolio CLI
**Date:** 2026-05-19

## Question

Approach check: phase-1 Card-Based Portfolio CLI (Python/Typer/Pydantic v2)
핵심 판단 지점 3개:
1. CardRepo loading strategy
2. Pydantic v2 validator + context injection for cross-file / disk checks
3. Typst subprocess invocation and --dry-run handling

## Advisor Response

1. **Card repo loading — CardRepo 단일 로드 채택**
   - glob 전체 로드 + 단일 CardRepo가 정답 (cross-file 검증, dup id 필요)
   - subset 로드는 cross-file 무결성 보장 불가 → reject
   - lazy property로 검증 1회만 실행

2. **Validator — model_validator + context 주입**
   - filename slug 일치: 모델 외부 검증 (CardRepo가 path 보유, 모델은 path 모름)
   - visuals[].path 디스크 존재: `model_validate(data, context={"repo_root": ...})` + `model_validator(mode='after')`에서 `info.context` 사용
   - field_validator로 cross-field/외부 IO 금지

3. **Typst subprocess — 분리 필요**
   - `shutil.which("typst")`로 존재 선확인
   - dry-run: JSON 생성까지만, compile skip, exit 0
   - 실제: JSON write → subprocess.run(check=True) → CalledProcessError 별도 처리
   - binary 부재 + non-dry-run = 명시적 에러 메시지 + non-zero exit

## Applied

- APPLY: CardRepo single load with lazy property validation
- APPLY: model_validator + context={"repo_root": ...} for disk/cross-file checks
- APPLY: shutil.which("typst") + explicit error path separation
