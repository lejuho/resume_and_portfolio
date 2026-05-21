let _lastDraft = null;

function _selectedIntent() {
  const el = document.querySelector('input[name="intent"]:checked');
  return el ? el.value : "both";
}

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

function renderPreview(draft, missingInfo) {
  const preview = document.getElementById("st-preview");
  preview.innerHTML = "";

  const fields = [
    ["Title", draft.title],
    ["Summary", draft.summary],
    draft.resume_bullet ? ["Resume bullet", draft.resume_bullet] : null,
    draft.portfolio_body ? ["Portfolio narrative", draft.portfolio_body] : null,
  ].filter(Boolean);

  for (const [label, val] of fields) {
    const div = document.createElement("div");
    div.className = "preview-field";
    div.innerHTML = `<label>${label}</label><div class="val">${_esc(val)}</div>`;
    preview.appendChild(div);
  }

  const miDiv = document.getElementById("st-missing-info");
  miDiv.innerHTML = "";
  if (missingInfo && missingInfo.length) {
    for (const item of missingInfo) {
      const el = document.createElement("div");
      el.className = "missing-item";
      el.innerHTML = `<span class="code">${_esc(item.code)}</span>${_esc(item.message)}`;
      miDiv.appendChild(el);
    }
  }

  document.getElementById("st-save-btn").style.display = "inline-block";
  document.getElementById("st-save-result").style.display = "none";
}

async function save() {
  if (!_lastDraft) return;
  const btn = document.getElementById("st-save-btn");
  const result = document.getElementById("st-save-result");

  btn.disabled = true;
  btn.textContent = "Saving…";

  try {
    const resp = await fetch("/api/studio/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ draft: _lastDraft }),
    });
    const data = await resp.json();
    result.style.display = "block";
    if (data.ok) {
      result.className = "save-result ok";
      result.textContent = `Saved: ${data.path}`;
      btn.style.display = "none";
    } else {
      result.className = "save-result err";
      result.textContent = data.error || "Save failed.";
      btn.disabled = false;
      btn.textContent = "Save as draft card";
    }
  } catch (e) {
    result.style.display = "block";
    result.className = "save-result err";
    result.textContent = "Network error: " + e.message;
    btn.disabled = false;
    btn.textContent = "Save as draft card";
  }
}

function _showPreviewError(msg) {
  const preview = document.getElementById("st-preview");
  preview.innerHTML = `<p style="color:#c62828">${_esc(msg)}</p>`;
  document.getElementById("st-save-btn").style.display = "none";
}

function _esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
