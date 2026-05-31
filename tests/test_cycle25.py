"""Cycle 25: Application Writing Export / Handoff tests.

Covers: export button DOM contract, export packet JS source contract, copy-separation,
blind-hiring safe labels, no-persistence guarantee, and empty-state behavior.
All source assertions use Flask test-client byte-substring style.
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

_IDENTITY_LIVE_MDX = """\
---
id: alumni-program-2024
title: Seoul National University Alumni Program
type: project
period:
  start: 2024-01-01
status: live
summary: "Born in Busan, led alumni research team."
metrics:
  - "30% engagement increase"
evidence:
  - type: repo
    url: https://github.com/example/alumni
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
def repo_with_identity_card(tmp_path, monkeypatch):
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "2024-01-alumni-program-2024.mdx").write_text(_IDENTITY_LIVE_MDX, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def client(repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def client_identity(repo_with_identity_card):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── A: Source/DOM contract ────────────────────────────────────────────────────


def test_studio_html_has_export_button(client):
    """Studio HTML exposes the export handoff button."""
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"st-app-export-btn" in rv.data


def test_studio_html_export_button_label(client):
    """Export button is labeled 'Export handoff packet'."""
    rv = client.get("/studio")
    assert b"Export handoff packet" in rv.data


def test_studio_html_has_export_output_element(client):
    """Studio HTML exposes the export packet output pre element."""
    rv = client.get("/studio")
    assert b"st-app-export-out" in rv.data


def test_studio_html_export_advisory_note(client):
    """Studio HTML notes that advisory guidance is labeled in the export."""
    rv = client.get("/studio")
    assert b"advisory" in rv.data.lower()


# ── B: JS source contract ─────────────────────────────────────────────────────


def test_studio_js_stores_last_preview(client):
    """studio.js declares _appLastPreview initialized to null."""
    rv = client.get("/static/studio.js")
    assert b"_appLastPreview" in rv.data
    assert b"_appLastPreview = null" in rv.data


def test_studio_js_render_sets_last_preview(client):
    """renderAppPreview assigns to _appLastPreview."""
    rv = client.get("/static/studio.js")
    assert b"_appLastPreview = preview" in rv.data


def test_studio_js_packet_builder_exists(client):
    """_buildHandoffPacket is defined in studio.js."""
    rv = client.get("/static/studio.js")
    assert b"_buildHandoffPacket" in rv.data


def test_studio_js_packet_reads_display_title(client):
    """Packet builder reads display_title from selected_cards, not raw _appCards."""
    rv = client.get("/static/studio.js")
    assert b"display_title" in rv.data
    # packet builder must not reference _appCards in the evidence loop
    src = rv.data.decode("utf-8")
    packet_start = src.index("function _buildHandoffPacket")
    packet_end = src.index("\n}", packet_start) + 2
    packet_src = src[packet_start:packet_end]
    assert "display_title" in packet_src
    assert "_appCards" not in packet_src


def test_studio_js_export_packet_function_exists(client):
    """exportAppPacket is defined and references _appLastPreview."""
    rv = client.get("/static/studio.js")
    assert b"exportAppPacket" in rv.data
    assert b"_appLastPreview" in rv.data


def test_studio_js_export_uses_blob_download(client):
    """Export uses Blob + createObjectURL + <a download> fallback chain."""
    rv = client.get("/static/studio.js")
    assert b"Blob" in rv.data
    assert b"createObjectURL" in rv.data
    assert b"download" in rv.data


def test_studio_js_advisory_label_in_packet(client):
    """Packet builder includes advisory label for AI guidance."""
    rv = client.get("/static/studio.js")
    assert b"ADVISORY" in rv.data


# ── C: Copy separation ────────────────────────────────────────────────────────


def test_studio_js_copy_draft_uses_only_draft_text(client):
    """copyAppDraft writes _appDraftText only; does not reference _appLastPreview."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    copy_start = src.index("async function copyAppDraft")
    copy_end = src.index("\n}", copy_start) + 2
    copy_src = src[copy_start:copy_end]
    assert "_appDraftText" in copy_src
    assert "_appLastPreview" not in copy_src


# ── D: Blind-hiring safe labels ───────────────────────────────────────────────


def test_blind_hiring_preview_selected_cards_uses_opaque_ref(client_identity, monkeypatch):
    """In blind-hiring mode, selected_cards display_title uses opaque Evidence ref."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    rv = client_identity.post(
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
    body = rv.get_json()
    assert body.get("ok"), f"Expected ok=True, got: {body}"
    preview = body["preview"]
    for sc in preview.get("selected_cards", []):
        label = sc.get("display_title", "")
        assert "alumni-program-2024" not in label, (
            f"Canonical card ID leaked into display_title: {label!r}"
        )


# ── E: No-persistence guarantee ───────────────────────────────────────────────


def test_no_application_packet_backend_route(client):
    """dashboard.py exposes no /api/studio/application-packet endpoint."""
    rv = client.post("/api/studio/application-packet", json={})
    assert rv.status_code == 404


def test_export_does_not_create_card_file(client, repo):
    """Generating a preview (the source of export data) does not create card files."""
    import os

    cards_dir = repo / "cards"
    before = set(os.listdir(cards_dir))
    client.post(
        "/api/studio/application-preview",
        json={
            "output_type": "application_answer",
            "card_ids": ["auth-service"],
            "target_context": {"question": "Describe a challenge."},
        },
    )
    after = set(os.listdir(cards_dir))
    assert after == before, f"Unexpected card files created: {after - before}"


# ── F: Empty-state behavior ───────────────────────────────────────────────────


def test_studio_html_export_button_starts_hidden(client):
    """Export button carries the hidden attribute in the initial HTML."""
    rv = client.get("/studio")
    # The button tag must contain both the id and hidden attribute
    assert b'id="st-app-export-btn"' in rv.data
    assert b'onclick="exportAppPacket()" hidden' in rv.data


def test_studio_js_export_packet_guards_null_preview(client):
    """exportAppPacket returns early if _appLastPreview is null."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    export_start = src.index("async function exportAppPacket")
    export_end = src.index("\n}", export_start) + 2
    export_src = src[export_start:export_end]
    assert "!_appLastPreview" in export_src or "_appLastPreview" in export_src


# ── G: Error path clears handoff state ───────────────────────────────────────


def test_studio_js_reset_helper_exists(client):
    """_resetAppHandoffState is defined in studio.js."""
    rv = client.get("/static/studio.js")
    assert b"_resetAppHandoffState" in rv.data


def test_studio_js_show_error_calls_reset(client):
    """_showAppError calls _resetAppHandoffState before rendering the error."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    err_start = src.index("function _showAppError")
    err_end = src.index("\n}", err_start) + 2
    err_src = src[err_start:err_end]
    assert "_resetAppHandoffState" in err_src


def test_studio_js_reset_clears_last_preview(client):
    """_resetAppHandoffState nulls _appLastPreview and clears _appDraftText."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    reset_start = src.index("function _resetAppHandoffState")
    reset_end = src.index("\n}", reset_start) + 2
    reset_src = src[reset_start:reset_end]
    assert "_appLastPreview = null" in reset_src
    assert "_appDraftText" in reset_src


def test_studio_js_reset_hides_export_and_copy_buttons(client):
    """_resetAppHandoffState hides both st-app-export-btn and st-app-copy-btn."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    reset_start = src.index("function _resetAppHandoffState")
    reset_end = src.index("\n}", reset_start) + 2
    reset_src = src[reset_start:reset_end]
    assert "st-app-export-btn" in reset_src
    assert "st-app-copy-btn" in reset_src
    assert "hidden = true" in reset_src


def test_studio_js_reset_clears_export_output(client):
    """_resetAppHandoffState clears and hides st-app-export-out."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    reset_start = src.index("function _resetAppHandoffState")
    reset_end = src.index("\n}", reset_start) + 2
    reset_src = src[reset_start:reset_end]
    assert "st-app-export-out" in reset_src
