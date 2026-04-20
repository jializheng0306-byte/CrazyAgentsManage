let alertRefreshInterval = null;
let currentFilter = 'all';
let acknowledgedAlerts = new Set();
let silencedAlerts = new Set();

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
    const resp = await fetch('/api/alerts/list');
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

    filtered = filtered.filter(a => !acknowledgedAlerts.has(a.id) && !silencedAlerts.has(a.id));

    if (filtered.length === 0) {
      container.innerHTML = '<div class="empty-state">✅ 暂无' + (currentFilter === 'all' ? '' : currentFilter + '级别') + '告警</div>';
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
    <div class="card mb-md" style="padding:16px;border-left:3px solid ${color};background:${color}11;">
      <div class="alert-item" style="padding:0;border:none;">
        <span class="alert-icon">${icons[alert.level] || '📋'}</span>
        <div class="alert-content">
          <div style="display:flex;align-items:center;gap:8px;">
            <h4 style="font-size:15px;font-weight:600;color:white;margin:0;">${escapeHtml(alert.message)}</h4>
            <span class="status-badge" style="background:${color}26;color:${color};font-size:11px;">${labels[alert.level] || alert.level}</span>
          </div>
          <div class="alert-desc">来源: ${escapeHtml(alert.source || 'unknown')}${alert.detail ? ' · ' + escapeHtml(alert.detail) : ''}</div>
          <div class="alert-time">${escapeHtml(alert.time || '')}</div>
        </div>
        <div class="alert-actions">
          <button class="alert-action-btn" onclick="acknowledgeAlert('${alert.id}')" title="确认告警">✓</button>
          <button class="alert-action-btn" onclick="silenceAlert('${alert.id}')" title="静默告警">🔇</button>
        </div>
      </div>
    </div>
  `;
}

function acknowledgeAlert(alertId) {
  acknowledgedAlerts.add(alertId);
  loadAlerts();
}

function silenceAlert(alertId) {
  silencedAlerts.add(alertId);
  loadAlerts();
}

async function loadPlatformStatus() {
  try {
    const resp = await fetch('/api/alerts/platform-status');
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
