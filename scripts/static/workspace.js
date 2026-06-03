// Workspace — evidence card list and target/output shell.
// Independent from the studio surface; no shared DOM ids or JS state.

(function () {
  "use strict";

  // ── Card list ──────────────────────────────────────────────────────────────

  let _wsCards = [];

  function _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
        div.innerHTML =
          `<input type="checkbox" id="ws-card-${_esc(card.id)}" value="${_esc(card.id)}" onchange="_wsOnCardToggle(this)" />` +
          `<label class="ws-card-body" for="ws-card-${_esc(card.id)}">` +
          `<span class="ws-card-pill">${_esc(pill)}</span>` +
          `<span class="ws-card-title">${_esc(card.title)}</span>` +
          `<span class="ws-card-context">${_esc(context)}</span>` +
          `<span class="ws-card-meta">${_esc(meta)}</span>` +
          `</label>`;
        list.appendChild(div);
      }
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
    // Toggle selected class on the parent card item
    if (cb) {
      const item = cb.closest(".ws-card-item");
      if (item) item.classList.toggle("ws-card-selected", cb.checked);
    }
    const selected = _wsSelectedCardIds();
    const coverageGap = document.getElementById("ws-coverage-gap");
    if (coverageGap) {
      if (selected.length) {
        coverageGap.textContent = `${selected.length} card${selected.length !== 1 ? "s" : ""} selected. Theme matching available in a later cycle.`;
      } else {
        coverageGap.textContent =
          "Select cards and add a target to calculate coverage.";
      }
    }
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
  window.generateWorkspacePreview = generateWorkspacePreview;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadWorkspaceCards);
  } else {
    loadWorkspaceCards();
  }
})();
