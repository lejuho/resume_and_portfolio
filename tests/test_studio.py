"""Tests for the Career Studio routes and API."""

from __future__ import annotations

import textwrap

import pytest

import scripts.dashboard as dash_mod
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

RAW_RICH = (
    "Rebuilt the auth service at NinjaLabs 2024-03\n"
    "Reduced latency by 40% and cut costs 2x\n"
    "https://github.com/example/auth-service\n"
    "Added screenshot of the new dashboard."
)

RAW_BARE = "Worked on some stuff last year."


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


# ─── GET /studio ──────────────────────────────────────────────────────────────


def test_studio_returns_200(client):
    rv = client.get("/studio")
    assert rv.status_code == 200


def test_studio_has_core_hooks(client):
    rv = client.get("/studio")
    assert b"st-raw" in rv.data
    assert b"st-intent" in rv.data
    assert b"st-preview" in rv.data
    assert b"st-save-btn" in rv.data
    assert b"/dashboard" in rv.data


# ─── GET /dashboard alias ─────────────────────────────────────────────────────


def test_dashboard_alias_returns_200(client):
    rv = client.get("/dashboard")
    assert rv.status_code == 200
    assert b"sample-card" in rv.data


# ─── POST /api/studio/refine ──────────────────────────────────────────────────


def test_refine_rejects_empty_raw_text(client):
    rv = client.post("/api/studio/refine", json={"raw_text": "", "intent": "both"})
    assert rv.status_code == 400


def test_refine_rejects_whitespace_only(client):
    rv = client.post("/api/studio/refine", json={"raw_text": "   \n\t  ", "intent": "resume"})
    assert rv.status_code == 400


def test_refine_invalid_intent(client):
    rv = client.post("/api/studio/refine", json={"raw_text": "some text", "intent": "linkedin"})
    assert rv.status_code == 400


def test_refine_resume_intent_returns_bullet(client):
    rv = client.post("/api/studio/refine", json={"raw_text": RAW_RICH, "intent": "resume"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert "resume_bullet" in body["draft"]
    assert "portfolio_body" not in body["draft"]


def test_refine_portfolio_intent_returns_blocks(client):
    rv = client.post("/api/studio/refine", json={"raw_text": RAW_RICH, "intent": "portfolio"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert "portfolio_body" in body["draft"]
    assert "## Problem" in body["draft"]["portfolio_body"]
    assert "## Outcome" in body["draft"]["portfolio_body"]
    assert "resume_bullet" not in body["draft"]


def test_refine_both_intent_returns_both(client):
    rv = client.post("/api/studio/refine", json={"raw_text": RAW_RICH, "intent": "both"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["ok"] is True
    assert "resume_bullet" in body["draft"]
    assert "portfolio_body" in body["draft"]


def test_refine_returns_missing_info_structured(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post("/api/studio/refine", json={"raw_text": RAW_BARE, "intent": "both"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert isinstance(body["missing_info"], list)
    codes = [m["code"] for m in body["missing_info"]]
    assert "MISSING_PERIOD" in codes
    assert "MISSING_METRICS" in codes
    for item in body["missing_info"]:
        assert "code" in item and "message" in item


def test_refine_is_deterministic(client):
    payload = {"raw_text": RAW_RICH, "intent": "both"}
    r1 = client.post("/api/studio/refine", json=payload).get_json()
    r2 = client.post("/api/studio/refine", json=payload).get_json()
    assert r1["draft"] == r2["draft"]
    assert r1["missing_info"] == r2["missing_info"]


# ─── POST /api/studio/save ────────────────────────────────────────────────────


def _get_draft(client, raw=RAW_RICH, intent="both"):
    rv = client.post("/api/studio/refine", json={"raw_text": raw, "intent": intent})
    return rv.get_json()["draft"]


def test_studio_save_creates_draft_card(client, repo):
    draft = _get_draft(client)
    rv = client.post("/api/studio/save", json={"draft": draft})
    assert rv.status_code == 201
    body = rv.get_json()
    assert body["ok"] is True
    assert "path" in body
    saved = repo / body["path"]
    assert saved.exists()


def test_studio_save_card_passes_validation(client, repo):
    from scripts.card import CardRepo

    draft = _get_draft(client)
    rv = client.post("/api/studio/save", json={"draft": draft})
    assert rv.status_code == 201
    saved_path = repo / rv.get_json()["path"]
    repo_obj = CardRepo(repo)
    ids = [c.id for c in repo_obj.cards]
    assert draft["id"] in ids
    assert not any("studio" in e for e in repo_obj.errors)
    _ = saved_path  # exists check already done above


def test_studio_save_duplicate_id_rejected(client, repo):
    draft = _get_draft(client)
    r1 = client.post("/api/studio/save", json={"draft": draft})
    assert r1.status_code == 201
    r2 = client.post("/api/studio/save", json={"draft": draft})
    assert r2.status_code == 409
    assert "already exists" in r2.get_json()["error"]


def test_studio_save_does_not_store_raw_input(client, repo):
    draft = _get_draft(client)
    # Pass raw_text alongside draft — save endpoint must ignore it entirely
    rv = client.post("/api/studio/save", json={"draft": draft, "raw_text": "SENSITIVE_RAW_TEXT"})
    assert rv.status_code == 201
    saved = (repo / rv.get_json()["path"]).read_text(encoding="utf-8")
    assert "SENSITIVE_RAW_TEXT" not in saved


def test_studio_save_does_not_persist_raw_body(client, repo, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    raw = "My Awesome Project 2024-01\nSECRET_BODY_PHRASE private rough notes must never be stored"
    rv_refine = client.post("/api/studio/refine", json={"raw_text": raw, "intent": "both"})
    assert rv_refine.status_code == 200
    draft = rv_refine.get_json()["draft"]
    rv_save = client.post("/api/studio/save", json={"draft": draft})
    assert rv_save.status_code == 201
    saved = (repo / rv_save.get_json()["path"]).read_text(encoding="utf-8")
    assert "SECRET_BODY_PHRASE" not in saved


# ─── Cycle 12: editable preview hooks ────────────────────────────────────────

_EDIT_DRAFT = {
    "id": "edit-draft-card",
    "title": "Edit Draft Card",
    "type": "project",
    "period_start": "2024-03-01",
    "status": "draft",
    "visibility": "public",
    "summary": "Original summary",
    "tags": {"domain": [], "skill": [], "audience": []},
    "metrics": [],
    "evidence": [],
    "visuals": [],
    "links": [],
    "related": [],
}


def test_studio_has_editable_preview_hooks(client):
    rv = client.get("/studio")
    assert b"st-edit-title" in rv.data
    assert b"st-edit-summary" in rv.data
    assert b"st-edit-resume-bullet" in rv.data
    assert b"st-edit-portfolio-body" in rv.data
    assert b"st-edit-fields" in rv.data


def test_studio_has_post_save_action_hooks(client):
    rv = client.get("/studio")
    assert b"st-post-save" in rv.data
    assert b"st-action-dashboard" in rv.data
    assert b"st-action-build-resume" in rv.data
    assert b"st-action-build-portfolio" in rv.data
    assert b"st-build-output" in rv.data


def test_studio_has_source_chips_hook(client):
    rv = client.get("/studio")
    assert b"st-source-chips" in rv.data


def test_edited_summary_persists(client, repo):
    draft = {**_EDIT_DRAFT, "summary": "EDITED_SUMMARY_VALUE"}
    rv = client.post("/api/studio/save", json={"draft": draft})
    assert rv.status_code == 201
    saved = (repo / rv.get_json()["path"]).read_text(encoding="utf-8")
    assert "EDITED_SUMMARY_VALUE" in saved


def test_edited_portfolio_body_persists(client, repo):
    draft = {
        **_EDIT_DRAFT,
        "id": "edit-body-card",
        "portfolio_body": "## Problem\n\nEDITED_BODY_CONTENT\n",
    }
    rv = client.post("/api/studio/save", json={"draft": draft})
    assert rv.status_code == 201
    saved = (repo / rv.get_json()["path"]).read_text(encoding="utf-8")
    assert "EDITED_BODY_CONTENT" in saved


def test_edited_resume_bullet_persists_as_narrative(client, repo):
    draft = {**_EDIT_DRAFT, "id": "edit-bullet-card", "resume_bullet": "EDITED_BULLET_VALUE"}
    rv = client.post("/api/studio/save", json={"draft": draft})
    assert rv.status_code == 201
    saved = (repo / rv.get_json()["path"]).read_text(encoding="utf-8")
    assert "EDITED_BULLET_VALUE" in saved


def test_missing_info_code_message_structure(client):
    rv = client.post("/api/studio/refine", json={"raw_text": RAW_BARE, "intent": "both"})
    assert rv.status_code == 200
    for item in rv.get_json()["missing_info"]:
        assert "code" in item
        assert "message" in item
        assert item["code"].isupper()


def test_studio_js_has_mi_code_message_hooks(client):
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"mi-code" in rv.data
    assert b"mi-message" in rv.data


def test_studio_html_has_chip_type_styles(client):
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"chip-date" in rv.data
    assert b"chip-metric" in rv.data
    assert b"chip-link" in rv.data
    assert b"chip-visual" in rv.data


def test_save_response_includes_id_for_build(client, repo):
    rv = client.post("/api/studio/save", json={"draft": _EDIT_DRAFT})
    assert rv.status_code == 201
    body = rv.get_json()
    assert "id" in body
    assert body["id"]  # non-empty — suitable for selected_ids in /api/build


def test_studio_js_calls_api_build_with_selected_ids(client):
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"/api/build" in rv.data
    assert b"selected_ids" in rv.data


def test_studio_js_resets_save_btn_on_render(client):
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    # renderPreview must restore the save button for a second refine→save flow
    assert b"disabled = false" in rv.data
    assert b'"Save as draft card"' in rv.data


# ─── Cycle 13: UX language ────────────────────────────────────────────────────


def test_studio_has_career_memory_language(client):
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"Career Memory" in rv.data
    # one-line flow description guiding the user through the studio pipeline
    assert b"refined draft" in rv.data
    assert b"generated outputs" in rv.data


def test_studio_save_success_has_draft_guidance(client):
    rv = client.get("/studio")
    assert rv.status_code == 200
    # post-save panel explains the Draft status and how to promote to Live
    assert b"st-post-save" in rv.data
    assert b"Mark it Live in Dashboard" in rv.data
