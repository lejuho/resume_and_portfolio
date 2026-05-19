"""Portfolio CLI entry point."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from .card import CardRepo, _filename_slug
from .select import filter_cards

app = typer.Typer(
    name="pcli",
    help="Card-Based Portfolio/Resume Builder CLI",
    no_args_is_help=True,
)
build_app = typer.Typer(help="Build resume or portfolio artifacts.", no_args_is_help=True)
app.add_typer(build_app, name="build")

console = Console()
err_console = Console(stderr=True, style="bold red")

REPO_ROOT = Path(__file__).parent.parent


def _repo() -> CardRepo:
    return CardRepo(REPO_ROOT)


# ---------------------------------------------------------------------------
# pcli new
# ---------------------------------------------------------------------------

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CARD_TYPES = [
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


@app.command("new")
def cmd_new(
    type_: str = typer.Argument(..., metavar="type", help="Card type"),
    slug: str = typer.Argument(..., help="Card id (kebab-case)"),
    title: str = typer.Option("", "--title", "-t", help="Card title"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
):
    """Create a new card stub in cards/<YYYY-MM>-<slug>.mdx."""
    if type_ not in CARD_TYPES:
        err_console.print(f"Unknown type {type_!r}. Valid: {', '.join(CARD_TYPES)}")
        raise typer.Exit(1)

    if not _KEBAB_RE.match(slug):
        err_console.print(f"slug must be kebab-case, got: {slug!r}")
        raise typer.Exit(1)

    start_date = start or date.today().isoformat()
    try:
        d = date.fromisoformat(start_date)
    except ValueError:
        err_console.print(f"--start must be YYYY-MM-DD, got: {start_date!r}")
        raise typer.Exit(1)

    month_prefix = d.strftime("%Y-%m")
    filename = f"{month_prefix}-{slug}.mdx"
    dest = REPO_ROOT / "cards" / filename

    if dest.exists():
        err_console.print(f"Card already exists: {dest}")
        raise typer.Exit(1)

    stub = f"""\
---
id: {slug}
title: {title or slug}
type: {type_}
period:
  start: {start_date}
  end: null
status: draft
visibility: public
tags:
  domain: []
  skill: []
  audience: []
metrics: []
summary: ""
summary_ko: null
narrative: null
visuals: []
evidence: []
links: []
related: []
---
"""
    dest.write_text(stub, encoding="utf-8")
    console.print(f"[green]Created[/green] {dest.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# pcli validate
# ---------------------------------------------------------------------------


@app.command("validate")
def cmd_validate(
    slug: Optional[str] = typer.Argument(None, help="Validate a single card by id"),
    strict: bool = typer.Option(False, "--strict", help="Treat warnings as errors"),
):
    """Validate all cards (or one card). Exit 0 = ok, 1 = error."""
    repo = _repo()
    errors = list(repo.errors)
    warnings = repo.warnings

    if slug:
        card = repo.get(slug)
        if card is None:
            # Card may have failed validation — scan errors for stem match
            # A filename stem "2026-05-my-card" ends with the id "my-card"
            slug_errors = [e for e in errors if _filename_slug(e.path) == slug]
            if slug_errors:
                for e in slug_errors:
                    err_console.print(
                        f"[red]ERROR[/red] {e.path.relative_to(REPO_ROOT)}: {e.message}"
                    )
                raise typer.Exit(1)
            err_console.print(f"Card not found: {slug!r}")
            raise typer.Exit(1)
        # exact match: error path stem must equal the card's source filename stem
        src_stem = card._source_path.stem if card._source_path else None
        errors = [e for e in errors if src_stem and e.path.stem == src_stem]
        warnings = {k: v for k, v in warnings.items() if k == card.id}

    has_error = False

    for e in errors:
        err_console.print(f"[red]ERROR[/red] {e.path.relative_to(REPO_ROOT)}: {e.message}")
        has_error = True

    for card_id, warns in warnings.items():
        for w in warns:
            msg = f"[yellow]WARN[/yellow]  {card_id}: {w}"
            if strict:
                err_console.print(msg)
                has_error = True
            else:
                console.print(msg)

    if not errors and not warnings:
        console.print("[green]All cards valid.[/green]")
    elif not has_error:
        console.print("[green]No errors.[/green]")

    if has_error:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# pcli ls
# ---------------------------------------------------------------------------


@app.command("ls")
def cmd_ls(
    type_: Optional[str] = typer.Option(None, "--type", help="Filter by type (comma-separated)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag (OR match, comma-sep)"),
    since: Optional[str] = typer.Option(None, "--since", help="Start on or after YYYY-MM"),
    until: Optional[str] = typer.Option(None, "--until", help="Start on or before YYYY-MM"),
    status: Optional[str] = typer.Option("live", "--status", help="Status filter (comma-sep)"),
    sort: str = typer.Option("date-desc", "--sort", help="Sort: date-desc|date-asc|title"),
):
    """List cards as a Rich table."""
    repo = _repo()
    if repo.errors:
        for e in repo.errors:
            err_console.print(f"[red]ERROR[/red] {e}")
        raise typer.Exit(1)

    cards = filter_cards(
        repo.cards,
        types=type_,
        tags=tag,
        since=since,
        until=until,
        status=status,
        sort=sort,
    )

    if not cards:
        console.print("[yellow]No cards match the given filters.[/yellow]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Title")
    table.add_column("Start")
    table.add_column("Status")
    table.add_column("Tags", overflow="fold")

    for card in cards:
        all_tags = card.tags.domain + card.tags.skill + card.tags.audience
        table.add_row(
            card.id,
            card.type,
            card.title,
            card.period.start.isoformat(),
            card.status,
            ", ".join(all_tags[:5]),
        )

    console.print(table)
    console.print(f"[dim]{len(cards)} card(s)[/dim]")


# ---------------------------------------------------------------------------
# pcli show
# ---------------------------------------------------------------------------


@app.command("show")
def cmd_show(
    slug: str = typer.Argument(..., help="Card id or filename slug"),
):
    """Pretty-print a single card."""
    repo = _repo()
    card = repo.get(slug)
    if card is None:
        err_console.print(f"Card not found: {slug!r}")
        raise typer.Exit(1)

    console.rule(f"[bold]{card.title}[/bold]")
    console.print(f"[bold]id:[/bold]         {card.id}")
    console.print(f"[bold]type:[/bold]       {card.type}")
    console.print(f"[bold]status:[/bold]     {card.status}")
    console.print(f"[bold]visibility:[/bold] {card.visibility}")
    console.print(f"[bold]period:[/bold]     {card.period.start} → {card.period.end or 'ongoing'}")

    all_tags = card.tags.domain + card.tags.skill + card.tags.audience
    console.print(f"[bold]tags:[/bold]       {', '.join(all_tags) or '(none)'}")

    if card.metrics:
        console.print("[bold]metrics:[/bold]")
        for m in card.metrics:
            console.print(f"  • {m}")

    console.print(f"\n[bold]summary:[/bold]\n  {card.summary.strip()}")

    if card.summary_ko:
        console.print(f"\n[bold]summary_ko:[/bold]\n  {card.summary_ko.strip()}")

    narr = card.effective_narrative
    if narr:
        console.print(f"\n[bold]narrative:[/bold]\n{narr.strip()}")

    if card.visuals:
        console.print("\n[bold]visuals:[/bold]")
        for v in card.visuals:
            console.print(f"  [{v.role}] {v.path}" + (f" — {v.caption}" if v.caption else ""))

    if card.evidence:
        console.print("\n[bold]evidence:[/bold]")
        for e in card.evidence:
            console.print(f"  [{e.type}] {e.url}")

    if card.links:
        console.print("\n[bold]links:[/bold]")
        for ln in card.links:
            console.print(f"  {ln.label}: {ln.url}")

    warns = card.warnings()
    if warns:
        console.print()
        for w in warns:
            console.print(f"[yellow]⚠ {w}[/yellow]")


# ---------------------------------------------------------------------------
# pcli build resume
# ---------------------------------------------------------------------------


@build_app.command("resume")
def cmd_build_resume(
    template: str = typer.Option(
        "default", "--template", help="Template name under templates/resume/"
    ),  # noqa: E501
    cards_arg: Optional[str] = typer.Option(None, "--cards", help="Explicit comma-sep card ids"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tag filter (OR, comma-separated)"),
    types: Optional[str] = typer.Option(None, "--types", help="Type filter (comma-separated)"),
    since: Optional[str] = typer.Option(None, "--since", help="Since YYYY-MM"),
    until: Optional[str] = typer.Option(None, "--until", help="Until YYYY-MM"),
    max_items: int = typer.Option(12, "--max-items", help="Max cards to include"),
    lang: str = typer.Option("en", "--lang", help="Language: en or ko"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output PDF path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print selected cards; skip Typst"),
    verbose: bool = typer.Option(False, "--verbose", help="Show render steps"),
):
    """Build a PDF resume via Typst."""
    from .render_resume import build_resume

    repo = _repo()
    if repo.errors:
        for e in repo.errors:
            err_console.print(f"[red]ERROR[/red] {e}")
        raise typer.Exit(1)

    explicit_ids = [s.strip() for s in cards_arg.split(",")] if cards_arg else None

    selected = filter_cards(
        repo.cards,
        types=types,
        tags=tags,
        since=since,
        until=until,
        status="live",
        sort="date-desc",
        max_items=max_items,
        explicit_ids=explicit_ids,
    )

    if not selected:
        console.print("[yellow]No cards selected. Check filters or use --cards.[/yellow]")
        raise typer.Exit(0)

    if dry_run:
        console.print(f"[bold]Dry run:[/bold] {len(selected)} card(s) selected\n")
        for card in selected:
            console.print(f"  • [cyan]{card.id}[/cyan]  {card.title}  ({card.type})")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = out or (REPO_ROOT / "output" / f"resume-{timestamp}.pdf")

    build_resume(
        cards=selected,
        repo_root=REPO_ROOT,
        template_name=template,
        lang=lang,
        out_path=out_path,
        verbose=verbose,
    )


if __name__ == "__main__":
    app()
