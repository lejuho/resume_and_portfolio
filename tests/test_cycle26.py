"""Cycle 26: Application Writing Packet Quality tests.

Covers the improved handoff packet formatting in scripts/static/studio.js:
output-type-specific titles, the Draft Metadata section (provenance, source,
fallback, character count/limit), improved section labels, and non-string
safety for warnings/ai_guidance.

All assertions use Flask test-client source-string (snapshot) style against the
deterministic, browser-only `_buildHandoffPacket` builder. No eval.
"""

from __future__ import annotations

import pytest

import scripts.dashboard as dash_mod
from scripts.dashboard import app

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


def _packet_src(client):
    """Return the source of the _buildHandoffPacket function only."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    start = src.index("function _buildHandoffPacket")
    end = src.index("\n}", start) + 2
    return src[start:end]


# ── A: Output-type-specific titles ────────────────────────────────────────────


def test_packet_title_helper_exists(client):
    """A dedicated _packetTitle helper isolates the title switch."""
    rv = client.get("/static/studio.js")
    assert b"_packetTitle" in rv.data


def test_packet_title_cover_letter(client):
    """Cover letter packets use a distinct title."""
    rv = client.get("/static/studio.js")
    assert b"Application Writing Handoff \xe2\x80\x94 Cover Letter" in rv.data


def test_packet_title_application_answer(client):
    """Application answer packets use a distinct title."""
    rv = client.get("/static/studio.js")
    assert b"Application Writing Handoff \xe2\x80\x94 Application Answer" in rv.data


def test_packet_title_fallback(client):
    """Unknown output types fall back to a generic title."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    start = src.index("function _packetTitle")
    end = src.index("\n}", start) + 2
    title_src = src[start:end]
    assert "cover_letter" in title_src
    assert "application_answer" in title_src
    # generic fallback distinct from the two specific titles
    assert 'return "Application Writing Handoff"' in title_src


# ── B: Draft Metadata section ─────────────────────────────────────────────────


def test_packet_has_draft_metadata_section(client):
    """Packet builder emits a Draft Metadata heading."""
    assert "=== Draft Metadata ===" in _packet_src(client)


def test_packet_metadata_includes_provenance_and_source(client):
    """Draft Metadata derives provenance and source from preview fields."""
    packet = _packet_src(client)
    assert "preview.draft_provenance" in packet
    assert "Provenance:" in packet
    assert "preview.refine_source" in packet
    assert "Source:" in packet


def test_packet_metadata_includes_fallback_reason(client):
    """Draft Metadata includes fallback reason when present."""
    packet = _packet_src(client)
    assert "preview.fallback_reason" in packet
    assert "Fallback reason:" in packet


def test_packet_metadata_character_count_and_limit(client):
    """Character count and limit both appear when limit is present."""
    packet = _packet_src(client)
    assert "Character count:" in packet
    assert "Character limit:" in packet
    assert "preview.character_count" in packet
    assert "preview.character_limit" in packet


def test_packet_metadata_count_only_when_no_limit(client):
    """When no limit is present, count is still emitted (count-only branch)."""
    packet = _packet_src(client)
    # an else-branch keyed off character_count handles the no-limit case
    assert "else if (preview.character_count)" in packet


# ── C: Improved section labels ────────────────────────────────────────────────


def test_packet_section_labels(client):
    """Scanability: key sections carry explicit === headings."""
    packet = _packet_src(client)
    assert "=== Target Context ===" in packet
    assert "=== Verified Draft ===" in packet
    assert "=== Evidence Used ===" in packet
    assert "=== Warnings ===" in packet
    assert "ADVISORY" in packet


# ── D: Non-string safety (future provider adapters) ───────────────────────────


def test_packet_safe_text_helper_exists(client):
    """A coercion helper guards non-string warnings/guidance items."""
    rv = client.get("/static/studio.js")
    src = rv.data.decode("utf-8")
    start = src.index("function _packetSafeText")
    end = src.index("\n}", start) + 2
    helper = src[start:end]
    assert 'typeof item === "string" ? item : String(item)' in helper


def test_packet_warnings_use_safe_text(client):
    """Warnings loop coerces items via _packetSafeText."""
    packet = _packet_src(client)
    assert "_packetSafeText(w)" in packet


def test_packet_guidance_uses_safe_text(client):
    """AI guidance loop coerces items via _packetSafeText."""
    packet = _packet_src(client)
    assert "_packetSafeText(g)" in packet


# ── E: Evidence stays sanitized (regression with Cycle 25) ────────────────────


def test_packet_evidence_uses_safe_display_fields(client):
    """Evidence loop reads display_title and never raw _appCards."""
    packet = _packet_src(client)
    assert "display_title" in packet
    assert "_appCards" not in packet
