// Shared front-end helpers for ShiftWise AI.

async function api(path, options = {}) {
  const init = { method: options.method || 'GET', headers: { Accept: 'application/json' } };
  if (options.body !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(options.body);
  }
  const res = await fetch(path, init);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`);
    err.violations = data.violations || [];
    throw err;
  }
  return data;
}

// Escape text before inserting it into HTML (prevents XSS from stored data).
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function formData(form) {
  const out = {};
  for (const [key, value] of new FormData(form).entries()) {
    if (value !== '') out[key] = value;
  }
  return out;
}

// Today's date in the browser's local time zone, as YYYY-MM-DD.
function todayISO() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function flash(text, kind) {
  const el = document.getElementById('flash');
  el.textContent = text;
  el.className = `flash ${kind}`;
  el.hidden = false;
  clearTimeout(flash.timer);
  flash.timer = setTimeout(() => { el.hidden = true; }, 6000);
}

function showMessage(text) { flash(text, 'ok'); }

function showError(err) {
  const extra = err.violations && err.violations.length ? `: ${err.violations.join('; ')}` : '';
  flash(`${err.message}${extra}`, 'error');
}

document.getElementById('logout-btn')?.addEventListener('click', async () => {
  await api('/api/auth/logout', { method: 'POST' }).catch(() => {});
  window.location.href = '/login';
});
