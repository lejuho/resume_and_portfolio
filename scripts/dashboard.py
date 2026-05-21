"""Local dashboard server for browsing, filtering, and building cards."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import date as _date
from pathlib import Path
from typing import Any

import frontmatter as fm
from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError as PydanticValidationError

_OUTPUT_PATH_RE = re.compile(
    r"output[/\\](resumes|portfolios)[/\\]\S+\.(pdf|pptx)",
    re.IGNORECASE,
)
_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

REPO_ROOT = Path(__file__).parents[1]
app = Flask(__name__, template_folder="templates", static_folder="static")


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


def _safe_card_path(card_id: str) -> Path | None:
    """Resolve card path and verify it stays within cards/. Returns None on traversal."""
    if not _KEBAB_RE.match(card_id):
        return None
    cards_dir = (REPO_ROOT / "cards").resolve()
    # Find the matching file (any YYYY-MM-<id>.mdx)
    matches = list(cards_dir.glob(f"????-??-{card_id}.mdx"))
    if not matches:
        return None
    target = matches[0].resolve()
    if not target.is_relative_to(cards_dir):
        return None
    return target


def _new_card_path(card_id: str, start_date: str) -> Path | None:
    """Compute new card path. Returns None if traversal detected."""
    if not _KEBAB_RE.match(card_id):
        return None
    cards_dir = (REPO_ROOT / "cards").resolve()
    try:
        d = _date.fromisoformat(start_date)
    except ValueError:
        return None
    filename = f"{d.strftime('%Y-%m')}-{card_id}.mdx"
    target = (cards_dir / filename).resolve()
    if not target.is_relative_to(cards_dir):
        return None
    return target


def _write_card_atomic(path: Path, post: Any) -> None:
    """Write frontmatter post to path atomically via temp file."""
    content = fm.dumps(post)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


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


@app.route("/api/cards/<card_id>", methods=["GET"])
def api_card_get(card_id: str):
    if not _KEBAB_RE.match(card_id):
        return jsonify({"ok": False, "error": "invalid card id"}), 400

    path = _safe_card_path(card_id)
    if path is None:
        return jsonify({"ok": False, "error": "not found"}), 404

    post = fm.load(str(path))
    fields = dict(post.metadata)
    resp: dict[str, Any] = {"ok": True, "id": card_id, "fields": fields, "body": post.content}
    if "visuals" in fields:
        hints: dict[str, bool] = {}
        for v in fields["visuals"] or []:
            if isinstance(v, dict) and "path" in v:
                hints[v["path"]] = (REPO_ROOT / v["path"]).exists()
        resp["visual_hints"] = hints
    return jsonify(resp)


@app.route("/api/cards", methods=["POST"])
def api_card_create():
    from scripts.card import Card

    data = request.get_json(force=True) or {}
    card_id = data.get("id", "")
    start_date = data.get("period_start", "") or data.get("start", "")

    if not _KEBAB_RE.match(card_id):
        return jsonify({"ok": False, "error": "id must be kebab-case"}), 400

    target = _new_card_path(card_id, start_date)
    if target is None:
        return jsonify({"ok": False, "error": "invalid id or start date"}), 400

    cards_dir = (REPO_ROOT / "cards").resolve()
    if any(cards_dir.glob(f"????-??-{card_id}.mdx")):
        return jsonify({"ok": False, "error": f"card id {card_id!r} already exists"}), 409

    meta: dict[str, Any] = {
        "id": card_id,
        "title": data.get("title") or card_id,
        "type": data.get("type", "project"),
        "period": {"start": start_date, "end": None},
        "status": data.get("status", "draft"),
        "visibility": data.get("visibility", "public"),
        "tags": {"domain": [], "skill": [], "audience": []},
        "metrics": [],
        "summary": data.get("summary", ""),
        "summary_ko": None,
        "narrative": None,
        "visuals": [],
        "evidence": [],
        "links": [],
        "related": [],
    }

    try:
        Card.model_validate(meta)
    except PydanticValidationError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 422

    post = fm.Post(content="", metadata=meta)
    _write_card_atomic(target, post)
    return jsonify({"ok": True, "id": card_id, "path": str(target.relative_to(REPO_ROOT))}), 201


@app.route("/api/cards/<card_id>", methods=["PUT"])
def api_card_update(card_id: str):
    from scripts.card import Card

    if not _KEBAB_RE.match(card_id):
        return jsonify({"ok": False, "error": "invalid card id"}), 400

    path = _safe_card_path(card_id)
    if path is None:
        return jsonify({"ok": False, "error": "not found"}), 404

    data = request.get_json(force=True) or {}
    incoming_fields: dict = data.get("fields", {})
    body: str = data.get("body", "")

    if "id" in incoming_fields and incoming_fields["id"] != card_id:
        return jsonify({"ok": False, "error": "id is immutable; rename not supported"}), 400

    post = fm.load(str(path))
    # Deep-merge: update only keys present in incoming_fields
    merged = dict(post.metadata)
    for k, v in incoming_fields.items():
        merged[k] = v

    try:
        Card.model_validate(merged)
    except PydanticValidationError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 422

    post.metadata = merged
    post.content = body

    original = path.read_text(encoding="utf-8")
    try:
        _write_card_atomic(path, post)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"write failed: {exc}"}), 500

    updated = path.read_text(encoding="utf-8")
    if updated == original and not incoming_fields and not body:
        pass  # no-op update is fine

    return jsonify({"ok": True, "id": card_id, "path": str(path.relative_to(REPO_ROOT))})


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
