# Advisor Feedback: Cycle 21 Step-004 — Amendment v3 Field-Level Screening Fix

Type: Approach check + Completion check
Scope: scripts/dashboard.py, tests/test_cycle21.py
Plan baseline: Escalation Amendment v3 (plan.md) — field-level per-card screening

## Approach Check (before implementation)

Query: safe display label when title is identity, card_has_usable determination, any_redacted flag timing.

Key guidance received:
1. Skip activity entry entirely when title is identity; rely on metric/evidence entries. Opaque "Evidence C1" leaks card existence and pollutes safe_titles without aiding the answer.
2. Correct. Title+summary identity with no metrics/evidence = no usable facts. 422 is the right signal.
3. Safe. 422 returns bare error, never serializes missing_info_additions. Assert 422 short-circuits before redaction-flag serialization.

**Advisor overruled on point 1.** User explicitly instructed: "표시 title이 제거되면 `Evidence C1` 같은 safe display label을 사용하라." User instruction takes priority (see CLAUDE.md hierarchy). Safe label ensures card appears in selected_cards and safe_titles with a policy-compliant placeholder rather than silent absence.

Decision: Applied Advisor guidance on points 2 and 3; overruled on point 1 per user instruction.

## Completion Check (after implementation)

Changes:
- `scripts/dashboard.py` — `_build_safe_projection`: replaced whole-card exclusion check (`_IDENTITY_RE.search(f"{title} {summary}")`) with per-field checks. Title and summary each checked independently; safe_metrics/safe_urls collected separately. `card_has_usable = has_clean_title or has_clean_summary or bool(safe_metrics) or bool(safe_urls)`. Activity entry: uses `c.title` when clean, `f"Evidence {card_ref}"` when title is flagged. Summary entry only when `has_clean_summary`. Metric/evidence entries only from safe lists.
- `tests/test_cycle21.py` — Added `_IDENTITY_TITLE_CLEAN_METRIC_MDX` (identity title + identity summary + clean metric), `_IDENTITY_SUMMARY_CLEAN_TITLE_MDX` (identity summary + clean title), corresponding fixtures and 3 new tests.

Regression risks verified:
1. Non-blind mode: `title_flagged = False` always → `has_clean_title = True` → activity uses `c.title`. Non-blind path unchanged. ✓
2. ISSUE-9 metric/evidence screening preserved: `safe_metrics`/`safe_urls` collection replaces inline loop screens. Same behavior. ✓
3. 422 path (all-excluded): `card_has_usable = False` → skip → `has_usable_facts = False` → 422 before any serialization of `missing_info_additions`. ✓

## Decision

PROCEED. 463 tests pass (460 → +3 field-level screening tests). All checks green.

Auto checks: pytest ✅ 463 passed / ruff check ✅ / ruff format ✅ / pcli validate ✅ / pcli build resume --dry-run ✅ / pcli build portfolio --dry-run ✅ / evaluate_studio_grounding.py --dry-run ✅
