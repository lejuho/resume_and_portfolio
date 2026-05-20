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
preset_app = typer.Typer(help="Manage build presets.", no_args_is_help=True)
app.add_typer(preset_app, name="preset")
llm_app = typer.Typer(
    help="LLM tailoring — score, rewrite, and suggest cards.", no_args_is_help=True
)
app.add_typer(llm_app, name="llm")

console = Console()
err_console = Console(stderr=True, style="bold red")

REPO_ROOT = Path(__file__).parent.parent

VALID_TONES = frozenset({"formal", "founder", "technical"})
VALID_LANGS = frozenset({"en", "ko"})


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
    preset_name: Optional[str] = typer.Option(None, "--preset", help="Preset name from presets/"),
    template: Optional[str] = typer.Option(None, "--template", help="Template (default: default)"),
    cards_arg: Optional[str] = typer.Option(None, "--cards", help="Explicit comma-sep card ids"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tag filter (OR, comma-separated)"),
    types: Optional[str] = typer.Option(None, "--types", help="Type filter (comma-separated)"),
    since: Optional[str] = typer.Option(None, "--since", help="Since YYYY-MM"),
    until: Optional[str] = typer.Option(None, "--until", help="Until YYYY-MM"),
    max_items: Optional[int] = typer.Option(None, "--max-items", help="Max cards (default: 12)"),
    lang: Optional[str] = typer.Option(None, "--lang", help="Language: en or ko (default: en)"),
    jd: Optional[str] = typer.Option(
        None, "--jd", help="Job description file path or '-' for stdin"
    ),
    tone: Optional[str] = typer.Option(
        None, "--tone", help="Rewrite tone: formal|founder|technical"
    ),
    show_llm_diff: bool = typer.Option(
        False, "--show-llm-diff", help="Print before/after summary rewrites"
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="Force LLM call, bypass cache"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output PDF path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print selected cards; skip Typst"),
    verbose: bool = typer.Option(False, "--verbose", help="Show render steps"),
):
    """Build a PDF resume via Typst."""
    from .preset import PresetError, load_preset, save_last_build
    from .render_resume import build_resume

    exclude_ids: list[str] = []

    if preset_name:
        try:
            p = load_preset(preset_name, REPO_ROOT / "presets")
        except PresetError as exc:
            err_console.print(f"[red]Preset error:[/red] {exc}")
            raise typer.Exit(1)
        if p.target != "resume":
            err_console.print(f"[red]Preset target is {p.target!r}, expected 'resume'.[/red]")
            raise typer.Exit(1)
        template = template or p.template or "default"
        lang = lang or p.lang or "en"
        max_items = max_items if max_items is not None else (p.max_items or 12)
        tags = tags or p.filters.tags
        types = types or p.filters.types
        since = since or p.filters.since
        until = until or p.filters.until
        exclude_ids = p.exclude_cards
        explicit_ids = (
            [s.strip() for s in cards_arg.split(",")] if cards_arg else (p.include_cards or None)
        )
    else:
        template = template or "default"
        lang = lang or "en"
        max_items = max_items if max_items is not None else 12
        explicit_ids = [s.strip() for s in cards_arg.split(",")] if cards_arg else None

    if lang not in VALID_LANGS:
        raise typer.BadParameter(f"must be one of {sorted(VALID_LANGS)}", param_hint="'--lang'")
    if tone and tone not in VALID_TONES:
        raise typer.BadParameter(f"must be one of {sorted(VALID_TONES)}", param_hint="'--tone'")
    if max_items is not None and max_items < 1:
        raise typer.BadParameter("must be a positive integer", param_hint="'--max-items'")

    repo = _repo()
    if repo.errors:
        for e in repo.errors:
            err_console.print(f"[red]ERROR[/red] {e}")
        raise typer.Exit(1)

    # JD scoring: filter without max_items, score+sort, then slice
    jd_text: Optional[str] = None
    if jd:
        from .llm import LLMError, read_jd

        try:
            jd_text = read_jd(jd)
        except LLMError as exc:
            err_console.print(f"[red]JD error:[/red] {exc}")
            raise typer.Exit(1)

    selected = filter_cards(
        repo.cards,
        types=types,
        tags=tags,
        since=since,
        until=until,
        status="live",
        sort="date-desc",
        max_items=None if jd_text else max_items,
        explicit_ids=explicit_ids,
        exclude_ids=exclude_ids or None,
    )

    if not selected:
        console.print("[yellow]No cards selected. Check filters or use --cards.[/yellow]")
        raise typer.Exit(0)

    llm_meta: dict = {}

    if jd_text and not dry_run:
        from .llm import LLMError, score_cards

        try:
            scored = score_cards(
                selected,
                jd_text,
                lang=lang,
                cache_dir=REPO_ROOT / ".cache" / "llm",
                no_cache=no_cache,
            )
        except LLMError as exc:
            console.print(f"[yellow]WARN[/yellow] LLM scoring failed, using unscored order: {exc}")
            scored = [(c, 0.0, "") for c in selected]
        selected = [c for c, _, _ in scored][:max_items]
        llm_meta["scores"] = {c.id: {"score": s, "reason": r} for c, s, r in scored}

    elif jd_text and dry_run:
        console.print(f"[dim]LLM: jd={jd!r} tone={tone!r} (scoring skipped in dry-run)[/dim]")
        selected = selected[:max_items]

    # Summary rewrites (in-memory only, never mutates Card)
    if (jd_text or tone) and not dry_run:
        from .llm import LLMError, rewrite_summary

        rewritten_cards = []
        rewrites: dict = {}
        effective_tone = tone or "formal"
        for card in selected:
            try:
                new_summary = rewrite_summary(
                    card,
                    jd_text,
                    tone=effective_tone,
                    lang=lang,
                    cache_dir=REPO_ROOT / ".cache" / "llm",
                    no_cache=no_cache,
                )
                if show_llm_diff or verbose:
                    original = card.summary_ko if lang == "ko" and card.summary_ko else card.summary
                    console.print(f"[dim]rewrite {card.id}:[/dim]")
                    console.print(f"  before: {original}")
                    console.print(f"  after:  {new_summary}")
                rewrites[card.id] = new_summary
                rewritten_cards.append(card.model_copy(update={"summary": new_summary}))
            except LLMError as exc:
                console.print(f"[yellow]WARN[/yellow] rewrite failed for {card.id}: {exc}")
                rewritten_cards.append(card)
        selected = rewritten_cards
        llm_meta["rewrites"] = rewrites

    # bok template requires summary_ko — validate before build, warn on dry-run
    missing_ko = [c.id for c in selected if template == "bok" and not c.summary_ko]

    if dry_run:
        llm_hint = f" [dim]jd={jd!r}[/dim]" if jd else ""
        console.print(
            f"[bold]Dry run:[/bold] {len(selected)} card(s) selected  "
            f"[dim]template={template} lang={lang}[/dim]{llm_hint}\n"
        )
        for card in selected:
            console.print(f"  • [cyan]{card.id}[/cyan]  {card.title}  ({card.type})")
        if missing_ko:
            console.print(
                f"[yellow]WARN[/yellow] bok: missing summary_ko on: {', '.join(missing_ko)}"
            )
        return

    if missing_ko:
        err_console.print(
            "[red]bok template requires summary_ko on all selected cards.[/red]\n"
            f"Missing summary_ko: {', '.join(missing_ko)}"
        )
        raise typer.Exit(1)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = out or (REPO_ROOT / "output" / "resumes" / f"resume-{timestamp}.pdf")

    save_last_build(
        {
            "target": "resume",
            "template": template,
            "lang": lang,
            "max_items": max_items,
            "filters": {"tags": tags, "types": types, "since": since, "until": until},
            "include_cards": explicit_ids or [],
            "exclude_cards": exclude_ids,
        },
        REPO_ROOT / ".cache",
    )

    build_resume(
        cards=selected,
        repo_root=REPO_ROOT,
        template_name=template,
        lang=lang,
        out_path=out_path,
        verbose=verbose,
        extra_meta={"llm": llm_meta} if llm_meta else None,
    )


@build_app.command("portfolio")
def cmd_build_portfolio(
    preset_name: Optional[str] = typer.Option(None, "--preset", help="Preset name from presets/"),
    cards_arg: Optional[str] = typer.Option(None, "--cards", help="Explicit comma-sep card ids"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Tag filter (OR, comma-separated)"),
    types: Optional[str] = typer.Option(None, "--types", help="Type filter (comma-separated)"),
    since: Optional[str] = typer.Option(None, "--since", help="Since YYYY-MM"),
    until: Optional[str] = typer.Option(None, "--until", help="Until YYYY-MM"),
    max_items: Optional[int] = typer.Option(None, "--max-items", help="Max cards (default: 12)"),
    layout: Optional[str] = typer.Option(None, "--layout", help="Layout (default: one-per-card)"),
    include_narrative: bool = typer.Option(
        True,
        "--include-narrative/--no-narrative",
        help="Include narrative excerpts on card slides",
    ),
    cover_title: Optional[str] = typer.Option(None, "--cover-title", help="Cover slide title"),
    cover_subtitle: Optional[str] = typer.Option(None, "--cover-subtitle", help="Cover subtitle"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output PPTX path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print selected cards; skip PPTX"),
    verbose: bool = typer.Option(False, "--verbose", help="Show render steps"),
):
    """Build a PPTX portfolio via python-pptx."""
    from .preset import PresetError, load_preset, save_last_build
    from .render_portfolio import build_portfolio

    exclude_ids: list[str] = []

    if preset_name:
        try:
            p = load_preset(preset_name, REPO_ROOT / "presets")
        except PresetError as exc:
            err_console.print(f"[red]Preset error:[/red] {exc}")
            raise typer.Exit(1)
        if p.target != "portfolio":
            err_console.print(f"[red]Preset target is {p.target!r}, expected 'portfolio'.[/red]")
            raise typer.Exit(1)
        layout = layout or p.layout or "one-per-card"
        max_items = max_items if max_items is not None else (p.max_items or 12)
        cover_title = cover_title or p.cover_title
        cover_subtitle = cover_subtitle or p.cover_subtitle
        tags = tags or p.filters.tags
        types = types or p.filters.types
        since = since or p.filters.since
        until = until or p.filters.until
        exclude_ids = p.exclude_cards
        explicit_ids = (
            [s.strip() for s in cards_arg.split(",")] if cards_arg else (p.include_cards or None)
        )
    else:
        layout = layout or "one-per-card"
        max_items = max_items if max_items is not None else 12
        explicit_ids = [s.strip() for s in cards_arg.split(",")] if cards_arg else None

    _SUPPORTED_LAYOUTS = frozenset({"one-per-card", "grouped-by-type", "timeline"})
    if layout not in _SUPPORTED_LAYOUTS:
        err_console.print(
            f"[red]Unsupported layout:[/red] {layout!r}. "
            f"Supported: {', '.join(sorted(_SUPPORTED_LAYOUTS))}"
        )
        raise typer.Exit(2)

    repo = CardRepo(REPO_ROOT, portfolio_mode=True)
    if repo.errors:
        for e in repo.errors:
            err_console.print(f"[red]ERROR[/red] {e}")
        raise typer.Exit(1)

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
        exclude_ids=exclude_ids or None,
    )

    if not selected:
        console.print("[yellow]No cards selected. Check filters or use --cards.[/yellow]")
        raise typer.Exit(0)

    if dry_run:
        console.print(
            f"[bold]Dry run:[/bold] {len(selected)} card(s) selected for portfolio  "
            f"[dim]layout={layout}[/dim]\n"
        )
        for card in selected:
            console.print(f"  • [cyan]{card.id}[/cyan]  {card.title}  ({card.type})")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = out or (REPO_ROOT / "output" / "portfolios" / f"portfolio-{timestamp}.pptx")

    save_last_build(
        {
            "target": "portfolio",
            "layout": layout,
            "max_items": max_items,
            "cover_title": cover_title,
            "cover_subtitle": cover_subtitle,
            "filters": {"tags": tags, "types": types, "since": since, "until": until},
            "include_cards": explicit_ids or [],
            "exclude_cards": exclude_ids,
        },
        REPO_ROOT / ".cache",
    )

    build_portfolio(
        cards=selected,
        repo_root=REPO_ROOT,
        layout=layout,
        include_narrative=include_narrative,
        cover_title=cover_title,
        cover_subtitle=cover_subtitle,
        out_path=out_path,
        verbose=verbose,
    )


# ---------------------------------------------------------------------------
# pcli preset
# ---------------------------------------------------------------------------


@preset_app.command("run")
def cmd_preset_run(
    name: str = typer.Argument(..., help="Preset name"),
    out: Optional[Path] = typer.Option(None, "--out", help="Override output path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print selection; skip rendering"),
    verbose: bool = typer.Option(False, "--verbose", help="Show render steps"),
):
    """Run a build preset by name."""
    from .preset import PresetError, load_preset

    try:
        p = load_preset(name, REPO_ROOT / "presets")
    except PresetError as exc:
        err_console.print(f"[red]Preset error:[/red] {exc}")
        raise typer.Exit(1)

    if p.target == "resume":
        cmd_build_resume(
            preset_name=name,
            template=None,
            cards_arg=None,
            tags=None,
            types=None,
            since=None,
            until=None,
            max_items=None,
            lang=None,
            jd=None,
            tone=None,
            show_llm_diff=False,
            no_cache=False,
            out=out,
            dry_run=dry_run,
            verbose=verbose,
        )
    elif p.target == "portfolio":
        cmd_build_portfolio(
            preset_name=name,
            cards_arg=None,
            tags=None,
            types=None,
            since=None,
            until=None,
            max_items=None,
            layout=None,
            include_narrative=True,
            cover_title=None,
            cover_subtitle=None,
            out=out,
            dry_run=dry_run,
            verbose=verbose,
        )
    else:
        err_console.print(f"[red]Unknown preset target:[/red] {p.target!r}")
        raise typer.Exit(1)


@preset_app.command("save")
def cmd_preset_save(
    name: str = typer.Argument(..., help="Preset name to save"),
):
    """Save the most recent build arguments as a named preset."""
    from .preset import PresetError, save_preset_from_cache

    try:
        dest = save_preset_from_cache(name, REPO_ROOT / "presets", REPO_ROOT / ".cache")
    except PresetError as exc:
        err_console.print(f"[red]Preset save error:[/red] {exc}")
        raise typer.Exit(1)
    console.print(f"[green]Preset saved:[/green] {dest.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# pcli llm
# ---------------------------------------------------------------------------


@llm_app.command("tailor")
def cmd_llm_tailor(
    cards_arg: str = typer.Option(..., "--cards", help="Comma-separated card ids"),
    jd: str = typer.Option(..., "--jd", help="Job description file path or '-' for stdin"),
    tone: str = typer.Option("formal", "--tone", help="Rewrite tone: formal|founder|technical"),
    lang: str = typer.Option("en", "--lang", help="Language: en or ko"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Force LLM call, bypass cache"),
):
    """Score and rewrite selected cards against a job description."""
    if lang not in VALID_LANGS:
        raise typer.BadParameter(f"must be one of {sorted(VALID_LANGS)}", param_hint="'--lang'")
    if tone not in VALID_TONES:
        raise typer.BadParameter(f"must be one of {sorted(VALID_TONES)}", param_hint="'--tone'")

    from .llm import LLMError, read_jd, rewrite_summary, score_cards

    try:
        jd_text = read_jd(jd)
    except LLMError as exc:
        err_console.print(f"[red]JD error:[/red] {exc}")
        raise typer.Exit(1)

    repo = _repo()
    ids = {s.strip() for s in cards_arg.split(",")}
    cards = [c for c in repo.cards if c.id in ids]
    missing = ids - {c.id for c in cards}
    if missing:
        err_console.print(f"[red]Cards not found:[/red] {', '.join(sorted(missing))}")
        raise typer.Exit(1)

    cache_dir = REPO_ROOT / ".cache" / "llm"
    try:
        scored = score_cards(cards, jd_text, lang=lang, cache_dir=cache_dir, no_cache=no_cache)
    except LLMError as exc:
        err_console.print(f"[red]LLM error:[/red] {exc}")
        raise typer.Exit(2)

    for card, score, reason in scored:
        try:
            new_summary = rewrite_summary(
                card, jd_text, tone=tone, lang=lang, cache_dir=cache_dir, no_cache=no_cache
            )
        except LLMError as exc:
            new_summary = f"[rewrite failed: {exc}]"
        original = card.summary_ko if lang == "ko" and card.summary_ko else card.summary
        console.print(f"\n[bold cyan]{card.id}[/bold cyan]  score={score:.2f}  {reason}")
        console.print(f"  [dim]before:[/dim] {original}")
        console.print(f"  [green]after: [/green] {new_summary}")


@llm_app.command("suggest")
def cmd_llm_suggest(
    from_file: str = typer.Option(..., "--from", help="Text file path or '-' for stdin"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Force LLM call, bypass cache"),
):
    """Suggest card frontmatter YAML from raw text (notes, README, etc.)."""
    import yaml as _yaml

    from .llm import LLMError, read_jd, suggest_card_from_text

    try:
        text = read_jd(from_file)
    except LLMError as exc:
        err_console.print(f"[red]File error:[/red] {exc}")
        raise typer.Exit(1)

    try:
        data = suggest_card_from_text(
            text, cache_dir=REPO_ROOT / ".cache" / "llm", no_cache=no_cache
        )
    except LLMError as exc:
        err_console.print(f"[red]LLM error:[/red] {exc}")
        raise typer.Exit(2)

    console.print(_yaml.dump(data, allow_unicode=True, sort_keys=False), end="")


if __name__ == "__main__":
    app()
