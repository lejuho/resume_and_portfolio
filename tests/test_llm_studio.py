"""Tests for the LLM-backed Studio refine adapter (fake client injection)."""

from __future__ import annotations

import json
import textwrap
from unittest.mock import MagicMock

import pytest

import scripts.dashboard as dash_mod
import scripts.llm as llm_mod
from scripts.dashboard import app

SAMPLE_MDX = textwrap.dedent("""\
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
""")

# ─── Shared fake LLM response builder ─────────────────────────────────────────

_LLM_BASE = {
    "title": "Auth Service Rebuild",
    "type": "project",
    "summary": "Rebuilt the auth service to reduce latency by 40%.",
    "tags": {"domain": ["backend"], "skill": ["python"], "audience": ["engineers"]},
    "metrics": ["40%", "2x"],
    "evidence": [{"type": "repo", "url": "https://github.com/example/auth"}],
    "missing_info": [],
}


def _fake_client(extra: dict | None = None) -> MagicMock:
    payload = {**_LLM_BASE, **(extra or {})}
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps(payload))]
    client = MagicMock()
    client.messages.create.return_value = msg
    return client


# ─── Fixtures ─────────────────────────────────────────────────────────────────


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


# ─── Mock fallback (no API key) ───────────────────────────────────────────────


def test_refine_mock_source_when_no_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post("/api/studio/refine", json={"raw_text": "Some project", "intent": "both"})
    assert rv.status_code == 200
    assert rv.get_json()["draft"]["refine_source"] == "mock"


# ─── LLM path via fake client ─────────────────────────────────────────────────


def test_refine_llm_source(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    fake = _fake_client({"resume_bullet": "• Rebuilt auth: achieved 40% result"})
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post("/api/studio/refine", json={"raw_text": "Some project", "intent": "resume"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["draft"]["refine_source"] == "llm"


def test_refine_llm_source_with_generic_ai_api_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_API_KEY", "generic-fake-key")
    fake = _fake_client({"resume_bullet": "• Rebuilt auth: achieved 40% result"})
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post("/api/studio/refine", json={"raw_text": "Some project", "intent": "resume"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["draft"]["refine_source"] == "llm"


def test_refine_llm_resume_intent(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake = _fake_client({"resume_bullet": "• Rebuilt auth: achieved 40% result"})
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild 2024-03", "intent": "resume"}
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert "resume_bullet" in body["draft"]
    assert "portfolio_body" not in body["draft"]


def test_refine_llm_portfolio_intent(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    body_md = (
        "## Problem\n\nLatency.\n\n## Framing\n\nScope.\n\n"
        "## Approach\n\nRefactor.\n\n## Outcome\n\n40%.\n\n## Insight\n\nLearning."
    )
    fake = _fake_client({"portfolio_body": body_md})
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild 2024-03", "intent": "portfolio"}
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert "portfolio_body" in body["draft"]
    assert "resume_bullet" not in body["draft"]
    assert "## Problem" in body["draft"]["portfolio_body"]


def test_refine_llm_both_intent(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    body_md = (
        "## Problem\n\nLatency.\n\n## Framing\n\nScope.\n\n"
        "## Approach\n\nRefactor.\n\n## Outcome\n\n40%.\n\n## Insight\n\nLearning."
    )
    fake = _fake_client(
        {
            "resume_bullet": "• Rebuilt auth: achieved 40% result",
            "portfolio_body": body_md,
        }
    )
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Auth rebuild 2024-03", "intent": "both"}
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert "resume_bullet" in body["draft"]
    assert "portfolio_body" in body["draft"]


# ─── Malformed LLM response → fallback ────────────────────────────────────────


def test_refine_llm_malformed_falls_back_to_mock(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    msg = MagicMock()
    msg.content = [MagicMock(text="not valid json {{{{")]
    bad_client = MagicMock()
    bad_client.messages.create.return_value = msg
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: bad_client)
    rv = client.post("/api/studio/refine", json={"raw_text": "Some project", "intent": "both"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert body["draft"]["refine_source"] == "mock"


# ─── LLM draft saves as valid card ────────────────────────────────────────────


def test_refine_llm_draft_saves_and_validates(client, repo, monkeypatch):
    from scripts.card import CardRepo

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake = _fake_client(
        {
            "resume_bullet": "• Rebuilt auth: achieved 40% result",
            "portfolio_body": (
                "## Problem\n\nLatency.\n\n## Framing\n\nScope.\n\n"
                "## Approach\n\nRefactor.\n\n## Outcome\n\n40%.\n\n## Insight\n\nLearning."
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
    assert draft["refine_source"] == "llm"

    rv_save = client.post("/api/studio/save", json={"draft": draft})
    assert rv_save.status_code == 201

    repo_obj = CardRepo(repo)
    ids = [c.id for c in repo_obj.cards]
    assert draft["id"] in ids


def test_refine_llm_overlong_summary_is_capped(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    long_summary = "x" * 250
    fake = _fake_client({"summary": long_summary})
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Long summary project", "intent": "both"}
    )
    assert rv.status_code == 200
    draft = rv.get_json()["draft"]
    assert len(draft["summary"]) <= 200


def test_refine_llm_overlong_summary_draft_saves(client, repo, monkeypatch):
    from scripts.card import CardRepo

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    long_summary = "x" * 250
    fake = _fake_client(
        {
            "summary": long_summary,
            "resume_bullet": "• Delivered project",
            "portfolio_body": (
                "## Problem\n\nX.\n\n## Framing\n\nY.\n\n"
                "## Approach\n\nZ.\n\n## Outcome\n\nW.\n\n## Insight\n\nV."
            ),
        }
    )
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv_refine = client.post(
        "/api/studio/refine", json={"raw_text": "Long summary project", "intent": "both"}
    )
    assert rv_refine.status_code == 200
    draft = rv_refine.get_json()["draft"]
    rv_save = client.post("/api/studio/save", json={"draft": draft})
    assert rv_save.status_code == 201
    assert draft["id"] in [c.id for c in CardRepo(repo).cards]


def test_refine_llm_invalid_evidence_type_normalizes_to_other(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake = _fake_client(
        {
            "evidence": [
                {"type": "github", "url": "https://github.com/example/auth"},
                {"type": "repo", "url": "https://github.com/example/valid"},
            ]
        }
    )
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv = client.post("/api/studio/refine", json={"raw_text": "Evidence test", "intent": "both"})
    assert rv.status_code == 200
    evidence = rv.get_json()["draft"]["evidence"]
    types = [e["type"] for e in evidence]
    assert "github" not in types
    assert types[0] == "other"
    assert types[1] == "repo"


def test_refine_llm_invalid_evidence_type_draft_saves(client, repo, monkeypatch):
    from scripts.card import CardRepo

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake = _fake_client(
        {
            "evidence": [{"type": "github", "url": "https://github.com/example/auth"}],
            "resume_bullet": "• Delivered project",
            "portfolio_body": (
                "## Problem\n\nX.\n\n## Framing\n\nY.\n\n"
                "## Approach\n\nZ.\n\n## Outcome\n\nW.\n\n## Insight\n\nV."
            ),
        }
    )
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)
    monkeypatch.setattr(llm_mod, "_cache_read", lambda *a, **k: None)
    monkeypatch.setattr(llm_mod, "_cache_write", lambda *a, **k: None)
    rv_refine = client.post(
        "/api/studio/refine", json={"raw_text": "Evidence test", "intent": "both"}
    )
    assert rv_refine.status_code == 200
    draft = rv_refine.get_json()["draft"]
    rv_save = client.post("/api/studio/save", json={"draft": draft})
    assert rv_save.status_code == 201
    assert draft["id"] in [c.id for c in CardRepo(repo).cards]
