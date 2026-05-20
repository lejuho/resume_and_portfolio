# Step 011 — Cycle-3 review-v1.md BLOCKED fix Approach check

Cycle: 3
Pass: 2
Files Changed: presets/bok-interview.yaml, scripts/preset.py, tests/test_preset.py, presets/smoke-test.yaml

## Advisor Verdict
OK

## Advisor Feedback
1. ISSUE-1: Option A (include_cards). Sample preset must "just work" without mutating content. include_cards keeps the demo deterministic and avoids drive-by edits to .mdx files outside cycle scope.
2. ISSUE-2: Plan is sound. Normalize in load_preset only (list→comma-join, str→passthrough, None→None). Add a unit test for both shapes so regression sticks. Do not touch select.py signature.
3. ISSUE-3: Safe to remove. First confirm no preset/test/docs references it (grep "smoke-test"), then git rm and commit.

## Sonnet Response
- 적용 (1): Add include_cards to bok-interview.yaml listing only cards with summary_ko.
- 적용 (2): Normalize PresetFilters tags/types in load_preset() — list→comma-join, str→passthrough, None→None. Add test.
- 적용 (3): git rm presets/smoke-test.yaml after grep confirms no references.
