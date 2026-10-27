/* Model performance dashboard and the signed-in user's activity summary. */
(function () {
  'use strict';
  const JG = window.JG;
  const el = JG.el;
  const METRICS = [['accuracy', 'Accuracy', 'm1'], ['precision', 'Precision', 'm2'], ['recall', 'Recall', 'm3'], ['f1', 'F1-score', 'm4']];
  const MODEL_LABELS = { logistic_regression: 'Logistic Regression', random_forest: 'Random Forest' };
  const pct = function (v) { return (v * 100).toFixed(1) + '%'; };

  function metricCards(model) {
    return el('div', { class: 'metric-cards' }, METRICS.map(function (m) {
      return el('div', { class: 'metric ' + m[2] }, el('span', { text: m[1] }), el('b', { text: pct(model[m[0]]) }));
    }));
  }

  function confusionMatrix(cm) {
    const flat = cm.matrix.flat(), max = Math.max.apply(null, flat.concat([1]));
    function cell(value, label) {
      const node = el('div', { class: 'cell' }, String(value), el('small', { text: label }));
      node.style.background = 'rgba(15, 47, 107,' + (0.35 + 0.65 * value / max).toFixed(2) + ')';
      return node;
    }
    return el('div', { class: 'matrix', role: 'table', 'aria-label': 'Confusion matrix' },
      el('div'), el('div', { class: 'axis', text: 'Predicted legitimate' }), el('div', { class: 'axis', text: 'Predicted fraudulent' }),
      el('div', { class: 'axis', text: 'Actually legitimate' }), cell(cm.matrix[0][0], 'correct'), cell(cm.matrix[0][1], 'false alarm'),
      el('div', { class: 'axis', text: 'Actually fraudulent' }), cell(cm.matrix[1][0], 'missed'), cell(cm.matrix[1][1], 'correct'));
  }

  function comparisonChart(models) {
    const names = Object.keys(models);
    const groups = METRICS.map(function (m) {
      const pair = el('div', { class: 'bar-pair' }, names.map(function (name, idx) {
        const bar = el('div', { class: 'bar ' + (idx === 0 ? 'a' : 'b'), title: (MODEL_LABELS[name] || name) + ' ' + m[1] + ': ' + pct(models[name][m[0]]) });
        bar.style.height = (models[name][m[0]] * 100).toFixed(1) + '%';
        return bar;
      }));
      return el('div', { class: 'bar-group' }, pair);
    });
    return el('div', {},
      el('div', { class: 'legend' }, names.map(function (name, idx) {
        const dot = el('i'); dot.style.background = idx === 0 ? '#1f6feb' : '#1fa971';
        return el('span', {}, dot, MODEL_LABELS[name] || name);
      })),
      el('div', { class: 'bars' }, groups),
      el('div', { class: 'bar-labels' }, METRICS.map(function (m) { return el('span', { text: m[1] }); })));
  }

  async function loadModel() {
    const root = document.getElementById('model-root');
    try {
      const data = await JG.api('/dashboard/model-performance', { auth: false });
      if (data.available === false) {
        root.replaceChildren(el('div', { class: 'alert info', text: 'No evaluation metrics yet. Train a model with "python -m ml.train" and they will appear here.' }));
        return;
      }
      const selected = data.models[data.selected_model];
      const ds = data.dataset;
      root.replaceChildren(
        ds.synthetic ? el('div', { class: 'alert warn', role: 'note', text: 'These metrics were measured on a synthetic demo dataset, so they say nothing about real-world accuracy. Train on the real dataset for meaningful results.' }) : null,
        el('p', { class: 'muted', text: 'Selected model: ' + (MODEL_LABELS[data.selected_model] || data.selected_model) + '. Measured on ' + ds.test_rows + ' held-out postings from ' + ds.source + ' (' + (ds.fraud_rate * 100).toFixed(1) + '% fraudulent). Precision, recall and F1 describe the fraudulent class.' }),
        metricCards(selected),
        el('div', { class: 'panels' },
          el('section', { class: 'card' }, el('h3', { text: 'Confusion matrix' }), confusionMatrix(data.confusion_matrix)),
          el('section', { class: 'card' }, el('h3', { text: 'Model comparison' }), comparisonChart(data.models))));
    } catch (e) {
      root.replaceChildren(el('div', { class: 'alert error', role: 'alert', text: e.message }));
    }
  }

  async function loadUser() {
    const root = document.getElementById('user-root');
    if (!JG.isLoggedIn()) {
      root.replaceChildren(el('p', { class: 'muted' }, el('a', { href: 'login.html?next=dashboard.html', text: 'Log in' }), ' to see a summary of your own analyses.'));
      return;
    }
    try {
      const s = await JG.api('/dashboard/stats');
      root.replaceChildren(el('div', { class: 'metric-cards' },
        [['Analyses', s.total_analyses, 'm1'], ['Flagged fraudulent', s.fraudulent, 'm3'], ['Likely legitimate', s.legitimate, 'm2'], ['Average fraud probability', s.average_probability + '%', 'm4']].map(function (x) {
          return el('div', { class: 'metric ' + x[2] }, el('span', { text: x[0] }), el('b', { text: String(x[1]) }));
        })));
    } catch (e) {
      root.replaceChildren(el('div', { class: 'alert error', role: 'alert', text: e.message }));
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (document.body.dataset.page !== 'dashboard') return;
    loadModel();
    loadUser();
  });
})();
