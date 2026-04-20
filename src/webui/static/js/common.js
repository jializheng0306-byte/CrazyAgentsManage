const SOURCE_EMOJI_MAP = {
  cli: '🖥️',
  cron: '⏰',
  telegram: '📱',
  discord: '💬',
  feishu: '🐦',
  slack: '💼',
  api_server: '🔌',
  acp: '📝',
  whatsapp: '📱',
  signal: '📡',
  homeassistant: '🏠',
};

function getSourceEmoji(source) {
  return SOURCE_EMOJI_MAP[source] || '📡';
}

function formatTokenCount(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0s';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return s > 0 ? `${m}m ${s}s` : `${m}m`;
  }
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function formatTime(timestamp) {
  if (!timestamp) return '--';
  const d = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);
  if (isNaN(d.getTime())) return '--';
  return d.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
}

function formatTimeAgo(timestamp) {
  if (!timestamp) return '--';
  const ts = typeof timestamp === 'number' ? timestamp * 1000 : timestamp;
  const diff = Date.now() - new Date(ts).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function sanitizeColor(val) {
  if (!val) return '#64748b';
  if (/^#[0-9a-fA-F]{6}$/.test(val.trim())) return val.trim();
  if (/^#[0-9a-fA-F]{3}$/.test(val.trim())) return val.trim();
  return '#64748b';
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

let _searchDropdownTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.querySelector('.nav-search');
  if (!searchInput) return;

  const wrapper = searchInput.parentElement;
  if (!wrapper.classList.contains('nav-search-wrapper')) {
    const newWrapper = document.createElement('div');
    newWrapper.className = 'nav-search-wrapper';
    searchInput.parentNode.insertBefore(newWrapper, searchInput);
    newWrapper.appendChild(searchInput);
  }

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const query = searchInput.value.trim();
      if (!query) return;
      closeSearchDropdown(searchInput);
      window.location.href = '/sessions?search=' + encodeURIComponent(query);
    }
    if (e.key === 'Escape') {
      closeSearchDropdown(searchInput);
    }
  });

  searchInput.addEventListener('input', () => {
    clearTimeout(_searchDropdownTimer);
    const query = searchInput.value.trim();
    if (query.length < 2) {
      closeSearchDropdown(searchInput);
      return;
    }
    _searchDropdownTimer = setTimeout(() => showSearchSuggestions(searchInput, query), 300);
  });

  searchInput.addEventListener('focus', () => {
    const query = searchInput.value.trim();
    if (query.length >= 2) {
      showSearchSuggestions(searchInput, query);
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.nav-search-wrapper')) {
      closeSearchDropdown(searchInput);
    }
  });

  const params = new URLSearchParams(window.location.search);
  const searchQuery = params.get('search');
  if (searchQuery && searchInput) {
    searchInput.value = searchQuery;
  }
});

async function showSearchSuggestions(input, query) {
  const pages = [
    { icon: '📊', title: '概览', url: '/', keywords: 'overview home 概览 首页' },
    { icon: '🟣', title: '智能体', url: '/agent', keywords: 'agent 智能体' },
    { icon: '📋', title: '任务', url: '/tasks', keywords: 'task 任务' },
    { icon: '📊', title: '监控仪表板', url: '/dashboard', keywords: 'dashboard 监控 仪表板' },
    { icon: '⚡', title: '技能', url: '/skills', keywords: 'skill 技能' },
    { icon: '📝', title: '团队记忆', url: '/team-memory', keywords: 'memory team 记忆 团队' },
    { icon: '⏰', title: '定时任务', url: '/cron', keywords: 'cron 定时' },
    { icon: '🔗', title: '图谱', url: '/graph', keywords: 'graph 图谱 知识' },
    { icon: '🔴', title: '会话流水线', url: '/sessions', keywords: 'session pipeline 会话 流水线' },
    { icon: '🔔', title: '告警', url: '/alerts', keywords: 'alert 告警' },
    { icon: '💰', title: 'Token', url: '/tokens', keywords: 'token 费用' },
  ];

  const q = query.toLowerCase();
  const matched = pages.filter(p =>
    p.title.toLowerCase().includes(q) ||
    p.keywords.toLowerCase().includes(q)
  );

  let dropdown = input.parentElement.querySelector('.nav-search-dropdown');
  if (!dropdown) {
    dropdown = document.createElement('div');
    dropdown.className = 'nav-search-dropdown';
    input.parentElement.appendChild(dropdown);
  }

  if (matched.length === 0) {
    dropdown.innerHTML = `
      <div class="nav-search-dropdown-empty">未找到匹配页面</div>
      <div class="nav-search-dropdown-hint">按 Enter 搜索会话: "${escapeHtml(query)}"</div>
    `;
  } else {
    dropdown.innerHTML = matched.map(p => `
      <div class="nav-search-dropdown-item" onclick="window.location.href='${p.url}'">
        <span class="nav-search-dropdown-item-icon">${p.icon}</span>
        <div class="nav-search-dropdown-item-text">
          <div class="nav-search-dropdown-item-title">${escapeHtml(p.title)}</div>
        </div>
      </div>
    `).join('') + `<div class="nav-search-dropdown-hint">按 Enter 搜索会话: "${escapeHtml(query)}"</div>`;
  }

  dropdown.style.display = 'block';
}

function closeSearchDropdown(input) {
  const dropdown = input.parentElement.querySelector('.nav-search-dropdown');
  if (dropdown) dropdown.style.display = 'none';
}
