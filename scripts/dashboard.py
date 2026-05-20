"""Local dashboard server for browsing, filtering, and building cards."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

_OUTPUT_PATH_RE = re.compile(
    r"output[/\\](resumes|portfolios)[/\\]\S+\.(pdf|pptx)",
    re.IGNORECASE,
)

REPO_ROOT = Path(__file__).parents[1]
app = Flask(__name__, template_folder="templates")


def _parse_output_path(stdout: str) -> str | None:
    """Return the first output file path found in build stdout, or None."""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        lowered = line.lower()
        is_output = "resumes" in lowered or "portfolios" in lowered
        if is_output and lowered.endswith((".pdf", ".pptx")):
            m = _OUTPUT_PATH_RE.search(line)
            if m:
                return m.group(0)
            parts = line.split(": ", 1)
            return parts[-1].strip()
    return None


def _card_to_dict(card: Any) -> dict:
    tags: dict = {}
    if card.tags:
        try:
            tags = card.tags.model_dump()
        except Exception:
            pass
    return {
        "id": card.id,
        "title": card.title,
        "type": card.type,
        "status": card.status,
        "period_start": str(card.period.start) if card.period and card.period.start else None,
        "summary": card.summary or "",
        "tags": tags,
        "metrics_count": len(card.metrics or []),
        "evidence_count": len(card.evidence or []),
        "has_visuals": bool(card.visuals),
    }


@app.route("/")
def index() -> str:
    from scripts.card import CardRepo

    repo = CardRepo(REPO_ROOT)
    cards_json = json.dumps([_card_to_dict(c) for c in repo.cards])
    return render_template("dashboard.html", cards_json=cards_json, errors=repo.errors)


@app.route("/api/cards")
def api_cards():
    from scripts.card import CardRepo
    from scripts.select import filter_cards

    repo = CardRepo(REPO_ROOT)
    cards = filter_cards(
        repo.cards,
        types=request.args.get("types"),
        tags=request.args.get("tags"),
        since=request.args.get("since"),
        until=request.args.get("until"),
        status=request.args.get("status"),
        sort=request.args.get("sort", "date-desc"),
    )
    return jsonify([_card_to_dict(c) for c in cards])


@app.route("/api/build", methods=["POST"])
def api_build():
    data = request.get_json(force=True) or {}
    target = data.get("target", "resume")
    dry_run = bool(data.get("dry_run", True))
    selected_ids: list[str] = data.get("selected_ids") or []

    if target not in ("resume", "portfolio"):
        err = {
            "ok": False,
            "exit_code": 1,
            "stdout": "",
            "stderr": "Invalid target",
            "command": "",
            "output_path": None,
            "target": target,
            "dry_run": dry_run,
            "selected_ids": selected_ids,
        }
        return jsonify(err), 400

    cmd = ["uv", "run", "pcli", "build", target]
    if selected_ids:
        cmd += ["--cards", ",".join(str(i) for i in selected_ids)]
    if dry_run:
        cmd += ["--dry-run"]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        output_path = None if dry_run else _parse_output_path(result.stdout)
        return jsonify(
            {
                "ok": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "output_path": output_path,
                "target": target,
                "dry_run": dry_run,
                "selected_ids": selected_ids,
            }
        )
    except subprocess.TimeoutExpired:
        return jsonify(
            {
                "ok": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Build timed out after 120s",
                "command": " ".join(cmd),
                "output_path": None,
                "target": target,
                "dry_run": dry_run,
                "selected_ids": selected_ids,
            }
        )


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    app.run(host=host, port=port, debug=debug)
