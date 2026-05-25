"""Tests for Cycle 21: Application Writing Harness Preview."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import scripts.dashboard as dash_mod
import scripts.llm as llm_mod
from scripts.dashboard import app

# ── Fixtures ──────────────────────────────────────────────────────────────────

LIVE_MDX = """\
---
id: auth-service
title: Auth Service
type: project
period:
  start: 2024-03-01
status: live
summary: "Rebuilt the auth service reducing latency by 40%."
narrative: "Rebuilt the auth service at NinjaLabs to reduce latency by 40%."
metrics:
  - "40% latency reduction"
evidence:
  - type: repo
    url: https://github.com/example/auth-service
---
"""

DRAFT_MDX = """\
---
id: draft-card
title: Draft Card
type: project
period:
  start: 2024-06-01
status: draft
summary: "A draft card not ready for applications."
---
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-03-auth-service.mdx").write_text(LIVE_MDX, encoding="utf-8")
    (cards / "2024-06-draft-card.mdx").write_text(DRAFT_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def client(repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _cover_payload(card_ids=None, **tc_overrides):
    tc = {"organization": "Kakao", "role": "Backend Engineer"}
    tc.update(tc_overrides)
    ids = card_ids or ["auth-service"]
    return {"output_type": "cover_letter", "card_ids": ids, "target_context": tc}


def _answer_payload(card_ids=None, **tc_overrides):
    tc = {"question": "Describe a technical challenge you solved."}
    tc.update(tc_overrides)
    ids = card_ids or ["auth-service"]
    return {"output_type": "application_answer", "card_ids": ids, "target_context": tc}


# ── UI hooks ──────────────────────────────────────────────────────────────────


def test_studio_has_app_writing_section(client):
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"st-app-writing" in rv.data


def test_studio_has_app_card_selector(client):
    rv = client.get("/studio")
    assert b"st-app-card-selector" in rv.data


def test_studio_has_app_output_type_controls(client):
    rv = client.get("/studio")
    assert b"st-app-output-type" in rv.data
    assert b"cover_letter" in rv.data
    assert b"application_answer" in rv.data


def test_studio_has_app_target_context_fields(client):
    rv = client.get("/studio")
    assert b"st-app-organization" in rv.data
    assert b"st-app-role" in rv.data
    assert b"st-app-question" in rv.data
    assert b"st-app-competency" in rv.data
    assert b"st-app-charlimit" in rv.data
    assert b"st-app-blind" in rv.data


def test_studio_has_app_preview_button(client):
    rv = client.get("/studio")
    assert b"st-app-preview-btn" in rv.data


def test_studio_has_app_preview_output_hooks(client):
    rv = client.get("/studio")
    assert b"st-app-result" in rv.data
    assert b"st-app-draft-text" in rv.data
    assert b"st-app-copy-btn" in rv.data
    assert b"st-app-fallback-notice" in rv.data


def test_studio_has_app_grounding_hooks(client):
    rv = client.get("/studio")
    assert b"st-app-facts-list" in rv.data
    assert b"st-app-context-list" in rv.data


def test_studio_js_has_app_functions(client):
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"generateAppPreview" in rv.data
    assert b"loadAppCards" in rv.data
    assert b"renderAppPreview" in rv.data
    assert b"copyAppDraft" in rv.data


def test_studio_js_calls_application_preview_endpoint(client):
    rv = client.get("/static/studio.js")
    assert b"application-preview" in rv.data


# ── Validation ────────────────────────────────────────────────────────────────


def test_app_rejects_invalid_output_type(client):
    rv = client.post(
        "/api/studio/application-preview",
        json={"output_type": "linkedin", "card_ids": ["auth-service"], "target_context": {}},
    )
    assert rv.status_code == 400
    assert "output_type" in rv.get_json()["error"].lower()


def test_app_rejects_empty_card_ids(client):
    rv = client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "cover_letter",
            "card_ids": [],
            "target_context": {"organization": "Kakao"},
        },
    )
    assert rv.status_code == 400
    assert "card_ids" in rv.get_json()["error"].lower()


def test_app_rejects_missing_card_ids_key(client):
    rv = client.post(
        "/api/studio/application-preview",
        json={"output_type": "cover_letter", "target_context": {"organization": "Kakao"}},
    )
    assert rv.status_code == 400


def test_app_cover_letter_requires_org_role_or_jd(client):
    rv = client.post(
        "/api/studio/application-preview",
        json={"output_type": "cover_letter", "card_ids": ["auth-service"], "target_context": {}},
    )
    assert rv.status_code == 400
    assert "cover_letter" in rv.get_json()["error"].lower()


def test_app_answer_requires_question(client):
    rv = client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["auth-service"],
            "target_context": {"competency": "problem-solving"},
        },
    )
    assert rv.status_code == 400
    assert "question" in rv.get_json()["error"].lower()


def test_app_rejects_character_limit_zero(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post("/api/studio/application-preview", json=_answer_payload(character_limit=0))
    assert rv.status_code == 400


def test_app_accepts_character_limit_one(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post("/api/studio/application-preview", json=_answer_payload(character_limit=1))
    assert rv.status_code == 200


def test_app_accepts_character_limit_5000(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post("/api/studio/application-preview", json=_answer_payload(character_limit=5000))
    assert rv.status_code == 200


def test_app_rejects_character_limit_5001(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post("/api/studio/application-preview", json=_answer_payload(character_limit=5001))
    assert rv.status_code == 400


def test_app_rejects_unknown_card(client):
    rv = client.post(
        "/api/studio/application-preview",
        json=_answer_payload(card_ids=["nonexistent-card"]),
    )
    assert rv.status_code == 404
    assert "not found" in rv.get_json()["error"].lower()


def test_app_rejects_draft_card(client):
    rv = client.post(
        "/api/studio/application-preview",
        json=_answer_payload(card_ids=["draft-card"]),
    )
    assert rv.status_code == 422
    assert "not live" in rv.get_json()["error"].lower()


# ── Mock output ───────────────────────────────────────────────────────────────


def _mock_client(client, payload):
    """Post to application-preview without LLM configured."""
    return client.post("/api/studio/application-preview", json=payload)


def test_mock_cover_letter_returns_ok(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _cover_payload())
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    preview = body["preview"]
    assert preview["output_type"] == "cover_letter"
    assert "answer_draft" in preview
    assert len(preview["answer_draft"]) > 0


def test_mock_answer_returns_ok(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    preview = body["preview"]
    assert preview["output_type"] == "application_answer"
    assert "answer_draft" in preview


def test_mock_personal_facts_come_from_cards_not_target(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    # Card title must appear in personal_facts
    assert any("Auth Service" in f for f in preview["personal_facts"])
    # Question text must appear in target_context_used, not personal_facts
    assert any("Question" in t for t in preview["target_context_used"])
    assert not any("technical challenge" in f.lower() for f in preview["personal_facts"])


def test_mock_target_context_used_contains_org_and_role(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _cover_payload(organization="Kakao", role="Backend Engineer"))
    preview = rv.get_json()["preview"]
    assert any("Kakao" in t for t in preview["target_context_used"])
    assert any("Backend Engineer" in t for t in preview["target_context_used"])


def test_mock_cover_letter_is_deterministic(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    payload = _cover_payload()
    r1 = _mock_client(client, payload).get_json()
    r2 = _mock_client(client, payload).get_json()
    assert r1["preview"]["answer_draft"] == r2["preview"]["answer_draft"]


def test_mock_has_selected_cards_field(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert "selected_cards" in preview
    sc = preview["selected_cards"]
    assert len(sc) == 1
    assert sc[0]["id"] == "auth-service"
    assert sc[0]["title"] == "Auth Service"
    assert "selection_reason" in sc[0] and sc[0]["selection_reason"]


# ── Selection: multiple cards ─────────────────────────────────────────────────


def test_multiple_live_cards_allowed(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    cards.joinpath("2024-03-auth-service.mdx").write_text(LIVE_MDX, encoding="utf-8")
    second_mdx = (
        LIVE_MDX.replace("auth-service", "second-project")
        .replace("Auth Service", "Second Project")
        .replace("2024-03-01", "2024-06-01")
    )
    cards.joinpath("2024-06-second-project.mdx").write_text(second_mdx, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    app.config["TESTING"] = True
    with app.test_client() as c:
        rv = c.post(
            "/api/studio/application-preview",
            json=_answer_payload(card_ids=["auth-service", "second-project"]),
        )
        assert rv.status_code == 200
        preview = rv.get_json()["preview"]
        assert len(preview["selected_cards"]) == 2
        ids = [sc["id"] for sc in preview["selected_cards"]]
        assert "auth-service" in ids and "second-project" in ids


def test_unselected_card_facts_not_in_personal_facts(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    cards.joinpath("2024-03-auth-service.mdx").write_text(LIVE_MDX, encoding="utf-8")
    other_mdx = (
        LIVE_MDX.replace("auth-service", "other-card")
        .replace("Auth Service", "Other Card")
        .replace("Rebuilt the auth", "Built the other")
    )
    cards.joinpath("2024-06-other-card.mdx").write_text(other_mdx, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    app.config["TESTING"] = True
    with app.test_client() as c:
        rv = c.post(
            "/api/studio/application-preview",
            json=_answer_payload(card_ids=["auth-service"]),
        )
        preview = rv.get_json()["preview"]
        assert not any("Other Card" in f for f in preview["personal_facts"])


# ── Grounding contract ────────────────────────────────────────────────────────


def test_adding_org_changes_target_context_not_personal_facts(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv_no_org = _mock_client(client, _answer_payload())
    rv_with_org = _mock_client(client, _answer_payload(organization="Kakao"))
    pf_no_org = rv_no_org.get_json()["preview"]["personal_facts"]
    pf_with_org = rv_with_org.get_json()["preview"]["personal_facts"]
    assert pf_no_org == pf_with_org


def test_no_organization_motivation_without_context(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert not any("Organization" in t for t in preview["target_context_used"])


# ── Question / character-count ────────────────────────────────────────────────


def test_answer_preview_exposes_question_intent(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert preview.get("question_intent")
    assert (
        "technical challenge" in preview["question_intent"].lower()
        or "assessing" in preview["question_intent"].lower()
    )


def test_character_count_is_accurate(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert preview["character_count"] == len(preview["answer_draft"])


def test_within_limit_true_when_draft_fits(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload(character_limit=5000))
    preview = rv.get_json()["preview"]
    assert preview["within_limit"] is True
    assert preview["character_limit"] == 5000


def test_character_limit_truncates_draft(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload(character_limit=10))
    preview = rv.get_json()["preview"]
    assert preview["character_count"] <= 10
    assert preview["within_limit"] is True


def test_no_char_limit_within_limit_is_none(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert preview["within_limit"] is None
    assert preview["character_limit"] is None


# ── Blind hiring ──────────────────────────────────────────────────────────────


def test_blind_hiring_adds_review_missing_info(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload(blind_hiring=True))
    preview = rv.get_json()["preview"]
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_REVIEW" in codes


def test_no_blind_hiring_has_no_review_missing_info(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_REVIEW" not in codes


def test_blind_hiring_in_target_context_used(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload(blind_hiring=True))
    preview = rv.get_json()["preview"]
    assert any("blind" in t.lower() for t in preview["target_context_used"])


# ── Provider / fallback transparency ─────────────────────────────────────────


def test_mock_fallback_has_not_configured_reason(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert preview["refine_source"] == "mock"
    assert preview["fallback_reason"] == "not_configured"


def test_mock_fallback_quota_error_reason(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_app_preview(*args, **kwargs):
        raise Exception("Resource exhausted: quota limit reached")

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_app_preview)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert preview["refine_source"] == "mock"
    assert preview["fallback_reason"] == "quota_or_rate_limit"


def test_mock_fallback_auth_error_reason(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_app_preview(*args, **kwargs):
        raise Exception("Authentication failed: invalid api_key")

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_app_preview)
    rv = _mock_client(client, _answer_payload())
    preview = rv.get_json()["preview"]
    assert preview["fallback_reason"] == "auth_failed"


def test_fallback_reason_does_not_leak_key(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-real-secret-key-12345")

    def fake_app_preview(*args, **kwargs):
        raise Exception("Auth failed: sk-real-secret-key-12345")

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_app_preview)
    rv = _mock_client(client, _answer_payload())
    assert b"sk-real-secret-key-12345" not in rv.data


def test_llm_app_preview_google_schema_used():
    """Google path requests structured output with _APP_WRITING_SCHEMA."""
    captured_config = {}

    class FakeGenerateContentConfig:
        def __init__(self, **kw):
            captured_config.update(kw)

    fake_response_text = json.dumps(
        {
            "personal_facts": ["Activity: Auth Service"],
            "target_context_used": ["Question: describe challenge"],
            "selected_cards": [
                {"id": "auth-service", "title": "Auth Service", "selection_reason": "relevant"}
            ],
            "assumptions": [],
            "missing_info": [],
            "answer_draft": "Draft answer.",
            "question_intent": "Assessing problem solving",
            "competency_target": "",
        }
    )

    fake_response = MagicMock()
    fake_response.text = fake_response_text
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    fake_card = MagicMock()
    fake_card.id = "auth-service"
    fake_card.title = "Auth Service"
    fake_card.summary = "Rebuilt auth service."
    fake_card.metrics = []
    fake_card.evidence = []

    with (
        patch("scripts.llm._build_client", return_value=fake_client),
        patch("scripts.llm._cache_read", return_value=None),
        patch("scripts.llm._cache_write"),
        patch(
            "scripts.llm.resolve_provider_config",
            return_value={"provider": "google", "model": "gemini-2.5-flash", "api_key": "fake"},
        ),
        patch("google.genai.types.GenerateContentConfig", FakeGenerateContentConfig),
    ):
        result = llm_mod.application_preview_llm(
            "application_answer", [fake_card], {"question": "describe challenge"}, no_cache=True
        )

    assert result["ok"] is True
    assert "response_schema" in captured_config
    assert captured_config["response_mime_type"] == "application/json"


def test_app_writing_schema_has_required_fields():
    assert "personal_facts" in llm_mod._APP_WRITING_SCHEMA["required"]
    assert "target_context_used" in llm_mod._APP_WRITING_SCHEMA["required"]
    assert "answer_draft" in llm_mod._APP_WRITING_SCHEMA["required"]
    assert "missing_info" in llm_mod._APP_WRITING_SCHEMA["required"]


# ── Preview not saved as card ─────────────────────────────────────────────────


def test_application_preview_does_not_create_card_file(client, repo, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    before = list((repo / "cards").glob("*.mdx"))
    _mock_client(client, _answer_payload())
    after = list((repo / "cards").glob("*.mdx"))
    assert len(after) == len(before)


# ── Refine fallback_reason (existing endpoint) ────────────────────────────────


def test_refine_mock_has_fallback_reason(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Some project 2024-01", "intent": "both"}
    )
    assert rv.status_code == 200
    draft = rv.get_json()["draft"]
    assert draft["refine_source"] == "mock"
    assert "fallback_reason" in draft
    assert draft["fallback_reason"] == "not_configured"


def test_refine_fallback_reason_on_llm_error(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_refine(*a, **kw):
        raise Exception("quota exhausted rate limit")

    monkeypatch.setattr(llm_mod, "studio_refine_llm", fake_refine)
    rv = client.post("/api/studio/refine", json={"raw_text": "Project 2024-01", "intent": "both"})
    assert rv.status_code == 200
    draft = rv.get_json()["draft"]
    assert draft["refine_source"] == "mock"
    assert draft["fallback_reason"] == "quota_or_rate_limit"


# ── Regression ────────────────────────────────────────────────────────────────


def test_existing_refine_endpoint_still_works(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={"raw_text": "Auth service 2024-03 https://github.com/x", "intent": "both"},
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert "draft" in body and "missing_info" in body


def test_existing_save_endpoint_still_works(client, repo, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv_refine = client.post(
        "/api/studio/refine",
        json={"raw_text": "My project 2024-05 https://github.com/x 30%", "intent": "both"},
    )
    draft = rv_refine.get_json()["draft"]
    rv_save = client.post("/api/studio/save", json={"draft": draft})
    assert rv_save.status_code == 201
    assert rv_save.get_json()["ok"] is True


def test_dashboard_endpoint_still_works(client):
    rv = client.get("/dashboard")
    assert rv.status_code == 200


# ── Review-v1 Regression Tests ────────────────────────────────────────────────

_IDENTITY_CARD_MDX = """\
---
id: snu-project
title: Seoul National University Graduate
type: project
period:
  start: 2024-01-01
status: live
summary: "Born in Busan; led an analytics migration project."
---
"""


@pytest.fixture()
def identity_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-01-snu-project.mdx").write_text(_IDENTITY_CARD_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def identity_client(identity_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _snu_answer_payload(**tc_overrides):
    tc = {"question": "Describe a challenge you solved."}
    tc.update(tc_overrides)
    return {"output_type": "application_answer", "card_ids": ["snu-project"], "target_context": tc}


# ISSUE-1: LLM/cache provenance enforcement


def test_llm_provenance_overrides_adversarial_llm_response():
    """personal_facts and selected_cards built server-side even when LLM returns fabrications."""
    adversarial_json = json.dumps(
        {
            "personal_facts": ["Metric: increased revenue 999%", "Role: CEO"],
            "target_context_used": ["Question: describe challenge"],
            "selected_cards": [
                {"id": "not-selected", "title": "Fake Card", "selection_reason": "invented"}
            ],
            "assumptions": [],
            "missing_info": [],
            "answer_draft": "I as CEO increased revenue 999%.",
            "question_intent": "problem solving",
            "competency_target": "",
        }
    )
    fake_response = MagicMock()
    fake_response.text = adversarial_json
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    fake_card = MagicMock()
    fake_card.id = "auth-service"
    fake_card.title = "Auth Service"
    fake_card.summary = "Rebuilt auth service."
    fake_card.metrics = []
    fake_card.evidence = []

    with (
        patch("scripts.llm._build_client", return_value=fake_client),
        patch("scripts.llm._cache_read", return_value=None),
        patch("scripts.llm._cache_write"),
        patch(
            "scripts.llm.resolve_provider_config",
            return_value={"provider": "google", "model": "gemini-2.5-flash", "api_key": "fake"},
        ),
        patch("google.genai.types.GenerateContentConfig", lambda **kw: MagicMock()),
    ):
        result = llm_mod.application_preview_llm(
            "application_answer", [fake_card], {"question": "describe challenge"}, no_cache=True
        )

    assert result["ok"] is True
    preview = result["preview"]
    assert not any("999%" in f for f in preview["personal_facts"])
    assert not any("CEO" in f for f in preview["personal_facts"])
    assert any("Auth Service" in f for f in preview["personal_facts"])
    ids = [sc["id"] for sc in preview["selected_cards"]]
    assert "not-selected" not in ids
    assert "auth-service" in ids
    # target_context_used must be server-side built; adversarial org must not appear
    assert not any("Fabricated Corp" in t for t in preview["target_context_used"])


# ISSUE-2: Blind-hiring identity detection


def test_blind_hiring_identity_card_triggers_identifier_flag(identity_client, monkeypatch):
    """Card with identity/background content in blind-hiring mode emits identifier flag."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 200
    codes = [m["code"] for m in rv.get_json()["preview"]["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes


def test_blind_hiring_identity_content_not_in_personal_facts(identity_client, monkeypatch):
    """Identity/background text is excluded from personal_facts in blind-hiring mode."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    preview = rv.get_json()["preview"]
    assert not any("Seoul National University" in f for f in preview["personal_facts"])
    assert not any("Born in Busan" in f for f in preview["personal_facts"])


def test_blind_hiring_identity_content_not_in_draft(identity_client, monkeypatch):
    """Identity/background text does not appear in the answer draft under blind-hiring mode."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    draft = rv.get_json()["preview"]["answer_draft"]
    assert "Seoul National University" not in draft
    assert "Born in Busan" not in draft


# ISSUE-3: Malformed response classification and refine-source rendering


def test_malformed_app_response_gives_malformed_response_fallback(client, monkeypatch):
    """Malformed LLM response for application-preview falls back with malformed_response reason."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_app_preview(*args, **kwargs):
        raise Exception("Malformed application_preview response: unexpected JSON structure")

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_app_preview)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert preview["fallback_reason"] == "malformed_response"
    assert preview["refine_source"] == "mock"


def test_studio_js_exposes_fallback_reason_in_refine_source(client):
    """studio.js renders fallback_reason alongside the source label in renderPreview."""
    rv = client.get("/static/studio.js")
    assert b"fallback_reason" in rv.data
    assert b"st-refine-source" in rv.data


# ISSUE-4: Selection rationale and assumptions render hooks


def test_studio_html_has_app_selected_section_hooks(client):
    rv = client.get("/studio")
    assert b"st-app-selected-section" in rv.data
    assert b"st-app-selected-list" in rv.data


def test_studio_html_has_app_assumptions_section_hooks(client):
    rv = client.get("/studio")
    assert b"st-app-assumptions-section" in rv.data
    assert b"st-app-assumptions-list" in rv.data


def test_studio_js_renders_selected_cards_rationale(client):
    rv = client.get("/static/studio.js")
    assert b"st-app-selected-section" in rv.data
    assert b"selected_cards" in rv.data
    assert b"selection_reason" in rv.data


def test_studio_js_renders_app_assumptions_block(client):
    rv = client.get("/static/studio.js")
    assert b"st-app-assumptions-section" in rv.data
    assert b"assumptions" in rv.data


# ISSUE-1 (route-level): grounding guard on answer_draft


def test_adversarial_llm_answer_triggers_grounding_fallback(client, monkeypatch):
    """Route grounding guard falls back when LLM answer contains invented metrics or roles."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, cards, target_context, **kwargs):
        return {
            "ok": True,
            "preview": {
                "personal_facts": ["Metric: increased revenue 999%"],
                "target_context_used": ["Organization: Fabricated Corp"],
                "selected_cards": [
                    {"id": "auth-service", "title": "Auth Service", "selection_reason": "r"}
                ],
                "assumptions": [],
                "missing_info": [],
                "answer_draft": "As CEO, I increased revenue 999% at Fabricated Corp.",
                "question_intent": "problem solving",
                "competency_target": "",
                "character_count": 51,
                "character_limit": None,
                "within_limit": None,
                "refine_source": "llm",
                "fallback_reason": None,
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert preview["refine_source"] == "mock"
    assert preview["fallback_reason"] == "malformed_response"
    assert "999%" not in preview["answer_draft"]
    assert "CEO" not in preview["answer_draft"]
    assert not any("Fabricated Corp" in t for t in preview["target_context_used"])


# ISSUE-2 (route-level): blind-hiring shared helper on LLM path


def test_llm_path_blind_hiring_identity_excluded_by_route(identity_client, monkeypatch):
    """Route applies blind-hiring redaction via shared helper on LLM path too."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, cards, target_context, **kwargs):
        return {
            "ok": True,
            "preview": {
                "personal_facts": [
                    "Activity: Seoul National University Graduate",
                    "Summary: Born in Busan; led an analytics migration project.",
                ],
                "target_context_used": ["Question: describe challenge"],
                "selected_cards": [
                    {
                        "id": "snu-project",
                        "title": "Seoul National University Graduate",
                        "selection_reason": "relevant",
                    }
                ],
                "assumptions": [],
                "missing_info": [],
                "answer_draft": "I developed analytics capabilities.",
                "question_intent": "assessing problem solving",
                "competency_target": "",
                "character_count": 35,
                "character_limit": None,
                "within_limit": None,
                "refine_source": "llm",
                "fallback_reason": None,
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert not any("Seoul National University" in f for f in preview["personal_facts"])
    assert not any("Born in Busan" in f for f in preview["personal_facts"])
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes
