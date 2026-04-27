/**
 * DAG View - SVG-based DAG visualization for task orchestration
 * v0.5.0: Enhanced DAG rendering with SVG edges, node positioning,
 * and interactive features (click, hover, zoom).
 *
 * Usage: Call renderDAGView(tasks, containerId) from tasks.js
 */

const DAG_CONFIG = {
  nodeWidth: 180,
  nodeHeight: 80,
  layerGap: 60,
  nodeGap: 20,
  edgeColor: '#334155',
  edgeHighlight: '#667eea',
  animDuration: '0.3s',
};

function renderDAGView(tasks, containerSelector) {
  const container = document.querySelector(containerSelector);
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
    if (layers.length === 0) layers.push([]);
    layers[0].push(t);
  });

  const totalWidth = Math.max(...layers.map(l => l.length)) * (DAG_CONFIG.nodeWidth + DAG_CONFIG.nodeGap) + DAG_CONFIG.nodeGap;
  const totalHeight = layers.length * (DAG_CONFIG.nodeHeight + DAG_CONFIG.layerGap) + DAG_CONFIG.layerGap;

  const svgWidth = Math.max(totalWidth, container.clientWidth || 800);
  const svgHeight = Math.max(totalHeight, 400);

  const positions = {};
  let svgContent = `<svg width="100%" height="${svgHeight}" viewBox="0 0 ${svgWidth} ${svgHeight}" xmlns="http://www.w3.org/2000/svg">`;

  svgContent += `<defs>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="${DAG_CONFIG.edgeColor}" />
    </marker>
    <marker id="arrowhead-highlight" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="${DAG_CONFIG.edgeHighlight}" />
    </marker>
  </defs>`;

  layers.forEach((layer, layerIdx) => {
    const layerWidth = layer.length * (DAG_CONFIG.nodeWidth + DAG_CONFIG.nodeGap) - DAG_CONFIG.nodeGap;
    const startX = (svgWidth - layerWidth) / 2;
    const y = layerIdx * (DAG_CONFIG.nodeHeight + DAG_CONFIG.layerGap) + DAG_CONFIG.layerGap / 2;

    layer.forEach((task, nodeIdx) => {
      const x = startX + nodeIdx * (DAG_CONFIG.nodeWidth + DAG_CONFIG.nodeGap);
      positions[task.id] = { x, y, cx: x + DAG_CONFIG.nodeWidth / 2, cy: y + DAG_CONFIG.nodeHeight / 2 };

      const sc = getStatusConfig(task.status);
      svgContent += `
        <g class="dag-svg-node" data-task-id="${escapeHtml(task.id)}" onclick="dagNodeClick('${escapeHtml(task.id)}')" style="cursor:pointer;">
          <rect x="${x}" y="${y}" width="${DAG_CONFIG.nodeWidth}" height="${DAG_CONFIG.nodeHeight}"
                rx="8" ry="8" fill="${sc.bg}" stroke="${sc.border}" stroke-width="1.5"
                style="transition: all ${DAG_CONFIG.animDuration};" />
          <circle cx="${x + 12}" cy="${y + 16}" r="4" fill="${sc.border}" />
          <text x="${x + 22}" y="${y + 20}" fill="#e2e8f0" font-size="12" font-weight="500"
                style="pointer-events:none;">${escapeHtml(truncate(task.name, 16))}</text>
          <text x="${x + 12}" y="${y + 38}" fill="#94a3b8" font-size="11"
                style="pointer-events:none;">${getSourceEmoji(task.source)} ${task.source || '--'}</text>
          <text x="${x + 12}" y="${y + 54}" fill="${sc.border}" font-size="11" font-weight="500"
                style="pointer-events:none;">${sc.text}</text>
          ${task.duration ? `<text x="${x + DAG_CONFIG.nodeWidth - 12}" y="${y + 54}" fill="#64748b" font-size="10" text-anchor="end"
                style="pointer-events:none;">${formatDuration(task.duration)}</text>` : ''}
        </g>`;
    });
  });

  Object.entries(childMap).forEach(([parentId, children]) => {
    const parentPos = positions[parentId];
    if (!parentPos) return;

    children.forEach(child => {
      const childPos = positions[child.id];
      if (!childPos) return;

      const x1 = parentPos.cx;
      const y1 = parentPos.y + DAG_CONFIG.nodeHeight;
      const x2 = childPos.cx;
      const y2 = childPos.cy - DAG_CONFIG.nodeHeight / 2;
      const midY = (y1 + y2) / 2;

      svgContent += `
        <path d="M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}"
              fill="none" stroke="${DAG_CONFIG.edgeColor}" stroke-width="1.5"
              marker-end="url(#arrowhead)"
              class="dag-svg-edge" data-from="${escapeHtml(parentId)}" data-to="${escapeHtml(child.id)}"
              style="transition: stroke ${DAG_CONFIG.animDuration};" />`;
    });
  });

  svgContent += '</svg>';

  container.innerHTML = `
    <div style="position:relative;overflow:auto;">
      ${svgContent}
    </div>
  `;

  container.querySelectorAll('.dag-svg-node').forEach(node => {
    node.addEventListener('mouseenter', () => highlightDAGNode(node.dataset.taskId, true));
    node.addEventListener('mouseleave', () => highlightDAGNode(node.dataset.taskId, false));
  });
}

function highlightDAGNode(taskId, highlight) {
  document.querySelectorAll('.dag-svg-edge').forEach(edge => {
    const from = edge.dataset.from;
    const to = edge.dataset.to;
    if (from === taskId || to === taskId) {
      edge.setAttribute('stroke', highlight ? DAG_CONFIG.edgeHighlight : DAG_CONFIG.edgeColor);
      edge.setAttribute('stroke-width', highlight ? '2.5' : '1.5');
      edge.setAttribute('marker-end', highlight ? 'url(#arrowhead-highlight)' : 'url(#arrowhead)');
    }
  });
}

function dagNodeClick(taskId) {
  if (typeof showTaskDetail === 'function') {
    showTaskDetail(taskId);
  }
}

function getStatusConfig(status) {
  const map = {
    running: { bg: '#f59e0b15', border: '#f59e0b', text: '运行中' },
    completed: { bg: '#10b98115', border: '#10b981', text: '已完成' },
    failed: { bg: '#ef444415', border: '#ef4444', text: '失败' },
    pending: { bg: '#64748b15', border: '#64748b', text: '等待中' },
  };
  return map[status] || map.pending;
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
