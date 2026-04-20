/**
 * Dashboard JavaScript - Vercel Workflow Style Timeline Visualization
 * 数据源: /api/dashboard/* (读取 state.db)
 * 渲染: Gantt时间轴 + 任务条 + 树形结构 + 缩放控制
 */

let currentSession = null;
let allSessions = [];
let zoomLevel = 1;
let refreshInterval = null;
const REFRESH_MS = 5000;

document.addEventListener('DOMContentLoaded', () => {
  loadLatestSession();
  startAutoRefresh();
});

function startAutoRefresh() {
  if (refreshInterval) clearInterval(refreshInterval);
  refreshInterval = setInterval(loadLatestSession, REFRESH_MS);
}

async function loadLatestSession() {
  try {
    const resp = await fetch('/api/dashboard/sessions?limit=5');
    const sessions = await resp.json();
    allSessions = sessions;

    if (sessions.length === 0) {
      renderEmptyState();
      return;
    }

    const targetId = currentSession ? currentSession.id : sessions[0].id;
    const target = sessions.find(s => s.id === targetId) || sessions[0];

    await loadSessionDetail(target.id);
  } catch (e) {
    console.error('Failed to load sessions:', e);
  }
}

async function loadSessionDetail(sessionId) {
  try {
    const resp = await fetch(`/api/dashboard/session/${sessionId}`);
    const data = await resp.json();

    if (data.error) {
      renderEmptyState();
      return;
    }

    currentSession = data;
    updateHeader(data);
    buildTimeline(data);
  } catch (e) {
    console.error('Failed to load session detail:', e);
  }
}

function updateHeader(session) {
  document.getElementById('sessionRunId').textContent = session.id?.substring(0, 12) || 'unknown';
  document.getElementById('taskName').textContent = session.title || 'Hermes 会话追踪';

  const pill = document.getElementById('statusPill');
  const statusText = document.getElementById('statusText');

  if (session.ended_at) {
    pill.className = 'vw-status-pill vw-status-completed';
    statusText.textContent = 'Completed';
  } else {
    pill.className = 'vw-status-pill vw-status-running';
    statusText.textContent = '运行中';
  }

  document.getElementById('metaCreated').textContent = formatTimeAgo(session.started_at);
  document.getElementById('metaCompleted').textContent = session.ended_at ? formatTimeAgo(session.ended_at) : '--';
  
  const duration = session.ended_at 
    ? (session.ended_at - session.started_at)
    : (Date.now() / 1000 - (session.started_at || 0));
  document.getElementById('metaDuration').textContent = formatDuration(duration);

  const tokens = (session.input_tokens || 0) + (session.output_tokens || 0);
  document.getElementById('metaTokens').textContent = tokens > 0 ? formatTokenCount(tokens) : '--';
  document.getElementById('metaMessages').textContent = (session.messages || []).length || '--';
  document.getElementById('metaSource').textContent = session.source || 'unknown';
}

function buildTimeline(session) {
  const messages = session.messages || [];
  if (messages.length === 0) {
    renderEmptyState();
    return;
  }

  const baseTime = messages[0]?.timestamp || (session.started_at || Date.now() / 1000);
  let maxTime = baseTime;

  const hasTimestamps = messages.some(m => m.timestamp);
  const sessionDuration = session.ended_at
    ? (session.ended_at - (session.started_at || baseTime))
    : (Date.now() / 1000 - (session.started_at || baseTime));
  const avgMsgDuration = sessionDuration > 0 && messages.length > 1
    ? sessionDuration / messages.length : 2;

  const spans = [];
  let msgIndex = 0;

  while (msgIndex < messages.length) {
    const msg = messages[msgIndex];
    
    if (msg.role === 'user') {
      const startTime = msg.timestamp || baseTime;
      const nextMsg = messages[msgIndex + 1];
      const fallbackEnd = startTime + Math.max(avgMsgDuration * 0.3, 0.5);
      const endTime = nextMsg ? (nextMsg.timestamp || fallbackEnd) : (session.ended_at || fallbackEnd);
      
      spans.push({
        id: `msg-${msgIndex}`,
        label: truncate(msg.content?.substring(0, 60) || '用户消息', 50),
        type: 'user',
        startTime,
        endTime: Math.max(endTime, startTime + 0.5),
        level: 0,
        duration: endTime - startTime,
      });
      maxTime = Math.max(maxTime, endTime);
    } else if (msg.role === 'assistant') {
      const startTime = msg.timestamp || baseTime;
      const nextMsg = messages[msgIndex + 1];
      const fallbackEnd = startTime + Math.max(avgMsgDuration * 0.8, 1);
      const endTime = nextMsg ? (nextMsg.timestamp || fallbackEnd) : (session.ended_at || fallbackEnd);
      const contentPreview = msg.content?.substring(0, 60) || '';

      spans.push({
        id: `msg-${msgIndex}`,
        label: contentPreview || '助手回复',
        type: 'assistant',
        subType: msg.finish_reason === 'stop' ? 'success' : 'running',
        startTime,
        endTime: Math.max(endTime, startTime + 1),
        level: 0,
        duration: endTime - startTime,
        tokenCount: msg.token_count,
      });
      maxTime = Math.max(maxTime, endTime);
    } else if (msg.role === 'tool') {
      const startTime = msg.timestamp || baseTime;
      const nextMsg = messages[msgIndex + 1];
      const fallbackEnd = startTime + Math.max(avgMsgDuration * 1.2, 2);
      const endTime = nextMsg ? (nextMsg.timestamp || fallbackEnd) : (session.ended_at || fallbackEnd);
      const toolName = msg.tool_name || 'tool_call';
      const contentPreview = msg.content?.substring(0, 50) || '';

      spans.push({
        id: `msg-${msgIndex}`,
        label: `${toolName}${contentPreview ? ': ' + truncate(contentPreview, 35) : ''}`,
        type: 'tool',
        toolName,
        startTime,
        endTime: Math.max(endTime, startTime + 2),
        level: 1,
        duration: endTime - startTime,
      });
      maxTime = Math.max(maxTime, endTime);
    } else if (msg.role === 'system') {
      spans.push({
        id: `msg-${msgIndex}`,
        label: truncate(msg.content?.substring(0, 60) || '系统提示', 50),
        type: 'system',
        startTime: msg.timestamp || baseTime,
        endTime: (msg.timestamp || baseTime) + 1,
        level: 0,
        duration: 1,
      });
    }

    msgIndex++;
  }

  const totalDuration = Math.max(maxTime - baseTime, 10);
  renderRuler(baseTime, totalDuration);
  renderGrid(spans, baseTime, totalDuration);
}

function renderRuler(startTime, totalDuration) {
  const rulerTrack = document.getElementById('rulerTrack');
  if (!rulerTrack) return;

  rulerTrack.innerHTML = '';
  const containerWidth = rulerTrack.offsetWidth || 1000;
  const tickCount = Math.min(Math.max(Math.floor(containerWidth / 80), 6), 20);
  const tickInterval = totalDuration / tickCount;

  for (let i = 0; i <= tickCount; i++) {
    const time = startTime + (i * tickInterval);
    const pct = (i / tickCount) * 100;

    const tick = document.createElement('div');
    tick.className = 'vw-ruler-tick';
    tick.style.left = `${pct}%`;
    tick.textContent = formatTimelineTick(time - startTime);
    rulerTrack.appendChild(tick);

    if (i > 0 && i < tickCount) {
      const gridLine = document.createElement('div');
      gridLine.className = 'vw-ruler-grid-line';
      gridLine.style.left = `${pct}%`;
      rulerTrack.appendChild(gridLine);
    }
  }
}

function renderGrid(spans, baseTime, totalDuration) {
  const grid = document.getElementById('timelineGrid');
  if (!grid) return;

  grid.innerHTML = '';
  const containerWidth = grid.parentElement?.offsetWidth || 1200;

  spans.forEach((span, idx) => {
    const row = document.createElement('div');
    row.className = `vw-row vw-indent-${span.level}`;
    row.dataset.spanId = span.id;

    const startPct = ((span.startTime - baseTime) / totalDuration) * 100 * zoomLevel;
    const widthPct = (span.duration / totalDuration) * 100 * zoomLevel;

    const bar = document.createElement('div');
    bar.className = getSpanBarClass(span);
    bar.style.left = `${Math.max(startPct, 0)}%`;
    bar.style.width = `${Math.min(widthPct, 95)}%`;

    bar.innerHTML = `
      <span class="vw-span-label">${escapeHtml(span.label)}</span>
      <span class="vw-span-duration">${formatDuration(span.duration)}</span>
    `;

    bar.onclick = () => onSpanClick(span);

    if (span.level > 0 && idx > 0 && spans[idx - 1].level < span.level) {
      const treeV = document.createElement('div');
      treeV.className = 'vw-tree-line-v';
      row.appendChild(treeV);
    }

    row.appendChild(bar);
    grid.appendChild(row);
  });

  if (spans.length === 0) {
    grid.innerHTML = '<div class="vw-empty-state">暂无活动数据</div>';
  }
}

function getSpanBarClass(span) {
  const base = 'vw-span-bar';

  if (span.type === 'user') return `${base} vw-span-info`;
  if (span.type === 'system') return `${base} vw-span-info`;

  if (span.type === 'assistant') {
    if (span.subType === 'success') return `${base} vw-span-success`;
    if (span.subType === 'running') return `${base} vw-span-running`;
    return `${base} vw-span-info`;
  }

  if (span.type === 'tool') {
    const name = (span.toolName || '').toLowerCase();
    if (name.includes('sleep') || name.includes('wait')) return `${base} vw-span-sleep`;
    if (name.includes('error') || name.includes('fail')) return `${base} vw-span-error`;
    if (name.includes('search') || name.includes('fetch')) return `${base} vw-span-waiting`;
    return `${base} vw-span-running`;
  }

  return `${base} vw-span-info`;
}

function onSpanClick(span) {
  console.log('Span clicked:', span);
}

function switchTab(tabName) {
  document.querySelectorAll('.vw-tab').forEach(t => t.classList.remove('vw-tab-active'));
  document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('vw-tab-active');

  const body = document.getElementById('timelineBody');
  if (!body) return;

  if (tabName === 'events' && currentSession) {
    renderEventsTab(currentSession.messages || []);
  } else if (tabName === 'trace' && currentSession) {
    buildTimeline(currentSession);
  } else if (tabName === 'streams') {
    renderStreamsTab();
  }
}

function renderEventsTab(messages) {
  const body = document.getElementById('timelineBody');
  if (!body) return;

  body.innerHTML = `<div class="vw-events-list" id="eventsList"></div>`;
  const list = document.getElementById('eventsList');

  messages.forEach((msg, i) => {
    const item = document.createElement('div');
    item.className = 'vw-event-item';

    const roleLabel = { user: '👤 用户', assistant: '🤖 助手', system: '⚙️ 系统', tool: '🔧 工具' };
    const timeStr = formatTimestamp(msg.timestamp);

    item.innerHTML = `
      <span class="vw-event-time">${timeStr}</span>
      <span class="vw-event-role">${roleLabel[msg.role] || msg.role}</span>
      <span class="vw-event-content">${escapeHtml(truncate(msg.content || (msg.tool_name || ''), 200))}</span>
    `;
    list.appendChild(item);
  });
}

function filterTimeline() {
  const query = (document.getElementById('timelineSearch')?.value || '').toLowerCase();
  const rows = document.querySelectorAll('.vw-row');

  rows.forEach(row => {
    const label = row.querySelector('.vw-span-label')?.textContent?.toLowerCase() || '';
    row.style.display = (!query || label.includes(query)) ? '' : 'none';
  });
}

let streamEventSource = null;
let streamEvents = [];

function renderStreamsTab() {
  const body = document.getElementById('timelineBody');
  if (!body) return;

  body.innerHTML = `
    <div style="padding: 16px;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="font-size: 14px; color: #94a3b8;">SSE 实时流 — 监控会话活动</div>
        <button class="vw-btn-outline" onclick="toggleStream()" id="streamToggleBtn" style="font-size: 12px; padding: 4px 12px;">连接</button>
      </div>
      <div id="streamStatus" style="font-size: 12px; color: #64748b; margin-bottom: 8px;">未连接</div>
      <div id="streamEventsList" style="max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px;"></div>
    </div>
  `;

  if (streamEventSource) {
    streamEventSource.close();
    streamEventSource = null;
  }
  streamEvents = [];
}

function toggleStream() {
  const btn = document.getElementById('streamToggleBtn');
  const status = document.getElementById('streamStatus');

  if (streamEventSource) {
    streamEventSource.close();
    streamEventSource = null;
    if (btn) btn.textContent = '连接';
    if (status) status.textContent = '已断开';
    return;
  }

  try {
    streamEventSource = new EventSource('/api/dashboard/stream');
    if (btn) btn.textContent = '断开';
    if (status) status.textContent = '连接中...';

    streamEventSource.onopen = () => {
      if (status) status.textContent = '已连接 — 等待事件...';
    };

    streamEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const list = document.getElementById('streamEventsList');
        if (!list) return;

        const time = new Date().toLocaleTimeString('zh-CN');
        const typeColor = data.type === 'new_session' ? '#10b981' : '#64748b';
        const typeLabel = data.type === 'new_session' ? '🆕 新会话' : '💓 心跳';

        let detail = `活跃会话: ${data.active_sessions || 0}`;
        if (data.latest_session) {
          detail += ` | 最新: ${data.latest_session.title || data.latest_session.id?.substring(0, 12) || '--'}`;
          if (data.latest_session.ended_at) {
            detail += ` [已完成]`;
          }
        }

        const entry = document.createElement('div');
        entry.style.cssText = 'padding: 6px 8px; border-bottom: 1px solid #1f2937; display: flex; gap: 8px;';
        entry.innerHTML = `
          <span style="color: #64748b; white-space: nowrap;">${time}</span>
          <span style="color: ${typeColor}; white-space: nowrap;">${typeLabel}</span>
          <span style="color: #cbd5e1; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(detail)}</span>
        `;

        list.insertBefore(entry, list.firstChild);

        while (list.children.length > 100) {
          list.removeChild(list.lastChild);
        }

        if (data.type === 'new_session') {
          loadLatestSession();
        }

        if (status) status.textContent = `已连接 — ${time}`;
      } catch (e) {
        console.error('Stream parse error:', e);
      }
    };

    streamEventSource.onerror = () => {
      if (status) status.textContent = '连接断开 — 3秒后重连...';
    };
  } catch (e) {
    if (status) status.textContent = '连接失败: ' + e.message;
  }
}

function toggleMenu() {
  let menu = document.getElementById('vwContextMenu');
  if (menu) {
    menu.remove();
    return;
  }

  menu = document.createElement('div');
  menu.id = 'vwContextMenu';
  menu.style.cssText = 'position: fixed; top: 50%; right: 24px; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 4px; z-index: 1000; min-width: 160px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);';

  const items = [
    { label: '🔄 刷新数据', action: () => loadLatestSession() },
    { label: '🔍 适应视图', action: () => fitToView() },
    { label: '📊 查看全部会话', action: () => window.location.href = '/sessions' },
    { label: '⏱️ 自动刷新: 开', action: (el) => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
        el.textContent = '⏱️ 自动刷新: 关';
      } else {
        startAutoRefresh();
        el.textContent = '⏱️ 自动刷新: 开';
      }
    }},
  ];

  items.forEach(item => {
    const btn = document.createElement('div');
    btn.style.cssText = 'padding: 8px 12px; color: #cbd5e1; font-size: 13px; cursor: pointer; border-radius: 4px;';
    btn.textContent = item.label;
    btn.onmouseenter = () => btn.style.background = '#334155';
    btn.onmouseleave = () => btn.style.background = '';
    btn.onclick = () => {
      item.action(btn);
      if (item.label !== '⏱️ 自动刷新: 开') menu.remove();
    };
    menu.appendChild(btn);
  });

  document.body.appendChild(menu);

  const closeHandler = (e) => {
    if (!menu.contains(e.target)) {
      menu.remove();
      document.removeEventListener('click', closeHandler);
    }
  };
  setTimeout(() => document.addEventListener('click', closeHandler), 10);
}

/* ── Zoom Controls ── */
function zoomIn() {
  zoomLevel = Math.min(zoomLevel * 1.5, 5);
  if (currentSession) buildTimeline(currentSession);
}

function zoomOut() {
  zoomLevel = Math.max(zoomLevel / 1.5, 0.2);
  if (currentSession) buildTimeline(currentSession);
}

function fitToView() {
  zoomLevel = 1;
  if (currentSession) buildTimeline(currentSession);
}

/* ── Utilities ── */
function renderEmptyState() {
  const grid = document.getElementById('timelineGrid');
  if (grid) {
    grid.innerHTML = '<div class="vw-empty-state">🔍 暂无会话数据<br><small style="color:#333;margin-top:8px;">启动 Hermes Agent 后，此处将显示实时追踪时间轴</small></div>';
  }
  const rulerTrack = document.getElementById('rulerTrack');
  if (rulerTrack) rulerTrack.innerHTML = '';

  document.getElementById('taskName').textContent = 'Hermes 会话追踪';
  document.getElementById('statusPill').className = 'vw-status-pill vw-status-warning';
  document.getElementById('statusText').textContent = '等待数据';
  ['metaCreated', 'metaCompleted', 'metaDuration', 'metaTokens', 'metaMessages', 'metaSource'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = '--';
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

function formatTimelineTick(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}:${String(s).padStart(2, '0')}s`;
  }
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}:${String(m).padStart(2, '0')}`;
}

function formatTokenCount(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function formatTimestamp(timestamp) {
  if (!timestamp) return '--';
  const d = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);
  if (isNaN(d.getTime())) return '--';
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 2 });
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
