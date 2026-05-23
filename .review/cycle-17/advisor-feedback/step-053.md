# Step 053 — Cycle-17 Approach check

Cycle: 17
Pass: 1
Files Changed: (pre-implementation)

## Advisor Verdict
OK

## Advisor Feedback
1. resolve_provider_config() as standalone dict-returning function in llm.py. Normalize provider with .strip().lower(). Empty AI_MODEL falls back to MODEL constant.
2. _call() stays signature-unchanged; pass model internally. _build_client() accepts resolved config dict. Each public function calls resolve_provider_config() once — no module-level cache so env overrides are always live.
3. Cache key: include resolved provider and model (not constant) in all payload dicts. All five cache sites need updating.
4. CLI helpers (score_cards, rewrite_summary, suggest_card_from_text): add model: str | None = None param defaulting to resolved config model. Keeps them consistent.
5. Unsupported provider: _build_client() raises LLMError("unsupported provider: X"); dashboard catches Exception and falls back to mock.
6. ai-status: reads resolve_provider_config(), returns provider/model/configured/mode — never the key value.

## Sonnet Response
- Add resolve_provider_config() to llm.py.
- Update _build_client(), _call() to use resolved config.
- Update all 5 cache payload sites with provider/model.
- Add model= param to score_cards, rewrite_summary, suggest_card_from_text.
- Update /api/studio/ai-status in dashboard.py.
- 구현 시작.
