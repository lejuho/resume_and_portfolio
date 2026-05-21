"""Tests for the local dashboard server."""

from __future__ import annotations

import json
import textwrap
from unittest.mock import MagicMock, patch

import pytest

import scripts.dashboard as dash_mod
from scripts.dashboard import _parse_output_path, app

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


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    (tmp_path / "cards" / "2026-05-sample-card.mdx").write_text(SAMPLE_MDX, encoding="utf-8")
    profile = textwrap.dedent("""\
        basics:
          name: Test User
          label: Engineer
          email: test@example.com
        education: []
    """)
    (tmp_path / "profile.example.yaml").write_text(profile, encoding="utf-8")
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture()
def client(repo):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─── index ────────────────────────────────────────────────────────────────────


def test_index_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200


def test_index_contains_sample_card_id(client):
    res = client.get("/")
    assert b"sample-card" in res.data


# ─── /api/cards ───────────────────────────────────────────────────────────────


def test_cards_endpoint_returns_sample_id(client):
    res = client.get("/api/cards?status=live")
    assert res.status_code == 200
    ids = [c["id"] for c in res.get_json()]
    assert "sample-card" in ids


def test_cards_endpoint_card_shape(client):
    res = client.get("/api/cards")
    card = next(c for c in res.get_json() if c["id"] == "sample-card")
    assert card["type"] == "hackathon"
    assert card["status"] == "live"
    assert "summary" in card
    assert "tags" in card
    assert "evidence_count" in card


def test_filter_by_type_returns_matching(client):
    res = client.get("/api/cards?types=hackathon&status=live")
    assert res.status_code == 200
    data = res.get_json()
    assert all(c["type"] == "hackathon" for c in data)
    assert any(c["id"] == "sample-card" for c in data)


def test_filter_by_type_excludes_others(client):
    res = client.get("/api/cards?types=role&status=all")
    assert res.status_code == 200
    assert not any(c["id"] == "sample-card" for c in res.get_json())


# ─── /api/build ───────────────────────────────────────────────────────────────


def _mock_ok(stdout="Dry run: 1 card(s) selected\n"):
    m = MagicMock()
    m.returncode = 0
    m.stdout = stdout
    m.stderr = ""
    return m


def _mock_fail(stderr="Error: build failed"):
    m = MagicMock()
    m.returncode = 1
    m.stdout = ""
    m.stderr = stderr
    return m


def test_build_passes_selected_ids(client):
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()) as mock_run:
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": ["sample-card"]}),
            content_type="application/json",
        )
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    cmd = mock_run.call_args[0][0]
    assert "--cards" in cmd
    assert "sample-card" in cmd


def test_build_dry_run_flag_present(client):
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()) as mock_run:
        client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": []}),
            content_type="application/json",
        )
    cmd = mock_run.call_args[0][0]
    assert "--dry-run" in cmd


def test_build_no_dry_run_flag_absent(client):
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()) as mock_run:
        client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": False, "selected_ids": []}),
            content_type="application/json",
        )
    cmd = mock_run.call_args[0][0]
    assert "--dry-run" not in cmd


def test_build_failure_returns_structured_error(client):
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_fail()):
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "portfolio", "dry_run": True, "selected_ids": []}),
            content_type="application/json",
        )
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is False
    assert data["exit_code"] == 1
    assert data["stderr"] != ""


def test_build_invalid_target_rejected(client):
    res = client.post(
        "/api/build",
        data=json.dumps({"target": "hack", "dry_run": True}),
        content_type="application/json",
    )
    assert res.status_code == 400


def test_no_mdx_mutated_during_build(client, repo):
    card_path = repo / "cards" / "2026-05-sample-card.mdx"
    original = card_path.read_text(encoding="utf-8")
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()):
        client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": ["sample-card"]}),
            content_type="application/json",
        )
    assert card_path.read_text(encoding="utf-8") == original


# ─── build result schema ──────────────────────────────────────────────────────


def test_build_result_schema_has_required_fields(client):
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()):
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": ["sample-card"]}),
            content_type="application/json",
        )
    d = res.get_json()
    required = (
        "ok",
        "exit_code",
        "stdout",
        "stderr",
        "command",
        "output_path",
        "target",
        "dry_run",
        "selected_ids",
    )
    for key in required:
        assert key in d, f"missing key: {key}"


def test_build_result_echoes_target_and_dry_run(client):
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()):
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "portfolio", "dry_run": False, "selected_ids": []}),
            content_type="application/json",
        )
    d = res.get_json()
    assert d["target"] == "portfolio"
    assert d["dry_run"] is False


def test_build_result_echoes_selected_ids_order(client):
    ids = ["card-b", "card-a", "card-c"]
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()):
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": ids}),
            content_type="application/json",
        )
    d = res.get_json()
    assert d["selected_ids"] == ids


def test_build_cards_flag_preserves_order(client):
    ids = ["card-b", "card-a", "card-c"]
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok()) as mock_run:
        client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": ids}),
            content_type="application/json",
        )
    cmd = mock_run.call_args[0][0]
    cards_arg = cmd[cmd.index("--cards") + 1]
    assert cards_arg == "card-b,card-a,card-c"


# ─── output path parsing ──────────────────────────────────────────────────────


def test_parse_output_path_resume():
    stdout = "Built 1 card(s).\nWrote output/resumes/2026-05-resume.pdf\nDone.\n"
    assert _parse_output_path(stdout) == "output/resumes/2026-05-resume.pdf"


def test_parse_output_path_portfolio():
    stdout = "Portfolio built → output/portfolios/portfolio-2026-05.pptx\n"
    assert _parse_output_path(stdout) == "output/portfolios/portfolio-2026-05.pptx"


def test_parse_output_path_windows_separators():
    stdout = r"Wrote output\resumes\2026-05-resume.pdf" + "\n"
    result = _parse_output_path(stdout)
    assert result is not None
    assert "resumes" in result
    assert result.endswith(".pdf")


def test_parse_output_path_dry_run_returns_none():
    stdout = "Dry run: 2 card(s) selected\nNo files written.\n"
    assert _parse_output_path(stdout) is None


def test_parse_output_path_empty_returns_none():
    assert _parse_output_path("") is None


def test_build_output_path_none_for_dry_run(client):
    stdout = "Dry run: 1 card(s) selected\n"
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok(stdout=stdout)):
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": True, "selected_ids": []}),
            content_type="application/json",
        )
    assert res.get_json()["output_path"] is None


def test_build_output_path_parsed_for_real_build(client):
    stdout = "Wrote output/resumes/cv.pdf\n"
    with patch("scripts.dashboard.subprocess.run", return_value=_mock_ok(stdout=stdout)):
        res = client.post(
            "/api/build",
            data=json.dumps({"target": "resume", "dry_run": False, "selected_ids": []}),
            content_type="application/json",
        )
    assert res.get_json()["output_path"] == "output/resumes/cv.pdf"


def test_parse_output_path_labeled_with_spaces():
    stdout = r"Resume written: C:\some dir\output\resumes\resume with space.pdf" + "\n"
    result = _parse_output_path(stdout)
    assert result is not None
    assert result.endswith("resume with space.pdf")
    assert "Resume written" not in result


def test_parse_output_path_path_on_next_line():
    stdout = "Portfolio written:\nC:\\output\\portfolios\\portfolio with space.pptx\n"
    result = _parse_output_path(stdout)
    assert result is not None
    assert result.endswith(".pptx")
    assert "portfolios" in result.lower()


def test_parse_output_path_relative_with_spaces():
    result = _parse_output_path("output/portfolios/my deck.pptx\n")
    assert result == "output/portfolios/my deck.pptx"


def test_parse_output_path_no_false_positive_on_error_line():
    stdout = "Error: expected output in resumes folder but file.pdf was missing\n"
    assert _parse_output_path(stdout) is None


# ─── card authoring: GET /api/cards/<id> ─────────────────────────────────────


def test_get_card_returns_fields(client):
    res = client.get("/api/cards/sample-card")
    assert res.status_code == 200
    d = res.get_json()
    assert d["ok"] is True
    assert d["id"] == "sample-card"
    assert "fields" in d
    assert d["fields"]["type"] == "hackathon"
    assert "body" in d


def test_get_card_not_found(client):
    res = client.get("/api/cards/nonexistent-card")
    assert res.status_code == 404


def test_get_card_invalid_id(client):
    res = client.get("/api/cards/INVALID_ID")
    assert res.status_code == 400


# ─── card authoring: POST /api/cards ─────────────────────────────────────────


def test_create_card_writes_file(client, repo):
    res = client.post(
        "/api/cards",
        data=json.dumps(
            {
                "id": "test-new-card",
                "title": "Test New Card",
                "type": "project",
                "period_start": "2026-01-15",
                "summary": "A test card for dashboard authoring.",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 201
    d = res.get_json()
    assert d["ok"] is True
    assert d["id"] == "test-new-card"
    created = repo / "cards" / "2026-01-test-new-card.mdx"
    assert created.exists()


def test_create_card_defaults_draft_public(client, repo):
    client.post(
        "/api/cards",
        data=json.dumps(
            {
                "id": "draft-card",
                "title": "Draft Card",
                "type": "project",
                "period_start": "2026-03-01",
                "summary": "Draft defaults test.",
            }
        ),
        content_type="application/json",
    )
    path = repo / "cards" / "2026-03-draft-card.mdx"
    content = path.read_text(encoding="utf-8")
    assert "status: draft" in content
    assert "visibility: public" in content


def test_create_card_duplicate_rejected(client, repo):
    payload = json.dumps(
        {
            "id": "sample-card",
            "title": "Duplicate",
            "type": "project",
            "period_start": "2026-05-01",
            "summary": "Should fail.",
        }
    )
    res = client.post("/api/cards", data=payload, content_type="application/json")
    assert res.status_code == 409


def test_create_card_invalid_id_rejected(client):
    res = client.post(
        "/api/cards",
        data=json.dumps(
            {
                "id": "INVALID ID!",
                "type": "project",
                "period_start": "2026-01-01",
                "summary": "x",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 400


def test_create_card_invalid_type_rejected(client):
    res = client.post(
        "/api/cards",
        data=json.dumps(
            {
                "id": "bad-type-card",
                "type": "notavalidtype",
                "period_start": "2026-01-01",
                "summary": "x",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 422


def test_create_card_path_traversal_rejected(client):
    res = client.post(
        "/api/cards",
        data=json.dumps(
            {
                "id": "ok-id",
                "type": "project",
                "period_start": "../../../etc/passwd",
                "summary": "x",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 400


# ─── card authoring: PUT /api/cards/<id> ─────────────────────────────────────


def test_update_card_changes_title(client, repo):
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"title": "Updated Title"},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    d = res.get_json()
    assert d["ok"] is True
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "Updated Title" in content


def test_update_card_preserves_other_fields(client, repo):
    client.put(
        "/api/cards/sample-card",
        data=json.dumps({"fields": {"summary": "New summary."}, "body": ""}),
        content_type="application/json",
    )
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "hackathon" in content


def test_update_card_invalid_data_leaves_file_unchanged(client, repo):
    card_path = repo / "cards" / "2026-05-sample-card.mdx"
    original = card_path.read_text(encoding="utf-8")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps({"fields": {"type": "notvalid"}, "body": ""}),
        content_type="application/json",
    )
    assert res.status_code == 422
    assert card_path.read_text(encoding="utf-8") == original


def test_update_card_not_found(client):
    res = client.put(
        "/api/cards/nonexistent-card",
        data=json.dumps({"fields": {}, "body": ""}),
        content_type="application/json",
    )
    assert res.status_code == 404


def test_update_card_invalid_id_rejected(client):
    res = client.put(
        "/api/cards/INVALID_ID",
        data=json.dumps({"fields": {}, "body": ""}),
        content_type="application/json",
    )
    assert res.status_code == 400


def test_create_card_duplicate_id_different_month(client, repo):
    """Creating same id with different month must be 409 (cross-month duplicate)."""
    res = client.post(
        "/api/cards",
        data=json.dumps(
            {
                "id": "sample-card",
                "type": "project",
                "period_start": "2026-06-01",
                "summary": "Different month same id.",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 409
    assert not (repo / "cards" / "2026-06-sample-card.mdx").exists()


def test_update_card_id_change_rejected(client, repo):
    """PUT with fields.id differing from URL id must return 400, file unchanged."""
    card_path = repo / "cards" / "2026-05-sample-card.mdx"
    original = card_path.read_text(encoding="utf-8")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps({"fields": {"id": "renamed-card"}, "body": ""}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert card_path.read_text(encoding="utf-8") == original


def test_update_card_same_id_accepted(client, repo):
    """PUT with fields.id matching URL card_id is fine."""
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps({"fields": {"id": "sample-card", "summary": "Updated."}, "body": ""}),
        content_type="application/json",
    )
    assert res.status_code == 200


def test_get_card_no_suffix_collision(client, repo):
    """????-??-<id>.mdx glob must not match files sharing the id as a suffix."""
    (repo / "cards" / "2026-01-foo-sample-card.mdx").write_text(SAMPLE_MDX, encoding="utf-8")
    res = client.get("/api/cards/sample-card")
    assert res.status_code == 200
    assert res.get_json()["id"] == "sample-card"


def test_dashboard_has_new_card_button(client):
    res = client.get("/")
    assert b"New card" in res.data or b"new-card" in res.data


def test_dashboard_has_edit_button(client):
    res = client.get("/")
    assert b"openEdit" in res.data or b"edit-btn" in res.data


# ─── card detail editing: tags / metrics / evidence / visuals ─────────────────


def test_update_card_tags(client, repo):
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"tags": {"domain": ["web3"], "skill": ["python"], "audience": []}},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "web3" in content
    assert "python" in content


def test_update_card_metrics(client, repo):
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"metrics": ["10k users", "99% uptime"]},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "10k users" in content


def test_update_card_evidence(client, repo):
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"evidence": [{"type": "repo", "url": "https://github.com/x/y"}]},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "github.com/x/y" in content


def test_update_card_invalid_evidence_type(client, repo):
    card_path = repo / "cards" / "2026-05-sample-card.mdx"
    original = card_path.read_text(encoding="utf-8")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"evidence": [{"type": "invalid_type", "url": "https://example.com"}]},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 422
    assert card_path.read_text(encoding="utf-8") == original


def test_update_card_visuals(client, repo):
    (repo / "assets").mkdir()
    (repo / "assets" / "hero.png").write_bytes(b"")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {
                    "visuals": [{"path": "assets/hero.png", "role": "hero", "caption": "Hero"}]
                },
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "assets/hero.png" in content


def test_update_card_invalid_visual_role(client, repo):
    card_path = repo / "cards" / "2026-05-sample-card.mdx"
    original = card_path.read_text(encoding="utf-8")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"visuals": [{"path": "assets/img.png", "role": "invalid_role"}]},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 422
    assert card_path.read_text(encoding="utf-8") == original


def test_update_card_body(client, repo):
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {},
                "body": "# Narrative\n\nThis is the body content.",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    content = (repo / "cards" / "2026-05-sample-card.mdx").read_text(encoding="utf-8")
    assert "# Narrative" in content


def test_get_card_includes_visual_hints(client, repo):
    mdx_with_visuals = textwrap.dedent("""\
        ---
        id: visual-card
        title: Visual Card
        type: project
        period:
          start: 2026-04-01
        status: draft
        summary: Card with visuals.
        visuals:
          - path: assets/hero.png
            role: hero
            caption: Hero
        ---
    """)
    (repo / "cards" / "2026-04-visual-card.mdx").write_text(mdx_with_visuals, encoding="utf-8")
    res = client.get("/api/cards/visual-card")
    assert res.status_code == 200
    d = res.get_json()
    assert "visual_hints" in d
    assert "assets/hero.png" in d["visual_hints"]
    assert d["visual_hints"]["assets/hero.png"] is False


def test_dashboard_static_js_served(client):
    res = client.get("/static/dashboard.js")
    assert res.status_code == 200
    assert b"render" in res.data


# ─── visual path existence validation ────────────────────────────────────────


def test_update_card_missing_visual_path_rejected(client, repo):
    card_path = repo / "cards" / "2026-05-sample-card.mdx"
    original = card_path.read_text(encoding="utf-8")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {"visuals": [{"path": "assets/missing.png", "role": "hero"}]},
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 422
    assert "does not exist" in res.get_json()["error"]
    assert card_path.read_text(encoding="utf-8") == original


def test_update_card_existing_visual_path_succeeds(client, repo):
    (repo / "assets").mkdir()
    (repo / "assets" / "hero.png").write_bytes(b"")
    res = client.put(
        "/api/cards/sample-card",
        data=json.dumps(
            {
                "fields": {
                    "visuals": [{"path": "assets/hero.png", "role": "hero", "caption": "Hero"}]
                },
                "body": "",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200


def test_dashboard_has_detail_hint(client):
    res = client.get("/")
    assert b"af-detail-hint" in res.data
