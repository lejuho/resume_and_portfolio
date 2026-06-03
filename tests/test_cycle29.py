"""Cycle 29: Workspace dark polish tests.

Covers: dark-mode media query and token overrides, card hover/selected/focus-visible
states, design-system regression (no uppercase / font-weight 600/700), workspace.js
array-contract regression, and route regression.
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


# ── Helpers ───────────────────────────────────────────────────────────────────


def _dark_block(html_bytes: bytes) -> str:
    """Return source text from the dark media query onward."""
    src = html_bytes.decode("utf-8")
    marker = "@media (prefers-color-scheme: dark)"
    return src[src.index(marker) :]


# ── A: Dark media query presence ─────────────────────────────────────────────


def test_workspace_html_has_dark_media_query(client):
    """workspace.html includes the dark mode media query."""
    rv = client.get("/workspace")
    assert b"@media (prefers-color-scheme: dark)" in rv.data


def test_workspace_html_has_theme_toggle_button(client):
    """workspace.html exposes a stable manual theme toggle."""
    rv = client.get("/workspace")
    assert b'id="ws-theme-toggle"' in rv.data
    assert b"toggleWorkspaceTheme()" in rv.data


def test_workspace_html_has_manual_dark_selector(client):
    """Manual dark mode is available without relying only on OS preference."""
    rv = client.get("/workspace")
    assert b':root[data-ws-theme="dark"]' in rv.data


# ── B: Dark token overrides ───────────────────────────────────────────────────


def test_workspace_html_dark_overrides_ws_bg(client):
    """Dark block overrides --ws-bg."""
    dark = _dark_block(client.get("/workspace").data)
    assert "--ws-bg" in dark


def test_workspace_html_dark_overrides_ws_surface(client):
    """Dark block overrides --ws-surface."""
    dark = _dark_block(client.get("/workspace").data)
    assert "--ws-surface" in dark


def test_workspace_html_dark_overrides_ws_text(client):
    """Dark block overrides --ws-text."""
    dark = _dark_block(client.get("/workspace").data)
    assert "--ws-text" in dark


def test_workspace_html_dark_overrides_ws_border(client):
    """Dark block overrides --ws-border."""
    dark = _dark_block(client.get("/workspace").data)
    assert "--ws-border" in dark


def test_workspace_html_dark_overrides_ws_accent(client):
    """Dark block overrides --ws-accent."""
    dark = _dark_block(client.get("/workspace").data)
    assert "--ws-accent" in dark


# ── C: Card interaction states ────────────────────────────────────────────────


def test_workspace_html_card_hover_state_exists(client):
    """workspace.html defines a card hover state."""
    rv = client.get("/workspace")
    assert b"ws-card-item:hover" in rv.data


def test_workspace_html_card_selected_state_exists(client):
    """workspace.html defines a card selected state (Cycle 28 preserved)."""
    rv = client.get("/workspace")
    assert b"ws-card-selected" in rv.data


def test_workspace_html_card_focus_visible_state_exists(client):
    """workspace.html defines a focus-visible state for card checkboxes."""
    rv = client.get("/workspace")
    assert b"focus-visible" in rv.data


# ── D: Design-system regression ──────────────────────────────────────────────


def test_workspace_html_no_uppercase_transform(client):
    """workspace.html still has no text-transform: uppercase."""
    rv = client.get("/workspace")
    assert b"text-transform: uppercase" not in rv.data


def test_workspace_html_no_font_weight_600(client):
    """workspace.html still has no font-weight: 600."""
    rv = client.get("/workspace")
    assert b"font-weight: 600" not in rv.data


def test_workspace_html_no_font_weight_700(client):
    """workspace.html still has no font-weight: 700."""
    rv = client.get("/workspace")
    assert b"font-weight: 700" not in rv.data


# ── E: workspace.js contract regression ──────────────────────────────────────


def test_workspace_js_array_is_array_preserved(client):
    """workspace.js still guards /api/cards with Array.isArray after Cycle 29."""
    rv = client.get("/static/workspace.js")
    assert b"Array.isArray(data)" in rv.data


def test_workspace_js_live_filter_preserved(client):
    """workspace.js still filters status === 'live' after Cycle 29."""
    rv = client.get("/static/workspace.js")
    assert b'status === "live"' in rv.data


def test_workspace_js_no_data_cards_preserved(client):
    """workspace.js still does not read data.cards after Cycle 29."""
    rv = client.get("/static/workspace.js")
    assert b"data.cards" not in rv.data


def test_workspace_js_theme_toggle_helper_exists(client):
    """workspace.js defines the manual theme toggle helper."""
    rv = client.get("/static/workspace.js")
    assert b"function toggleWorkspaceTheme()" in rv.data
    assert b"window.toggleWorkspaceTheme = toggleWorkspaceTheme" in rv.data


def test_workspace_js_theme_uses_local_storage(client):
    """workspace.js stores only browser-local theme preference."""
    rv = client.get("/static/workspace.js")
    assert b"localStorage.setItem" in rv.data
    assert b"localStorage.getItem" in rv.data
    assert b"workspace-theme" in rv.data


# ── F: Route regression ───────────────────────────────────────────────────────


def test_workspace_route_returns_200(client):
    """/workspace returns HTTP 200 after Cycle 29 changes."""
    assert client.get("/workspace").status_code == 200


def test_studio_route_still_returns_200(client):
    """/studio is unaffected by Cycle 29 workspace changes."""
    assert client.get("/studio").status_code == 200
