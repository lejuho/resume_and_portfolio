"""Cycle 30: Workspace evidence fit signals tests.

Covers: fit/tokenization helper presence, coverage update wiring, target listener
wiring, matched terms hook, preview payload regression, API contract regression,
and route regression.
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


# ── A: Fit helper source contracts ────────────────────────────────────────────


def test_workspace_js_has_tokenize_helper(client):
    """workspace.js defines a _wsTokenize tokenization helper."""
    rv = client.get("/static/workspace.js")
    assert b"function _wsTokenize(" in rv.data


def test_workspace_js_has_card_tokens_helper(client):
    """workspace.js defines a _wsCardTokens helper to extract card text."""
    rv = client.get("/static/workspace.js")
    assert b"function _wsCardTokens(" in rv.data


def test_workspace_js_has_update_coverage_function(client):
    """workspace.js defines _wsUpdateCoverage to refresh the coverage panel."""
    rv = client.get("/static/workspace.js")
    assert b"function _wsUpdateCoverage(" in rv.data


def test_workspace_js_stop_words_defined(client):
    """workspace.js defines a stop-word set (_WS_STOP) to suppress noise."""
    rv = client.get("/static/workspace.js")
    assert b"_WS_STOP" in rv.data


# ── B: Target listener wiring ─────────────────────────────────────────────────


def test_workspace_js_wires_target_listeners(client):
    """workspace.js wires input listeners to target fields via _wsWireTargetListeners."""
    rv = client.get("/static/workspace.js")
    assert b"_wsWireTargetListeners" in rv.data
    assert b'addEventListener("input"' in rv.data


def test_workspace_js_target_listeners_cover_role_field(client):
    """_wsWireTargetListeners includes the ws-role target field."""
    rv = client.get("/static/workspace.js")
    src = rv.data.decode("utf-8")
    wire_start = src.index("_wsWireTargetListeners")
    assert "ws-role" in src[wire_start : wire_start + 500]


def test_workspace_js_target_listeners_cover_question_field(client):
    """_wsWireTargetListeners includes the ws-question target field."""
    rv = client.get("/static/workspace.js")
    src = rv.data.decode("utf-8")
    wire_start = src.index("_wsWireTargetListeners")
    assert "ws-question" in src[wire_start : wire_start + 500]


# ── C: Card toggle refreshes coverage ────────────────────────────────────────


def test_workspace_js_card_toggle_calls_update_coverage(client):
    """_wsOnCardToggle calls _wsUpdateCoverage after toggling selected class."""
    rv = client.get("/static/workspace.js")
    src = rv.data.decode("utf-8")
    toggle_start = src.index("function _wsOnCardToggle(")
    toggle_end = src.index("\n  }", toggle_start) + 4
    assert "_wsUpdateCoverage" in src[toggle_start:toggle_end]


# ── D: Coverage panel hooks ───────────────────────────────────────────────────


def test_workspace_html_has_coverage_terms_hook(client):
    """workspace.html exposes a ws-coverage-terms element for matched terms."""
    rv = client.get("/workspace")
    assert b"ws-coverage-terms" in rv.data


def test_workspace_html_coverage_value_hook_exists(client):
    """ws-coverage-value hook still exists in workspace.html (Cycle 28 preserved)."""
    rv = client.get("/workspace")
    assert b"ws-coverage-value" in rv.data


# ── E: Card text containment and disclosure ──────────────────────────────────


def test_workspace_html_card_content_constrains_width(client):
    """Card content uses min-width zero and safe wrapping inside the left pane."""
    rv = client.get("/workspace")
    assert b".ws-card-content" in rv.data
    assert b"min-width: 0" in rv.data
    assert b"overflow-wrap: anywhere" in rv.data


def test_workspace_html_card_context_uses_line_clamp(client):
    """Long card summaries are clamped until expanded."""
    rv = client.get("/workspace")
    assert b"-webkit-line-clamp: 2" in rv.data
    assert b"ws-card-context-expanded" in rv.data


def test_workspace_js_renders_visible_disclosure_control(client):
    """Card markup includes a descriptive disclosure control outside the label."""
    rv = client.get("/static/workspace.js")
    assert b"ws-card-content" in rv.data
    assert b"ws-card-more" in rv.data
    assert b"_wsToggleCardDetails(event, this)" in rv.data
    assert b"Show full summary" in rv.data
    assert b"Collapse summary" in rv.data
    assert b"aria-controls" in rv.data


def test_workspace_html_disclosure_is_full_width_target(client):
    """Disclosure bar is a visible, comfortably sized full-width target."""
    rv = client.get("/workspace")
    assert b"width: 100%" in rv.data
    assert b"min-height: 32px" in rv.data
    assert b"justify-content: center" in rv.data


def test_workspace_js_disclosure_stops_selection_click(client):
    """Disclosure helper stops propagation instead of toggling card selection."""
    rv = client.get("/static/workspace.js")
    src = rv.data.decode("utf-8")
    start = src.index("function _wsToggleCardDetails(")
    end = src.index("\n  }", start) + 4
    helper = src[start:end]
    assert "event.stopPropagation()" in helper
    assert "_wsOnCardToggle" not in helper


def test_workspace_js_only_shows_more_when_truncated(client):
    """More is revealed only when rendered summary height exceeds the clamp."""
    rv = client.get("/static/workspace.js")
    assert b"contextEl.scrollHeight > contextEl.clientHeight" in rv.data
    assert b"moreButton.hidden = false" in rv.data


# ── F: Preview payload regression ────────────────────────────────────────────


def test_workspace_js_preview_posts_to_application_preview(client):
    """generateWorkspacePreview still posts to /api/studio/application-preview."""
    rv = client.get("/static/workspace.js")
    assert b"/api/studio/application-preview" in rv.data


def test_workspace_js_preview_includes_output_type(client):
    """generateWorkspacePreview request body includes output_type."""
    rv = client.get("/static/workspace.js")
    assert b"output_type" in rv.data


def test_workspace_js_preview_includes_target_context(client):
    """generateWorkspacePreview request body includes target_context."""
    rv = client.get("/static/workspace.js")
    assert b"target_context" in rv.data


def test_workspace_js_preview_includes_card_ids(client):
    """generateWorkspacePreview request body includes card_ids."""
    rv = client.get("/static/workspace.js")
    assert b"card_ids" in rv.data


# ── G: API contract regression ────────────────────────────────────────────────


def test_workspace_js_array_is_array_preserved(client):
    """Array.isArray guard still present after Cycle 30 changes."""
    rv = client.get("/static/workspace.js")
    assert b"Array.isArray(data)" in rv.data


def test_workspace_js_live_filter_preserved(client):
    """Live status filter still present after Cycle 30 changes."""
    rv = client.get("/static/workspace.js")
    assert b'status === "live"' in rv.data


def test_workspace_js_no_data_cards_preserved(client):
    """workspace.js still does not read data.cards after Cycle 30 changes."""
    rv = client.get("/static/workspace.js")
    assert b"data.cards" not in rv.data


# ── H: Route regression ───────────────────────────────────────────────────────


def test_workspace_route_returns_200(client):
    """/workspace returns HTTP 200 after Cycle 30 changes."""
    assert client.get("/workspace").status_code == 200


def test_studio_route_still_returns_200(client):
    """/studio is unaffected by Cycle 30 workspace changes."""
    assert client.get("/studio").status_code == 200
