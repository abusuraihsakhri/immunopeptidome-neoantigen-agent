'use strict';

const $ = (id) => document.getElementById(id);
const state = { runs: [], batch: [], last: null };
const primaryLimit = 25;
const secondaryLimit = 12;
const phiPattern = /\bMRN[:#\s-]*\d{4,10}\b|\b\d{3}-\d{2}-\d{4}\b|\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b/i;

function validate(source) {
  const task = String(source.task_id ?? '').trim();
  const target = String(source.target_identifier ?? '').trim();
  const descriptor = String(source.status_descriptor ?? '').trim();
  const primary = Number(source.primary_metric);
  const secondary = Number(source.secondary_metric);
  if (!task || !target || !descriptor || [task, target, descriptor].some(s => s.length > 120)) {
    throw new Error('Task, target and descriptor are required (maximum 120 characters each).');
  }
  if (!Number.isFinite(primary) || !Number.isFinite(secondary) || String(source.primary_metric).trim() === '' || String(source.secondary_metric).trim() === '') {
    throw new Error('Both metrics must be finite numbers.');
  }
  if ([task, target, descriptor].some(s => phiPattern.test(s))) {
    throw new Error('Potential identifying information detected. Use de-identified sample IDs.');
  }
  let critical;
  if (typeof source.is_critical_flag === 'boolean') critical = source.is_critical_flag;
  else if (['true', '1', 'yes', 'y', 'on'].includes(String(source.is_critical_flag ?? '').trim().toLowerCase())) critical = true;
  else if (['false', '0', 'no', 'n', 'off', ''].includes(String(source.is_critical_flag ?? '').trim().toLowerCase())) critical = false;
  else throw new Error('Critical flag must be true/false, yes/no or 1/0.');
  return {task_id: task, target_identifier: target, primary_metric: primary,
    secondary_metric: secondary, status_descriptor: descriptor, is_critical_flag: critical};
}

// Mirrors the three generic demonstration rules in agents/workers.py.
// It is not a peptide-HLA binding or immunogenicity predictor.
function evaluate(payload) {
  const alerts = [];
  if (payload.primary_metric > primaryLimit) {
    alerts.push({origin_worker: 'InvariantQCWorker', urgency: 'ELEVATED_RISK',
      summary: `Primary metric exceeds demonstration threshold (${primaryLimit})`});
  }
  if (payload.is_critical_flag || payload.secondary_metric > secondaryLimit) {
    alerts.push({origin_worker: 'SafetyEscalationWorker',
      urgency: payload.is_critical_flag ? 'CRITICAL_STAT_PANIC' : 'ELEVATED_RISK',
      summary: 'Critical flag or secondary demonstration threshold exceeded'});
  }
  if (['DISCORDANT', 'ANOMALY', 'MUTANT', 'VIOLATION', 'FAIL', 'REJECT'].some(flag => payload.status_descriptor.toUpperCase().includes(flag))) {
    alerts.push({origin_worker: 'ProtocolConformanceWorker', urgency: 'ELEVATED_RISK',
      summary: 'Descriptor matches a configured anomaly keyword'});
  }
  const critical = alerts.some(a => a.urgency === 'CRITICAL_STAT_PANIC');
  const elevated = alerts.length > 0;
  return {...payload, evaluation_mode: 'LOCAL_DEMONSTRATION',
    overall_urgency: critical ? 'CRITICAL_STAT_PANIC' : elevated ? 'ELEVATED_RISK' : 'ROUTINE',
    integrity_status: critical ? 'RECALIBRATION_REQUIRED' : elevated ? 'DISCORDANT_ANOMALY' : 'VALIDATED_OPTIMAL',
    total_alerts: alerts.length, critical_alerts_count: alerts.filter(a => a.urgency === 'CRITICAL_STAT_PANIC').length,
    alerts, note: 'Generic example rules only. No NetMHCpan, HLA-binding model, signature or clinical assessment was run.'};
}

function formPayload() {
  return validate({task_id: $('task_id').value, target_identifier: $('target_identifier').value,
    primary_metric: $('primary_metric').value, secondary_metric: $('secondary_metric').value,
    status_descriptor: $('status_descriptor').value, is_critical_flag: $('is_critical_flag').checked});
}

function showResult(data, mode) {
  state.last = data;
  state.runs.push({mode, data});
  $('output').textContent = JSON.stringify(data, null, 2);
  $('result-title').textContent = mode === 'api' ? 'Backend response' : 'Local rule evaluation';
  $('run-count').textContent = String(state.runs.length);
  $('alert-count').textContent = String(state.runs.reduce((n, r) => n + (r.data.total_alerts ?? 0), 0));
  $('mode-status').textContent = mode === 'api' ? 'FastAPI' : 'In-browser';
  $('save-json').disabled = false;
  setMessage('Evaluation completed.', 'ok');
}

function setMessage(msg, kind = '') {
  $('message').textContent = msg;
  $('message').dataset.kind = kind;
}

async function run(payload) {
  const mode = $('execution-mode').value;
  if (mode === 'local') return showResult(evaluate(payload), 'local');
  const response = await fetch('/api/audit', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
  let data;
  try { data = await response.json(); }
  catch { throw new Error('The server did not return JSON. Check the FastAPI backend.'); }
  if (!response.ok) throw new Error(data.detail ? String(data.detail) : `HTTP ${response.status}`);
  showResult(data, 'api');
}

function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') {
      if (field !== '') throw new Error('Malformed CSV quoting.');
      quoted = true;
    } else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (c !== '\r') field += c;
  }
  if (quoted) throw new Error('Unterminated CSV quotation.');
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  return rows.filter(r => r.some(x => x.trim() !== ''));
}

function csvEscape(value) {
  let v = String(value ?? '');
  // Prevent spreadsheet formula execution in exported cells.
  if (/^[=+@\-\t\r]/.test(v)) v = "'" + v;
  return '"' + v.replaceAll('"', '""') + '"';
}

function download(name, text, mime) {
  const url = URL.createObjectURL(new Blob([text], {type: mime}));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$('audit-form').addEventListener('submit', async e => {
  e.preventDefault();
  $('run-button').disabled = true;
  setMessage('Evaluating…');
  try { await run(formPayload()); }
  catch (error) { setMessage(error.message, 'error'); }
  finally { $('run-button').disabled = false; }
});

$('save-json').addEventListener('click', () => {
  if (state.last) download('audit-result.json', JSON.stringify(state.last, null, 2) + '\n', 'application/json');
});

$('csv-file').addEventListener('change', async e => {
  state.batch = [];
  $('save-csv').disabled = true;
  const file = e.target.files[0];
  if (!file) return;
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error('Maximum CSV file size is 2 MiB.');
    const rows = parseCsv((await file.text()).replace(/^\uFEFF/, ''));
    if (!rows.length) throw new Error('CSV is empty.');
    const headers = rows.shift().map(h => h.trim());
    const needed = ['task_id', 'target_identifier', 'primary_metric', 'secondary_metric', 'status_descriptor', 'is_critical_flag'];
    if (needed.some(h => !headers.includes(h)) || new Set(headers).size !== headers.length) throw new Error('CSV must have six distinct required headers.');
    if (rows.length > 2000) throw new Error('Maximum 2,000 data records per batch.');
    state.batch = rows.map((values, i) => {
      if (values.length !== headers.length) throw new Error(`CSV row ${i + 2} has an incorrect field count.`);
      const record = Object.fromEntries(headers.map((h, j) => [h, values[j]]));
      try { return evaluate(validate(record)); }
      catch (error) { throw new Error(`CSV row ${i + 2}: ${error.message}`); }
    });
    $('save-csv').disabled = state.batch.length === 0;
    $('batch-count').textContent = String(state.batch.length);
    setMessage(`Processed ${state.batch.length} CSV records locally. Download the results below.`, 'ok');
  } catch (error) { $('batch-count').textContent = '0'; setMessage(error.message, 'error'); }
});

$('save-csv').addEventListener('click', () => {
  if (!state.batch.length) return;
  const keys = ['task_id', 'target_identifier', 'primary_metric', 'secondary_metric', 'status_descriptor', 'is_critical_flag', 'overall_urgency', 'integrity_status', 'total_alerts', 'critical_alerts_count'];
  const lines = [keys.map(csvEscape).join(','), ...state.batch.map(d => keys.map(k => csvEscape(d[k])).join(','))];
  download('audit-batch.csv', lines.join('\r\n') + '\r\n', 'text/csv;charset=utf-8');
});

$('execution-mode').addEventListener('change', () => {
  setMessage($('execution-mode').value === 'api' ? 'Backend mode requires the FastAPI server at this origin.' : 'Local evaluation stays in this browser.');
});

// GitHub Pages cannot host the Python API.
if (location.hostname.endsWith('.github.io') || location.protocol === 'file:') {
  $('api-mode').disabled = true;
}
