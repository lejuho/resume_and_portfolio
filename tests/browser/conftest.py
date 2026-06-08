"""Browser test fixtures for Workspace integration tests.

Spins up a real ephemeral Flask server against a temporary card repository,
then yields a live base URL to Playwright-based tests.

Scope design
------------
``live_repo``         — session: immutable temp directory, safe to share.
``monkeypatch_module`` — module: ensures REPO_ROOT is restored after the
                         browser module finishes and before test_cycle*.py runs.
``server``            — module: server shuts down before the next module starts,
                         preventing REPO_ROOT / env-var leakage into the full suite.
``ws_page``           — function: fresh browser context (fresh localStorage) per test.
``narrow_ws_page``    — function: 320 px viewport, guarantees line-clamp overflow.
"""

from __future__ import annotations

import threading

import pytest
from werkzeug.serving import make_server

import scripts.dashboard as dash_mod
from scripts.dashboard import app

# ── Card fixtures ──────────────────────────────────────────────────────────────

_LIVE_SHORT_MDX = """\
---
id: auth-service
title: Auth Service Platform
type: project
period:
  start: 2024-03-01
status: live
summary: "Rebuilt the authentication service reducing latency by 40 percent."
metrics:
  - "40% latency reduction"
evidence:
  - type: repo
    url: https://github.com/example/auth-service
---
"""

_LIVE_LONG_MDX = """\
---
id: search-platform
title: Search Platform Overhaul
type: project
period:
  start: 2023-06-01
status: live
summary: >-
  Led the complete redesign of the enterprise search platform, replacing
  the legacy Lucene cluster with a distributed vector pipeline, cutting
  p99 query latency from 800ms to 50ms.
metrics:
  - "800ms to 50ms p99 latency"
  - "500M documents per day"
evidence:
  - type: other
    url: https://example.com/search-case-study
---
"""

_DRAFT_MDX = """\
---
id: old-draft
title: Draft Card
type: project
period:
  start: 2022-01-01
status: draft
summary: "This is a draft and should not appear in Workspace."
---
"""


@pytest.fixture(scope="session")
def live_repo(tmp_path_factory):
    """Temporary card repository with deterministic live fixtures."""
    repo = tmp_path_factory.mktemp("repo")
    cards = repo / "cards"
    cards.mkdir()
    (cards / "2024-03-auth-service.mdx").write_text(_LIVE_SHORT_MDX, encoding="utf-8")
    (cards / "2023-06-search-platform.mdx").write_text(_LIVE_LONG_MDX, encoding="utf-8")
    (cards / "2022-01-old-draft.mdx").write_text(_DRAFT_MDX, encoding="utf-8")
    return repo


@pytest.fixture(scope="module")
def monkeypatch_module():
    """Module-scoped monkeypatch — undone after the browser module finishes.

    pytest's built-in monkeypatch is function-scoped only; this wrapper uses
    the same MonkeyPatch class with module scope so that REPO_ROOT and env-var
    patches are reversed before test_cycle*.py modules start.
    """
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="module")
def server(live_repo, monkeypatch_module):
    """Real ephemeral Flask server on a temporary repository.

    Yields the base URL ``http://127.0.0.1:<port>``.  Server and patches are
    torn down after the browser module completes (module scope), preventing
    REPO_ROOT / env-var leakage into non-browser test modules.
    """
    monkeypatch_module.setattr(dash_mod, "REPO_ROOT", live_repo)

    # Clear provider env vars so no live AI call can be made.
    for var in (
        "AI_PROVIDER",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "AI_API_KEY",
    ):
        monkeypatch_module.delenv(var, raising=False)

    srv = make_server("127.0.0.1", 0, app)
    port = srv.server_port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.shutdown()
        t.join(timeout=5)


@pytest.fixture()
def ws_page(server, page):
    """Playwright page navigated to /workspace with cards loaded."""
    page.goto(f"{server}/workspace")
    # Wait for at least one card to render (5 s timeout).
    page.wait_for_selector(".ws-card-item", timeout=5_000)
    # Wait for the count element to confirm loadWorkspaceCards finished (5 s).
    page.wait_for_function(
        "document.getElementById('ws-card-count')?.textContent?.trim() !== ''",
        timeout=5_000,
    )
    yield page


@pytest.fixture()
def narrow_ws_page(server, browser):
    """Workspace page in a 320 px-wide viewport.

    The narrow viewport guarantees that the long-summary card's ``scrollHeight``
    exceeds its ``clientHeight`` after ``-webkit-line-clamp: 2`` is applied by
    the browser, making disclosure button visibility deterministic without any
    DOM mutation or ``pytest.skip``.
    """
    context = browser.new_context(viewport={"width": 320, "height": 800})
    pg = context.new_page()
    try:
        pg.goto(f"{server}/workspace")
        pg.wait_for_selector(".ws-card-item", timeout=5_000)
        pg.wait_for_function(
            "document.getElementById('ws-card-count')?.textContent?.trim() !== ''",
            timeout=5_000,
        )
        yield pg
    finally:
        context.close()
