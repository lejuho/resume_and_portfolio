"""Cycle 27: /workspace route shell tests.

Covers: route existence and coexistence with /studio, HTML pane landmarks/hook ids,
workspace.js source contracts (Array.isArray, live filter, no data.cards, no studio.js
import), and no new mutation route.
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


# ── A: Route coexistence ──────────────────────────────────────────────────────


def test_workspace_route_returns_200(client):
    """/workspace returns HTTP 200."""
    rv = client.get("/workspace")
    assert rv.status_code == 200


def test_studio_route_still_returns_200(client):
    """/studio is unaffected by workspace addition."""
    rv = client.get("/studio")
    assert rv.status_code == 200


def test_workspace_serves_workspace_js(client):
    """/workspace HTML includes /static/workspace.js."""
    rv = client.get("/workspace")
    assert b"/static/workspace.js" in rv.data


def test_studio_serves_studio_js(client):
    """/studio HTML still includes /static/studio.js."""
    rv = client.get("/studio")
    assert b"/static/studio.js" in rv.data


def test_workspace_js_route_returns_200(client):
    """/static/workspace.js is served."""
    rv = client.get("/static/workspace.js")
    assert rv.status_code == 200


def test_studio_js_route_still_returns_200(client):
    """/static/studio.js is still served."""
    rv = client.get("/static/studio.js")
    assert rv.status_code == 200


# ── B: Dashboard link ─────────────────────────────────────────────────────────


def test_dashboard_still_has_studio_link(client):
    """Dashboard retains the /studio link."""
    rv = client.get("/dashboard")
    assert b'href="/studio"' in rv.data


def test_dashboard_has_workspace_link(client):
    """Dashboard has a /workspace link alongside /studio."""
    rv = client.get("/dashboard")
    assert b'href="/workspace"' in rv.data


# ── C: Workspace HTML pane landmarks and hook ids ─────────────────────────────


def test_workspace_has_left_pane(client):
    """Workspace has a left evidence/card pane."""
    rv = client.get("/workspace")
    assert b"ws-left-pane" in rv.data
    assert b"ws-card-list" in rv.data


def test_workspace_has_right_pane(client):
    """Workspace has a right target/output pane."""
    rv = client.get("/workspace")
    assert b"ws-right-pane" in rv.data


def test_workspace_has_target_inputs(client):
    """Workspace exposes target context input hooks."""
    rv = client.get("/workspace")
    assert b"ws-organization" in rv.data
    assert b"ws-role" in rv.data
    assert b"ws-question" in rv.data
    assert b"ws-competency" in rv.data


def test_workspace_has_output_type_control(client):
    """Workspace has output type radio controls."""
    rv = client.get("/workspace")
    assert b"ws_output_type" in rv.data
    assert b"application_answer" in rv.data
    assert b"cover_letter" in rv.data


def test_workspace_has_coverage_panel(client):
    """Workspace exposes a coverage/match placeholder panel."""
    rv = client.get("/workspace")
    assert b"ws-coverage-panel" in rv.data
    assert b"ws-coverage-value" in rv.data


def test_workspace_has_generate_and_preview_hooks(client):
    """Workspace exposes generate button and preview output hooks."""
    rv = client.get("/workspace")
    assert b"ws-generate-btn" in rv.data
    assert b"ws-preview-out" in rv.data


# ── D: workspace.js source contracts ─────────────────────────────────────────


def test_workspace_js_uses_array_is_array(client):
    """workspace.js consumes /api/cards via Array.isArray guard."""
    rv = client.get("/static/workspace.js")
    assert b"Array.isArray(data)" in rv.data


def test_workspace_js_filters_live_status(client):
    """workspace.js filters cards to status === 'live'."""
    rv = client.get("/static/workspace.js")
    assert b'status === "live"' in rv.data


def test_workspace_js_fetches_api_cards(client):
    """workspace.js fetches /api/cards."""
    rv = client.get("/static/workspace.js")
    assert b"/api/cards" in rv.data


def test_workspace_js_does_not_read_data_cards(client):
    """workspace.js does not read data.cards (bare array contract)."""
    rv = client.get("/static/workspace.js")
    assert b"data.cards" not in rv.data


def test_workspace_js_does_not_import_studio_js(client):
    """workspace.js has no reference to studio.js."""
    rv = client.get("/static/workspace.js")
    assert b"studio.js" not in rv.data


def test_workspace_js_does_not_reference_st_prefix_ids(client):
    """workspace.js uses ws- ids, not st- ids from studio."""
    rv = client.get("/static/workspace.js")
    src = rv.data.decode("utf-8")
    # st-app-* ids must not appear; st-app- prefix is studio's namespace
    assert "st-app-" not in src


# ── E: No new mutation route ──────────────────────────────────────────────────


def test_workspace_api_mutation_route_absent(client):
    """No /api/workspace mutation route is added."""
    rv = client.post("/api/workspace", json={})
    assert rv.status_code == 404


def test_workspace_does_not_create_card_file(client, repo):
    """Visiting /workspace does not create card files."""
    import os

    cards_dir = repo / "cards"
    before = set(os.listdir(cards_dir))
    client.get("/workspace")
    after = set(os.listdir(cards_dir))
    assert after == before


# ── F: Sentence-case design direction ────────────────────────────────────────


def test_workspace_html_no_uppercase_transform(client):
    """workspace.html contains no text-transform: uppercase (sentence-case direction)."""
    rv = client.get("/workspace")
    assert b"text-transform: uppercase" not in rv.data
