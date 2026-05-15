/**
 * CrazyAgentsManage — Governance Workbench JS
 * Uses existing graph + agent APIs without changing backend semantics.
 */

var GV_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
  refreshInterval: 60000,
  maxNodes: 8,
  maxAgents: 6,
};

function gvFetchJSON(url) {
  return fetch(GV_CONFIG.apiBase + url).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
}

function gvSetText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function gvEscape(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderGovernance(graphData, agents) {
  var nodes = (graphData && graphData.nodes) || [];
  var edges = (graphData && graphData.edges) || [];
  var agentNodes = nodes.filter(function(n) { return n.type === 'agent'; });
  var connectedCount = nodes.filter(function(n) { return n.platform_state === 'connected'; }).length;

  gvSetText('gv-node-count', nodes.length);
  gvSetText('gv-agent-count', agentNodes.length || (Array.isArray(agents) ? agents.length : 0));
  gvSetText('gv-edge-count', edges.length);
  gvSetText('gv-connected-count', connectedCount);

  renderNodeList(nodes, edges);
  renderGraphPreview(nodes, edges);
  renderLegends(nodes, edges);
  renderAgentList(Array.isArray(agents) ? agents : agentNodes);
}

function nodeDegree(nodeId, edges) {
  return edges.filter(function(e) { return e.source === nodeId || e.target === nodeId; }).length;
}

function renderNodeList(nodes, edges) {
  var host = document.getElementById('gv-node-list');
  if (!host) return;

  if (!Array.isArray(nodes) || nodes.length === 0) {
    host.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>暂无治理节点</p></div>';
    return;
  }

  var ranked = nodes.slice().sort(function(a, b) {
    return nodeDegree(b.id, edges) - nodeDegree(a.id, edges);
  }).slice(0, GV_CONFIG.maxNodes);

  host.innerHTML = ranked.map(function(node) {
    var degree = nodeDegree(node.id, edges);
    var typeLabel = node.type === 'coordinator' ? 'graph node' : 'agent node';
    return '<div class="gv-node-card">' +
      '<div class="gv-node-top">' +
        '<div>' +
          '<p class="gv-node-name">' + gvEscape((node.icon || '') + ' ' + (node.name || node.id || '未命名节点')) + '</p>' +
          '<div class="gv-node-sub">' + gvEscape(node.id || '—') + '</div>' +
        '</div>' +
        '<span class="gv-node-badge ' + gvEscape(node.type || 'agent') + '">' + gvEscape(typeLabel) + '</span>' +
      '</div>' +
      '<div class="gv-node-meta">关联 ' + degree + ' 条关系 · 会话 ' + (node.session_count || 0) + ' · 状态 ' + gvEscape(node.platform_state || 'topology') + '</div>' +
    '</div>';
  }).join('');
}

function renderGraphPreview(nodes, edges) {
  var host = document.getElementById('gv-graph-preview');
  if (!host) return;

  if (!Array.isArray(nodes) || nodes.length === 0) {
    host.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>暂无图谱数据</p></div>';
    return;
  }

  var centerX = 50;
  var centerY = 50;
  var outer = nodes.filter(function(n) { return n.type !== 'coordinator'; });
  var radius = Math.max(22, Math.min(38, 82 / Math.sqrt(outer.length || 1)));
  var angleStep = (2 * Math.PI) / Math.max(outer.length, 1);
  var positions = {};

  nodes.forEach(function(node) {
    if (node.type === 'coordinator') {
      positions[node.id] = { x: centerX, y: centerY };
    } else {
      var outerIndex = outer.findIndex(function(item) { return item.id === node.id; });
      var angle = -Math.PI / 2 + outerIndex * angleStep;
      positions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    }
  });

  var svg = '<svg viewBox="0 0 100 100" class="gv-graph-canvas">';
  edges.forEach(function(edge) {
    var from = positions[edge.source];
    var to = positions[edge.target];
    if (!from || !to) return;
    var color = edge.type === 'coordinator' ? '#3B82F6' : (edge.type === 'dataflow' ? '#22C55E' : '#8B5CF6');
    svg += '<line x1="' + from.x + '" y1="' + from.y + '" x2="' + to.x + '" y2="' + to.y + '" stroke="' + color + '" stroke-width="0.5" stroke-dasharray="1.2 1.2" opacity="0.7"></line>';
  });
  nodes.forEach(function(node) {
    var pos = positions[node.id];
    var fill = node.type === 'coordinator' ? '#3B82F6' : '#8B5CF6';
    svg += '<circle cx="' + pos.x + '" cy="' + pos.y + '" r="' + (node.type === 'coordinator' ? 5 : 3.6) + '" fill="' + fill + '"></circle>';
    svg += '<text x="' + pos.x + '" y="' + (pos.y + (node.type === 'coordinator' ? 9 : 7)) + '" fill="#cbd5e1" font-size="3" text-anchor="middle">' + gvEscape((node.name || node.id || '').slice(0, 12)) + '</text>';
  });
  svg += '</svg>';
  host.innerHTML = svg;
}

function renderLegends(nodes, edges) {
  var nodeHost = document.getElementById('gv-node-legend');
  var edgeHost = document.getElementById('gv-edge-legend');
  if (nodeHost) {
    var groupedNodes = {};
    (nodes || []).forEach(function(node) {
      groupedNodes[node.type || 'node'] = (groupedNodes[node.type || 'node'] || 0) + 1;
    });
    nodeHost.innerHTML = Object.keys(groupedNodes).map(function(type) {
      var color = type === 'coordinator' ? '#3B82F6' : '#8B5CF6';
      var label = type === 'coordinator' ? 'graph node' : (type === 'agent' ? 'agent node' : type);
      return '<div class="gv-legend-item"><span><span class="gv-legend-dot" style="background:' + color + '"></span>' + gvEscape(label) + '</span><span>' + groupedNodes[type] + '</span></div>';
    }).join('');
  }
  if (edgeHost) {
    var groupedEdges = {};
    (edges || []).forEach(function(edge) {
      groupedEdges[edge.type || 'relation'] = (groupedEdges[edge.type || 'relation'] || 0) + 1;
    });
    edgeHost.innerHTML = Object.keys(groupedEdges).map(function(type) {
      return '<div class="gv-legend-item"><span>' + gvEscape(type) + '</span><span>' + groupedEdges[type] + '</span></div>';
    }).join('');
  }
}

function renderAgentList(agents) {
  var host = document.getElementById('gv-agent-list');
  if (!host) return;

  if (!Array.isArray(agents) || agents.length === 0) {
    host.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>暂无 Agent 节点数据</p></div>';
    return;
  }

  host.innerHTML = agents.slice(0, GV_CONFIG.maxAgents).map(function(agent) {
    var stateClass = agent.platform_state === 'connected' ? 'connected' : ((agent.platform_state === 'error' || agent.platform_state === 'disconnected' || agent.platform_state === 'fatal') ? 'error' : 'unknown');
    return '<div class="gv-agent-card">' +
      '<div class="gv-agent-top">' +
        '<div>' +
          '<p class="gv-agent-name">' + gvEscape((agent.icon || '') + ' ' + (agent.name || agent.id || '未命名 Agent')) + '</p>' +
          '<div class="gv-agent-sub">' + gvEscape(agent.source || agent.id || '—') + '</div>' +
        '</div>' +
        '<span class="gv-state-badge ' + stateClass + '">' + gvEscape(agent.platform_state || 'unknown') + '</span>' +
      '</div>' +
      '<div class="gv-agent-meta">会话 ' + (agent.session_count || 0) + ' · Token ' + (agent.total_tokens || 0) + ' · 成功率 ' + ((agent.success_rate == null ? '--' : agent.success_rate + '%')) + '</div>' +
    '</div>';
  }).join('');
}

function loadGovernance() {
  Promise.all([
    gvFetchJSON('/api/graph/data').catch(function() { return { nodes: [], edges: [] }; }),
    gvFetchJSON('/api/agents/list').catch(function() { return []; })
  ]).then(function(results) {
    renderGovernance(results[0], results[1]);
  }).catch(function() {
    renderGovernance({ nodes: [], edges: [] }, []);
  });
}

function initGovernance() {
  loadGovernance();
  setInterval(loadGovernance, GV_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGovernance);
} else {
  initGovernance();
}
