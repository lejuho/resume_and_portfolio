# Step 049 — Cycle-15 Approach check

Cycle: 15
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. _load_dotenv() in dashboard.py (not separate module) — ~15 lines, no new import complexity. Parse: strip inline comments, skip blank/comment-only lines, split on first = only, strip quotes from values; empty-string value → unconfigured.
2. ai-status model field: inline `from scripts.llm import MODEL` inside route handler (matches existing pattern at refine endpoint). configured=false when key absent or empty-string; return model: null in that case.
3. Studio status fetch: DOMContentLoaded in studio.js (existing listener at ~line 12). Keeps status live-refreshable; server-rendering would require template context changes.

## Sonnet Response
- _load_dotenv() inline in dashboard.py, called once at module load.
- Handle quoted values, comments, blank lines, empty KEY= in parser.
- GET /api/studio/ai-status with inline MODEL import.
- Studio status + refine_source fetch/render in studio.js DOMContentLoaded.
- 구현 시작.
