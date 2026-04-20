document.addEventListener('DOMContentLoaded', () => {
  Promise.all([loadAgentStats(), loadAgentCards()]);
});

async function loadAgentStats() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/agents/list');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const agents = await resp.json();
    if (!Array.isArray(agents)) throw new Error('Invalid response');

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

async function loadAgentCards() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/agents/list');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const agents = await resp.json();
    if (!Array.isArray(agents)) throw new Error('Invalid response');

    const container = document.querySelector('.agent-cards') || document.querySelector('.agents-grid');
    if (!container) return;

    if (agents.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无智能体数据</div>';
      return;
    }

    container.innerHTML = agents.map(agent => {
      const gradients = agent.gradient ? agent.gradient.split(',') : ['#64748b', '#475569'];
      if (gradients.length < 2) gradients.push(gradients[0]);
      const statusClass = agent.platform_state === 'connected' ? 'active' :
                          agent.platform_state === 'error' || agent.platform_state === 'fatal' ? 'error' :
                          agent.session_count > 0 ? 'executing' : 'idle';
      const statusText = statusClass === 'active' ? '在线' :
                         statusClass === 'error' ? '异常' :
                         statusClass === 'executing' ? '活跃' : '空闲';

      return '<div class="card agent-card" style="padding:var(--spacing-lg);position:relative;overflow:hidden;">' +
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
    }).join('');
  } catch (e) {
    console.error('Failed to load agent cards:', e);
    const container = document.querySelector('.agent-cards') || document.querySelector('.agents-grid');
    if (container) container.innerHTML = '<div style="padding:24px;text-align:center;color:#ef4444;">加载失败，请刷新重试</div>';
  }
}

function sanitizeColor(val) {
  if (!val) return '#64748b';
  if (/^#[0-9a-fA-F]{6}$/.test(val.trim())) return val.trim();
  if (/^#[0-9a-fA-F]{3}$/.test(val.trim())) return val.trim();
  return '#64748b';
}

function formatTokenCount(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
