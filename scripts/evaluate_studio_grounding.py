"""Developer-only Studio grounding evaluation.

Compares baseline (prompt-only) vs grounded one-shot Studio preview for
synthetic Track K and Track G fixtures. Records parse reliability, token
usage, and latency. Requires configured provider credentials for --live.

Usage:
    uv run python scripts/evaluate_studio_grounding.py --dry-run
    uv run python scripts/evaluate_studio_grounding.py --live --provider google --max-calls 12
"""

from __future__ import annotations

import argparse
import json
import os
import re as _re
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Synthetic fixtures ────────────────────────────────────────────────────────

FIXTURES = [
    {
        "id": "tk-001",
        "track": "K",
        "intent": "both",
        "description": "Korean formal: team blockchain project, no metric",
        "raw_text": (
            "팀 프로젝트로 NFT 마켓플레이스 스마트 컨트랙트를 개발했습니다. "
            "Solidity와 Hardhat을 사용했고, 팀원 3명과 함께 작업했습니다. "
            "메인넷 배포는 아직 하지 않았습니다."
        ),
    },
    {
        "id": "tk-002",
        "track": "K",
        "intent": "resume",
        "description": "Korean formal: solo contribution with metric",
        "raw_text": (
            "2024-03에 DeFi 스테이킹 컨트랙트를 단독으로 설계하고 배포했습니다. "
            "가스 비용을 30% 절감했고 TVL 5억원을 달성했습니다. "
            "https://github.com/example/staking-contract"
        ),
    },
    {
        "id": "tg-001",
        "track": "G",
        "intent": "both",
        "description": "Global tech: solo project with evidence",
        "raw_text": (
            "Built a cross-chain bridge for ERC-20 tokens between Ethereum and Polygon. "
            "Used LayerZero messaging protocol. Solo project. 2023-08. "
            "https://github.com/example/evm-bridge"
        ),
    },
    {
        "id": "tg-002",
        "track": "G",
        "intent": "portfolio",
        "description": "Global tech: team project, metric-free",
        "raw_text": (
            "Our team built a multi-signature wallet UI using React and ethers.js. "
            "We used Safe SDK for transaction management. No live deployment yet."
        ),
    },
]

# ── Baseline prompt (prompt-only, no grounding fields) ───────────────────────

_BASELINE_PROMPT = """\
You are a senior career consultant. Turn these career notes into a structured card.
Return ONLY a JSON object with: title, type, summary, tags, metrics, evidence, \
resume_bullet (if resume), portfolio_body (if portfolio), missing_info.

Intent: {intent}
Raw notes:
{raw_text}
"""


def _baseline_call(client, raw_text: str, intent: str, model: str) -> dict:
    from scripts.llm import _call_with_meta

    prompt = _BASELINE_PROMPT.format(intent=intent, raw_text=raw_text)
    return {"prompt": prompt, "caller": lambda: _call_with_meta(client, prompt, model)}


def _grounded_call(client, raw_text: str, intent: str, model: str, provider: str) -> dict:
    from scripts.llm import _STUDIO_REFINE_PROMPT, _call_with_meta

    prompt = _STUDIO_REFINE_PROMPT.format(intent=intent, raw_text=raw_text)
    use_json = provider == "google"
    return {
        "prompt": prompt,
        "caller": lambda: _call_with_meta(client, prompt, model, response_json=use_json),
    }


# ── Numeric-claim heuristic ──────────────────────────────────────────────────

_UNSUPPORTED_NUM_RE = _re.compile(r"\b\d+(?:\.\d+)?[kKmMbBx%]|\b\d{2,}\b")


def _has_unsupported_numeric(response_text: str, raw_text: str) -> bool:
    """Return True if the response contains numeric claims absent from raw_text."""
    resp_nums = set(_UNSUPPORTED_NUM_RE.findall(response_text))
    raw_nums = set(_UNSUPPORTED_NUM_RE.findall(raw_text))
    return bool(resp_nums - raw_nums)


# ── Evaluation runner ────────────────────────────────────────────────────────

_QUOTA_SIGNALS = ("quota", "rate", "429", "limit", "resource_exhausted")


def _is_quota_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return any(s in msg for s in _QUOTA_SIGNALS)


def _safe_error_category(exc: BaseException) -> str:
    msg = str(exc).lower()
    if any(s in msg for s in ("quota", "rate", "429", "limit", "resource_exhausted")):
        return "quota_or_rate_limit"
    if any(s in msg for s in ("auth", "key", "401", "403", "permission", "credential")):
        return "auth_failed"
    if any(s in msg for s in ("network", "connect", "timeout", "dns", "unreachable")):
        return "network_error"
    return "provider_error"


def _run_call(caller_fn, raw_text: str) -> dict:
    t0 = time.monotonic()
    try:
        raw, usage = caller_fn()
        latency = time.monotonic() - t0
        try:
            json.loads(raw.strip())
            parse_ok = True
        except Exception:
            parse_ok = False
        unsupported_num = _has_unsupported_numeric(raw, raw_text) if parse_ok else None
        result = {
            "ok": True,
            "parse_ok": parse_ok,
            "unsupported_numeric": unsupported_num,
            "latency_s": round(latency, 2),
            "output_chars": len(raw),
        }
        if usage:
            result.update(usage)
        return result
    except Exception as exc:
        latency = time.monotonic() - t0
        is_quota = _is_quota_error(exc)
        return {
            "ok": False,
            "error": str(exc)[:200],
            "safe_error_category": _safe_error_category(exc),
            "quota_error": is_quota,
            "latency_s": round(latency, 2),
        }


def _checkpoint(results: list[dict], out_dir: Path, timestamp: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"studio-grounding-{timestamp}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return path


# ── Main ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print plan; no provider calls.")
    parser.add_argument("--live", action="store_true", help="Run live evaluation.")
    parser.add_argument("--provider", default="google", help="Provider override (default: google).")
    parser.add_argument("--max-calls", type=int, default=12, help="Max provider calls.")
    args = parser.parse_args(argv)

    candidates = ["baseline", "grounded"]
    total_calls = len(FIXTURES) * len(candidates)

    if args.dry_run:
        print(f"Fixtures   : {len(FIXTURES)}")
        print(f"Candidates : {len(candidates)} ({', '.join(candidates)})")
        print(f"Max calls  : {args.max_calls}")
        print(f"Calls (est): {total_calls} (capped at --max-calls)")
        for fix in FIXTURES:
            print(f"  [{fix['track']}] {fix['id']}: {fix['description']}")
        return 0

    if not args.live:
        print("Pass --dry-run or --live.", file=sys.stderr)
        return 1

    # Live path — resolve provider (explicit CLI flag takes precedence)
    os.environ["AI_PROVIDER"] = args.provider
    try:
        from scripts.llm import _build_client, resolve_provider_config

        cfg = resolve_provider_config()
        client = _build_client(cfg)
        model = cfg["model"]
        provider = cfg["provider"]
    except Exception as exc:
        print(f"Provider setup failed: {exc}", file=sys.stderr)
        return 1

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    out_dir = Path("output/evaluations")
    results: list[dict] = []
    call_count = 0

    for fix in FIXTURES:
        for candidate in candidates:
            if call_count >= args.max_calls:
                print(f"Reached --max-calls {args.max_calls}. Stopping.")
                _checkpoint(results, out_dir, timestamp)
                return 0

            label = f"[{call_count + 1}/{args.max_calls}] {fix['id']} / {candidate}"
            print(f"{label} ...", end=" ", flush=True)

            if candidate == "baseline":
                call_info = _baseline_call(client, fix["raw_text"], fix["intent"], model)
            else:
                call_info = _grounded_call(client, fix["raw_text"], fix["intent"], model, provider)

            result = _run_call(call_info["caller"], fix["raw_text"])
            result.update({"fixture_id": fix["id"], "track": fix["track"], "candidate": candidate})
            results.append(result)
            call_count += 1

            status = "OK" if result.get("ok") else "ERR"
            parse = "parse=OK" if result.get("parse_ok") else "parse=FAIL"
            print(f"{status} {parse} latency={result.get('latency_s', '?')}s")

            cp = _checkpoint(results, out_dir, timestamp)

            if not result.get("ok") and result.get("quota_error"):
                print(f"Quota/rate error — stopping. Results: {cp}")
                return 0

    _checkpoint(results, out_dir, timestamp)
    print(f"\nDone. {call_count} calls. Results: {out_dir}/studio-grounding-{timestamp}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
