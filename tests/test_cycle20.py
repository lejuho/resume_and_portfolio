"""Tests for cycle-20: Grounded Studio preview."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

import scripts.dashboard as dash_mod
import scripts.llm as llm_mod
from scripts.dashboard import app

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "cards").mkdir()
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _fake_llm_response(extra: dict | None = None) -> str:
    base = {
        "source_facts": ["Activity: Test Project", "Metric: 40%"],
        "assumptions": ["Solo contribution assumed."],
        "title": "Test Project",
        "type": "project",
        "summary": "A test project summary.",
        "problem": "Problem statement.",
        "framing": "Framing statement.",
        "approach": "Approach description.",
        "outcome": "Outcome achieved.",
        "insight": "Key insight.",
        "decisions_tradeoffs": "A notable tradeoff.",
        "tags": {"domain": ["web3"], "skill": ["python"], "audience": ["recruiter"]},
        "metrics": ["40%"],
        "evidence": [],
        "missing_info": [],
        "resume_bullet": "• Built Test Project achieving 40% improvement",
        "portfolio_body": "## Problem\n\nProblem.",
    }
    if extra:
        base.update(extra)
    return json.dumps(base)


def _fake_anthropic_client(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    c = MagicMock()
    c.messages.create.return_value = msg
    return c


# ── API: source_facts and assumptions always present ─────────────────────────


def test_mock_refine_has_source_facts_and_assumptions_resume(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post("/api/studio/refine", json={"raw_text": "Built a thing.", "intent": "resume"})
    body = rv.get_json()
    assert body["ok"] is True
    assert "source_facts" in body["draft"]
    assert "assumptions" in body["draft"]
    assert isinstance(body["draft"]["source_facts"], list)
    assert isinstance(body["draft"]["assumptions"], list)


def test_mock_refine_has_source_facts_and_assumptions_portfolio(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Built a thing.", "intent": "portfolio"}
    )
    body = rv.get_json()
    assert "source_facts" in body["draft"]
    assert "assumptions" in body["draft"]


def test_mock_refine_has_source_facts_and_assumptions_both(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post("/api/studio/refine", json={"raw_text": "Built a thing.", "intent": "both"})
    body = rv.get_json()
    assert "source_facts" in body["draft"]
    assert "assumptions" in body["draft"]


# ── Grounding: metric-free input produces no fabricated numeric claim ─────────


def test_mock_metric_free_bullet_has_no_fabricated_metric(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={"raw_text": "Built an internal dashboard for the ops team.", "intent": "resume"},
    )
    body = rv.get_json()
    bullet = body["draft"]["resume_bullet"]
    assert "measurable impact" not in bullet
    assert "result" not in bullet.lower() or "%" not in bullet


def test_mock_provided_metric_is_preserved_in_source_facts(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={"raw_text": "Optimised queries, reduced latency by 40%.", "intent": "both"},
    )
    body = rv.get_json()
    facts = body["draft"]["source_facts"]
    assert any("40%" in f for f in facts)


def test_mock_team_signal_adds_contribution_unclear(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={"raw_text": "Our team built the authentication module.", "intent": "both"},
    )
    body = rv.get_json()
    codes = [m["code"] for m in body["missing_info"]]
    assert "CONTRIBUTION_UNCLEAR" in codes


def test_mock_no_team_signal_no_contribution_unclear(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={"raw_text": "I built the authentication module.", "intent": "both"},
    )
    body = rv.get_json()
    codes = [m["code"] for m in body["missing_info"]]
    assert "CONTRIBUTION_UNCLEAR" not in codes


# ── Metamorphic: adding evidence URL satisfies the evidence gap ───────────────


def test_metamorphic_url_satisfies_evidence_gap(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    without_url = client.post(
        "/api/studio/refine", json={"raw_text": "Built a thing.", "intent": "both"}
    ).get_json()
    with_url = client.post(
        "/api/studio/refine",
        json={"raw_text": "Built a thing. https://github.com/example/repo", "intent": "both"},
    ).get_json()
    without_codes = [m["code"] for m in without_url["missing_info"]]
    with_codes = [m["code"] for m in with_url["missing_info"]]
    assert "MISSING_EVIDENCE" in without_codes
    assert "MISSING_EVIDENCE" not in with_codes


def test_metamorphic_resume_portfolio_share_source_facts(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    raw = "Reduced load time by 3x in 2024-06. https://github.com/example/perf"
    resume_body = client.post(
        "/api/studio/refine", json={"raw_text": raw, "intent": "resume"}
    ).get_json()
    portfolio_body = client.post(
        "/api/studio/refine", json={"raw_text": raw, "intent": "portfolio"}
    ).get_json()
    r_facts = set(resume_body["draft"]["source_facts"])
    p_facts = set(portfolio_body["draft"]["source_facts"])
    assert r_facts == p_facts


# ── Provider: Google structured response config is requested ──────────────────


def test_google_structured_response_config_requested(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-fake")
    monkeypatch.delenv("AI_MODEL", raising=False)

    captured: dict = {}

    def _fake_call(client, prompt, model, response_json=False):
        captured["response_json"] = response_json
        return _fake_llm_response()

    monkeypatch.setattr(llm_mod, "_call", _fake_call)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    studio_refine_llm("test project notes", "both", cache_dir=tmp_path)
    assert captured.get("response_json") is True


def test_anthropic_does_not_use_json_schema(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    captured: dict = {}

    def _fake_call(client, prompt, model, response_json=False):
        captured["response_json"] = response_json
        return _fake_llm_response()

    monkeypatch.setattr(llm_mod, "_call", _fake_call)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    studio_refine_llm("test project notes", "both", cache_dir=tmp_path)
    assert captured.get("response_json") is False


def test_llm_malformed_response_falls_back_to_mock(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    fake = _fake_anthropic_client("not valid json at all")
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: fake)

    rv = client.post(
        "/api/studio/refine", json={"raw_text": "Some project notes.", "intent": "both"}
    )
    body = rv.get_json()
    assert body["ok"] is True
    assert body["draft"]["refine_source"] == "mock"


# ── LLM path: source_facts and assumptions normalized from response ───────────


def test_llm_refine_normalizes_source_facts(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    resp = _fake_llm_response(
        {"source_facts": ["Tool: Python", "Date: 2024-03"], "assumptions": []}
    )
    monkeypatch.setattr(llm_mod, "_call", lambda *a, **kw: resp)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    result = studio_refine_llm("notes", "both", cache_dir=tmp_path)
    assert result["draft"]["source_facts"] == ["Tool: Python", "Date: 2024-03"]
    assert result["draft"]["assumptions"] == []


def test_llm_refine_missing_source_facts_defaults_to_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    # Response without source_facts/assumptions keys
    resp = _fake_llm_response()
    parsed = json.loads(resp)
    del parsed["source_facts"]
    del parsed["assumptions"]

    monkeypatch.setattr(llm_mod, "_call", lambda *a, **kw: json.dumps(parsed))
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    result = studio_refine_llm("notes", "both", cache_dir=tmp_path)
    assert result["draft"]["source_facts"] == []
    assert result["draft"]["assumptions"] == []


# ── UI: Studio has grounding sections ────────────────────────────────────────


def test_studio_html_has_supported_facts_section(client):
    rv = client.get("/studio")
    assert rv.status_code == 200
    assert b"st-supported-facts" in rv.data
    assert b"Supported facts" in rv.data


def test_studio_html_has_needs_confirmation_section(client):
    rv = client.get("/studio")
    assert b"st-needs-confirmation" in rv.data
    assert b"Needs confirmation" in rv.data


def test_studio_js_renders_source_facts():
    import pathlib

    js = pathlib.Path("scripts/static/studio.js").read_text(encoding="utf-8")
    assert "source_facts" in js
    assert "_renderGroundingList" in js


def test_studio_js_renders_assumptions():
    import pathlib

    js = pathlib.Path("scripts/static/studio.js").read_text(encoding="utf-8")
    assert "assumptions" in js


# ── Persistence: save does not store source_facts or assumptions ──────────────


def test_save_does_not_persist_source_facts(client, tmp_path, monkeypatch):
    monkeypatch.setattr(dash_mod, "REPO_ROOT", tmp_path)
    (tmp_path / "cards").mkdir(exist_ok=True)

    draft = {
        "title": "Grounding Test Card",
        "type": "project",
        "period_start": "2026-01-01",
        "summary": "A test summary.",
        "source_facts": ["Fact: directly stated"],
        "assumptions": ["Solo contribution assumed."],
        "tags": {"domain": [], "skill": [], "audience": []},
        "metrics": [],
        "evidence": [],
        "resume_bullet": "• Built thing",
        "portfolio_body": "## Problem\n\nA problem.",
    }
    rv = client.post("/api/studio/save", json={"draft": draft})
    assert rv.status_code == 201

    saved_path = next(tmp_path.glob("cards/*.mdx"))
    content = saved_path.read_text(encoding="utf-8")
    assert "source_facts" not in content
    assert "assumptions" not in content
    assert "Fact: directly stated" not in content


# ── Evaluation: dry-run and live fake-client behavior ─────────────────────────


def test_evaluator_dry_run_prints_fixture_count(capsys):
    from scripts.evaluate_studio_grounding import FIXTURES, main

    rc = main(["--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert str(len(FIXTURES)) in out
    assert "Calls" in out


def test_evaluator_dry_run_makes_no_provider_calls(monkeypatch):
    called = []

    def _fake_call_with_meta(*a, **kw):
        called.append(True)
        return "{}", {}

    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)

    from scripts.evaluate_studio_grounding import main

    main(["--dry-run"])
    assert called == []


def test_evaluator_live_stops_at_max_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    call_count = [0]

    def _fake_call_with_meta(*a, **kw):
        call_count[0] += 1
        return _fake_llm_response(), {}

    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "evaluations").mkdir(parents=True)

    from scripts.evaluate_studio_grounding import main

    rc = main(["--live", "--provider", "anthropic", "--max-calls", "3"])
    assert rc == 0
    assert call_count[0] <= 3


def test_evaluator_live_checkpoints_after_each_call(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    def _fake_call_with_meta(*a, **kw):
        return _fake_llm_response(), {}

    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "evaluations").mkdir(parents=True)

    from scripts.evaluate_studio_grounding import main

    main(["--live", "--provider", "anthropic", "--max-calls", "2"])
    checkpoints = list((tmp_path / "output" / "evaluations").glob("*.json"))
    assert len(checkpoints) == 1
    with checkpoints[0].open() as f:
        data = json.load(f)
    assert len(data) >= 1


def test_evaluator_live_stops_on_quota_error(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    call_count = [0]

    def _fake_call_with_meta(*a, **kw):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise Exception("429 rate limit exceeded")
        return _fake_llm_response(), {}

    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "evaluations").mkdir(parents=True)

    from scripts.evaluate_studio_grounding import main

    rc = main(["--live", "--provider", "anthropic", "--max-calls", "10"])
    assert rc == 0
    # Stopped after quota error — did not exhaust max-calls
    assert call_count[0] < 10


# ── ISSUE-1: period_start derived from raw date; undated adds MISSING_PERIOD ──


def test_llm_dated_input_uses_raw_date_not_today(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    resp = _fake_llm_response({"source_facts": ["Date: 2024-03"], "missing_info": []})
    monkeypatch.setattr(llm_mod, "_call", lambda *a, **kw: resp)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    result = studio_refine_llm("Built DeFi contract in 2024-03.", "resume", cache_dir=tmp_path)
    assert result["draft"]["period_start"] == "2024-03-01"


def test_llm_undated_input_adds_missing_period(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    resp = _fake_llm_response({"missing_info": []})
    monkeypatch.setattr(llm_mod, "_call", lambda *a, **kw: resp)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    result = studio_refine_llm("Built something without any date.", "resume", cache_dir=tmp_path)
    codes = [m["code"] for m in result["missing_info"]]
    assert "MISSING_PERIOD" in codes


# ── ISSUE-2: Korean team markers trigger CONTRIBUTION_UNCLEAR ────────────────


def test_mock_korean_team_signal_adds_contribution_unclear(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={
            "raw_text": "팀 프로젝트로 스마트 컨트랙트를 개발했습니다.",
            "intent": "both",
        },
    )
    body = rv.get_json()
    codes = [m["code"] for m in body["missing_info"]]
    assert "CONTRIBUTION_UNCLEAR" in codes


def test_mock_korean_solo_no_contribution_unclear(client, monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rv = client.post(
        "/api/studio/refine",
        json={
            "raw_text": "DeFi 스테이킹 컨트랙트를 단독으로 설계하고 배포했습니다.",
            "intent": "both",
        },
    )
    body = rv.get_json()
    codes = [m["code"] for m in body["missing_info"]]
    assert "CONTRIBUTION_UNCLEAR" not in codes


# ── ISSUE-3: JS grounding list preserves <ul> ID across renders ──────────────


def test_studio_js_grounding_list_does_not_destroy_ul_id():
    import pathlib

    js = pathlib.Path("scripts/static/studio.js").read_text(encoding="utf-8")
    assert "replaceWith" not in js


# ── ISSUE-4: Google structured-output schema enforces required grounding fields


def test_grounded_draft_schema_has_required_grounding_fields():
    from scripts.llm import _GROUNDED_DRAFT_SCHEMA

    required = _GROUNDED_DRAFT_SCHEMA.get("required", [])
    for field in ("source_facts", "assumptions", "missing_info"):
        assert field in required, f"missing required field: {field}"


def test_google_structured_call_uses_response_schema(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "gkey-fake")
    monkeypatch.delenv("AI_MODEL", raising=False)

    captured: dict = {}

    def _fake_call_with_meta(client, prompt, model, response_json=False):
        captured["response_json"] = response_json
        return _fake_llm_response(), {}

    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())

    from scripts.llm import studio_refine_llm

    studio_refine_llm("test project notes", "both", cache_dir=tmp_path)
    assert captured.get("response_json") is True


# ── ISSUE-5: evaluator checkpoint records token fields and CLI provider wins ──


def test_evaluator_live_checkpoint_has_token_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    fake_usage = {"input_tokens": 42, "output_tokens": 77, "total_tokens": 119}

    def _fake_call_with_meta(*a, **kw):
        return _fake_llm_response(), fake_usage

    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)
    monkeypatch.setattr(llm_mod, "_build_client", lambda *a, **k: MagicMock())
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "evaluations").mkdir(parents=True)

    from scripts.evaluate_studio_grounding import main

    main(["--live", "--provider", "anthropic", "--max-calls", "1"])
    cp = next((tmp_path / "output" / "evaluations").glob("*.json"))
    data = json.load(cp.open())
    record = data[0]
    assert record.get("input_tokens") == 42
    assert record.get("output_tokens") == 77
    assert record.get("total_tokens") == 119


def test_evaluator_cli_provider_overrides_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "google")  # env says google
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)

    captured: dict = {}

    def _fake_build_client(cfg):
        captured["provider"] = cfg["provider"]
        return MagicMock()

    def _fake_call_with_meta(*a, **kw):
        return _fake_llm_response(), {}

    monkeypatch.setattr(llm_mod, "_build_client", _fake_build_client)
    monkeypatch.setattr(llm_mod, "_call_with_meta", _fake_call_with_meta)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "evaluations").mkdir(parents=True)

    from scripts.evaluate_studio_grounding import main

    rc = main(["--live", "--provider", "anthropic", "--max-calls", "1"])
    assert rc == 0
    assert captured.get("provider") == "anthropic"


# ── user-direction-001: prompt uses grounded procedure, not persona ───────────


def test_prompt_describes_grounded_procedure():
    from scripts.llm import _STUDIO_REFINE_PROMPT

    lower = _STUDIO_REFINE_PROMPT.lower()
    assert "evidence-grounded" in lower or "evidence grounded" in lower
    assert "source_facts" in _STUDIO_REFINE_PROMPT
    assert "missing_info" in _STUDIO_REFINE_PROMPT
    assert "{intent}" in _STUDIO_REFINE_PROMPT
    assert "{raw_text}" in _STUDIO_REFINE_PROMPT


def test_prompt_does_not_contain_persona_wording():
    from scripts.llm import _STUDIO_REFINE_PROMPT

    assert "you are a" not in _STUDIO_REFINE_PROMPT.lower()
