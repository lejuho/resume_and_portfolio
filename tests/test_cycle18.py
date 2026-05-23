"""Tests for cycle-18: Google Gemini provider adapter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

import scripts.dashboard as dash_mod
import scripts.llm as llm_mod
from scripts.dashboard import app
from scripts.llm import MODEL_GOOGLE, LLMError, _build_client, _call, resolve_provider_config

# ─── Fake Google client ───────────────────────────────────────────────────────


def _make_google_client(text: str):
    """Return a genai.Client subclass instance that passes isinstance and returns text."""
    from google import genai

    class _FakeGoogleClient(genai.Client):
        def __init__(self, response_text: str):
            resp = MagicMock()
            resp.text = response_text
            m = MagicMock()
            m.generate_content.return_value = resp
            self._models = m

        @property
        def models(self):
            return self._models

    return _FakeGoogleClient(text)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _fake_anthropic_client(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(payload))]
    c = MagicMock()
    c.messages.create.return_value = msg
    return c


# ─── resolve_provider_config: Google key chain ───────────────────────────────


def test_google_provider_uses_google_api_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-test")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    cfg = resolve_provider_config()
    assert cfg["provider"] == "google"
    assert cfg["api_key"] == "gkey-test"


def test_google_gemini_api_key_fallback(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    cfg = resolve_provider_config()
    assert cfg["api_key"] == "gemini-test"


def test_google_ai_api_key_alias_fallback(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("AI_API_KEY", "generic-key")
    cfg = resolve_provider_config()
    assert cfg["api_key"] == "generic-key"


def test_google_api_key_takes_priority_over_gemini(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-priority")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-lower")
    cfg = resolve_provider_config()
    assert cfg["api_key"] == "gkey-priority"


def test_google_default_model_is_gemini_flash(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.delenv("AI_MODEL", raising=False)
    cfg = resolve_provider_config()
    assert cfg["model"] == MODEL_GOOGLE
    assert cfg["model"] == "gemini-2.5-flash"


def test_google_ai_model_override(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("AI_MODEL", "gemini-2.0-flash")
    cfg = resolve_provider_config()
    assert cfg["model"] == "gemini-2.0-flash"


def test_anthropic_default_model_unchanged_by_google_constant(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    from scripts.llm import MODEL

    cfg = resolve_provider_config()
    assert cfg["model"] == MODEL


# ─── _build_client: Google ────────────────────────────────────────────────────


def test_build_client_google_returns_genai_client(monkeypatch):
    from google import genai

    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "real-looking-key")
    c = _build_client()
    assert isinstance(c, genai.Client)


def test_build_client_google_raises_when_no_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    with pytest.raises(LLMError, match="not set"):
        _build_client()


def test_build_client_google_rejects_placeholder_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "your_key_here")
    with pytest.raises(LLMError, match="not set"):
        _build_client()


# ─── _call: Google dispatch ───────────────────────────────────────────────────


def test_call_google_returns_text():
    fake = _make_google_client('{"title": "Test"}')
    result = _call(fake, "prompt", "gemini-2.5-flash")
    assert result == '{"title": "Test"}'


def test_call_google_empty_response_raises():
    from google import genai

    class _EmptyClient(genai.Client):
        def __init__(self):
            resp = MagicMock()
            resp.text = ""
            m = MagicMock()
            m.generate_content.return_value = resp
            self._models = m

        @property
        def models(self):
            return self._models

    with pytest.raises(LLMError, match="empty response"):
        _call(_EmptyClient(), "prompt", "gemini-2.5-flash")


def test_call_google_none_text_raises():
    from google import genai

    class _NoneTextClient(genai.Client):
        def __init__(self):
            resp = MagicMock(spec=[])  # no .text attr → AttributeError
            m = MagicMock()
            m.generate_content.return_value = resp
            self._models = m

        @property
        def models(self):
            return self._models

    with pytest.raises(LLMError, match="empty response"):
        _call(_NoneTextClient(), "prompt", "gemini-2.5-flash")


# ─── /api/studio/ai-status: Google ───────────────────────────────────────────


def test_ai_status_google_configured(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-fake")
    monkeypatch.delenv("AI_MODEL", raising=False)
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["provider"] == "google"
    assert body["configured"] is True
    assert body["mode"] == "llm"
    assert body["model"] == MODEL_GOOGLE


def test_ai_status_google_does_not_leak_key(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-ultra-secret-99")
    rv = client.get("/api/studio/ai-status")
    assert "gkey-ultra-secret-99" not in rv.get_data(as_text=True)


def test_ai_status_google_placeholder_key_reports_mock(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "your_key_here")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["configured"] is False
    assert body["mode"] == "mock"


# ─── /api/studio/refine: Google path ─────────────────────────────────────────

_CONSULTANT_BASE = {
    "title": "Auth Service Rebuild",
    "type": "project",
    "summary": "Rebuilt auth service, cutting latency 40%.",
    "problem": "Legacy auth caused P99 spikes.",
    "framing": "Scoped to the auth hot path.",
    "approach": "Replaced blocking calls with async token cache.",
    "outcome": "Latency dropped 40%. Zero incidents in 3 months.",
    "insight": "Bottleneck was connection pool exhaustion.",
    "decisions_tradeoffs": "Chose eventual consistency to avoid distributed locks.",
    "tags": {"domain": ["backend"], "skill": ["python"], "audience": ["engineers"]},
    "metrics": ["40%"],
    "evidence": [{"type": "repo", "url": "https://github.com/example/auth"}],
    "missing_info": [],
    "resume_bullet": "• Rebuilt auth service: 40% latency reduction",
    "portfolio_body": "## Problem\n\nSpikes.\n\n## Approach\n\nAsync cache.",
}


def test_refine_google_path_returns_llm_source(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-fake")
    fake = _make_google_client(json.dumps(_CONSULTANT_BASE))
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild notes", "intent": "both"}
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["draft"]["refine_source"] == "llm"
    assert body["draft"]["title"] == "Auth Service Rebuild"


def test_refine_google_no_key_falls_back_to_mock(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Some project notes", "intent": "both"}
    )
    assert rv.status_code == 200
    assert rv.get_json()["draft"]["refine_source"] == "mock"


# ─── Regression: Anthropic path unchanged ────────────────────────────────────


def test_anthropic_refine_still_works(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    fake = _fake_anthropic_client(_CONSULTANT_BASE)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild notes", "intent": "both"}
    )
    assert rv.status_code == 200
    assert rv.get_json()["draft"]["refine_source"] == "llm"
