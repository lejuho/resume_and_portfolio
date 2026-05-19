"""Filter and sort cards."""

from __future__ import annotations

from datetime import date
from typing import Optional

from .card import Card


def _parse_ym(ym: str) -> date:
    """Parse YYYY-MM into the first day of that month."""
    year, month = ym.split("-")
    return date(int(year), int(month), 1)


def filter_cards(
    cards: list[Card],
    types: Optional[str] = None,  # comma-separated type list
    tags: Optional[str] = None,  # comma-separated tag OR match
    since: Optional[str] = None,  # YYYY-MM
    until: Optional[str] = None,  # YYYY-MM
    status: Optional[str] = None,  # comma-separated, default "live"
    sort: str = "date-desc",
    max_items: Optional[int] = None,
    explicit_ids: Optional[list[str]] = None,
) -> list[Card]:
    """Return filtered and sorted subset of cards."""

    # explicit card selection bypasses all filters
    if explicit_ids:
        id_set = set(explicit_ids)
        result = [c for c in cards if c.id in id_set]
        return result

    result = list(cards)

    # status filter (default: live)
    status_set = set((status or "live").split(","))
    result = [c for c in result if c.status in status_set]

    # type filter (OR)
    if types:
        type_set = set(types.split(","))
        result = [c for c in result if c.type in type_set]

    # tag filter — OR match across domain/skill/audience
    if tags:
        tag_set = set(tags.split(","))
        result = [
            c
            for c in result
            if tag_set & (set(c.tags.domain) | set(c.tags.skill) | set(c.tags.audience))
        ]

    # since filter — card must start on or after first day of since month
    if since:
        since_date = _parse_ym(since)
        result = [c for c in result if c.period.start >= since_date]

    # until filter — card must start on or before first day of until month
    if until:
        until_date = _parse_ym(until)
        result = [c for c in result if c.period.start <= until_date]

    # sort
    def _sort_key(c: Card):
        # ongoing (no end) sorts as today for date ordering
        end = c.period.end or date.today()
        return (c.period.start, end)

    if sort == "date-desc":
        result.sort(key=_sort_key, reverse=True)
    elif sort == "date-asc":
        result.sort(key=_sort_key)
    elif sort == "title":
        result.sort(key=lambda c: c.title.lower())

    if max_items is not None:
        result = result[:max_items]

    return result
