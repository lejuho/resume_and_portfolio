"""Tests for cycle-19: Studio AI connection check."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import scripts.dashboard as dash_mod
import scripts.llm as llm_mod
from scripts.dashboard import app
from scripts.llm import LLMConnectionError, check_provider_connection

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─── Fake clients ─────────────────────────────────────────────────────────────


def _fake_anthropic_client(text: str = "ok") -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    c = MagicMock()
    c.messages.create.return_value = msg
    return c


def _make_google_client(text: str = "ok"):
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


# ─── check_provider_connection: success paths ────────────────────────────────


def test_check_connection_anthropic_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    fake = _fake_anthropic_client()
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    result = check_provider_connection()
    assert result["ok"] is True
    assert result["connected"] is True
    assert result["provider"] == "anthropic"


def test_check_connection_google_success(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-fake")
    fake = _make_google_client("ok")
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    result = check_provider_connection()
    assert result["ok"] is True
    assert result["connected"] is True
    assert result["provider"] == "google"


def test_check_connection_returns_provider_and_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    from scripts.llm import MODEL

    fake = _fake_anthropic_client()
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    result = check_provider_connection()
    assert result["provider"] == "anthropic"
    assert result["model"] == MODEL


# ─── check_provider_connection: failure paths ────────────────────────────────


def test_check_connection_missing_key_raises_not_configured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "not_configured"


def test_check_connection_placeholder_key_raises_not_configured(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "your_key_here")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "not_configured"


def test_check_connection_unsupported_provider_raises(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_API_KEY", "some-key")
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "unsupported_provider"


def test_check_connection_auth_error_maps_to_auth_failed(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("401 authentication error: invalid api key")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "auth_failed"


def test_check_connection_quota_error_maps_to_quota(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("429 rate limit exceeded")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "quota_or_rate_limit"


def test_check_connection_network_error_maps_to_network(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("network connection timeout")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "network_error"


def test_check_connection_generic_error_maps_to_provider_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("unexpected server error 500")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert exc_info.value.error_code == "provider_error"


def test_check_connection_error_message_is_safe(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ultra-secret-99")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("401 invalid api key: sk-ultra-secret-99")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    with pytest.raises(LLMConnectionError) as exc_info:
        check_provider_connection()
    assert "sk-ultra-secret-99" not in str(exc_info.value)


# ─── /api/studio/ai-check endpoint ───────────────────────────────────────────


def test_ai_check_success_response_shape(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    fake = _fake_anthropic_client()
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post("/api/studio/ai-check")
    body = rv.get_json()
    assert body["ok"] is True
    assert body["connected"] is True
    assert body["provider"] == "anthropic"
    assert "model" in body
    assert body["message"] == "Connection check passed"


def test_ai_check_not_configured_response(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    rv = client.post("/api/studio/ai-check")
    body = rv.get_json()
    assert body["ok"] is False
    assert body["connected"] is False
    assert body["error_code"] == "not_configured"


def test_ai_check_auth_failed_response(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("401 authentication failed")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    rv = client.post("/api/studio/ai-check")
    body = rv.get_json()
    assert body["ok"] is False
    assert body["error_code"] == "auth_failed"


def test_ai_check_does_not_leak_key(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ultra-secret-77")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    def _build_fake(*a, **k):
        fake = MagicMock()
        fake.messages.create.side_effect = Exception("401 invalid api key: sk-ultra-secret-77")
        return fake

    monkeypatch.setattr(llm_mod, "_build_client", _build_fake)
    rv = client.post("/api/studio/ai-check")
    assert "sk-ultra-secret-77" not in rv.get_data(as_text=True)


def test_ai_check_google_success(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-fake")
    fake = _make_google_client("ok")
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post("/api/studio/ai-check")
    body = rv.get_json()
    assert body["ok"] is True
    assert body["connected"] is True
    assert body["provider"] == "google"


# ─── UI: button and JS hooks ─────────────────────────────────────────────────


def test_studio_html_has_check_button():
    path = __import__("pathlib").Path("scripts/templates/studio.html")
    content = path.read_text(encoding="utf-8")
    assert "Check AI connection" in content
    assert "st-ai-check-btn" in content


def test_studio_js_check_calls_ai_check_endpoint():
    path = __import__("pathlib").Path("scripts/static/studio.js")
    content = path.read_text(encoding="utf-8")
    assert "/api/studio/ai-check" in content


def test_studio_js_check_not_called_on_domcontentloaded():
    path = __import__("pathlib").Path("scripts/static/studio.js")
    content = path.read_text(encoding="utf-8")
    # checkAiConnection must not appear inside the DOMContentLoaded block
    dom_block_start = content.find("DOMContentLoaded")
    dom_block_end = content.find("});", dom_block_start)
    dom_block = content[dom_block_start:dom_block_end]
    assert "checkAiConnection" not in dom_block


def test_studio_js_check_triggered_by_button_click():
    path = __import__("pathlib").Path("scripts/static/studio.js")
    content = path.read_text(encoding="utf-8")
    assert "async function checkAiConnection" in content
