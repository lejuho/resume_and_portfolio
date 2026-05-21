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
});

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
