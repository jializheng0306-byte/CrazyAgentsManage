/**
 * CrazyAgentsManage — Overview Dashboard JS
 * Macro-level monitoring of Hermes Agent system
 */

const OVERVIEW_CONFIG = {
  apiBase: document.body && document.body.dataset ? (document.body.dataset.base || '') : '',
  refreshInterval: 15000,
  maxErrors: 10,
  maxActiveSessions: 12,
};

function withBase(path) {
  var base = OVERVIEW_CONFIG.apiBase || '';
  var normalizedPath = path.startsWith('/') ? path : '/' + path;
  return base + normalizedPath;
}

/* ---- Utilities ---- */
function fmt(n) {
  if (n == null) return '--';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return n.toString();
}

function fmtDuration(sec) {
  if (!sec) return '--';
  if (sec >= 3600) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    return h + 'h ' + m + 'm';
  }
  if (sec >= 60) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return m + 'm ' + s + 's';
  }
  return Math.round(sec) + 's';
}

function fmtMs(ms) {
  if (!ms) return '--';
  if (ms >= 1000) return (ms / 1000).toFixed(1) + 's';
  return Math.round(ms) + 'ms';
}

function relativeTime(ts) {
  if (!ts) return '--';
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return Math.round(diff) + 's ago';
  if (diff < 3600) return Math.round(diff / 60) + 'm ago';
  if (diff < 86400) return Math.round(diff / 3600) + 'h ago';
  return Math.round(diff / 86400) + 'd ago';
}

function fetchJSON(url) {
  return fetch(withBase(url))
    .then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
}

/* ---- Renderers ---- */

function renderMetrics(data) {
  document.getElementById('metric-total-sessions').textContent = fmt(data.total_sessions || 0);
  document.getElementById('metric-active-count').textContent = data.active_sessions || 0;
  document.getElementById('active-count-badge').textContent = data.active_sessions || 0;

  const totalTokens = (data.total_input || 0) + (data.total_output || 0);
  document.getElementById('metric-total-tokens').textContent = fmt(totalTokens);

  document.getElementById('metric-tool-calls').textContent = fmt(data.total_tool_calls || 0);
  document.getElementById('metric-error-count').textContent = fmt(data.error_count || 0);

  const avgTps = data.avg_tps ? data.avg_tps.toFixed(1) : '--';
  document.getElementById('metric-avg-tps').textContent = avgTps;

  /* Active indicator */
  const indicator = document.getElementById('indicator-active');
  indicator.className = 'ov-metric-indicator ' + (data.active_sessions > 0 ? 'active' : 'inactive');
}

function renderActiveSessions(sessions) {
  const grid = document.getElementById('active-sessions-grid');
  const limited = (sessions || []).slice(0, OVERVIEW_CONFIG.maxActiveSessions);

  if (limited.length === 0) {
    grid.innerHTML = '<div class="ov-empty"><div class="ov-empty-icon">&#128274;</div><p>暂无活跃会话</p></div>';
    return;
  }

  grid.innerHTML = limited.map(function(s) {
    var statusClass = s.ended_at ? 'done' : 'running';
    var statusText = s.ended_at ? '已完成' : '运行中';
    if (s.end_reason === 'error') { statusClass = 'error'; statusText = '错误'; }

    var tokens = (s.input_tokens || 0) + (s.output_tokens || 0);
    var duration = s.ended_at ? (s.ended_at - s.started_at) : (Date.now() / 1000 - s.started_at);

    var tools = (s.tool_names || []).slice(0, 6);
    var toolsHtml = tools.map(function(t) {
      return '<span class="ov-tool-badge">' + t + '</span>';
    }).join('');

    var toolsUsed = s.tool_call_count || 0;

    return '<a class="ov-session-card" href="' + withBase('/runtime/dashboard') + '?session=' + encodeURIComponent(s.id) + '">' +
      '<div class="ov-session-card-header">' +
        '<h3 class="ov-session-title" title="' + (s.title || s.id) + '">' + (s.title || s.id) + '</h3>' +
        '<span class="ov-session-status ' + statusClass + '">' +
          '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:currentColor"></span>' +
          statusText +
        '</span>' +
      '</div>' +
      '<div class="ov-session-meta">' +
        '<div class="ov-session-meta-item">' +
          '<span class="ov-session-meta-label">来源</span>' +
          '<span class="ov-session-meta-value">' + (s.source || '—') + '</span>' +
        '</div>' +
        '<div class="ov-session-meta-item">' +
          '<span class="ov-session-meta-label">模型</span>' +
          '<span class="ov-session-meta-value">' + (s.model || '—') + '</span>' +
        '</div>' +
        '<div class="ov-session-meta-item">' +
          '<span class="ov-session-meta-label">Token</span>' +
          '<span class="ov-session-meta-value">' + fmt(tokens) + '</span>' +
        '</div>' +
        '<div class="ov-session-meta-item">' +
          '<span class="ov-session-meta-label">耗时</span>' +
          '<span class="ov-session-meta-value">' + fmtDuration(duration) + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="ov-session-tools">' +
        '<div class="ov-session-tools-label">工具调用 (' + toolsUsed + ')</div>' +
        '<div class="ov-session-tools-list">' + (toolsHtml || '<span style="color:var(--ov-text-muted);font-size:11px">无</span>') + '</div>' +
      '</div>' +
    '</a>';
  }).join('');
}

function renderToolUsage(tools) {
  var chart = document.getElementById('tools-bar-chart');
  var legend = document.getElementById('tools-legend');

  if (!tools || tools.length === 0) {
    chart.innerHTML = '<div class="ov-empty"><div class="ov-empty-icon">&#128295;</div><p>暂无工具使用数据</p></div>';
    legend.innerHTML = '';
    return;
  }

  var maxCount = Math.max.apply(null, tools.map(function(t) { return t.call_count || 0; }));
  var colors = ['blue', 'green', 'orange', 'purple', 'cyan', 'pink', 'red'];

  chart.innerHTML = tools.map(function(t, i) {
    var pct = maxCount > 0 ? ((t.call_count || 0) / maxCount * 100) : 0;
    var color = colors[i % colors.length];
    var duration = t.avg_duration ? fmtMs(t.avg_duration) : '--';
    return '<div class="ov-tool-bar">' +
      '<span class="ov-tool-name" title="' + t.tool_name + '">' + t.tool_name + '</span>' +
      '<div class="ov-tool-bar-track">' +
        '<div class="ov-tool-bar-fill ' + color + '" style="width:' + pct + '%">' + (t.call_count || 0) + '</div>' +
      '</div>' +
    '</div>';
  }).join('');

  var totalCalls = tools.reduce(function(sum, t) { return sum + (t.call_count || 0); }, 0);
  var totalErrors = tools.reduce(function(sum, t) { return sum + (t.errors || 0); }, 0);
  var totalTokens = tools.reduce(function(sum, t) { return sum + (t.total_tokens || 0); }, 0);

  legend.innerHTML =
    '<div class="ov-legend-item"><span>工具种类</span><span class="ov-legend-value">' + tools.length + '</span></div>' +
    '<div class="ov-legend-item"><span>总调用次数</span><span class="ov-legend-value">' + fmt(totalCalls) + '</span></div>' +
    '<div class="ov-legend-item"><span>总错误数</span><span class="ov-legend-value">' + totalErrors + '</span></div>' +
    '<div class="ov-legend-item"><span>总Token</span><span class="ov-legend-value">' + fmt(totalTokens) + '</span></div>';
}

function renderPerformance(data) {
  var ttft = data.avg_ttft || 0;
  var tps = data.avg_tps || 0;
  var duration = data.avg_duration || 0;
  var errorRate = data.error_rate || 0;

  document.getElementById('perf-ttft').textContent = fmtMs(ttft);
  document.getElementById('perf-ttft-bar').style.width = Math.min(ttft / 50, 100) + '%';
  document.getElementById('perf-ttft-bar').className = 'ov-perf-bar-fill' + (ttft > 30 ? ' warn' : '') + (ttft > 50 ? ' error' : '');

  document.getElementById('perf-tps').textContent = tps.toFixed(1) + ' tok/s';
  document.getElementById('perf-tps-bar').style.width = Math.min(tps / 50 * 100, 100) + '%';

  document.getElementById('perf-duration').textContent = fmtDuration(duration);
  document.getElementById('perf-duration-bar').style.width = Math.min(duration / 3600 * 100, 100) + '%';

  document.getElementById('perf-error-rate').textContent = (errorRate * 100).toFixed(1) + '%';
  document.getElementById('perf-error-rate-bar').style.width = Math.min(errorRate * 100, 100) + '%';
  document.getElementById('perf-error-rate-bar').className = 'ov-perf-bar-fill' + (errorRate > 0.05 ? ' warn' : '') + (errorRate > 0.1 ? ' error' : '');
}

function renderErrors(errors) {
  var list = document.getElementById('recent-errors-list');
  var limited = (errors || []).slice(0, OVERVIEW_CONFIG.maxErrors);

  if (limited.length === 0) {
    list.innerHTML = '<div class="ov-empty"><div class="ov-empty-icon">&#9989;</div><p>暂无错误记录</p></div>';
    return;
  }

  list.innerHTML = limited.map(function(e) {
    return '<div class="ov-error-item">' +
      '<div class="ov-error-icon">&#9888;</div>' +
      '<div class="ov-error-content">' +
        '<p class="ov-error-title">' + (e.error_message || '未知错误') + '</p>' +
        '<p class="ov-error-detail" title="' + (e.session_id || '') + '">' + (e.session_id || '') + ' — ' + (e.tool_name || '') + '</p>' +
      '</div>' +
      '<span class="ov-error-time">' + relativeTime(e.timestamp) + '</span>' +
    '</div>';
  }).join('');
}

function renderSources(sources) {
  var container = document.getElementById('sources-container');
  var icons = { cli: '&#128187;', cron: '&#9200;', feishu: '&#128197;', telegram: '&#9992;', api_server: '&#127760;', api: '&#127760;', discord: '&#128172;', slack: '&#128276;' };

  if (!sources || sources.length === 0) {
    container.innerHTML = '<div class="ov-empty"><p>暂无来源数据</p></div>';
    return;
  }

  container.innerHTML = sources.map(function(s) {
    var src = (s.src || s.source || 'unknown').toLowerCase();
    var icon = icons[src] || '&#128279;';
    return '<div class="ov-source-card">' +
      '<div class="ov-source-icon">' + icon + '</div>' +
      '<div class="ov-source-name">' + s.src + '</div>' +
      '<div class="ov-source-count">' + s.cnt + ' 会话</div>' +
    '</div>';
  }).join('');
}

/* ---- Subagent List ---- */
function renderSubagents(agents) {
  var list = document.getElementById('subagent-list');
  if (!agents || agents.length === 0) {
    list.innerHTML = '<div class="ov-block-sub-item">Expert</div>' +
      '<div class="ov-block-sub-item">Research</div>' +
      '<div class="ov-block-sub-item">Code</div>' +
      '<div class="ov-block-sub-item">Ops</div>';
    return;
  }
  list.innerHTML = agents.map(function(a) {
    return '<div class="ov-block-sub-item">' + a.role + '</div>';
  }).join('');
}

/* ---- Tool Registry ---- */
function renderToolRegistry(tools) {
  var container = document.getElementById('tool-registry');
  if (!tools || tools.length === 0) {
    container.innerHTML =
      '<div class="ov-block-item">FileToolHandler</div>' +
      '<div class="ov-block-item">WebToolHandler</div>' +
      '<div class="ov-block-item">TerminalToolHandler</div>' +
      '<div class="ov-block-item">McpToolHandler</div>';
    return;
  }
  container.innerHTML = tools.slice(0, 6).map(function(t) {
    return '<div class="ov-block-item">' + t.tool_name + '</div>';
  }).join('');
}

/* ---- Data Fetching ---- */
function loadOverview() {
  fetchJSON('/api/overview').then(function(data) {
    renderMetrics(data.metrics);
    renderActiveSessions(data.active_sessions);
    renderToolUsage(data.tool_usage);
    renderPerformance(data.performance);
    renderErrors(data.recent_errors);
    renderSources(data.sources);
    renderSubagents(data.subagents);
    renderToolRegistry(data.tool_registry);
  }).catch(function(err) {
    console.error('Failed to load overview:', err);
  });
}

/* ---- Init ---- */
function init() {
  loadOverview();
  setInterval(loadOverview, OVERVIEW_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
