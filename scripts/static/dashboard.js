// ALL and sel are defined inline in dashboard.html
let _editMode = null;

const allTypes = [...new Set(ALL.map(c => c.type))].sort();
const tf = document.getElementById('type-filters');
allTypes.forEach(t => {
  const l = document.createElement('label');
  l.innerHTML = `<input type="checkbox" class="tcb" value="${t}"> ${t}`;
  tf.appendChild(l);
});

function filtered() {
  const types = [...document.querySelectorAll('.tcb:checked')].map(e => e.value);
  const st = document.querySelector('input[name=st]:checked').value;
  const tag = document.getElementById('tag-filter').value.trim().toLowerCase();
  const txt = document.getElementById('text-filter').value.trim().toLowerCase();
  return ALL.filter(c => {
    if (types.length && !types.includes(c.type)) return false;
    if (st !== 'all' && c.status !== st) return false;
    if (tag) {
      const allTags = Object.values(c.tags || {}).flat().join(' ').toLowerCase();
      if (!allTags.includes(tag)) return false;
    }
    if (txt && !`${c.id} ${c.title} ${c.summary}`.toLowerCase().includes(txt)) return false;
    return true;
  });
}

function chipClass(val, pool) {
  return pool.includes(val) ? val : 'type-default';
}
const knownTypes = ['hackathon','project','role','talk','paper','award','writing','course','community'];

function render() {
  const cards = filtered();
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';
  const empty = document.getElementById('empty-state');
  empty.style.display = cards.length === 0 ? '' : 'none';
  cards.forEach(c => {
    const tr = document.createElement('tr');
    if (sel.has(c.id)) tr.classList.add('sel');
    const ev = `${c.evidence_count}/${c.has_visuals ? '&#10003;' : '0'}`;
    const eid = c.id.replace(/'/g, "\\'");
    tr.innerHTML =
      `<td><input type="checkbox" class="rcb" data-id="${c.id}"${sel.has(c.id) ? ' checked' : ''}></td>` +
      `<td style="font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${c.id}">${c.id}</td>` +
      `<td style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${c.title}">${c.title}</td>` +
      `<td><span class="chip ${chipClass(c.type,knownTypes)}">${c.type}</span></td>` +
      `<td><span class="chip ${c.status}">${c.status}</span></td>` +
      `<td style="color:#666;white-space:nowrap">${c.period_start||''}</td>` +
      `<td style="text-align:center;color:#555;font-size:11px">${ev}</td>` +
      `<td><button class="edit-btn" onclick="openEdit('${eid}')">edit</button></td>`;
    tbody.appendChild(tr);
  });
  document.querySelectorAll('.rcb').forEach(cb => cb.addEventListener('change', () => {
    cb.checked ? sel.add(cb.dataset.id) : sel.delete(cb.dataset.id);
    cb.closest('tr').classList.toggle('sel', cb.checked);
    updateSel();
  }));
  const vis = filtered();
  document.getElementById('check-all').checked = vis.length > 0 && vis.every(c => sel.has(c.id));
}

function updateSel() {
  const ids = [...sel];
  document.getElementById('sel-count').textContent = `${ids.length} selected`;
  const container = document.getElementById('sel-chips');
  container.innerHTML = '';
  if (ids.length === 0) {
    container.innerHTML = '<span id="no-sel">No cards selected.</span>';
  } else {
    ids.forEach(id => {
      const chip = document.createElement('span');
      chip.className = 'sch';
      const eid = id.replace(/'/g, "\\'");
      chip.innerHTML = `${id}<button title="Remove" onclick="removeCard('${eid}')">&#215;</button>`;
      container.appendChild(chip);
    });
  }
}

function removeCard(id) {
  sel.delete(id);
  render();
  updateSel();
}

// ── authoring helpers ──────────────────────────────────────────────────────────

function _splitTags(val) {
  return val.split(',').map(s => s.trim()).filter(Boolean);
}

function _clearLists() {
  ['af-metrics-list', 'af-evidence-list', 'af-visuals-list'].forEach(id => {
    document.getElementById(id).innerHTML = '';
  });
}

function addMetric() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  row.innerHTML = '<input type="text" placeholder="e.g. 10k users">' +
    '<button class="rm-btn" onclick="removeRow(this)">&#215;</button>';
  document.getElementById('af-metrics-list').appendChild(row);
}

function addEvidence() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  const opts = ['repo','deck','writeup','demo','article','other']
    .map(t => `<option>${t}</option>`).join('');
  row.innerHTML = `<select class="ev-type">${opts}</select>` +
    '<input type="text" class="ev-url" placeholder="https://">' +
    '<button class="rm-btn" onclick="removeRow(this)">&#215;</button>';
  document.getElementById('af-evidence-list').appendChild(row);
}

function addVisual() {
  const row = document.createElement('div');
  row.className = 'dyn-row';
  const ropts = ['hero','diagram','screenshot','other']
    .map(r => `<option>${r}</option>`).join('');
  row.innerHTML = '<input type="text" class="vis-path" placeholder="assets/hero.png">' +
    `<select class="vis-role">${ropts}</select>` +
    '<input type="text" class="vis-caption" placeholder="Caption">' +
    '<button class="rm-btn" onclick="removeRow(this)">&#215;</button>';
  document.getElementById('af-visuals-list').appendChild(row);
}

function removeRow(btn) {
  btn.closest('.dyn-row').remove();
}

// ── authoring: open/close ──────────────────────────────────────────────────────

function openNew() {
  _editMode = null;
  document.getElementById('af-title').textContent = 'New card';
  document.getElementById('af-id').value = '';
  document.getElementById('af-id').disabled = false;
  document.getElementById('af-title-field').value = '';
  document.getElementById('af-type').value = 'project';
  document.getElementById('af-start').value = new Date().toISOString().slice(0,10);
  document.getElementById('af-status').value = 'draft';
  document.getElementById('af-summary').value = '';
  document.getElementById('af-tag-domain').value = '';
  document.getElementById('af-tag-skill').value = '';
  document.getElementById('af-tag-audience').value = '';
  _clearLists();
  document.getElementById('af-body').value = '';
  document.getElementById('af-status-msg').textContent = '';
  document.getElementById('authoring-panel').hidden = false;
  document.getElementById('af-id').focus();
}

async function openEdit(cardId) {
  _editMode = cardId;
  document.getElementById('af-title').textContent = `Edit: ${cardId}`;
  document.getElementById('af-id').value = cardId;
  document.getElementById('af-id').disabled = true;
  document.getElementById('af-status-msg').textContent = 'Loading…';
  document.getElementById('authoring-panel').hidden = false;
  _clearLists();
  try {
    const r = await fetch(`/api/cards/${encodeURIComponent(cardId)}`);
    const d = await r.json();
    if (!d.ok) { setAfStatus(false, d.error || 'load failed'); return; }
    const f = d.fields || {};
    document.getElementById('af-title-field').value = f.title || '';
    document.getElementById('af-type').value = f.type || 'project';
    const start = f.period && f.period.start ? f.period.start : '';
    document.getElementById('af-start').value = start;
    document.getElementById('af-status').value = f.status || 'draft';
    document.getElementById('af-summary').value = f.summary || '';
    const tags = f.tags || {};
    document.getElementById('af-tag-domain').value = (tags.domain || []).join(', ');
    document.getElementById('af-tag-skill').value = (tags.skill || []).join(', ');
    document.getElementById('af-tag-audience').value = (tags.audience || []).join(', ');
    (f.metrics || []).forEach(m => {
      const row = document.createElement('div');
      row.className = 'dyn-row';
      row.innerHTML = `<input type="text" value="${String(m).replace(/"/g,'&quot;')}">` +
        '<button class="rm-btn" onclick="removeRow(this)">&#215;</button>';
      document.getElementById('af-metrics-list').appendChild(row);
    });
    (f.evidence || []).forEach(e => {
      const row = document.createElement('div');
      row.className = 'dyn-row';
      const opts = ['repo','deck','writeup','demo','article','other']
        .map(t => `<option${t === e.type ? ' selected' : ''}>${t}</option>`).join('');
      row.innerHTML = `<select class="ev-type">${opts}</select>` +
        `<input type="text" class="ev-url" value="${(e.url||'').replace(/"/g,'&quot;')}">` +
        '<button class="rm-btn" onclick="removeRow(this)">&#215;</button>';
      document.getElementById('af-evidence-list').appendChild(row);
    });
    (f.visuals || []).forEach(v => {
      const row = document.createElement('div');
      row.className = 'dyn-row';
      const ropts = ['hero','diagram','screenshot','other']
        .map(r => `<option${r === v.role ? ' selected' : ''}>${r}</option>`).join('');
      row.innerHTML = `<input type="text" class="vis-path" value="${(v.path||'').replace(/"/g,'&quot;')}">` +
        `<select class="vis-role">${ropts}</select>` +
        `<input type="text" class="vis-caption" value="${(v.caption||'').replace(/"/g,'&quot;')}">` +
        '<button class="rm-btn" onclick="removeRow(this)">&#215;</button>';
      document.getElementById('af-visuals-list').appendChild(row);
    });
    document.getElementById('af-body').value = d.body || '';
    document.getElementById('af-status-msg').textContent = '';
  } catch(e) {
    setAfStatus(false, `Network error: ${e}`);
  }
}

function closeForm() {
  document.getElementById('authoring-panel').hidden = true;
  document.getElementById('af-status-msg').textContent = '';
  _editMode = null;
}

function setAfStatus(ok, msg) {
  const el = document.getElementById('af-status-msg');
  el.textContent = msg;
  el.className = ok ? 'af-ok' : 'af-err';
}

async function saveCard() {
  const btn = document.getElementById('af-save');
  btn.disabled = true;
  setAfStatus(false, 'Saving…');
  document.getElementById('af-status-msg').className = '';
  try {
    if (_editMode === null) {
      const body = {
        id: document.getElementById('af-id').value.trim(),
        title: document.getElementById('af-title-field').value.trim(),
        type: document.getElementById('af-type').value,
        period_start: document.getElementById('af-start').value.trim(),
        status: document.getElementById('af-status').value,
        summary: document.getElementById('af-summary').value.trim(),
      };
      const r = await fetch('/api/cards', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify(body)
      });
      const d = await r.json();
      if (d.ok) {
        setAfStatus(true, `Created ${d.path}`);
        setTimeout(() => { closeForm(); location.reload(); }, 800);
      } else {
        setAfStatus(false, d.error || 'create failed');
      }
    } else {
      const metricRows = [...document.querySelectorAll('#af-metrics-list .dyn-row')];
      const metrics = metricRows.map(row => row.querySelector('input').value.trim()).filter(Boolean);
      const evidenceRows = [...document.querySelectorAll('#af-evidence-list .dyn-row')];
      const evidence = evidenceRows.map(row => ({
        type: row.querySelector('.ev-type').value,
        url: row.querySelector('.ev-url').value.trim(),
      })).filter(e => e.url);
      const visualRows = [...document.querySelectorAll('#af-visuals-list .dyn-row')];
      const visuals = visualRows.map(row => ({
        path: row.querySelector('.vis-path').value.trim(),
        role: row.querySelector('.vis-role').value,
        caption: row.querySelector('.vis-caption').value.trim() || null,
      })).filter(v => v.path);
      const fields = {
        title: document.getElementById('af-title-field').value.trim(),
        type: document.getElementById('af-type').value,
        period: { start: document.getElementById('af-start').value.trim(), end: null },
        status: document.getElementById('af-status').value,
        summary: document.getElementById('af-summary').value.trim(),
        tags: {
          domain: _splitTags(document.getElementById('af-tag-domain').value),
          skill: _splitTags(document.getElementById('af-tag-skill').value),
          audience: _splitTags(document.getElementById('af-tag-audience').value),
        },
        metrics,
        evidence,
        visuals,
      };
      const body = document.getElementById('af-body').value;
      const r = await fetch(`/api/cards/${encodeURIComponent(_editMode)}`, {
        method: 'PUT', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({fields, body})
      });
      const d = await r.json();
      if (d.ok) {
        setAfStatus(true, `Saved ${d.path}`);
        setTimeout(() => { closeForm(); location.reload(); }, 800);
      } else {
        setAfStatus(false, d.error || 'save failed');
      }
    }
  } catch(e) {
    setAfStatus(false, `Network error: ${e}`);
  } finally {
    btn.disabled = false;
  }
}

// ── filter / selection ────────────────────────────────────────────────────────

document.querySelectorAll('.tcb,input[name=st]').forEach(e => e.addEventListener('change', render));
document.getElementById('tag-filter').addEventListener('input', render);
document.getElementById('text-filter').addEventListener('input', render);
document.getElementById('check-all').addEventListener('change', function() {
  filtered().forEach(c => this.checked ? sel.add(c.id) : sel.delete(c.id));
  render(); updateSel();
});
document.getElementById('btn-sel-all').addEventListener('click', () => {
  filtered().forEach(c => sel.add(c.id)); render(); updateSel();
});
document.getElementById('btn-clear').addEventListener('click', () => {
  sel.clear(); render(); updateSel();
});

// ── copy ─────────────────────────────────────────────────────────────────────

function copyText(btnId, text) {
  const btn = document.getElementById(btnId);
  const done = () => {
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'copy'; btn.classList.remove('copied'); }, 1500);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
  } else {
    fallbackCopy(text, done);
  }
}

function fallbackCopy(text, done) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px';
  document.body.appendChild(ta);
  ta.focus(); ta.select();
  try { document.execCommand('copy'); done(); } catch(e) {}
  document.body.removeChild(ta);
}

// ── build ─────────────────────────────────────────────────────────────────────

async function build(target, dryRun) {
  const rp = document.getElementById('result-panel');
  const summary = document.getElementById('result-summary');
  const cmdText = document.getElementById('cmd-text');
  const rawLog = document.getElementById('raw-log');
  const pathRow = document.getElementById('output-path-row');
  const pathText = document.getElementById('output-path-text');

  rp.style.display = '';
  summary.innerHTML = '<span style="color:#666;font-size:11px">Building&#8230;</span>';
  pathRow.style.display = 'none';
  cmdText.textContent = '';
  rawLog.textContent = '';
  document.getElementById('raw-details').open = false;
  document.querySelectorAll('#build-btns button').forEach(b => b.disabled = true);

  try {
    const r = await fetch('/api/build', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({target, dry_run: dryRun, selected_ids: [...sel]})
    });
    const d = await r.json();

    const statusLabel = d.ok
      ? `<span class="result-ok">&#10003; ${d.dry_run ? 'dry-run ok' : 'build ok'}</span>`
      : `<span class="result-err">&#10007; exit ${d.exit_code}</span>`;
    const selLabel = d.selected_ids && d.selected_ids.length
      ? `<span style="color:#555;font-size:10px">${d.selected_ids.length} card(s)</span>`
      : '';
    summary.innerHTML = statusLabel + (selLabel ? ' ' + selLabel : '');

    cmdText.textContent = d.command || '';

    if (d.output_path) {
      pathText.textContent = d.output_path;
      pathRow.style.display = '';
    } else {
      pathRow.style.display = 'none';
    }

    const logParts = [d.stdout, d.stderr ? `STDERR:\n${d.stderr}` : ''].filter(Boolean);
    rawLog.textContent = logParts.join('\n');
    if (rawLog.textContent.trim()) {
      document.getElementById('raw-details').open = !d.ok;
    }
  } catch(e) {
    summary.innerHTML = `<span class="result-err">Network error: ${e}</span>`;
  } finally {
    document.querySelectorAll('#build-btns button').forEach(b => b.disabled = false);
  }
}

render(); updateSel();
