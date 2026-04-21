document.addEventListener('DOMContentLoaded', () => {
  Promise.all([loadAgentStats(), loadAgentCards()]);
});

let allAgents = [];

async function loadAgentStats() {
  try {
    const resp = await fetch('./api/agents/list');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const agents = await resp.json();
    if (!Array.isArray(agents)) throw new Error('Invalid response');
    allAgents = agents;

    const running = agents.filter(a => a.platform_state === 'connected').length;
    const idle = agents.filter(a => a.platform_state !== 'connected' && a.platform_state !== 'error' && a.platform_state !== 'fatal').length;
    const errorCount = agents.filter(a => a.platform_state === 'error' || a.platform_state === 'fatal').length;

    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = agents.length;
    if (statValues[1]) statValues[1].textContent = running;
    if (statValues[2]) statValues[2].textContent = idle;
    if (statValues[3]) statValues[3].textContent = errorCount;
  } catch (e) {
    console.error('Failed to load agent stats:', e);
    document.querySelectorAll('.stat-value').forEach(el => { if (el) el.textContent = 'N/A'; });
  }
}

async function loadAgentCards(filterSource) {
  try {
    const agents = filterSource ? allAgents.filter(a => a.source === filterSource) : allAgents;
    const container = document.querySelector('.agent-cards') || document.querySelector('.agents-grid');
    if (!container) return;

    if (agents.length === 0) {
      container.innerHTML = '<div class="empty-state">暂无智能体数据</div>';
      return;
    }

    const sources = [...new Set(allAgents.map(a => a.source))];
    const filterHtml = sources.length > 1 ? `
      <div class="filter-bar">
        <button class="btn ${!filterSource ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="loadAgentCards()">全部</button>
        ${sources.map(s => `<button class="btn ${filterSource === s ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="loadAgentCards('${s}')">${getSourceEmoji(s)} ${s}</button>`).join('')}
      </div>
    ` : '';

    container.innerHTML = filterHtml + '<div class="agents-grid-inner">' + agents.map(agent => {
      const gradients = agent.gradient ? agent.gradient.split(',') : ['#64748b', '#475569'];
      if (gradients.length < 2) gradients.push(gradients[0]);
      const sc = agent.platform_state === 'connected' ? 'active' :
                 agent.platform_state === 'error' || agent.platform_state === 'fatal' ? 'error' :
                 agent.session_count > 0 ? 'running' : 'idle';
      const st = sc === 'active' ? '在线' : sc === 'error' ? '异常' : sc === 'running' ? '活跃' : '空闲';
      const successColor = agent.success_rate != null && agent.success_rate < 80 ? '#f59e0b' : '#10b981';

      return `<div class="card agent-card" onclick="showAgentDetail('${escapeHtml(agent.source)}')">
        <div class="agent-card-gradient-bar" style="background:linear-gradient(90deg,${sanitizeColor(gradients[0])},${sanitizeColor(gradients[1])});"></div>
        <div class="agent-card-header">
          <span class="agent-card-icon">${escapeHtml(agent.icon || '')}</span>
          <div style="flex:1;">
            <h3 class="agent-card-name">${escapeHtml(agent.name)}</h3>
            <span class="status-badge status-badge-${sc}">${st}</span>
          </div>
        </div>
        <p class="agent-card-desc">${escapeHtml(agent.description || '')}</p>
        <div class="agent-card-stats">
          <div class="agent-stat-cell"><div class="agent-stat-label">会话数</div><div class="agent-stat-value">${(agent.session_count || 0).toLocaleString()}</div></div>
          <div class="agent-stat-cell"><div class="agent-stat-label">成功率</div><div class="agent-stat-value" style="color:${successColor}">${agent.success_rate != null ? agent.success_rate + '%' : '--'}</div></div>
          <div class="agent-stat-cell"><div class="agent-stat-label">Token 消耗</div><div class="agent-stat-value-sm detail-value-warning">${formatTokenCount(agent.total_tokens || 0)}</div></div>
          <div class="agent-stat-cell"><div class="agent-stat-label">工具调用</div><div class="agent-stat-value-sm detail-value-info">${(agent.total_tool_calls || 0).toLocaleString()}</div></div>
        </div>
      </div>`;
    }).join('') + '</div>';
  } catch (e) {
    console.error('Failed to load agent cards:', e);
    const container = document.querySelector('.agent-cards') || document.querySelector('.agents-grid');
    if (container) container.innerHTML = '<div class="error-state">加载失败，请刷新重试</div>';
  }
}

function showAgentDetail(source) {
  const agent = allAgents.find(a => a.source === source);
  if (!agent) return;

  const existing = document.getElementById('agentDetailModal');
  if (existing) existing.remove();

  const sc = agent.platform_state === 'connected' ? 'active' :
             agent.platform_state === 'error' || agent.platform_state === 'fatal' ? 'error' : 'idle';
  const st = sc === 'active' ? '在线' : sc === 'error' ? '异常' : '空闲';
  const successColor = agent.success_rate != null && agent.success_rate < 80 ? '#f59e0b' : '#10b981';

  const modal = document.createElement('div');
  modal.id = 'agentDetailModal';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="modal-close" onclick="document.getElementById('agentDetailModal').remove()">&times;</button>
      <div class="modal-header">
        <span class="modal-icon">${escapeHtml(agent.icon || '')}</span>
        <div>
          <h2 class="modal-title">${escapeHtml(agent.name)}</h2>
          <span class="status-badge status-badge-${sc}">${st}</span>
        </div>
      </div>
      <p class="agent-card-desc" style="margin-bottom:20px;">${escapeHtml(agent.description || '')}</p>
      <div class="detail-grid">
        <div class="detail-cell"><div class="detail-label">来源</div><div class="detail-value">${getSourceEmoji(agent.source)} ${escapeHtml(agent.source)}</div></div>
        <div class="detail-cell"><div class="detail-label">会话数</div><div class="detail-value">${(agent.session_count || 0).toLocaleString()}</div></div>
        <div class="detail-cell"><div class="detail-label">Token 消耗</div><div class="detail-value-warning">${formatTokenCount(agent.total_tokens || 0)}</div></div>
        <div class="detail-cell"><div class="detail-label">成功率</div><div class="detail-value" style="color:${successColor}">${agent.success_rate != null ? agent.success_rate + '%' : '--'}</div></div>
        <div class="detail-cell"><div class="detail-label">消息总数</div><div class="detail-value">${(agent.total_messages || 0).toLocaleString()}</div></div>
        <div class="detail-cell"><div class="detail-label">工具调用</div><div class="detail-value-info">${(agent.total_tool_calls || 0).toLocaleString()}</div></div>
        <div class="detail-cell-span2"><div class="detail-label">总费用</div><div class="detail-value-success">$${(agent.total_cost || 0).toFixed(4)}</div></div>
      </div>
      <div style="margin-top:16px;text-align:center;">
        <a href="/sessions?source=${encodeURIComponent(agent.source)}" class="link-more">查看该智能体的所有会话 &rarr;</a>
      </div>
    </div>
  `;
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  document.body.appendChild(modal);
}
