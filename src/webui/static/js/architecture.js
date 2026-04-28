var ARCH_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
};

function archFetchJSON(url) {
  return fetch(ARCH_CONFIG.apiBase + url).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
}

function archFmt(n) {
  if (n == null) return '--';
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderSourcePills(sources) {
  var host = document.getElementById('arch-source-pills');
  if (!host) return;
  if (!Array.isArray(sources) || sources.length === 0) {
    host.innerHTML = '<span class="arch-empty">暂无来源分布</span>';
    return;
  }
  host.innerHTML = sources.slice(0, 8).map(function(item) {
    var label = item.src || item.source || 'unknown';
    var count = item.cnt || 0;
    return '<span class="arch-pill">' + label + ' · ' + count + '</span>';
  }).join('');
}

function renderList(id, items, formatter, emptyText) {
  var host = document.getElementById(id);
  if (!host) return;
  if (!Array.isArray(items) || items.length === 0) {
    host.innerHTML = '<div class="arch-empty">' + emptyText + '</div>';
    return;
  }
  host.innerHTML = items.map(formatter).join('');
}

function renderSharedMetrics(data) {
  if (!data) return;
  setText('arch-metric-sessions', archFmt(data.sessions));
  setText('arch-metric-active', archFmt(data.active_sessions));
  setText('arch-metric-skills', archFmt(data.skills));
  setText('arch-metric-memory', archFmt(data.memory_files));
  setText('arch-hero-live', archFmt(data.active_sessions));
  setText('arch-hero-meta', '累计会话 ' + archFmt(data.sessions) + ' · 技能 ' + archFmt(data.skills));
}

function renderRuntimeSummary(data) {
  if (!data) return;
  var metrics = data.metrics || {};
  setText('arch-runtime-tool-calls', archFmt(metrics.total_tool_calls || 0));
  setText('arch-runtime-errors', archFmt(metrics.error_count || 0));
  setText('arch-runtime-tokens', archFmt((metrics.total_input || 0) + (metrics.total_output || 0)));
  setText('arch-runtime-gateway', data.gateway && data.gateway.running ? '在线' : '待确认');
  renderSourcePills(data.sources || []);

  renderList(
    'arch-active-session-list',
    data.active_sessions || [],
    function(item) {
      return '<div class="arch-kv-row"><span class="arch-kv-key">' + (item.source || 'unknown') + '</span><span class="arch-kv-value">' + (item.title || item.id || '--') + '</span></div>';
    },
    '暂无活跃会话'
  );

  renderList(
    'arch-tool-usage-list',
    data.tool_usage || [],
    function(item) {
      return '<div class="arch-kv-row"><span class="arch-kv-key">' + item.tool_name + '</span><span class="arch-kv-value">' + archFmt(item.call_count || 0) + '</span></div>';
    },
    '暂无工具使用记录'
  );
}

function renderHarnessSummary(data) {
  if (!data) return;
  setText('arch-handoff-count', archFmt(data.success_count || 0));
  setText('arch-closeout-count', archFmt(data.failure_count || 0));
}

function loadArchitecture() {
  archFetchJSON('/api/overview/stats').then(renderSharedMetrics).catch(function() {});
  archFetchJSON('/api/runtime/summary').then(renderRuntimeSummary).catch(function() {});
  archFetchJSON('/api/runtime/harness-summary').then(renderHarnessSummary).catch(function() {});
  archFetchJSON('/api/runtime/handoffs').then(function(items) {
    renderList(
      'arch-handoff-list',
      items || [],
      function(item) {
        return '<div class="arch-timeline-item"><strong>' + item.name + '</strong><br>' + (item.preview || '').slice(0, 100) + '</div>';
      },
      '暂无 Hermes 交接包'
    );
  }).catch(function() {});
  archFetchJSON('/api/skills/list').then(function(data) {
    var skills = (data && data.skills) || [];
    renderList(
      'arch-skill-list',
      skills.slice(0, 6),
      function(item) {
        return '<div class="arch-kv-row"><span class="arch-kv-key">' + (item.category_display || item.category || 'skill') + '</span><span class="arch-kv-value">' + (item.name || '--') + '</span></div>';
      },
      '暂无技能清单'
    );
  }).catch(function() {});
  archFetchJSON('/api/cron/list').then(function(items) {
    renderList(
      'arch-cron-list',
      items.slice(0, 5),
      function(item) {
        return '<div class="arch-kv-row"><span class="arch-kv-key">' + (item.name || item.id || '--') + '</span><span class="arch-kv-value">' + (item.schedule || item.cron || '--') + '</span></div>';
      },
      '暂无定时任务'
    );
  }).catch(function() {});
  archFetchJSON('/api/agents/list').then(function(items) {
    renderList(
      'arch-agent-list',
      items.slice(0, 6),
      function(item) {
        return '<div class="arch-kv-row"><span class="arch-kv-key">' + (item.source || 'agent') + '</span><span class="arch-kv-value">' + (item.name || item.title || item.id || '--') + '</span></div>';
      },
      '暂无智能体清单'
    );
  }).catch(function() {});
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadArchitecture);
} else {
  loadArchitecture();
}
