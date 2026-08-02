/**
 * Ontology Semantic Layer — visualization logic
 * Vanilla JS, no frameworks. SVG rendering.
 */
(function () {
  'use strict';

  const BASE = window.BASE || '';
  const REFRESH_INTERVAL = 60000; // 60s polling

  let refreshTimer = null;

  // ── Color palettes ──
  const DOMAIN_COLORS = {
    D1_GTD: '#3B82F6',
    D2_MetaOntology: '#22C55E',
    D3_OKF: '#F59E0B',
    D4_KG: '#8B5CF6',
    D5_Memory: '#06B6D4',
    Horizontal: '#94A3B8',
  };

  const TYPE_COLORS = {
    object: '#3B82F6',
    action: '#F59E0B',
    constraint: '#EF4444',
    context: '#22C55E',
    relation: '#8B5CF6',
    risk: '#F97316',
  };

  // ── API helpers ──
  function api(path) {
    return fetch(BASE + '/api' + path).then(function (r) {
      if (!r.ok) throw new Error(path + ' ' + r.status);
      return r.json();
    });
  }

  // ── Render: metrics ──
  function renderMetrics(data) {
    document.getElementById('gv-ont-dsl-count').textContent = data.dsl_stats?.total ?? '--';
    document.getElementById('gv-ont-okf-count').textContent = data.okf_stats?.total ?? '--';
    document.getElementById('gv-ont-domain-count').textContent = Object.keys(data.domains || {}).length;
    document.getElementById('gv-ont-agent-count').textContent = '4';
  }

  // ── Render: radar chart ──
  function renderRadarChart(domains) {
    var container = document.getElementById('gv-ont-radar');
    var keys = Object.keys(domains);
    if (!keys.length) { container.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>无领域数据</p></div>'; return; }

    var w = 400, h = 360, cx = 200, cy = 180, r = 130;
    var n = keys.length;
    var maxVal = 0;
    keys.forEach(function (k) { maxVal = Math.max(maxVal, domains[k].total || 0); });
    maxVal = Math.max(maxVal, 1);

    var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';

    // concentric rings
    for (var ring = 1; ring <= 4; ring++) {
      var rr = r * ring / 4;
      svg += '<circle cx="' + cx + '" cy="' + cy + '" r="' + rr + '" fill="none" stroke="#334155" stroke-width="1"/>';
    }

    // axis lines
    for (var i = 0; i < n; i++) {
      var angle = -Math.PI / 2 + (2 * Math.PI * i) / n;
      var x = cx + r * Math.cos(angle);
      var y = cy + r * Math.sin(angle);
      svg += '<line x1="' + cx + '" y1="' + cy + '" x2="' + x + '" y2="' + y + '" stroke="#475569" stroke-width="1"/>';
    }

    // polygon
    var pts = [];
    for (var i2 = 0; i2 < n; i2++) {
      var a2 = -Math.PI / 2 + (2 * Math.PI * i2) / n;
      var val = domains[keys[i2]].total || 0;
      var dist = r * val / maxVal;
      pts.push((cx + dist * Math.cos(a2)).toFixed(1) + ',' + (cy + dist * Math.sin(a2)).toFixed(1));
    }
    svg += '<polygon points="' + pts.join(' ') + '" fill="rgba(59,130,246,0.15)" stroke="#3B82F6" stroke-width="2"/>';

    // vertex labels
    for (var i3 = 0; i3 < n; i3++) {
      var a3 = -Math.PI / 2 + (2 * Math.PI * i3) / n;
      var lx = cx + (r + 32) * Math.cos(a3);
      var ly = cy + (r + 32) * Math.sin(a3);
      var color = DOMAIN_COLORS[keys[i3]] || '#94A3B8';
      var label = keys[i3].replace('_', ' ');
      var count = domains[keys[i3]].total || 0;
      svg += '<text x="' + lx.toFixed(1) + '" y="' + ly.toFixed(1) + '" text-anchor="middle" dominant-baseline="middle" fill="' + color + '" font-size="11" font-weight="600">' + label + '</text>';
      svg += '<text x="' + lx.toFixed(1) + '" y="' + (ly + 14).toFixed(1) + '" text-anchor="middle" dominant-baseline="middle" fill="#94A3B8" font-size="10">' + count + '</text>';
    }

    // center label
    svg += '<text x="' + cx + '" y="' + cy + '" text-anchor="middle" dominant-baseline="middle" fill="#94A3B8" font-size="10">本体语义层</text>';

    svg += '</svg>';
    container.innerHTML = svg;
  }

  // ── Render: type distribution ──
  function renderTypeChart(byType) {
    var container = document.getElementById('gv-ont-type-chart');
    var keys = Object.keys(byType || {});
    if (!keys.length) { container.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>无数据</p></div>'; return; }

    var maxVal = 0;
    keys.forEach(function (k) { maxVal = Math.max(maxVal, byType[k]); });
    maxVal = Math.max(maxVal, 1);

    var html = '';
    keys.forEach(function (k) {
      var pct = Math.round(byType[k] / maxVal * 100);
      var color = TYPE_COLORS[k] || '#94A3B8';
      html += '<div class="gv-ont-type-bar">';
      html += '<span class="gv-ont-type-bar-label">' + k + '</span>';
      html += '<div class="gv-ont-type-bar-fill" style="width:' + pct + '%;background:' + color + '"></div>';
      html += '<span class="gv-ont-type-bar-count">' + byType[k] + '</span>';
      html += '</div>';
    });
    container.innerHTML = html;
  }

  // ── Render: DSL → Agent flow ──
  function renderFlowDiagram() {
    var container = document.getElementById('gv-ont-flow');
    var w = 640, h = 180;

    var nodes = [
      { id: 'dsl', label: 'Canonical DSL', sub: '111条目 · 6类', x: 50, y: 65, w: 110, h: 50, color: '#3B82F6' },
      { id: 'okf', label: 'OKF 投影层', sub: '124条目 · 只读', x: 195, y: 65, w: 110, h: 50, color: '#22C55E' },
      { id: 'bridge', label: 'Bridge Surface', sub: '6 消费面', x: 340, y: 65, w: 110, h: 50, color: '#F59E0B' },
      { id: 'agent', label: '开发智能体', sub: '4 类消费者', x: 485, y: 65, w: 110, h: 50, color: '#8B5CF6' },
    ];

    var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';

    // arrows
    function arrow(x1, y1, x2, y2) {
      var midY = y1 + y2 / 2; // not used, keeping simple
      return '<line x1="' + x1 + '" y1="' + (y1 + 25) + '" x2="' + x2 + '" y2="' + (y2 + 25) + '" stroke="#475569" stroke-width="2" marker-end="url(#arrowhead)"/>';
    }

    svg += '<defs><marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#475569"/></marker></defs>';

    for (var i = 0; i < nodes.length - 1; i++) {
      svg += arrow(nodes[i].x + nodes[i].w, nodes[i].y, nodes[i + 1].x, nodes[i + 1].y);
    }

    // edge labels
    var edgeLabels = ['PROJECTS_TO', 'CONSUMES', 'QUERIES'];
    for (var j = 0; j < edgeLabels.length; j++) {
      var ex = nodes[j].x + nodes[j].w + (nodes[j + 1].x - nodes[j].x - nodes[j].w) / 2 - 24;
      svg += '<text x="' + ex + '" y="' + (nodes[j].y + 15) + '" text-anchor="middle" fill="#64748B" font-size="9">' + edgeLabels[j] + '</text>';
    }

    // nodes
    nodes.forEach(function (nd) {
      svg += '<rect x="' + nd.x + '" y="' + nd.y + '" width="' + nd.w + '" height="' + nd.h + '" rx="8" ry="8" fill="' + nd.color + '15" stroke="' + nd.color + '" stroke-width="1.5"/>';
      svg += '<text x="' + (nd.x + nd.w / 2) + '" y="' + (nd.y + 18) + '" text-anchor="middle" fill="' + nd.color + '" font-size="11" font-weight="600">' + nd.label + '</text>';
      svg += '<text x="' + (nd.x + nd.w / 2) + '" y="' + (nd.y + 36) + '" text-anchor="middle" fill="#94A3B8" font-size="9">' + nd.sub + '</text>';
    });

    svg += '</svg>';
    container.innerHTML = svg;
  }

  // ── Render: protocol cards ──
  function renderProtocol() {
    var container = document.getElementById('gv-ont-protocol');
    var layers = [
      { l: '1', title: 'Layer 1: DSL Query 层', desc: 'semantic-query CLI — get/search/summary，107 条可查询。优先通过 CLI 确认语义层覆盖。', meta: '路径: packages/ontology/dist/semantic-query/cli.js', cls: '' },
      { l: '2', title: 'Layer 2: OKF 投影层', desc: 'docs/okf/ 只读投影，验证 DSL↔OKF 同步。124 个投影条目覆盖全部 6 种类型。', meta: '路径: docs/okf/', cls: 'l2' },
      { l: '3', title: 'Layer 3: Bridge Surface 层', desc: 'mcp-server semantic-bridge-context.service.ts — 6 个消费面（truth/candidate/context-pack/feedback/trace/task）。', meta: '路径: packages/mcp-server/src/services/', cls: 'l3' },
      { l: '4', title: 'Layer 4: 原始实现层', desc: 'packages/*/src/ — 仅在前三层不足以回答问题时读取，需明确标记下钻原因。', meta: '触发条件: L1-L3 insufficient + 下钻原因标注', cls: 'l4' },
    ];

    var html = '';
    layers.forEach(function (ly) {
      html += '<div class="gv-ont-protocol-card ' + ly.cls + '">';
      html += '<div class="gv-ont-protocol-card-title">' + ly.title + '</div>';
      html += '<div class="gv-ont-protocol-card-desc">' + ly.desc + '</div>';
      html += '<div class="gv-ont-protocol-card-meta"><span>' + ly.meta + '</span></div>';
      html += '</div>';
    });
    container.innerHTML = html;
  }

  // ── Render: agent matrix ──
  function renderAgentMatrix(agents) {
    var container = document.getElementById('gv-ont-agent-table');
    if (!agents || !agents.length) {
      container.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>无数据</p></div>';
      return;
    }

    var html = '<table class="gv-ont-agent-table">';
    html += '<thead><tr><th>Agent</th><th>环境</th><th>入口</th><th>协议</th><th>Hook/Skill</th></tr></thead>';
    html += '<tbody>';
    agents.forEach(function (a) {
      html += '<tr>';
      html += '<td><span class="gv-ont-agent-name">' + a.id + '</span></td>';
      html += '<td>' + a.environment + '</td>';
      html += '<td>' + a.entry + '</td>';
      html += '<td>' + a.protocol + '</td>';
      html += '<td>';
      (a.hooks || []).forEach(function (h) {
        html += '<span class="gv-ont-hook-tag">' + h + '</span>';
      });
      html += '</td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  }

  // ── Main load ──
  function loadAll() {
    api('/ontology/domains').then(function (data) {
      renderMetrics(data);
      renderRadarChart(data.domains || {});
      renderTypeChart(data.dsl_stats?.by_type || {});
      renderFlowDiagram();
      renderProtocol();
    }).catch(function (err) {
      console.error('Ontology load failed:', err);
    });

    api('/ontology/agents').then(function (data) {
      renderAgentMatrix(data.agents || []);
    }).catch(function (err) {
      console.error('Agents load failed:', err);
    });
  }

  // ── Init ──
  document.addEventListener('DOMContentLoaded', function () {
    loadAll();
    refreshTimer = setInterval(loadAll, REFRESH_INTERVAL);

    var refreshBtn = document.getElementById('gv-ont-refresh');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', function () {
        loadAll();
      });
    }
  });

  // cleanup on navigation
  window.addEventListener('beforeunload', function () {
    if (refreshTimer) clearInterval(refreshTimer);
  });
})();
