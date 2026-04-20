document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
});

let allTasks = [];
let currentStatusFilter = 'all';

async function loadTasks() {
  try {
    const resp = await fetch('/api/tasks/list');
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
  filterBar.className = 'task-filter-bar';
  filterBar.style.cssText = 'display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;';
  filterBar.innerHTML = ['all', 'running', 'completed', 'failed'].map(s => {
    const labels = { all: '全部', running: '运行中', completed: '已完成', failed: '失败' };
    const colors = { all: '#667eea', running: '#f59e0b', completed: '#10b981', failed: '#ef4444' };
    return `<button class="btn ${currentStatusFilter === s ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="filterTasks('${s}')" style="${currentStatusFilter === s ? 'background:' + colors[s] + ';border-color:' + colors[s] : ''}">${labels[s]} (${counts[s]})</button>`;
  }).join('');

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
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无任务数据</div>';
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

  let html = '<div style="overflow-x: auto; padding: 16px;">';

  layers.forEach((layer, layerIdx) => {
    html += `<div style="display: flex; gap: 16px; justify-content: center; margin-bottom: ${layerIdx < layers.length - 1 ? '32px' : '0'}; position: relative;">`;

    layer.forEach(task => {
      const statusColors = {
        running: { bg: '#f59e0b22', border: '#f59e0b', text: '运行中' },
        completed: { bg: '#10b98122', border: '#10b981', text: '已完成' },
        failed: { bg: '#ef444422', border: '#ef4444', text: '失败' },
        pending: { bg: '#64748b22', border: '#64748b', text: '等待中' },
      };
      const sc = statusColors[task.status] || statusColors.pending;

      html += `
        <div style="background: ${sc.bg}; border: 1px solid ${sc.border}33; border-radius: 10px; padding: 14px; min-width: 160px; max-width: 220px; position: relative; cursor: pointer;" onclick="showTaskDetail('${escapeHtml(task.id)}')">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: ${sc.border};"></div>
            <span style="font-size: 13px; font-weight: 600; color: white;">${escapeHtml(task.name)}</span>
          </div>
          <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">
            ${getSourceEmoji(task.source)} ${task.source || '--'}
          </div>
          <div style="font-size: 11px; color: ${sc.border};">${sc.text}</div>
          ${task.duration ? `<div style="font-size: 10px; color: #64748b; margin-top: 4px;">${formatDuration(task.duration)}</div>` : ''}
        </div>
      `;
    });

    html += '</div>';

    if (layerIdx < layers.length - 1) {
      html += `<div style="text-align: center; margin: -16px 0 16px; color: #64748b; font-size: 18px;">↓</div>`;
    }
  });

  html += '</div>';
  container.innerHTML = html;
}

function renderTaskList(tasks) {
  const container = document.querySelector('.task-list') || document.querySelector('.tasks-table-body');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无任务记录</div>';
    return;
  }

  container.innerHTML = tasks.slice(0, 20).map(task => {
    const statusMap = {
      running: { color: '#f59e0b', text: '运行中' },
      completed: { color: '#10b981', text: '已完成' },
      failed: { color: '#ef4444', text: '失败' },
      pending: { color: '#64748b', text: '等待中' },
    };
    const st = statusMap[task.status] || statusMap.pending;

    return `
      <div style="display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid #1f2937; gap: 16px; cursor: pointer;" onclick="showTaskDetail('${escapeHtml(task.id)}')">
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 14px; color: white; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(task.name)}</div>
          <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">${getSourceEmoji(task.source)} ${task.source || '--'} · ${task.model || '--'}</div>
        </div>
        <span style="font-size: 12px; color: ${st.color}; padding: 2px 8px; background: ${st.color}15; border-radius: 4px;">${st.text}</span>
        <span style="font-size: 12px; color: #64748b; min-width: 60px; text-align: right;">${task.duration ? formatDuration(task.duration) : '--'}</span>
      </div>
    `;
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
  modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:1000;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;max-width:500px;width:90%;position:relative;">
      <button onclick="document.getElementById('taskDetailModal').remove()" style="position:absolute;top:12px;right:12px;background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;">&times;</button>
      <h2 style="font-size:18px;font-weight:600;color:white;margin:0 0 16px;">${escapeHtml(task.name)}</h2>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">状态</div>
          <div style="font-size:14px;color:${st.color};font-weight:500;">${st.text}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">来源</div>
          <div style="font-size:14px;color:white;font-weight:500;">${getSourceEmoji(task.source)} ${escapeHtml(task.source || '--')}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">模型</div>
          <div style="font-size:14px;color:white;font-weight:500;">${escapeHtml(task.model || '--')}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">持续时间</div>
          <div style="font-size:14px;color:white;font-weight:500;">${task.duration ? formatDuration(task.duration) : '--'}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">消息数</div>
          <div style="font-size:14px;color:white;font-weight:500;">${task.message_count || 0}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">工具调用</div>
          <div style="font-size:14px;color:white;font-weight:500;">${task.tool_call_count || 0}</div>
        </div>
      </div>
      <div style="margin-top:16px;text-align:center;">
        <a href="/sessions" style="color:#667eea;font-size:13px;text-decoration:none;">在会话流水线中查看 →</a>
      </div>
    </div>
  `;
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  document.body.appendChild(modal);
}
