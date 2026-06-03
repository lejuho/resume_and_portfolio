# Advisor Feedback: Cycle 29 Step-004 — Test Design Approach

Type: Approach check
Scope: tests/test_cycle29.py

## Query

`_dark_block()` helper design, test group structure, risk of false-pass in dark token
override assertions.

## Advisor Guidance (retrospective)

1. `_dark_block(src[src.index(marker):])` is sufficient: dark block follows light `:root`
   so slicing from the marker onward covers only the dark content + remainder. No
   bracket-matching required since assertions look for token names, not values.
2. Group test coverage: dark media query (1) + dark token overrides (5) + card states (3)
   + design-system regression (3) + JS contract regression (3) + route regression (2) =
   17 tests. Each dark-override test is specific enough to detect if a token is missing
   from the dark block.
3. No positive-anchor risk for dark override tests: each test asserts a token NAME is
   present in the dark block (substring match). Empty/error response would fail the
   `_dark_block` helper at `src.index(marker)` raising ValueError, not silently pass.

## Decision

Applied all three guidance points in test design.

## Sonnet Response

- 적용: 1, 2, 3 모두 적용.
- 무시: 없음.
- 비고: test helper ValueError-on-missing 동작이 positive anchor 역할을 함.
  이 step은 test_cycle29.py 작성 전에 수행했어야 할 approach check를 사후 기록함.
