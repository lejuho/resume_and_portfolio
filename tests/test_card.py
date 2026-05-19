"""Unit tests for card schema validation."""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

import pytest

from scripts.card import Card, CardRepo, ValidationError, parse_card

# ─── Fixtures ──────────────────────────────────────────────────────────────

MINIMAL_FRONTMATTER = {
    "id": "test-card",
    "title": "Test Card",
    "type": "hackathon",
    "period": {"start": date(2026, 5, 1)},
    "summary": "A short test summary.",
}


def _make_card(**overrides) -> Card:
    data = dict(MINIMAL_FRONTMATTER, **overrides)
    return Card.model_validate(data)


# ─── id validation ─────────────────────────────────────────────────────────


def test_id_kebab_valid():
    card = _make_card(id="my-project-123")
    assert card.id == "my-project-123"


@pytest.mark.parametrize("bad_id", ["MyProject", "my_project", "my project", "123-", "-abc"])
def test_id_kebab_invalid(bad_id):
    with pytest.raises(Exception, match="kebab"):
        _make_card(id=bad_id)


# ─── summary length ────────────────────────────────────────────────────────


def test_summary_ok():
    card = _make_card(summary="x" * 200)
    assert len(card.summary) == 200


def test_summary_too_long():
    with pytest.raises(Exception, match="200"):
        _make_card(summary="x" * 201)


def test_summary_ko_ok():
    card = _make_card(summary_ko="가" * 250)
    assert card.summary_ko is not None


def test_summary_ko_too_long():
    with pytest.raises(Exception, match="250"):
        _make_card(summary_ko="가" * 251)


# ─── type enum ─────────────────────────────────────────────────────────────

ALL_TYPES = (
    "project",
    "talk",
    "paper",
    "hackathon",
    "role",
    "award",
    "writing",
    "course",
    "community",
)  # noqa: E501


def test_type_valid():
    for t in ALL_TYPES:
        card = _make_card(type=t)
        assert card.type == t


def test_type_invalid():
    with pytest.raises(Exception):
        _make_card(type="unknown-type")


# ─── visuals disk check ────────────────────────────────────────────────────


def test_visuals_path_missing(tmp_path):
    data = dict(MINIMAL_FRONTMATTER, visuals=[{"path": "assets/nonexistent.png", "role": "hero"}])
    with pytest.raises(Exception, match="visual path does not exist"):
        Card.model_validate(data, context={"repo_root": tmp_path})


def test_visuals_path_exists(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "hero.png").write_bytes(b"")
    data = dict(MINIMAL_FRONTMATTER, visuals=[{"path": "assets/hero.png", "role": "hero"}])
    card = Card.model_validate(data, context={"repo_root": tmp_path})
    assert len(card.visuals) == 1


def test_visuals_no_context():
    # Without context, disk check is skipped
    data = dict(MINIMAL_FRONTMATTER, visuals=[{"path": "assets/missing.png", "role": "hero"}])
    card = Card.model_validate(data)
    assert len(card.visuals) == 1


# ─── warnings ──────────────────────────────────────────────────────────────


def test_warning_no_evidence():
    card = _make_card(evidence=[])
    warns = card.warnings()
    assert any("evidence" in w for w in warns)


def test_warning_too_many_metrics():
    card = _make_card(metrics=["m1", "m2", "m3", "m4", "m5", "m6"])
    warns = card.warnings()
    assert any("metrics" in w for w in warns)


def test_warning_narrative_live_short():
    card = _make_card(status="live", narrative="short")
    warns = card.warnings()
    assert any("narrative" in w for w in warns)


def test_warning_narrative_live_ok():
    card = _make_card(status="live", narrative="x" * 100)
    warns = card.warnings()
    assert not any("narrative" in w for w in warns)


# ─── body fallback ─────────────────────────────────────────────────────────


def test_effective_narrative_body_fallback():
    card = _make_card(narrative=None)
    object.__setattr__(card, "_body", "body text here")
    assert card.effective_narrative == "body text here"


def test_effective_narrative_prefers_frontmatter():
    card = _make_card(narrative="frontmatter narrative")
    object.__setattr__(card, "_body", "body text")
    assert card.effective_narrative == "frontmatter narrative"


# ─── parse_card + CardRepo ──────────────────────────────────────────────────


def _write_card(cards_dir: Path, filename: str, content: str) -> Path:
    p = cards_dir / filename
    p.write_text(content, encoding="utf-8")
    return p


SAMPLE_MDX = textwrap.dedent("""\
    ---
    id: sample-card
    title: Sample Card
    type: hackathon
    period:
      start: 2026-05-01
    status: live
    summary: "A valid summary for the card."
    narrative: "This is a long enough narrative to pass the live status warning check easily yes."
    evidence:
      - type: repo
        url: https://github.com/example/repo
    ---
    Optional body text here.
""")


def test_parse_card_ok(tmp_path):
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    path = _write_card(cards_dir, "2026-05-sample-card.mdx", SAMPLE_MDX)
    card = parse_card(path, tmp_path)
    assert card.id == "sample-card"
    assert card._body.strip() == "Optional body text here."


def test_parse_card_id_slug_mismatch(tmp_path):
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    content = SAMPLE_MDX.replace("id: sample-card", "id: other-id")
    path = _write_card(cards_dir, "2026-05-sample-card.mdx", content)
    with pytest.raises(ValidationError, match="does not match filename slug"):
        parse_card(path, tmp_path)


def test_card_repo_duplicate_id(tmp_path):
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    _write_card(cards_dir, "2026-05-sample-card.mdx", SAMPLE_MDX)
    dup = SAMPLE_MDX.replace("start: 2026-05-01", "start: 2026-04-01")
    _write_card(cards_dir, "2026-04-sample-card.mdx", dup)
    repo = CardRepo(tmp_path)
    # one card loaded successfully, one duplicate error
    assert len(repo.errors) >= 1
    assert any("duplicate" in str(e) for e in repo.errors)


def test_card_repo_get(tmp_path):
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    _write_card(cards_dir, "2026-05-sample-card.mdx", SAMPLE_MDX)
    repo = CardRepo(tmp_path)
    assert repo.get("sample-card") is not None
    assert repo.get("nonexistent") is None


def test_card_repo_get_no_partial_match(tmp_path):
    """get() must not return a card whose id merely contains the query as substring."""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    _write_card(cards_dir, "2026-05-sample-card.mdx", SAMPLE_MDX)
    repo = CardRepo(tmp_path)
    # "sample" is a substring of "sample-card" but is NOT a valid exact id
    assert repo.get("sample") is None


def test_private_attrs_accessible(tmp_path):
    """_body and _source_path are set via PrivateAttr and accessible normally."""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    path = _write_card(cards_dir, "2026-05-sample-card.mdx", SAMPLE_MDX)
    card = parse_card(path, tmp_path)
    assert card._source_path == path
    assert isinstance(card._body, str)


def test_card_repo_get_by_filename_stem(tmp_path):
    """get() must return a card when queried by exact filename stem (ISSUE-2 regression)."""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    _write_card(cards_dir, "2026-05-sample-card.mdx", SAMPLE_MDX)
    repo = CardRepo(tmp_path)
    # lookup by full filename stem "2026-05-sample-card"
    card = repo.get("2026-05-sample-card")
    assert card is not None
    assert card.id == "sample-card"
