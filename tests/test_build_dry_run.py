"""Tests verifying dry-run does not produce final artifacts and validates inputs."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.pcli import app

runner = CliRunner()

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
    (tmp_path / ".build").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "templates" / "portfolio").mkdir(parents=True)
    template_src = Path(__file__).parents[1] / "templates" / "portfolio" / "default.py"
    shutil.copy(template_src, tmp_path / "templates" / "portfolio" / "default.py")

    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", tmp_path)
    return tmp_path


# ─── dry-run creates no final artifacts ────────────────────────────────────


def test_resume_dry_run_creates_no_pdf(repo):
    result = runner.invoke(app, ["build", "resume", "--dry-run"])
    assert result.exit_code == 0
    assert list(repo.rglob("*.pdf")) == []


def test_portfolio_dry_run_creates_no_pptx(repo):
    result = runner.invoke(app, ["build", "portfolio", "--dry-run"])
    assert result.exit_code == 0
    assert list(repo.rglob("*.pptx")) == []


def test_resume_dry_run_shows_cards(repo):
    result = runner.invoke(app, ["build", "resume", "--dry-run"])
    assert result.exit_code == 0
    assert "sample-card" in result.output
    assert "Dry run" in result.output


def test_portfolio_dry_run_shows_cards(repo):
    result = runner.invoke(app, ["build", "portfolio", "--dry-run"])
    assert result.exit_code == 0
    assert "sample-card" in result.output


# ─── input validation ───────────────────────────────────────────────────────


def test_invalid_tone_rejected(repo):
    result = runner.invoke(app, ["build", "resume", "--tone", "aggressive", "--dry-run"])
    assert result.exit_code != 0
    assert "formal" in result.output or "formal" in (result.stderr or "")


def test_invalid_lang_rejected(repo):
    result = runner.invoke(app, ["build", "resume", "--lang", "jp", "--dry-run"])
    assert result.exit_code != 0
    assert "en" in result.output or "ko" in result.output or "en" in (result.stderr or "")


def test_invalid_max_items_zero_rejected(repo):
    result = runner.invoke(app, ["build", "resume", "--max-items", "0", "--dry-run"])
    assert result.exit_code != 0


def test_invalid_max_items_negative_rejected(repo):
    result = runner.invoke(app, ["build", "resume", "--max-items", "-1", "--dry-run"])
    assert result.exit_code != 0


def test_portfolio_max_items_zero_rejected(repo):
    result = runner.invoke(app, ["build", "portfolio", "--max-items", "0", "--dry-run"])
    assert result.exit_code != 0


def test_portfolio_max_items_negative_rejected(repo):
    result = runner.invoke(app, ["build", "portfolio", "--max-items", "-1", "--dry-run"])
    assert result.exit_code != 0


def test_invalid_layout_rejected(repo):
    result = runner.invoke(app, ["build", "portfolio", "--layout", "bad-layout", "--dry-run"])
    assert result.exit_code != 0


def test_valid_tone_accepted(repo):
    for tone in ("formal", "founder", "technical"):
        result = runner.invoke(app, ["build", "resume", "--tone", tone, "--dry-run"])
        assert result.exit_code == 0, f"tone={tone!r} failed: {result.output}"


def test_valid_lang_accepted(repo):
    for lang in ("en", "ko"):
        result = runner.invoke(app, ["build", "resume", "--lang", lang, "--dry-run"])
        assert result.exit_code == 0, f"lang={lang!r} failed: {result.output}"


def test_valid_max_items_accepted(repo):
    result = runner.invoke(app, ["build", "resume", "--max-items", "3", "--dry-run"])
    assert result.exit_code == 0


# ─── llm tailor validation ──────────────────────────────────────────────────


def test_llm_tailor_invalid_tone(repo, tmp_path):
    jd = tmp_path / "jd.txt"
    jd.write_text("engineer", encoding="utf-8")
    result = runner.invoke(
        app, ["llm", "tailor", "--cards", "sample-card", "--jd", str(jd), "--tone", "casual"]
    )
    assert result.exit_code != 0


def test_llm_tailor_invalid_lang(repo, tmp_path):
    jd = tmp_path / "jd.txt"
    jd.write_text("engineer", encoding="utf-8")
    result = runner.invoke(
        app, ["llm", "tailor", "--cards", "sample-card", "--jd", str(jd), "--lang", "fr"]
    )
    assert result.exit_code != 0
