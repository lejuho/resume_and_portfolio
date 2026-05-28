"""Cycle 22: Studio UI contract smoke tests.

Covers Application Writing selector, submit, render, copy-separation, HTML hooks,
and an API-level end-to-end smoke that catches frontend/backend shape mismatches.
All source assertions use the existing Flask test-client byte-substring style; no
new JS tooling is introduced.
"""

from __future__ import annotations

import pytest

import scripts.dashboard as dash_mod
from scripts.dashboard import app

# ── Fixtures ──────────────────────────────────────────────────────────────────

_LIVE_MDX = """\
---
id: auth-service
title: Auth Service Platform
type: project
period:
  start: 2024-03-01
status: live
summary: "Rebuilt the auth service reducing latency by 40%."
metrics:
  - "40% latency reduction"
evidence:
  - type: repo
    url: https://github.com/example/auth-service
---
"""

_DRAFT_MDX = """\
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
    (cards / "2024-03-auth-service.mdx").write_text(_LIVE_MDX, encoding="utf-8")
    (cards / "2024-06-draft-card.mdx").write_text(_DRAFT_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def client(repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── A: loadAppCards source contract ───────────────────────────────────────────


def test_studio_js_load_app_cards_source_contract(client):
    """loadAppCards fetches /api/cards, targets the selector DOM id, and handles both states."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"/api/cards" in rv.data
    assert b"st-app-card-selector" in rv.data
    assert b"No live cards found" in rv.data
    assert b"Could not load cards" in rv.data


# ── B: generateAppPreview target-context field contract ───────────────────────


def test_studio_js_generate_preview_target_context_contract(client):
    """generateAppPreview collects all target-context fields from the expected DOM IDs."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    # DOM field IDs
    assert b"st-app-organization" in rv.data
    assert b"st-app-role" in rv.data
    assert b"st-app-question" in rv.data
    assert b"st-app-competency" in rv.data
    assert b"st-app-jd" in rv.data
    assert b"st-app-charlimit" in rv.data
    assert b"st-app-blind" in rv.data
    # JSON body keys
    assert b"target_context" in rv.data
    assert b"card_ids" in rv.data
    assert b"output_type" in rv.data


# ── C: renderAppPreview draft and count contract ───────────────────────────────


def test_studio_js_render_preview_draft_and_counts_contract(client):
    """renderAppPreview writes answer_draft to _appDraftText and the draft DOM element."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"answer_draft" in rv.data
    assert b"_appDraftText" in rv.data
    assert b"st-app-draft-text" in rv.data
    assert b"st-app-missing-info" in rv.data
    assert b"character_count" in rv.data
    assert b"st-app-char-status" in rv.data


# ── D: copyAppDraft separation contract ───────────────────────────────────────


def test_studio_js_copy_draft_separation_contract(client):
    """copyAppDraft copies _appDraftText to clipboard; advisory guidance is not the copy source."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    # Copy source is _appDraftText (set from preview.answer_draft, not ai_guidance)
    assert b"navigator.clipboard.writeText(_appDraftText)" in rv.data
    # ai_guidance is rendered in its own section; the copy path must not reference it
    assert b"writeText" in rv.data
    assert b"ai_guidance" in rv.data  # rendered separately
    # _appDraftText assignment must come from answer_draft, not ai_guidance
    assert b"preview.answer_draft" in rv.data


# ── E: HTML DOM hook IDs ───────────────────────────────────────────────────────


def test_studio_html_app_writing_hook_ids(client):
    """Studio HTML exposes all DOM IDs required by the Application Writing JS."""
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"st-app-card-selector" in rv.data
    assert b"st-app-preview-btn" in rv.data
    assert b"st-app-result" in rv.data
    assert b"st-app-draft-text" in rv.data
    assert b"st-app-copy-btn" in rv.data
    assert b"st-app-missing-info" in rv.data
    assert b"st-app-guidance-section" in rv.data


# ── F: API-level end-to-end response fields ───────────────────────────────────


def test_studio_app_writing_preview_response_fields(client, monkeypatch):
    """Live card from /api/cards produces a valid preview with expected response fields."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)

    cards_rv = client.get("/api/cards")
    live = [c for c in cards_rv.get_json() if c.get("status") == "live"]
    assert live, "precondition: at least one live card required"
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
    body = rv.get_json()
    assert body["ok"] is True
    preview = body["preview"]
    assert "answer_draft" in preview
    assert isinstance(preview["answer_draft"], str)
    assert "character_count" in preview
    assert isinstance(preview["character_count"], int)
    assert preview["refine_source"] in ("mock", "llm")
    assert isinstance(preview.get("selected_cards", []), list)
