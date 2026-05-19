"""Build the JSON context and invoke Typst to produce a PDF resume."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console

from .card import Card

console = Console()
err_console = Console(stderr=True)


def _load_profile(repo_root: Path) -> dict:
    for name in ("profile.yaml", "profile.example.yaml"):
        p = repo_root / name
        if p.exists():
            with p.open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def _card_to_dict(card: Card, lang: str) -> dict:
    summary = card.summary_ko if (lang == "ko" and card.summary_ko) else card.summary
    return {
        "id": card.id,
        "title": card.title,
        "type": card.type,
        "status": card.status,
        "period": {
            "start": card.period.start.isoformat(),
            "end": card.period.end.isoformat() if card.period.end else None,
        },
        "summary": summary.strip(),
        "metrics": card.metrics,
        "tags": {
            "domain": card.tags.domain,
            "skill": card.tags.skill,
            "audience": card.tags.audience,
        },
        "evidence": [{"type": e.type, "url": e.url} for e in card.evidence],
        "links": [{"label": ln.label, "url": ln.url} for ln in card.links],
    }


def build_resume(
    cards: list[Card],
    repo_root: Path,
    template_name: str = "default",
    lang: str = "en",
    out_path: Optional[Path] = None,
    verbose: bool = False,
) -> None:
    profile = _load_profile(repo_root)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_path = out_path or (repo_root / "output" / "resumes" / f"resume-{timestamp}.pdf")

    build_dir = repo_root / ".build"
    build_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    context = {
        "basics": profile.get("basics", {}),
        "education": profile.get("education", []),
        "cards": [_card_to_dict(c, lang) for c in cards],
        "meta": {
            "generated_at": timestamp,
            "template": template_name,
            "lang": lang,
            "card_count": len(cards),
        },
    }

    json_path = build_dir / "resume-data.json"
    json_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")

    if verbose:
        console.print(f"[dim]Wrote build context → {json_path}[/dim]")
        console.print(f"[dim]Selected cards: {[c.id for c in cards]}[/dim]")

    template_path = repo_root / "templates" / "resume" / f"{template_name}.typ"
    if not template_path.exists():
        err_console.print(
            f"[red]Template not found:[/red] {template_path}\n"
            "Create it under templates/resume/ or use --template default"
        )
        sys.exit(2)

    typst_bin = shutil.which("typst")
    if typst_bin is None:
        err_console.print(
            "[red]typst binary not found.[/red] "
            "Install from https://github.com/typst/typst/releases "
            "or run with --dry-run to skip rendering."
        )
        sys.exit(2)

    data_path_for_typst = os.path.relpath(json_path, start=template_path.parent).replace(
        os.sep, "/"
    )

    cmd = [
        typst_bin,
        "compile",
        "--root",
        str(repo_root),
        f"--input=data-path={data_path_for_typst}",
        f"--input=lang={lang}",
        str(template_path),
        str(out_path),
    ]

    if verbose:
        console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if verbose and result.stdout:
            console.print(result.stdout)
    except subprocess.CalledProcessError as exc:
        err_console.print("[red]Typst compile failed:[/red]")
        err_console.print(exc.stderr or exc.stdout or str(exc))
        sys.exit(2)

    console.print(f"[green]Resume written:[/green] {out_path}")
    console.print(f"[dim]{len(cards)} card(s) included[/dim]")
