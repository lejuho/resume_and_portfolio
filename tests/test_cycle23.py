"""Cycle 23: Application Writing UX polish tests.

Covers selector card metadata, extended empty-state message, copy explanation,
copy button label, actionable blind-hiring 422 message, and summary truncation.
No new tooling; existing Flask test-client byte-substring and API-assertion style.
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

_IDENTITY_MDX = """\
---
id: snu-project
title: Seoul National University Research Project
type: project
period:
  start: 2023-09-01
status: live
summary: "Graduate research at Seoul National University."
---
"""


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-03-auth-service.mdx").write_text(_LIVE_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def client(repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def identity_repo(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2023-09-snu-project.mdx").write_text(_IDENTITY_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def identity_client(identity_repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Selector metadata ─────────────────────────────────────────────────────────


def test_studio_js_selector_renders_card_metadata(client):
    """loadAppCards renders card-title, card-summary, and card-counts spans from API fields."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200
    assert b"card-title" in rv.data
    assert b"card-summary" in rv.data
    assert b"card-counts" in rv.data
    assert b"metrics_count" in rv.data
    assert b"evidence_count" in rv.data


def test_studio_js_selector_summary_truncation(client):
    """loadAppCards trims summary to 80 chars with an ellipsis."""
    rv = client.get("/static/studio.js")
    assert b"slice(0, 80)" in rv.data
    assert "…".encode() in rv.data  # ellipsis character


def test_studio_js_selector_empty_metric_fallback(client):
    """loadAppCards shows 'no metrics or evidence' when counts are both zero."""
    rv = client.get("/static/studio.js")
    assert b"no metrics or evidence" in rv.data


# ── Empty-state message ───────────────────────────────────────────────────────


def test_studio_js_empty_state_mentions_validation_errors(client):
    """Empty-state message mentions validation errors as a possible cause."""
    rv = client.get("/static/studio.js")
    assert b"validation errors" in rv.data
    assert b"No live cards found" in rv.data


# ── Copy explanation ──────────────────────────────────────────────────────────


def test_studio_html_copy_note_present(client):
    """HTML contains a copy explanation note making clear only Verified draft is copied."""
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"st-app-copy-note" in rv.data
    assert b"Only the Verified draft text" in rv.data
    assert b"AI Guidance is not included" in rv.data


def test_studio_html_copy_button_label_updated(client):
    """Copy button initial label and post-copy reset string both name Verified draft."""
    html_rv = client.get("/studio")
    assert b"Copy Verified draft to clipboard" in html_rv.data
    js_rv = client.get("/static/studio.js")
    assert b"Copy Verified draft to clipboard" in js_rv.data
    assert b'"Copy to clipboard"' not in js_rv.data


# ── Blind-hiring 422 actionable message ───────────────────────────────────────


def test_blind_hiring_422_actionable_message(identity_client, monkeypatch):
    """Blind-hiring all-redacted 422 error explains the corrective action."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = identity_client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["snu-project"],
            "target_context": {"question": "Describe a challenge.", "blind_hiring": True},
        },
    )
    assert rv.status_code == 422
    error = rv.get_json()["error"]
    assert "blind-hiring policy" in error
    assert "choose cards" in error or "remove those details" in error
