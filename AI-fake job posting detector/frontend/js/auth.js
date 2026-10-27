/* Shared helpers (API client, session, header) plus the login, register and profile pages.
   Everything rendered from server data goes through textContent, never innerHTML. */
(function () {
  'use strict';

  const API_BASE = window.API_BASE || '';
  const TOKEN_KEY = 'jg_token';
  const USER_KEY = 'jg_user';

  function getToken() { try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; } }
  function getUser() {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch (e) { return null; }
  }
  function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
  function clearSession() {
    try { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); } catch (e) { /* ignore */ }
  }
  function isLoggedIn() { return Boolean(getToken() && getUser()); }

  class ApiError extends Error {
    constructor(message, status) { super(message); this.status = status; }
  }

  function formatDetail(data) {
    if (!data || !data.detail) return '';
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map(function (d) {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : '';
        return (field ? field + ': ' : '') + (d.msg || 'Invalid value');
      }).join('. ');
    }
    return '';
  }

  async function api(path, options) {
    const opts = options || {};
    const headers = {};
    if (opts.body !== undefined) headers['Content-Type'] = 'application/json';
    const token = getToken();
    if (opts.auth !== false && token) headers.Authorization = 'Bearer ' + token;
    let response;
    try {
      response = await fetch(API_BASE + path, {
        method: opts.method || 'GET',
        headers: headers,
        body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
      });
    } catch (e) {
      throw new ApiError('Cannot reach the server. Check that the API is running and try again.', 0);
    }
    let data = null;
    if (response.status !== 204) {
      try { data = await response.json(); } catch (e) { data = null; }
    }
    if (!response.ok) {
      if (response.status === 401 && token) clearSession();
      throw new ApiError(formatDetail(data) || 'Request failed (' + response.status + ')', response.status);
    }
    return data;
  }

  /* ---- tiny DOM helpers ---- */
  function el(tag, props) {
    const node = document.createElement(tag);
    Object.entries(props || {}).forEach(function (entry) {
      const k = entry[0], v = entry[1];
      if (v === null || v === undefined || v === false) return;
      if (k === 'class') node.className = v;
      else if (k === 'text') node.textContent = v;
      else if (k.indexOf('on') === 0 && typeof v === 'function') node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : v);
    });
    Array.prototype.slice.call(arguments, 2).flat().forEach(function (child) {
      if (child === null || child === undefined || child === false) return;
      node.append(child.nodeType ? child : document.createTextNode(String(child)));
    });
    return node;
  }
  const SVG_NS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs) {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs || {}).forEach(function (e) { node.setAttribute(e[0], e[1]); });
    Array.prototype.slice.call(arguments, 2).forEach(function (c) { node.append(c); });
    return node;
  }
  function showError(container, message) {
    if (!container) return;
    container.textContent = message || '';
    if (message) container.focus && container.focus();
  }
  function formatDate(value) { return value ? String(value).slice(0, 10) : ''; }
  function percent(value) { return Number(value).toFixed(0) + '%'; }

  /* ---- header ---- */
  const NAV = [
    { page: 'home', href: 'index.html', label: 'Home' },
    { page: 'analyze', href: 'analyze.html', label: 'Analyze' },
    { page: 'history', href: 'history.html', label: 'History' },
    { page: 'dashboard', href: 'dashboard.html', label: 'Dashboard' },
  ];

  function logo() {
    return svg('svg', { width: 26, height: 26, viewBox: '0 0 24 24', 'aria-hidden': 'true' },
      svg('path', { d: 'M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Z', fill: '#2f7bff' }),
      svg('circle', { cx: 11, cy: 11, r: 3.6, fill: 'none', stroke: '#fff', 'stroke-width': 1.8 }),
      svg('path', { d: 'm13.8 13.8 3 3', stroke: '#fff', 'stroke-width': 1.8, 'stroke-linecap': 'round' }));
  }

  function renderHeader() {
    const host = document.getElementById('site-header');
    if (!host) return;
    const current = document.body.dataset.page === 'result' ? 'analyze' : document.body.dataset.page;
    const user = getUser();
    const account = isLoggedIn()
      ? el('div', { class: 'account' },
          el('a', { class: 'link', href: 'profile.html', text: user.full_name }),
          el('button', { class: 'btn ghost', type: 'button', text: 'Log out', onclick: function () { clearSession(); location.href = 'index.html'; } }))
      : el('div', { class: 'account' }, el('a', { class: 'btn ghost', href: 'login.html', text: 'Log in' }));
    host.replaceChildren(el('div', { class: 'bar' },
      el('a', { class: 'brand', href: 'index.html' }, logo(), 'JobGuard AI'),
      el('nav', { class: 'nav', 'aria-label': 'Main' }, NAV.map(function (n) {
        return el('a', { href: n.href, text: n.label, 'aria-current': n.page === current ? 'page' : null });
      })),
      account));
  }

  function requireLogin() {
    if (isLoggedIn()) return true;
    const next = location.pathname.split('/').pop() || 'index.html';
    location.replace('login.html?next=' + encodeURIComponent(next));
    return false;
  }

  function safeNext() {
    const next = new URLSearchParams(location.search).get('next') || '';
    return /^[a-z]+\.html$/.test(next) ? next : 'analyze.html';
  }

  /* ---- pages ---- */
  function bindAuthForm(formId, path, buildBody) {
    const form = document.getElementById(formId);
    if (!form) return;
    const errorBox = document.getElementById('form-error');
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      showError(errorBox, '');
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        const data = await api(path, { method: 'POST', body: buildBody(new FormData(form)), auth: false });
        setSession(data.access_token, data.user);
        location.href = safeNext();
      } catch (e) {
        showError(errorBox, e.message);
        button.disabled = false;
      }
    });
  }

  async function initProfile() {
    if (!requireLogin()) return;
    const user = getUser();
    document.getElementById('profile-name').textContent = user.full_name;
    document.getElementById('profile-email').textContent = user.email;
    document.getElementById('profile-joined').textContent = formatDate(user.created_at) || 'Not available';
    document.getElementById('logout-button').addEventListener('click', function () { clearSession(); location.href = 'index.html'; });
    try {
      const stats = await api('/dashboard/stats');
      document.getElementById('stat-total').textContent = stats.total_analyses;
      document.getElementById('stat-fraud').textContent = stats.fraudulent;
      document.getElementById('stat-legit').textContent = stats.legitimate;
      document.getElementById('stat-avg').textContent = stats.average_probability + '%';
    } catch (e) {
      showError(document.getElementById('form-error'), e.message);
    }
  }

  window.JG = { api: api, el: el, svg: svg, getUser: getUser, getToken: getToken, isLoggedIn: isLoggedIn,
    requireLogin: requireLogin, showError: showError, formatDate: formatDate, percent: percent, ApiError: ApiError };

  document.addEventListener('DOMContentLoaded', function () {
    renderHeader();
    const page = document.body.dataset.page;
    if (page === 'login') {
      bindAuthForm('login-form', '/auth/login', function (f) { return { email: f.get('email'), password: f.get('password') }; });
    } else if (page === 'register') {
      bindAuthForm('register-form', '/auth/register', function (f) {
        return { full_name: f.get('full_name'), email: f.get('email'), password: f.get('password') };
      });
    } else if (page === 'profile') {
      initProfile();
    }
  });
})();
