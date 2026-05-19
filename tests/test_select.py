"""Unit tests for card filtering and sorting."""

from __future__ import annotations

from datetime import date

from scripts.card import Card
from scripts.select import filter_cards


def _card(
    id: str,
    type: str = "project",
    status: str = "live",
    start: date = date(2026, 1, 1),
    domain: list[str] | None = None,
    skill: list[str] | None = None,
    audience: list[str] | None = None,
    title: str = "Title",
) -> Card:
    return Card.model_validate(
        {
            "id": id,
            "title": title,
            "type": type,
            "period": {"start": start},
            "status": status,
            "summary": "Short summary.",
            "tags": {
                "domain": domain or [],
                "skill": skill or [],
                "audience": audience or [],
            },
        }
    )


CARDS = [
    _card("alpha", type="hackathon", start=date(2026, 3, 1), domain=["web3"], skill=["solana"]),
    _card("beta", type="project", start=date(2026, 1, 1), domain=["analytics"]),
    _card("gamma", type="talk", status="archived", start=date(2025, 11, 1)),
    _card("delta", type="role", start=date(2025, 6, 1), audience=["korean-market"]),
]


# ─── status filter ─────────────────────────────────────────────────────────


def test_default_status_live():
    result = filter_cards(CARDS)
    ids = [c.id for c in result]
    assert "gamma" not in ids  # archived
    assert "alpha" in ids


def test_status_include_archived():
    result = filter_cards(CARDS, status="archived")
    assert [c.id for c in result] == ["gamma"]


def test_status_multi():
    result = filter_cards(CARDS, status="live,archived")
    ids = {c.id for c in result}
    assert "gamma" in ids
    assert "alpha" in ids


# ─── type filter ───────────────────────────────────────────────────────────


def test_type_single():
    result = filter_cards(CARDS, types="hackathon")
    assert all(c.type == "hackathon" for c in result)


def test_type_multi_or():
    result = filter_cards(CARDS, types="hackathon,talk", status="live,archived")
    types = {c.type for c in result}
    assert types == {"hackathon", "talk"}


# ─── tag filter ────────────────────────────────────────────────────────────


def test_tag_domain_match():
    result = filter_cards(CARDS, tags="web3")
    assert [c.id for c in result] == ["alpha"]


def test_tag_skill_match():
    result = filter_cards(CARDS, tags="solana")
    assert [c.id for c in result] == ["alpha"]


def test_tag_audience_match():
    result = filter_cards(CARDS, tags="korean-market")
    assert [c.id for c in result] == ["delta"]


def test_tag_or_match():
    result = filter_cards(CARDS, tags="web3,analytics")
    ids = {c.id for c in result}
    assert ids == {"alpha", "beta"}


def test_tag_no_match():
    result = filter_cards(CARDS, tags="nonexistent")
    assert result == []


# ─── since / until ─────────────────────────────────────────────────────────


def test_since_filters():
    result = filter_cards(CARDS, since="2026-01")
    ids = {c.id for c in result}
    assert "alpha" in ids
    assert "beta" in ids
    assert "delta" not in ids


def test_until_filters():
    result = filter_cards(CARDS, until="2025-12", status="live,archived")
    ids = {c.id for c in result}
    assert "gamma" in ids
    assert "delta" in ids
    assert "alpha" not in ids


def test_until_month_inclusive():
    """--until 2026-03 must include cards starting on any day within March 2026."""
    cards = [
        _card("mid-month", start=date(2026, 3, 15)),
        _card("end-month", start=date(2026, 3, 31)),
        _card("next-month", start=date(2026, 4, 1)),
    ]
    result = filter_cards(cards, until="2026-03")
    ids = {c.id for c in result}
    assert "mid-month" in ids
    assert "end-month" in ids
    assert "next-month" not in ids


def test_until_first_day_of_month_included():
    """--until 2026-04 must include a card starting on 2026-04-15 (ISSUE-1 regression)."""
    cards = [_card("apr-card", start=date(2026, 4, 15))]
    result = filter_cards(cards, until="2026-04")
    assert len(result) == 1


# ─── sort ──────────────────────────────────────────────────────────────────


def test_sort_date_desc():
    result = filter_cards(CARDS, sort="date-desc")
    starts = [c.period.start for c in result]
    assert starts == sorted(starts, reverse=True)


def test_sort_date_asc():
    result = filter_cards(CARDS, sort="date-asc")
    starts = [c.period.start for c in result]
    assert starts == sorted(starts)


def test_sort_title():
    cards = [
        _card("z-card", title="Zebra"),
        _card("a-card", title="Apple"),
        _card("m-card", title="Mango"),
    ]
    result = filter_cards(cards, sort="title")
    assert [c.title for c in result] == ["Apple", "Mango", "Zebra"]


# ─── max_items ─────────────────────────────────────────────────────────────


def test_max_items():
    result = filter_cards(CARDS, max_items=2)
    assert len(result) <= 2


# ─── explicit_ids ──────────────────────────────────────────────────────────


def test_explicit_ids_bypass_filters():
    result = filter_cards(CARDS, explicit_ids=["gamma"], status="live")
    # gamma is archived but should be included via explicit selection
    assert len(result) == 1
    assert result[0].id == "gamma"
