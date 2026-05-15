/**
 * CrazyAgentsManage — Collaboration Aggregation Page JS
 * Consumes handoff/snapshot/closeout/evidence APIs
 */

var CL_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
  refreshInterval: 30000,
  maxHandoffs: 8,
  maxTraces: 6,
};

function fetchJSON(url) {
  return fetch(CL_CONFIG.apiBase + url)
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function relativeTime(isoStr) {
  if (!isoStr) return '--';
  var d = new Date(isoStr);
  var diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return Math.round(diff) + 's ago';
  if (diff < 3600) return Math.round(diff / 60) + 'm ago';
  if (diff < 86400) return Math.round(diff / 3600) + 'h ago';
  return Math.round(diff / 86400) + 'd ago';
}

function renderMetrics() {
  fetchJSON('/api/runtime/handoffs').then(function(handoffs) {
    setText('cl-handoff-count', Array.isArray(handoffs) ? handoffs.length : 0);
  }).catch(function() { setText('cl-handoff-count', '0'); });

  fetchJSON('/api/runtime/harness-summary').then(function(summary) {
    var success = summary.success_count || 0;
    var failure = summary.failure_count || 0;
    setText('cl-trace-count', success + failure);
    setText('cl-closeout-count', failure);
  }).catch(function() {
    setText('cl-trace-count', '0');
    setText('cl-closeout-count', '0');
  });

  fetchJSON('/api/runtime/state').then(function(state) {
    var hasState = state && state.exists;
    setText('cl-snapshot-count', hasState ? '1' : '0');
  }).catch(function() { setText('cl-snapshot-count', '0'); });
}

function renderHandoffs() {
  var list = document.getElementById('cl-handoff-list');

  fetchJSON('/api/runtime/handoffs').then(function(handoffs) {
    if (!Array.isArray(handoffs) || handoffs.length === 0) {
      list.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">📤</div><p>暂无交接包</p></div>';
      return;
    }

    var limited = handoffs.slice(0, CL_CONFIG.maxHandoffs);

    list.innerHTML = limited.map(function(h) {
      return '<div class="cl-handoff-item">' +
        '<span class="cl-handoff-icon">📤</span>' +
        '<div class="cl-handoff-info">' +
          '<p class="cl-handoff-name">' + (h.name || '未命名') + '</p>' +
          '<p class="cl-handoff-preview" title="' + (h.preview || '') + '">' + (h.preview || '—') + '</p>' +
        '</div>' +
        '<div class="cl-handoff-meta">' +
          '<span class="cl-handoff-badge">主协作对象</span>' +
          '<span class="cl-handoff-time">' + relativeTime(h.updated_at) + '</span>' +
        '</div>' +
      '</div>';
    }).join('');
  }).catch(function() {
    list.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function renderTraces() {
  var grid = document.getElementById('cl-trace-grid');

  fetchJSON('/api/runtime/harness-summary').then(function(summary) {
    var items = [];

    if (summary.latest_success) {
      items.push({
        type: 'success',
        name: summary.latest_success.name || summary.latest_success.id || '成功记录',
        meta: summary.latest_success.timestamp || '--',
        desc: '最近成功执行，作为交接闭环的结果证据。'
      });
    }

    if (summary.latest_failure) {
      items.push({
        type: 'failure',
        name: summary.latest_failure.name || summary.latest_failure.id || '失败记录',
        meta: summary.latest_failure.timestamp || '--',
        desc: '最近失败执行，作为协作排障与复核证据。'
      });
    }

    if (items.length === 0) {
      grid.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">📋</div><p>暂无追踪记录</p></div>';
      return;
    }

    grid.innerHTML = items.slice(0, CL_CONFIG.maxTraces).map(function(t) {
      return '<div class="cl-trace-card">' +
        '<span class="cl-trace-type ' + t.type + '">' + (t.type === 'success' ? '支持证据 / 成功' : '支持证据 / 失败') + '</span>' +
        '<div class="cl-trace-name">' + t.name + '</div>' +
        '<div class="cl-trace-meta">' + t.meta + '</div>' +
        '<p class="cl-trace-desc">' + t.desc + '</p>' +
      '</div>';
    }).join('');
  }).catch(function() {
    grid.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function loadCollaboration() {
  renderMetrics();
  renderHandoffs();
  renderTraces();
}

function init() {
  loadCollaboration();
  setInterval(loadCollaboration, CL_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
