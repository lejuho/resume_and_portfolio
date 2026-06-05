// Workspace — evidence card list, fit signals, and target/output shell.
// Independent from the studio surface; no shared DOM ids or JS state.

(function () {
  "use strict";

  // ── Stop words (includes TLDs to suppress URL noise) ──────────────────────

  const _WS_STOP = new Set([
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of",
    "with", "is", "was", "are", "were", "be", "been", "by", "from", "as",
    "that", "this", "these", "those", "have", "has", "had", "it", "its",
    "we", "our", "they", "their", "i", "my", "not", "but", "use", "used",
    "using", "www", "http", "https",
    "com", "io", "dev", "net", "org", "co", "app", "ai",
  ]);

  // ── Fit signal helpers ─────────────────────────────────────────────────────

  function _wsTokenize(text) {
    if (!text) return new Set();
    const cleaned = String(text).replace(/https?:\/\/(www\.)?/gi, "");
    return new Set(
      cleaned
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, " ")
        .split(/\s+/)
        .filter((t) => t.length > 2 && !_WS_STOP.has(t))
    );
  }

  function _wsCardTokens(card) {
    const parts = [card.title, card.summary, card.type];
    if (Array.isArray(card.metrics)) parts.push(...card.metrics);
    if (Array.isArray(card.evidence)) {
      for (const e of card.evidence) {
        if (e && e.url) parts.push(e.url);
        if (e && e.text) parts.push(e.text);
      }
    }
    return _wsTokenize(parts.filter(Boolean).join(" "));
  }

  function _wsTargetText() {
    const ids = ["ws-organization", "ws-role", "ws-question", "ws-competency", "ws-jd"];
    return ids.map((id) => (document.getElementById(id) || {}).value || "").join(" ");
  }

  function _wsUpdateCoverage() {
    const valueEl = document.getElementById("ws-coverage-value");
    const gapEl = document.getElementById("ws-coverage-gap");
    const termsEl = document.getElementById("ws-coverage-terms");

    const selectedIds = _wsSelectedCardIds();
    const selected = _wsCards.filter((c) => selectedIds.includes(c.id));
    const targetText = _wsTargetText();

    if (!selected.length && !targetText.trim()) {
      if (valueEl) valueEl.textContent = "—";
      if (gapEl) gapEl.textContent = "Select cards and add a target to calculate coverage.";
      if (termsEl) termsEl.textContent = "";
      return;
    }
    if (!selected.length) {
      if (valueEl) valueEl.textContent = "—";
      if (gapEl) gapEl.textContent = "Select at least one evidence card.";
      if (termsEl) termsEl.textContent = "";
      return;
    }
    if (!targetText.trim()) {
      if (valueEl) valueEl.textContent = "—";
      if (gapEl) gapEl.textContent = "Add a target role or question to calculate fit.";
      if (termsEl) termsEl.textContent = "";
      return;
    }

    const targetTokens = _wsTokenize(targetText);
    const cardTokens = new Set();
    for (const card of selected) {
      for (const t of _wsCardTokens(card)) cardTokens.add(t);
    }

    const matched = [...targetTokens].filter((t) => cardTokens.has(t));
    const pct = targetTokens.size > 0
      ? Math.round((matched.length / targetTokens.size) * 100)
      : 0;

    if (valueEl) valueEl.textContent = `${pct}%`;
    if (matched.length > 0) {
      if (gapEl) gapEl.textContent = `${matched.length} term${matched.length !== 1 ? "s" : ""} matched`;
      if (termsEl) {
        const shown = matched.slice(0, 6).join(", ");
        termsEl.textContent = shown + (matched.length > 6 ? ` +${matched.length - 6} more` : "");
      }
    } else {
      if (gapEl) gapEl.textContent = "No matching terms found. Add relevant keywords to the target.";
      if (termsEl) termsEl.textContent = "";
    }
  }

  // ── Target input listeners ─────────────────────────────────────────────────

  function _wsWireTargetListeners() {
    const ids = ["ws-organization", "ws-role", "ws-question", "ws-competency", "ws-jd"];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) el.addEventListener("input", _wsUpdateCoverage);
    }
  }

  // ── Card list ──────────────────────────────────────────────────────────────

  let _wsCards = [];

  function _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  const WS_THEME_KEY = "workspace-theme";

  function _wsStoredTheme() {
    try {
      const stored = window.localStorage.getItem(WS_THEME_KEY);
      return stored === "dark" || stored === "light" ? stored : "";
    } catch (err) {
      return "";
    }
  }

  function _wsSystemTheme() {
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  function _wsApplyTheme(theme) {
    const selected = theme === "dark" || theme === "light" ? theme : "";
    const resolved = selected || _wsSystemTheme();
    if (selected) {
      document.documentElement.setAttribute("data-ws-theme", selected);
    } else {
      document.documentElement.removeAttribute("data-ws-theme");
    }
    const toggle = document.getElementById("ws-theme-toggle");
    if (toggle) {
      toggle.setAttribute("aria-pressed", resolved === "dark" ? "true" : "false");
      toggle.textContent = resolved === "dark" ? "Light mode" : "Dark mode";
    }
  }

  function toggleWorkspaceTheme() {
    const current =
      document.documentElement.getAttribute("data-ws-theme") || _wsSystemTheme();
    const next = current === "dark" ? "light" : "dark";
    try {
      window.localStorage.setItem(WS_THEME_KEY, next);
    } catch (err) {
      // Theme still applies for this page when localStorage is unavailable.
    }
    _wsApplyTheme(next);
  }

  async function loadWorkspaceCards() {
    const list = document.getElementById("ws-card-list");
    const countEl = document.getElementById("ws-card-count");
    if (!list) return;
    try {
      const resp = await fetch("/api/cards");
      const data = await resp.json();
      const live = (Array.isArray(data) ? data : []).filter(
        (c) => c.status === "live"
      );
      list.innerHTML = "";
      if (!live.length) {
        list.innerHTML =
          '<p class="ws-empty">No live cards found. Mark cards as Live in Dashboard first.</p>';
        _wsCards = [];
        if (countEl) countEl.textContent = "";
        _wsUpdateCoverage();
        return;
      }
      _wsCards = live;
      if (countEl) countEl.textContent = `${live.length} live card${live.length !== 1 ? "s" : ""}`;
      for (const card of live) {
        const div = document.createElement("div");
        div.className = "ws-card-item";
        const mCount = card.metrics_count || 0;
        const eCount = card.evidence_count || 0;
        const parts = [];
        if (mCount) parts.push(`${mCount} metric${mCount !== 1 ? "s" : ""}`);
        if (eCount) parts.push(`${eCount} evidence`);
        const meta = parts.length ? parts.join(" · ") : "no metrics or evidence";
        const pill = card.type || "card";
        const context = card.summary || "";
        const contextId = `ws-card-context-${_esc(card.id)}`;
        div.innerHTML =
          `<input type="checkbox" id="ws-card-${_esc(card.id)}" value="${_esc(card.id)}" onchange="_wsOnCardToggle(this)" />` +
          `<div class="ws-card-content">` +
          `<label class="ws-card-body" for="ws-card-${_esc(card.id)}">` +
          `<span class="ws-card-pill">${_esc(pill)}</span>` +
          `<span class="ws-card-title">${_esc(card.title)}</span>` +
          `<span class="ws-card-context" id="${contextId}">${_esc(context)}</span>` +
          `<span class="ws-card-meta">${_esc(meta)}</span>` +
          `</label>` +
          `<button class="ws-card-more" type="button" aria-expanded="false" aria-controls="${contextId}" hidden onclick="_wsToggleCardDetails(event, this)"><span>Show full summary</span><span aria-hidden="true">&#8595;</span></button>` +
          `</div>`;
        list.appendChild(div);
        const contextEl = div.querySelector(".ws-card-context");
        const moreButton = div.querySelector(".ws-card-more");
        if (contextEl && moreButton && contextEl.scrollHeight > contextEl.clientHeight) {
          moreButton.hidden = false;
        }
      }
      _wsUpdateCoverage();
    } catch (_) {
      if (list) list.innerHTML = '<p class="ws-empty">Could not load cards.</p>';
    }
  }

  function _wsSelectedCardIds() {
    const checks = document.querySelectorAll(
      '#ws-card-list input[type="checkbox"]:checked'
    );
    return Array.from(checks).map((c) => c.value);
  }

  function _wsOnCardToggle(cb) {
    if (cb) {
      const item = cb.closest(".ws-card-item");
      if (item) item.classList.toggle("ws-card-selected", cb.checked);
    }
    _wsUpdateCoverage();
  }

  function _wsToggleCardDetails(event, button) {
    event.preventDefault();
    event.stopPropagation();
    const content = button.closest(".ws-card-content");
    const context = content ? content.querySelector(".ws-card-context") : null;
    if (!context) return;
    const expanded = context.classList.toggle("ws-card-context-expanded");
    button.setAttribute("aria-expanded", expanded ? "true" : "false");
    button.innerHTML = expanded
      ? '<span>Collapse summary</span><span aria-hidden="true">&#8593;</span>'
      : '<span>Show full summary</span><span aria-hidden="true">&#8595;</span>';
  }

  // ── Output type ────────────────────────────────────────────────────────────

  function _wsOutputType() {
    const el = document.querySelector('input[name="ws_output_type"]:checked');
    return el ? el.value : "application_answer";
  }

  // ── Preview stub ───────────────────────────────────────────────────────────

  async function generateWorkspacePreview() {
    const btn = document.getElementById("ws-generate-btn");
    const out = document.getElementById("ws-preview-out");
    const cardIds = _wsSelectedCardIds();
    if (!cardIds.length) {
      if (out) { out.textContent = "Select at least one evidence card first."; out.style.display = "block"; }
      return;
    }
    if (btn) { btn.disabled = true; btn.textContent = "Generating…"; }
    try {
      const organization = (document.getElementById("ws-organization") || {}).value || "";
      const role = (document.getElementById("ws-role") || {}).value || "";
      const question = (document.getElementById("ws-question") || {}).value || "";
      const competency = (document.getElementById("ws-competency") || {}).value || "";
      const job_description = (document.getElementById("ws-jd") || {}).value || "";
      const charLimitRaw = (document.getElementById("ws-charlimit") || {}).value || "";
      const blind_hiring = document.getElementById("ws-blind")
        ? document.getElementById("ws-blind").checked
        : false;
      const target_context = { organization, role, question, competency, job_description, blind_hiring };
      if (charLimitRaw) {
        const parsed = parseInt(charLimitRaw, 10);
        if (!isNaN(parsed)) target_context.character_limit = parsed;
      }
      const resp = await fetch("/api/studio/application-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output_type: _wsOutputType(), card_ids: cardIds, target_context }),
      });
      const data = await resp.json();
      if (out) {
        out.textContent = data.ok
          ? (data.preview && data.preview.answer_draft) || ""
          : (data.error || "Preview failed.");
        out.style.display = "block";
      }
    } catch (e) {
      if (out) { out.textContent = "Network error: " + e.message; out.style.display = "block"; }
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Generate preview"; }
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────────

  // Expose for inline onclick handlers
  window._wsOnCardToggle = _wsOnCardToggle;
  window._wsToggleCardDetails = _wsToggleCardDetails;
  window.generateWorkspacePreview = generateWorkspacePreview;
  window.toggleWorkspaceTheme = toggleWorkspaceTheme;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      _wsApplyTheme(_wsStoredTheme());
      _wsWireTargetListeners();
      loadWorkspaceCards();
    });
  } else {
    _wsApplyTheme(_wsStoredTheme());
    _wsWireTargetListeners();
    loadWorkspaceCards();
  }
})();
