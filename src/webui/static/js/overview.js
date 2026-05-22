/**
 * CrazyAgentsManage — Overview Workbench JS
 * Stage 2: object-driven overview centered on active monitored sessions
 */

var OVERVIEW_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
  refreshInterval: 15000,
  maxErrors: 6,
  maxActiveSessions: 8,
  maxToolTracks: 5,
  maxSourceRows: 5,
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
  if (diff < 60) return Math.max(1, Math.round(diff)) + 's ago';
  if (diff < 3600) return Math.round(diff / 60) + 'm ago';
  if (diff < 86400) return Math.round(diff / 3600) + 'h ago';
  return Math.round(diff / 86400) + 'd ago';
}

function fetchJSON(url) {
  return fetch(OVERVIEW_CONFIG.apiBase + url).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
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

function statusLabel(status) {
  var map = {
    healthy: '健康',
    degraded: '降级',
    failed: '异常',
    unknown: '未知'
  };
  return map[status] || status || '未知';
}

function getSessionStatus(session) {
  if (!session) return { key: 'idle', label: '空闲' };
  if (session.end_reason === 'error') return { key: 'error', label: '异常' };
  if (session.ended_at) return { key: 'done', label: '已完成' };
  return { key: 'running', label: '运行中' };
}

function sessionDuration(session) {
  if (!session || !session.started_at) return 0;
  var endAt = session.ended_at || Date.now() / 1000;
  return Math.max(0, endAt - session.started_at);
}

function sessionTokenTotal(session) {
  return (session && ((session.input_tokens || 0) + (session.output_tokens || 0))) || 0;
}

function pickFocusSession(data) {
  var sessions = (data && data.active_sessions) || [];
  if (!sessions.length) return null;

  var errorSession = sessions.find(function(s) { return s.end_reason === 'error'; });
  if (errorSession) return errorSession;

  var runningSession = sessions.find(function(s) { return !s.ended_at; });
  return runningSession || sessions[0];
}

function renderOverviewBriefing(opsSummary, hostHealth) {
  var briefing = (opsSummary && opsSummary.briefing) || {};
  setText('ov-briefing-label', briefing.label || 'Overview aggregation');
  setText('ov-briefing-title', briefing.title || '跨域摘要不可用');

  var hostStatus = hostHealth && hostHealth.status ? statusLabel(hostHealth.status) : '未知';
  var opsStatus = opsSummary && opsSummary.status ? statusLabel(opsSummary.status) : '未知';
  var hostDisk = hostHealth && hostHealth.disk && hostHealth.disk.used_percent != null
    ? hostHealth.disk.used_percent + '%'
    : '--';
  var hostMemory = hostHealth && hostHealth.memory && hostHealth.memory.used_percent != null
    ? hostHealth.memory.used_percent + '%'
    : '--';

  var copy = briefing.summary || '当前未拿到跨域聚合摘要。';
  copy += ' 当前运营面状态 ' + opsStatus + '；主机磁盘 ' + hostDisk + '，内存 ' + hostMemory + '，主机状态 ' + hostStatus + '。';
  setText('ov-briefing-copy', copy);

  var nextHop = (opsSummary && opsSummary.nextHop) || {};
  var nextHopEl = document.getElementById('ov-next-hop');
  if (nextHopEl) {
    nextHopEl.href = OVERVIEW_CONFIG.apiBase + (nextHop.href || '/operations');
  }
  setText('ov-next-hop-label', nextHop.label || '进入 Operations');
  setText('ov-next-hop-reason', nextHop.reason || '继续查看跨域对象与运行支持信号。');
}

function renderOverviewSummary(opsSummary, hostHealth) {
  var el = document.getElementById('ov-summary-grid');
  if (!el) return;

  var families = (opsSummary && opsSummary.families) || [];
  var hostCard = {
    key: 'host',
    title: 'Host Health',
    icon: '🖥️',
    status: (hostHealth && hostHealth.status) || 'unknown',
    count: hostHealth && hostHealth.disk && hostHealth.disk.used_percent != null ? hostHealth.disk.used_percent + '%' : '--',
    summary: 'disk / memory 输入已进入 Overview 支持信号层'
  };
  var cards = families.concat([hostCard]);

  if (!cards.length) {
    el.innerHTML = '<div class="ov-summary-card">' +
      '<div class="ov-summary-icon">⚠️</div>' +
      '<div><div class="ov-summary-title">摘要不可用</div><div class="ov-summary-copy">当前未能加载 Operations summary payload。</div></div>' +
    '</div>';
    return;
  }

  el.innerHTML = cards.map(function(card) {
    var href = card.key === 'host' ? (OVERVIEW_CONFIG.apiBase + '/operations/alerts') : (OVERVIEW_CONFIG.apiBase + (card.href || '/operations'));
    var value = card.count != null ? card.count : '--';
    if (typeof value === 'number') value = fmt(value);
    return '<a class="ov-summary-card" href="' + href + '">' +
      '<div class="ov-summary-icon">' + escapeHtml(card.icon || '•') + '</div>' +
      '<div style="min-width:0;">' +
        '<div class="ov-summary-header">' +
          '<div class="ov-summary-title">' + escapeHtml(card.title || card.key || 'Summary') + '</div>' +
          '<span class="ov-status-chip ' + escapeHtml(card.status || 'unknown') + '">' + escapeHtml(statusLabel(card.status || 'unknown')) + '</span>' +
        '</div>' +
        '<div class="ov-summary-value">' + escapeHtml(value) + '</div>' +
        '<div class="ov-summary-copy">' + escapeHtml(card.summary || '—') + '</div>' +
      '</div>' +
    '</a>';
  }).join('');
}

function renderGlobalStatus(metrics, focusSession) {
  var dot = document.getElementById('health-dot');
  var text = document.getElementById('health-text');
  var errors = (metrics.error_count || 0);
  var active = (metrics.active_sessions || 0);

  if (errors > 0) {
    dot.className = 'ov-status-dot error';
    text.textContent = '存在异常对象需要关注';
  } else if (focusSession) {
    dot.className = 'ov-status-dot healthy';
    text.textContent = '对象工作台已绑定当前监控上下文';
  } else if (active > 0) {
    dot.className = 'ov-status-dot healthy';
    text.textContent = '系统正常运行';
  } else {
    dot.className = 'ov-status-dot idle';
    text.textContent = '当前没有活跃对象';
  }

  var now = new Date();
  setText('last-updated', '更新于 ' + now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0'));
}

function renderObjectCluster(metrics, sessions) {
  var el = document.getElementById('object-cluster-summary');
  if (!el) return;

  var activeSessions = metrics.active_sessions || 0;
  var errorCount = metrics.error_count || 0;
  var totalToolCalls = metrics.total_tool_calls || 0;
  var totalTokens = (metrics.total_input || 0) + (metrics.total_output || 0);

  el.innerHTML = [
    { label: '活跃对象', value: activeSessions },
    { label: '异常对象', value: errorCount },
    { label: '工具调用', value: fmt(totalToolCalls) },
    { label: '总 Token', value: fmt(totalTokens) }
  ].map(function(item) {
    return '<div class="ov-cluster-card">' +
      '<span class="ov-cluster-label">' + escapeHtml(item.label) + '</span>' +
      '<div class="ov-cluster-value">' + escapeHtml(item.value) + '</div>' +
    '</div>';
  }).join('');
}

function renderObjectTree(sessions, focusSession) {
  var tree = document.getElementById('object-session-list');
  if (!tree) return;

  var limited = (sessions || []).slice(0, OVERVIEW_CONFIG.maxActiveSessions);
  if (!limited.length) {
    tree.innerHTML = '<div class="ov-empty">暂无活跃对象，Overview 将在有监控对象时绑定工作上下文。</div>';
    return;
  }

  tree.innerHTML = limited.map(function(session) {
    var status = getSessionStatus(session);
    var isSelected = focusSession && focusSession.id === session.id;
    var tools = (session.tool_names || []).slice(0, 3).map(function(tool) {
      return '<span class="ov-tool-pill">' + escapeHtml(tool) + '</span>';
    }).join('');

    return '<article class="ov-session-node' + (isSelected ? ' is-selected' : '') + '">' +
      '<div class="ov-session-node-head">' +
        '<div>' +
          '<h3 class="ov-tree-title">' + escapeHtml(session.title || session.id || '未命名对象') + '</h3>' +
          '<span class="ov-tree-meta">' + escapeHtml(session.id || '--') + '</span>' +
        '</div>' +
        '<span class="ov-tree-status ' + status.key + '">' + status.label + '</span>' +
      '</div>' +
      '<div class="ov-tree-meta-row">' +
        '<span class="ov-tree-pill">来源 ' + escapeHtml(session.source || '—') + '</span>' +
        '<span class="ov-tree-pill">模型 ' + escapeHtml(session.model || '—') + '</span>' +
        '<span class="ov-tree-pill">耗时 ' + escapeHtml(fmtDuration(sessionDuration(session))) + '</span>' +
      '</div>' +
      '<div class="ov-tree-tool-row" style="margin-top:8px;">' +
        (tools || '<span class="ov-tree-meta">当前无工具轨迹</span>') +
      '</div>' +
    '</article>';
  }).join('');
}

function renderWorkspaceHeader(focusSession) {
  if (!focusSession) {
    setText('workspace-object-title', '当前没有活跃监控对象');
    setText('workspace-object-subtitle', 'Overview 已准备为对象工作台，但当前无可绑定的对象上下文。');
    setText('workspace-status-pill', '空闲');
    return;
  }

  var status = getSessionStatus(focusSession);
  setText('workspace-object-title', focusSession.title || focusSession.id || '未命名对象');
  setText('workspace-object-subtitle', '围绕当前监控对象展开：来源、模型、工具轨迹、性能与异常全部收束到同一工作上下文。');

  var pill = document.getElementById('workspace-status-pill');
  if (pill) {
    pill.className = 'ov-workspace-status ' + status.key;
    pill.textContent = status.label;
  }
}

function renderWorkspaceMetrics(metrics, focusSession) {
  var el = document.getElementById('workspace-metrics');
  if (!el) return;

  if (!focusSession) {
    el.innerHTML = '<div class="ov-empty">暂无对象指标</div>';
    return;
  }

  var sessionTokens = sessionTokenTotal(focusSession);
  var sessionTools = focusSession.tool_call_count || 0;
  var activeShare = metrics.total_sessions ? (((metrics.active_sessions || 0) / metrics.total_sessions) * 100).toFixed(1) + '%' : '--';
  var sessionAge = relativeTime(focusSession.started_at);

  var cards = [
    { label: '对象 Token', value: fmt(sessionTokens) },
    { label: '对象工具调用', value: fmt(sessionTools) },
    { label: '活跃占比', value: activeShare },
    { label: '对象起始', value: sessionAge }
  ];

  el.innerHTML = cards.map(function(card) {
    return '<div class="ov-metric-tile">' +
      '<span class="ov-metric-caption">' + escapeHtml(card.label) + '</span>' +
      '<div class="ov-metric-value">' + escapeHtml(card.value) + '</div>' +
    '</div>';
  }).join('');
}

function renderFocusCard(metrics, focusSession, data) {
  var el = document.getElementById('workspace-focus-card');
  if (!el) return;

  if (!focusSession) {
    el.innerHTML = '<div class="ov-empty">对象上下文未激活。</div>';
    return;
  }

  var status = getSessionStatus(focusSession);
  var toolNames = (focusSession.tool_names || []).slice(0, 6);
  var score = focusSession.end_reason === 'error'
    ? '需介入'
    : status.key === 'running'
      ? '进行中'
      : '已归档';

  var sourceTop = ((data.sources || [])[0] || {}).src || 'unknown';
  var avgDuration = fmtDuration((data.performance || {}).avg_duration || 0);

  el.innerHTML = '<div class="ov-focus-hero">' +
    '<div>' +
      '<h3 class="ov-focus-headline">' + escapeHtml(focusSession.title || focusSession.id || '未命名对象') + '</h3>' +
      '<p class="ov-focus-note">当前对象是 Overview 中央主语，不再与跨域摘要平权竞争。</p>' +
    '</div>' +
    '<div class="ov-focus-score">' +
      '<span class="ov-tree-meta">对象态势</span>' +
      '<strong>' + escapeHtml(score) + '</strong>' +
    '</div>' +
  '</div>' +
  '<div class="ov-focus-lanes">' +
    '<div class="ov-focus-lane"><strong>对象来源</strong><p class="ov-focus-context">' + escapeHtml(focusSession.source || '—') + ' / ' + escapeHtml(focusSession.model || '—') + '</p></div>' +
    '<div class="ov-focus-lane"><strong>对象耗时</strong><p class="ov-focus-context">' + escapeHtml(fmtDuration(sessionDuration(focusSession))) + '，系统均值 ' + escapeHtml(avgDuration) + '</p></div>' +
    '<div class="ov-focus-lane"><strong>主要工具</strong><p class="ov-focus-context">' + escapeHtml(toolNames.join(' · ') || '暂无工具轨迹') + '</p></div>' +
    '<div class="ov-focus-lane"><strong>全局来源主峰</strong><p class="ov-focus-context">' + escapeHtml(sourceTop) + '，用于校准对象所处群组</p></div>' +
  '</div>' +
  '<div class="ov-tree-meta">对象 ID：' + escapeHtml(focusSession.id || '--') + '</div>';
}

function renderWorkspaceTools(toolUsage, focusSession) {
  var el = document.getElementById('workspace-tools');
  if (!el) return;

  if (!focusSession || !toolUsage || !toolUsage.length) {
    el.innerHTML = '<div class="ov-empty">暂无工具行为数据</div>';
    return;
  }

  var maxCount = Math.max.apply(null, toolUsage.map(function(item) { return item.call_count || 0; }));
  el.innerHTML = toolUsage.slice(0, OVERVIEW_CONFIG.maxToolTracks).map(function(item) {
    var pct = maxCount ? Math.max(6, Math.round(((item.call_count || 0) / maxCount) * 100)) : 0;
    return '<div class="ov-tool-track">' +
      '<div class="ov-tool-track-head">' +
        '<span class="ov-tool-name">' + escapeHtml(item.tool_name || 'unknown') + '</span>' +
        '<span class="ov-tool-count">' + escapeHtml(fmt(item.call_count || 0)) + ' 次</span>' +
      '</div>' +
      '<div class="ov-tool-bar"><div class="ov-tool-bar-fill" style="width:' + pct + '%"></div></div>' +
    '</div>';
  }).join('');
}

function renderWorkspacePerformance(performance, focusSession) {
  var el = document.getElementById('workspace-performance');
  if (!el) return;

  if (!focusSession) {
    el.innerHTML = '<div class="ov-empty">暂无性能上下文</div>';
    return;
  }

  var items = [
    { label: '平均 TTFT', value: fmtMs(performance.avg_ttft) },
    { label: '平均 TPS', value: performance.avg_tps ? performance.avg_tps.toFixed(1) + ' tok/s' : '--' },
    { label: '平均会话耗时', value: fmtDuration(performance.avg_duration) },
    { label: '错误率', value: ((performance.error_rate || 0) * 100).toFixed(1) + '%' }
  ];

  el.innerHTML = items.map(function(item) {
    return '<div class="ov-performance-item">' +
      '<div><span class="ov-performance-label">' + escapeHtml(item.label) + '</span></div>' +
      '<div class="ov-performance-value">' + escapeHtml(item.value) + '</div>' +
    '</div>';
  }).join('');
}

function renderErrors(errors) {
  var el = document.getElementById('workspace-errors');
  if (!el) return;

  var limited = (errors || []).slice(0, OVERVIEW_CONFIG.maxErrors);
  if (!limited.length) {
    el.innerHTML = '<div class="ov-empty">暂无错误记录</div>';
    return;
  }

  el.innerHTML = limited.map(function(error) {
    return '<div class="ov-error-item">' +
      '<div>' +
        '<p class="ov-error-title">' + escapeHtml(error.error_message || '未知错误') + '</p>' +
        '<p class="ov-error-meta">' + escapeHtml(error.session_id || '') + (error.tool_name ? ' · ' + escapeHtml(error.tool_name) : '') + '</p>' +
      '</div>' +
      '<span class="ov-error-time">' + escapeHtml(relativeTime(error.timestamp)) + '</span>' +
    '</div>';
  }).join('');
}

function renderSupportSignals(stats, collab, data, opsSummary, hostHealth) {
  var el = document.getElementById('support-signals-list');
  if (!el) return;

  var opsMetrics = (opsSummary && opsSummary.metrics) || {};
  var hostDisk = hostHealth && hostHealth.disk && hostHealth.disk.used_percent != null
    ? hostHealth.disk.used_percent + '%'
    : '--';
  var hostMemory = hostHealth && hostHealth.memory && hostHealth.memory.used_percent != null
    ? hostHealth.memory.used_percent + '%'
    : '--';

  var cards = [
    {
      label: '运营面',
      value: fmt(opsMetrics.skillsCount || 0),
      desc: '直接复用 Operations summary 的技能库存摘要'
    },
    {
      label: '治理面',
      value: fmt(data.metrics.error_count || 0),
      desc: '异常对象数，替代大块治理摘要'
    },
    {
      label: '协作面',
      value: fmt(collab.handoffs || 0),
      desc: 'Open handoff 数，提示对象交接压力'
    },
    {
      label: '定时任务',
      value: fmt(opsMetrics.cronCount || stats.cron || 0),
      desc: '直接复用 Operations summary 的 routines 规模'
    },
    {
      label: '主机健康',
      value: statusLabel((hostHealth && hostHealth.status) || 'unknown'),
      desc: 'disk ' + hostDisk + ' · memory ' + hostMemory
    }
  ];

  el.innerHTML = cards.map(function(card) {
    return '<div class="ov-support-card">' +
      '<div>' +
        '<span class="ov-support-label">' + escapeHtml(card.label) + '</span>' +
        '<div class="ov-support-value">' + escapeHtml(card.value) + '</div>' +
      '</div>' +
      '<div class="ov-support-desc">' + escapeHtml(card.desc) + '</div>' +
    '</div>';
  }).join('');
}

function renderFacts(focusSession, data, stats, collab, opsSummary, hostHealth) {
  var el = document.getElementById('detail-facts-list');
  if (!el) return;

  if (!focusSession) {
    el.innerHTML = '<div class="ov-empty">暂无对象事实</div>';
    return;
  }

  var facts = [
    { key: '对象 ID', value: focusSession.id || '--' },
    { key: '来源 / 模型', value: (focusSession.source || '—') + ' / ' + (focusSession.model || '—') },
    { key: '对象耗时', value: fmtDuration(sessionDuration(focusSession)) },
    { key: '对象工具调用', value: fmt(focusSession.tool_call_count || 0) },
    { key: '总会话规模', value: fmt((data.metrics || {}).total_sessions || 0) },
    { key: 'Open Handoffs', value: fmt(collab.handoffs || 0) },
    { key: '记忆文件', value: fmt((opsSummary && opsSummary.metrics && opsSummary.metrics.memoryCount) || stats.memory_files || 0) },
    { key: '主机磁盘', value: hostHealth && hostHealth.disk && hostHealth.disk.used_percent != null ? hostHealth.disk.used_percent + '%' : '--' },
    { key: '主机内存', value: hostHealth && hostHealth.memory && hostHealth.memory.used_percent != null ? hostHealth.memory.used_percent + '%' : '--' }
  ];

  el.innerHTML = facts.map(function(fact) {
    return '<div class="ov-fact-row">' +
      '<span class="ov-fact-key">' + escapeHtml(fact.key) + '</span>' +
      '<span class="ov-fact-value">' + escapeHtml(fact.value) + '</span>' +
    '</div>';
  }).join('');
}

function renderSources(sources) {
  var el = document.getElementById('detail-source-list');
  if (!el) return;

  if (!sources || !sources.length) {
    el.innerHTML = '<div class="ov-empty">暂无来源分布</div>';
    return;
  }

  el.innerHTML = sources.slice(0, OVERVIEW_CONFIG.maxSourceRows).map(function(source) {
    return '<div class="ov-source-row">' +
      '<div>' +
        '<span class="ov-fact-key">' + escapeHtml(source.src || 'unknown') + '</span>' +
        '<span class="ov-source-meta">会话 ' + escapeHtml(fmt(source.cnt || 0)) + '</span>' +
      '</div>' +
      '<span class="ov-source-value">' + escapeHtml(fmt(source.total_tokens || 0)) + ' tok</span>' +
    '</div>';
  }).join('');
}

function loadSupportData() {
  return Promise.all([
    fetchJSON('/api/overview/stats').catch(function() { return {}; }),
    fetchJSON('/api/cron/list').catch(function() { return []; }),
    fetchJSON('/api/runtime/handoffs').catch(function() { return []; }),
    fetchJSON('/api/runtime/harness-summary').catch(function() { return {}; }),
    fetchJSON('/api/operations/summary').catch(function() { return {}; }),
    fetchJSON('/api/runtime/host-health').catch(function() { return {}; })
  ]).then(function(results) {
    return {
      stats: {
        skills: results[0].skills || 0,
        memory_files: results[0].memory_files || 0,
        cron: Array.isArray(results[1]) ? results[1].length : 0,
      },
      collab: {
        handoffs: Array.isArray(results[2]) ? results[2].length : 0,
        traces: (results[3].success_count || 0) + (results[3].failure_count || 0),
        failures: results[3].failure_count || 0,
      },
      operations: results[4] || {},
      hostHealth: results[5] || {}
    };
  });
}

function loadOverview() {
  Promise.all([
    fetchJSON('/api/overview'),
    loadSupportData()
  ]).then(function(results) {
    var data = results[0] || {};
    var support = results[1] || { stats: {}, collab: {} };
    var opsSummary = support.operations || {};
    var hostHealth = support.hostHealth || {};
    var metrics = data.metrics || {};
    var sessions = data.active_sessions || [];
    var focusSession = pickFocusSession(data);

    renderOverviewBriefing(opsSummary, hostHealth);
    renderOverviewSummary(opsSummary, hostHealth);
    renderGlobalStatus(metrics, focusSession);
    renderObjectCluster(metrics, sessions);
    renderObjectTree(sessions, focusSession);
    renderWorkspaceHeader(focusSession);
    renderWorkspaceMetrics(metrics, focusSession);
    renderFocusCard(metrics, focusSession, data);
    renderWorkspaceTools(data.tool_usage || [], focusSession);
    renderWorkspacePerformance(data.performance || {}, focusSession);
    renderErrors(data.recent_errors || []);
    renderSupportSignals(support.stats, support.collab, data, opsSummary, hostHealth);
    renderFacts(focusSession, data, support.stats, support.collab, opsSummary, hostHealth);
    renderSources(data.sources || []);
  }).catch(function(err) {
    console.error('Failed to load overview:', err);
  });
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
