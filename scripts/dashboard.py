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
_DATE_RE = re.compile(r"\b(20\d{2})[-/](0[1-9]|1[0-2])\b")
_URL_RE = re.compile(r"https?://\S+")
_METRIC_RE = re.compile(r"\b\d+(?:\.\d+)?[kKmMbBx%]")

REPO_ROOT = Path(__file__).parents[1]
app = Flask(__name__, template_folder="templates", static_folder="static")


def _load_dotenv(path: Path) -> None:
    """Load KEY=value pairs from a .env file without overwriting existing env vars."""
    if not path.exists():
        return
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.split("#")[0].strip()  # strip inline comments
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            if not key or key in os.environ:
                continue
            os.environ[key] = val
    except Exception:
        pass  # malformed .env must not prevent startup


_load_dotenv(REPO_ROOT / ".env")
_load_dotenv(REPO_ROOT / ".env.local")


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

    post = fm.Post(content="")
    post.metadata = meta
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

    if "visuals" in incoming_fields:
        repo_resolved = REPO_ROOT.resolve()
        for v in incoming_fields["visuals"] or []:
            if isinstance(v, dict) and "path" in v:
                vpath = v["path"]
                if Path(vpath).is_absolute():
                    err = f"visual path must be relative: {vpath}"
                    return jsonify({"ok": False, "error": err}), 422
                candidate = (REPO_ROOT / vpath).resolve()
                if not candidate.is_relative_to(repo_resolved):
                    err = f"visual path outside repo: {vpath}"
                    return jsonify({"ok": False, "error": err}), 422
                if not candidate.exists():
                    err = f"visual path does not exist: {vpath}"
                    return jsonify({"ok": False, "error": err}), 422

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


def _title_to_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug or not _KEBAB_RE.match(slug):
        return "studio-draft"
    if slug[0].isdigit():
        slug = f"draft-{slug}"
    return slug


_TEAM_RE = re.compile(
    r"\b(?:we|team|our|collaborated|together|co-)\b"
    r"|(?:팀|함께|공동|협업|같이)"
    r"|우리(?=[\s가는도와의팀들]|$)",  # 우리 only as pronoun; not inside org names like 우리은행
    re.IGNORECASE,
)

_IDENTITY_RE = re.compile(
    r"\b(?:university|college|school|born|native|hometown|undergraduate|graduate|alumni"
    r"|nationality|birth|ethnicity)"
    r"|(?:대학교|대학원|출신|고향|학교|생년|출생|국적)",
    re.IGNORECASE,
)


def _build_safe_projection(cards: list, blind_hiring: bool = False) -> dict:
    """Build unified server-owned data projection from selected live cards.

    In blind mode, assigns opaque card refs (C1, C2, ...) as source_card_id to prevent
    canonical IDs from entering provider payloads or rendered previews. Screens all card
    fields (title, summary, metrics, evidence) with _IDENTITY_RE under blind_hiring=True.

    Returns dict with: fact_ledger, selected_cards, personal_facts, safe_titles,
    has_usable_facts, any_redacted, missing_info_additions, _provenance.
    _provenance is server-internal only (opaque_ref → canonical_id) and must not be serialized.
    """
    fact_ledger: list[dict] = []
    any_redacted = False
    card_counter = 0
    provenance: dict[str, str] = {}
    n = 0
    for c in cards:
        title_text = c.title or ""
        summary_text = c.summary or ""
        title_flagged = blind_hiring and bool(_IDENTITY_RE.search(title_text))
        summary_flagged = blind_hiring and bool(_IDENTITY_RE.search(summary_text))
        if title_flagged:
            any_redacted = True
        if summary_flagged:
            any_redacted = True
        safe_metrics: list[str] = []
        for m in list(c.metrics or [])[:2]:
            m_text = str(m)
            if blind_hiring and bool(_IDENTITY_RE.search(m_text)):
                any_redacted = True
            else:
                safe_metrics.append(m_text)
        safe_urls: list[str] = []
        for ev in list(c.evidence or [])[:2]:
            url = (
                ev.url
                if hasattr(ev, "url")
                else (ev.get("url", "") if isinstance(ev, dict) else "")
            )
            if url:
                if blind_hiring and bool(_IDENTITY_RE.search(url)):
                    any_redacted = True
                else:
                    safe_urls.append(url)
        has_clean_title = not title_flagged and bool(title_text)
        has_clean_summary = not summary_flagged and bool(summary_text)
        card_has_usable = (
            has_clean_title or has_clean_summary or bool(safe_metrics) or bool(safe_urls)
        )
        if not card_has_usable:
            continue
        card_counter += 1
        card_ref = f"C{card_counter}" if blind_hiring else c.id
        if blind_hiring:
            provenance[card_ref] = c.id
        # Activity entry: safe title, or opaque display label when title was redacted.
        activity_text = title_text if has_clean_title else f"Evidence {card_ref}"
        n += 1
        fact_ledger.append(
            {"id": f"F{n}", "kind": "activity", "text": activity_text, "source_card_id": card_ref}
        )
        if has_clean_summary:
            n += 1
            fact_ledger.append(
                {
                    "id": f"F{n}",
                    "kind": "summary",
                    "text": summary_text[:100],
                    "source_card_id": card_ref,
                }
            )
        for m_text in safe_metrics:
            n += 1
            fact_ledger.append(
                {"id": f"F{n}", "kind": "metric", "text": m_text, "source_card_id": card_ref}
            )
        for url in safe_urls:
            n += 1
            fact_ledger.append(
                {"id": f"F{n}", "kind": "evidence", "text": url, "source_card_id": card_ref}
            )
    has_usable_facts = bool(fact_ledger)
    personal_facts = _ledger_to_personal_facts(fact_ledger)
    selected_cards = _ledger_to_selected_cards(fact_ledger)
    safe_titles = [e["text"] for e in fact_ledger if e["kind"] == "activity"]
    missing_info_additions: list[dict] = []
    if blind_hiring:
        missing_info_additions.append(
            {
                "code": "BLIND_HIRING_REVIEW",
                "message": "Review output to confirm it meets blind-hiring requirements.",
            }
        )
        if any_redacted:
            missing_info_additions.append(
                {
                    "code": "BLIND_HIRING_PERSONAL_IDENTIFIERS",
                    "message": (
                        "Card content contains education/background identifiers "
                        "that were excluded from the blind-hiring preview."
                    ),
                }
            )
    return {
        "fact_ledger": fact_ledger,
        "selected_cards": selected_cards,
        "personal_facts": personal_facts,
        "safe_titles": safe_titles,
        "has_usable_facts": has_usable_facts,
        "any_redacted": any_redacted,
        "missing_info_additions": missing_info_additions,
        "_provenance": provenance,
    }


def _sanitize_advisory(advisory: dict, blind_hiring: bool) -> tuple[dict, list[dict]]:
    """Sanitize all provider-derived advisory strings for blind-hiring compliance.

    Returns (safe_advisory_dict, new_missing_info_items_to_append).
    When blind_hiring is False, returns advisory fields normalised but unchanged.
    """
    raw_missing = [
        m for m in (advisory.get("missing_info") or []) if isinstance(m, dict) and "code" in m
    ]
    raw_guidance = [g for g in (advisory.get("ai_guidance") or []) if isinstance(g, str)]
    if not blind_hiring:
        return {
            "question_intent": str(advisory.get("question_intent") or ""),
            "competency_target": str(advisory.get("competency_target") or ""),
            "missing_info": raw_missing,
            "ai_guidance": raw_guidance,
        }, []
    adv_redacted = False
    new_warnings: list[dict] = []
    question_intent = str(advisory.get("question_intent") or "")
    if _IDENTITY_RE.search(question_intent):
        question_intent = "Question interpretation withheld under blind-hiring policy."
        adv_redacted = True
    competency_target = str(advisory.get("competency_target") or "")
    if _IDENTITY_RE.search(competency_target):
        competency_target = "Competency interpretation withheld under blind-hiring policy."
        adv_redacted = True
    safe_missing: list[dict] = []
    for mi in raw_missing:
        if _IDENTITY_RE.search(mi.get("message", "")):
            safe_missing.append(
                {"code": mi["code"], "message": "Content withheld under blind-hiring policy."}
            )
            adv_redacted = True
        else:
            safe_missing.append(mi)
    guidance_clean = [g for g in raw_guidance if not _IDENTITY_RE.search(g)]
    if len(guidance_clean) < len(raw_guidance):
        new_warnings.append(
            {
                "code": "BLIND_HIRING_GUIDANCE_REDACTED",
                "message": (
                    "Some AI guidance contained excluded background identifiers and was withheld."
                ),
            }
        )
    if adv_redacted:
        new_warnings.append(
            {
                "code": "BLIND_HIRING_ADVISORY_REDACTED",
                "message": (
                    "Some AI advisory content contained excluded background "
                    "identifiers and was withheld."
                ),
            }
        )
    return {
        "question_intent": question_intent,
        "competency_target": competency_target,
        "missing_info": safe_missing,
        "ai_guidance": guidance_clean,
    }, new_warnings


def _build_target_context_used(tc: dict) -> list[str]:
    """Build target_context_used list from submitted target context dict."""
    result: list[str] = []
    if tc.get("organization"):
        result.append(f"Organization: {tc['organization']}")
    if tc.get("role"):
        result.append(f"Role: {tc['role']}")
    if tc.get("job_description"):
        result.append("Job description provided")
    if tc.get("question"):
        result.append(f"Question: {tc['question']}")
    if tc.get("competency"):
        result.append(f"Competency: {tc['competency']}")
    if tc.get("blind_hiring"):
        result.append("Blind-hiring restrictions applied")
    return result


def _compose_answer_draft(output_type: str, safe_titles: list[str], tc: dict) -> str:
    """Compose answer draft from server-authoritative card titles and submitted context only."""
    card_titles = ", ".join(safe_titles) if safe_titles else "selected cards"
    organization = tc.get("organization", "")
    role = tc.get("role", "")
    question = tc.get("question", "")
    competency = tc.get("competency", "")
    if output_type == "cover_letter":
        org_str = f" at {organization}" if organization else ""
        role_str = f"the {role} position" if role else "this position"
        return (
            f"I am writing to express my interest in {role_str}{org_str}. "
            f"My experience with {card_titles} demonstrates capabilities relevant to this role."
        )
    q_intro = f'Regarding "{question[:80]}": ' if question else ""
    blind_hiring = bool(tc.get("blind_hiring", False))
    if blind_hiring and competency and bool(_IDENTITY_RE.search(competency)):
        comp_str = ""
    else:
        comp_str = f" This reflects {competency}." if competency else ""
    return (
        f"{q_intro}Through my work on {card_titles}, "
        f"I developed the relevant capabilities.{comp_str}"
    )


def _mock_refine(raw_text: str, intent: str) -> dict:
    lines = raw_text.strip().splitlines()
    title = lines[0].strip() if lines else "Untitled"

    dates = _DATE_RE.findall(raw_text)
    urls = _URL_RE.findall(raw_text)
    metric_hits = _METRIC_RE.findall(raw_text)
    has_visual_kw = any(
        w in raw_text.lower()
        for w in ("screenshot", "diagram", "image", "figure", "photo", "visual")
    )
    has_team_signal = bool(_TEAM_RE.search(raw_text))

    evidence = []
    for url in urls:
        ul = url.lower()
        if "github.com" in ul or "gitlab.com" in ul:
            kind = "repo"
        elif "demo" in ul or url.startswith("https://app."):
            kind = "demo"
        else:
            kind = "other"
        evidence.append({"type": kind, "url": url})

    metrics = list(metric_hits[:3])

    if dates:
        year, month = dates[0]
        period_start: str | None = f"{year}-{month}-01"
    else:
        period_start = None

    # Source facts: items directly present in raw text
    source_facts: list[str] = []
    if title:
        source_facts.append(f"Activity: {title}")
    for year, month in dates:
        source_facts.append(f"Date: {year}-{month}")
    for url in urls:
        source_facts.append(f"Link: {url}")
    for m in metric_hits:
        source_facts.append(f"Metric: {m}")

    # Assumptions: interpretations beyond what is stated
    assumptions: list[str] = []
    if not dates:
        assumptions.append("Project period is not provided and needs confirmation.")
    if has_team_signal:
        assumptions.append("Team activity detected; individual contribution assumed.")

    missing_info = []
    if not dates:
        missing_info.append(
            {"code": "MISSING_PERIOD", "message": "No date found — when did this happen?"}
        )
    if not metric_hits:
        missing_info.append(
            {
                "code": "MISSING_METRICS",
                "message": "No metrics found — add numbers, percentages, or multipliers.",
            }
        )
    if not evidence:
        missing_info.append(
            {
                "code": "MISSING_EVIDENCE",
                "message": "No URLs found — add a repo, demo, or reference link.",
            }
        )
    if not has_visual_kw:
        missing_info.append(
            {
                "code": "MISSING_VISUAL",
                "message": "No visual context — add a screenshot, diagram, or image reference.",
            }
        )
    if has_team_signal:
        missing_info.append(
            {
                "code": "CONTRIBUTION_UNCLEAR",
                "message": "Team activity detected — what was your individual contribution?",
            }
        )

    draft: dict[str, Any] = {
        "id": _title_to_slug(title),
        "title": title,
        "type": "project",
        "period_start": period_start,
        "status": "draft",
        "visibility": "public",
        "summary": title,
        "source_facts": source_facts,
        "assumptions": assumptions,
        "tags": {"domain": [], "skill": [], "audience": []},
        "metrics": metrics,
        "evidence": evidence,
        "visuals": [],
        "links": [],
        "related": [],
    }

    if intent in ("resume", "both"):
        if metric_hits:
            draft["resume_bullet"] = f"• {title}: {metric_hits[0]}"
        else:
            draft["resume_bullet"] = f"• {title}"

    if intent in ("portfolio", "both"):
        outcome = metric_hits[0] if metric_hits else "Outcome to be detailed."
        draft["portfolio_body"] = (
            f"## Problem\n\nChallenge: {title}.\n\n"
            f"## Framing\n\nScope: {title}.\n\n"
            f"## Approach\n\nApproached this by breaking down the challenge systematically.\n\n"
            f"## Outcome\n\n{outcome}\n\n"
            f"## Insight\n\nKey learning from this work."
        )

    return {"ok": True, "draft": draft, "missing_info": missing_info}


@app.route("/dashboard")
def dashboard() -> str:
    return index()


@app.route("/studio")
def studio() -> str:
    return render_template("studio.html")


@app.route("/api/studio/ai-status")
def api_studio_ai_status():
    try:
        from scripts.llm import _SUPPORTED_PROVIDERS, is_api_key_configured, resolve_provider_config

        cfg = resolve_provider_config()
        configured = (
            is_api_key_configured(cfg["api_key"]) and cfg["provider"] in _SUPPORTED_PROVIDERS
        )
        mode = "llm" if configured else "mock"
        return jsonify(
            {
                "ok": True,
                "configured": configured,
                "provider": cfg["provider"],
                "mode": mode,
                "model": cfg["model"] if configured else None,
            }
        )
    except Exception:
        pass  # llm.py import failure → safe fallback
    return jsonify(
        {"ok": True, "configured": False, "provider": "anthropic", "mode": "mock", "model": None}
    )


@app.route("/api/studio/ai-check", methods=["POST"])
def api_studio_ai_check():
    try:
        from scripts.llm import LLMConnectionError, check_provider_connection

        result = check_provider_connection()
        return jsonify(
            {
                "ok": True,
                "connected": True,
                "provider": result["provider"],
                "model": result["model"],
                "message": "Connection check passed",
            }
        )
    except LLMConnectionError as exc:
        from scripts.llm import resolve_provider_config

        cfg = resolve_provider_config()
        return jsonify(
            {
                "ok": False,
                "connected": False,
                "provider": cfg["provider"],
                "model": cfg["model"],
                "error_code": exc.error_code,
                "message": str(exc),
            }
        )
    except Exception:
        return jsonify(
            {
                "ok": False,
                "connected": False,
                "provider": "unknown",
                "model": None,
                "error_code": "provider_error",
                "message": "Connection check failed.",
            }
        )


@app.route("/api/studio/refine", methods=["POST"])
def api_studio_refine():
    data = request.get_json(force=True) or {}
    raw_text: str = data.get("raw_text", "")
    intent: str = data.get("intent", "")

    if not raw_text or not raw_text.strip():
        return jsonify({"ok": False, "error": "raw_text is required"}), 400
    if intent not in ("resume", "portfolio", "both"):
        return jsonify({"ok": False, "error": "intent must be resume, portfolio, or both"}), 400

    try:
        from scripts.llm import _SUPPORTED_PROVIDERS, is_api_key_configured, resolve_provider_config

        cfg = resolve_provider_config()
        can_try_llm = (
            is_api_key_configured(cfg["api_key"]) and cfg["provider"] in _SUPPORTED_PROVIDERS
        )
    except Exception:
        can_try_llm = False

    refine_fallback_reason: str | None = None
    if can_try_llm:
        try:
            from scripts.llm import studio_refine_llm

            return jsonify(studio_refine_llm(raw_text, intent))
        except Exception as exc:
            try:
                from scripts.llm import _classify_exc

                refine_fallback_reason = _classify_exc(exc).error_code
            except Exception:
                refine_fallback_reason = "provider_error"
    else:
        refine_fallback_reason = "not_configured"

    result = _mock_refine(raw_text, intent)
    result["draft"]["refine_source"] = "mock"
    result["draft"]["fallback_reason"] = refine_fallback_reason
    return jsonify(result)


@app.route("/api/studio/save", methods=["POST"])
def api_studio_save():
    from scripts.card import Card

    data = request.get_json(force=True) or {}
    draft = data.get("draft")
    if not isinstance(draft, dict):
        return jsonify({"ok": False, "error": "draft is required"}), 400

    title = draft.get("title", "")
    if not title:
        return jsonify({"ok": False, "error": "draft.title is required"}), 400

    card_id = _title_to_slug(title)
    period_start = draft.get("period_start") or None
    if not period_start:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": (
                        "draft.period_start is required — confirm when this happened before saving"
                    ),
                }
            ),
            422,
        )

    target = _new_card_path(card_id, period_start)
    if target is None:
        return jsonify({"ok": False, "error": "could not resolve card path"}), 400

    cards_dir = (REPO_ROOT / "cards").resolve()
    if any(cards_dir.glob(f"????-??-{card_id}.mdx")):
        return jsonify({"ok": False, "error": f"card id {card_id!r} already exists"}), 409

    meta: dict[str, Any] = {
        "id": card_id,
        "title": title,
        "type": draft.get("type", "project"),
        "period": {"start": period_start, "end": None},
        "status": "draft",
        "visibility": "public",
        "tags": draft.get("tags") or {"domain": [], "skill": [], "audience": []},
        "metrics": draft.get("metrics") or [],
        "summary": draft.get("summary") or "",
        "summary_ko": None,
        "narrative": draft.get("resume_bullet") or None,
        "visuals": [],
        "evidence": draft.get("evidence") or [],
        "links": [],
        "related": [],
    }

    try:
        Card.model_validate(meta)
    except PydanticValidationError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 422

    body_content = draft.get("portfolio_body") or ""
    post = fm.Post(content=body_content)
    post.metadata = meta
    _write_card_atomic(target, post)

    return jsonify({"ok": True, "id": card_id, "path": str(target.relative_to(REPO_ROOT))}), 201


def _load_live_cards(card_ids: list, repo_root: Path) -> tuple[list, tuple | None]:
    """Load validated live cards. Returns (cards, None) or ([], (error_dict, status_code))."""
    from scripts.card import CardRepo

    repo = CardRepo(repo_root)
    all_cards = {c.id: c for c in repo.cards}
    loaded = []
    for cid in card_ids:
        if cid not in all_cards:
            return [], ({"ok": False, "error": f"card {cid!r} not found"}, 404)
        card = all_cards[cid]
        if card.status != "live":
            msg = f"card {cid!r} is not live (status: {card.status})"
            return [], ({"ok": False, "error": msg}, 422)
        loaded.append(card)
    return loaded, None


def _ledger_to_personal_facts(ledger: list[dict]) -> list[str]:
    """Derive legacy personal_facts list from a fact ledger for response compatibility."""
    _prefix = {
        "activity": "Activity",
        "summary": "Summary",
        "metric": "Metric",
        "evidence": "Evidence",
    }
    return [f"{_prefix.get(e['kind'], e['kind'].title())}: {e['text']}" for e in ledger]


def _ledger_to_selected_cards(ledger: list[dict]) -> list[dict]:
    """Build server-derived selected_cards from ledger activity entries."""
    seen: set[str] = set()
    result = []
    for e in ledger:
        if e["kind"] == "activity" and e["source_card_id"] not in seen:
            seen.add(e["source_card_id"])
            metrics = [
                x["text"]
                for x in ledger
                if x["kind"] == "metric" and x["source_card_id"] == e["source_card_id"]
            ]
            reason = (
                f"Demonstrates {e['text']}: {metrics[0]}"
                if metrics
                else f"Demonstrates {e['text']}"
            )
            result.append(
                {"id": e["source_card_id"], "display_title": e["text"], "selection_reason": reason}
            )
    return result


def _mock_application_preview(output_type: str, projection: dict, target_context: dict) -> dict:
    question = target_context.get("question", "")
    competency = target_context.get("competency", "")
    char_limit = target_context.get("character_limit")

    fact_ledger = projection["fact_ledger"]
    selected_cards_info = projection["selected_cards"]
    personal_facts = projection["personal_facts"]
    safe_titles = projection["safe_titles"]
    missing_info: list[dict] = list(projection["missing_info_additions"])
    target_context_used = _build_target_context_used(target_context)
    selected_facts = [e["id"] for e in fact_ledger]

    question_intent = (
        f"Assessing: {question[:100]}" if output_type == "application_answer" and question else ""
    )
    competency_target = competency
    assumptions: list[str] = []

    draft = _compose_answer_draft(output_type, safe_titles, target_context)

    if char_limit and len(draft) > char_limit:
        draft = draft[:char_limit]
        assumptions.append("Draft truncated to fit the character limit.")

    char_count = len(draft)
    within_limit = (char_count <= char_limit) if char_limit else None

    return {
        "output_type": output_type,
        "fact_ledger": fact_ledger,
        "selected_facts": selected_facts,
        "question_intent": question_intent,
        "competency_target": competency_target,
        "selected_cards": selected_cards_info,
        "personal_facts": personal_facts,
        "target_context_used": target_context_used,
        "assumptions": assumptions,
        "missing_info": missing_info,
        "answer_draft": draft,
        "draft_provenance": "server_composed",
        "ai_guidance": [],
        "character_count": char_count,
        "character_limit": char_limit,
        "within_limit": within_limit,
    }


@app.route("/api/studio/application-preview", methods=["POST"])
def api_studio_application_preview():
    data = request.get_json(force=True) or {}
    output_type = data.get("output_type", "")
    card_ids = data.get("card_ids") or []
    target_context: dict = data.get("target_context") or {}

    _valid_types = ("cover_letter", "application_answer")
    if output_type not in _valid_types:
        _msg = "output_type must be cover_letter or application_answer"
        return jsonify({"ok": False, "error": _msg}), 400
    if not isinstance(card_ids, list) or not card_ids:
        return jsonify({"ok": False, "error": "card_ids must be a non-empty list"}), 400

    if output_type == "cover_letter":
        _ctx_fields = ("organization", "role", "job_description")
        if not any(target_context.get(f) for f in _ctx_fields):
            _msg = "cover_letter requires organization, role, or job_description"
            return jsonify({"ok": False, "error": _msg}), 400
    if output_type == "application_answer":
        if not target_context.get("question"):
            return jsonify({"ok": False, "error": "application_answer requires question"}), 400

    char_limit = target_context.get("character_limit")
    if char_limit is not None:
        if not isinstance(char_limit, int) or not (1 <= char_limit <= 5000):
            _msg = "character_limit must be an integer from 1 to 5000"
            return jsonify({"ok": False, "error": _msg}), 400

    cards, err = _load_live_cards(card_ids, REPO_ROOT)
    if err is not None:
        return jsonify(err[0]), err[1]

    fallback_reason: str | None = None
    try:
        from scripts.llm import _SUPPORTED_PROVIDERS, is_api_key_configured, resolve_provider_config

        cfg = resolve_provider_config()
        can_try_llm = (
            is_api_key_configured(cfg["api_key"]) and cfg["provider"] in _SUPPORTED_PROVIDERS
        )
    except Exception:
        can_try_llm = False

    _blind = bool(target_context.get("blind_hiring", False))
    projection = _build_safe_projection(cards, _blind)

    if _blind and not projection["has_usable_facts"]:
        return jsonify(
            {
                "ok": False,
                "error": (
                    "All submitted cards were excluded under blind-hiring policy. "
                    "Submit cards without education or background identifiers."
                ),
            }
        ), 422

    if can_try_llm:
        try:
            from scripts.llm import application_preview_llm

            llm_result = application_preview_llm(
                output_type, projection["fact_ledger"], target_context
            )
        except Exception as exc:
            try:
                from scripts.llm import _classify_exc

                fallback_reason = _classify_exc(exc).error_code
            except Exception:
                fallback_reason = "provider_error"
        else:
            advisory = llm_result.get("advisory", {})
            _valid_ids_set = {e["id"] for e in projection["fact_ledger"]}
            raw_ids = advisory.get("selected_fact_ids") or []
            _filtered_ids = [fid for fid in raw_ids if fid in _valid_ids_set]
            if not _filtered_ids:
                sel_ids = [e["id"] for e in projection["fact_ledger"]]
            else:
                # Expand selection to include the activity fact of each represented card.
                _sel_card_ids = {
                    e["source_card_id"]
                    for e in projection["fact_ledger"]
                    if e["id"] in set(_filtered_ids)
                }
                _expanded = set(_filtered_ids) | {
                    e["id"]
                    for e in projection["fact_ledger"]
                    if e["kind"] == "activity" and e["source_card_id"] in _sel_card_ids
                }
                sel_ids = [e["id"] for e in projection["fact_ledger"] if e["id"] in _expanded]
            sel_ledger = [e for e in projection["fact_ledger"] if e["id"] in set(sel_ids)]
            _safe_titles = [e["text"] for e in sel_ledger if e["kind"] == "activity"]
            if not _safe_titles:
                _safe_titles = [
                    e["text"] for e in projection["fact_ledger"] if e["kind"] == "activity"
                ]
            _char_limit = target_context.get("character_limit")
            _draft = _compose_answer_draft(output_type, _safe_titles, target_context)
            _assumptions: list[str] = []
            if _char_limit and len(_draft) > _char_limit:
                _draft = _draft[:_char_limit]
                _assumptions.append("Draft truncated to fit the character limit.")
            safe_adv, adv_warnings = _sanitize_advisory(advisory, _blind)
            _missing = (
                list(safe_adv["missing_info"])
                + list(projection["missing_info_additions"])
                + adv_warnings
            )
            preview = {
                "output_type": output_type,
                "fact_ledger": projection["fact_ledger"],
                "selected_facts": sel_ids,
                "question_intent": safe_adv["question_intent"],
                "competency_target": safe_adv["competency_target"],
                "selected_cards": _ledger_to_selected_cards(
                    sel_ledger or projection["fact_ledger"]
                ),
                "personal_facts": _ledger_to_personal_facts(projection["fact_ledger"]),
                "target_context_used": _build_target_context_used(target_context),
                "assumptions": _assumptions,
                "missing_info": _missing,
                "answer_draft": _draft,
                "draft_provenance": "server_composed",
                "ai_guidance": safe_adv["ai_guidance"],
                "character_count": len(_draft),
                "character_limit": _char_limit,
                "within_limit": (len(_draft) <= _char_limit) if _char_limit else None,
                "refine_source": "llm",
                "fallback_reason": None,
            }
            return jsonify({"ok": True, "preview": preview})
    else:
        fallback_reason = "not_configured"

    preview = _mock_application_preview(output_type, projection, target_context)
    preview["refine_source"] = "mock"
    preview["fallback_reason"] = fallback_reason
    return jsonify({"ok": True, "preview": preview})


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    app.run(host=host, port=port, debug=debug)
