/**
 * CrazyAgentsManage — Runtime Aggregation Page JS
 * Consumes session/trace/lineage/metrics APIs
 */

var RUNTIME_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
  refreshInterval: 15000,
  maxActiveSessions: 8,
  maxErrors: 8,
};

function fmt(n) {
  if (n == null) return '--';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return n.toString();
}

function fmtDuration(sec) {
  if (!sec) return '--';
  if (sec >= 3600) {
    var h = Math.floor(sec / 3600);
    var m = Math.floor((sec % 3600) / 60);
    return h + 'h ' + m + 'm';
  }
  if (sec >= 60) {
    var m2 = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return m2 + 'm ' + s + 's';
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
  var diff = Date.now() / 1000 - ts;
  if (diff < 60) return Math.round(diff) + 's ago';
  if (diff < 3600) return Math.round(diff / 60) + 'm ago';
  if (diff < 86400) return Math.round(diff / 3600) + 'h ago';
  return Math.round(diff / 86400) + 'd ago';
}

function fetchJSON(url) {
  return fetch(RUNTIME_CONFIG.apiBase + url)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderStatusBar(metrics) {
  var dot = document.getElementById('rt-health-dot');
  var text = document.getElementById('rt-health-text');
  var errors = (metrics.error_count || 0);
  var active = (metrics.active_sessions || 0);

  if (errors > 0) {
    dot.className = 'rt-status-dot error';
    text.textContent = '运行态异常 (' + errors + ' 个错误)';
  } else if (active > 0) {
    dot.className = 'rt-status-dot healthy';
    text.textContent = '运行态正常 (' + active + ' 个活跃会话)';
  } else {
    dot.className = 'rt-status-dot idle';
    text.textContent = '运行态空闲';
  }

  var now = new Date();
  setText('rt-last-updated', '更新于 ' + now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0'));
}

function renderMetrics(metrics) {
  setText('rt-total-sessions', fmt(metrics.total_sessions || 0));
  setText('rt-active-count', metrics.active_sessions || 0);
  var totalTokens = (metrics.total_input || 0) + (metrics.total_output || 0);
  setText('rt-total-tokens', fmt(totalTokens));
  setText('rt-tool-calls', fmt(metrics.total_tool_calls || 0));
  setText('rt-error-count', fmt(metrics.error_count || 0));

  var indicator = document.getElementById('rt-active-indicator');
  if (indicator) {
    indicator.className = 'rt-metric-indicator ' + (metrics.active_sessions > 0 ? 'active' : 'inactive');
  }
}

function renderActiveSessions(sessions) {
  var grid = document.getElementById('rt-active-sessions-grid');
  var limited = (sessions || []).slice(0, RUNTIME_CONFIG.maxActiveSessions);

  if (limited.length === 0) {
    grid.innerHTML = '<div class="rt-empty"><div class="rt-empty-icon">🔒</div><p>暂无活跃会话</p></div>';
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
      return '<span class="rt-tool-badge">' + t + '</span>';
    }).join('');

    return '<a class="rt-session-card" href="' + RUNTIME_CONFIG.apiBase + '/runtime/sessions">' +
      '<div class="rt-session-card-header">' +
        '<h3 class="rt-session-title" title="' + (s.title || s.id) + '">' + (s.title || s.id) + '</h3>' +
        '<span class="rt-session-status ' + statusClass + '">' +
          '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:currentColor"></span>' +
          statusText +
        '</span>' +
      '</div>' +
      '<div class="rt-session-meta">' +
        '<div class="rt-session-meta-item">' +
          '<span class="rt-session-meta-label">来源</span>' +
          '<span class="rt-session-meta-value">' + (s.source || '—') + '</span>' +
        '</div>' +
        '<div class="rt-session-meta-item">' +
          '<span class="rt-session-meta-label">模型</span>' +
          '<span class="rt-session-meta-value">' + (s.model || '—') + '</span>' +
        '</div>' +
        '<div class="rt-session-meta-item">' +
          '<span class="rt-session-meta-label">Token</span>' +
          '<span class="rt-session-meta-value">' + fmt(tokens) + '</span>' +
        '</div>' +
        '<div class="rt-session-meta-item">' +
          '<span class="rt-session-meta-label">耗时</span>' +
          '<span class="rt-session-meta-value">' + fmtDuration(duration) + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="rt-session-tools">' +
        '<div class="rt-session-tools-label">工具调用 (' + (s.tool_call_count || 0) + ')</div>' +
        '<div class="rt-session-tools-list">' + (toolsHtml || '<span style="color:var(--rt-text-muted);font-size:11px">无</span>') + '</div>' +
      '</div>' +
    '</a>';
  }).join('');
}

function renderToolUsage(tools) {
  var chart = document.getElementById('rt-tools-chart');

  if (!tools || tools.length === 0) {
    chart.innerHTML = '<div class="rt-empty"><div class="rt-empty-icon">🔧</div><p>暂无工具使用数据</p></div>';
    return;
  }

  var maxCount = Math.max.apply(null, tools.map(function(t) { return t.call_count || 0; }));
  var colors = ['blue', 'green', 'orange', 'purple', 'cyan', 'pink', 'red'];

  chart.innerHTML = tools.map(function(t, i) {
    var pct = maxCount > 0 ? ((t.call_count || 0) / maxCount * 100) : 0;
    var color = colors[i % colors.length];
    return '<div class="rt-tool-bar">' +
      '<span class="rt-tool-name" title="' + t.tool_name + '">' + t.tool_name + '</span>' +
      '<div class="rt-tool-bar-track">' +
        '<div class="rt-tool-bar-fill ' + color + '" style="width:' + pct + '%">' + (t.call_count || 0) + '</div>' +
      '</div>' +
    '</div>';
  }).join('');
}

function renderPerformance(data) {
  var ttft = data.avg_ttft || 0;
  var tps = data.avg_tps || 0;
  var duration = data.avg_duration || 0;
  var errorRate = data.error_rate || 0;

  setText('rt-perf-ttft', fmtMs(ttft));
  var ttftBar = document.getElementById('rt-perf-ttft-bar');
  if (ttftBar) { ttftBar.style.width = Math.min(ttft / 50, 100) + '%'; ttftBar.className = 'rt-perf-bar-fill' + (ttft > 30 ? ' warn' : '') + (ttft > 50 ? ' error' : ''); }

  setText('rt-perf-tps', tps ? tps.toFixed(1) + ' tok/s' : '--');
  var tpsBar = document.getElementById('rt-perf-tps-bar');
  if (tpsBar) tpsBar.style.width = Math.min(tps / 50 * 100, 100) + '%';

  setText('rt-perf-duration', fmtDuration(duration));
  var durBar = document.getElementById('rt-perf-duration-bar');
  if (durBar) durBar.style.width = Math.min(duration / 3600 * 100, 100) + '%';

  setText('rt-perf-error-rate', (errorRate * 100).toFixed(1) + '%');
  var errBar = document.getElementById('rt-perf-error-rate-bar');
  if (errBar) { errBar.style.width = Math.min(errorRate * 100, 100) + '%'; errBar.className = 'rt-perf-bar-fill' + (errorRate > 0.05 ? ' warn' : '') + (errorRate > 0.1 ? ' error' : ''); }
}

function renderErrors(errors) {
  var list = document.getElementById('rt-errors-list');
  var limited = (errors || []).slice(0, RUNTIME_CONFIG.maxErrors);

  if (limited.length === 0) {
    list.innerHTML = '<div class="rt-empty"><div class="rt-empty-icon">✅</div><p>暂无错误记录</p></div>';
    return;
  }

  list.innerHTML = limited.map(function(e) {
    return '<div class="rt-error-item">' +
      '<div class="rt-error-icon">⚠️</div>' +
      '<div class="rt-error-content">' +
        '<p class="rt-error-title">' + (e.error_message || '未知错误') + '</p>' +
        '<p class="rt-error-detail" title="' + (e.session_id || '') + '">' + (e.session_id || '') + (e.tool_name ? ' — ' + e.tool_name : '') + '</p>' +
      '</div>' +
      '<span class="rt-error-time">' + relativeTime(e.timestamp) + '</span>' +
    '</div>';
  }).join('');
}

function renderAgents(agents) {
  var grid = document.getElementById('rt-agents-grid');

  if (!agents || agents.length === 0) {
    grid.innerHTML = '<div class="rt-empty"><div class="rt-empty-icon">🤖</div><p>暂无智能体数据</p></div>';
    return;
  }

  grid.innerHTML = agents.map(function(a) {
    var stateClass = 'unknown';
    var stateText = '未知';
    if (a.platform_state === 'connected') { stateClass = 'connected'; stateText = '已连接'; }
    else if (a.platform_state === 'disconnected' || a.platform_state === 'error') { stateClass = 'error'; stateText = '异常'; }
    else if (a.platform_state === 'stopped') { stateClass = 'disconnected'; stateText = '已停止'; }

    var gradient = a.gradient || '#64748b,#475569';

    return '<a class="rt-agent-card" href="' + RUNTIME_CONFIG.apiBase + '/runtime/agents">' +
      '<div class="rt-agent-header">' +
        '<div class="rt-agent-icon" style="background:linear-gradient(135deg,' + gradient + ')">' + a.icon + '</div>' +
        '<div>' +
          '<p class="rt-agent-name">' + a.name + '</p>' +
          '<p class="rt-agent-desc">' + a.source + '</p>' +
        '</div>' +
      '</div>' +
      '<div class="rt-agent-stats">' +
        '<div class="rt-agent-stat">' +
          '<div class="rt-agent-stat-value">' + a.session_count + '</div>' +
          '<div class="rt-agent-stat-label">会话</div>' +
        '</div>' +
        '<div class="rt-agent-stat">' +
          '<div class="rt-agent-stat-value">' + fmt(a.total_tokens) + '</div>' +
          '<div class="rt-agent-stat-label">Token</div>' +
        '</div>' +
        '<div class="rt-agent-stat">' +
          '<div class="rt-agent-stat-value">' + (a.success_rate || 0) + '%</div>' +
          '<div class="rt-agent-stat-label">成功率</div>' +
        '</div>' +
      '</div>' +
      '<span class="rt-agent-state ' + stateClass + '">' + stateText + '</span>' +
    '</a>';
  }).join('');
}

function loadRuntime() {
  fetchJSON('/api/overview').then(function(data) {
    renderStatusBar(data.metrics || {});
    renderMetrics(data.metrics || {});
    renderActiveSessions(data.active_sessions);
    renderToolUsage(data.tool_usage);
    renderPerformance(data.performance || {});
  }).catch(function(err) {
    console.error('Failed to load runtime summary:', err);
  });

  fetchJSON('/api/overview').then(function(data) {
    renderErrors(data.recent_errors);
  }).catch(function(err) {
    console.error('Failed to load overview errors:', err);
  });

  fetchJSON('/api/agents/list').then(function(agents) {
    renderAgents(agents);
  }).catch(function(err) {
    console.error('Failed to load agents:', err);
  });
}

function init() {
  loadRuntime();
  setInterval(loadRuntime, RUNTIME_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
