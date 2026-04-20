/**
 * Tokens JavaScript - Token消耗管理
 * 数据源: /api/tokens/* (读取 state.db SQL聚合)
 */

document.addEventListener('DOMContentLoaded', () => {
  loadTokenStats();
  loadProviderBreakdown();
  loadAgentBreakdown();
  loadRecentUsage();
});

async function loadTokenStats() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/tokens/stats');
    const data = await resp.json();

    const statValues = document.querySelectorAll('.stat-value');
    const budgetUsd = data.budget_usd || null;
    const activeDays = data.active_days || 1;
    const budgetPct = budgetUsd ? Math.round(((data.total_cost_usd || 0) / budgetUsd) * 100) : null;
    const dailyAvg = (data.total_input_tokens + data.total_output_tokens) / activeDays;

    const mappings = [
      formatTokenCount(data.total_input_tokens + data.total_output_tokens),
      '$' + (data.total_cost_usd || 0).toFixed(2),
      budgetPct != null ? budgetPct + '%' : '--',
      formatTokenCount(Math.round(dailyAvg)),
    ];
    mappings.forEach((v, i) => { if (statValues[i]) statValues[i].textContent = v; });
  } catch (e) {
    console.error('Failed to load token stats:', e);
  }
}

async function loadProviderBreakdown() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/tokens/stats');
    const data = await resp.json();
    const providers = data.by_provider || {};
    const container = document.getElementById('providerDistribution') || document.querySelector('.provider-breakdown');
    if (!container) return;

    const entries = Object.entries(providers);
    if (entries.length === 0) {
      container.innerHTML = '<div style="padding: 16px; text-align: center; color: #64748b;">暂无数据</div>';
      return;
    }

    const totalTokens = entries.reduce((sum, [, v]) => sum + v.input_tokens + v.output_tokens, 0);

    container.innerHTML = entries.map(([name, v]) => {
      const pct = totalTokens > 0 ? Math.round(((v.input_tokens + v.output_tokens) / totalTokens) * 100) : 0;
      return `
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 14px; color: white;">${escapeHtml(name)}</span>
            <span style="font-size: 14px; color: #94a3b8;">${formatTokenCount(v.input_tokens + v.output_tokens)} tokens ($${(v.cost_usd || 0).toFixed(2)})</span>
          </div>
          <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: #10a37f; border-radius: 4px;"></div>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Failed to load provider breakdown:', e);
  }
}

async function loadAgentBreakdown() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/tokens/stats');
    const data = await resp.json();
    const sources = data.by_source || {};
    const container = document.getElementById('sourceDistribution') || document.querySelector('.agent-breakdown');
    if (!container) return;

    const entries = Object.entries(sources);
    if (entries.length === 0) {
      container.innerHTML = '<div style="padding: 16px; text-align: center; color: #64748b;">暂无数据</div>';
      return;
    }

    const totalTokens = entries.reduce((sum, [, v]) => sum + v.input_tokens + v.output_tokens, 0);
    const colors = ['#10b981', '#f59e0b', '#06b6d4', '#667eea', '#ec4899', '#8b5cf6'];

    container.innerHTML = entries.map(([name, v], i) => {
      const pct = totalTokens > 0 ? Math.round(((v.input_tokens + v.output_tokens) / totalTokens) * 100) : 0;
      return `
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 14px; color: white;">${escapeHtml(name)}</span>
            <span style="font-size: 14px; color: #94a3b8;">${formatTokenCount(v.input_tokens + v.output_tokens)} tokens</span>
          </div>
          <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: ${colors[i % colors.length]}; border-radius: 4px;"></div>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Failed to load agent breakdown:', e);
  }
}

async function loadRecentUsage() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/tokens/recent?limit=10');
    const data = await resp.json();

    const container = document.getElementById('recentUsage') || document.querySelector('.recent-usage-tbody');
    if (!container) return;

    if (data.length === 0) {
      container.innerHTML = '<div style="padding: 16px; text-align: center; color: #64748b;">暂无消耗记录</div>';
      return;
    }

    container.innerHTML = `
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="border-bottom: 1px solid #334155;">
            <th style="padding: 10px; font-size: 12px; color: #64748b; text-align: left;">时间</th>
            <th style="padding: 10px; font-size: 12px; color: #64748b; text-align: left;">来源</th>
            <th style="padding: 10px; font-size: 12px; color: #64748b; text-align: left;">会话</th>
            <th style="padding: 10px; font-size: 12px; color: #64748b; text-align: right;">Token</th>
            <th style="padding: 10px; font-size: 12px; color: #64748b; text-align: right;">费用</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(r => `
            <tr style="border-bottom: 1px solid #1f2937;">
              <td style="padding: 10px; font-size: 13px; color: #cbd5e1;">${formatTime(r.started_at)}</td>
              <td style="padding: 10px; font-size: 13px; color: #cbd5e1;">${escapeHtml(r.source)}</td>
              <td style="padding: 10px; font-size: 13px; color: #cbd5e1; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(r.title)}</td>
              <td style="padding: 10px; font-size: 13px; color: white; text-align: right; font-weight: 500;">${formatTokenCount(r.input_tokens + r.output_tokens)}</td>
              <td style="padding: 10px; font-size: 13px; color: #10b981; text-align: right; font-weight: 500;">$${(r.cost_usd || 0).toFixed(4)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    console.error('Failed to load recent usage:', e);
  }
}

function formatTokenCount(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function formatTime(timestamp) {
  if (!timestamp) return '--';
  const d = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);
  if (isNaN(d.getTime())) return '--';
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
