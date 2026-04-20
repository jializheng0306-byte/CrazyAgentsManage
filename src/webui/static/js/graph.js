document.addEventListener('DOMContentLoaded', () => {
  loadGraphData();
});

async function loadGraphData() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/graph/data');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();

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
    if (container) container.innerHTML = '<div style="padding:24px;text-align:center;color:#ef4444;">加载失败，请刷新重试</div>';
  }
}

function sanitizeColor(val) {
  if (!val) return '#64748b';
  if (/^#[0-9a-fA-F]{6}$/.test(val.trim())) return val.trim();
  if (/^#[0-9a-fA-F]{3}$/.test(val.trim())) return val.trim();
  return '#64748b';
}

function renderGraph(data) {
  const container = document.querySelector('.graph-visualization') || document.querySelector('.graph-container');
  if (!container) return;

  const nodes = data.nodes || [];
  const edges = data.edges || [];

  if (nodes.length === 0) {
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无图谱数据</div>';
    return;
  }

  const centerX = 50;
  const centerY = 50;
  const agentNodes = nodes.filter(n => n.type === 'agent');
  const radius = Math.max(20, Math.min(40, 80 / Math.sqrt(agentNodes.length || 1)));
  const angleStep = (2 * Math.PI) / Math.max(agentNodes.length, 1);

  let svgContent = '<svg viewBox="0 0 100 100" style="width:100%;height:100%;position:absolute;top:0;left:0;">';

  const edgeColorMap = { 'coordinator': '#3b82f6', 'dataflow': '#10b981' };
  const fallbackEdgeColors = ['#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'];
  let fallbackIdx = 0;
  const dynamicEdgeColors = {};

  edges.forEach(edge => {
    if (!dynamicEdgeColors[edge.type]) {
      dynamicEdgeColors[edge.type] = edgeColorMap[edge.type] || fallbackEdgeColors[fallbackIdx++ % fallbackEdgeColors.length];
    }
  });

  edges.forEach(edge => {
    const sourceNode = nodes.find(n => n.id === edge.source);
    const targetNode = nodes.find(n => n.id === edge.target);
    if (!sourceNode || !targetNode) return;

    let sx, sy, tx, ty;
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
    tx = centerX + radius * Math.cos(tAngle);
    ty = centerY + radius * Math.sin(tAngle);

    const edgeColor = dynamicEdgeColors[edge.type] || '#f59e0b';
    svgContent += '<line x1="' + sx + '" y1="' + sy + '" x2="' + tx + '" y2="' + ty + '" stroke="' + edgeColor + '" stroke-width="0.3" stroke-dasharray="1,1" opacity="0.6"/>';
  });

  svgContent += '</svg>';

  let html = '<div style="position:relative;width:100%;padding-top:100%;">' + svgContent;

  const centerNode = nodes.find(n => n.type === 'coordinator');
  if (centerNode) {
    const gradients = (centerNode.gradient || '#64748b,#475569').split(',');
    html += '<div style="position:absolute;left:' + centerX + '%;top:' + centerY + '%;transform:translate(-50%,-50%);z-index:10;">' +
      '<div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,' + sanitizeColor(gradients[0]) + ',' + sanitizeColor(gradients[1] || gradients[0]) + ');display:flex;align-items:center;justify-content:center;font-size:28px;box-shadow:0 0 20px rgba(102,126,234,0.4);cursor:pointer;" title="' + escapeHtml(centerNode.name) + '">' + escapeHtml(centerNode.icon || '') + '</div>' +
      '<div style="text-align:center;margin-top:6px;font-size:11px;color:white;font-weight:600;">' + escapeHtml(centerNode.name) + '</div>' +
      '<div style="text-align:center;font-size:10px;color:#94a3b8;">' + (centerNode.session_count || 0) + ' 会话</div>' +
      '</div>';
  }

  agentNodes.forEach((node, idx) => {
    const angle = -Math.PI / 2 + idx * angleStep;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    const stateColor = node.platform_state === 'connected' ? '#10b981' :
                       node.platform_state === 'error' ? '#ef4444' : '#64748b';

    const gradients = (node.gradient || '#64748b,#475569').split(',');
    html += '<div style="position:absolute;left:' + x + '%;top:' + y + '%;transform:translate(-50%,-50%);z-index:5;">' +
      '<div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,' + sanitizeColor(gradients[0]) + ',' + sanitizeColor(gradients[1] || gradients[0]) + ');display:flex;align-items:center;justify-content:center;font-size:22px;cursor:pointer;position:relative;" title="' + escapeHtml(node.name) + '">' + escapeHtml(node.icon || '') +
      '<div style="position:absolute;bottom:-2px;right:-2px;width:12px;height:12px;border-radius:50%;background:' + stateColor + ';border:2px solid #0f172a;"></div></div>' +
      '<div style="text-align:center;margin-top:4px;font-size:10px;color:white;font-weight:500;">' + escapeHtml(node.name.replace(' 智能体', '')) + '</div>' +
      '<div style="text-align:center;font-size:9px;color:#94a3b8;">' + (node.session_count || 0) + ' 会话</div>' +
      '</div>';
  });

  html += '</div>';
  container.innerHTML = html;
}

function renderNodeTypes(data) {
  const container = document.querySelector('.node-types') || document.querySelector('.legend-nodes');
  if (!container) return;

  const nodes = data.nodes || [];
  container.innerHTML = nodes.map(node =>
    '<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">' +
    '<span style="font-size:16px;">' + escapeHtml(node.icon || '') + '</span>' +
    '<span style="font-size:13px;color:#cbd5e1;">' + escapeHtml(node.name) + '</span>' +
    '<span style="font-size:11px;color:#64748b;margin-left:auto;">' + (node.type === 'coordinator' ? '核心调度' : '平台节点') + '</span>' +
    '</div>'
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
    '<div style="display:flex;align-items:center;gap:8px;padding:6px 0;">' +
    '<div style="width:24px;height:2px;background:' + et.color + ';border-radius:1px;"></div>' +
    '<span style="font-size:13px;color:#cbd5e1;">' + escapeHtml(et.label) + '</span>' +
    '<span style="font-size:11px;color:#64748b;margin-left:auto;">' + escapeHtml(et.desc) + ' (' + et.count + ')</span>' +
    '</div>'
  ).join('');
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
