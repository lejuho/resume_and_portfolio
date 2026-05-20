"""Optional Anthropic LLM tailoring — scoring, rewriting, and card suggestion."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

from .card import Card

MODEL = "claude-sonnet-4-6"
_SCHEMA_VER = 1


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


# ─── client ────────────────────────────────────────────────────────────────


def _build_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("ANTHROPIC_API_KEY is not set")
    try:
        from anthropic import Anthropic  # type: ignore[import]

        return Anthropic(api_key=api_key)
    except ImportError as exc:
        raise LLMError("anthropic package not installed; run: uv sync --extra llm") from exc


def _call(client, prompt: str) -> str:
    response = client.messages.create(
        model=MODEL,
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
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> list[tuple[Card, float, str]]:
    """Score cards 0.0-1.0 for JD relevance. Returns list sorted by score desc.
    Cache key excludes tone so score results are tone-independent.
    """
    if client is None:
        client = _build_client()
    cache_dir = cache_dir or Path(".cache/llm")

    results: list[tuple[Card, float, str]] = []
    for card in cards:
        payload = {
            "schema_ver": _SCHEMA_VER,
            "task": "score",
            "model": MODEL,
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
            raw = _call(client, prompt)
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
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> str:
    """Rewrite card summary for tone/JD alignment. Returns new string; source unchanged."""
    if client is None:
        client = _build_client()
    cache_dir = cache_dir or Path(".cache/llm")

    original = card.summary_ko if lang == "ko" and card.summary_ko else card.summary
    payload = {
        "schema_ver": _SCHEMA_VER,
        "task": "rewrite",
        "model": MODEL,
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
    rewritten = _call(client, prompt).strip()
    _cache_write(key, {"rewritten": rewritten}, cache_dir)
    return rewritten


def suggest_card_from_text(
    text: str,
    client=None,
    cache_dir: Optional[Path] = None,
    no_cache: bool = False,
) -> dict:
    """Suggest card frontmatter fields from raw text. Returns dict with required fields."""
    if client is None:
        client = _build_client()
    cache_dir = cache_dir or Path(".cache/llm")

    payload = {
        "schema_ver": _SCHEMA_VER,
        "task": "suggest",
        "model": MODEL,
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
    raw = _call(client, prompt)
    try:
        data = json.loads(raw.strip())
    except Exception as exc:
        raise LLMError(f"Malformed suggest response: {exc}\nRaw: {raw}") from exc

    _cache_write(key, data, cache_dir)
    return data
