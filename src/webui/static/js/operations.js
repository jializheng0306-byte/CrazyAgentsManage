/**
 * CrazyAgentsManage — Operations Workbench JS
 * Three-column layout: left object tree + center workspace + right detail rail
 * Supports both built-in ops objects and executor integrations
 */

var OPS = {
  apiBase: (function() {
    var p = window.location.pathname || '';
    return (p === '/manage' || p.indexOf('/manage/') === 0) ? '/manage' : '';
  })(),
  currentFamily: 'task-registry',
  selectedItemId: null,
  cache: {},
  summary: null,
  filterText: '',
  filterChip: '',
  providerMode: 'sample',
  capabilities: {
    sourceCreate: true,
    sourceCreateTypes: ['openapi', 'graphql', 'mcp', 'discovery'],
    sourceRefresh: true,
    sourceStatusToggle: true,
    sourceDelete: true,
    credentialBind: true,
    credentialUnbind: true,
    modeLabel: 'sample'
  }
};

function _queryParams() {
  return new URLSearchParams(window.location.search || '');
}

function _url(path) {
  return OPS.apiBase + path;
}

function _fetch(path, options) {
  return fetch(_url(path), options || {}).then(function(r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
}

function _el(id) {
  return document.getElementById(id);
}

function _setText(id, text) {
  var el = _el(id);
  if (el) el.textContent = text;
}

function _familyFromHash() {
  var hash = (window.location.hash || '').replace(/^#/, '');
  return FAMILIES[hash] ? hash : '';
}

function _familyFromQuery() {
  var family = String(_queryParams().get('family') || '').trim();
  return FAMILIES[family] ? family : '';
}

function _actionContext() {
  var params = _queryParams();
  var action = String(params.get('action') || '').trim();
  var focus = String(params.get('focus') || '').trim();
  if (!action && !focus) return null;
  return { action: action, focus: focus };
}

function _showContextBanner(message, isError) {
  var banner = _el('ops-context-banner');
  if (!banner) return;
  if (!message) {
    banner.style.display = 'none';
    banner.textContent = '';
    return;
  }
  banner.style.display = 'block';
  banner.style.borderLeft = isError ? '4px solid #ef4444' : '4px solid #22c55e';
  banner.style.color = isError ? '#fecaca' : '#bbf7d0';
  banner.textContent = message;
}

function _contextMessage(context) {
  if (!context) return '';
  if (context.action === 'prd-closeout') {
    return '来自 Collaboration 的 PRD closeout playbook：当前已切到 Harness family，请先核对 canonical closeout commands 和文档回写路径。';
  }
  return '来自 Collaboration 的协作动作跳转：请优先处理当前 operations context。';
}

function _focusOpsContext(context) {
  if (!context || context.focus !== 'commands') return;
  var rail = _el('ops-rail');
  if (rail && typeof rail.scrollIntoView === 'function') {
    rail.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ============================================================
// Family definitions
// ============================================================

var FAMILIES = {
  'task-registry': { icon: '📋', label: 'Task Registry', api: '/api/operations/task-registry', filterBy: null },
  automation:  { icon: '🤖', label: 'Automation Maturity', api: '/api/operations/automation-maturity', filterBy: null },
  'host-health': { icon: '🖥️', label: 'Host Health', api: '/api/operations/host-health', filterBy: null },
  harness:     { icon: '🧪', label: 'Harness', api: '/api/operations/harness', filterBy: null },
  'env-map':   { icon: '🗺️', label: 'Env Map', api: '/api/operations/env-map', filterBy: null },
  'backup-recovery': { icon: '🛟', label: 'Backup / Recovery', api: '/api/operations/backup-recovery', filterBy: null },
  'recovery-paths': { icon: '🧭', label: 'Recovery Paths', api: '/api/operations/recovery-paths', filterBy: null },
  runbooks:    { icon: '📚', label: 'Runbooks', api: '/api/operations/runbooks', filterBy: null },
  cron:        { icon: '⏰', label: 'Cron Jobs',        api: '/api/cron/list',                    filterBy: 'status' },
  alerts:      { icon: '🔔', label: 'Alerts',           api: '/api/alerts/list',                  filterBy: 'level' },
  skills:      { icon: '⚡', label: 'Skills',           api: '/api/skills/list',                  filterBy: 'category' },
  memory:      { icon: '📝', label: 'Team Memory',      api: '/api/overview/memories',            filterBy: null },
  isolation:   { icon: '🧱', label: 'Role / Memory Isolation', api: '/api/operations/isolation',   filterBy: null },
  sources:     { icon: '🔌', label: 'Sources',          api: '/api/operations/integrations/sources',     filterBy: 'type' },
  tools:       { icon: '🧰', label: 'Tool Catalog',     api: '/api/operations/integrations/tools',       filterBy: 'status' },
  credentials: { icon: '🔑', label: 'Credential Health',api: '/api/operations/integrations/credentials', filterBy: 'status' },
  providers:   { icon: '📡', label: 'Provider Health',  api: '/api/operations/integrations/providers',   filterBy: 'status' },
  boundary:    { icon: '🧭', label: 'Readonly Boundary',api: '/api/operations/integrations/boundary',    filterBy: null },
};

// ============================================================
// Metrics & tree counts
// ============================================================

function loadMetrics() {
  _fetch('/api/operations/support-projection').then(function(summary) {
    OPS.summary = summary || null;
    OPS.providerMode = summary.providerMode || 'sample';
    OPS.capabilities = summary.capabilities || OPS.capabilities;
    applySummaryCounts(summary || {});
    renderBriefing(summary || {});
    renderSummaryGrid(summary || {});
    var suffix = OPS.providerMode === 'http' ? ' · executor' : ' · sample';
    var title = document.title || '';
    if (title.indexOf(suffix) === -1 && title.indexOf('运营工作台') !== -1) {
      document.title = '运营工作台 - CrazyAgentsManage' + suffix;
    }
    updateWorkspaceActions(OPS.currentFamily);
  }).catch(function() {
    _fetch('/api/operations/summary').then(function(summary) {
      OPS.summary = summary || null;
      applySummaryCounts(summary || {});
      renderBriefing(summary || {});
      renderSummaryGrid(summary || {});
      return _fetch('/api/operations/integrations/provider-mode');
    }).then(function(info) {
      if (info) {
        OPS.providerMode = info.mode || 'sample';
        OPS.capabilities = info.capabilities || OPS.capabilities;
        var suffix = OPS.providerMode === 'http' ? ' · executor' : ' · sample';
        var title = document.title || '';
        if (title.indexOf(suffix) === -1 && title.indexOf('运营工作台') !== -1) {
          document.title = '运营工作台 - CrazyAgentsManage' + suffix;
        }
        updateWorkspaceActions(OPS.currentFamily);
      }
    }).catch(function() {
      renderBriefing({});
      renderSummaryGrid({});
    });
  });
}

function _updateTreeCount(family, count) {
  var el = document.querySelector('.ops-tree-item[data-family="' + family + '"] .ops-tree-item-count');
  if (el) el.textContent = count;
}

function applySummaryCounts(summary) {
  var metrics = summary.metrics || {};
  _setText('ops-skills-count', metrics.skillsCount || 0);
  _setText('ops-cron-count', metrics.cronCount || 0);
  _setText('ops-memory-count', metrics.memoryCount || 0);
  _setText('ops-integrations-count', metrics.integrationCount || 0);

  _updateTreeCount('skills', metrics.skillsCount || 0);
  _updateTreeCount('cron', metrics.cronCount || 0);
  _updateTreeCount('memory', metrics.memoryCount || 0);
  _updateTreeCount('task-registry', metrics.taskRegistryCount || 0);
  _updateTreeCount('automation', metrics.automationCount || 0);
  _updateTreeCount('host-health', metrics.hostHealthCount || 0);
  _updateTreeCount('harness', metrics.harnessCount || 0);
  _updateTreeCount('env-map', metrics.envMapCount || 0);
  _updateTreeCount('backup-recovery', metrics.backupRecoveryCount || 0);
  _updateTreeCount('recovery-paths', metrics.recoveryPathCount || 0);
  _updateTreeCount('runbooks', metrics.runbookCount || 0);
  _updateTreeCount('isolation', metrics.isolationCount || 0);
  _updateTreeCount('alerts', (summary.alerts && summary.alerts.total) || 0);
  _updateTreeCount('sources', metrics.integrationCount || 0);
  _updateTreeCount('tools', metrics.toolCount || 0);
  _updateTreeCount('credentials', metrics.credentialCount || 0);
  _updateTreeCount('providers', metrics.providerCount || 0);
  _updateTreeCount('boundary', metrics.boundaryCount || 1);
}

function renderBriefing(summary) {
  var briefing = summary.briefing || {};
  _setText('ops-briefing-label', briefing.label || 'Operations aggregation');
  _setText('ops-briefing-title', briefing.title || '运营对象聚合摘要不可用');
  _setText('ops-briefing-copy', briefing.summary || '当前未拿到 Operations summary payload。');

  var nextHop = summary.nextHop || {};
  var nextHopEl = _el('ops-next-hop');
  if (nextHopEl) {
    nextHopEl.href = _url(nextHop.href || '/operations');
    nextHopEl.setAttribute('data-status', summary.status || 'unknown');
  }
  _setText('ops-next-hop-label', nextHop.label || '回到 Operations 主面');
  _setText('ops-next-hop-reason', nextHop.reason || '当前没有可用的下一跳建议。');
}

function renderSummaryGrid(summary) {
  var grid = _el('ops-summary-grid');
  if (!grid) return;
  var families = summary.families || [];
  if (!families.length) {
    grid.innerHTML = '<div class="ops-summary-card">' +
      '<div class="ops-summary-icon">⚠️</div>' +
      '<div><div class="ops-summary-title">摘要不可用</div><div class="ops-summary-copy">当前未能加载 Operations summary payload。</div></div>' +
    '</div>';
    return;
  }

  grid.innerHTML = families.map(function(card) {
    return '<a class="ops-summary-card" href="' + _url(card.href || '/operations') + '">' +
      '<div class="ops-summary-icon">' + (card.icon || '•') + '</div>' +
      '<div style="min-width:0;">' +
        '<div class="ops-summary-header">' +
          '<div class="ops-summary-title">' + (card.title || card.key || 'Summary') + '</div>' +
          '<span class="ops-chip ' + (card.status || 'unknown') + '">' + statusLabel(card.status || 'unknown') + '</span>' +
        '</div>' +
        '<div class="ops-summary-value">' + (card.count != null ? card.count : '--') + '</div>' +
        '<div class="ops-summary-copy">' + (card.summary || '—') + '</div>' +
      '</div>' +
    '</a>';
  }).join('');
}

// ============================================================
// Family switching
// ============================================================

function updateWorkspaceActions(family) {
  if (!_el('ops-workspace-actions')) return;
  _el('ops-workspace-actions').innerHTML = family === 'sources'
    ? (OPS.capabilities.sourceCreate
      ? '<button class="ops-btn ops-btn-primary" onclick="showImportSourceModal()">+ 导入 Source</button>'
      : '<button class="ops-btn ops-btn-secondary" disabled title="真实 executor 模式下仅支持按插件类型创建 source">+ 导入 Source</button>')
    : (family === 'credentials'
      ? (OPS.capabilities.credentialBind
        ? '<button class="ops-btn ops-btn-primary" onclick="showBindCredentialModal()">+ 绑定凭证</button>'
        : '<button class="ops-btn ops-btn-secondary" disabled>+ 绑定凭证</button>')
      : '');
}

function switchFamily(family) {
  if (family === OPS.currentFamily) {
    updateWorkspaceActions(family);
    return;
  }

  var items = document.querySelectorAll('.ops-tree-item');
  for (var i = 0; i < items.length; i++) {
    items[i].classList.toggle('active', items[i].getAttribute('data-family') === family);
  }

  OPS.currentFamily = family;
  OPS.selectedItemId = null;
  OPS.filterText = '';
  OPS.filterChip = '';

  var def = FAMILIES[family];
  _el('ops-workspace-title').innerHTML = '<span>' + def.icon + '</span> ' + def.label;

  updateWorkspaceActions(family);

  _el('ops-rail').innerHTML =
    '<div class="ops-detail-card"><div class="ops-detail-empty">选择一个对象查看详情</div></div>';

  loadWorkspace(family);
}

// ============================================================
// Workspace rendering
// ============================================================

function loadWorkspace(family) {
  var def = FAMILIES[family];
  var content = _el('ops-workspace-content');
  content.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⏳</div><p>加载中...</p></div>';

  _fetch(def.api).then(function(data) {
    OPS.cache[family] = data;
    renderWorkspace(family, data);
    _focusOpsContext(_actionContext());
  }).catch(function() {
    content.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function renderWorkspace(family, data) {
  var content = _el('ops-workspace-content');

  switch (family) {
    case 'cron':      renderFilterableCron(content, data); break;
    case 'alerts':    renderFilterableAlerts(content, data); break;
    case 'skills':    renderFilterableSkills(content, data); break;
    case 'memory':    renderMemory(content, data); break;
    case 'task-registry': renderTaskRegistry(content, data); break;
    case 'automation': renderAutomationMaturity(content, data); break;
    case 'host-health': renderHostHealth(content, data); break;
    case 'harness': renderHarness(content, data); break;
    case 'env-map': renderEnvMap(content, data); break;
    case 'backup-recovery': renderBackupRecovery(content, data); break;
    case 'recovery-paths': renderRecoveryPaths(content, data); break;
    case 'runbooks':  renderRunbooks(content, data); break;
    case 'isolation': renderIsolation(content, data); break;
    case 'sources':   renderFilterableSources(content, data); break;
    case 'tools':     renderFilterableTools(content, data); break;
    case 'credentials': renderFilterableCredentials(content, data); break;
    case 'providers': renderFilterableProviders(content, data); break;
    case 'boundary':  renderBoundary(content, data); break;
  }
}

// ============================================================
// Filter bar helper
// ============================================================

function _filterBar(chips) {
  var html = '<div class="ops-filter-bar">' +
    '<input class="ops-search-input" type="text" placeholder="搜索..." id="ops-search-input" oninput="onFilterInput()">' +
    '<div class="ops-filter-chips" id="ops-filter-chips">';
  if (chips && chips.length) {
    html += '<span class="ops-filter-chip active" data-chip="" onclick="onFilterChip(this, \'\')">全部</span>';
    for (var i = 0; i < chips.length; i++) {
      html += '<span class="ops-filter-chip" data-chip="' + chips[i].value + '" onclick="onFilterChip(this, \'' + chips[i].value + '\')">' + chips[i].label + '</span>';
    }
  }
  html += '</div></div>';
  return html;
}

function onFilterInput() {
  OPS.filterText = (_el('ops-search-input').value || '').toLowerCase();
  reFilter();
}

function onFilterChip(el, value) {
  OPS.filterChip = value;
  var chips = document.querySelectorAll('#ops-filter-chips .ops-filter-chip');
  for (var i = 0; i < chips.length; i++) {
    chips[i].classList.toggle('active', chips[i].getAttribute('data-chip') === value);
  }
  reFilter();
}

function reFilter() {
  var family = OPS.currentFamily;
  var data = OPS.cache[family];
  if (!data) return;
  renderWorkspace(family, data);
}

function _matchesFilter(item, fields) {
  if (!OPS.filterText) return true;
  for (var i = 0; i < fields.length; i++) {
    var val = item[fields[i]];
    if (val && String(val).toLowerCase().indexOf(OPS.filterText) !== -1) return true;
  }
  return false;
}

function _matchesChip(item, field) {
  if (!OPS.filterChip) return true;
  return String(item[field] || '') === OPS.filterChip;
}

function _showDetail(html) {
  _el('ops-rail').innerHTML = '<div class="ops-detail-card">' + html + '</div>';
}

function showToast(message, type) {
  var stack = document.getElementById('ops-toast-stack');
  if (!stack) {
    if (type === 'error') alert(message);
    return;
  }
  var toast = document.createElement('div');
  toast.className = 'ops-toast ' + (type || 'info');
  toast.textContent = message;
  stack.appendChild(toast);
  window.setTimeout(function() {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 180ms ease';
  }, 2200);
  window.setTimeout(function() {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 2600);
}

function rerenderCurrentWorkspace() {
  if (!OPS.cache[OPS.currentFamily]) return;
  renderWorkspace(OPS.currentFamily, OPS.cache[OPS.currentFamily]);
}

function _replaceInCache(family, matcher, replacer) {
  var list = OPS.cache[family];
  if (!Array.isArray(list)) return null;
  for (var i = 0; i < list.length; i++) {
    if (matcher(list[i], i)) {
      list[i] = replacer(list[i], i);
      return {item: list[i], index: i};
    }
  }
  return null;
}

function _removeFromCache(family, matcher) {
  var list = OPS.cache[family];
  if (!Array.isArray(list)) return false;
  for (var i = 0; i < list.length; i++) {
    if (matcher(list[i], i)) {
      list.splice(i, 1);
      return true;
    }
  }
  return false;
}

function _appendToCache(family, item) {
  if (!Array.isArray(OPS.cache[family])) OPS.cache[family] = [];
  OPS.cache[family].push(item);
}

// Filter helper: preserve original array index for correct selection after filtering
function _filterWithOrig(arr, filterFn) {
  var result = [];
  for (var i = 0; i < arr.length; i++) {
    if (filterFn(arr[i], i)) {
      result.push({item: arr[i], origIdx: i});
    }
  }
  return result;
}

// ============================================================
// Render: Cron with filter
// ============================================================

function renderFilterableCron(container, jobs) {
  if (!Array.isArray(jobs) || jobs.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⏰</div><p>暂无定时任务</p></div>';
    return;
  }

  var filtered = jobs.filter(function(j) {
    return _matchesFilter(j, ['name', 'id', 'schedule', 'cron']) && _matchesChip(j, 'active');
  });

  var chips = [
    {value: 'true', label: '运行中'},
    {value: 'false', label: '已暂停'},
  ];

  container.innerHTML = _filterBar(chips) + '<div class="ops-cron-list">' +
    (filtered.length ? filtered.map(function(j) {
      var active = j.active !== false && j.paused !== true;
      var cls = active ? 'active' : 'paused';
      var txt = active ? '运行中' : '已暂停';
      return '<div class="ops-cron-item" data-id="' + (j.id || '') + '" onclick="selectCron(\'' + (j.id || '') + '\')">' +
        '<span class="ops-cron-icon">⏰</span>' +
        '<div class="ops-cron-info">' +
          '<p class="ops-cron-name">' + (j.name || j.id || '未命名') + '</p>' +
          '<span class="ops-cron-schedule">' + (j.schedule || j.cron || '--') + '</span>' +
        '</div>' +
        '<span class="ops-cron-status ' + cls + '">' + txt + '</span>' +
        '<span class="ops-cron-outputs">' + (j.output_count || 0) + ' 次输出</span>' +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectCron(id) {
  var jobs = OPS.cache['cron'] || [];
  var job = null;
  for (var i = 0; i < jobs.length; i++) {
    if (jobs[i].id === id || jobs[i].name === id) { job = jobs[i]; break; }
  }
  if (!job) return;
  _highlightSelected('ops-cron-item', id, 'id');
  var active = job.active !== false && job.paused !== true;
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + (job.name || job.id || '未命名') + '</h3>' +
      '<div class="ops-detail-sub">' + (job.schedule || job.cron || '--') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">状态</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">运行状态</span><span class="ops-detail-row-value">' + (active ? '运行中' : '已暂停') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">输出次数</span><span class="ops-detail-row-value">' + (job.output_count || 0) + '</span></div>' +
    '</div>'
  );
}

// ============================================================
// Render: Alerts with filter
// ============================================================

function renderFilterableAlerts(container, alerts) {
  if (!Array.isArray(alerts) || alerts.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">✅</div><p>暂无告警</p></div>';
    return;
  }

  var filtered = _filterWithOrig(alerts, function(a) {
    return _matchesFilter(a, ['source', 'message']) && _matchesChip(a, 'level');
  });

  var chips = [
    {value: 'critical', label: '严重'},
    {value: 'warning', label: '警告'},
    {value: 'info', label: '信息'},
  ];

  container.innerHTML = _filterBar(chips) + '<div class="ops-alerts-list">' +
    (filtered.length ? filtered.map(function(pair) {
      var a = pair.item;
      var icon = a.level === 'critical' ? '🔴' : (a.level === 'warning' ? '🟡' : '🔵');
      return '<div class="ops-alert-item" data-idx="' + pair.origIdx + '" onclick="selectAlert(' + pair.origIdx + ')">' +
        '<div class="ops-alert-icon ' + (a.level || 'info') + '">' + icon + '</div>' +
        '<div class="ops-alert-content">' +
          '<p class="ops-alert-title">' + (a.source || '系统') + '</p>' +
          '<p class="ops-alert-detail">' + (a.message || '—') + '</p>' +
        '</div>' +
        '<span class="ops-alert-time">' + (a.time || '--') + '</span>' +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectAlert(idx) {
  var alerts = OPS.cache['alerts'] || [];
  var a = alerts[idx];
  if (!a) return;
  _highlightSelected('ops-alert-item', idx, 'idx');
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + (a.source || '系统') + '</h3>' +
      '<div class="ops-detail-sub">' + (a.level || 'info') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">详情</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">消息</span><span class="ops-detail-row-value">' + (a.message || '—') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">时间</span><span class="ops-detail-row-value">' + (a.time || '--') + '</span></div>' +
    '</div>'
  );
}

// ============================================================
// Render: Skills with filter
// ============================================================

function renderFilterableSkills(container, data) {
  var skills = (data.skills || []).slice(0, 40);
  if (skills.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🔧</div><p>暂无已安装技能</p></div>';
    return;
  }

  var filtered = _filterWithOrig(skills, function(s) {
    return _matchesFilter(s, ['name', 'description', 'category']) && _matchesChip(s, 'category');
  });

  var cats = {};
  skills.forEach(function(s) { cats[s.category] = (cats[s.category] || 0) + 1; });
  var chips = Object.keys(cats).sort().map(function(k) { return {value: k, label: k}; });

  container.innerHTML = _filterBar(chips) + '<div class="ops-skills-grid">' +
    (filtered.length ? filtered.map(function(pair) {
      var s = pair.item;
      return '<div class="ops-skill-card" onclick="selectSkill(' + pair.origIdx + ')">' +
        '<div class="ops-skill-category">' + (s.category_display || s.category || '') + '</div>' +
        '<div class="ops-skill-name">' + (s.name || '') + '</div>' +
        '<div class="ops-skill-desc">' + (s.description || '—') + '</div>' +
      '</div>';
    }).join('') : '<div class="ops-empty" style="grid-column:1/-1"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectSkill(idx) {
  var data = OPS.cache['skills'] || {skills:[]};
  var s = data.skills[idx];
  if (!s) return;
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + (s.name || '') + '</h3>' +
      '<div class="ops-detail-sub">' + (s.category_display || s.category || '') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">描述</div>' +
      '<div style="font-size:13px;color:var(--ops-text-secondary);">' + (s.description || '—') + '</div>' +
    '</div>'
  );
}

// ============================================================
// Render: Memory (no filter needed)
// ============================================================

function renderMemory(container, memories) {
  if (!Array.isArray(memories) || memories.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">📝</div><p>暂无记忆文件</p></div>';
    return;
  }

  var filtered = memories.filter(function(m) {
    return _matchesFilter(m, ['name', 'path', 'preview']);
  });

  container.innerHTML = _filterBar([]) + '<div class="ops-memory-grid">' +
    (filtered.length ? filtered.map(function(m, idx) {
      return '<div class="ops-memory-card" onclick="selectMemory(' + idx + ')">' +
        '<p class="ops-memory-name">' + (m.name || '未命名') + '</p>' +
        '<p class="ops-memory-preview">' + (m.preview || '(空)') + '</p>' +
        '<div class="ops-memory-meta">' +
          '<span>' + (m.path || '') + '</span>' +
          '<span>' + (m.size || 0) + ' bytes</span>' +
        '</div>' +
      '</div>';
    }).join('') : '<div class="ops-empty" style="grid-column:1/-1"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectMemory(idx) {
  var memories = OPS.cache['memory'] || [];
  var m = memories[idx];
  if (!m) return;
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + (m.name || '未命名') + '</h3>' +
      '<div class="ops-detail-sub">' + (m.path || '') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">预览</div>' +
      '<div style="font-size:13px;color:var(--ops-text-secondary);word-break:break-all;">' + (m.preview || '(空)') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">大小</span><span class="ops-detail-row-value">' + (m.size || 0) + ' bytes</span></div>' +
    '</div>'
  );
}

// ============================================================
// Render: Sources with filter + tool sublist on select
// ============================================================

function renderFilterableSources(container, sources) {
  if (!Array.isArray(sources) || sources.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🔌</div><p>暂无集成源</p></div>';
    return;
  }

  var filtered = _filterWithOrig(sources, function(s) {
    return _matchesFilter(s, ['name', 'type', 'scope', 'provider', 'id']) && _matchesChip(s, 'type');
  });

  var chips = [
    {value: 'openapi', label: 'OpenAPI'},
    {value: 'graphql', label: 'GraphQL'},
    {value: 'mcp', label: 'MCP'},
    {value: 'discovery', label: 'Discovery'},
  ];

  var iconMap = {openapi: '🔷', graphql: '🟣', mcp: '🟪', discovery: '🔵'};

  container.innerHTML = _filterBar(chips) + '<div class="ops-source-list">' +
    (filtered.length ? filtered.map(function(pair) {
      var s = pair.item;
      var icon = iconMap[s.type] || '🔌';
      return '<div class="ops-source-item" data-idx="' + pair.origIdx + '" onclick="selectSource(' + pair.origIdx + ')">' +
        '<div class="ops-source-icon ' + (s.type || '') + '">' + icon + '</div>' +
        '<div class="ops-source-info">' +
          '<div class="ops-source-name">' + s.name + '</div>' +
          '<div class="ops-source-meta">' + (s.type || '') + ' · ' + (s.scope || '') + '</div>' +
        '</div>' +
        '<span class="ops-chip ' + (s.status || 'unknown') + '">' + statusLabel(s.status) + '</span>' +
        '<span style="font-size:12px;color:var(--ops-text-muted);white-space:nowrap;">' + (s.toolCount || 0) + ' 工具</span>' +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectSource(idx) {
  var sources = OPS.cache['sources'] || [];
  var s = sources[idx];
  if (!s) return;
  OPS.selectedItemId = s.id;
  _highlightSelected('ops-source-item', idx, 'idx');

  var isDisabled = s.status === 'disabled';
  var canRefresh = !!OPS.capabilities.sourceRefresh && !s.isControl && s.canRefresh !== false;
  var canDelete = !!OPS.capabilities.sourceDelete && !s.isControl && s.canRemove !== false;
  var refreshBtn = canRefresh
    ? '<button class="ops-btn ops-btn-sm ops-btn-primary" onclick="refreshSource(\'' + s.id + '\')">刷新</button>'
    : '<button class="ops-btn ops-btn-sm ops-btn-secondary" disabled title="当前 source 不支持刷新">刷新</button>';
  var toggleBtn = '<button class="ops-btn ops-btn-sm ' + (isDisabled ? 'ops-btn-primary' : 'ops-btn-warning') + '" ' + (OPS.capabilities.sourceStatusToggle ? '' : 'disabled title="真实 executor 模式下未开放通用状态切换"') + ' onclick="toggleSourceStatus(\'' + s.id + '\', \'' + s.status + '\')">' + (isDisabled ? '启用' : '禁用') + '</button>';
  var deleteBtn = canDelete
    ? '<button class="ops-btn ops-btn-sm ops-btn-danger" onclick="deleteSource(\'' + s.id + '\')">删除</button>'
    : '<button class="ops-btn ops-btn-sm ops-btn-secondary" disabled title="当前 source 不支持删除">删除</button>';

  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + s.name + '</h3>' +
      '<div class="ops-detail-sub">' + (s.type || '') + (s.isControl ? ' · control source' : '') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">状态</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">状态</span><span class="ops-detail-row-value"><span class="ops-chip ' + (s.status || 'unknown') + '">' + statusLabel(s.status) + '</span></span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Scope</span><span class="ops-detail-row-value">' + (s.scope || '—') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">工具数</span><span class="ops-detail-row-value">' + (s.toolCount || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Provider</span><span class="ops-detail-row-value">' + (s.provider || '—') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Can Remove</span><span class="ops-detail-row-value">' + (s.canRemove ? 'yes' : 'no') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Can Refresh</span><span class="ops-detail-row-value">' + (s.canRefresh ? 'yes' : 'no') + '</span></div>' +
    '</div>' +
    '<div class="ops-detail-actions">' + refreshBtn + toggleBtn + deleteBtn + '</div>' +
    '<div class="ops-source-tools" id="ops-source-tools">' +
      '<div class="ops-source-tools-title">工具目录</div>' +
      '<div style="font-size:12px;color:var(--ops-text-muted);padding:8px 0;">加载中...</div>' +
    '</div>'
  );

  _fetch('/api/operations/integrations/tools?sourceId=' + s.id).then(function(tools) {
    var toolsEl = document.getElementById('ops-source-tools');
    if (!toolsEl) return;
    if (!tools || !tools.length) {
      toolsEl.innerHTML = '<div class="ops-source-tools-title">工具目录</div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);padding:8px 0;">该 source 暂无可用工具</div>';
      return;
    }
    toolsEl.innerHTML = '<div class="ops-source-tools-title">工具目录 (' + tools.length + ')</div>' +
      tools.map(function(t) {
        return '<div class="ops-source-tool-item">' +
          '<span class="ops-source-tool-name">' + t.name + '</span>' +
          '<span class="ops-chip ' + (t.status || 'unknown') + '" style="font-size:10px;">' + statusLabel(t.status) + '</span>' +
        '</div>';
      }).join('');
  }).catch(function() {
    var toolsEl = document.getElementById('ops-source-tools');
    if (toolsEl) {
      toolsEl.innerHTML = '<div class="ops-source-tools-title">工具目录</div>' +
        '<div style="font-size:12px;color:var(--ops-color-red);padding:8px 0;">加载失败</div>';
    }
  });
}

// ============================================================
// Render: Tools with filter
// ============================================================

function renderFilterableTools(container, tools) {
  if (!Array.isArray(tools) || tools.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🧰</div><p>暂无工具目录</p></div>';
    return;
  }

  var filtered = _filterWithOrig(tools, function(t) {
    return _matchesFilter(t, ['name', 'summary', 'sourceId', 'id']) && _matchesChip(t, 'status');
  });

  var chips = [
    {value: 'available', label: '可用'},
    {value: 'auth-required', label: '需认证'},
    {value: 'disabled', label: '已禁用'},
  ];

  container.innerHTML = _filterBar(chips) + '<div class="ops-tool-list">' +
    (filtered.length ? filtered.map(function(pair) {
      var t = pair.item;
      return '<div class="ops-tool-item" data-idx="' + pair.origIdx + '" onclick="selectTool(' + pair.origIdx + ')">' +
        '<div class="ops-tool-info">' +
          '<div class="ops-tool-name">' + t.name + '</div>' +
          '<div class="ops-tool-summary">' + (t.summary || t.schemaSummary || '') + '</div>' +
        '</div>' +
        '<span class="ops-chip ' + (t.status || 'unknown') + '">' + statusLabel(t.status) + '</span>' +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectTool(idx) {
  var tools = OPS.cache['tools'] || [];
  var t = tools[idx];
  if (!t) return;
  _highlightSelected('ops-tool-item', idx, 'idx');
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + t.name + '</h3>' +
      '<div class="ops-detail-sub">' + (t.sourceId || '') + '</div>' +
    '</div>' +
      '<div class="ops-detail-section">' +
        '<div class="ops-detail-section-title">工具信息</div>' +
        '<div class="ops-detail-row"><span class="ops-detail-row-label">状态</span><span class="ops-detail-row-value"><span class="ops-chip ' + (t.status || 'unknown') + '">' + statusLabel(t.status) + '</span></span></div>' +
        '<div class="ops-detail-row"><span class="ops-detail-row-label">需认证</span><span class="ops-detail-row-value">' + (t.requiresAuth ? '是' : '否') + '</span></div>' +
        '<div class="ops-detail-row"><span class="ops-detail-row-label">Schema 摘要</span><span class="ops-detail-row-value">' + (t.schemaSummary || '—') + '</span></div>' +
      '</div>' +
        (t.summary ? '<div class="ops-detail-section"><div class="ops-detail-section-title">描述</div><div style="font-size:13px;color:var(--ops-text-secondary);">' + t.summary + '</div></div>' : '')
  );
}

// ============================================================
// Render: Credentials with filter
// ============================================================

function renderFilterableCredentials(container, creds) {
  if (!Array.isArray(creds) || creds.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🔑</div><p>暂无凭证记录</p></div>';
    return;
  }

  var filtered = _filterWithOrig(creds, function(c) {
    return _matchesFilter(c, ['provider', 'targetId', 'id']) && _matchesChip(c, 'status');
  });

  var chips = [
    {value: 'healthy', label: '健康'},
    {value: 'missing', label: '缺失'},
    {value: 'expired', label: '已过期'},
  ];

  container.innerHTML = _filterBar(chips) + '<div class="ops-cred-list">' +
    (filtered.length ? filtered.map(function(pair) {
      var c = pair.item;
      return '<div class="ops-cred-item" data-idx="' + pair.origIdx + '" onclick="selectCredential(' + pair.origIdx + ')">' +
        '<div class="ops-cred-info">' +
          '<div class="ops-cred-provider">' + (c.provider || '') + '</div>' +
          '<div class="ops-cred-target">目标: ' + (c.targetId || '') + '</div>' +
        '</div>' +
        '<span class="ops-chip ' + (c.status || 'unknown') + '">' + statusLabel(c.status) + '</span>' +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectCredential(idx) {
  var creds = OPS.cache['credentials'] || [];
  var c = creds[idx];
  if (!c) return;
  _highlightSelected('ops-cred-item', idx, 'idx');
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + (c.provider || '') + '</h3>' +
      '<div class="ops-detail-sub">目标: ' + (c.targetId || '') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">凭证状态</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">状态</span><span class="ops-detail-row-value"><span class="ops-chip ' + (c.status || 'unknown') + '">' + statusLabel(c.status) + '</span></span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Provider</span><span class="ops-detail-row-value">' + (c.provider || '—') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">影响工具数</span><span class="ops-detail-row-value">' + (c.impactCount || 0) + '</span></div>' +
      (c.slot ? '<div class="ops-detail-row"><span class="ops-detail-row-label">Slot</span><span class="ops-detail-row-value">' + c.slot + '</span></div>' : '') +
      (c.valueKind ? '<div class="ops-detail-row"><span class="ops-detail-row-label">值类型</span><span class="ops-detail-row-value">' + c.valueKind + '</span></div>' : '') +
      (c.lastCheckedAt ? '<div class="ops-detail-row"><span class="ops-detail-row-label">最后检查</span><span class="ops-detail-row-value">' + c.lastCheckedAt + '</span></div>' : '') +
    '</div>' +
    '<div class="ops-detail-actions">' +
      '<button class="ops-btn ops-btn-sm ops-btn-danger" ' + (OPS.capabilities.credentialUnbind ? '' : 'disabled') + ' onclick="unbindCredential(\'' + c.id + '\')">解绑</button>' +
    '</div>'
  );
}

// ============================================================
// Render: Providers with filter
// ============================================================

function renderFilterableProviders(container, provs) {
  if (!Array.isArray(provs) || provs.length === 0) {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">📡</div><p>暂无 Provider 记录</p></div>';
    return;
  }

  var filtered = _filterWithOrig(provs, function(p) {
    return _matchesFilter(p, ['provider', 'issueSummary', 'id']) && _matchesChip(p, 'status');
  });

  var chips = [
    {value: 'reachable', label: '可达'},
    {value: 'degraded', label: '降级'},
    {value: 'failed', label: '失败'},
  ];

  container.innerHTML = _filterBar(chips) + '<div class="ops-provider-list">' +
    (filtered.length ? filtered.map(function(pair) {
      var p = pair.item;
      return '<div class="ops-provider-item" data-idx="' + pair.origIdx + '" onclick="selectProvider(' + pair.origIdx + ')">' +
        '<div class="ops-provider-info">' +
          '<div class="ops-provider-name">' + (p.provider || '') + '</div>' +
          '<div class="ops-provider-meta">' + (p.sourceCount || 0) + ' sources · ' + (p.toolCount || 0) + ' tools</div>' +
        '</div>' +
        '<span class="ops-chip ' + (p.status || 'unknown') + '">' + statusLabel(p.status) + '</span>' +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">🔍</div><p>无匹配结果</p></div>') +
  '</div>';
}

function selectProvider(idx) {
  var provs = OPS.cache['providers'] || [];
  var p = provs[idx];
  if (!p) return;
  _highlightSelected('ops-provider-item', idx, 'idx');
  _showDetail(
    '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">' + (p.provider || '') + '</h3>' +
      '<div class="ops-detail-sub">Provider Health</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">状态</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">状态</span><span class="ops-detail-row-value"><span class="ops-chip ' + (p.status || 'unknown') + '">' + statusLabel(p.status) + '</span></span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Sources</span><span class="ops-detail-row-value">' + (p.sourceCount || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Tools</span><span class="ops-detail-row-value">' + (p.toolCount || 0) + '</span></div>' +
      (p.issueSummary ? '<div class="ops-detail-row"><span class="ops-detail-row-label">问题</span><span class="ops-detail-row-value" style="color:var(--ops-color-red);">' + p.issueSummary + '</span></div>' : '') +
    '</div>'
  );
}

// ============================================================
// Render: Readonly Boundary
// ============================================================

function renderBoundary(container, boundary) {
  if (!boundary || typeof boundary !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🧭</div><p>暂无 boundary 数据</p></div>';
    return;
  }

  var allowed = boundary.allowedTaskTypes || [];
  var completed = boundary.completedTaskTypes || [];
  var forbidden = boundary.forbiddenTaskTypes || [];

  container.innerHTML =
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Capability Plane Boundary</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Provider Mode</span><span class="ops-detail-row-value"><span class="ops-chip ' + (boundary.providerMode === 'http' ? 'healthy' : 'degraded') + '">' + (boundary.providerMode || 'unknown') + '</span></span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Policy</span><span class="ops-detail-row-value">' + (boundary.version || '--') + ' · ' + (boundary.policyPath || '--') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Owners</span><span class="ops-detail-row-value">' + ((boundary.owners && Object.keys(boundary.owners).length) ? Object.keys(boundary.owners).length + ' lanes' : '—') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Task Types</span><span class="ops-detail-row-value">' + (boundary.totalTaskTypeCount || 0) + '</span></div>' +
    '</div>' +
    '<div class="ops-summary-grid" style="margin-top:16px;">' +
      boundaryCard('Wave 1 Allowed', '🟢', allowed.length, 'healthy') +
      boundaryCard('Wave 2 Completed', '✅', completed.length, 'healthy') +
      boundaryCard('Forbidden Now', '⛔', forbidden.length, forbidden.length ? 'degraded' : 'healthy') +
    '</div>' +
    '<div class="ops-detail-section" style="margin-top:16px;">' +
      '<div class="ops-detail-section-title">Preconditions</div>' +
      '<div style="display:grid;gap:8px;">' + (boundary.preconditions || []).map(function(item) {
        return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + item + '</span></div>';
      }).join('') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section" style="margin-top:16px;">' +
      '<div class="ops-detail-section-title">Runbooks</div>' +
      '<div style="display:grid;gap:8px;">' + (boundary.runbooks || []).map(function(item) {
        return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + item + '</span></div>';
      }).join('') + '</div>' +
    '</div>';

  _showDetail(buildBoundaryDetail(boundary, allowed, completed, forbidden));
}

// ============================================================
// Render: Role / Credential / Memory Isolation
// ============================================================

function renderIsolation(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🧱</div><p>暂无 isolation 数据</p></div>';
    return;
  }

  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Roles', '👥', counts.roleCount || 0, data.roleStatus || 'unknown') +
      boundaryCard('Credentials', '🔑', counts.credentialCount || 0, data.credentialStatus || 'unknown') +
      boundaryCard('Memory Planes', '📝', counts.memoryBoundaryCount || 0, data.memoryStatus || 'unknown') +
      boundaryCard('Runbooks', '📚', counts.runbookCount || 0, data.runbookStatus || 'unknown') +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Isolation Summary</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Overall</span><span class="ops-detail-row-value"><span class="ops-chip ' + (data.status || 'unknown') + '">' + statusLabel(data.status || 'unknown') + '</span></span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Missing Credentials</span><span class="ops-detail-row-value">' + (counts.missingCredentialCount || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Missing Runbooks</span><span class="ops-detail-row-value">' + (counts.missingRunbookCount || 0) + '</span></div>' +
    '</div>';

  _showDetail(buildIsolationDetail(data));
}

// ============================================================
// Render: Task Registry / Automation / Host / Runbooks
// ============================================================

function renderTaskRegistry(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">📋</div><p>暂无 task registry 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  var owners = data.owners || [];
  var lanes = data.lanes || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Open', '📥', counts.open || 0, data.status || 'unknown') +
      boundaryCard('Working', '🧰', counts.working || 0, data.status || 'unknown') +
      boundaryCard('Failed', '⚠️', counts.failed || 0, (counts.failed || counts.timedOut ? 'degraded' : 'healthy')) +
      boundaryCard('Timed Out', '⏱️', counts.timedOut || 0, counts.timedOut ? 'degraded' : 'healthy') +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Task Registry Summary</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Total</span><span class="ops-detail-row-value">' + (counts.total || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Lanes</span><span class="ops-detail-row-value">inbox=' + ((lanes.inbox || []).length) + ' · working=' + ((lanes.working || []).length) + ' · outbox=' + ((lanes.outbox || []).length) + ' · archive=' + ((lanes.archive || []).length) + '</span></div>' +
    '</div>' +
    isolationSection('Open Owners', owners.slice(0, 8), function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.owner + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">open=' + item.open + ' · pending=' + item.pending + ' · failed=' + item.failed + '</div>' +
      '</div>';
    }) +
    isolationSection('Recent Requests', (data.items || []).slice(0, 12), function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + (item.action || item.request_id || '--') + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">owner=' + (item.owner || '--') + ' · lane=' + (item.lane || '--') + ' · auto=' + (item.automation_state || 'prototype') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Task Registry</h3><div class="ops-detail-sub">request bus object flow</div></div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Linked Runbooks</div>' +
      (data.runbooks || []).map(function(path) {
        return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + path + '</span></div>';
      }).join('') +
    '</div>' +
    isolationSection('Lane Details', ['inbox', 'working', 'outbox', 'archive'].map(function(name) {
      return { name: name, count: (lanes[name] || []).length };
    }), function(item) {
      return '<div class="ops-detail-row"><span class="ops-detail-row-label">' + item.name + '</span><span class="ops-detail-row-value">' + item.count + '</span></div>';
    })
  );
}

function renderAutomationMaturity(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🤖</div><p>暂无 automation 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Prototype', '🧪', counts.prototype || 0, counts.prototype ? 'degraded' : 'unknown') +
      boundaryCard('Rehearsed', '🛠️', counts.rehearsed || 0, data.status || 'unknown') +
      boundaryCard('Approved', '✅', counts.approved || 0, data.status || 'unknown') +
      boundaryCard('Automated', '⚙️', counts.automated || 0, data.status || 'unknown') +
    '</div>' +
    isolationSection('Promoted Workflows', data.items || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + (item.action || item.request_id || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">state=' + (item.automation_state || 'prototype') + ' · owner=' + (item.owner || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">rollback=' + (item.rollback_rule || '--') + ' · evidence=' + ((item.evidence_refs || []).join(' | ') || '--') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Automation Maturity</h3><div class="ops-detail-sub">promotion state and rollback discipline</div></div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Linked Runbooks</div>' +
      (data.runbooks || []).map(function(path) { return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + path + '</span></div>'; }).join('') +
    '</div>'
  );
}

function renderHostHealth(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🖥️</div><p>暂无 host health 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Disk', '💽', (data.host && data.host.disk && data.host.disk.used_percent != null) ? data.host.disk.used_percent + '%' : '--', data.diskStatus || 'unknown') +
      boundaryCard('Memory', '🧠', (data.host && data.host.memory && data.host.memory.used_percent != null) ? data.host.memory.used_percent + '%' : '--', data.memoryStatus || 'unknown') +
      boundaryCard('Gateway', '📡', counts.platforms || 0, data.gatewayState === 'running' ? 'healthy' : 'degraded') +
      boundaryCard('Alerts', '🔔', counts.alerts || 0, counts.alerts ? 'degraded' : 'healthy') +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Host Evidence</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Gateway</span><span class="ops-detail-row-value">' + (data.gatewayState || '--') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Active Agents</span><span class="ops-detail-row-value">' + (counts.activeAgents || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Platforms</span><span class="ops-detail-row-value">' + (counts.platforms || 0) + '</span></div>' +
    '</div>' +
    isolationSection('Recent Alerts', data.alerts || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + (item.source || '--') + ' <span class="ops-chip ' + (item.level === 'critical' ? 'failed' : item.level === 'warning' ? 'degraded' : 'healthy') + '">' + (item.level || '--') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.message || '') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Host Health Evidence</h3><div class="ops-detail-sub">disk / memory / gateway / alerts</div></div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Linked Runbooks</div>' +
      (data.runbooks || []).map(function(path) { return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + path + '</span></div>'; }).join('') +
    '</div>'
  );
}

function renderHarness(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🧪</div><p>暂无 harness 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Success', '✅', counts.successCount || 0, data.status || 'unknown') +
      boundaryCard('Failure', '⚠️', counts.failureCount || 0, counts.failureCount ? 'degraded' : 'healthy') +
      boundaryCard('Closeouts', '📦', counts.closeoutCount || 0, data.status || 'unknown') +
      boundaryCard('Pending', '🧾', counts.pendingCloseoutCount || 0, counts.pendingCloseoutCount ? 'degraded' : 'healthy') +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Harness Summary</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Failure newer than success</span><span class="ops-detail-row-value">' + (data.failureNewerThanSuccess ? 'yes' : 'no') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Default entry</span><span class="ops-detail-row-value">' + (((data.policy || {}).defaultEntry) || '--') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Direct trace policy</span><span class="ops-detail-row-value">' + (((data.policy || {}).directTracePolicy) || '--') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Latest success</span><span class="ops-detail-row-value">' + ((data.latestSuccess && data.latestSuccess.id) || '--') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Latest failure</span><span class="ops-detail-row-value">' + ((data.latestFailure && data.latestFailure.id) || '--') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Latest closeout</span><span class="ops-detail-row-value">' + ((data.latestCloseout && data.latestCloseout.id) || '--') + '</span></div>' +
    '</div>' +
    isolationSection('Readiness Layers', data.readiness || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.notes || '') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Harness Readiness</h3><div class="ops-detail-sub">success / failure / critic / closeout / worktree</div></div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Required Commands</div>' +
      (data.commands || []).map(function(cmd) { return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + cmd + '</span></div>'; }).join('') +
    '</div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Runbooks</div>' +
      (data.runbooks || []).map(function(path) { return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + path + '</span></div>'; }).join('') +
    '</div>'
  );
}

function renderEnvMap(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🗺️</div><p>暂无 env map 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Configured', '✅', counts.configuredCount || 0, data.status || 'unknown') +
      boundaryCard('Drift', '⚠️', counts.driftCount || 0, counts.driftCount ? 'degraded' : 'healthy') +
      boundaryCard('Entries', '🗂️', counts.entryCount || 0, data.status || 'unknown') +
    '</div>' +
    isolationSection('Env Entries', data.entries || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + (item.value || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">owner=' + (item.owner || '--') + ' · ' + (item.notes || '') + '</div>' +
      '</div>';
    }) +
    isolationSection('Drift Signals', data.driftEntries || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + (item.value || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.reason || '') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Environment Map</h3><div class="ops-detail-sub">deploy shell / runtime root / capability endpoints</div></div>' +
    isolationSection('Env Map', data.entries || [], function(item) {
      return '<div class="ops-detail-row"><span class="ops-detail-row-label">' + item.name + '</span><span class="ops-detail-row-value">' + item.value + '</span></div>';
    })
  );
}

function renderBackupRecovery(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🛟</div><p>暂无 backup/recovery 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Healthy', '✅', counts.healthyCount || 0, data.status || 'unknown') +
      boundaryCard('Degraded', '⚠️', counts.degradedCount || 0, counts.degradedCount ? 'degraded' : 'healthy') +
      boundaryCard('Surfaces', '🗂️', counts.surfaceCount || 0, data.status || 'unknown') +
    '</div>' +
    isolationSection('Backup Surfaces', data.surfaces || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + (item.location || '--') + ' · count=' + (item.count || 0) + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.recoveryPath || '') + '</div>' +
      '</div>';
    }) +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Backup Coverage</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Deploy Copy Backups</span><span class="ops-detail-row-value">' + ((data.coverage || {}).deployCopyBackups || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Host Backup Snapshots</span><span class="ops-detail-row-value">' + ((data.coverage || {}).hostBackupSnapshots || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Memory Edit Backups</span><span class="ops-detail-row-value">' + ((data.coverage || {}).memoryEditBackups || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Mirror Manifest</span><span class="ops-detail-row-value">' + (((data.coverage || {}).mirrorManifestPresent) ? 'present' : 'missing') + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Runbook Coverage</span><span class="ops-detail-row-value">' + ((data.coverage || {}).runbookCoverage || 0) + '</span></div>' +
    '</div>';

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Backup / Recovery</h3><div class="ops-detail-sub">backup coverage and recovery path visibility</div></div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Linked Runbooks</div>' +
      (data.runbooks || []).map(function(path) { return '<div class="ops-detail-row"><span class="ops-detail-row-value">' + path + '</span></div>'; }).join('') +
    '</div>'
  );
}

function renderRecoveryPaths(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🧭</div><p>暂无 recovery path 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Ready', '✅', counts.readyCount || 0, data.status || 'unknown') +
      boundaryCard('Degraded', '⚠️', counts.degradedCount || 0, counts.degradedCount ? 'degraded' : 'healthy') +
      boundaryCard('Env Drift', '🗺️', counts.envDriftCount || 0, counts.envDriftCount ? 'degraded' : 'healthy') +
      boundaryCard('Paths', '🧭', counts.pathCount || 0, data.status || 'unknown') +
    '</div>' +
    isolationSection('Recovery Paths', data.paths || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status === 'ready' ? 'healthy' : 'degraded') + '">' + (item.status === 'ready' ? 'ready' : 'degraded') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">trigger=' + (item.trigger || '--') + ' · owner=' + (item.owner || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.recoveryPath || []).join(' → ') + '</div>' +
      '</div>';
    }) +
    isolationSection('Env Drift Signals', data.envDrift || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + (item.value || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.reason || '') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Recovery Paths</h3><div class="ops-detail-sub">explicit restoration paths and env-drift linkage</div></div>' +
    '<div class="ops-detail-section"><div class="ops-detail-section-title">Backup Coverage Snapshot</div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Deploy Backups</span><span class="ops-detail-row-value">' + ((data.backupCoverage || {}).deployCopyBackups || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Host Backups</span><span class="ops-detail-row-value">' + ((data.backupCoverage || {}).hostBackupSnapshots || 0) + '</span></div>' +
      '<div class="ops-detail-row"><span class="ops-detail-row-label">Mirror Manifest</span><span class="ops-detail-row-value">' + (((data.backupCoverage || {}).mirrorManifestPresent) ? 'present' : 'missing') + '</span></div>' +
    '</div>'
  );
}

function renderRunbooks(container, data) {
  if (!data || typeof data !== 'object') {
    container.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">📚</div><p>暂无 runbook 数据</p></div>';
    return;
  }
  var counts = data.counts || {};
  container.innerHTML =
    '<div class="ops-summary-grid" style="margin-bottom:16px;">' +
      boundaryCard('Visible', '📘', counts.visibleCount || 0, data.status || 'unknown') +
      boundaryCard('Missing', '⚠️', counts.missingCount || 0, counts.missingCount ? 'degraded' : 'healthy') +
      boundaryCard('Total', '🗂️', counts.runbookCount || 0, data.status || 'unknown') +
    '</div>' +
    isolationSection('Runbooks', data.items || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status === 'visible' ? 'healthy' : 'degraded') + '">' + (item.status === 'visible' ? '可见' : '缺失') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + (item.path || '--') + '</div>' +
      '</div>';
    });

  _showDetail(
    '<div class="ops-detail-header"><h3 class="ops-detail-name">Runbook Visibility</h3><div class="ops-detail-sub">next-hop operator guides</div></div>' +
    isolationSection('Runbook List', data.items || [], function(item) {
      return '<div class="ops-detail-row"><span class="ops-detail-row-label">' + item.name + '</span><span class="ops-detail-row-value">' + item.path + '</span></div>';
    })
  );
}

function buildIsolationDetail(data) {
  return '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">Role / Credential / Memory Isolation</h3>' +
      '<div class="ops-detail-sub">control-room isolation registry</div>' +
    '</div>' +
    isolationSection('Role Registry', data.roleRegistry || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">lane=' + (item.lane || '--') + ' · memory=' + (item.memoryBoundary || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">scope=' + (item.primaryScopes || []).join(' | ') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">credentials=' + (item.credentialBoundary || '--') + '</div>' +
      '</div>';
    }) +
    isolationSection('Credential Ownership', data.credentialOwnership || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + (item.provider || '--') + ' → ' + (item.targetId || '--') + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">owner=' + (item.ownerRole || item.owner || '--') + ' · impact=' + (item.impactCount || 0) + ' · kind=' + (item.valueKind || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.notes || '') + '</div>' +
      '</div>';
    }) +
    isolationSection('Memory Boundaries', data.memoryBoundaries || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status || 'unknown') + '">' + statusLabel(item.status || 'unknown') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">owner=' + (item.owner || '--') + ' · files=' + (item.fileCount || 0) + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">write=' + (item.writeBoundary || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">roots=' + (item.roots || []).join(' | ') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + (item.notes || '') + '</div>' +
      '</div>';
    }) +
    isolationSection('Runbook Visibility', data.runbooks || [], function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + item.name + ' <span class="ops-chip ' + (item.status === 'visible' ? 'healthy' : 'degraded') + '">' + (item.status === 'visible' ? '可见' : '缺失') + '</span></div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + (item.path || '--') + '</div>' +
      '</div>';
    });
}

function isolationSection(title, items, renderer) {
  return '<div class="ops-detail-section">' +
    '<div class="ops-detail-section-title">' + title + '</div>' +
    (items.length ? items.map(renderer).join('') : '<div class="ops-empty"><div class="ops-empty-icon">—</div><p>当前为空</p></div>') +
  '</div>';
}

function boundaryCard(title, icon, count, status) {
  return '<div class="ops-summary-card">' +
    '<div class="ops-summary-icon">' + icon + '</div>' +
    '<div style="min-width:0;">' +
      '<div class="ops-summary-header">' +
        '<div class="ops-summary-title">' + title + '</div>' +
        '<span class="ops-chip ' + status + '">' + statusLabel(status) + '</span>' +
      '</div>' +
      '<div class="ops-summary-value">' + count + '</div>' +
      '<div class="ops-summary-copy">executor readonly delegation policy</div>' +
    '</div>' +
  '</div>';
}

function buildBoundaryDetail(boundary, allowed, completed, forbidden) {
  return '<div class="ops-detail-header">' +
      '<h3 class="ops-detail-name">Readonly Capability Boundary</h3>' +
      '<div class="ops-detail-sub">' + (boundary.host || 'ALI-HERMES') + ' · mode=' + (boundary.providerMode || 'unknown') + '</div>' +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Execution Boundary</div>' +
      listDetailRows('Canonical Authority', boundary.executionBoundary && boundary.executionBoundary.canonicalAuthority) +
      listDetailRows('Local Writable Targets', boundary.executionBoundary && boundary.executionBoundary.localWritableTargets) +
      listDetailRows('Human Gate Actions', boundary.executionBoundary && boundary.executionBoundary.humanGateActions) +
      listDetailRows('Forbidden Mutations', boundary.executionBoundary && boundary.executionBoundary.forbiddenMutations) +
    '</div>' +
    '<div class="ops-detail-section">' +
      '<div class="ops-detail-section-title">Owners</div>' +
      Object.keys(boundary.owners || {}).map(function(key) {
        return '<div class="ops-detail-row"><span class="ops-detail-row-label">' + key + '</span><span class="ops-detail-row-value">' + boundary.owners[key] + '</span></div>';
      }).join('') +
    '</div>' +
    boundaryTaskSection('Wave 1 Allowed', allowed, 'healthy') +
    boundaryTaskSection('Wave 2 Completed', completed, 'healthy') +
    boundaryTaskSection('Forbidden Now', forbidden, 'degraded');
}

function listDetailRows(label, values) {
  if (!Array.isArray(values) || !values.length) {
    return '<div class="ops-detail-row"><span class="ops-detail-row-label">' + label + '</span><span class="ops-detail-row-value">—</span></div>';
  }
  return '<div class="ops-detail-row"><span class="ops-detail-row-label">' + label + '</span><span class="ops-detail-row-value">' + values.join(' | ') + '</span></div>';
}

function boundaryTaskSection(title, items, status) {
  return '<div class="ops-detail-section">' +
    '<div class="ops-detail-section-title">' + title + ' <span class="ops-chip ' + status + '">' + statusLabel(status) + '</span></div>' +
    ((items && items.length) ? items.map(function(item) {
      return '<div style="padding:10px 0;border-bottom:1px solid rgba(148,163,184,0.12);">' +
        '<div style="font-weight:600;">' + (item.taskType || '--') + '</div>' +
        '<div style="font-size:12px;color:var(--ops-text-muted);margin-top:4px;">' + ((item.repoEntrypoints || []).join(' | ') || '—') + '</div>' +
        (item.delegationUnit ? '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">delegation=' + item.delegationUnit + '</div>' : '') +
        (item.resolution ? '<div style="font-size:12px;color:var(--ops-text-secondary);margin-top:4px;">' + item.resolution + '</div>' : '') +
        (item.reason ? '<div style="font-size:12px;color:var(--ops-color-red);margin-top:4px;">' + item.reason + '</div>' : '') +
      '</div>';
    }).join('') : '<div class="ops-empty"><div class="ops-empty-icon">—</div><p>当前为空</p></div>') +
  '</div>';
}

// ============================================================
// Utility
// ============================================================

function statusLabel(status) {
  var map = {
    healthy: '健康', reachable: '可达', available: '可用',
    degraded: '降级',
    'missing-auth': '缺少凭证', 'auth-required': '需认证',
    disabled: '已禁用',
    failed: '失败', 'invalid-schema': 'Schema 无效',
    missing: '缺失', expired: '已过期',
    sample: '样例',
    http: '实连',
    unknown: '未知',
  };
  return map[status] || status;
}

function _highlightSelected(className, id, attr) {
  var items = document.querySelectorAll('.' + className);
  for (var i = 0; i < items.length; i++) {
    items[i].classList.toggle('selected', items[i].getAttribute('data-' + attr) == id);
  }
}

// ============================================================
// Modal & write actions (Phase 2)
// ============================================================

function showModal(id) {
  var all = document.querySelectorAll('#ops-modal-overlay > div > div');
  for (var i = 0; i < all.length; i++) { all[i].style.display = 'none'; }
  var el = document.getElementById(id);
  if (el) el.style.display = 'block';
  document.getElementById('ops-modal-overlay').style.display = 'flex';
}

function closeModal(e) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('ops-modal-overlay').style.display = 'none';
}

function onImportTypeChange() {
  var type = document.getElementById('src-import-type').value;
  var show = function(id, yes) {
    var el = document.getElementById(id);
    if (el) el.style.display = yes ? 'block' : 'none';
  };
  show('src-import-openapi-fields', type === 'openapi');
  show('src-import-graphql-fields', type === 'graphql');
  show('src-import-mcp-fields', type === 'mcp');
  show('src-import-discovery-fields', type === 'discovery');
}

function onMcpTransportChange() {
  var transport = document.getElementById('src-import-mcp-transport').value;
  var remote = document.getElementById('src-import-mcp-remote-fields');
  var stdio = document.getElementById('src-import-mcp-stdio-fields');
  if (remote) remote.style.display = transport === 'remote' ? 'block' : 'none';
  if (stdio) stdio.style.display = transport === 'stdio' ? 'block' : 'none';
}

function onCredentialValueKindChange() {
  var kind = document.getElementById('cred-bind-value-kind').value;
  var secret = document.getElementById('cred-bind-secret-fields');
  var text = document.getElementById('cred-bind-text-fields');
  var connection = document.getElementById('cred-bind-connection-fields');
  if (secret) secret.style.display = kind === 'secret' ? 'block' : 'none';
  if (text) text.style.display = kind === 'text' ? 'block' : 'none';
  if (connection) connection.style.display = kind === 'connection' ? 'block' : 'none';
}

function onCredentialSourceChange() {
  var select = document.getElementById('cred-bind-source');
  var sourceId = select ? select.value : '';
  var src = (OPS.cache.sources || []).find(function(s) { return s.id === sourceId; });
  var slot = document.getElementById('cred-bind-slot');
  if (!src || !slot) return;
  if (src.type === 'openapi') slot.placeholder = '例如: header:authorization';
  else if (src.type === 'graphql') slot.placeholder = '例如: header:authorization';
  else if (src.type === 'mcp') slot.placeholder = '例如: header:authorization 或 auth:oauth2:connection';
  else slot.placeholder = '请输入 slot';
}

function populateCredentialSourceOptions() {
  var select = document.getElementById('cred-bind-source');
  if (!select) return;
  var sources = (OPS.cache.sources || []).filter(function(s) { return !s.isControl; });
  select.innerHTML = sources.map(function(s) {
    return '<option value="' + s.id + '">' + s.name + ' (' + s.type + ')</option>';
  }).join('');
  onCredentialSourceChange();
}

function showImportSourceModal() {
  var setValue = function(id, value) {
    var el = document.getElementById(id);
    if (el) el.value = value;
  };
  setValue('src-import-name', '');
  setValue('src-import-type', 'openapi');
  setValue('src-import-namespace', '');
  setValue('src-import-spec', '');
  setValue('src-import-base-url', '');
  setValue('src-import-endpoint', '');
  setValue('src-import-introspection', '');
  setValue('src-import-mcp-transport', 'remote');
  setValue('src-import-mcp-endpoint', '');
  setValue('src-import-mcp-command', '');
  setValue('src-import-mcp-args', '');
  setValue('src-import-mcp-cwd', '');
  setValue('src-import-discovery-url', '');
  onImportTypeChange();
  onMcpTransportChange();
  showModal('ops-modal-import-source');
}

function submitImportSource() {
  var type = document.getElementById('src-import-type').value;
  var payload = {
    type: type,
    name: document.getElementById('src-import-name').value.trim(),
    namespace: document.getElementById('src-import-namespace').value.trim() || undefined,
  };

  if (type === 'openapi') {
    payload.spec = document.getElementById('src-import-spec').value.trim();
    payload.baseUrl = document.getElementById('src-import-base-url').value.trim() || undefined;
    if (!payload.spec) { showToast('请输入 OpenAPI Spec', 'error'); return; }
  } else if (type === 'graphql') {
    payload.endpoint = document.getElementById('src-import-endpoint').value.trim();
    payload.introspectionJson = document.getElementById('src-import-introspection').value.trim() || undefined;
    if (!payload.endpoint) { showToast('请输入 GraphQL Endpoint', 'error'); return; }
  } else if (type === 'mcp') {
    payload.transport = document.getElementById('src-import-mcp-transport').value;
    if (payload.transport === 'remote') {
      payload.endpoint = document.getElementById('src-import-mcp-endpoint').value.trim();
      payload.remoteTransport = document.getElementById('src-import-mcp-remote-transport').value;
      if (!payload.endpoint) { showToast('请输入 MCP Endpoint', 'error'); return; }
    } else {
      payload.command = document.getElementById('src-import-mcp-command').value.trim();
      payload.args = (document.getElementById('src-import-mcp-args').value.trim() || '').split(/\s+/).filter(Boolean);
      payload.cwd = document.getElementById('src-import-mcp-cwd').value.trim() || undefined;
      if (!payload.command) { showToast('请输入 MCP Command', 'error'); return; }
    }
  } else if (type === 'discovery') {
    payload.discoveryUrl = document.getElementById('src-import-discovery-url').value.trim();
    if (!payload.discoveryUrl) { showToast('请输入 Discovery URL', 'error'); return; }
  }

  _fetch('/api/operations/integrations/sources', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  }).then(function(source) {
    closeModal();
    if (source) _appendToCache('sources', source);
    rerenderCurrentWorkspace();
    loadMetrics();
    showToast('Source 导入成功', 'success');
  }).catch(function(e) { showToast('导入失败: ' + e.message, 'error'); });
}

function showBindCredentialModal() {
  var setValue = function(id, value) {
    var el = document.getElementById(id);
    if (el) el.value = value;
  };
  setValue('cred-bind-slot', '');
  setValue('cred-bind-value-kind', 'secret');
  setValue('cred-bind-provider', 'file');
  setValue('cred-bind-secret-name', '');
  setValue('cred-bind-secret-value', '');
  setValue('cred-bind-text-value', '');
  setValue('cred-bind-connection-id', '');
  populateCredentialSourceOptions();
  onCredentialValueKindChange();
  showModal('ops-modal-bind-cred');
}

function submitBindCredential() {
  var sourceId = document.getElementById('cred-bind-source').value;
  var source = (OPS.cache.sources || []).find(function(s) { return s.id === sourceId; });
  var slot = document.getElementById('cred-bind-slot').value.trim();
  var valueKind = document.getElementById('cred-bind-value-kind').value;
  if (!source || !slot) { showToast('请选择 Source 并填写 Slot', 'error'); return; }

  var payload = {
    sourceType: source.type,
    targetType: 'source',
    targetId: source.id,
    sourceScope: source.scope,
    bindingScope: source.scope,
    slot: slot,
    valueKind: valueKind,
  };

  if (valueKind === 'secret') {
    payload.provider = document.getElementById('cred-bind-provider').value.trim() || 'file';
    payload.secretName = document.getElementById('cred-bind-secret-name').value.trim() || payload.provider;
    payload.secretValue = document.getElementById('cred-bind-secret-value').value;
    if (!payload.secretValue) { showToast('请输入 Secret Value', 'error'); return; }
  } else if (valueKind === 'text') {
    payload.textValue = document.getElementById('cred-bind-text-value').value;
    if (!payload.textValue) { showToast('请输入 Text Value', 'error'); return; }
  } else if (valueKind === 'connection') {
    payload.connectionId = document.getElementById('cred-bind-connection-id').value.trim();
    if (!payload.connectionId) { showToast('请输入 Connection ID', 'error'); return; }
  }

  _fetch('/api/operations/integrations/credentials', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  }).then(function(credential) {
    closeModal();
    if (credential) _appendToCache('credentials', credential);
    rerenderCurrentWorkspace();
    loadMetrics();
    showToast('凭证绑定成功', 'success');
  }).catch(function(e) { showToast('绑定失败: ' + e.message, 'error'); });
}

function refreshSource(sourceId) {
  _fetch('/api/operations/integrations/sources/' + sourceId, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ refresh: true }),
  }).then(function() {
    showToast('Source 刷新成功', 'success');
    loadWorkspace('sources');
  }).catch(function(e) {
    showToast('刷新失败: ' + e.message, 'error');
  });
}

function toggleSourceStatus(sourceId, currentStatus) {
  var newStatus = currentStatus === 'disabled' ? 'healthy' : 'disabled';
  _fetch('/api/operations/integrations/sources/' + sourceId, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({status: newStatus}),
  }).then(function(updatedSource) {
    var updated = _replaceInCache('sources', function(item) {
      return item.id === sourceId;
    }, function() {
      return updatedSource;
    });
    rerenderCurrentWorkspace();
    if (updated) selectSource(updated.index);
    showToast(newStatus === 'disabled' ? 'Source 已禁用' : 'Source 已启用', 'success');
  }).catch(function(e) {
    showToast('更新失败: ' + e.message, 'error');
  });
}

function deleteSource(sourceId) {
  if (!confirm('确定要删除此 Source 吗？')) return;
  _fetch('/api/operations/integrations/sources/' + sourceId, {
    method: 'DELETE',
  }).then(function() {
    _removeFromCache('sources', function(item) { return item.id === sourceId; });
    rerenderCurrentWorkspace();
    _el('ops-rail').innerHTML = '<div class="ops-detail-card"><div class="ops-detail-empty">已删除</div></div>';
    loadMetrics();
    showToast('Source 已删除', 'success');
  }).catch(function(e) {
    showToast('删除失败: ' + e.message, 'error');
  });
}

function unbindCredential(credId) {
  if (!confirm('确定要解绑此凭证吗？')) return;
  _fetch('/api/operations/integrations/credentials/' + credId, {
    method: 'DELETE',
  }).then(function() {
    _removeFromCache('credentials', function(item) { return item.id === credId; });
    rerenderCurrentWorkspace();
    _el('ops-rail').innerHTML = '<div class="ops-detail-card"><div class="ops-detail-empty">已解绑</div></div>';
    loadMetrics();
    showToast('凭证已解绑', 'success');
  }).catch(function(e) {
    showToast('解绑失败: ' + e.message, 'error');
  });
}

// ============================================================
// Init
// ============================================================

function applyHashFamily() {
  var family = _familyFromHash();
  if (family && family !== OPS.currentFamily) switchFamily(family);
}

function init() {
  window.addEventListener('hashchange', applyHashFamily);
  var initialFamily = _familyFromQuery() || _familyFromHash();
  if (initialFamily) {
    OPS.currentFamily = initialFamily;
    var items = document.querySelectorAll('.ops-tree-item');
    for (var i = 0; i < items.length; i++) {
      items[i].classList.toggle('active', items[i].getAttribute('data-family') === initialFamily);
    }
    var def = FAMILIES[initialFamily];
    _el('ops-workspace-title').innerHTML = '<span>' + def.icon + '</span> ' + def.label;
  }
  var context = _actionContext();
  _showContextBanner(_contextMessage(context), false);
  updateWorkspaceActions(OPS.currentFamily);
  loadMetrics();
  loadWorkspace(OPS.currentFamily);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
