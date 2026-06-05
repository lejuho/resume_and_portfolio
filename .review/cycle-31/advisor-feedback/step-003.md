# Advisor Feedback: Cycle 31 Step-003 — Review Fix Approach

Type: Approach check
Scope: ISSUE-1/2/3/4 fixes from review-v1.md

## Approach Check (before implementation)

Key judgment points:

1. **ISSUE-1 (counts vs total)**: Fix the 10 exact counts AND add a one-line note that
   236 = sum of C21-C30 suites only; 612 = full repo baseline including other files.
   Silent fix would invite the same finding in the next review.

2. **ISSUE-2 (generate button focus + color: #fff)**: Three-part fix:
   (a) Correct `design-system-workspace.md` interaction-table row to "browser default"
   (b) Add explicit `color: #fff` exception/debt note in the design doc
   (c) Update `report-v1.md` conformance row to record the Generate-button focus exception.
   Leaving report-v1.md as-is creates doc-vs-doc inconsistency Codex would re-flag.

3. **ISSUE-3 (theme-coverage plan)**: Rewrite §9 to the deterministic client-side description
   (manual required-themes, covered/required*100, no AI/S1, no backend mutation).
   Do NOT invent browser-first sequencing — the plan has no browser dependency;
   assert independence rather than fabricate a rationale.

4. **ISSUE-4 (acceptance-studio.md metadata)**: Simple wording update.

## Advisor Verdict

PROCEED — all 4 issues are APPLY. No CSS changes; documentation-only.

## Sonnet Response

- 적용: 모든 판단 기준 수용. color:#fff는 별도 exception note로 문서화. browser-first ordering 근거 없으면 claim하지 않음.
- 무시: 없음.
