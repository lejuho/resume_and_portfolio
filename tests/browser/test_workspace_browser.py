"""TC-WS-010 through TC-WS-019: Workspace browser integration tests.

Uses a real ephemeral Flask server and Playwright Chromium. Each test
receives a fresh browser context (fresh localStorage) via the ``page``
fixture from pytest-playwright.

Run:
    uv run pytest tests/browser/test_workspace_browser.py -v
Preflight:
    uv run playwright install chromium
"""

from __future__ import annotations

import json

import pytest

# ── TC-WS-010: Manual dark toggle and localStorage persistence ─────────────────


def test_dark_toggle_sets_attribute_and_storage(server, page):
    """TC-WS-010 — clicking theme toggle sets data-ws-theme and localStorage."""
    page.goto(f"{server}/workspace")
    page.wait_for_selector(".ws-card-item")

    toggle = page.locator("#ws-theme-toggle")
    initial = toggle.text_content().strip()

    toggle.click()

    if initial == "Dark mode":
        assert page.evaluate("document.documentElement.getAttribute('data-ws-theme')") == "dark"
        assert page.evaluate("localStorage.getItem('workspace-theme')") == "dark"
        assert toggle.text_content().strip() == "Light mode"
    else:
        assert page.evaluate("document.documentElement.getAttribute('data-ws-theme')") == "light"
        assert page.evaluate("localStorage.getItem('workspace-theme')") == "light"
        assert toggle.text_content().strip() == "Dark mode"


def test_dark_preference_persists_across_reload(server, page):
    """TC-WS-010 — stored dark preference survives a page reload."""
    page.goto(f"{server}/workspace")
    page.wait_for_selector(".ws-card-item")

    page.evaluate("localStorage.setItem('workspace-theme', 'dark')")
    page.reload()
    page.wait_for_selector(".ws-card-item")

    assert page.evaluate("document.documentElement.getAttribute('data-ws-theme')") == "dark"


def test_light_preference_overrides_dark_os_scheme(server, browser):
    """TC-WS-010 — manual light preference overrides emulated dark OS scheme."""
    context = browser.new_context(color_scheme="dark")
    pg = context.new_page()
    pg.goto(f"{server}/workspace")
    pg.wait_for_selector(".ws-card-item")

    assert pg.evaluate("window.matchMedia('(prefers-color-scheme: dark)').matches") is True

    # Store light preference, reload, confirm override.
    pg.evaluate("localStorage.setItem('workspace-theme', 'light')")
    pg.reload()
    pg.wait_for_selector(".ws-card-item")

    assert pg.evaluate("document.documentElement.getAttribute('data-ws-theme')") == "light"
    context.close()


# ── TC-WS-011: Card selected state ────────────────────────────────────────────


def test_card_selection_adds_class(ws_page):
    """TC-WS-011 — checking the checkbox adds ws-card-selected; unchecking removes it."""
    card = ws_page.locator(".ws-card-item").first
    checkbox = card.locator("input[type='checkbox']")

    assert not card.evaluate("el => el.classList.contains('ws-card-selected')")
    checkbox.check()
    assert card.evaluate("el => el.classList.contains('ws-card-selected')")
    checkbox.uncheck()
    assert not card.evaluate("el => el.classList.contains('ws-card-selected')")


# ── TC-WS-012: Card hover state ───────────────────────────────────────────────
# TC-WS-012: Browser-executed computed-style after :hover is not reliably
# detectable in headless Chromium without a layout flush guarantee.
# The .ws-card-item:hover { background: var(--ws-accent-tint) } rule is
# verified by source-inspection tests (test_cycle28.py / test_cycle29.py).
# This browser test verifies the card IS rendered and hoverable without error.


def test_card_hover_does_not_raise(ws_page):
    """TC-WS-012 — card item is rendered and accepts a hover event."""
    card = ws_page.locator(".ws-card-item").first
    card.hover()  # must not raise
    assert card.is_visible()


# ── TC-WS-013: Keyboard Tab navigation and ARIA relationships ─────────────────


def test_keyboard_tab_sequence_reaches_controls(narrow_ws_page):
    """TC-WS-013 — Tab from neutral document focus reaches all 5 required control categories.

    Uses narrow_ws_page so the disclosure button is naturally visible and participates in the
    tab order.  Starts from document.body.focus() (neutral) so the theme toggle itself must
    be reachable by Tab — not pre-focused programmatically.
    """
    # Neutral start: no interactive element is pre-focused.
    narrow_ws_page.evaluate("() => document.body.focus()")

    reached: set[str] = set()
    for _ in range(50):
        active = narrow_ws_page.evaluate(
            "() => ({ id: document.activeElement.id,"
            " type: document.activeElement.type || '',"
            " hasExpanded: document.activeElement.hasAttribute('aria-expanded') })"
        )
        if active["id"] == "ws-theme-toggle":
            reached.add("theme-toggle")
        if active["type"] == "checkbox":
            reached.add("checkbox")
        if active["id"] in {"ws-organization", "ws-role", "ws-question", "ws-competency", "ws-jd"}:
            reached.add("target-field")
        if active["hasExpanded"]:
            reached.add("disclosure")
        if active["id"] == "ws-generate-btn":
            reached.add("generate-btn")
        if len(reached) == 5:
            break
        narrow_ws_page.keyboard.press("Tab")

    assert "theme-toggle" in reached, "Tab did not reach the theme toggle button"
    assert "checkbox" in reached, "Tab did not reach any card checkbox"
    assert "target-field" in reached, "Tab did not reach any target input field"
    assert "disclosure" in reached, "Tab did not reach the disclosure button"
    assert "generate-btn" in reached, "Tab did not reach the generate button"


def test_checkbox_accessible_name_from_label(ws_page):
    """TC-WS-013 — card checkbox has an accessible name via a non-empty <label>."""
    label = ws_page.locator("label[for='ws-card-auth-service']")
    assert label.count() > 0, "Expected <label for='ws-card-auth-service'>"
    assert label.inner_text().strip() != "", "Label text must not be empty"


def test_disclosure_button_aria_controls(ws_page):
    """TC-WS-013 — disclosure button has aria-controls referencing the context element."""
    btn = ws_page.locator("[aria-controls='ws-card-context-search-platform']")
    assert btn.count() > 0, "Expected disclosure button with aria-controls"
    ctx = ws_page.locator("#ws-card-context-search-platform")
    assert ctx.count() > 0, "Element referenced by aria-controls must exist"


def test_theme_toggle_has_visible_label(ws_page):
    """TC-WS-013 — theme toggle button has non-empty visible text."""
    toggle = ws_page.locator("#ws-theme-toggle")
    assert toggle.inner_text().strip() != "", "Theme toggle must have non-empty label"


# ── TC-WS-014/015/016: Fit signal coverage percentage and input listeners ─────


def test_coverage_shows_dash_with_no_selection_and_no_target(ws_page):
    """TC-WS-015 — no selection and no target shows em-dash."""
    value = ws_page.locator("#ws-coverage-value").text_content()
    assert value.strip() == "—"


def test_coverage_updates_on_target_input(ws_page):
    """TC-WS-016 — typing in a target field triggers _wsUpdateCoverage."""
    # Select auth-service card
    ws_page.locator("#ws-card-auth-service").check()

    # Type keywords that overlap with auth-service tokens (title/summary)
    ws_page.locator("#ws-role").fill("auth service platform")

    value = ws_page.locator("#ws-coverage-value").text_content().strip()
    assert value.endswith("%"), f"Expected a percentage, got: {value!r}"
    pct = int(value.rstrip("%"))
    assert pct > 0, "Expected non-zero coverage for matching keywords"


def test_coverage_shows_dash_with_card_but_no_target(ws_page):
    """TC-WS-015 — card selected but target empty shows em-dash."""
    ws_page.locator("#ws-card-auth-service").check()
    value = ws_page.locator("#ws-coverage-value").text_content().strip()
    assert value == "—"


def test_coverage_zero_for_no_keyword_overlap(ws_page):
    """TC-WS-015 — target with no shared keywords shows 0%."""
    ws_page.locator("#ws-card-auth-service").check()
    ws_page.locator("#ws-role").fill("xyzzy quux frobnitz")
    value = ws_page.locator("#ws-coverage-value").text_content().strip()
    assert value == "0%"


@pytest.mark.parametrize(
    "field_id",
    ["ws-organization", "ws-role", "ws-question", "ws-competency", "ws-jd"],
)
def test_target_field_triggers_coverage(ws_page, field_id):
    """TC-WS-016 — each target field individually wires to _wsUpdateCoverage."""
    ws_page.locator("#ws-card-auth-service").check()
    ws_page.locator(f"#{field_id}").fill("auth service platform")

    value = ws_page.locator("#ws-coverage-value").text_content().strip()
    assert value.endswith("%"), f"#{field_id} did not trigger coverage update: {value!r}"
    pct = int(value.rstrip("%"))
    assert pct > 0, f"#{field_id} produced 0% coverage for matching keyword"


# ── TC-WS-017/018/019: Card disclosure ────────────────────────────────────────


def test_disclosure_button_present_in_dom(ws_page):
    """TC-WS-017 — ws-card-more button is always rendered (may be hidden)."""
    btns = ws_page.locator(".ws-card-more")
    assert btns.count() == 2  # two live cards


def test_disclosure_button_shown_for_long_summary(narrow_ws_page):
    """TC-WS-017 — more button is naturally visible when summary overflows in narrow viewport."""
    ctx_id = "ws-card-context-search-platform"
    js = (
        "id => { const el = document.getElementById(id);"
        " return el ? el.scrollHeight > el.clientHeight : null; }"
    )
    overflows = narrow_ws_page.evaluate(js, ctx_id)
    assert overflows, "Long summary must overflow 2-line clamp at 320 px viewport"

    btn = narrow_ws_page.locator(f"[aria-controls='{ctx_id}']")
    assert not btn.evaluate("el => el.hidden"), (
        "Disclosure button must be visible (not hidden) when summary overflows"
    )


def test_disclosure_expand_collapse_toggle(narrow_ws_page):
    """TC-WS-018 — clicking more button toggles aria-expanded and button text."""
    btn = narrow_ws_page.locator("[aria-controls='ws-card-context-search-platform']")

    assert btn.get_attribute("aria-expanded") == "false"
    assert "Show full summary" in btn.inner_text()

    btn.click()
    assert btn.get_attribute("aria-expanded") == "true"
    assert "Collapse summary" in btn.inner_text()

    btn.click()
    assert btn.get_attribute("aria-expanded") == "false"
    assert "Show full summary" in btn.inner_text()


def test_disclosure_collapsed_height_less_than_expanded(narrow_ws_page):
    """TC-WS-018 — collapsed context is shorter than expanded context."""
    ctx = narrow_ws_page.locator("#ws-card-context-search-platform")
    btn = narrow_ws_page.locator("[aria-controls='ws-card-context-search-platform']")

    collapsed_h = ctx.evaluate("el => el.clientHeight")
    btn.click()
    expanded_h = ctx.evaluate("el => el.clientHeight")

    assert expanded_h > collapsed_h


def test_disclosure_click_does_not_toggle_selection(narrow_ws_page):
    """TC-WS-019 — clicking more button does not change checkbox checked state."""
    btn = narrow_ws_page.locator("[aria-controls='ws-card-context-search-platform']")
    checkbox = narrow_ws_page.locator("#ws-card-search-platform")

    assert not checkbox.is_checked()
    btn.click()
    assert not checkbox.is_checked()


# ── Long-text containment ─────────────────────────────────────────────────────


def test_long_title_and_summary_no_horizontal_overflow(ws_page):
    """Left pane must not gain horizontal scroll from long card text."""
    overflow = ws_page.evaluate(
        "el => el.scrollWidth - el.clientWidth",
        ws_page.locator("#ws-card-list").element_handle(),
    )
    assert overflow == 0, f"Left pane has horizontal overflow: {overflow}px"


# ── Live-card filter (source + browser) ──────────────────────────────────────


def test_only_live_cards_rendered(ws_page):
    """Only live cards appear; the draft card is excluded."""
    count_text = ws_page.locator("#ws-card-count").text_content()
    assert "2 live cards" in count_text
    assert ws_page.locator("#ws-card-old-draft").count() == 0


# ── Preview payload contract and no-persistence ───────────────────────────────


def test_preview_payload_and_no_persistence(server, page, live_repo):
    """Preview sends correct payload shape to /api/studio/application-preview; no card created."""
    captured: dict = {}

    def on_request(request):
        if "/api/studio/application-preview" in request.url:
            try:
                captured["body"] = json.loads(request.post_data or "null")
                captured["method"] = request.method
            except (json.JSONDecodeError, Exception):
                captured["body"] = None

    page.on("request", on_request)

    before = len(list((live_repo / "cards").glob("*.mdx")))

    page.goto(f"{server}/workspace")
    page.wait_for_selector(".ws-card-item")

    page.locator("#ws-card-auth-service").check()
    page.locator("#ws-organization").fill("Acme Corp")
    page.locator("#ws-role").fill("auth engineer")
    page.locator("#ws-generate-btn").click()

    out = page.locator("#ws-preview-out")
    out.wait_for(state="visible", timeout=10_000)
    text = out.text_content().strip()
    assert text, "Preview output should not be empty"
    assert "Network error" not in text
    assert "Preview failed" not in text

    # Payload shape contract
    assert "body" in captured, "No request to /api/studio/application-preview was captured"
    body = captured["body"]
    assert body is not None, "Request body could not be parsed as JSON"
    assert "output_type" in body, "Missing output_type in preview payload"
    assert "card_ids" in body, "Missing card_ids in preview payload"
    assert "target_context" in body, "Missing target_context in preview payload"
    assert "auth-service" in body["card_ids"], "Selected card ID not in payload card_ids"

    after = len(list((live_repo / "cards").glob("*.mdx")))
    assert after == before, "Preview must not create any card files"
