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
