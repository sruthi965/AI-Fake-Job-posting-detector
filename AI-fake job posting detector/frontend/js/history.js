/* Analysis history: paged table, detail dialog and delete. */
(function () {
  'use strict';
  const JG = window.JG;
  const el = JG.el;
  const PAGE_SIZE = 10;
  let page = 1;

  function badge(prediction) {
    const fraud = prediction === 'Fraudulent';
    return el('span', { class: 'badge ' + (fraud ? 'fraud' : 'legit'), text: prediction });
  }

  async function showDetail(id) {
    const dialog = document.getElementById('detail-dialog');
    const body = document.getElementById('detail-body');
    body.replaceChildren(el('p', { class: 'muted', text: 'Loading…' }));
    dialog.showModal();
    try {
      const d = await JG.api('/history/' + id);
      const rows = [['Company', d.company_name || 'Not provided'], ['Type', d.employment_type || 'Not provided'], ['Salary', d.salary_range || 'Not provided'], ['Date', JG.formatDate(d.created_at)]];
      body.replaceChildren(
        el('h2', { text: d.job_title }),
        el('p', {}, badge(d.prediction), ' ', JG.percent(d.fraud_probability) + ' estimated fraud probability'),
        el('dl', { class: 'summary' }, rows.map(function (r) { return [el('dt', { text: r[0] }), el('dd', { text: r[1] })]; }).flat()),
        el('h3', { text: 'Warning indicators' }),
        d.risk_indicators.length ? el('ul', { class: 'indicators' }, d.risk_indicators.map(function (i) {
          return el('li', {}, el('span', { class: 'sev ' + i.severity, text: i.severity }), el('span', { text: i.label }));
        })) : el('p', { class: 'muted', text: 'None found.' }),
        d.explanation ? el('div', { class: 'explanation' }, el('h3', { text: 'AI explanation' }), el('p', { text: d.explanation.summary }),
          d.explanation.reasons.length ? el('ol', {}, d.explanation.reasons.map(function (r) { return el('li', {}, el('strong', { text: r.title }), ' ', r.detail); })) : null,
          el('div', { class: 'recommend' }, el('strong', { text: 'Recommendation' }), el('p', { text: d.explanation.recommendation }))) : null,
        el('h3', { text: 'Job description' }), el('p', { text: d.description, class: 'muted' }));
    } catch (e) {
      body.replaceChildren(el('div', { class: 'alert error', role: 'alert', text: e.message }));
    }
  }

  async function remove(id) {
    if (!window.confirm('Delete this analysis from your history?')) return;
    try { await JG.api('/history/' + id, { method: 'DELETE' }); await load(); }
    catch (e) { JG.showError(document.getElementById('form-error'), e.message); }
  }

  function pager(total) {
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const go = function (n) { return function () { page = n; load(); }; };
    const nodes = [el('button', { class: 'btn secondary small', type: 'button', text: 'Previous', disabled: page <= 1, onclick: go(page - 1) })];
    const start = Math.max(1, Math.min(page - 2, pages - 4)), end = Math.min(pages, start + 4);
    for (let n = start; n <= end; n++) {
      nodes.push(el('button', { class: 'btn secondary small', type: 'button', text: String(n), 'aria-current': n === page ? 'page' : null, onclick: go(n) }));
    }
    nodes.push(el('button', { class: 'btn secondary small', type: 'button', text: 'Next', disabled: page >= pages, onclick: go(page + 1) }));
    nodes.push(el('span', { class: 'total', text: 'Total: ' + total + ' record' + (total === 1 ? '' : 's') }));
    return nodes;
  }

  async function load() {
    const root = document.getElementById('history-root');
    JG.showError(document.getElementById('form-error'), '');
    try {
      const data = await JG.api('/history?page=' + page + '&page_size=' + PAGE_SIZE);
      if (data.total === 0) {
        root.replaceChildren(el('div', { class: 'empty' }, el('p', { text: 'You have not saved any analyses yet.' }), el('a', { class: 'btn', href: 'analyze.html', text: 'Analyze a job posting' })));
        return;
      }
      const head = el('tr', {}, ['ID', 'Job title', 'Company', 'Prediction', 'Probability', 'Date', 'Actions'].map(function (h) { return el('th', { scope: 'col', text: h }); }));
      const rows = data.items.map(function (item) {
        return el('tr', {}, el('td', { text: '#' + item.id }), el('td', { text: item.job_title }), el('td', { text: item.company_name || '—' }),
          el('td', {}, badge(item.prediction)), el('td', { text: JG.percent(item.fraud_probability) }), el('td', { text: JG.formatDate(item.created_at) }),
          el('td', {}, el('button', { class: 'btn secondary small', type: 'button', text: 'View', onclick: function () { showDetail(item.id); } }), ' ',
            el('button', { class: 'btn danger small', type: 'button', text: 'Delete', onclick: function () { remove(item.id); } })));
      });
      root.replaceChildren(el('div', { class: 'table-wrap' }, el('table', {}, el('thead', {}, head), el('tbody', {}, rows))), el('div', { class: 'pager' }, pager(data.total)));
    } catch (e) {
      if (e.status === 401) { JG.requireLogin(); return; }
      root.replaceChildren(el('div', { class: 'alert error', role: 'alert', text: e.message }));
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (document.body.dataset.page !== 'history' || !JG.requireLogin()) return;
    document.getElementById('detail-close').addEventListener('click', function () { document.getElementById('detail-dialog').close(); });
    load();
  });
})();
