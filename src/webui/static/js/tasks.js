document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
});

let allTasks = [];
let currentStatusFilter = 'all';

async function loadTasks() {
  try {
    const resp = await fetch('./api/tasks/list');
    const data = await resp.json();
    allTasks = data.tasks || [];

    const stats = data.stats || {};
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = stats.total || 0;
    if (statValues[1]) statValues[1].textContent = stats.running || 0;
    if (statValues[2]) statValues[2].textContent = stats.completed || 0;
    if (statValues[3]) statValues[3].textContent = stats.failed || 0;

    renderStatusFilter();
    renderDAG(allTasks);
    renderTaskList(allTasks);
  } catch (e) {
    console.error('Failed to load tasks:', e);
  }
}

function renderStatusFilter() {
  const container = document.querySelector('.task-filter') || document.querySelector('.stats-grid');
  if (!container) return;

  const counts = { all: allTasks.length, running: 0, completed: 0, failed: 0, pending: 0 };
  allTasks.forEach(t => { if (counts[t.status] !== undefined) counts[t.status]++; });

  const filterBar = document.createElement('div');
  filterBar.className = 'task-filter-bar filter-bar';
  const labels = { all: '全部', running: '运行中', completed: '已完成', failed: '失败' };
  const colors = { all: '#667eea', running: '#f59e0b', completed: '#10b981', failed: '#ef4444' };
  filterBar.innerHTML = Object.entries(labels).map(([s, label]) =>
    `<button class="btn ${currentStatusFilter === s ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="filterTasks('${s}')" style="${currentStatusFilter === s ? 'background:' + colors[s] + ';border-color:' + colors[s] : ''}">${label} (${counts[s]})</button>`
  ).join('');

  const existing = document.querySelector('.task-filter-bar');
  if (existing) existing.replaceWith(filterBar);
  else container.parentNode.insertBefore(filterBar, container.nextSibling);
}

function filterTasks(status) {
  currentStatusFilter = status;
  const filtered = status === 'all' ? allTasks : allTasks.filter(t => t.status === status);
  renderStatusFilter();
  renderDAG(filtered);
  renderTaskList(filtered);
}

function renderDAG(tasks) {
  const container = document.querySelector('.dag-visualization') || document.querySelector('.dag-container');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无任务数据</div>';
    return;
  }

  const rootTasks = tasks.filter(t => !t.parent_session_id);
  const childMap = {};
  tasks.forEach(t => {
    if (t.parent_session_id) {
      if (!childMap[t.parent_session_id]) childMap[t.parent_session_id] = [];
      childMap[t.parent_session_id].push(t);
    }
  });

  const layers = [];
  const processed = new Set();

  function buildLayers(taskId, depth) {
    if (processed.has(taskId)) return;
    processed.add(taskId);
    while (layers.length <= depth) layers.push([]);
    const task = tasks.find(t => t.id === taskId);
    if (task) layers[depth].push(task);
    (childMap[taskId] || []).forEach(child => buildLayers(child.id, depth + 1));
  }

  rootTasks.forEach(t => buildLayers(t.id, 0));
  tasks.filter(t => !processed.has(t.id)).forEach(t => {
    while (layers.length <= 0) layers.push([]);
    layers[0].push(t);
  });

  const statusColors = {
    running: { bg: '#f59e0b22', border: '#f59e0b', text: '运行中' },
    completed: { bg: '#10b98122', border: '#10b981', text: '已完成' },
    failed: { bg: '#ef444422', border: '#ef4444', text: '失败' },
    pending: { bg: '#64748b22', border: '#64748b', text: '等待中' },
  };

  let html = '<div style="overflow-x:auto;padding:16px;">';
  layers.forEach((layer, layerIdx) => {
    html += `<div style="display:flex;gap:16px;justify-content:center;margin-bottom:${layerIdx < layers.length - 1 ? '32px' : '0'};">`;
    layer.forEach(task => {
      const sc = statusColors[task.status] || statusColors.pending;
      html += `<div class="dag-node" style="background:${sc.bg};border:1px solid ${sc.border}33;" onclick="showTaskDetail('${escapeHtml(task.id)}')">
        <div class="dag-node-header">
          <div class="dag-node-status-dot" style="background:${sc.border};"></div>
          <span class="dag-node-name">${escapeHtml(task.name)}</span>
        </div>
        <div class="dag-node-source">${getSourceEmoji(task.source)} ${task.source || '--'}</div>
        <div class="dag-node-status" style="color:${sc.border};">${sc.text}</div>
        ${task.duration ? `<div class="dag-node-duration">${formatDuration(task.duration)}</div>` : ''}
      </div>`;
    });
    html += '</div>';
    if (layerIdx < layers.length - 1) {
      html += '<div class="dag-layer-connector">&darr;</div>';
    }
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderTaskList(tasks) {
  const container = document.querySelector('.task-list') || document.querySelector('.tasks-table-body');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无任务记录</div>';
    return;
  }

  const statusMap = {
    running: { color: '#f59e0b', text: '运行中' },
    completed: { color: '#10b981', text: '已完成' },
    failed: { color: '#ef4444', text: '失败' },
    pending: { color: '#64748b', text: '等待中' },
  };

  container.innerHTML = tasks.slice(0, 20).map(task => {
    const st = statusMap[task.status] || statusMap.pending;
    return `<div class="task-row" onclick="showTaskDetail('${escapeHtml(task.id)}')">
      <div class="task-row-info">
        <div class="task-row-name">${escapeHtml(task.name)}</div>
        <div class="task-row-meta">${getSourceEmoji(task.source)} ${task.source || '--'} &middot; ${task.model || '--'}</div>
      </div>
      <span class="status-badge status-badge-${task.status || 'pending'}">${st.text}</span>
      <span class="task-row-duration">${task.duration ? formatDuration(task.duration) : '--'}</span>
    </div>`;
  }).join('');
}

function showTaskDetail(taskId) {
  const task = allTasks.find(t => t.id === taskId);
  if (!task) return;

  const existing = document.getElementById('taskDetailModal');
  if (existing) existing.remove();

  const statusMap = {
    running: { color: '#f59e0b', text: '运行中' },
    completed: { color: '#10b981', text: '已完成' },
    failed: { color: '#ef4444', text: '失败' },
    pending: { color: '#64748b', text: '等待中' },
  };
  const st = statusMap[task.status] || statusMap.pending;

  const modal = document.createElement('div');
  modal.id = 'taskDetailModal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="modal-close" onclick="document.getElementById('taskDetailModal').remove()">&times;</button>
      <h2 class="modal-title" style="margin-bottom:16px;">${escapeHtml(task.name)}</h2>
      <div class="detail-grid">
        <div class="detail-cell"><div class="detail-label">状态</div><div class="detail-value" style="color:${st.color}">${st.text}</div></div>
        <div class="detail-cell"><div class="detail-label">来源</div><div class="detail-value">${getSourceEmoji(task.source)} ${escapeHtml(task.source || '--')}</div></div>
        <div class="detail-cell"><div class="detail-label">模型</div><div class="detail-value">${escapeHtml(task.model || '--')}</div></div>
        <div class="detail-cell"><div class="detail-label">持续时间</div><div class="detail-value">${task.duration ? formatDuration(task.duration) : '--'}</div></div>
        <div class="detail-cell"><div class="detail-label">消息数</div><div class="detail-value">${task.message_count || 0}</div></div>
        <div class="detail-cell"><div class="detail-label">工具调用</div><div class="detail-value">${task.tool_call_count || 0}</div></div>
      </div>
      <div style="margin-top:16px;text-align:center;">
        <a href="/sessions" class="link-more">在会话流水线中查看 &rarr;</a>
      </div>
    </div>
  `;
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  document.body.appendChild(modal);
}
