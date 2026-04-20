document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
});

async function loadTasks() {
  try {
    const resp = await fetch('/api/tasks/list');
    const data = await resp.json();

    const stats = data.stats || {};
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = stats.total || 0;
    if (statValues[1]) statValues[1].textContent = stats.running || 0;
    if (statValues[2]) statValues[2].textContent = stats.completed || 0;
    if (statValues[3]) statValues[3].textContent = stats.failed || 0;

    renderDAG(data.tasks || []);
    renderTaskList(data.tasks || []);
  } catch (e) {
    console.error('Failed to load tasks:', e);
  }
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
        <div style="background: ${sc.bg}; border: 1px solid ${sc.border}33; border-radius: 10px; padding: 14px; min-width: 160px; max-width: 220px; position: relative;">
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
      <div style="display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid #1f2937; gap: 16px;">
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

function getSourceEmoji(source) {
  if (typeof window.getSourceEmoji === 'function') return window.getSourceEmoji(source);
  const map = { cli: '🖥️', cron: '⏰', telegram: '📱', discord: '💬', feishu: '🐦', slack: '💼', api_server: '🔌', acp: '📝' };
  return map[source] || '📡';
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0s';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return s > 0 ? `${m}m ${s}s` : `${m}m`;
  }
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
