document.addEventListener('DOMContentLoaded', () => {
  loadGraphData();
});

let graphData = null;

async function loadGraphData() {
  try {
    const resp = await fetch('/api/graph/data');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    graphData = data;

    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = data.stats?.agent_nodes || 0;
    if (statValues[1]) statValues[1].textContent = data.stats?.connections || 0;
    if (statValues[2]) statValues[2].textContent = data.stats?.total_sessions || 0;

    renderGraph(data);
    renderNodeTypes(data);
    renderEdgeTypes(data);
  } catch (e) {
    console.error('Failed to load graph data:', e);
    const container = document.querySelector('.graph-visualization') || document.querySelector('.graph-container');
    if (container) container.innerHTML = '<div class="error-state">加载失败，请刷新重试</div>';
  }
}

function renderGraph(data) {
  const container = document.querySelector('.graph-visualization') || document.querySelector('.graph-container');
  if (!container) return;

  const nodes = data.nodes || [];
  const edges = data.edges || [];

  if (nodes.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无图谱数据</div>';
    return;
  }

  const centerX = 50;
  const centerY = 50;
  const agentNodes = nodes.filter(n => n.type === 'agent');
  const radius = Math.max(20, Math.min(40, 80 / Math.sqrt(agentNodes.length || 1)));
  const angleStep = (2 * Math.PI) / Math.max(agentNodes.length, 1);

  const edgeColorMap = { 'coordinator': '#3b82f6', 'dataflow': '#10b981' };
  const fallbackEdgeColors = ['#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'];
  let fallbackIdx = 0;
  const dynamicEdgeColors = {};

  edges.forEach(edge => {
    if (!dynamicEdgeColors[edge.type]) {
      dynamicEdgeColors[edge.type] = edgeColorMap[edge.type] || fallbackEdgeColors[fallbackIdx++ % fallbackEdgeColors.length];
    }
  });

  let svgContent = '<svg viewBox="0 0 100 100" style="width:100%;height:100%;position:absolute;top:0;left:0;">';
  edges.forEach(edge => {
    const sourceNode = nodes.find(n => n.id === edge.source);
    const targetNode = nodes.find(n => n.id === edge.target);
    if (!sourceNode || !targetNode) return;

    let sx, sy;
    if (sourceNode.type === 'coordinator') {
      sx = centerX; sy = centerY;
    } else {
      const sIdx = agentNodes.findIndex(n => n.id === sourceNode.id);
      const sAngle = -Math.PI / 2 + sIdx * angleStep;
      sx = centerX + radius * Math.cos(sAngle);
      sy = centerY + radius * Math.sin(sAngle);
    }

    const tIdx = agentNodes.findIndex(n => n.id === targetNode.id);
    const tAngle = -Math.PI / 2 + tIdx * angleStep;
    const tx = centerX + radius * Math.cos(tAngle);
    const ty = centerY + radius * Math.sin(tAngle);

    const edgeColor = dynamicEdgeColors[edge.type] || '#f59e0b';
    svgContent += `<line x1="${sx}" y1="${sy}" x2="${tx}" y2="${ty}" stroke="${edgeColor}" stroke-width="0.3" stroke-dasharray="1,1" opacity="0.6"/>`;
  });
  svgContent += '</svg>';

  let html = `<div style="position:relative;width:100%;padding-top:100%;">${svgContent}`;

  const centerNode = nodes.find(n => n.type === 'coordinator');
  if (centerNode) {
    const gradients = (centerNode.gradient || '#64748b,#475569').split(',');
    html += `<div class="graph-node-wrapper graph-node-center" style="left:${centerX}%;top:${centerY}%;">
      <div class="graph-node-circle" style="width:80px;height:80px;background:linear-gradient(135deg,${sanitizeColor(gradients[0])},${sanitizeColor(gradients[1] || gradients[0])});font-size:28px;box-shadow:0 0 20px rgba(102,126,234,0.4);" title="${escapeHtml(centerNode.name)}" onclick="showNodeDetail('coordinator')">${escapeHtml(centerNode.icon || '')}</div>
      <div class="graph-node-label">${escapeHtml(centerNode.name)}</div>
      <div class="graph-node-sublabel">${centerNode.session_count || 0} 会话</div>
    </div>`;
  }

  agentNodes.forEach((node, idx) => {
    const angle = -Math.PI / 2 + idx * angleStep;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    const stateColor = node.platform_state === 'connected' ? '#10b981' :
                       node.platform_state === 'error' ? '#ef4444' : '#64748b';
    const gradients = (node.gradient || '#64748b,#475569').split(',');

    html += `<div class="graph-node-wrapper" style="left:${x}%;top:${y}%;">
      <div class="graph-node-circle" style="width:56px;height:56px;background:linear-gradient(135deg,${sanitizeColor(gradients[0])},${sanitizeColor(gradients[1] || gradients[0])});font-size:22px;" title="${escapeHtml(node.name)}" onclick="showNodeDetail('${escapeHtml(node.id)}')">${escapeHtml(node.icon || '')}
        <div class="graph-node-status-dot" style="background:${stateColor};"></div>
      </div>
      <div class="graph-node-label">${escapeHtml(node.name.replace(' 智能体', ''))}</div>
      <div class="graph-node-sublabel">${node.session_count || 0} 会话</div>
    </div>`;
  });

  html += '</div>';
  container.innerHTML = html;
}

function showNodeDetail(nodeId) {
  if (!graphData) return;
  const node = graphData.nodes.find(n => n.id === nodeId);
  if (!node) return;

  const existing = document.getElementById('nodeDetailModal');
  if (existing) existing.remove();

  const nodeEdges = graphData.edges.filter(e => e.source === nodeId || e.target === nodeId);
  const connectedTo = nodeEdges.map(e => {
    const otherId = e.source === nodeId ? e.target : e.source;
    const otherNode = graphData.nodes.find(n => n.id === otherId);
    return otherNode ? (otherNode.icon || '') + ' ' + otherNode.name : otherId;
  });

  const stateColor = node.platform_state === 'connected' ? '#10b981' :
                     node.platform_state === 'error' ? '#ef4444' : '#64748b';
  const stateText = node.platform_state === 'connected' ? '已连接' :
                    node.platform_state === 'error' ? '异常' : '未知';

  const modal = document.createElement('div');
  modal.id = 'nodeDetailModal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="modal-close" onclick="document.getElementById('nodeDetailModal').remove()">&times;</button>
      <div class="modal-header">
        <span class="modal-icon">${escapeHtml(node.icon || '')}</span>
        <div>
          <h2 class="modal-title">${escapeHtml(node.name)}</h2>
          <span class="status-badge" style="background:${stateColor}22;color:${stateColor};">${stateText}</span>
          <span class="status-badge status-badge-idle" style="margin-left:4px;">${node.type === 'coordinator' ? '核心调度' : '平台节点'}</span>
        </div>
      </div>
      <div class="detail-grid" style="margin-bottom:16px;">
        <div class="detail-cell"><div class="detail-label">会话数</div><div class="detail-value-lg">${node.session_count || 0}</div></div>
        <div class="detail-cell"><div class="detail-label">连接数</div><div class="detail-value-lg">${nodeEdges.length}</div></div>
      </div>
      ${connectedTo.length > 0 ? `
        <div style="margin-bottom:12px;">
          <div class="detail-label" style="margin-bottom:8px;">关联节点</div>
          ${connectedTo.map(c => `<div style="font-size:13px;color:#cbd5e1;padding:4px 0;">${c}</div>`).join('')}
        </div>
      ` : ''}
      ${node.type === 'agent' ? `
        <div style="text-align:center;">
          <a href="/agent" class="link-more">查看智能体详情 &rarr;</a>
        </div>
      ` : ''}
    </div>
  `;
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  document.body.appendChild(modal);
}

function renderNodeTypes(data) {
  const container = document.querySelector('.node-types') || document.querySelector('.legend-nodes');
  if (!container) return;

  const nodes = data.nodes || [];
  container.innerHTML = nodes.map(node =>
    `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">
      <span style="font-size:16px;">${escapeHtml(node.icon || '')}</span>
      <span style="font-size:13px;color:#cbd5e1;">${escapeHtml(node.name)}</span>
      <span style="font-size:11px;color:#64748b;margin-left:auto;">${node.type === 'coordinator' ? '核心调度' : '平台节点'}</span>
    </div>`
  ).join('');
}

function renderEdgeTypes(data) {
  const container = document.querySelector('.edge-types') || document.querySelector('.legend-edges');
  if (!container) return;

  const edges = data.edges || [];
  const edgeTypeMap = {};
  const defaultEdgeMeta = {
    'coordinator': { label: '协调关系', desc: 'Gateway -> Agent' },
    'dataflow': { label: '数据流', desc: 'Agent -> Agent' },
  };
  const edgeColorMap = { 'coordinator': '#3b82f6', 'dataflow': '#10b981' };
  const fallbackColors = ['#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#f97316'];

  edges.forEach(edge => {
    if (!edgeTypeMap[edge.type]) {
      const meta = defaultEdgeMeta[edge.type] || { label: edge.type, desc: edge.label || '' };
      const color = edgeColorMap[edge.type] || fallbackColors[Object.keys(edgeTypeMap).length % fallbackColors.length];
      edgeTypeMap[edge.type] = { ...meta, color, count: 0 };
    }
    edgeTypeMap[edge.type].count++;
  });

  const edgeTypes = Object.values(edgeTypeMap);
  container.innerHTML = edgeTypes.map(et =>
    `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">
      <div style="width:24px;height:2px;background:${et.color};border-radius:1px;"></div>
      <span style="font-size:13px;color:#cbd5e1;">${escapeHtml(et.label)}</span>
      <span style="font-size:11px;color:#64748b;margin-left:auto;">${escapeHtml(et.desc)} (${et.count})</span>
    </div>`
  ).join('');
}
