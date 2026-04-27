/**
 * CrazyAgentsManage — Overview Dashboard JS
 * Aggregation page consuming runtime + operations + governance + collaboration summaries
 */

var OVERVIEW_CONFIG = {
  apiBase: '',
  refreshInterval: 15000,
  maxErrors: 10,
  maxActiveSessions: 12,
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
  return fetch(OVERVIEW_CONFIG.apiBase + url)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

/* ---- Global Status Bar ---- */
function renderGlobalStatus(metrics) {
  var dot = document.getElementById('health-dot');
  var text = document.getElementById('health-text');
  var errors = (metrics.error_count || 0);
  var active = (metrics.active_sessions || 0);

  if (errors > 0) {
    dot.className = 'ov-status-dot error';
    text.textContent = '系统存在异常 (' + errors + ' 个错误)';
  } else if (active > 0) {
    dot.className = 'ov-status-dot healthy';
    text.textContent = '系统正常运行 (' + active + ' 个活跃会话)';
  } else {
    dot.className = 'ov-status-dot idle';
    text.textContent = '系统空闲';
  }

  var now = new Date();
  setText('last-updated', '更新于 ' + now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0'));
}

/* ---- Runtime Metrics ---- */
function renderMetrics(data) {
  setText('metric-total-sessions', fmt(data.total_sessions || 0));
  setText('metric-active-count', data.active_sessions || 0);
  setText('active-count-badge', data.active_sessions || 0);

  var totalTokens = (data.total_input || 0) + (data.total_output || 0);
  setText('metric-total-tokens', fmt(totalTokens));
  setText('metric-tool-calls', fmt(data.total_tool_calls || 0));
  setText('metric-error-count', fmt(data.error_count || 0));

  var indicator = document.getElementById('indicator-active');
  if (indicator) {
    indicator.className = 'ov-metric-indicator ' + (data.active_sessions > 0 ? 'active' : 'inactive');
  }
}

/* ---- Operations Summary ---- */
function renderOpsSummary() {
  fetchJSON('/api/overview/stats').then(function(stats) {
    setText('ops-skills-count', stats.skills || 0);
    setText('ops-memory-count', stats.memory_files || 0);
  }).catch(function() {});

  fetchJSON('/api/cron/list').then(function(jobs) {
    var count = Array.isArray(jobs) ? jobs.length : 0;
    setText('ops-cron-count', count);
  }).catch(function() {
    setText('ops-cron-count', '0');
  });

  fetchJSON('/api/alerts/list').then(function(alerts) {
    var critical = 0;
    if (Array.isArray(alerts)) {
      alerts.forEach(function(a) {
        if (a.level === 'critical' || a.level === 'warning') critical++;
      });
    }
    setText('ops-alerts-count', critical);
  }).catch(function() {
    setText('ops-alerts-count', '0');
  });
}

/* ---- Governance Summary ---- */
function renderGovSummary() {
  setText('gov-candidate-count', '--');
  setText('gov-truth-count', '--');
  setText('gov-review-count', '--');
  setText('gov-drift-count', '--');
}

/* ---- Collaboration Summary ---- */
function renderCollabSummary() {
  fetchJSON('/api/runtime/handoffs').then(function(handoffs) {
    setText('collab-handoff-count', Array.isArray(handoffs) ? handoffs.length : 0);
  }).catch(function() {
    setText('collab-handoff-count', '0');
  });

  fetchJSON('/api/runtime/harness-summary').then(function(summary) {
    var successCount = summary.success_count || 0;
    var failureCount = summary.failure_count || 0;
    setText('collab-trace-count', successCount + failureCount);
    setText('collab-closeout-count', failureCount > 0 ? failureCount : '0');
    setText('collab-writeback-count', '0');
  }).catch(function() {
    setText('collab-trace-count', '0');
    setText('collab-closeout-count', '0');
    setText('collab-writeback-count', '0');
  });
}

/* ---- Active Sessions ---- */
function renderActiveSessions(sessions) {
  var grid = document.getElementById('active-sessions-grid');
  var limited = (sessions || []).slice(0, OVERVIEW_CONFIG.maxActiveSessions);

  if (limited.length === 0) {
    grid.innerHTML = '<div class="ov-empty"><div class="ov-empty-icon">🔒</div><p>暂无活跃会话</p></div>';
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

    return '<a class="ov-session-card" href="' + OVERVIEW_CONFIG.apiBase + '/runtime/sessions">' +
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
        '<div class="ov-session-tools-list">' + (toolsHtml || '<span style="color:var(--color-text-muted);font-size:11px">无</span>') + '</div>' +
      '</div>' +
    '</a>';
  }).join('');
}

/* ---- Tool Usage ---- */
function renderToolUsage(tools) {
  var chart = document.getElementById('tools-bar-chart');
  var legend = document.getElementById('tools-legend');

  if (!tools || tools.length === 0) {
    chart.innerHTML = '<div class="ov-empty"><div class="ov-empty-icon">🔧</div><p>暂无工具使用数据</p></div>';
    legend.innerHTML = '';
    return;
  }

  var maxCount = Math.max.apply(null, tools.map(function(t) { return t.call_count || 0; }));
  var colors = ['blue', 'green', 'orange', 'purple', 'cyan', 'pink', 'red'];

  chart.innerHTML = tools.map(function(t, i) {
    var pct = maxCount > 0 ? ((t.call_count || 0) / maxCount * 100) : 0;
    var color = colors[i % colors.length];
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

/* ---- Performance ---- */
function renderPerformance(data) {
  var ttft = data.avg_ttft || 0;
  var tps = data.avg_tps || 0;
  var duration = data.avg_duration || 0;
  var errorRate = data.error_rate || 0;

  setText('perf-ttft', fmtMs(ttft));
  var ttftBar = document.getElementById('perf-ttft-bar');
  if (ttftBar) { ttftBar.style.width = Math.min(ttft / 50, 100) + '%'; ttftBar.className = 'ov-perf-bar-fill' + (ttft > 30 ? ' warn' : '') + (ttft > 50 ? ' error' : ''); }

  setText('perf-tps', tps ? tps.toFixed(1) + ' tok/s' : '--');
  var tpsBar = document.getElementById('perf-tps-bar');
  if (tpsBar) tpsBar.style.width = Math.min(tps / 50 * 100, 100) + '%';

  setText('perf-duration', fmtDuration(duration));
  var durBar = document.getElementById('perf-duration-bar');
  if (durBar) durBar.style.width = Math.min(duration / 3600 * 100, 100) + '%';

  setText('perf-error-rate', (errorRate * 100).toFixed(1) + '%');
  var errBar = document.getElementById('perf-error-rate-bar');
  if (errBar) { errBar.style.width = Math.min(errorRate * 100, 100) + '%'; errBar.className = 'ov-perf-bar-fill' + (errorRate > 0.05 ? ' warn' : '') + (errorRate > 0.1 ? ' error' : ''); }
}

/* ---- Errors ---- */
function renderErrors(errors) {
  var list = document.getElementById('recent-errors-list');
  var limited = (errors || []).slice(0, OVERVIEW_CONFIG.maxErrors);

  if (limited.length === 0) {
    list.innerHTML = '<div class="ov-empty"><div class="ov-empty-icon">✅</div><p>暂无错误记录</p></div>';
    return;
  }

  list.innerHTML = limited.map(function(e) {
    return '<div class="ov-error-item">' +
      '<div class="ov-error-icon">⚠️</div>' +
      '<div class="ov-error-content">' +
        '<p class="ov-error-title">' + (e.error_message || '未知错误') + '</p>' +
        '<p class="ov-error-detail" title="' + (e.session_id || '') + '">' + (e.session_id || '') + (e.tool_name ? ' — ' + e.tool_name : '') + '</p>' +
      '</div>' +
      '<span class="ov-error-time">' + relativeTime(e.timestamp) + '</span>' +
    '</div>';
  }).join('');
}

/* ---- Sources ---- */
function renderSources(sources) {
  var container = document.getElementById('sources-container');
  var icons = { cli: '🖥️', cron: '⏰', feishu: '📅', telegram: '✈️', api_server: '🌐', api: '🌐', discord: '💬', slack: '🔔' };

  if (!sources || sources.length === 0) {
    container.innerHTML = '<div class="ov-empty"><p>暂无来源数据</p></div>';
    return;
  }

  container.innerHTML = sources.map(function(s) {
    var src = (s.src || s.source || 'unknown').toLowerCase();
    var icon = icons[src] || '🔗';
    return '<div class="ov-source-card">' +
      '<div class="ov-source-icon">' + icon + '</div>' +
      '<div class="ov-source-name">' + s.src + '</div>' +
      '<div class="ov-source-count">' + s.cnt + ' 会话</div>' +
    '</div>';
  }).join('');
}

/* ---- Main Load ---- */
function loadOverview() {
  fetchJSON('/api/overview').then(function(data) {
    renderGlobalStatus(data.metrics || {});
    renderMetrics(data.metrics || {});
    renderActiveSessions(data.active_sessions);
    renderToolUsage(data.tool_usage);
    renderPerformance(data.performance || {});
    renderErrors(data.recent_errors);
    renderSources(data.sources);
  }).catch(function(err) {
    console.error('Failed to load overview:', err);
  });

  renderOpsSummary();
  renderGovSummary();
  renderCollabSummary();
}

function init() {
  loadOverview();
  setInterval(loadOverview, OVERVIEW_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}