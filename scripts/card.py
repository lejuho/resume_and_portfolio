"""Card schema, parsing, and repo loading."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Literal, Optional

import frontmatter
from pydantic import BaseModel, Field, PrivateAttr, field_validator

CARD_TYPE = Literal[
    "project",
    "talk",
    "paper",
    "hackathon",
    "role",
    "award",
    "writing",
    "course",
    "community",
]
CARD_STATUS = Literal["draft", "live", "archived"]
CARD_VISIBILITY = Literal["public", "private", "sensitive"]
EVIDENCE_TYPE = Literal["repo", "deck", "writeup", "demo", "article", "other"]
VISUAL_ROLE = Literal["hero", "diagram", "screenshot", "other"]

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Period(BaseModel):
    start: date
    end: Optional[date] = None


class Visual(BaseModel):
    path: str
    role: VISUAL_ROLE = "other"
    caption: Optional[str] = None


class Evidence(BaseModel):
    type: EVIDENCE_TYPE
    url: str


class Link(BaseModel):
    label: str
    url: str


class Tags(BaseModel):
    domain: list[str] = Field(default_factory=list)
    skill: list[str] = Field(default_factory=list)
    audience: list[str] = Field(default_factory=list)


class Card(BaseModel):
    id: str
    title: str
    type: CARD_TYPE
    period: Period
    status: CARD_STATUS = "draft"
    visibility: CARD_VISIBILITY = "public"
    tags: Tags = Field(default_factory=Tags)
    metrics: list[str] = Field(default_factory=list)
    summary: str
    summary_ko: Optional[str] = None
    narrative: Optional[str] = None
    visuals: list[Visual] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)

    _body: str = PrivateAttr(default="")
    _source_path: Optional[Path] = PrivateAttr(default=None)

    @field_validator("id")
    @classmethod
    def id_kebab(cls, v: str) -> str:
        if not _KEBAB_RE.match(v):
            raise ValueError(f"id must be kebab-case, got: {v!r}")
        return v

    @field_validator("summary")
    @classmethod
    def summary_length(cls, v: str) -> str:
        if len(v.strip()) > 200:
            raise ValueError(f"summary exceeds 200 chars ({len(v.strip())})")
        return v

    @field_validator("summary_ko")
    @classmethod
    def summary_ko_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 250:
            raise ValueError(f"summary_ko exceeds 250 chars ({len(v.strip())})")
        return v

    @property
    def effective_narrative(self) -> Optional[str]:
        """narrative frontmatter or markdown body fallback."""
        return self.narrative or (self._body.strip() or None)

    def warnings(self) -> list[str]:
        """Return warning-level validation messages."""
        warns = []
        if not self.evidence:
            warns.append("evidence is empty (recommended ≥ 1)")
        if len(self.metrics) > 5:
            warns.append(f"metrics has {len(self.metrics)} items (recommended ≤ 5)")
        if self.status == "live":
            narr = self.effective_narrative or ""
            if len(narr) < 100:
                warns.append(f"narrative < 100 chars for live card ({len(narr)} chars)")
        return warns


class ValidationError(Exception):
    def __init__(self, path: Path, message: str):
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def _filename_slug(path: Path) -> str:
    """Extract the slug portion from `<YYYY-MM>-<slug>.mdx`."""
    stem = path.stem  # e.g. "2026-05-pocavault-seoulana"
    # remove YYYY-MM- prefix
    parts = stem.split("-", 2)
    if len(parts) >= 3:
        return parts[2]
    return stem


def parse_card(path: Path, repo_root: Path) -> Card:
    """Parse a single .mdx file into a Card. Raises ValidationError on failure."""
    try:
        post = frontmatter.load(str(path))
    except Exception as exc:
        raise ValidationError(path, f"frontmatter parse error: {exc}") from exc

    data: dict[str, Any] = dict(post.metadata)
    body: str = post.content or ""

    try:
        card = Card.model_validate(data, context={"repo_root": repo_root})
    except Exception as exc:
        raise ValidationError(path, str(exc)) from exc

    # cross-check: id must appear in filename
    slug = _filename_slug(path)
    if card.id != slug:
        raise ValidationError(
            path,
            f"id {card.id!r} does not match filename slug {slug!r}",
        )

    card._body = body
    card._source_path = path
    return card


class CardRepo:
    """Loads all cards from a repo root. Validates cross-file constraints lazily."""

    def __init__(self, root: Path, portfolio_mode: bool = False):
        self.root = root
        self.portfolio_mode = portfolio_mode
        self._cards: Optional[list[Card]] = None
        self._errors: Optional[list[ValidationError]] = None
        self._warnings: Optional[dict[str, list[str]]] = None

    def _load(self) -> None:
        cards: list[Card] = []
        errors: list[ValidationError] = []
        warnings: dict[str, list[str]] = {}
        seen_ids: dict[str, Path] = {}

        for mdx in sorted((self.root / "cards").glob("*.mdx")):
            try:
                card = parse_card(mdx, self.root)
            except ValidationError as e:
                errors.append(e)
                continue

            # duplicate id check
            if card.id in seen_ids:
                errors.append(
                    ValidationError(
                        mdx,
                        f"duplicate id {card.id!r} (also in {seen_ids[card.id]})",
                    )
                )
                continue

            seen_ids[card.id] = mdx
            cards.append(card)

            # Visual disk check: validate mode → error; portfolio mode → renderer handles it
            if not self.portfolio_mode:
                for visual in card.visuals:
                    vp = self.root / visual.path
                    if not vp.exists():
                        errors.append(
                            ValidationError(mdx, f"visual path does not exist: {visual.path}")
                        )

            w = card.warnings()
            if w:
                warnings[card.id] = w

        self._cards = cards
        self._errors = errors
        self._warnings = warnings

    @property
    def cards(self) -> list[Card]:
        if self._cards is None:
            self._load()
        return self._cards  # type: ignore[return-value]

    @property
    def errors(self) -> list[ValidationError]:
        if self._errors is None:
            self._load()
        return self._errors  # type: ignore[return-value]

    @property
    def warnings(self) -> dict[str, list[str]]:
        if self._warnings is None:
            self._load()
        return self._warnings  # type: ignore[return-value]

    def get(self, slug: str) -> Optional[Card]:
        """Return card by exact id, or by exact filename stem (e.g. '2026-05-my-card')."""
        for card in self.cards:
            if card.id == slug:
                return card
        for card in self.cards:
            if card._source_path and card._source_path.stem == slug:
                return card
        return None
