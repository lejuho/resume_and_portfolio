"""Tests for cycle-15: .env loading, ai-status endpoint, Studio UI hooks."""

from __future__ import annotations

import os

import pytest

import scripts.dashboard as dash_mod
from scripts.dashboard import _load_dotenv, app

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─── .env loading ─────────────────────────────────────────────────────────────


def test_load_dotenv_sets_value(tmp_path, monkeypatch):
    monkeypatch.delenv("DOTENV_TEST_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DOTENV_TEST_KEY=hello\n", encoding="utf-8")
    _load_dotenv(env_file)
    assert os.environ.get("DOTENV_TEST_KEY") == "hello"


def test_load_dotenv_does_not_overwrite(tmp_path, monkeypatch):
    monkeypatch.setenv("DOTENV_TEST_KEY", "original")
    env_file = tmp_path / ".env"
    env_file.write_text("DOTENV_TEST_KEY=overwritten\n", encoding="utf-8")
    _load_dotenv(env_file)
    assert os.environ["DOTENV_TEST_KEY"] == "original"


def test_load_dotenv_strips_quotes(tmp_path, monkeypatch):
    monkeypatch.delenv("DOTENV_QUOTED", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text('DOTENV_QUOTED="my value"\n', encoding="utf-8")
    _load_dotenv(env_file)
    assert os.environ.get("DOTENV_QUOTED") == "my value"


def test_load_dotenv_skips_comments_and_blanks(tmp_path, monkeypatch):
    monkeypatch.delenv("DOTENV_REAL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# a comment\n\nDOTENV_REAL=yes  # inline comment\n",
        encoding="utf-8",
    )
    _load_dotenv(env_file)
    assert os.environ.get("DOTENV_REAL") == "yes"


def test_load_dotenv_empty_value_stays_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("DOTENV_EMPTY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DOTENV_EMPTY=\n", encoding="utf-8")
    _load_dotenv(env_file)
    assert os.environ.get("DOTENV_EMPTY") == ""


def test_load_dotenv_missing_file_is_noop(tmp_path):
    _load_dotenv(tmp_path / "nonexistent.env")  # must not raise


def test_gitignore_includes_dotenv():
    import pathlib

    gitignore = pathlib.Path(__file__).parents[1] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert ".env" in text


# ─── /api/studio/ai-status ────────────────────────────────────────────────────


def test_ai_status_unconfigured(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.get("/api/studio/ai-status")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert body["configured"] is False
    assert body["mode"] == "mock"
    assert body["model"] is None


def test_ai_status_configured(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.get("/api/studio/ai-status")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert body["configured"] is True
    assert body["mode"] == "llm"
    assert body["model"] is not None


def test_ai_status_does_not_leak_key(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret-12345")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.get("/api/studio/ai-status")
    text = rv.get_data(as_text=True)
    assert "sk-secret-12345" not in text


def test_ai_status_empty_key_is_unconfigured(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.get("/api/studio/ai-status")
    body = rv.get_json()
    assert body["configured"] is False
    assert body["mode"] == "mock"


def test_ai_status_accepts_generic_ai_api_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_API_KEY", "generic-fake-key")
    rv = client.get("/api/studio/ai-status")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["configured"] is True
    assert body["mode"] == "llm"


def test_ai_status_does_not_leak_generic_ai_api_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_API_KEY", "generic-secret-12345")
    rv = client.get("/api/studio/ai-status")
    text = rv.get_data(as_text=True)
    assert "generic-secret-12345" not in text


# ─── Studio HTML/JS hooks ─────────────────────────────────────────────────────


def test_studio_html_has_ai_status_element(client):
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"st-ai-status" in rv.data


def test_studio_html_has_refine_source_element(client):
    rv = client.get("/studio")
    assert b"st-refine-source" in rv.data


def test_studio_js_fetches_ai_status():
    import pathlib

    js = pathlib.Path(__file__).parents[1] / "scripts" / "static" / "studio.js"
    text = js.read_text(encoding="utf-8")
    assert "/api/studio/ai-status" in text


def test_studio_js_renders_refine_source():
    import pathlib

    js = pathlib.Path(__file__).parents[1] / "scripts" / "static" / "studio.js"
    text = js.read_text(encoding="utf-8")
    assert "refine_source" in text
    assert "Source: LLM" in text
    assert "Source: Mock" in text
