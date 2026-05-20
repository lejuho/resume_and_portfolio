"""Build PPTX portfolio artifacts from selected cards."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console

from .card import Card

console = Console()
err_console = Console(stderr=True)


@dataclass(frozen=True)
class PortfolioOptions:
    layout: str = "one-per-card"
    include_narrative: bool = True
    cover_title: Optional[str] = None
    cover_subtitle: Optional[str] = None
    verbose: bool = False
    repo_root: Path = Path(".")


def load_profile(repo_root: Path) -> dict:
    """Load private profile first, then the example profile as fallback."""
    for name in ("profile.yaml", "profile.example.yaml"):
        path = repo_root / name
        if path.exists():
            with path.open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def build_portfolio(
    cards: list[Card],
    repo_root: Path,
    layout: str = "one-per-card",
    include_narrative: bool = True,
    cover_title: Optional[str] = None,
    cover_subtitle: Optional[str] = None,
    out_path: Optional[Path] = None,
    verbose: bool = False,
) -> Path:
    _SUPPORTED = frozenset({"one-per-card", "grouped-by-type", "timeline"})
    if layout not in _SUPPORTED:
        err_console.print(
            f"[red]Unsupported portfolio layout:[/red] {layout!r}. "
            f"Supported: {', '.join(sorted(_SUPPORTED))}"
        )
        sys.exit(2)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = out_path or (repo_root / "output" / "portfolios" / f"portfolio-{timestamp}.pptx")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    template_path = repo_root / "templates" / "portfolio" / "default.py"
    if not template_path.exists():
        err_console.print(f"[red]Portfolio template not found:[/red] {template_path}")
        sys.exit(2)

    spec = importlib.util.spec_from_file_location("portfolio_template_default", template_path)
    if spec is None or spec.loader is None:
        err_console.print(f"[red]Could not load portfolio template:[/red] {template_path}")
        sys.exit(2)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    options = PortfolioOptions(
        layout=layout,
        include_narrative=include_narrative,
        cover_title=cover_title,
        cover_subtitle=cover_subtitle,
        verbose=verbose,
        repo_root=repo_root,
    )

    profile = load_profile(repo_root)
    module.render(cards=cards, profile=profile, options=options, output_path=out_path)

    console.print(f"[green]Portfolio written:[/green] {out_path}")
    console.print(f"[dim]{len(cards)} card(s) included[/dim]")
    return out_path
