"""Preset loading, merging, and saving for repeatable builds."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class PresetFilters:
    tags: Optional[str] = None
    types: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None


@dataclass
class Preset:
    name: str
    target: str  # "resume" or "portfolio"
    template: Optional[str] = None
    layout: Optional[str] = None
    lang: Optional[str] = None
    max_items: Optional[int] = None
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    filters: PresetFilters = field(default_factory=PresetFilters)
    include_cards: list[str] = field(default_factory=list)
    exclude_cards: list[str] = field(default_factory=list)


class PresetError(Exception):
    pass


def _normalize_filter(value: object) -> Optional[str]:
    """Accept list or comma-string; return comma-string or None."""
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(str(v) for v in value) if value else None
    return str(value)


def load_preset(name: str, presets_dir: Path) -> Preset:
    """Load a preset from presets/<name>.yaml. Raises PresetError on failure."""
    path = presets_dir / f"{name}.yaml"
    if not path.exists():
        raise PresetError(f"Preset not found: {name!r} (looked in {presets_dir})")

    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        raise PresetError(f"Failed to parse preset {name!r}: {exc}") from exc

    target = data.get("target")
    if not target:
        raise PresetError(f"Preset {name!r} is missing required field 'target'")

    filters_raw = data.get("filters") or {}
    filters = PresetFilters(
        tags=_normalize_filter(filters_raw.get("tags")),
        types=_normalize_filter(filters_raw.get("types")),
        since=filters_raw.get("since"),
        until=filters_raw.get("until"),
    )

    return Preset(
        name=name,
        target=str(target),
        template=data.get("template"),
        layout=data.get("layout"),
        lang=data.get("lang"),
        max_items=data.get("max_items"),
        cover_title=data.get("cover_title"),
        cover_subtitle=data.get("cover_subtitle"),
        filters=filters,
        include_cards=list(data.get("include_cards") or []),
        exclude_cards=list(data.get("exclude_cards") or []),
    )


def save_last_build(args: dict, cache_dir: Path) -> None:
    """Persist the most recent build arguments to .cache/last-build.yaml."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "last-build.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(args, f, allow_unicode=True, sort_keys=False)


def load_last_build(cache_dir: Path) -> dict:
    """Load last build args from .cache/last-build.yaml. Returns {} if absent."""
    path = cache_dir / "last-build.yaml"
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_preset_from_cache(name: str, presets_dir: Path, cache_dir: Path) -> Path:
    """Write presets/<name>.yaml from the cached last-build args."""
    last = load_last_build(cache_dir)
    if not last:
        raise PresetError("No cached build found. Run a build command first.")
    if "target" not in last:
        raise PresetError("Cached build is missing 'target'. Re-run the build command.")

    presets_dir.mkdir(parents=True, exist_ok=True)
    dest = presets_dir / f"{name}.yaml"
    with dest.open("w", encoding="utf-8") as f:
        yaml.dump(last, f, allow_unicode=True, sort_keys=False)
    return dest
