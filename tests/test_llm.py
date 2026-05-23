"""Tests for scripts/llm.py — cache, scoring, rewriting, suggest. No network."""

from __future__ import annotations

import json
from datetime import date

import pytest

from scripts.card import Card
from scripts.llm import (
    LLMError,
    _cache_key,
    _cache_read,
    _cache_write,
    rewrite_summary,
    score_cards,
    suggest_card_from_text,
)

# ─── Fake Anthropic client ─────────────────────────────────────────────────


class _FakeContent:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeMessage:
    def __init__(self, text: str) -> None:
        self.content = [_FakeContent(text)]


class _FakeMessages:
    def __init__(self, responses: list[str]) -> None:
        self._iter = iter(responses)

    def create(self, **kwargs) -> _FakeMessage:
        return _FakeMessage(next(self._iter))


class FakeClient:
    def __init__(self, responses: list[str]) -> None:
        self.messages = _FakeMessages(responses)


# ─── Helpers ───────────────────────────────────────────────────────────────


def _card(id_: str, summary: str = "A short summary.") -> Card:
    return Card.model_validate(
        {
            "id": id_,
            "title": id_.replace("-", " ").title(),
            "type": "project",
            "period": {"start": date(2026, 1, 1)},
            "status": "live",
            "summary": summary,
            "evidence": [{"type": "repo", "url": "https://example.com"}],
        }
    )


JD = "Senior Blockchain Engineer needing Solidity and DeFi experience."


# ─── Cache ─────────────────────────────────────────────────────────────────


def test_cache_key_stable():
    k1 = _cache_key({"a": 1, "b": 2})
    k2 = _cache_key({"b": 2, "a": 1})
    assert k1 == k2


def test_cache_key_changes_with_content():
    k1 = _cache_key({"task": "score", "text": "foo"})
    k2 = _cache_key({"task": "score", "text": "bar"})
    assert k1 != k2


def test_cache_read_write_roundtrip(tmp_path):
    key = "abc123"
    data = {"score": 0.9, "reason": "relevant"}
    _cache_write(key, data, tmp_path)
    assert _cache_read(key, tmp_path) == data


def test_cache_read_missing_returns_none(tmp_path):
    assert _cache_read("nonexistent", tmp_path) is None


def test_cache_read_corrupt_returns_none(tmp_path):
    (tmp_path / "bad.json").write_text("{broken", encoding="utf-8")
    assert _cache_read("bad", tmp_path) is None


# ─── score_cards ───────────────────────────────────────────────────────────


def test_score_cards_returns_sorted_desc(tmp_path):
    cards = [_card("low"), _card("high"), _card("mid")]
    responses = [
        '{"score": 0.3, "reason": "low match"}',
        '{"score": 0.9, "reason": "high match"}',
        '{"score": 0.6, "reason": "mid match"}',
    ]
    client = FakeClient(responses)
    results = score_cards(cards, JD, client=client, cache_dir=tmp_path)
    scores = [s for _, s, _ in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0][0].id == "high"


def test_score_cards_uses_cache_on_second_call(tmp_path):
    card = _card("alpha")
    client = FakeClient(['{"score": 0.8, "reason": "cached"}'])
    # First call writes cache
    score_cards([card], JD, client=client, cache_dir=tmp_path)
    # Second call with exhausted client should hit cache (no more responses)
    exhausted_client = FakeClient([])
    results = score_cards([card], JD, client=exhausted_client, cache_dir=tmp_path)
    assert results[0][1] == pytest.approx(0.8)


def test_score_cards_no_cache_bypasses_cache(tmp_path):
    card = _card("beta")
    # Pre-populate cache with 0.5
    from scripts.llm import _cache_key, _cache_write

    payload = {
        "schema_ver": 1,
        "task": "score",
        "model": "claude-sonnet-4-6",
        "lang": "en",
        "card_id": "beta",
        "card_summary": card.summary,
        "jd": JD,
    }
    _cache_write(_cache_key(payload), {"score": 0.5, "reason": "old"}, tmp_path)
    # With no_cache=True should call fake client for 0.9
    client = FakeClient(['{"score": 0.9, "reason": "fresh"}'])
    results = score_cards([card], JD, client=client, cache_dir=tmp_path, no_cache=True)
    assert results[0][1] == pytest.approx(0.9)


def test_score_cards_malformed_response_raises(tmp_path):
    card = _card("gamma")
    client = FakeClient(["not json at all"])
    with pytest.raises(LLMError, match="Malformed score"):
        score_cards([card], JD, client=client, cache_dir=tmp_path)


# ─── rewrite_summary ───────────────────────────────────────────────────────


def test_rewrite_summary_returns_string(tmp_path):
    card = _card("delta")
    client = FakeClient(["Rewritten for formal tone."])
    result = rewrite_summary(card, JD, tone="formal", client=client, cache_dir=tmp_path)
    assert isinstance(result, str)
    assert "Rewritten" in result


def test_rewrite_summary_cached_on_second_call(tmp_path):
    card = _card("epsilon")
    client = FakeClient(["First rewrite."])
    rewrite_summary(card, JD, tone="formal", client=client, cache_dir=tmp_path)
    exhausted = FakeClient([])
    result = rewrite_summary(card, JD, tone="formal", client=exhausted, cache_dir=tmp_path)
    assert result == "First rewrite."


def test_rewrite_summary_different_tone_different_cache(tmp_path):
    card = _card("zeta")
    c1 = FakeClient(["Formal rewrite."])
    c2 = FakeClient(["Technical rewrite."])
    r1 = rewrite_summary(card, JD, tone="formal", client=c1, cache_dir=tmp_path)
    r2 = rewrite_summary(card, JD, tone="technical", client=c2, cache_dir=tmp_path)
    assert r1 != r2


def test_rewrite_does_not_mutate_card(tmp_path):
    card = _card("eta", summary="Original summary.")
    client = FakeClient(["New summary."])
    rewrite_summary(card, JD, tone="founder", client=client, cache_dir=tmp_path)
    assert card.summary == "Original summary."


def test_rewrite_uses_summary_ko_when_lang_ko(tmp_path):
    raw = Card.model_validate(
        {
            "id": "ko-card",
            "title": "Ko Card",
            "type": "project",
            "period": {"start": date(2026, 1, 1)},
            "status": "live",
            "summary": "English summary.",
            "summary_ko": "한국어 요약.",
            "evidence": [{"type": "repo", "url": "https://example.com"}],
        }
    )
    captured: list[str] = []

    class CapturingMessages:
        def create(self, **kwargs):
            captured.append(kwargs["messages"][0]["content"])
            return _FakeMessage("새 요약.")

    class CapturingClient:
        messages = CapturingMessages()

    rewrite_summary(
        raw, None, tone="formal", lang="ko", client=CapturingClient(), cache_dir=tmp_path
    )
    assert "한국어 요약" in captured[0]


# ─── suggest_card_from_text ────────────────────────────────────────────────


def test_suggest_returns_required_fields(tmp_path):
    fake_response = json.dumps(
        {
            "title": "EVM Bridge Contract",
            "type": "project",
            "summary": "Built a cross-chain bridge.",
            "tags_domain": ["web3"],
            "tags_skill": ["solidity"],
        }
    )
    client = FakeClient([fake_response])
    result = suggest_card_from_text("bridge contract notes", client=client, cache_dir=tmp_path)
    for field in ("title", "type", "summary", "tags_domain", "tags_skill"):
        assert field in result


def test_suggest_malformed_response_raises(tmp_path):
    client = FakeClient(["{bad json"])
    with pytest.raises(LLMError, match="Malformed suggest"):
        suggest_card_from_text("some text", client=client, cache_dir=tmp_path)


def test_suggest_cached_on_second_call(tmp_path):
    fake_resp = json.dumps(
        {
            "title": "T",
            "type": "project",
            "summary": "S.",
            "tags_domain": [],
            "tags_skill": [],
        }
    )
    client = FakeClient([fake_resp])
    suggest_card_from_text("text", client=client, cache_dir=tmp_path)
    result = suggest_card_from_text("text", client=FakeClient([]), cache_dir=tmp_path)
    assert result["title"] == "T"


# ─── missing API key ───────────────────────────────────────────────────────


def test_build_client_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from scripts.llm import _build_client

    with pytest.raises(LLMError, match="AI_API_KEY"):
        _build_client()
