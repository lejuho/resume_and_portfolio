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
    assert sc[0]["display_title"] == "Auth Service"
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
    """Google path requests structured output with _APP_ADVISORY_SCHEMA."""
    captured_config = {}

    class FakeGenerateContentConfig:
        def __init__(self, **kw):
            captured_config.update(kw)

    fake_response_text = json.dumps(
        {
            "selected_fact_ids": ["F1"],
            "question_intent": "Assessing problem solving",
            "competency_target": "",
            "missing_info": [],
            "ai_guidance": [],
        }
    )

    fake_response = MagicMock()
    fake_response.text = fake_response_text
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    fake_ledger = [
        {"id": "F1", "kind": "activity", "text": "Auth Service", "source_card_id": "auth-service"}
    ]

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
            "application_answer", fake_ledger, {"question": "describe challenge"}, no_cache=True
        )

    assert result["ok"] is True
    assert "advisory" in result
    assert "response_schema" in captured_config
    assert captured_config["response_mime_type"] == "application/json"


def test_app_writing_schema_has_required_fields():
    assert "selected_fact_ids" in llm_mod._APP_ADVISORY_SCHEMA["required"]
    assert "question_intent" in llm_mod._APP_ADVISORY_SCHEMA["required"]
    assert "missing_info" in llm_mod._APP_ADVISORY_SCHEMA["required"]


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
    """LLM advisory with unknown fact IDs is returned as-is; route filters fabricated IDs."""
    adversarial_json = json.dumps(
        {
            "selected_fact_ids": ["FAKE-99", "not-a-real-id"],
            "question_intent": "problem solving",
            "competency_target": "",
            "missing_info": [],
            "ai_guidance": ["Mention CEO role at Fabricated Corp."],
        }
    )
    fake_response = MagicMock()
    fake_response.text = adversarial_json
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    fake_ledger = [
        {"id": "F1", "kind": "activity", "text": "Auth Service", "source_card_id": "auth-service"},
        {
            "id": "F2",
            "kind": "summary",
            "text": "Rebuilt auth service.",
            "source_card_id": "auth-service",
        },
    ]

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
            "application_answer", fake_ledger, {"question": "describe challenge"}, no_cache=True
        )

    assert result["ok"] is True
    advisory = result["advisory"]
    # LLM-returned IDs are passed through; the route discards unknown ones
    assert advisory["selected_fact_ids"] == ["FAKE-99", "not-a-real-id"]
    assert advisory["question_intent"] == "problem solving"
    # ai_guidance is advisory only — returned but never enters answer_draft
    assert any("Fabricated Corp" in g for g in advisory["ai_guidance"])


# ISSUE-2: Blind-hiring identity detection


def test_blind_hiring_identity_card_triggers_identifier_flag(identity_client, monkeypatch):
    """All-identity cards in blind-hiring mode return 422 — no preview exposed."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 422
    body = rv.get_json()
    assert not body["ok"]
    assert "blind-hiring policy" in body["error"]


def test_blind_hiring_identity_content_not_in_personal_facts(identity_client, monkeypatch):
    """All-identity cards under blind-hiring return 422 — no personal_facts in response."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 422
    body = rv.get_json()
    assert "preview" not in body


def test_blind_hiring_identity_content_not_in_draft(identity_client, monkeypatch):
    """All-identity cards under blind-hiring return 422 — no answer_draft in response."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 422
    body = rv.get_json()
    assert "preview" not in body


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


# ISSUE-1 (route-level): server-composed answer replaces LLM prose


def test_llm_path_qualitative_fabrication_absent_from_answer(client, monkeypatch):
    """LLM prose with qualitative fabrications is replaced by server-composed answer."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, cards, target_context, **kwargs):
        return {
            "ok": True,
            "preview": {
                "personal_facts": [],
                "target_context_used": [],
                "selected_cards": [],
                "assumptions": [],
                "missing_info": [],
                "answer_draft": "I founded Fabricated Corp and led its global expansion.",
                "question_intent": "problem solving",
                "competency_target": "",
                "character_count": 55,
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
    assert "Fabricated Corp" not in preview["answer_draft"]
    assert "founded" not in preview["answer_draft"]


def test_llm_path_answer_composed_from_card_facts_only(client, monkeypatch):
    """Route composes answer_draft from server-authoritative card titles, not LLM prose."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, cards, target_context, **kwargs):
        return {
            "ok": True,
            "preview": {
                "personal_facts": ["Activity: Fabricated Service"],
                "target_context_used": ["Organization: Fabricated Corp"],
                "selected_cards": [],
                "assumptions": [],
                "missing_info": [],
                "answer_draft": "As CEO of Fabricated Corp I achieved 999% growth.",
                "question_intent": "problem solving",
                "competency_target": "",
                "character_count": 50,
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
    # answer_draft must mention the real card title, not the LLM-invented content
    assert "Auth Service" in preview["answer_draft"]
    assert "Fabricated Corp" not in preview["answer_draft"]
    assert "999%" not in preview["answer_draft"]
    # refine_source should be "llm" (non-blind-hiring LLM path succeeds)
    assert preview["refine_source"] == "llm"


# ISSUE-2 (route-level): blind-hiring shared helper on LLM path


def test_llm_path_blind_hiring_identity_excluded_by_route(identity_client, monkeypatch):
    """All-identity card under blind-hiring returns 422 before LLM is called."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    llm_called = []

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        llm_called.append(True)
        return {"advisory": {}}

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 422
    assert not llm_called
    body = rv.get_json()
    assert not body["ok"]
    assert "blind-hiring policy" in body["error"]


# ── Revised Sprint Contract: fact_ledger, draft_provenance, ai_guidance ───────


def test_response_includes_fact_ledger_and_provenance(client, monkeypatch):
    """Mock response includes fact_ledger entries and draft_provenance=server_composed."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert "fact_ledger" in preview
    assert len(preview["fact_ledger"]) > 0
    entry = preview["fact_ledger"][0]
    assert "id" in entry and "kind" in entry and "text" in entry and "source_card_id" in entry
    assert preview["draft_provenance"] == "server_composed"
    assert "selected_facts" in preview


def test_llm_path_unknown_fact_ids_discarded(client, monkeypatch):
    """LLM returning non-existent fact IDs falls back to all ledger facts for draft."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": ["UNKNOWN-99", "FAKE-100"],
                "question_intent": "problem solving",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # No unknown IDs → falls back to all ledger facts → real card title in draft
    assert "Auth Service" in preview["answer_draft"]
    assert preview["refine_source"] == "llm"
    assert preview["draft_provenance"] == "server_composed"


def test_blind_hiring_llm_not_called_when_identity_flagged(identity_client, monkeypatch):
    """Route skips LLM call when blind_hiring=True and identity card is selected."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    llm_called = []

    def fake_llm(*args, **kwargs):
        llm_called.append(True)
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [],
                "question_intent": "",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert len(llm_called) == 0, "LLM must not be called when identity card is flagged"


def test_llm_path_response_includes_new_fields(client, monkeypatch):
    """LLM path response includes fact_ledger, selected_facts, draft_provenance, ai_guidance."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing problem solving",
                "competency_target": "analytical",
                "missing_info": [],
                "ai_guidance": ["Consider adding quantitative outcomes."],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert preview["draft_provenance"] == "server_composed"
    assert "fact_ledger" in preview
    assert "selected_facts" in preview
    assert "ai_guidance" in preview
    assert preview["ai_guidance"] == ["Consider adding quantitative outcomes."]
    assert preview["refine_source"] == "llm"


def test_studio_html_has_app_guidance_section(client):
    rv = client.get("/studio")
    assert b"st-app-guidance-section" in rv.data
    assert b"st-app-guidance-list" in rv.data


def test_studio_js_renders_ai_guidance_separately(client):
    rv = client.get("/static/studio.js")
    assert b"st-app-guidance-section" in rv.data
    assert b"ai_guidance" in rv.data


# --- review-v5 new coverage ---


def test_selected_facts_expands_to_include_activity_for_summary_selection(client, monkeypatch):
    """When LLM selects only a summary fact (F2), selected_facts expands to include F1."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        # Find the first summary entry and return only its ID.
        summary_id = next((e["id"] for e in fact_ledger if e["kind"] == "summary"), None)
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [summary_id] if summary_id else [],
                "question_intent": "problem solving",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = _mock_client(client, _answer_payload())
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    selected = preview["selected_facts"]
    ledger = preview["fact_ledger"]
    activity_ids = {e["id"] for e in ledger if e["kind"] == "activity"}
    # At least one activity ID must appear in selected_facts.
    assert activity_ids & set(selected), (
        f"selected_facts {selected} must include an activity fact when summary is selected; "
        f"activity IDs in ledger: {activity_ids}"
    )


def test_blind_hiring_provider_guidance_identity_withheld(client, monkeypatch):
    """Under blind_hiring, provider guidance with identity text is withheld."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    identity_guidance = "Seoul National University graduate with strong analytical skills."
    clean_guidance = "Consider quantifying the performance improvement."

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "problem solving",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [identity_guidance, clean_guidance],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    payload = _answer_payload()
    payload["target_context"]["blind_hiring"] = True
    rv = _mock_client(client, payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # Identity guidance must not appear.
    assert identity_guidance not in preview.get("ai_guidance", [])
    # Clean guidance may remain.
    assert clean_guidance in preview.get("ai_guidance", [])
    # Warning must be emitted.
    codes = [m.get("code") for m in preview.get("missing_info", [])]
    assert "BLIND_HIRING_GUIDANCE_REDACTED" in codes


def test_advisory_cache_separates_different_ledgers(tmp_path, monkeypatch):
    """Two ledgers with same positional IDs but different texts get different cache keys."""
    from scripts.llm import _cache_key

    monkeypatch.setenv("AI_PROVIDER", "anthropic")

    base_payload = {
        "schema_ver": "1",
        "app_ver": 2,
        "task": "application_advisory",
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "output_type": "application_answer",
        "target_context": {"question": "Describe a challenge", "character_limit": 500},
    }

    ledger_a = [{"id": "F1", "kind": "activity", "text": "Auth Service", "source_card_id": "c1"}]
    ledger_b = [
        {"id": "F1", "kind": "activity", "text": "Payments Platform", "source_card_id": "c2"}
    ]

    key_a = _cache_key({**base_payload, "fact_ledger": ledger_a})
    key_b = _cache_key({**base_payload, "fact_ledger": ledger_b})

    assert key_a != key_b, (
        "Different ledger contents must produce different cache keys; "
        "same key risks returning Auth Service guidance for Payments Platform."
    )


# ── review-v6: ISSUE-8 — advisory surface blind-hiring screening ──────────────

_IDENTITY_METRIC_MDX = """\
---
id: payment-service
title: Payment Service
type: project
period:
  start: 2024-05-01
status: live
summary: "Optimized payment processing pipeline by 30%."
metrics:
  - "Seoul National University graduate led delivery"
  - "30% performance improvement"
evidence:
  - type: repo
    url: https://github.com/example/payment-service
---
"""

_IDENTITY_EVIDENCE_MDX = """\
---
id: search-service
title: Search Service
type: project
period:
  start: 2024-07-01
status: live
summary: "Built distributed search indexing."
metrics:
  - "50% faster query response"
evidence:
  - type: repo
    url: https://alumni.example.com/search-project
---
"""


@pytest.fixture()
def metric_identity_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-05-payment-service.mdx").write_text(_IDENTITY_METRIC_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def metric_identity_client(metric_identity_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def evidence_identity_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-07-search-service.mdx").write_text(_IDENTITY_EVIDENCE_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def evidence_identity_client(evidence_identity_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _payment_answer_payload(**tc_overrides):
    tc = {"question": "Describe a technical challenge you solved."}
    tc.update(tc_overrides)
    return {
        "output_type": "application_answer",
        "card_ids": ["payment-service"],
        "target_context": tc,
    }  # noqa: E501


def _search_answer_payload(**tc_overrides):
    tc = {"question": "Describe a technical challenge you solved."}
    tc.update(tc_overrides)
    return {
        "output_type": "application_answer",
        "card_ids": ["search-service"],
        "target_context": tc,
    }  # noqa: E501


# ISSUE-8: question_intent screening


def test_blind_hiring_question_intent_identity_withheld(client, monkeypatch):
    """Provider question_intent with identity phrase is replaced with safe wording."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    identity_intent = "Assess Seoul National University graduate background"

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": identity_intent,
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    payload = _answer_payload()
    payload["target_context"]["blind_hiring"] = True
    rv = _mock_client(client, payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert "Seoul National University" not in preview["question_intent"]
    assert preview["question_intent"] != ""
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_ADVISORY_REDACTED" in codes


# ISSUE-8: competency_target screening


def test_blind_hiring_competency_target_identity_withheld(client, monkeypatch):
    """Provider competency_target with identity phrase is replaced with safe wording."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    identity_competency = "Born in Busan leadership style"

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing problem solving",
                "competency_target": identity_competency,
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    payload = _answer_payload()
    payload["target_context"]["blind_hiring"] = True
    rv = _mock_client(client, payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert "Born in Busan" not in preview["competency_target"]
    assert preview["competency_target"] != ""
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_ADVISORY_REDACTED" in codes


# ISSUE-8: missing_info message screening


def test_blind_hiring_missing_info_message_identity_withheld(client, monkeypatch):
    """Provider missing_info item with identity message has message replaced; code preserved."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing problem solving",
                "competency_target": "",
                "missing_info": [
                    {
                        "code": "SOME_PROVIDER_CODE",
                        "message": "Confirm university alumni history.",
                    }
                ],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    payload = _answer_payload()
    payload["target_context"]["blind_hiring"] = True
    rv = _mock_client(client, payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # Identity phrase must not appear anywhere in missing_info messages.
    for m in preview["missing_info"]:
        assert "university" not in m.get("message", "").lower()
    # Original code must be preserved (message replaced, not dropped).
    codes = [m["code"] for m in preview["missing_info"]]
    assert "SOME_PROVIDER_CODE" in codes
    assert "BLIND_HIRING_ADVISORY_REDACTED" in codes


# ISSUE-9: metric-only identity card — mock path


def test_blind_hiring_metric_identity_excluded_from_ledger_mock(
    metric_identity_client, monkeypatch
):
    """Identity-bearing metric excluded from fact_ledger and preview in mock path."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = metric_identity_client.post(
        "/api/studio/application-preview",
        json=_payment_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # Identity metric must not appear in fact_ledger.
    for entry in preview["fact_ledger"]:
        assert "Seoul National University" not in entry["text"]
    # Must not appear in answer_draft or personal_facts.
    assert "Seoul National University" not in preview["answer_draft"]
    for f in preview["personal_facts"]:
        assert "Seoul National University" not in f
    # Warning must be emitted.
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes


# ISSUE-9: metric-only identity card — LLM path (provider input capture)


def test_blind_hiring_metric_identity_excluded_from_llm_input(metric_identity_client, monkeypatch):
    """Identity-bearing metric must not reach provider input or returned fact_ledger."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    captured_ledger: list = []

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        captured_ledger.extend(fact_ledger)
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing delivery ownership",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = metric_identity_client.post(
        "/api/studio/application-preview",
        json=_payment_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # Provider input must not contain the identity metric.
    for entry in captured_ledger:
        assert "Seoul National University" not in entry["text"]
    # Returned fact_ledger must not contain it either.
    for entry in preview["fact_ledger"]:
        assert "Seoul National University" not in entry["text"]
    # Answer preview must not contain it.
    assert "Seoul National University" not in preview["answer_draft"]


# ISSUE-9: evidence-only identity card — mock path


def test_blind_hiring_evidence_identity_excluded_from_ledger_mock(
    evidence_identity_client, monkeypatch
):
    """Identity-bearing evidence URL excluded from fact_ledger and preview."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = evidence_identity_client.post(
        "/api/studio/application-preview",
        json=_search_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # Identity URL must not appear in fact_ledger.
    for entry in preview["fact_ledger"]:
        assert "alumni.example.com" not in entry["text"]
    # Must not appear in answer_draft or personal_facts.
    assert "alumni.example.com" not in preview["answer_draft"]
    for f in preview["personal_facts"]:
        assert "alumni.example.com" not in f
    # Warning must be emitted.
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes


# ISSUE-9: evidence-only identity card — LLM path (provider input capture)


def test_blind_hiring_evidence_identity_excluded_from_llm_input(
    evidence_identity_client, monkeypatch
):
    """Identity-bearing evidence URL must not reach provider input or returned fact_ledger."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    captured_ledger: list = []

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        captured_ledger.extend(fact_ledger)
        return {
            "ok": True,
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing search engineering",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            },
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = evidence_identity_client.post(
        "/api/studio/application-preview",
        json=_search_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    # Provider input must not contain identity URL.
    for entry in captured_ledger:
        assert "alumni.example.com" not in entry["text"]
    # Returned fact_ledger must not contain it.
    for entry in preview["fact_ledger"]:
        assert "alumni.example.com" not in entry["text"]
    assert "alumni.example.com" not in preview["answer_draft"]


# ── Amendment v3: Unified Blind-Hiring Boundary ────────────────────────────────

_OPAQUE_ID_CARD_MDX = """\
---
id: alumni-program-2024
title: Payment Gateway Integration
type: project
period:
  start: 2024-03-01
status: live
summary: "Built a high-performance payment gateway handling 10k TPS."
---
"""

_CLEAN_CARD_MDX = """\
---
id: auth-service
title: Auth Service Platform
type: project
period:
  start: 2024-02-01
status: live
summary: "Implemented OAuth2 authentication service."
---
"""


@pytest.fixture()
def opaque_id_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-03-alumni-program-2024.mdx").write_text(_OPAQUE_ID_CARD_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def opaque_id_client(opaque_id_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def partial_redact_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-01-snu-project.mdx").write_text(_IDENTITY_CARD_MDX, encoding="utf-8")
    (cards / "2024-02-auth-service.mdx").write_text(_CLEAN_CARD_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def partial_redact_client(partial_redact_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_blind_hiring_opaque_card_id_in_preview(opaque_id_client, monkeypatch):
    """Canonical card ID is replaced with opaque ref (C1) in all blind-hiring preview fields."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = opaque_id_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["alumni-program-2024"],
            "target_context": {"question": "Describe a technical challenge.", "blind_hiring": True},
        },
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    for entry in preview["fact_ledger"]:
        assert entry["source_card_id"] == "C1"
        assert entry["source_card_id"] != "alumni-program-2024"
    for sc in preview["selected_cards"]:
        assert sc["id"] != "alumni-program-2024"
    import json as _json

    assert "alumni-program-2024" not in _json.dumps(preview)


def test_blind_hiring_partial_redaction_returns_200_with_warning(
    partial_redact_client, monkeypatch
):
    """One excluded + one clean card: 200 with BLIND_HIRING_PERSONAL_IDENTIFIERS warning."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = partial_redact_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["snu-project", "auth-service"],
            "target_context": {"question": "Describe a challenge.", "blind_hiring": True},
        },
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes
    for entry in preview["fact_ledger"]:
        assert "Seoul National University" not in entry["text"]
        assert "Born in Busan" not in entry["text"]


def test_blind_hiring_all_redacted_returns_422_llm_not_called(identity_client, monkeypatch):
    """All cards excluded under blind-hiring: 422 returned before LLM is called."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    llm_called = []

    def fake_llm(*args, **kwargs):
        llm_called.append(True)
        return {"advisory": {}}

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 422
    assert not llm_called


def test_blind_hiring_target_context_identity_not_in_personal_facts(client, monkeypatch):
    """Identity in target_context flows to target_context_used but not card-derived fields."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    payload = _answer_payload()
    payload["target_context"]["blind_hiring"] = True
    payload["target_context"]["question"] = "How did Seoul National University alumni handle scale?"
    rv = _mock_client(client, payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    for pf in preview["personal_facts"]:
        assert "Seoul National University" not in pf
        assert "alumni" not in pf.lower()
    tcu_str = " ".join(preview["target_context_used"])
    assert "Seoul National University" in tcu_str


def test_blind_hiring_whole_payload_no_identity_in_card_derived_fields(
    partial_redact_client, monkeypatch
):
    """Full blind-hiring preview: card-derived fields contain no excluded identity markers."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = partial_redact_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["snu-project", "auth-service"],
            "target_context": {"question": "Describe a challenge.", "blind_hiring": True},
        },
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    _MARKERS = ("Seoul National University", "Born in Busan", "snu-project")
    for pf in preview["personal_facts"]:
        for marker in _MARKERS:
            assert marker not in pf
    for entry in preview["fact_ledger"]:
        for marker in _MARKERS:
            assert marker not in entry["text"]
            assert marker not in entry["source_card_id"]
    for marker in _MARKERS:
        assert marker not in preview["answer_draft"]


# ── Amendment v3: field-level screening (per-field, not per-card) ──────────────

_IDENTITY_TITLE_CLEAN_METRIC_MDX = """\
---
id: id-title-clean-metric
title: Seoul National University Project
type: project
period:
  start: 2024-04-01
status: live
summary: "Born in Busan, led research team."
metrics:
  - "30% performance improvement"
---
"""

_IDENTITY_SUMMARY_CLEAN_TITLE_MDX = """\
---
id: id-summary-clean-title
title: Payment Processing Service
type: project
period:
  start: 2024-05-01
status: live
summary: "Born in Busan, led payment team."
---
"""


@pytest.fixture()
def id_title_clean_metric_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-04-id-title-clean-metric.mdx").write_text(
        _IDENTITY_TITLE_CLEAN_METRIC_MDX, encoding="utf-8"
    )
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def id_title_clean_metric_client(id_title_clean_metric_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def id_summary_clean_title_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-05-id-summary-clean-title.mdx").write_text(
        _IDENTITY_SUMMARY_CLEAN_TITLE_MDX, encoding="utf-8"
    )
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def id_summary_clean_title_client(id_summary_clean_title_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_blind_hiring_identity_title_clean_metric_returns_200(
    id_title_clean_metric_client, monkeypatch
):
    """Identity title screened; card's clean metric remains usable — HTTP 200 with warning."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = id_title_clean_metric_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["id-title-clean-metric"],
            "target_context": {"question": "Describe a challenge.", "blind_hiring": True},
        },
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes
    metric_texts = [e["text"] for e in preview["fact_ledger"] if e["kind"] == "metric"]
    assert "30% performance improvement" in metric_texts
    for entry in preview["fact_ledger"]:
        assert "Seoul National University" not in entry["text"]
    for pf in preview["personal_facts"]:
        assert "Seoul National University" not in pf


def test_blind_hiring_identity_summary_safe_title_retained(
    id_summary_clean_title_client, monkeypatch
):
    """Identity summary screened; card's clean title is retained in blind-hiring preview."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = id_summary_clean_title_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["id-summary-clean-title"],
            "target_context": {"question": "Describe a challenge.", "blind_hiring": True},
        },
    )
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    codes = [m["code"] for m in preview["missing_info"]]
    assert "BLIND_HIRING_PERSONAL_IDENTIFIERS" in codes
    activity_texts = [e["text"] for e in preview["fact_ledger"] if e["kind"] == "activity"]
    assert "Payment Processing Service" in activity_texts
    for entry in preview["fact_ledger"]:
        assert "Born in Busan" not in entry["text"]
    for pf in preview["personal_facts"]:
        assert "Born in Busan" not in pf


def test_blind_hiring_identity_title_summary_no_safe_facts_returns_422(
    identity_client, monkeypatch
):
    """Card with identity title+summary and no safe metrics/evidence returns 422."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    llm_called = []

    def fake_llm(*args, **kwargs):
        llm_called.append(True)
        return {"advisory": {}}

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json=_snu_answer_payload(blind_hiring=True),
    )
    assert rv.status_code == 422
    assert not llm_called
    body = rv.get_json()
    assert not body["ok"]
    assert "blind-hiring policy" in body["error"]


# ── Amendment v3: target_context.competency policy ────────────────────────────

_IDENTITY_COMPETENCY = "Seoul National University graduate background"


def test_blind_hiring_identity_competency_not_in_draft_mock_path(client, monkeypatch):
    """Blind mode: identity competency absent from answer_draft; target_context_used keeps it."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    payload = _answer_payload(competency=_IDENTITY_COMPETENCY, blind_hiring=True)
    rv = _mock_client(client, payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert "Seoul National University" not in preview["answer_draft"]
    for pf in preview["personal_facts"]:
        assert "Seoul National University" not in pf
    tcu_str = " ".join(preview["target_context_used"])
    assert "Seoul National University" in tcu_str


def test_blind_hiring_identity_competency_not_in_draft_llm_path(client, monkeypatch):
    """Identity-bearing competency omitted from answer_draft (LLM); target_context_used keeps it."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    def fake_llm(output_type, fact_ledger, target_context, **kwargs):
        return {
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing problem solving",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            }
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", fake_llm)
    payload = _answer_payload(competency=_IDENTITY_COMPETENCY, blind_hiring=True)
    rv = client.post("/api/studio/application-preview", json=payload)
    assert rv.status_code == 200
    preview = rv.get_json()["preview"]
    assert preview["refine_source"] == "llm"
    assert "Seoul National University" not in preview["answer_draft"]
    for pf in preview["personal_facts"]:
        assert "Seoul National University" not in pf
    tcu_str = " ".join(preview["target_context_used"])
    assert "Seoul National University" in tcu_str


# ── ISSUE-11: provider-payload opaque-ID regression ───────────────────────────


def test_blind_hiring_opaque_card_id_in_provider_payload(opaque_id_client, monkeypatch):
    """Canonical card ID absent from fact_ledger sent to provider; opaque ref C1 present."""
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    captured: list[list[dict]] = []

    def capturing_llm(output_type, fact_ledger, target_context, **kwargs):
        captured.append(list(fact_ledger))
        return {
            "advisory": {
                "selected_fact_ids": [fact_ledger[0]["id"]] if fact_ledger else [],
                "question_intent": "Assessing technical depth",
                "competency_target": "",
                "missing_info": [],
                "ai_guidance": [],
            }
        }

    monkeypatch.setattr(llm_mod, "application_preview_llm", capturing_llm)
    rv = opaque_id_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["alumni-program-2024"],
            "target_context": {
                "question": "Describe a technical challenge.",
                "blind_hiring": True,
            },
        },
    )
    assert rv.status_code == 200
    assert captured, "LLM was not called"
    provider_ledger = captured[0]
    raw_ids = [e["source_card_id"] for e in provider_ledger]
    assert "alumni-program-2024" not in raw_ids
    assert any(sid == "C1" for sid in raw_ids)
    preview = rv.get_json()["preview"]
    for entry in preview["fact_ledger"]:
        assert entry["source_card_id"] != "alumni-program-2024"
    import json as _json

    assert "alumni-program-2024" not in _json.dumps(preview)


# ── ISSUE-12: live-card selector API shape regression ─────────────────────────


def test_api_cards_returns_array_with_live_card(client):
    """/api/cards returns a JSON array; live cards are present for the selector to consume."""
    rv = client.get("/api/cards")
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list), "expected a JSON array, not an object"
    live = [c for c in data if c.get("status") == "live"]
    assert len(live) >= 1, "expected at least one live card in the default fixture"
    card = live[0]
    assert "id" in card
    assert "title" in card
    assert "status" in card


def test_api_cards_live_card_usable_in_application_preview(client, monkeypatch):
    """A live card from /api/cards can be submitted to the application-preview endpoint."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    cards_rv = client.get("/api/cards")
    live = [c for c in cards_rv.get_json() if c.get("status") == "live"]
    assert live, "precondition: at least one live card must be available"
    card_id = live[0]["id"]
    rv = client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": [card_id],
            "target_context": {"question": "Describe a technical challenge you solved."},
        },
    )
    assert rv.status_code == 200
    assert rv.get_json()["ok"] is True


def test_studio_js_uses_array_guard(client):
    """loadAppCards() uses Array.isArray guard, status=live filter, and empty-state text."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"Array.isArray(data)" in rv.data
    assert b'status === "live"' in rv.data
    assert b"No live cards found" in rv.data


def test_studio_js_no_data_cards_access(client):
    """studio.js must not read data.cards — that property does not exist on the array response."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"data.cards" not in rv.data
