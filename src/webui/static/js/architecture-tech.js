/**
 * CrazyAgentsManage — Tech architecture collaboration projection.
 */

var TECH_ARCH_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
};

function techFetchJSON(url) {
  return fetch(TECH_ARCH_CONFIG.apiBase + url)
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
}

function techEscapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function techStatusLabel(status) {
  var map = { healthy: '健康', degraded: '降级', unknown: '未知' };
  return map[status] || status || '未知';
}

function techRouteHref(path) {
  return TECH_ARCH_CONFIG.apiBase + path;
}

function renderTechCollaborationProjection(data) {
  var chain = document.getElementById('tech-collaboration-chain');
  var jumps = document.getElementById('tech-collaboration-jumps');
  if (!chain || !jumps) return;

  var nodes = (data && data.nodes) || [];
  if (!nodes.length) {
    chain.innerHTML = '<div class="ov-empty">暂无协作链路状态</div>';
    jumps.innerHTML = '<div class="ov-empty">暂无证据跳转</div>';
    return;
  }

  chain.innerHTML = nodes.map(function(node) {
    return '<div class="ov-gov-card">' +
      '<div class="ov-gov-card-label">' + techEscapeHtml(node.label || node.id || 'Node') + ' · ' + techEscapeHtml(techStatusLabel(node.status)) + '</div>' +
      '<div class="ov-gov-card-desc">' + techEscapeHtml(node.summary || '—') + '</div>' +
      '<div style="margin-top:10px;"><a class="ov-reference-link" href="' + techRouteHref(node.href || '/collaboration') + '"><span>查看节点证据</span></a></div>' +
    '</div>';
  }).join('');

  jumps.innerHTML = ((data && data.evidenceJumps) || []).map(function(item) {
    return '<a class="ov-reference-link" href="' + techRouteHref(item.href || '/collaboration') + '">' +
      '<span>' + techEscapeHtml(item.label || 'Evidence jump') + '</span>' +
      '<small>' + techEscapeHtml(item.desc || '—') + '</small>' +
    '</a>';
  }).join('');
}

function initTechArchitectureProjection() {
  techFetchJSON('/api/collaboration/graph-projection')
    .then(renderTechCollaborationProjection)
    .catch(function() {
      renderTechCollaborationProjection({ nodes: [], evidenceJumps: [] });
    });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTechArchitectureProjection);
} else {
  initTechArchitectureProjection();
}
