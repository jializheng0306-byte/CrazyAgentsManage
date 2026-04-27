/**
 * CrazyAgentsManage — Operations Aggregation Page JS
 * Consumes skills/cron/memory/alerts APIs
 */

var OPS_CONFIG = {
  apiBase: '',
  refreshInterval: 30000,
  maxSkills: 8,
  maxCronJobs: 6,
  maxAlerts: 8,
  maxMemories: 6,
};

function fetchJSON(url) {
  return fetch(OPS_CONFIG.apiBase + url)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
}

function setText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function renderMetrics() {
  fetchJSON('/api/overview/stats').then(function(stats) {
    setText('ops-skills-count', stats.skills || 0);
    setText('ops-memory-count', stats.memory_files || 0);
  }).catch(function() {});

  fetchJSON('/api/cron/list').then(function(jobs) {
    var count = Array.isArray(jobs) ? jobs.length : 0;
    setText('ops-cron-count', count);
  }).catch(function() {
    setText('ops-cron-count', '0');
  });

  fetchJSON('/api/alerts/list').then(function(alerts) {
    var critical = 0;
    if (Array.isArray(alerts)) {
      alerts.forEach(function(a) {
        if (a.level === 'critical' || a.level === 'warning') critical++;
      });
    }
    setText('ops-alerts-count', critical);
  }).catch(function() {
    setText('ops-alerts-count', '0');
  });
}

function renderSkills() {
  var grid = document.getElementById('ops-skills-grid');

  fetchJSON('/api/skills/list').then(function(data) {
    var skills = (data.skills || []).slice(0, OPS_CONFIG.maxSkills);

    if (skills.length === 0) {
      grid.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">🔧</div><p>暂无已安装技能</p></div>';
      return;
    }

    grid.innerHTML = skills.map(function(s) {
      return '<div class="ops-skill-card">' +
        '<div class="ops-skill-category">' + (s.category_display || s.category || '') + '</div>' +
        '<div class="ops-skill-name">' + (s.name || '') + '</div>' +
        '<div class="ops-skill-desc" title="' + (s.description || '') + '">' + (s.description || '—') + '</div>' +
      '</div>';
    }).join('');
  }).catch(function() {
    grid.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function renderCronJobs() {
  var list = document.getElementById('ops-cron-list');

  fetchJSON('/api/cron/list').then(function(jobs) {
    if (!Array.isArray(jobs) || jobs.length === 0) {
      list.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⏰</div><p>暂无定时任务</p></div>';
      return;
    }

    var limited = jobs.slice(0, OPS_CONFIG.maxCronJobs);

    list.innerHTML = limited.map(function(j) {
      var isActive = j.active !== false && j.paused !== true;
      var statusClass = isActive ? 'active' : 'paused';
      var statusText = isActive ? '运行中' : '已暂停';

      return '<div class="ops-cron-item">' +
        '<span class="ops-cron-icon">⏰</span>' +
        '<div class="ops-cron-info">' +
          '<p class="ops-cron-name">' + (j.name || j.id || '未命名') + '</p>' +
          '<span class="ops-cron-schedule">' + (j.schedule || j.cron || '--') + '</span>' +
        '</div>' +
        '<span class="ops-cron-status ' + statusClass + '">' + statusText + '</span>' +
        '<span class="ops-cron-outputs">' + (j.output_count || 0) + ' 次输出</span>' +
      '</div>';
    }).join('');
  }).catch(function() {
    list.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function renderAlerts() {
  var list = document.getElementById('ops-alerts-list');

  fetchJSON('/api/alerts/list').then(function(alerts) {
    if (!Array.isArray(alerts) || alerts.length === 0) {
      list.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">✅</div><p>暂无告警</p></div>';
      return;
    }

    var limited = alerts.slice(0, OPS_CONFIG.maxAlerts);

    list.innerHTML = limited.map(function(a) {
      var iconClass = a.level || 'info';
      var icon = a.level === 'critical' ? '🔴' : (a.level === 'warning' ? '🟡' : '🔵');

      return '<div class="ops-alert-item">' +
        '<div class="ops-alert-icon ' + iconClass + '">' + icon + '</div>' +
        '<div class="ops-alert-content">' +
          '<p class="ops-alert-title">' + (a.source || '系统') + '</p>' +
          '<p class="ops-alert-detail" title="' + (a.message || '') + '">' + (a.message || '—') + '</p>' +
        '</div>' +
        '<span class="ops-alert-time">' + (a.time || '--') + '</span>' +
      '</div>';
    }).join('');
  }).catch(function() {
    list.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function renderMemories() {
  var grid = document.getElementById('ops-memory-grid');

  fetchJSON('/api/overview/memories').then(function(memories) {
    if (!Array.isArray(memories) || memories.length === 0) {
      grid.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">📝</div><p>暂无记忆文件</p></div>';
      return;
    }

    var limited = memories.slice(0, OPS_CONFIG.maxMemories);

    grid.innerHTML = limited.map(function(m) {
      return '<div class="ops-memory-card">' +
        '<p class="ops-memory-name">' + (m.name || '未命名') + '</p>' +
        '<p class="ops-memory-preview" title="' + (m.preview || '') + '">' + (m.preview || '(空)') + '</p>' +
        '<div class="ops-memory-meta">' +
          '<span>' + (m.path || '') + '</span>' +
          '<span>' + (m.size || 0) + ' bytes</span>' +
        '</div>' +
      '</div>';
    }).join('');
  }).catch(function() {
    grid.innerHTML = '<div class="ops-empty"><div class="ops-empty-icon">⚠️</div><p>加载失败</p></div>';
  });
}

function loadOperations() {
  renderMetrics();
  renderSkills();
  renderCronJobs();
  renderAlerts();
  renderMemories();
}

function init() {
  loadOperations();
  setInterval(loadOperations, OPS_CONFIG.refreshInterval);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
