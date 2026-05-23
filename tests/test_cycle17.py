"""Tests for cycle-17: AI provider configuration."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

import scripts.dashboard as dash_mod
from scripts.dashboard import app
from scripts.llm import (
    MODEL,
    LLMError,
    _build_client,
    is_api_key_configured,
    resolve_provider_config,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _fake_llm_client(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(payload))]
    c = MagicMock()
    c.messages.create.return_value = msg
    return c


# ─── resolve_provider_config ──────────────────────────────────────────────────


def test_default_provider_is_anthropic(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    cfg = resolve_provider_config()
    assert cfg["provider"] == "anthropic"


def test_default_model_is_constant(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    cfg = resolve_provider_config()
    assert cfg["model"] == MODEL


def test_ai_model_override(monkeypatch):
    monkeypatch.setenv("AI_MODEL", "claude-haiku-4-5-20251001")
    cfg = resolve_provider_config()
    assert cfg["model"] == "claude-haiku-4-5-20251001"


def test_empty_ai_model_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("AI_MODEL", "")
    cfg = resolve_provider_config()
    assert cfg["model"] == MODEL


def test_anthropic_key_resolved(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    cfg = resolve_provider_config()
    assert cfg["api_key"] == "sk-test"


def test_generic_ai_api_key_alias(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("AI_API_KEY", "generic-test")
    cfg = resolve_provider_config()
    assert cfg["api_key"] == "generic-test"


def test_anthropic_key_takes_priority_over_alias(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "specific-key")
    monkeypatch.setenv("AI_API_KEY", "generic-key")
    cfg = resolve_provider_config()
    assert cfg["api_key"] == "specific-key"


def test_placeholder_key_is_not_configured():
    assert is_api_key_configured("your_key_here") is False


def test_realish_key_is_configured():
    assert is_api_key_configured("sk-fake") is True


def test_provider_normalized_to_lowercase(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "  Anthropic  ")
    cfg = resolve_provider_config()
    assert cfg["provider"] == "anthropic"


# ─── _build_client ────────────────────────────────────────────────────────────


def test_build_client_raises_for_unsupported_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "some-key")
    with pytest.raises(LLMError, match="unsupported provider"):
        _build_client()


def test_build_client_raises_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    with pytest.raises(LLMError, match="not set"):
        _build_client()


# ─── /api/studio/ai-status ────────────────────────────────────────────────────


def test_ai_status_reports_resolved_provider(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["provider"] == "anthropic"
    assert body["configured"] is True
    assert body["mode"] == "llm"
    assert body["model"] == MODEL


def test_ai_status_model_override_reflected(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.setenv("AI_MODEL", "claude-haiku-4-5-20251001")
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["model"] == "claude-haiku-4-5-20251001"


def test_ai_status_unsupported_provider_returns_mock(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "some-key")
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["ok"] is True
    assert body["configured"] is False
    assert body["mode"] == "mock"


def test_ai_status_does_not_leak_key(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ultra-secret-99")
    rv = client.get("/api/studio/ai-status")
    assert "sk-ultra-secret-99" not in rv.get_data(as_text=True)


def test_ai_status_placeholder_key_returns_mock(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "your_key_here")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["configured"] is False
    assert body["mode"] == "mock"


# ─── cache key includes provider/model ───────────────────────────────────────


def test_cache_key_changes_with_model_override(monkeypatch):
    from scripts.llm import _cache_key

    payload_default = {
        "schema_ver": 2,
        "task": "studio_refine",
        "provider": "anthropic",
        "model": MODEL,
        "intent": "both",
        "raw_text": "test",
    }
    payload_override = {**payload_default, "model": "claude-haiku-4-5-20251001"}
    assert _cache_key(payload_default) != _cache_key(payload_override)


# ─── /api/studio/refine unsupported provider falls back to mock ───────────────


def test_refine_unsupported_provider_falls_back_to_mock(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "some-key")
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Some project notes", "intent": "both"}
    )
    assert rv.status_code == 200
    assert rv.get_json()["draft"]["refine_source"] == "mock"


def test_refine_placeholder_key_falls_back_to_mock(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "your_key_here")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Some project notes", "intent": "both"}
    )
    assert rv.status_code == 200
    assert rv.get_json()["draft"]["refine_source"] == "mock"
