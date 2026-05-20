# Step 032 — Cycle-9 Card Authoring Approach check

Cycle: 9
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. Merge: load existing `post.metadata`, deep-merge incoming JSON, re-validate via `Card.model_validate`. Preserves unknown keys; safer.
2. Use `os.replace(tmp, target)` — atomic on NTFS same-volume. `Path.replace` wraps it but be explicit.
3. `frontmatter.dumps` does NOT preserve comments and may reorder keys (PyYAML default_flow_style). Acceptable for MVP; document in commit.
4. Single inline panel above table, toggled via `hidden` attr. Modal is over-engineering for local-only MVP. Add form reset on close.
5. Validate card_id with `_KEBAB_RE`; resolve path, assert `target.resolve().is_relative_to((REPO_ROOT/"cards").resolve())`.
6. Return 409 on POST if file exists (duplicate ID).

## Sonnet Response
- 진행: GET/POST/PUT /api/cards 라우트 추가.
- 진행: os.replace() 사용, deep-merge 전략.
- 진행: frontmatter.dumps() 사용 (key 순서 미보장 — MVP 허용).
- 진행: inline panel (hidden 토글) in dashboard.html.
- 구현 시작.
