document.addEventListener('DOMContentLoaded', function() {
  loadTasks();
});

var allTasks = [];
var currentStatusFilter = 'all';
var requestBus = [];
var requestBusLanes = { inbox: [], working: [], outbox: [], archive: [] };
var requestBusAutomation = {};

function fetchJsonWithTimeout(url) {
  var controller = new AbortController();
  var timeoutId = setTimeout(function() { controller.abort(); }, 60000);
  return fetch(url, { signal: controller.signal }).then(function(resp) {
    clearTimeout(timeoutId);
    return resp.json();
  });
}

function postJson(url, payload) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {}),
  }).then(function(resp) {
    return resp.json().catch(function() { return {}; }).then(function(data) {
      if (!resp.ok) {
        throw new Error(data && data.error ? data.error : ('HTTP ' + resp.status));
      }
      return data;
    });
  });
}

function showTaskBusBanner(message, isError) {
  var banner = document.getElementById('task-bus-banner');
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

function domSafeId(value) {
  return String(value || '').replace(/[^a-zA-Z0-9_-]/g, '-');
}

async function loadTasks() {
  showTaskBusBanner('', false);
  try {
    var taskData = await fetchJsonWithTimeout('./api/tasks/list');
    allTasks = taskData.tasks || [];

    var stats = taskData.stats || {};
    var statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = stats.total || 0;
    if (statValues[1]) statValues[1].textContent = stats.running || 0;
    if (statValues[2]) statValues[2].textContent = stats.completed || 0;
    if (statValues[3]) statValues[3].textContent = stats.failed || 0;

    renderStatusFilter();
    renderDAG(allTasks);
    renderTaskList(allTasks);
  } catch (e) {
    console.error('Failed to load tasks:', e);
    showTaskBusBanner('任务列表加载失败。', true);
  }

  try {
    var requestData = await fetchJsonWithTimeout('./api/tasks/request-bus');
    requestBus = requestData.requests || [];
    requestBusLanes = requestData.lanes || { inbox: [], working: [], outbox: [], archive: [] };
    requestBusAutomation = requestData.automation || {};
    renderRequestBusSummary(requestData.stats || {});
    renderAutomationSummary(requestBusAutomation);
    renderRequestBusLanes(requestBusLanes);
    renderRequestBus(requestBus);
  } catch (e) {
    console.error('Failed to load request bus:', e);
    showTaskBusBanner('task bus 控制面加载失败。', true);
  }
}

function renderStatusFilter() {
  var container = document.querySelector('.task-filter') || document.querySelector('.stats-grid');
  if (!container) return;

  var counts = { all: allTasks.length, running: 0, completed: 0, failed: 0, pending: 0 };
  allTasks.forEach(function(t) { if (counts[t.status] !== undefined) counts[t.status]++; });

  var filterBar = document.createElement('div');
  filterBar.className = 'task-filter-bar filter-bar';
  var labels = { all: '全部', running: '运行中', completed: '已完成', failed: '失败' };
  var colors = { all: '#667eea', running: '#f59e0b', completed: '#10b981', failed: '#ef4444' };
  filterBar.innerHTML = Object.keys(labels).map(function(s) {
    return '<button class="btn ' + (currentStatusFilter === s ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
      'onclick="filterTasks(\'' + s + '\')" ' +
      'style="' + (currentStatusFilter === s ? 'background:' + colors[s] + ';border-color:' + colors[s] : '') + '">' +
      labels[s] + ' (' + (counts[s] || 0) + ')</button>';
  }).join('');

  var existing = document.querySelector('.task-filter-bar');
  if (existing) existing.replaceWith(filterBar);
  else container.parentNode.insertBefore(filterBar, container.nextSibling);
}

function filterTasks(status) {
  currentStatusFilter = status;
  var filtered = status === 'all' ? allTasks : allTasks.filter(function(t) { return t.status === status; });
  renderStatusFilter();
  renderDAG(filtered);
  renderTaskList(filtered);
}

function renderDAG(tasks) {
  var container = document.querySelector('.dag-visualization') || document.querySelector('.dag-container');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无任务数据</div>';
    return;
  }

  var rootTasks = tasks.filter(function(t) { return !t.parent_session_id; });
  var childMap = {};
  tasks.forEach(function(t) {
    if (t.parent_session_id) {
      if (!childMap[t.parent_session_id]) childMap[t.parent_session_id] = [];
      childMap[t.parent_session_id].push(t);
    }
  });

  var layers = [];
  var processed = new Set();

  function buildLayers(taskId, depth) {
    if (processed.has(taskId)) return;
    processed.add(taskId);
    while (layers.length <= depth) layers.push([]);
    var task = tasks.find(function(t) { return t.id === taskId; });
    if (task) layers[depth].push(task);
    (childMap[taskId] || []).forEach(function(child) { buildLayers(child.id, depth + 1); });
  }

  rootTasks.forEach(function(t) { buildLayers(t.id, 0); });
  tasks.filter(function(t) { return !processed.has(t.id); }).forEach(function(t) {
    while (layers.length <= 0) layers.push([]);
    layers[0].push(t);
  });

  var statusColors = {
    running: { bg: '#f59e0b22', border: '#f59e0b', text: '运行中' },
    completed: { bg: '#10b98122', border: '#10b981', text: '已完成' },
    failed: { bg: '#ef444422', border: '#ef4444', text: '失败' },
    pending: { bg: '#64748b22', border: '#64748b', text: '等待中' },
  };

  var html = '<div style="overflow-x:auto;padding:16px;">';
  layers.forEach(function(layer, layerIdx) {
    html += '<div style="display:flex;gap:16px;justify-content:center;margin-bottom:' + (layerIdx < layers.length - 1 ? '32px' : '0') + ';">';
    layer.forEach(function(task) {
      var sc = statusColors[task.status] || statusColors.pending;
      html += '<div class="dag-node" style="background:' + sc.bg + ';border:1px solid ' + sc.border + '33;" onclick="showTaskDetail(\'' + escapeHtml(task.id) + '\')">' +
        '<div class="dag-node-header">' +
          '<div class="dag-node-status-dot" style="background:' + sc.border + ';"></div>' +
          '<span class="dag-node-name">' + escapeHtml(task.name) + '</span>' +
        '</div>' +
        '<div class="dag-node-source">' + getSourceEmoji(task.source) + ' ' + (task.source || '--') + '</div>' +
        '<div class="dag-node-status" style="color:' + sc.border + ';">' + sc.text + '</div>' +
        (task.duration ? '<div class="dag-node-duration">' + formatDuration(task.duration) + '</div>' : '') +
      '</div>';
    });
    html += '</div>';
    if (layerIdx < layers.length - 1) html += '<div class="dag-layer-connector">&darr;</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderTaskList(tasks) {
  var container = document.querySelector('.task-list') || document.querySelector('.tasks-table-body');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无任务记录</div>';
    return;
  }

  var statusMap = {
    running: { color: '#f59e0b', text: '运行中' },
    completed: { color: '#10b981', text: '已完成' },
    failed: { color: '#ef4444', text: '失败' },
    pending: { color: '#64748b', text: '等待中' },
  };

  container.innerHTML = tasks.slice(0, 20).map(function(task) {
    var st = statusMap[task.status] || statusMap.pending;
    return '<div class="task-row" onclick="showTaskDetail(\'' + escapeHtml(task.id) + '\')">' +
      '<div class="task-row-info">' +
        '<div class="task-row-name">' + escapeHtml(task.name) + '</div>' +
        '<div class="task-row-meta">' + getSourceEmoji(task.source) + ' ' + (task.source || '--') + ' &middot; ' + (task.model || '--') + '</div>' +
      '</div>' +
      '<span class="status-badge status-badge-' + (task.status || 'pending') + '">' + st.text + '</span>' +
      '<span class="task-row-duration">' + (task.duration ? formatDuration(task.duration) : '--') + '</span>' +
    '</div>';
  }).join('');
}

function renderRequestBusSummary(stats) {
  var container = document.querySelector('.request-bus-summary');
  if (!container) return;
  var chips = [
    ['总数', stats.total || 0],
    ['开放', stats.open || 0],
    ['Inbox', (requestBusLanes.inbox || []).length],
    ['Working', (requestBusLanes.working || []).length],
    ['Outbox', (requestBusLanes.outbox || []).length],
    ['Archive', (requestBusLanes.archive || []).length],
  ];
  container.innerHTML = chips.map(function(item) {
    return '<span class="status-badge">' + item[0] + ': ' + item[1] + '</span>';
  }).join('');
}

function renderAutomationSummary(stats) {
  var container = document.querySelector('.request-bus-automation-summary');
  if (!container) return;
  var chips = [
    ['prototype', stats.prototype || 0],
    ['rehearsed', stats.rehearsed || 0],
    ['approved', stats['approved-for-automation'] || 0],
    ['automated', stats.automated || 0],
  ];
  container.innerHTML = chips.map(function(item) {
    return '<span class="status-badge">' + item[0] + ': ' + item[1] + '</span>';
  }).join('');
}

function renderRequestBusLanes(lanes) {
  var container = document.querySelector('.request-bus-lanes');
  if (!container) return;
  var labels = {
    inbox: 'Inbox',
    working: 'Working',
    outbox: 'Outbox',
    archive: 'Archive',
  };
  container.innerHTML = Object.keys(labels).map(function(lane) {
    var items = lanes[lane] || [];
    return '<div class="card" style="padding:16px;">' +
      '<div class="section-title" style="margin-bottom:12px;">' + labels[lane] + ' (' + items.length + ')</div>' +
      (items.length ? items.map(renderRequestCard).join('') : '<div class="empty-state">当前没有对象</div>') +
    '</div>';
  }).join('');
}

function renderRequestBus(requests) {
  var container = document.querySelector('.request-bus-body');
  if (!container) return;

  if (!Array.isArray(requests) || requests.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无 task-bus 请求记录</div>';
    return;
  }

  container.innerHTML = requests.slice(0, 20).map(function(req) {
    var latestEvents = (req.events || []).slice(0, 3).map(function(event) {
      var payload = event.payload || {};
      var detail = payload.to_status || payload.to_state || payload.note || '';
      return '<div style="font-size:12px;color:#94a3b8;">' + escapeHtml(event.timestamp || '--') + ' · ' + escapeHtml(event.event_type || '--') + ' · ' + escapeHtml(detail) + '</div>';
    }).join('');
    return '<div class="task-row">' +
      '<div class="task-row-info">' +
        '<div class="task-row-name">' + escapeHtml(req.action || req.request_id || '未命名请求') + '</div>' +
        '<div class="task-row-meta">' + escapeHtml(req.sender || '--') + ' → ' + escapeHtml(req.target || '--') + ' · ack=' + escapeHtml(req.ack_id || '--') + ' · lane=' + escapeHtml(req.lane || '--') + ' · auto=' + escapeHtml(req.automation_state || 'prototype') + '</div>' +
        '<div style="margin-top:4px;">' + latestEvents + '</div>' +
      '</div>' +
      '<span class="status-badge status-badge-' + escapeHtml(req.status || 'queued') + '">' + escapeHtml(req.status || 'queued') + '</span>' +
      '<span class="task-row-duration">' + escapeHtml(req.updated_at || req.created_at || '--') + '</span>' +
    '</div>';
  }).join('');
}

function renderRequestCard(req) {
  var domId = domSafeId(req.ack_id);
  var eventsHtml = (req.events || []).slice(0, 3).map(function(event) {
    var payload = event.payload || {};
    var detail = payload.to_status || payload.to_state || payload.note || '';
    return '<div style="font-size:12px;color:#94a3b8;">' + escapeHtml(event.timestamp || '--') + ' · ' + escapeHtml(event.event_type || '--') + ' · ' + escapeHtml(detail) + '</div>';
  }).join('');
  var transitionOptions = (req.allowedTransitions || []).map(function(status) {
    return '<option value="' + escapeHtml(status) + '">' + escapeHtml(status) + '</option>';
  }).join('');
  var automationOptions = ['prototype', 'rehearsed', 'approved-for-automation', 'automated'].map(function(state) {
    return '<option value="' + escapeHtml(state) + '"' + (req.automation_state === state ? ' selected' : '') + '>' + escapeHtml(state) + '</option>';
  }).join('');
  var evidenceValue = Array.isArray(req.evidence_refs) ? req.evidence_refs.join(', ') : '';
  return '<div style="border:1px solid var(--color-border);border-radius:12px;padding:12px;margin-bottom:12px;">' +
    '<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">' +
      '<div>' +
        '<div style="font-weight:600;">' + escapeHtml(req.action || req.request_id || '未命名请求') + '</div>' +
        '<div style="font-size:12px;color:#94a3b8;margin-top:4px;">' + escapeHtml(req.sender || '--') + ' → ' + escapeHtml(req.target || '--') + ' · owner=' + escapeHtml(req.owner || '--') + ' · ack=' + escapeHtml(req.ack_id || '--') + '</div>' +
        '<div style="font-size:12px;color:#94a3b8;margin-top:4px;">status=' + escapeHtml(req.status || '--') + ' · lane=' + escapeHtml(req.lane || '--') + ' · automation=' + escapeHtml(req.automation_state || 'prototype') + '</div>' +
      '</div>' +
      '<span class="status-badge status-badge-' + escapeHtml(req.status || 'queued') + '">' + escapeHtml(req.status || 'queued') + '</span>' +
    '</div>' +
    '<div style="margin-top:8px;font-size:12px;color:#94a3b8;">最近事件</div>' +
    '<div style="margin-top:4px;">' + (eventsHtml || '<div style="font-size:12px;color:#64748b;">暂无事件</div>') + '</div>' +
    '<div style="display:grid;gap:8px;margin-top:12px;">' +
      '<div style="display:grid;grid-template-columns:180px 1fr auto;gap:8px;align-items:center;">' +
        '<select class="input" id="bus-status-' + domId + '">' + (transitionOptions || '<option value="">无可用流转</option>') + '</select>' +
        '<input class="input" id="bus-status-note-' + domId + '" value="' + escapeHtml(req.last_transition_note || '') + '" placeholder="状态流转说明">' +
        '<button type="button" class="btn btn-primary btn-sm" onclick="transitionTaskBus(\'' + escapeHtml(req.ack_id) + '\')">更新状态</button>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:180px 1fr 1fr;gap:8px;">' +
        '<select class="input" id="bus-auto-' + domId + '">' + automationOptions + '</select>' +
        '<input class="input" id="bus-approval-' + domId + '" value="' + escapeHtml(req.approval || '') + '" placeholder="approval / approver ref">' +
        '<input class="input" id="bus-rollback-' + domId + '" value="' + escapeHtml(req.rollback_rule || '') + '" placeholder="rollback rule">' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr auto;gap:8px;align-items:center;">' +
        '<input class="input" id="bus-evidence-' + domId + '" value="' + escapeHtml(evidenceValue) + '" placeholder="evidence refs，逗号分隔">' +
        '<input class="input" id="bus-auto-note-' + domId + '" value="' + escapeHtml(req.note || '') + '" placeholder="晋升说明或回退原因">' +
        '<button type="button" class="btn btn-secondary btn-sm" onclick="promoteTaskBus(\'' + escapeHtml(req.ack_id) + '\')">记录晋升</button>' +
      '</div>' +
    '</div>' +
  '</div>';
}

function collectValue(id) {
  var el = document.getElementById(id);
  return el ? String(el.value || '').trim() : '';
}

function transitionTaskBus(ackId) {
  var domId = domSafeId(ackId);
  var status = collectValue('bus-status-' + domId);
  if (!status) {
    showTaskBusBanner('当前请求没有可用状态流转。', true);
    return;
  }
  postJson('./api/tasks/request-bus/' + encodeURIComponent(ackId) + '/transition', {
    status: status,
    note: collectValue('bus-status-note-' + domId),
  }).then(function() {
    showTaskBusBanner('task bus 状态已更新。', false);
    return loadTasks();
  }).catch(function(err) {
    showTaskBusBanner(err && err.message ? err.message : '状态流转失败。', true);
  });
}

function promoteTaskBus(ackId) {
  var domId = domSafeId(ackId);
  postJson('./api/tasks/request-bus/' + encodeURIComponent(ackId) + '/automation-state', {
    automationState: collectValue('bus-auto-' + domId),
    approval: collectValue('bus-approval-' + domId),
    rollbackRule: collectValue('bus-rollback-' + domId),
    evidenceRefs: collectValue('bus-evidence-' + domId),
    note: collectValue('bus-auto-note-' + domId),
  }).then(function() {
    showTaskBusBanner('automation promotion gate 已更新。', false);
    return loadTasks();
  }).catch(function(err) {
    showTaskBusBanner(err && err.message ? err.message : 'automation promotion 更新失败。', true);
  });
}

function showTaskDetail(taskId) {
  var task = allTasks.find(function(t) { return t.id === taskId; });
  if (!task) return;

  var existing = document.getElementById('taskDetailModal');
  if (existing) existing.remove();

  var statusMap = {
    running: { color: '#f59e0b', text: '运行中' },
    completed: { color: '#10b981', text: '已完成' },
    failed: { color: '#ef4444', text: '失败' },
    pending: { color: '#64748b', text: '等待中' },
  };
  var st = statusMap[task.status] || statusMap.pending;

  var modal = document.createElement('div');
  modal.id = 'taskDetailModal';
  modal.className = 'modal-overlay';
  modal.innerHTML = '<div class="modal-content">' +
    '<button class="modal-close" onclick="document.getElementById(\'taskDetailModal\').remove()">&times;</button>' +
    '<h2 class="modal-title" style="margin-bottom:16px;">' + escapeHtml(task.name) + '</h2>' +
    '<div class="detail-grid">' +
      '<div class="detail-cell"><div class="detail-label">状态</div><div class="detail-value" style="color:' + st.color + '">' + st.text + '</div></div>' +
      '<div class="detail-cell"><div class="detail-label">来源</div><div class="detail-value">' + getSourceEmoji(task.source) + ' ' + escapeHtml(task.source || '--') + '</div></div>' +
      '<div class="detail-cell"><div class="detail-label">模型</div><div class="detail-value">' + escapeHtml(task.model || '--') + '</div></div>' +
      '<div class="detail-cell"><div class="detail-label">持续时间</div><div class="detail-value">' + (task.duration ? formatDuration(task.duration) : '--') + '</div></div>' +
      '<div class="detail-cell"><div class="detail-label">消息数</div><div class="detail-value">' + (task.message_count || 0) + '</div></div>' +
      '<div class="detail-cell"><div class="detail-label">工具调用</div><div class="detail-value">' + (task.tool_call_count || 0) + '</div></div>' +
    '</div>' +
    '<div style="margin-top:16px;text-align:center;">' +
      '<a href="/sessions" class="link-more">在会话流水线中查看 &rarr;</a>' +
    '</div>' +
  '</div>';
  modal.onclick = function(e) { if (e.target === modal) modal.remove(); };
  document.body.appendChild(modal);
}
