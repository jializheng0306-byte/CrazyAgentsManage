/**
 * CrazyAgentsManage — Collaboration Aggregation Page JS
 * Consumes canonical collaboration summary / evidence APIs.
 */

var CL_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
  refreshInterval: 30000,
  maxHandoffs: 8,
  maxTriage: 4,
};

function fetchJSON(url) {
  return fetch(CL_CONFIG.apiBase + url)
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
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

function statusLabel(status) {
  var map = {
    healthy: '健康',
    degraded: '降级',
    unknown: '未知'
  };
  return map[status] || status || '未知';
}

function routeHref(path) {
  return CL_CONFIG.apiBase + path;
}

function renderBriefing(summary) {
  var briefing = (summary && summary.briefing) || {};
  setText('cl-briefing-label', briefing.label || 'Collaboration aggregation');
  setText('cl-briefing-title', briefing.title || '协作聚合摘要不可用');
  setText('cl-briefing-copy', briefing.summary || '当前未拿到 collaboration summary payload。');

  var nextHop = (summary && summary.nextHop) || {};
  var nextHopEl = document.getElementById('cl-next-hop');
  if (nextHopEl) nextHopEl.href = routeHref(nextHop.href || '/collaboration');
  setText('cl-next-hop-label', nextHop.label || '继续查看协作面');
  setText('cl-next-hop-reason', nextHop.reason || '当前没有可用的下一跳建议。');
}

function renderMetrics(summary) {
  var counts = (summary && summary.counts) || {};
  setText('cl-handoff-count', counts.handoffCount || 0);
  setText('cl-trace-count', counts.openHandoffCount || 0);
  setText('cl-closeout-count', counts.pendingCloseoutCount || 0);
  setText('cl-snapshot-count', counts.snapshotCount || 0);
}

function renderTriage(summary) {
  var triage = (summary && summary.triage) || [];
  var list = document.getElementById('cl-triage-list');
  if (!list) return;

  if (!triage.length) {
    list.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">🧭</div><p>暂无协作缺口</p></div>';
    return;
  }

  list.innerHTML = triage.slice(0, CL_CONFIG.maxTriage).map(function(item) {
    var refs = (item.evidenceRefs || []).map(function(ref) {
      if (ref.href) {
        return '<a class="cl-evidence-link" href="' + routeHref(ref.href) + '">' + escapeHtml(ref.label) + '</a>';
      }
      return '<span class="cl-evidence-pill" title="' + escapeHtml(ref.path || '') + '">' + escapeHtml(ref.label) + '</span>';
    }).join('');
    return '<article class="cl-triage-card">' +
      '<div class="cl-triage-head">' +
        '<div>' +
          '<span class="cl-triage-label">' + escapeHtml(item.label || 'Triage') + '</span>' +
          '<div class="cl-triage-value">' + escapeHtml(item.count || 0) + '</div>' +
        '</div>' +
        '<span class="cl-handoff-badge ' + escapeHtml(item.status || 'unknown') + '">' + escapeHtml(statusLabel(item.status || 'unknown')) + '</span>' +
      '</div>' +
      '<p class="cl-triage-desc">' + escapeHtml(item.summary || '—') + '</p>' +
      '<div class="cl-evidence-links">' + refs + '</div>' +
    '</article>';
  }).join('');
}

function renderEvidenceChain(summary) {
  var chain = (summary && summary.evidenceChain) || [];
  var list = document.getElementById('cl-evidence-chain');
  if (!list) return;

  if (!chain.length) {
    list.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">🪢</div><p>暂无统一证据链</p></div>';
    return;
  }

  list.innerHTML = chain.map(function(item) {
    var playbook = item.playbook || {};
    var commands = (playbook.commands || []).map(function(cmd) {
      return '<span class="cl-evidence-pill" title="' + escapeHtml(cmd) + '">' + escapeHtml(cmd) + '</span>';
    }).join('');
    var writebacks = (playbook.writebackPaths || []).map(function(path) {
      return '<span class="cl-evidence-pill" title="' + escapeHtml(path) + '">' + escapeHtml(path) + '</span>';
    }).join('');
    var refs = (item.evidenceRefs || []).map(function(ref) {
      if (ref.href) {
        return '<a class="cl-evidence-link" href="' + routeHref(ref.href) + '">' + escapeHtml(ref.label) + '</a>';
      }
      return '<span class="cl-evidence-pill" title="' + escapeHtml(ref.path || '') + '">' + escapeHtml(ref.label) + '</span>';
    }).join('');
    return '<article class="cl-triage-card cl-chain-card">' +
      '<div class="cl-triage-head">' +
        '<div>' +
          '<span class="cl-triage-label">' + escapeHtml(item.label || 'Evidence stage') + '</span>' +
          '<div class="cl-chain-next-actor">' + escapeHtml(item.nextActor || '--') + '</div>' +
        '</div>' +
        '<span class="cl-handoff-badge ' + escapeHtml(item.status || 'unknown') + '">' + escapeHtml(statusLabel(item.status || 'unknown')) + '</span>' +
      '</div>' +
      '<p class="cl-triage-desc">' + escapeHtml(item.summary || '—') + '</p>' +
      '<p class="cl-chain-next-action">' + escapeHtml(item.nextAction || '—') + '</p>' +
      (playbook.routeHref ? '<a class="cl-chain-primary-link" href="' + routeHref(playbook.routeHref) + '">' + escapeHtml(playbook.routeLabel || '打开处理工作面') + '</a>' : '') +
      (commands ? '<div class="cl-chain-subtitle">Canonical commands</div><div class="cl-evidence-links">' + commands + '</div>' : '') +
      (writebacks ? '<div class="cl-chain-subtitle">Writeback paths</div><div class="cl-evidence-links">' + writebacks + '</div>' : '') +
      '<div class="cl-chain-subtitle">Evidence refs</div>' +
      '<div class="cl-evidence-links">' + refs + '</div>' +
    '</article>';
  }).join('');
}

function renderHandoffs(summary) {
  var handoffs = (summary && summary.handoffs) || [];
  var list = document.getElementById('cl-handoff-list');
  if (!list) return;

  if (!handoffs.length) {
    list.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">📤</div><p>暂无交接包</p></div>';
    return;
  }

  list.innerHTML = handoffs.slice(0, CL_CONFIG.maxHandoffs).map(function(h) {
    var artifacts = (h.artifactsToReview || []).slice(0, 3).map(function(item) {
      return '<span class="cl-evidence-pill" title="' + escapeHtml(item) + '">' + escapeHtml(item) + '</span>';
    }).join('');
    var jumpHref = h.queueStatus === 'open' ? '/collaboration/tasks' : '/operations#harness';
    return '<div class="cl-handoff-item">' +
      '<span class="cl-handoff-icon">📤</span>' +
      '<div class="cl-handoff-info">' +
        '<p class="cl-handoff-name">' + escapeHtml(h.title || h.name || '未命名') + '</p>' +
        '<p class="cl-handoff-preview" title="' + escapeHtml(h.preview || '') + '">' + escapeHtml(h.preview || '—') + '</p>' +
        '<div class="cl-evidence-links" style="margin-top:8px;">' + (artifacts || '<span class="cl-evidence-pill">无 artifacts</span>') + '</div>' +
      '</div>' +
      '<div class="cl-handoff-meta">' +
        '<span class="cl-handoff-badge ' + escapeHtml(h.severity || 'pending') + '">' + escapeHtml(h.runtimeStatus || 'unknown') + '</span>' +
        '<span class="cl-handoff-time">' + escapeHtml(relativeTime(h.updated_at)) + '</span>' +
        '<a class="cl-evidence-link" href="' + routeHref(jumpHref) + '">继续处理</a>' +
      '</div>' +
    '</div>';
  }).join('');
}

function renderEvidence(summary) {
  var grid = document.getElementById('cl-trace-grid');
  if (!grid) return;

  var snapshot = summary.runtimeSnapshot || {};
  var harness = summary.harness || {};
  var items = [];

  if (snapshot.exists) {
    items.push({
      type: 'snapshot',
      name: (snapshot.data && snapshot.data.phase) || 'runtime snapshot',
      meta: (snapshot.data && snapshot.data.updated_at) || '--',
      desc: (snapshot.data && snapshot.data.summary) || '当前协作轮次的 runtime-local phase / status / actor 摘要。',
      refs: [
        { label: '任务协作工作台', href: '/collaboration/tasks' },
        { label: 'Runtime sessions', href: '/runtime/sessions' },
      ],
    });
  }

  if (harness.latest_closeout) {
    items.push({
      type: 'closeout',
      name: harness.latest_closeout.id || '最新 closeout',
      meta: harness.latest_closeout.timestamp || '--',
      desc: harness.latest_closeout.message || '最近一次 closeout artifact。',
      refs: [
        { label: 'Harness readiness', href: '/operations#harness' },
        { label: 'Governance graph', href: '/governance/graph' },
      ],
    });
  }

  if (harness.latest_success) {
    items.push({
      type: 'success',
      name: harness.latest_success.id || '最近成功 trace',
      meta: harness.latest_success.timestamp || '--',
      desc: harness.latest_success.message || '最近一条成功执行 evidence。',
      refs: [{ label: 'Harness readiness', href: '/operations#harness' }],
    });
  }

  if (!items.length) {
    grid.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">📋</div><p>暂无协作证据</p></div>';
    return;
  }

  grid.innerHTML = items.map(function(item) {
    var refs = (item.refs || []).map(function(ref) {
      return '<a class="cl-evidence-link" href="' + routeHref(ref.href) + '">' + escapeHtml(ref.label) + '</a>';
    }).join('');
    return '<div class="cl-trace-card">' +
      '<span class="cl-trace-type ' + escapeHtml(item.type) + '">' + escapeHtml(item.type) + '</span>' +
      '<div class="cl-trace-name">' + escapeHtml(item.name) + '</div>' +
      '<div class="cl-trace-meta">' + escapeHtml(item.meta) + '</div>' +
      '<p class="cl-trace-desc">' + escapeHtml(item.desc) + '</p>' +
      '<div class="cl-evidence-links" style="margin-top:12px;">' + refs + '</div>' +
    '</div>';
  }).join('');
}

function renderEvidenceJumps(summary) {
  var container = document.getElementById('cl-evidence-jumps');
  if (!container) return;
  var items = (summary && summary.evidenceJumps) || [];
  if (!items.length) {
    container.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">🔗</div><p>暂无证据跳转</p></div>';
    return;
  }
  container.innerHTML = items.map(function(item) {
    return '<a class="cl-support-link" href="' + routeHref(item.href || '/collaboration') + '">' +
      '<strong>' + escapeHtml(item.label || 'Evidence jump') + '</strong>' +
      '<span>' + escapeHtml(item.desc || '—') + '</span>' +
    '</a>';
  }).join('');
}

function loadCollaboration() {
  fetchJSON('/api/collaboration/summary').then(function(summary) {
    renderBriefing(summary || {});
    renderMetrics(summary || {});
    renderTriage(summary || {});
    renderEvidenceChain(summary || {});
    renderHandoffs(summary || {});
    renderEvidence(summary || {});
    renderEvidenceJumps(summary || {});
  }).catch(function() {
    renderBriefing({});
    renderMetrics({});
    renderTriage({ triage: [] });
    renderEvidenceChain({ evidenceChain: [] });
    renderHandoffs({ handoffs: [] });
    renderEvidence({ runtimeSnapshot: {}, harness: {} });
    renderEvidenceJumps({ evidenceJumps: [] });
  });
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
