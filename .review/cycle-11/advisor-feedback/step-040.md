# Step 040 — Cycle-11 Studio MVP Approach check

Cycle: 11
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Draft payload coupling: save should accept flat pre-validated fields from draft, not raw draft blob; re-validate at save (trust boundary). resume_bullet/portfolio_body map to summary/narrative; keep flat.
2. Slug generation: validate against _KEBAB_RE after transform; add "draft-" prefix for numeric-only; fallback "studio-draft" for truly unresolvable; also dedup via existing glob check.
3. missing_info structure: return {code, message} objects (MISSING_PERIOD, MISSING_METRICS, MISSING_EVIDENCE, MISSING_VISUAL); structured now avoids future breaking change.

## Sonnet Response
- _mock_refine returns {ok, draft, missing_info}; draft is flat fields dict.
- api_studio_save re-validates all fields independently; only draft accepted (raw_text ignored).
- Structured missing_info with codes.
- 구현 시작.
