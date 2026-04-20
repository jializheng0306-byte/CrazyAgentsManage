/**
 * Alerts JavaScript - 系统告警中心
 * 数据源: /api/alerts/* (读取 gateway_state.json)
 */

let alertRefreshInterval = null;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
  loadAlerts();
  loadPlatformStatus();
  alertRefreshInterval = setInterval(() => {
    loadAlerts();
    loadPlatformStatus();
  }, 10000);
});

async function loadAlerts() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/alerts/list');
    const alerts = await resp.json();

    let criticalCount = alerts.filter(a => a.level === 'critical').length;
    let warningCount = alerts.filter(a => a.level === 'warning').length;
    let infoCount = alerts.filter(a => a.level === 'info').length;

    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = criticalCount || '--';
    if (statValues[1]) statValues[1].textContent = warningCount || '--';
    if (statValues[2]) statValues[2].textContent = infoCount || '--';

    const container = document.getElementById('alertsListContainer');
    if (!container) return;

    let filtered = alerts;
    if (currentFilter !== 'all') {
      filtered = alerts.filter(a => a.level === currentFilter);
    }

    if (filtered.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">✅ 暂无' + (currentFilter === 'all' ? '' : currentFilter + '级别') + '告警</div>';
      return;
    }

    container.innerHTML = filtered.map(a => renderAlertItem(a)).join('');
  } catch (e) {
    console.error('Failed to load alerts:', e);
  }
}

function renderAlertItem(alert) {
  const colors = { critical: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };
  const icons = { critical: '🚨', warning: '⚠️', info: 'ℹ️' };
  const labels = { critical: 'CRITICAL', warning: 'WARNING', info: 'INFO' };
  const color = colors[alert.level] || '#3b82f6';

  return `
    <div class="card mb-md" style="padding: 16px; border-left: 3px solid ${color}; background: ${color}11;">
      <div style="display: flex; align-items: start; justify-content: space-between; margin-bottom: 8px;">
        <div style="flex: 1;">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
            <span style="font-size: 20px;">${icons[alert.level] || '📋'}</span>
            <h4 style="font-size: 15px; font-weight: 600; color: white; margin: 0;">${escapeHtml(alert.message)}</h4>
            <span style="font-size: 11px; padding: 2px 8px; background: ${color}26; color: ${color}; border-radius: 4px; font-weight: 500;">${labels[alert.level] || alert.level}</span>
          </div>
        </div>
        <span style="font-size: 12px; color: #64748b;">${escapeHtml(alert.time || '')}</span>
      </div>
      <div style="font-size: 12px; color: #64748b;">
        来源: ${escapeHtml(alert.source || 'unknown')}
        ${alert.detail ? `<br>详情: ${escapeHtml(alert.detail)}` : ''}
      </div>
    </div>
  `;
}

async function loadPlatformStatus() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/alerts/platform-status');
    const data = await resp.json();

    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[3]) {
      statValues[3].textContent = data.running ? data.platform_count || '--' : '离线';
    }
  } catch (e) {
    console.error('Failed to load platform status:', e);
  }
}

function filterAlerts(level) {
  currentFilter = level;
  loadAlerts();
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
