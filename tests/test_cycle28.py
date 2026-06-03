"""Cycle 28: Workspace design token alignment tests.

Covers: :root token definitions, font-weight compliance, card markup class hooks
in workspace.js, selected-state toggle, and Cycle 27 source contract preservation.
"""

from __future__ import annotations

import os

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


# ── A: Design token definitions ───────────────────────────────────────────────


def test_workspace_html_has_token_accent(client):
    """workspace.html defines --ws-accent CSS custom property."""
    rv = client.get("/workspace")
    assert b"--ws-accent" in rv.data


def test_workspace_html_has_token_surface(client):
    """workspace.html defines --ws-surface CSS custom property."""
    rv = client.get("/workspace")
    assert b"--ws-surface" in rv.data


def test_workspace_html_has_token_border(client):
    """workspace.html defines --ws-border CSS custom property."""
    rv = client.get("/workspace")
    assert b"--ws-border" in rv.data


def test_workspace_html_has_token_radius_md(client):
    """workspace.html defines --ws-radius-md CSS custom property."""
    rv = client.get("/workspace")
    assert b"--ws-radius-md" in rv.data


def test_workspace_html_has_token_radius_lg(client):
    """workspace.html defines --ws-radius-lg CSS custom property."""
    rv = client.get("/workspace")
    assert b"--ws-radius-lg" in rv.data


# ── B: Font-weight and case compliance ────────────────────────────────────────


def test_workspace_html_no_font_weight_600(client):
    """Workspace CSS contains no font-weight: 600 (400/500 only)."""
    rv = client.get("/workspace")
    assert b"font-weight: 600" not in rv.data


def test_workspace_html_no_font_weight_700(client):
    """Workspace CSS contains no font-weight: 700."""
    rv = client.get("/workspace")
    assert b"font-weight: 700" not in rv.data


def test_workspace_html_no_uppercase_transform(client):
    """workspace.html contains no text-transform: uppercase (Cycle 27 preserved)."""
    rv = client.get("/workspace")
    assert b"text-transform: uppercase" not in rv.data


# ── C: Card markup class hooks in workspace.js ───────────────────────────────


def test_workspace_js_card_emits_pill_class(client):
    """workspace.js emits ws-card-pill class for tag/status pill."""
    rv = client.get("/static/workspace.js")
    assert b"ws-card-pill" in rv.data


def test_workspace_js_card_emits_title_class(client):
    """workspace.js emits ws-card-title class for card title."""
    rv = client.get("/static/workspace.js")
    assert b"ws-card-title" in rv.data


def test_workspace_js_card_emits_context_class(client):
    """workspace.js emits ws-card-context class for one-line summary."""
    rv = client.get("/static/workspace.js")
    assert b"ws-card-context" in rv.data


def test_workspace_js_card_emits_meta_class(client):
    """workspace.js emits ws-card-meta class for result/evidence metadata."""
    rv = client.get("/static/workspace.js")
    assert b"ws-card-meta" in rv.data


# ── D: Selected-state class toggle ────────────────────────────────────────────


def test_workspace_js_toggles_selected_class(client):
    """workspace.js applies ws-card-selected class when card toggle fires."""
    rv = client.get("/static/workspace.js")
    assert b"ws-card-selected" in rv.data


# ── E: Cycle 27 source contract preservation ─────────────────────────────────


def test_workspace_js_still_uses_array_is_array(client):
    """Array.isArray guard still present after Cycle 28 changes."""
    rv = client.get("/static/workspace.js")
    assert b"Array.isArray(data)" in rv.data


def test_workspace_js_still_filters_live_status(client):
    """Live status filter still present after Cycle 28 changes."""
    rv = client.get("/static/workspace.js")
    assert b'status === "live"' in rv.data


def test_workspace_js_still_no_data_cards(client):
    """workspace.js does not read data.cards after Cycle 28 changes."""
    rv = client.get("/static/workspace.js")
    assert b"data.cards" not in rv.data


def test_workspace_does_not_create_card_file(client, repo):
    """Visiting /workspace does not create card files."""
    cards_dir = repo / "cards"
    before = set(os.listdir(cards_dir))
    client.get("/workspace")
    after = set(os.listdir(cards_dir))
    assert after == before


# ── F: Raw value absence outside :root ───────────────────────────────────────


def _after_root(html_bytes: bytes) -> str:
    src = html_bytes.decode("utf-8")
    root_start = src.index(":root {")
    root_end = src.index("}", root_start) + 1
    return src[root_end:]


def test_workspace_html_no_raw_rgba_accent_outside_root(client):
    """rgba(74, 144, 217 absent outside :root; var(--ws-accent-tint) used instead."""
    rv = client.get("/workspace")
    assert rv.status_code == 200
    assert b"var(--ws-accent-tint)" in rv.data
    assert "rgba(74, 144, 217" not in _after_root(rv.data)


def test_workspace_html_no_raw_accent_hover_outside_root(client):
    """#3a7fc7 absent outside :root; var(--ws-accent-hover) used instead."""
    rv = client.get("/workspace")
    assert rv.status_code == 200
    assert b"var(--ws-accent-hover)" in rv.data
    assert "#3a7fc7" not in _after_root(rv.data)
