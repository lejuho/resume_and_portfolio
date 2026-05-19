"""CLI integration tests using Typer's CliRunner."""

from __future__ import annotations

import textwrap

import pytest
from typer.testing import CliRunner

from scripts.pcli import app

runner = CliRunner()


# ─── Fixtures ──────────────────────────────────────────────────────────────

SAMPLE_MDX = textwrap.dedent("""\
    ---
    id: sample-card
    title: Sample Card
    type: hackathon
    period:
      start: 2026-05-01
    status: live
    summary: "A valid summary for testing the CLI commands."
    narrative: "Long enough narrative to pass live status check. Over 100 chars needed here yes."
    evidence:
      - type: repo
        url: https://github.com/example/repo
    ---
""")


@pytest.fixture()
def card_repo(tmp_path, monkeypatch):
    """Monkeypatch REPO_ROOT and create a minimal card."""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    (cards_dir / "2026-05-sample-card.mdx").write_text(SAMPLE_MDX, encoding="utf-8")
    # profile
    profile = textwrap.dedent("""\
        basics:
          name: Test User
          label: Test Engineer
          email: test@example.com
          summary_en: "Test summary."
        education: []
    """)
    (tmp_path / "profile.example.yaml").write_text(profile, encoding="utf-8")
    # .build and output dirs
    (tmp_path / ".build").mkdir()
    (tmp_path / "output").mkdir()

    import scripts.pcli as pcli_mod
    import scripts.render_resume as rr_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(rr_mod, "console", rr_mod.console)  # no-op, keep reference
    return tmp_path


# ─── help ──────────────────────────────────────────────────────────────────


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "pcli" in result.output.lower() or "portfolio" in result.output.lower()


def test_new_help():
    result = runner.invoke(app, ["new", "--help"])
    assert result.exit_code == 0


def test_validate_help():
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0


def test_ls_help():
    result = runner.invoke(app, ["ls", "--help"])
    assert result.exit_code == 0


def test_show_help():
    result = runner.invoke(app, ["show", "--help"])
    assert result.exit_code == 0


def test_build_resume_help():
    result = runner.invoke(app, ["build", "resume", "--help"])
    assert result.exit_code == 0


# ─── new ───────────────────────────────────────────────────────────────────


def test_new_creates_file(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)

    result = runner.invoke(
        app,
        [
            "new",
            "hackathon",
            "my-test-card",
            "--title",
            "My Test Card",
            "--start",
            "2026-06-01",
        ],
    )
    assert result.exit_code == 0
    expected = card_repo / "cards" / "2026-06-my-test-card.mdx"
    assert expected.exists()
    content = expected.read_text(encoding="utf-8")
    assert "id: my-test-card" in content
    assert "type: hackathon" in content


def test_new_invalid_type(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["new", "invalidtype", "slug"])
    assert result.exit_code != 0


def test_new_invalid_slug(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["new", "hackathon", "Invalid Slug"])
    assert result.exit_code != 0


def test_new_duplicate(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    # create once
    runner.invoke(app, ["new", "hackathon", "dup-card", "--start", "2026-06-01"])
    # try again
    result = runner.invoke(app, ["new", "hackathon", "dup-card", "--start", "2026-06-01"])
    assert result.exit_code != 0


# ─── validate ──────────────────────────────────────────────────────────────


def test_validate_ok(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0


def test_validate_error(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    # write a bad card
    bad = textwrap.dedent("""\
        ---
        id: bad card id
        title: Bad
        type: hackathon
        period:
          start: 2026-05-01
        summary: "ok"
        ---
    """)
    (card_repo / "cards" / "2026-05-bad-card-id.mdx").write_text(bad, encoding="utf-8")
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1


def test_validate_slug_broken_card(card_repo, monkeypatch):
    """validate <slug> must report errors for a card that failed parsing (ISSUE-3)."""
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    broken = textwrap.dedent("""\
        ---
        id: broken-card
        title: Broken
        type: hackathon
        period:
          start: 2026-05-01
        summary: "x" * 300
        ---
    """)
    (card_repo / "cards" / "2026-05-broken-card.mdx").write_text(broken, encoding="utf-8")
    # Target the broken card by id slug
    result = runner.invoke(app, ["validate", "broken-card"])
    assert result.exit_code == 1


def test_show_by_filename_stem(card_repo, monkeypatch):
    """show must resolve a card by full filename stem (ISSUE-2 regression)."""
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["show", "2026-05-sample-card"])
    assert result.exit_code == 0
    assert "Sample Card" in result.output


def test_validate_slug_no_false_positive(card_repo, monkeypatch):
    """validate <slug> must NOT report errors for a different card sharing slug suffix."""
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    # "other-broken-card" shares the "-card" suffix with "broken-card"
    broken = textwrap.dedent("""\
        ---
        id: broken-card
        title: Broken
        type: hackathon
        period:
          start: 2026-05-01
        summary: "x" * 300
        ---
    """)
    other_broken = textwrap.dedent("""\
        ---
        id: other-broken-card
        title: Other Broken
        type: hackathon
        period:
          start: 2026-04-01
        summary: "x" * 300
        ---
    """)
    (card_repo / "cards" / "2026-05-broken-card.mdx").write_text(broken, encoding="utf-8")
    (card_repo / "cards" / "2026-04-other-broken-card.mdx").write_text(
        other_broken, encoding="utf-8"
    )
    # validate "broken-card" must only report broken-card, NOT other-broken-card
    result = runner.invoke(app, ["validate", "broken-card"])
    assert result.exit_code == 1
    assert "other-broken-card" not in result.output


# ─── ls ────────────────────────────────────────────────────────────────────


def test_ls_shows_cards(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "sample-card" in result.output


def test_ls_type_filter(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["ls", "--type", "talk"])
    assert result.exit_code == 0
    assert "No cards" in result.output


# ─── show ──────────────────────────────────────────────────────────────────


def test_show_existing(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["show", "sample-card"])
    assert result.exit_code == 0
    assert "Sample Card" in result.output


def test_show_missing(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["show", "nonexistent-card"])
    assert result.exit_code == 1


# ─── build resume --dry-run ────────────────────────────────────────────────


def test_build_resume_dry_run(card_repo, monkeypatch):
    import scripts.pcli as pcli_mod

    monkeypatch.setattr(pcli_mod, "REPO_ROOT", card_repo)
    result = runner.invoke(app, ["build", "resume", "--dry-run"])
    assert result.exit_code == 0
    assert "sample-card" in result.output
    assert "Dry run" in result.output
