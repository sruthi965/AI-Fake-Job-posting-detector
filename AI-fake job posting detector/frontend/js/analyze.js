/* Analyze form and result page. */
(function () {
  'use strict';
  const JG = window.JG;
  const el = JG.el, svg = JG.svg;
  const SESSION_KEY = 'jg_result';

  function readJob(form) {
    const f = new FormData(form);
    return {
      job_title: f.get('job_title'), company_name: f.get('company_name'), description: f.get('description'),
      requirements: f.get('requirements'), employment_type: f.get('employment_type'), salary_range: f.get('salary_range'),
    };
  }

  function initForm() {
    const form = document.getElementById('analyze-form');
    const errorBox = document.getElementById('form-error');
    const saveRow = document.getElementById('save-row');
    if (saveRow && !JG.isLoggedIn()) saveRow.hidden = true;
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      JG.showError(errorBox, '');
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      button.textContent = 'Analyzing…';
      const job = readJob(form);
      const saveBox = document.getElementById('save_history');
      try {
        const result = await JG.api('/predict', { method: 'POST', body: Object.assign({}, job, { save_history: Boolean(saveBox && saveBox.checked) }) });
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({ job: job, result: result, explanation: null }));
        location.href = 'result.html';
      } catch (e) {
        JG.showError(errorBox, e.message);
        button.disabled = false;
        button.textContent = 'Analyze job posting';
      }
    });
  }

  /* ---- result page ---- */
  function ring(probability, fraud) {
    const radius = 38, circumference = 2 * Math.PI * radius;
    const color = fraud ? '#c9252d' : '#12713f';
    return svg('svg', { class: 'ring', viewBox: '0 0 100 100', role: 'img', 'aria-label': 'Fraud probability ' + JG.percent(probability) },
      svg('circle', { cx: 50, cy: 50, r: radius, fill: 'none', stroke: '#e3e9f4', 'stroke-width': 10 }),
      svg('circle', { cx: 50, cy: 50, r: radius, fill: 'none', stroke: color, 'stroke-width': 10, 'stroke-linecap': 'round',
        'stroke-dasharray': (circumference * probability / 100).toFixed(1) + ' ' + circumference.toFixed(1), transform: 'rotate(-90 50 50)' }),
      (function () { const t = svg('text', { x: 50, y: 52, 'text-anchor': 'middle' }); t.textContent = JG.percent(probability); return t; })(),
      (function () { const t = svg('text', { x: 50, y: 66, 'text-anchor': 'middle', class: 'sub' }); t.textContent = 'fraud probability'; return t; })());
  }

  function indicatorList(indicators) {
    if (!indicators.length) return el('p', { class: 'muted', text: 'No specific warning signs were found in the text you entered.' });
    return el('ul', { class: 'indicators' }, indicators.map(function (i) {
      return el('li', {}, el('span', { class: 'sev ' + i.severity, text: i.severity }),
        el('span', {}, i.label, i.evidence ? el('span', { class: 'evidence', text: 'Found: ' + i.evidence }) : null));
    }));
  }

  function summaryList(job, result) {
    const rows = [['Job title', job.job_title], ['Company', job.company_name || 'Not provided'],
      ['Type', job.employment_type || 'Not provided'], ['Salary', job.salary_range || 'Not provided'],
      ['Scoring', result.model_used === 'rules-only' ? 'Warning-sign rules only (no trained model loaded)' : result.model_used.replace(/_/g, ' ')]];
    return el('dl', { class: 'summary' }, rows.map(function (r) { return [el('dt', { text: r[0] }), el('dd', { text: r[1] })]; }).flat());
  }

  function renderExplanation(container, explanation) {
    container.replaceChildren(el('h2', { text: 'AI explanation' }),
      el('p', { class: 'muted', text: explanation.source === 'llm' ? 'Written by a language model from the indicators above.' : 'Generated from the indicators above.' }),
      el('p', { text: explanation.summary }),
      explanation.reasons.length ? el('ol', {}, explanation.reasons.map(function (r) { return el('li', {}, el('strong', { text: r.title }), ' ', r.detail); })) : null,
      el('div', { class: 'recommend' }, el('strong', { text: 'Recommendation' }), el('p', { text: explanation.recommendation })));
    container.hidden = false;
  }

  function initResult() {
    const root = document.getElementById('result-root');
    let state = null;
    try { state = JSON.parse(sessionStorage.getItem(SESSION_KEY)); } catch (e) { state = null; }
    if (!state) {
      root.replaceChildren(el('div', { class: 'card empty' }, el('p', { text: 'There is no analysis to show yet.' }),
        el('a', { class: 'btn', href: 'analyze.html', text: 'Analyze a job posting' })));
      return;
    }
    const job = state.job, result = state.result, fraud = result.is_fraudulent;
    const errorBox = el('div', { class: 'alert error', role: 'alert', tabindex: '-1' });
    const explainBox = el('section', { class: 'card explanation', 'aria-live': 'polite', hidden: true });
    const explainBtn = el('button', { class: 'btn', type: 'button', text: 'Get AI explanation' });
    const saveBtn = el('button', { class: 'btn secondary', type: 'button', text: result.analysis_id ? 'Saved to history' : 'Save to history', disabled: Boolean(result.analysis_id) });

    function persist() { sessionStorage.setItem(SESSION_KEY, JSON.stringify(state)); }

    explainBtn.addEventListener('click', async function () {
      JG.showError(errorBox, '');
      explainBtn.disabled = true;
      explainBtn.textContent = 'Generating…';
      try {
        const body = Object.assign({}, job, { prediction: result.prediction, fraud_probability: result.fraud_probability,
          risk_indicators: result.risk_indicators, analysis_id: result.analysis_id });
        state.explanation = await JG.api('/explain', { method: 'POST', body: body });
        persist();
        renderExplanation(explainBox, state.explanation);
        explainBtn.textContent = 'Explanation ready';
      } catch (e) {
        JG.showError(errorBox, e.message);
        explainBtn.disabled = false;
        explainBtn.textContent = 'Get AI explanation';
      }
    });

    saveBtn.addEventListener('click', async function () {
      JG.showError(errorBox, '');
      if (!JG.isLoggedIn()) { location.href = 'login.html?next=result.html'; return; }
      saveBtn.disabled = true;
      try {
        const body = Object.assign({}, job, { prediction: result.prediction, fraud_probability: result.fraud_probability,
          risk_indicators: result.risk_indicators, explanation: state.explanation, model_used: result.model_used });
        const saved = await JG.api('/history', { method: 'POST', body: body });
        result.analysis_id = saved.id;
        persist();
        saveBtn.textContent = 'Saved to history';
      } catch (e) {
        JG.showError(errorBox, e.message);
        saveBtn.disabled = false;
      }
    });

    root.replaceChildren(
      el('section', { class: 'verdict ' + (fraud ? 'fraud' : 'legit') },
        el('div', { class: 'text' },
          el('h1', { text: fraud ? 'Potentially fraudulent' : 'Likely legitimate' }),
          el('p', { text: fraud ? 'This posting shows signs of potential fraud.' : 'This posting did not match known fraud patterns closely.' })),
        ring(result.fraud_probability, fraud)),
      el('div', { class: 'two-col' },
        el('section', { class: 'card' }, el('h2', { text: 'Key risk indicators' }), indicatorList(result.risk_indicators)),
        el('section', { class: 'card' }, el('h2', { text: 'Quick summary' }), summaryList(job, result))),
      el('div', { class: 'alert warn', style: null, role: 'note' }, result.disclaimer),
      errorBox,
      el('div', { class: 'actions-row' }, explainBtn, saveBtn),
      explainBox);

    if (state.explanation) { renderExplanation(explainBox, state.explanation); explainBtn.textContent = 'Explanation ready'; explainBtn.disabled = true; }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const page = document.body.dataset.page;
    if (page === 'analyze') initForm();
    if (page === 'result') initResult();
  });
})();
