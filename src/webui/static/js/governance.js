/**
 * CrazyAgentsManage — Governance Aggregation Page JS
 * Consumes candidate/truth/review/feedback/drift APIs (placeholder)
 */

var GV_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
  refreshInterval: 60000,
};

function fetchJSON(url) {
  return fetch(GV_CONFIG.apiBase + url)
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderMetrics() {
  setText('gv-candidate-count', '--');
  setText('gv-truth-count', '--');
  setText('gv-review-count', '--');
  setText('gv-drift-count', '--');
}

function loadGovernance() {
  renderMetrics();
}

function init() {
  loadGovernance();
  setInterval(loadGovernance, GV_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
