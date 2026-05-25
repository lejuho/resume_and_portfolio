"""Tests for cycle-16: consultant prompt harness."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

import scripts.dashboard as dash_mod
import scripts.llm as llm_mod
from scripts.dashboard import app
from scripts.llm import _STUDIO_REFINE_PROMPT, studio_refine_llm

# ─── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_MDX = """\
---
id: sample-card
title: Sample Card
type: hackathon
period:
  start: 2026-05-01
status: live
summary: "A valid summary for testing."
narrative: "Long enough narrative to pass live status check. Over 100 chars needed here yes."
evidence:
  - type: repo
    url: https://github.com/example/repo
---
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    (tmp_path / "cards" / "2026-05-sample-card.mdx").write_text(SAMPLE_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def client(repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─── Shared fake LLM builder ──────────────────────────────────────────────────

_CONSULTANT_BASE = {
    "title": "Auth Service Rebuild",
    "type": "project",
    "summary": "Rebuilt auth service, cutting latency 40% and eliminating a security gap.",
    "problem": "Legacy auth used synchronous DB lookups on every request, causing P99 spikes.",
    "framing": "Scoped to the auth hot path only; left session store unchanged.",
    "approach": "Replaced blocking calls with async token cache. Added circuit breaker.",
    "outcome": "Latency dropped 40%. Zero auth-related incidents in 3 months post-deploy.",
    "insight": "The bottleneck was in connection pool exhaustion, not query time.",
    "decisions_tradeoffs": "Chose eventual consistency in the cache to avoid distributed locks.",
    "tags": {"domain": ["backend"], "skill": ["python"], "audience": ["engineers"]},
    "metrics": ["40%", "2x"],
    "evidence": [{"type": "repo", "url": "https://github.com/example/auth"}],
    "missing_info": [],
}


def _fake_client(extra: dict | None = None) -> MagicMock:
    payload = {**_CONSULTANT_BASE, **(extra or {})}
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(payload))]
    client = MagicMock()
    client.messages.create.return_value = msg
    return client


# ─── Prompt content checks ────────────────────────────────────────────────────


def test_prompt_contains_consultant_persona():
    assert "consultant" in _STUDIO_REFINE_PROMPT.lower()


def test_prompt_contains_portfolio_designer_role():
    assert "portfolio" in _STUDIO_REFINE_PROMPT.lower()


def test_prompt_requires_narrative_fields():
    for field in ("problem", "framing", "approach", "outcome", "insight", "decisions_tradeoffs"):
        assert field in _STUDIO_REFINE_PROMPT


def test_prompt_instructs_not_to_copy_raw_notes():
    lower = _STUDIO_REFINE_PROMPT.lower()
    assert "verbatim" in lower or "not copy" in lower or "do not copy" in lower


def test_prompt_includes_intent_and_raw_text_placeholders():
    assert "{intent}" in _STUDIO_REFINE_PROMPT
    assert "{raw_text}" in _STUDIO_REFINE_PROMPT


# ─── Field mapping ────────────────────────────────────────────────────────────


def test_consultant_fields_appear_in_draft(monkeypatch):
    fake = _fake_client()
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    result = studio_refine_llm("Auth rebuild 2024-03", "both", client=fake)
    draft = result["draft"]
    assert draft["problem"] == _CONSULTANT_BASE["problem"]
    assert draft["framing"] == _CONSULTANT_BASE["framing"]
    assert draft["approach"] == _CONSULTANT_BASE["approach"]
    assert draft["outcome"] == _CONSULTANT_BASE["outcome"]
    assert draft["insight"] == _CONSULTANT_BASE["insight"]
    assert draft["decisions_tradeoffs"] == _CONSULTANT_BASE["decisions_tradeoffs"]


def test_refine_source_is_llm(monkeypatch):
    fake = _fake_client()
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    result = studio_refine_llm("Auth rebuild 2024-03", "both", client=fake)
    assert result["draft"]["refine_source"] == "llm"


# ─── Normalization: malformed optional fields ─────────────────────────────────


def test_missing_narrative_fields_default_to_empty_string(monkeypatch):
    fake = _fake_client({"problem": None, "framing": 42, "insight": []})
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    result = studio_refine_llm("Auth rebuild", "both", client=fake)
    draft = result["draft"]
    assert draft["problem"] == ""
    assert draft["framing"] == ""
    assert draft["insight"] == ""


def test_narrative_field_non_string_coerced(monkeypatch):
    fake = _fake_client({"approach": {"text": "used async"}})
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    result = studio_refine_llm("Auth rebuild", "both", client=fake)
    assert result["draft"]["approach"] == ""


def test_malformed_tags_list_coerces_to_empty_buckets(monkeypatch):
    fake = _fake_client({"tags": ["backend"]})
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    result = studio_refine_llm("Auth rebuild", "both", client=fake)
    assert result["draft"]["tags"] == {"domain": [], "skill": [], "audience": []}


def test_malformed_tags_string_coerces_to_empty_buckets(monkeypatch):
    fake = _fake_client({"tags": "backend"})
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    result = studio_refine_llm("Auth rebuild", "both", client=fake)
    assert result["draft"]["tags"] == {"domain": [], "skill": [], "audience": []}


# ─── Integration: API endpoint ────────────────────────────────────────────────


def test_api_refine_returns_consultant_fields(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake = _fake_client(
        {
            "resume_bullet": "• Rebuilt auth service: 40% latency reduction",
            "portfolio_body": (
                "## Problem\n\nSpikes.\n\n## Framing\n\nHot path only.\n\n"
                "## Approach\n\nAsync cache.\n\n## Outcome\n\n40% faster.\n\n"
                "## Insight\n\nPool exhaustion.\n\n"
                "## Decisions & Tradeoffs\n\nEventual consistency."
            ),
        }
    )
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild 2024-03", "intent": "both"}
    )
    assert rv.status_code == 200
    draft = rv.get_json()["draft"]
    assert draft["refine_source"] == "llm"
    assert "problem" in draft
    assert "framing" in draft
    assert "approach" in draft
    assert "outcome" in draft
    assert "insight" in draft
    assert "decisions_tradeoffs" in draft


def test_mock_fallback_unaffected(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post("/api/studio/refine", json={"raw_text": "Some project work", "intent": "both"})
    assert rv.status_code == 200
    assert rv.get_json()["draft"]["refine_source"] == "mock"


def test_consultant_draft_saves_and_validates(client, repo, monkeypatch):
    from scripts.card import CardRepo

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake = _fake_client(
        {
            "resume_bullet": "• Rebuilt auth service: 40% latency reduction",
            "portfolio_body": (
                "## Problem\n\nSpikes.\n\n## Framing\n\nHot path.\n\n"
                "## Approach\n\nAsync cache.\n\n## Outcome\n\n40%.\n\n"
                "## Insight\n\nPool.\n\n## Decisions & Tradeoffs\n\nConsistency."
            ),
        }
    )
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv_refine = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild 2024-03", "intent": "both"}
    )
    assert rv_refine.status_code == 200
    draft = rv_refine.get_json()["draft"]
    rv_save = client.post("/api/studio/save", json={"draft": draft})
    assert rv_save.status_code == 201
    assert draft["id"] in [c.id for c in CardRepo(repo).cards]
