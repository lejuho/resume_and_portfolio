let _lastDraft = null;
let _savedId = null;
let _chipTimer = null;

function _selectedIntent() {
  const el = document.querySelector('input[name="intent"]:checked');
  return el ? el.value : "both";
}

// ── Source chips ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("st-raw").addEventListener("input", () => {
    clearTimeout(_chipTimer);
    _chipTimer = setTimeout(detectChips, 200);
  });
  _fetchAiStatus();
  loadAppCards();
});

async function _fetchAiStatus() {
  const el = document.getElementById("st-ai-status");
  if (!el) return;
  try {
    const resp = await fetch("/api/studio/ai-status");
    const data = await resp.json();
    if (data.configured) {
      el.textContent = "AI: configured";
    } else {
      el.textContent = "AI: mock fallback";
    }
  } catch (_) {
    el.textContent = "AI: unavailable";
  }
}

function detectChips() {
  const raw = document.getElementById("st-raw").value;
  const container = document.getElementById("st-source-chips");
  container.innerHTML = "";

  const dateM = raw.match(/\b(20\d{2})[-/](0[1-9]|1[0-2])\b/);
  const metricM = raw.match(/\b\d+(?:\.\d+)?[kKmMbBx%]/);
  const urlM = raw.match(/https?:\/\/\S+/);
  const visualM = /screenshot|diagram|image|figure|photo|visual/i.test(raw);

  if (dateM) container.appendChild(_chip("date", dateM[0]));
  if (metricM) container.appendChild(_chip("metric", metricM[0]));
  if (urlM) {
    const label = urlM[0].replace(/^https?:\/\//, "").slice(0, 40);
    container.appendChild(_chip("link", label));
  }
  if (visualM) container.appendChild(_chip("visual", "visual"));
}

function _chip(type, label) {
  const span = document.createElement("span");
  span.className = `chip chip-${type}`;
  span.dataset.detect = type;
  span.textContent = label;
  return span;
}

// ── AI connection check ───────────────────────────────────────────────────────

async function checkAiConnection() {
  const statusEl = document.getElementById("st-ai-status");
  const btn = document.getElementById("st-ai-check-btn");
  btn.disabled = true;
  btn.textContent = "Checking…";
  try {
    const resp = await fetch("/api/studio/ai-check", { method: "POST" });
    const data = await resp.json();
    if (data.connected) {
      if (statusEl) statusEl.textContent = "AI: verified";
    } else {
      if (statusEl) statusEl.textContent = "AI: configured, check failed";
    }
  } catch (_) {
    if (statusEl) statusEl.textContent = "AI: check unavailable";
  } finally {
    btn.disabled = false;
    btn.textContent = "Check AI connection";
  }
}

// ── Refine ───────────────────────────────────────────────────────────────────

async function refine() {
  const raw = document.getElementById("st-raw").value;
  const intent = _selectedIntent();
  const btn = document.getElementById("st-refine-btn");

  btn.disabled = true;
  btn.textContent = "Generating…";

  try {
    const resp = await fetch("/api/studio/refine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: raw, intent }),
    });
    const data = await resp.json();
    if (!data.ok) {
      _showPreviewError(data.error || "Refine failed.");
      return;
    }
    _lastDraft = data.draft;
    renderPreview(data.draft, data.missing_info);
  } catch (e) {
    _showPreviewError("Network error: " + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate preview";
  }
}

// ── Preview ──────────────────────────────────────────────────────────────────

function renderPreview(draft, missingInfo) {
  document.getElementById("st-placeholder").hidden = true;
  document.getElementById("st-edit-fields").hidden = false;

  document.getElementById("st-edit-title").value = draft.title || "";
  document.getElementById("st-edit-summary").value = draft.summary || "";

  const bulletWrap = document.getElementById("st-bullet-wrap");
  const bulletEl = document.getElementById("st-edit-resume-bullet");
  bulletWrap.hidden = !draft.resume_bullet;
  bulletEl.value = draft.resume_bullet || "";

  const bodyWrap = document.getElementById("st-body-wrap");
  const bodyEl = document.getElementById("st-edit-portfolio-body");
  bodyWrap.hidden = !draft.portfolio_body;
  bodyEl.value = draft.portfolio_body || "";

  const miDiv = document.getElementById("st-missing-info");
  miDiv.innerHTML = "";
  for (const item of missingInfo || []) {
    const el = document.createElement("div");
    el.className = "missing-item";
    el.innerHTML =
      `<span class="mi-code">${_esc(item.code)}</span>` +
      `<span class="mi-message">${_esc(item.message)}</span>`;
    miDiv.appendChild(el);
  }

  _renderGroundingList("st-supported-facts", "st-facts-list", draft.source_facts || []);
  _renderGroundingList("st-needs-confirmation", "st-assumptions-list", draft.assumptions || []);

  const sourceEl = document.getElementById("st-refine-source");
  if (sourceEl) {
    const label = draft.refine_source === "llm" ? "Source: LLM" : "Source: Mock";
    const reason = draft.fallback_reason ? ` — ${draft.fallback_reason}` : "";
    sourceEl.textContent = label + reason;
    sourceEl.hidden = false;
  }

  const saveBtn = document.getElementById("st-save-btn");
  saveBtn.hidden = false;
  saveBtn.disabled = false;
  saveBtn.textContent = "Save as draft card";

  document.getElementById("st-save-result").hidden = true;
  document.getElementById("st-post-save").hidden = true;

  _savedId = null;
  const buildOutput = document.getElementById("st-build-output");
  buildOutput.style.display = "none";
  buildOutput.textContent = "";
}

// ── Save ─────────────────────────────────────────────────────────────────────

async function save() {
  if (!_lastDraft) return;

  const editedDraft = { ..._lastDraft };
  const titleEl = document.getElementById("st-edit-title");
  const summaryEl = document.getElementById("st-edit-summary");
  const bulletWrap = document.getElementById("st-bullet-wrap");
  const bulletEl = document.getElementById("st-edit-resume-bullet");
  const bodyWrap = document.getElementById("st-body-wrap");
  const bodyEl = document.getElementById("st-edit-portfolio-body");

  if (titleEl) editedDraft.title = titleEl.value.trim();
  if (summaryEl) editedDraft.summary = summaryEl.value.trim();
  if (bulletEl && bulletWrap && !bulletWrap.hidden) {
    editedDraft.resume_bullet = bulletEl.value.trim();
  }
  if (bodyEl && bodyWrap && !bodyWrap.hidden) {
    editedDraft.portfolio_body = bodyEl.value.trim();
  }

  const btn = document.getElementById("st-save-btn");
  const result = document.getElementById("st-save-result");
  btn.disabled = true;
  btn.textContent = "Saving…";

  try {
    const resp = await fetch("/api/studio/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ draft: editedDraft }),
    });
    const data = await resp.json();
    result.hidden = false;
    if (data.ok) {
      _savedId = data.id;
      result.className = "save-result ok";
      result.textContent = `Saved: ${data.path}`;
      btn.hidden = true;
      document.getElementById("st-post-save").hidden = false;
    } else {
      result.className = "save-result err";
      result.textContent = data.error || "Save failed.";
      btn.disabled = false;
      btn.textContent = "Save as draft card";
    }
  } catch (e) {
    result.hidden = false;
    result.className = "save-result err";
    result.textContent = "Network error: " + e.message;
    btn.disabled = false;
    btn.textContent = "Save as draft card";
  }
}

// ── Build ────────────────────────────────────────────────────────────────────

async function buildCard(target) {
  if (!_savedId) return;
  const output = document.getElementById("st-build-output");
  output.style.display = "block";
  output.textContent = `Building ${target}…`;

  try {
    const resp = await fetch("/api/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target, selected_ids: [_savedId], dry_run: false }),
    });
    const data = await resp.json();
    if (data.ok) {
      output.textContent = `Done: ${data.output_path || "build complete"}`;
    } else {
      output.textContent = `Error (${data.exit_code}):\n${data.stderr || data.stdout || "unknown error"}`;
    }
  } catch (e) {
    output.textContent = "Network error: " + e.message;
  }
}

// ── Grounding helpers ────────────────────────────────────────────────────────

function _renderGroundingList(sectionId, listId, items) {
  const section = document.getElementById(sectionId);
  const list = document.getElementById(listId);
  if (!section || !list) return;
  list.innerHTML = "";
  if (items.length === 0) {
    const em = document.createElement("li");
    em.className = "grounding-empty";
    em.textContent = "None detected.";
    list.appendChild(em);
    section.hidden = false;
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
  section.hidden = false;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function _showPreviewError(msg) {
  document.getElementById("st-placeholder").hidden = false;
  document.getElementById("st-edit-fields").hidden = true;
  document.getElementById("st-placeholder").textContent = msg;
  document.getElementById("st-placeholder").style.color = "#c62828";
  document.getElementById("st-save-btn").hidden = true;
}

function _esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Application Writing ──────────────────────────────────────────────────────

let _appCards = [];
let _appDraftText = "";
let _appLastPreview = null;

async function loadAppCards() {
  const container = document.getElementById("st-app-card-selector");
  if (!container) return;
  try {
    const resp = await fetch("/api/cards");
    const data = await resp.json();
    const live = (Array.isArray(data) ? data : []).filter(c => c.status === "live");
    container.innerHTML = "";
    if (!live.length) {
      container.innerHTML = '<span class="placeholder">No live cards found. Mark cards as Live in Dashboard first. If a card shows validation errors it will not appear here.</span>';
      _appCards = [];
      return;
    }
    _appCards = live;
    for (const card of live) {
      const div = document.createElement("div");
      div.className = "card-check-item";
      const rawSummary = card.summary || "";
      const summary = rawSummary.length > 80 ? rawSummary.slice(0, 80) + "…" : rawSummary;
      const mCount = card.metrics_count || 0;
      const eCount = card.evidence_count || 0;
      const metaParts = [];
      if (mCount) metaParts.push(`${mCount} metric${mCount > 1 ? "s" : ""}`);
      if (eCount) metaParts.push(`${eCount} evidence`);
      const metaStr = metaParts.length ? metaParts.join(" · ") : "no metrics or evidence";
      div.innerHTML =
        `<input type="checkbox" id="app-card-${_esc(card.id)}" value="${_esc(card.id)}" />` +
        `<label for="app-card-${_esc(card.id)}">` +
          `<span class="card-title">${_esc(card.title)}</span>` +
          (summary ? `<span class="card-summary">${_esc(summary)}</span>` : "") +
          `<span class="card-counts">${_esc(metaStr)}</span>` +
        `</label>`;
      container.appendChild(div);
    }
  } catch (_) {
    if (container) container.innerHTML = '<span class="placeholder">Could not load cards.</span>';
  }
}

function _selectedAppCardIds() {
  const checks = document.querySelectorAll('#st-app-card-selector input[type="checkbox"]:checked');
  return Array.from(checks).map(c => c.value);
}

function _selectedAppOutputType() {
  const el = document.querySelector('input[name="app_output_type"]:checked');
  return el ? el.value : "application_answer";
}

async function generateAppPreview() {
  const card_ids = _selectedAppCardIds();
  const output_type = _selectedAppOutputType();
  const organization = (document.getElementById("st-app-organization") || {}).value || "";
  const role = (document.getElementById("st-app-role") || {}).value || "";
  const question = (document.getElementById("st-app-question") || {}).value || "";
  const competency = (document.getElementById("st-app-competency") || {}).value || "";
  const job_description = (document.getElementById("st-app-jd") || {}).value || "";
  const charLimitRaw = (document.getElementById("st-app-charlimit") || {}).value;
  const blind_hiring = document.getElementById("st-app-blind")
    ? document.getElementById("st-app-blind").checked
    : false;

  const target_context = { organization, role, question, competency, job_description, blind_hiring };
  if (charLimitRaw) {
    const parsed = parseInt(charLimitRaw, 10);
    if (!isNaN(parsed)) target_context.character_limit = parsed;
  }

  const btn = document.getElementById("st-app-preview-btn");
  btn.disabled = true;
  btn.textContent = "Generating…";

  try {
    const resp = await fetch("/api/studio/application-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ output_type, card_ids, target_context }),
    });
    const data = await resp.json();
    if (!data.ok) {
      _showAppError(data.error || "Preview failed.");
      return;
    }
    renderAppPreview(data.preview);
  } catch (e) {
    _showAppError("Network error: " + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate application preview";
  }
}

function renderAppPreview(preview) {
  _appLastPreview = preview;
  document.getElementById("st-app-result").hidden = false;

  _renderGroundingList("st-app-facts-section", "st-app-facts-list", preview.personal_facts || []);
  _renderGroundingList("st-app-context-section", "st-app-context-list", preview.target_context_used || []);

  const selSection = document.getElementById("st-app-selected-section");
  const selList = document.getElementById("st-app-selected-list");
  if (selSection && selList) {
    selList.innerHTML = "";
    for (const sc of preview.selected_cards || []) {
      const li = document.createElement("li");
      li.textContent = `${sc.display_title || sc.title || ""}: ${sc.selection_reason || ""}`;
      selList.appendChild(li);
    }
    selSection.hidden = (preview.selected_cards || []).length === 0;
  }

  _renderGroundingList(
    "st-app-guidance-section", "st-app-guidance-list", preview.ai_guidance || []
  );

  _renderGroundingList(
    "st-app-assumptions-section", "st-app-assumptions-list", preview.assumptions || []
  );

  const interpEl = document.getElementById("st-app-interpretation");
  if (interpEl) {
    const parts = [];
    if (preview.question_intent) parts.push(`Intent: ${preview.question_intent}`);
    if (preview.competency_target) parts.push(`Competency: ${preview.competency_target}`);
    interpEl.textContent = parts.join(" · ");
  }

  const draftEl = document.getElementById("st-app-draft-text");
  if (draftEl) draftEl.textContent = preview.answer_draft || "";
  _appDraftText = preview.answer_draft || "";

  const charEl = document.getElementById("st-app-char-status");
  if (charEl && preview.character_limit) {
    const over = preview.character_count > preview.character_limit;
    charEl.textContent = `${preview.character_count} / ${preview.character_limit} characters`;
    charEl.className = "app-char-status " + (over ? "app-char-over" : "app-char-ok");
  } else if (charEl) {
    charEl.textContent = `${preview.character_count || 0} characters`;
    charEl.className = "app-char-status";
  }

  const miDiv = document.getElementById("st-app-missing-info");
  if (miDiv) {
    miDiv.innerHTML = "";
    for (const item of preview.missing_info || []) {
      const el = document.createElement("div");
      el.className = "missing-item";
      el.innerHTML =
        `<span class="mi-code">${_esc(item.code)}</span>` +
        `<span class="mi-message">${_esc(item.message)}</span>`;
      miDiv.appendChild(el);
    }
  }

  const copyBtn = document.getElementById("st-app-copy-btn");
  if (copyBtn) copyBtn.hidden = false;
  const exportBtn = document.getElementById("st-app-export-btn");
  if (exportBtn) exportBtn.hidden = false;

  const fallbackEl = document.getElementById("st-app-fallback-notice");
  if (fallbackEl) {
    if (preview.fallback_reason) {
      fallbackEl.textContent = `Fallback reason: ${preview.fallback_reason}`;
      fallbackEl.hidden = false;
    } else {
      fallbackEl.hidden = true;
    }
  }

  const srcEl = document.getElementById("st-app-refine-source");
  if (srcEl) {
    srcEl.textContent = preview.refine_source === "llm" ? "Source: LLM" : "Source: Mock";
  }
}

async function copyAppDraft() {
  if (!_appDraftText) return;
  try {
    await navigator.clipboard.writeText(_appDraftText);
    const btn = document.getElementById("st-app-copy-btn");
    if (btn) { btn.textContent = "Copied!"; setTimeout(() => { btn.textContent = "Copy Verified draft to clipboard"; }, 1500); }
  } catch (_) {}
}

function _buildHandoffPacket(preview) {
  const lines = ["=== Application Writing Handoff ===", ""];
  lines.push(`Output type: ${preview.output_type || ""}`);
  const tc = preview.target_context_used || [];
  if (tc.length) {
    lines.push("", "Target context used:");
    for (const item of tc) lines.push(`  • ${item}`);
  }
  lines.push("", "=== Verified Draft ===", preview.answer_draft || "");
  const sc = preview.selected_cards || [];
  if (sc.length) {
    lines.push("", "=== Evidence Used ===");
    for (const c of sc) {
      lines.push(`  ${c.display_title || c.title || ""}: ${c.selection_reason || ""}`);
    }
  }
  const warnings = preview.warnings || [];
  if (warnings.length) {
    lines.push("", "=== Warnings ===");
    for (const w of warnings) lines.push(`  • ${w}`);
  }
  if (preview.fallback_reason) lines.push("", `Source fallback: ${preview.fallback_reason}`);
  if (preview.refine_source) lines.push(`Refine source: ${preview.refine_source}`);
  const guidance = preview.ai_guidance || [];
  if (guidance.length) {
    lines.push("", "=== ADVISORY (AI-generated, verify — not part of verified draft) ===");
    for (const g of guidance) lines.push(`  • ${g}`);
  }
  lines.push("", "---", "This packet was generated from an Application Writing preview and is not stored in Career Memory.");
  return lines.join("\n");
}

async function exportAppPacket() {
  if (!_appLastPreview) return;
  const packet = _buildHandoffPacket(_appLastPreview);
  const outEl = document.getElementById("st-app-export-out");
  if (outEl) { outEl.textContent = packet; outEl.style.display = "block"; }
  try {
    const blob = new Blob([packet], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "application-handoff.txt";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1000);
  } catch (_) {
    try { await navigator.clipboard.writeText(packet); } catch (_2) {}
  }
}

function _resetAppHandoffState() {
  _appLastPreview = null;
  _appDraftText = "";
  const copyBtn = document.getElementById("st-app-copy-btn");
  if (copyBtn) copyBtn.hidden = true;
  const exportBtn = document.getElementById("st-app-export-btn");
  if (exportBtn) exportBtn.hidden = true;
  const exportOut = document.getElementById("st-app-export-out");
  if (exportOut) { exportOut.textContent = ""; exportOut.style.display = "none"; }
}

function _showAppError(msg) {
  _resetAppHandoffState();
  const result = document.getElementById("st-app-result");
  if (result) result.hidden = false;
  const draftEl = document.getElementById("st-app-draft-text");
  if (draftEl) draftEl.textContent = msg;
}
