"""Optional Anthropic LLM tailoring — scoring, rewriting, and card suggestion."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from .card import Card

MODEL = "claude-sonnet-4-6"
_SCHEMA_VER = 2


class LLMError(Exception):
    pass


# ─── cache ─────────────────────────────────────────────────────────────────


def _cache_key(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _cache_read(key: str, cache_dir: Path) -> Optional[dict]:
    path = cache_dir / f"{key}.json"
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _cache_write(key: str, data: dict, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{key}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── provider config ───────────────────────────────────────────────────────

_SUPPORTED_PROVIDERS = frozenset({"anthropic"})
_PLACEHOLDER_API_KEYS = frozenset(
    {
        "your_key_here",
        "your-key-here",
        "paste_key_here",
        "paste-your-key-here",
        "changeme",
        "change_me",
        "replace_me",
        "replace-with-your-key",
    }
)


def is_api_key_configured(api_key: str | None) -> bool:
    """Return True when an API key looks intentionally configured.

    This is not a live credential check. It only prevents obvious placeholders
    from being treated as configured.
    """
    key = (api_key or "").strip()
    return bool(key) and key.lower() not in _PLACEHOLDER_API_KEYS


def resolve_provider_config() -> dict:
    """Resolve provider, model, and API key from environment variables.

    Returns dict with keys: provider (str), model (str), api_key (str).
    Never returns the api_key value in any log or serialized form.
    """
    provider = (os.environ.get("AI_PROVIDER") or "anthropic").strip().lower()
    raw_model = (os.environ.get("AI_MODEL") or "").strip()
    model = raw_model if raw_model else MODEL
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("AI_API_KEY") or ""
    return {"provider": provider, "model": model, "api_key": api_key}


# ─── client ────────────────────────────────────────────────────────────────


def _build_client(config: dict | None = None):
    cfg = config or resolve_provider_config()
    provider = cfg["provider"]
    api_key = cfg["api_key"]
    if provider not in _SUPPORTED_PROVIDERS:
        raise LLMError(f"unsupported provider: {provider!r}")
    if not is_api_key_configured(api_key):
        raise LLMError("ANTHROPIC_API_KEY or AI_API_KEY is not set")
    try:
        from anthropic import Anthropic  # type: ignore[import]

        return Anthropic(api_key=api_key)
    except ImportError as exc:
        raise LLMError("anthropic package not installed; run: uv sync --extra llm") from exc


def _call(client, prompt: str, model: str = MODEL) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ─── public API ────────────────────────────────────────────────────────────


def read_jd(source: str) -> str:
    """Read JD text from a file path or '-' for stdin."""
    if source == "-":
        return sys.stdin.read()
    path = Path(source)
    if not path.exists():
        raise LLMError(f"JD file not found: {source!r}")
    return path.read_text(encoding="utf-8")


def score_cards(
    cards: list[Card],
    jd: str,
    lang: str = "en",
    client=None,
    model: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> list[tuple[Card, float, str]]:
    """Score cards 0.0-1.0 for JD relevance. Returns list sorted by score desc.
    Cache key excludes tone so score results are tone-independent.
    """
    cfg = resolve_provider_config()
    resolved_model = model or cfg["model"]
    if client is None:
        client = _build_client(cfg)
    cache_dir = cache_dir or Path(".cache/llm")

    results: list[tuple[Card, float, str]] = []
    for card in cards:
        payload = {
            "schema_ver": _SCHEMA_VER,
            "task": "score",
            "provider": cfg["provider"],
            "model": resolved_model,
            "lang": lang,
            "card_id": card.id,
            "card_summary": card.summary,
            "jd": jd,
        }
        key = _cache_key(payload)
        cached = None if no_cache else _cache_read(key, cache_dir)
        if cached:
            score = float(cached["score"])
            reason = str(cached["reason"])
        else:
            prompt = (
                f"Score this card's relevance to the job description on a scale 0.0–1.0.\n"
                f"Respond with JSON only: "
                f'{{ "score": <float>, "reason": "<one sentence>" }}\n\n'
                f"Card title: {card.title}\n"
                f"Card summary: {card.summary}\n\n"
                f"Job description:\n{jd}"
            )
            raw = _call(client, prompt, resolved_model)
            try:
                parsed = json.loads(raw.strip())
                score = float(parsed["score"])
                reason = str(parsed["reason"])
            except Exception as exc:
                raise LLMError(
                    f"Malformed score response for {card.id}: {exc}\nRaw: {raw}"
                ) from exc
            _cache_write(key, {"score": score, "reason": reason}, cache_dir)
        results.append((card, score, reason))

    results.sort(key=lambda t: t[1], reverse=True)
    return results


def rewrite_summary(
    card: Card,
    jd: Optional[str],
    tone: str,
    lang: str = "en",
    client=None,
    model: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> str:
    """Rewrite card summary for tone/JD alignment. Returns new string; source unchanged."""
    cfg = resolve_provider_config()
    resolved_model = model or cfg["model"]
    if client is None:
        client = _build_client(cfg)
    cache_dir = cache_dir or Path(".cache/llm")

    original = card.summary_ko if lang == "ko" and card.summary_ko else card.summary
    payload = {
        "schema_ver": _SCHEMA_VER,
        "task": "rewrite",
        "provider": cfg["provider"],
        "model": resolved_model,
        "tone": tone,
        "lang": lang,
        "card_id": card.id,
        "original_summary": original,
        "jd": jd or "",
    }
    key = _cache_key(payload)
    cached = None if no_cache else _cache_read(key, cache_dir)
    if cached:
        return str(cached["rewritten"])

    jd_section = f"\nJob description:\n{jd}" if jd else ""
    prompt = (
        f"Rewrite this professional summary matching tone '{tone}'.\n"
        f"Return ONLY the rewritten summary text, nothing else.\n\n"
        f"Original: {original}{jd_section}"
    )
    rewritten = _call(client, prompt, resolved_model).strip()
    _cache_write(key, {"rewritten": rewritten}, cache_dir)
    return rewritten


_VALID_TYPES = frozenset(
    {"project", "talk", "paper", "hackathon", "role", "award", "writing", "course", "community"}
)
_VALID_EVIDENCE_TYPES = frozenset({"repo", "deck", "writeup", "demo", "article", "other"})

_STUDIO_REFINE_PROMPT = """\
You are a senior career consultant and portfolio narrative designer.
Your job is to turn rough career notes into compelling, specific career artifacts.
Do NOT summarize or restate the raw input — infer career value, sharpen framing,
and produce output that a hiring manager or portfolio reader would find credible.
Return ONLY a JSON object — no markdown fences, no explanation.

Always-present fields:
  title: string — concise project/role name (≤80 chars)
  type: one of project/talk/paper/hackathon/role/award/writing/course/community
  summary: string — 1-2 sharp sentences for a portfolio card (≤200 chars)
  problem: string — what situation or gap prompted this work (1-2 sentences)
  framing: string — how you scoped or reframed the problem (1-2 sentences)
  approach: string — key technical or strategic decisions made (2-3 sentences)
  outcome: string — measurable or observable results (1-2 sentences)
  insight: string — what you learned or would do differently (1 sentence)
  decisions_tradeoffs: string — a notable tradeoff or constraint navigated (1-2 sentences)
  tags: object with domain (list[str]), skill (list[str]), audience (list[str])
  metrics: list of short strings — concrete numbers/percentages (e.g. "40%", "2x")
  evidence: list of objects with type ("repo"|"deck"|"writeup"|"demo"|"article"|"other")
    and url (string)
  missing_info: list of objects with code (string) and message (string) for gaps

Intent-conditional fields:
  resume_bullet: string starting with "•" and an action verb — one line,
    quantified result if possible (if intent includes resume)
  portfolio_body: markdown string — narrative prose using ## Problem, ## Framing,
    ## Approach, ## Outcome, ## Insight, ## Decisions & Tradeoffs sections.
    Write in first person. Do not copy the raw notes verbatim. (if intent includes portfolio)

Intent: {intent}
Raw notes:
{raw_text}
"""


def studio_refine_llm(
    raw_text: str,
    intent: str,
    client=None,
    model: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> dict:
    """Refine raw career notes into a structured Studio draft via LLM.

    Returns a dict compatible with _mock_refine: {ok, draft, missing_info}.
    draft includes refine_source="llm".
    Raises LLMError on malformed response.
    """
    cfg = resolve_provider_config()
    resolved_model = model or cfg["model"]
    if client is None:
        client = _build_client(cfg)
    cache_dir = cache_dir or Path(".cache/llm")

    payload = {
        "schema_ver": _SCHEMA_VER,
        "task": "studio_refine",
        "provider": cfg["provider"],
        "model": resolved_model,
        "intent": intent,
        "raw_text": raw_text,
    }
    key = _cache_key(payload)
    cached = None if no_cache else _cache_read(key, cache_dir)

    if cached:
        raw_parsed = cached
    else:
        prompt = _STUDIO_REFINE_PROMPT.format(intent=intent, raw_text=raw_text)
        raw = _call(client, prompt, resolved_model)
        try:
            raw_parsed = json.loads(raw.strip())
        except Exception as exc:
            raise LLMError(f"Malformed studio_refine response: {exc}\nRaw: {raw}") from exc
        _cache_write(key, raw_parsed, cache_dir)

    # Validate and normalize
    title = str(raw_parsed.get("title") or "Untitled")[:80]
    card_type = raw_parsed.get("type", "project")
    if card_type not in _VALID_TYPES:
        card_type = "project"
    summary = str(raw_parsed.get("summary") or title)[:200]
    tags_raw = raw_parsed.get("tags")
    tags_raw = tags_raw if isinstance(tags_raw, dict) else {}
    tags = {
        "domain": [str(t) for t in (tags_raw.get("domain") or [])],
        "skill": [str(t) for t in (tags_raw.get("skill") or [])],
        "audience": [str(t) for t in (tags_raw.get("audience") or [])],
    }
    metrics = [str(m) for m in (raw_parsed.get("metrics") or [])][:5]
    evidence_raw = raw_parsed.get("evidence") or []
    evidence = [
        {
            "type": str(e.get("type", "other"))
            if str(e.get("type", "other")) in _VALID_EVIDENCE_TYPES
            else "other",
            "url": str(e.get("url", "")),
        }
        for e in evidence_raw
        if isinstance(e, dict) and e.get("url")
    ]
    missing_info = [
        {"code": str(m.get("code", "")), "message": str(m.get("message", ""))}
        for m in (raw_parsed.get("missing_info") or [])
        if isinstance(m, dict)
    ]

    def _narrative(key: str, fallback: str = "") -> str:
        val = raw_parsed.get(key)
        return str(val).strip() if val and isinstance(val, str) else fallback

    problem = _narrative("problem")
    framing = _narrative("framing")
    approach = _narrative("approach")
    outcome = _narrative("outcome")
    insight = _narrative("insight")
    decisions_tradeoffs = _narrative("decisions_tradeoffs")

    from datetime import date as _date

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "studio-draft"
    if not slug[0].isalpha() and not slug[0].isdigit():
        slug = "studio-draft"
    elif slug[0].isdigit():
        slug = f"draft-{slug}"

    draft: dict = {
        "id": slug,
        "title": title,
        "type": card_type,
        "period_start": str(_date.today()),
        "status": "draft",
        "visibility": "public",
        "summary": summary,
        "problem": problem,
        "framing": framing,
        "approach": approach,
        "outcome": outcome,
        "insight": insight,
        "decisions_tradeoffs": decisions_tradeoffs,
        "tags": tags,
        "metrics": metrics,
        "evidence": evidence,
        "visuals": [],
        "links": [],
        "related": [],
        "refine_source": "llm",
    }

    if intent in ("resume", "both"):
        bullet = str(raw_parsed.get("resume_bullet") or f"• Delivered {title}")
        draft["resume_bullet"] = bullet[:200]

    if intent in ("portfolio", "both"):
        body = str(raw_parsed.get("portfolio_body") or f"## Problem\n\n{title}.\n")
        draft["portfolio_body"] = body

    return {"ok": True, "draft": draft, "missing_info": missing_info}


def suggest_card_from_text(
    text: str,
    client=None,
    model: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> dict:
    """Suggest card frontmatter fields from raw text. Returns dict with required fields."""
    cfg = resolve_provider_config()
    resolved_model = model or cfg["model"]
    if client is None:
        client = _build_client(cfg)
    cache_dir = cache_dir or Path(".cache/llm")

    payload = {
        "schema_ver": _SCHEMA_VER,
        "task": "suggest",
        "provider": cfg["provider"],
        "model": resolved_model,
        "text": text,
    }
    key = _cache_key(payload)
    cached = None if no_cache else _cache_read(key, cache_dir)
    if cached:
        return cached

    prompt = (
        "Extract a card frontmatter from the following text. "
        "Return ONLY a JSON object with these fields: "
        "title (string), "
        "type (one of: project/talk/paper/hackathon/role/award/writing/course/community), "
        "summary (1-2 sentence string), "
        "tags_domain (list of strings), "
        "tags_skill (list of strings). "
        "No markdown fences, no explanation.\n\n"
        f"Text:\n{text}"
    )
    raw = _call(client, prompt, resolved_model)
    try:
        data = json.loads(raw.strip())
    except Exception as exc:
        raise LLMError(f"Malformed suggest response: {exc}\nRaw: {raw}") from exc

    _cache_write(key, data, cache_dir)
    return data
