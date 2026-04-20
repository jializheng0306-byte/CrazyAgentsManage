document.addEventListener('DOMContentLoaded', () => {
  Promise.all([loadAgentStats(), loadAgentCards()]);
});

let allAgents = [];

async function loadAgentStats() {
  try {
    const resp = await fetch('/api/agents/list');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const agents = await resp.json();
    if (!Array.isArray(agents)) throw new Error('Invalid response');
    allAgents = agents;

    const totalAgents = agents.length;
    const running = agents.filter(a => a.platform_state === 'connected').length;
    const idle = agents.filter(a => a.platform_state !== 'connected' && a.platform_state !== 'error' && a.platform_state !== 'fatal').length;
    const errorCount = agents.filter(a => a.platform_state === 'error' || a.platform_state === 'fatal').length;

    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = totalAgents;
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
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无智能体数据</div>';
      return;
    }

    const sources = [...new Set(allAgents.map(a => a.source))];
    const filterHtml = sources.length > 1 ? `
      <div style="margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap;">
        <button class="btn ${!filterSource ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="loadAgentCards()">全部</button>
        ${sources.map(s => `<button class="btn ${filterSource === s ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="loadAgentCards('${s}')">${getSourceEmoji(s)} ${s}</button>`).join('')}
      </div>
    ` : '';

    container.innerHTML = filterHtml + '<div class="agents-grid-inner">' + agents.map(agent => {
      const gradients = agent.gradient ? agent.gradient.split(',') : ['#64748b', '#475569'];
      if (gradients.length < 2) gradients.push(gradients[0]);
      const statusClass = agent.platform_state === 'connected' ? 'active' :
                          agent.platform_state === 'error' || agent.platform_state === 'fatal' ? 'error' :
                          agent.session_count > 0 ? 'executing' : 'idle';
      const statusText = statusClass === 'active' ? '在线' :
                         statusClass === 'error' ? '异常' :
                         statusClass === 'executing' ? '活跃' : '空闲';

      return '<div class="card agent-card" style="padding:var(--spacing-lg);position:relative;overflow:hidden;cursor:pointer;" onclick="showAgentDetail(\'' + escapeHtml(agent.source) + '\')">' +
        '<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,' + sanitizeColor(gradients[0]) + ',' + sanitizeColor(gradients[1]) + ');"></div>' +
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">' +
        '<span style="font-size:32px;">' + escapeHtml(agent.icon || '') + '</span>' +
        '<div style="flex:1;">' +
        '<h3 style="font-size:16px;font-weight:600;color:white;margin:0;">' + escapeHtml(agent.name) + '</h3>' +
        '<span style="font-size:12px;padding:2px 8px;border-radius:4px;background:' + (statusClass === 'active' ? '#10b98122' : statusClass === 'error' ? '#ef444422' : '#64748b22') + ';color:' + (statusClass === 'active' ? '#10b981' : statusClass === 'error' ? '#ef4444' : '#94a3b8') + ';">' + statusText + '</span>' +
        '</div></div>' +
        '<p style="font-size:13px;color:#94a3b8;margin-bottom:16px;line-height:1.5;">' + escapeHtml(agent.description || '') + '</p>' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">' +
        '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px;">' +
        '<div style="font-size:11px;color:#64748b;margin-bottom:4px;">会话数</div>' +
        '<div style="font-size:18px;font-weight:600;color:white;">' + (agent.session_count || 0).toLocaleString() + '</div></div>' +
        '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px;">' +
        '<div style="font-size:11px;color:#64748b;margin-bottom:4px;">成功率</div>' +
        '<div style="font-size:18px;font-weight:600;color:' + (agent.success_rate != null && agent.success_rate < 80 ? '#f59e0b' : '#10b981') + ';">' + (agent.success_rate != null ? agent.success_rate + '%' : '--') + '</div></div>' +
        '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px;">' +
        '<div style="font-size:11px;color:#64748b;margin-bottom:4px;">Token 消耗</div>' +
        '<div style="font-size:14px;font-weight:500;color:#f59e0b;">' + formatTokenCount(agent.total_tokens || 0) + '</div></div>' +
        '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:10px;">' +
        '<div style="font-size:11px;color:#64748b;margin-bottom:4px;">工具调用</div>' +
        '<div style="font-size:14px;font-weight:500;color:#06b6d4;">' + (agent.total_tool_calls || 0).toLocaleString() + '</div></div>' +
        '</div></div>';
    }).join('') + '</div>';
  } catch (e) {
    console.error('Failed to load agent cards:', e);
    const container = document.querySelector('.agent-cards') || document.querySelector('.agents-grid');
    if (container) container.innerHTML = '<div style="padding:24px;text-align:center;color:#ef4444;">加载失败，请刷新重试</div>';
  }
}

function showAgentDetail(source) {
  const agent = allAgents.find(a => a.source === source);
  if (!agent) return;

  const existing = document.getElementById('agentDetailModal');
  if (existing) existing.remove();

  const gradients = agent.gradient ? agent.gradient.split(',') : ['#64748b', '#475569'];
  if (gradients.length < 2) gradients.push(gradients[0]);
  const statusClass = agent.platform_state === 'connected' ? 'active' :
                      agent.platform_state === 'error' || agent.platform_state === 'fatal' ? 'error' : 'idle';
  const statusText = statusClass === 'active' ? '在线' : statusClass === 'error' ? '异常' : '空闲';

  const modal = document.createElement('div');
  modal.id = 'agentDetailModal';
  modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:1000;display:flex;align-items:center;justify-content:center;';
  modal.innerHTML = `
    <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;max-width:500px;width:90%;position:relative;">
      <button onclick="document.getElementById('agentDetailModal').remove()" style="position:absolute;top:12px;right:12px;background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;">&times;</button>
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <span style="font-size:48px;">${escapeHtml(agent.icon || '')}</span>
        <div>
          <h2 style="font-size:20px;font-weight:600;color:white;margin:0 0 4px;">${escapeHtml(agent.name)}</h2>
          <span style="font-size:13px;padding:4px 10px;border-radius:4px;background:${statusClass === 'active' ? '#10b98122' : statusClass === 'error' ? '#ef444422' : '#64748b22'};color:${statusClass === 'active' ? '#10b981' : statusClass === 'error' ? '#ef4444' : '#94a3b8'};">${statusText}</span>
        </div>
      </div>
      <p style="font-size:14px;color:#94a3b8;line-height:1.6;margin-bottom:20px;">${escapeHtml(agent.description || '')}</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">来源</div>
          <div style="font-size:14px;font-weight:500;color:white;">${getSourceEmoji(agent.source)} ${escapeHtml(agent.source)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">会话数</div>
          <div style="font-size:14px;font-weight:500;color:white;">${(agent.session_count || 0).toLocaleString()}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">Token 消耗</div>
          <div style="font-size:14px;font-weight:500;color:#f59e0b;">${formatTokenCount(agent.total_tokens || 0)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">成功率</div>
          <div style="font-size:14px;font-weight:500;color:${agent.success_rate != null && agent.success_rate < 80 ? '#f59e0b' : '#10b981'};">${agent.success_rate != null ? agent.success_rate + '%' : '--'}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">消息总数</div>
          <div style="font-size:14px;font-weight:500;color:white;">${(agent.total_messages || 0).toLocaleString()}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">工具调用</div>
          <div style="font-size:14px;font-weight:500;color:#06b6d4;">${(agent.total_tool_calls || 0).toLocaleString()}</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:12px;grid-column:span 2;">
          <div style="font-size:11px;color:#64748b;margin-bottom:4px;">总费用</div>
          <div style="font-size:14px;font-weight:500;color:#10b981;">$${(agent.total_cost || 0).toFixed(4)}</div>
        </div>
      </div>
      <div style="margin-top:16px;text-align:center;">
        <a href="/sessions?source=${encodeURIComponent(agent.source)}" style="color:#667eea;font-size:13px;text-decoration:none;">查看该智能体的所有会话 →</a>
      </div>
    </div>
  `;
  modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
  document.body.appendChild(modal);
}
