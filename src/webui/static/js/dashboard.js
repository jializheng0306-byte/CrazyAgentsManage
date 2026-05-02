/**
 * Dashboard JavaScript - Trace Tree View (NestJS/Vercel Trace inspired)
 * Data: /api/dashboard/* (reads state.db)
 * Render: Vertical nested tree with expand/collapse, tokens, status
 *
 * Design rationale:
 * - Vercel Gantt charts work for workflows with parallel execution (true startTime/endTime)
 * - Hermes messages are sequential with near-identical timestamps
 * - Horizontal timeline is meaningless for our data model
 * - Solution: Nested tree showing conversation flow (user -> assistant -> tool calls)
 */

let currentSession = null;
let allSessions = [];
let refreshInterval = null;
let autoRefreshEnabled = true;
const REFRESH_MS = 60000;
let currentSpans = [];
let expandedNodes = new Set();
let expandedRounds = new Set();

const ROLE_ICONS = { user: '👤', assistant: '🤖', system: '⚙️', tool: '🔧' };
const ROLE_LABELS = { user: '用户消息', assistant: '助手回复', system: '系统提示', tool: '工具调用' };

document.addEventListener('DOMContentLoaded', () => {
  loadLatestSession();
  startAutoRefresh();

  const metaArea = document.getElementById('metaSource');
  if (metaArea && !document.getElementById('autoRefreshToggle')) {
    const btn = document.createElement('button');
    btn.id = 'autoRefreshToggle';
    btn.textContent = '⏸️ 暂停';
    btn.style.cssText = 'padding:4px 12px;background:#334155;color:#cbd5e1;border:1px solid #475569;border-radius:6px;cursor:pointer;font-size:12px;margin-left:8px;';
    btn.onclick = (e) => { e.stopPropagation(); toggleAutoRefresh(); };
    metaArea.parentNode.insertBefore(btn, metaArea.nextSibling);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSidePanel();
    }
  });
});

function startAutoRefresh() {
  if (refreshInterval) clearInterval(refreshInterval);
  if (!autoRefreshEnabled) return;
  refreshInterval = setInterval(loadLatestSession, REFRESH_MS);
}

function toggleAutoRefresh() {
  autoRefreshEnabled = !autoRefreshEnabled;
  const btn = document.getElementById('autoRefreshToggle');
  if (btn) {
    if (autoRefreshEnabled) {
      btn.textContent = '⏸️ 暂停';
      btn.style.background = '#334155';
      startAutoRefresh();
    } else {
      btn.textContent = '▶️ 已暂停';
      btn.style.background = '#dc2626';
      if (refreshInterval) { clearInterval(refreshInterval); refreshInterval = null; }
    }
  }
}

async function loadLatestSession() {
  showLoadingSpinner();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    const resp = await fetch('./api/dashboard/sessions?limit=5', { signal: controller.signal });
    clearTimeout(timeoutId);
    const sessions = await resp.json();
    allSessions = sessions;
    if (sessions.length === 0) { renderEmptyState(); return; }
    const targetId = currentSession ? currentSession.id : sessions[0].id;
    const target = sessions.find(s => s.id === targetId) || sessions[0];
    await loadSessionDetail(target.id);
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('Failed to load sessions:', e);
      renderEmptyState();
    }
  }
}

async function loadSessionDetail(sessionId) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    const resp = await fetch(`./api/dashboard/session/${sessionId}`, { signal: controller.signal });
    clearTimeout(timeoutId);
    const data = await resp.json();
    if (data.error || !data || typeof data.id === 'undefined') {
      console.warn('Invalid session data:', data);
      renderEmptyState();
      return;
    }
    currentSession = data;
    updateHeader(data);
    buildTraceTree(data);
  } catch (e) {
    if (e.name !== 'AbortError') {
      console.error('Failed to load session detail:', e);
      renderEmptyState();
    }
  }
}

function updateHeader(session) {
  document.getElementById('sessionRunId').textContent = (session?.id || 'unknown').substring(0, 12);
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

/**
 * Build the trace tree from session messages
 * Structure: Round -> [User, Assistant, [Tool calls...]]
 */
function buildTraceTree(session) {
  const messages = session.messages || [];
  if (messages.length === 0) { renderEmptyState(); return; }

  const spans = [];
  let roundNum = 0;

  // First pass: build flat spans with parent-child relationships
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];

    if (msg.role === 'user') {
      roundNum++;
      spans.push({
        id: `msg-${i}`,
        role: 'user',
        label: truncate(msg.content?.substring(0, 80) || '用户消息', 60),
        content: msg.content || '',
        tokenCount: null,
        status: 'info',
        round: roundNum,
        level: 0,
        hasChildren: false,
        raw: msg,
      });
    } else if (msg.role === 'assistant') {
      const isDone = msg.finish_reason === 'stop';
      // Check if next message is a tool call
      let nextIsTool = false;
      if (i + 1 < messages.length && messages[i + 1].role === 'tool') {
        nextIsTool = true;
      }

      spans.push({
        id: `msg-${i}`,
        role: 'assistant',
        label: truncate(msg.content?.substring(0, 80) || (isDone ? '✅ 完成' : '⏳ 思考中...'), 60),
        content: msg.content || '',
        tokenCount: msg.token_count,
        status: isDone ? 'success' : 'running',
        round: roundNum || 1,
        level: 0,
        hasChildren: nextIsTool,
        raw: msg,
      });
    } else if (msg.role === 'tool') {
      const toolName = msg.tool_name || 'tool_call';
      let contentPreview = msg.content?.substring(0, 50) || '';
      let toolStatus = 'success';

      try {
        const parsed = JSON.parse(msg.content || '');
        if (parsed.output) contentPreview = String(parsed.output).substring(0, 50);
        else if (parsed.error) { contentPreview = '❌ Error: ' + String(parsed.error).substring(0, 35); toolStatus = 'error'; }
        else if (parsed.success === false) { contentPreview = '❌ Failed'; toolStatus = 'error'; }
        else if (parsed.success === true) { contentPreview = '✅ OK' + (parsed.skills ? ` (${parsed.skills.length} skills)` : ''); toolStatus = 'success'; }
      } catch(e) { /* not JSON */ }

      // Calculate duration from adjacent timestamps
      let duration = 0;
      if (msg.timestamp && i + 1 < messages.length && messages[i + 1].timestamp) {
        duration = messages[i + 1].timestamp - msg.timestamp;
      }

      spans.push({
        id: `msg-${i}`,
        role: 'tool',
        toolName: toolName,
        label: `${toolName}${contentPreview ? ': ' + truncate(contentPreview, 35) : ''}`,
        content: msg.content || '',
        tokenCount: null,
        status: toolStatus,
        round: roundNum || 1,
        level: 1,
        hasChildren: false,
        duration: duration,
        raw: msg,
      });
    } else if (msg.role === 'system') {
      spans.push({
        id: `msg-${i}`,
        role: 'system',
        label: truncate(msg.content?.substring(0, 80) || '系统提示', 60),
        content: msg.content || '',
        tokenCount: null,
        status: 'info',
        round: 0,
        level: 0,
        hasChildren: false,
        raw: msg,
      });
    }
  }

  currentSpans = spans;
  renderTraceTree(spans, session);
  renderSummaryBar(spans, session);
}

/**
 * Render the trace tree as nested HTML
 */
function renderTraceTree(spans, session) {
  const container = document.getElementById('traceTree');
  if (!container) return;

  container.innerHTML = '';

  // Group by round
  const rounds = {};
  const systemMessages = [];

  spans.forEach(span => {
    if (span.round === 0) {
      systemMessages.push(span);
    } else {
      if (!rounds[span.round]) rounds[span.round] = [];
      rounds[span.round].push(span);
    }
  });

  // Render system messages first
  if (systemMessages.length > 0) {
    const group = document.createElement('div');
    group.className = 'vw-round-group';

    const header = document.createElement('div');
    header.className = 'vw-round-header';
    header.innerHTML = `
      <span class="vw-round-chevron">▼</span>
      <span class="vw-round-label">System</span>
      <span class="vw-round-badge">${systemMessages.length} message(s)</span>
    `;
    group.appendChild(header);

    const children = document.createElement('div');
    children.className = 'vw-round-children';
    systemMessages.forEach(span => {
      children.appendChild(createTreeNode(span));
    });
    group.appendChild(children);
    container.appendChild(group);
  }

  // Render each round
  Object.keys(rounds).sort((a, b) => a - b).forEach(roundNum => {
    const group = document.createElement('div');
    group.className = 'vw-round-group';
    group.dataset.round = roundNum;

    const roundSpans = rounds[roundNum];
    const msgCount = roundSpans.length;
    const toolCount = roundSpans.filter(s => s.role === 'tool').length;
    const tokenCount = roundSpans.reduce((sum, s) => sum + (s.tokenCount || 0), 0);

    const header = document.createElement('div');
    header.className = 'vw-round-header';
    const isExpanded = expandedRounds.has(roundNum);
    if (!isExpanded) header.classList.add('vw-round-collapsed');

    header.innerHTML = `
      <span class="vw-round-chevron">${isExpanded ? '▼' : '▶'}</span>
      <span class="vw-round-label">Round ${roundNum}</span>
      <span class="vw-round-badge">${msgCount} spans · ${toolCount} tools · ${formatTokenCount(tokenCount)} tokens</span>
    `;
    header.onclick = () => toggleRound(roundNum, header);
    group.appendChild(header);

    const children = document.createElement('div');
    children.className = 'vw-round-children';
    if (!isExpanded) children.style.display = 'none';

    roundSpans.forEach(span => {
      children.appendChild(createTreeNode(span));
    });
    group.appendChild(children);
    container.appendChild(group);
  });

  if (spans.length === 0) {
    container.innerHTML = '<div class="vw-empty-state">暂无活动数据</div>';
  }
}

/**
 * Create a single tree node element
 */
function createTreeNode(span) {
  const wrapper = document.createElement('div');

  // Main node row
  const node = document.createElement('div');
  node.className = `vw-tree-node vw-tree-indent-${Math.min(span.level, 3)}`;
  node.dataset.spanId = span.id;

  const isExpanded = expandedNodes.has(span.id);
  if (!isExpanded && span.hasChildren) {
    node.classList.add('vw-tree-node-collapsed');
  }

  // Toggle arrow (only for assistant nodes that have tool children)
  const toggleEl = span.hasChildren
    ? `<div class="vw-tree-toggle" onclick="event.stopPropagation(); toggleNode('${span.id}')">
         <span class="vw-tree-toggle-icon">${isExpanded ? '▼' : '▶'}</span>
       </div>`
    : `<div class="vw-tree-toggle-empty"></div>`;

  // Icon
  const icon = ROLE_ICONS[span.role] || '📌';

  // Label
  const label = escapeHtml(span.label);

  // Token
  const tokenHtml = span.tokenCount
    ? `<span class="vw-tree-token vw-tree-token-highlight">${span.tokenCount}</span>`
    : `<span class="vw-tree-token">--</span>`;

  // Duration
  const durationHtml = span.duration
    ? `<span class="vw-tree-duration">${formatDuration(span.duration)}</span>`
    : `<span class="vw-tree-duration">--</span>`;

  // Status badge
  const statusHtml = getStatusBadge(span.status);

  node.innerHTML = `
    ${toggleEl}
    <span class="vw-tree-icon">${icon}</span>
    <span class="vw-tree-label" title="${escapeHtml(span.content?.substring(0, 200) || '')}">${label}</span>
    ${tokenHtml}
    ${durationHtml}
    ${statusHtml}
  `;

  node.onclick = (e) => {
    if (e.target.closest('.vw-tree-toggle')) return;
    onSpanClick(span);
  };

  wrapper.appendChild(node);

  // Inline detail panel (for expanded assistant nodes)
  if (span.hasChildren && isExpanded) {
    const detail = document.createElement('div');
    detail.className = 'vw-tree-detail';
    detail.innerHTML = `
      <div class="vw-tree-detail-inner">
        <div class="vw-detail-section">
          <div class="vw-detail-label">消息内容</div>
          <div class="vw-detail-content"><code>${escapeHtml(span.content || '(空)')}</code></div>
        </div>
      </div>
    `;
    wrapper.appendChild(detail);
  }

  return wrapper;
}

function getStatusBadge(status) {
  const map = {
    success: '<span class="vw-node-badge vw-node-badge-success"><span class="vw-node-dot vw-node-dot-success"></span> 成功</span>',
    running: '<span class="vw-node-badge vw-node-badge-running"><span class="vw-node-dot vw-node-dot-running"></span> 运行中</span>',
    error: '<span class="vw-node-badge vw-node-badge-error"><span class="vw-node-dot vw-node-dot-error"></span> 失败</span>',
    info: '<span class="vw-node-badge vw-node-badge-info">信息</span>',
  };
  return `<span class="vw-tree-status">${map[status] || map.info}</span>`;
}

function toggleRound(roundNum, headerEl) {
  if (expandedRounds.has(roundNum)) {
    expandedRounds.delete(roundNum);
    headerEl.classList.add('vw-round-collapsed');
    headerEl.querySelector('.vw-round-chevron').textContent = '▶';
    const children = headerEl.nextElementSibling;
    if (children) children.style.display = 'none';
  } else {
    expandedRounds.add(roundNum);
    headerEl.classList.remove('vw-round-collapsed');
    headerEl.querySelector('.vw-round-chevron').textContent = '▼';
    const children = headerEl.nextElementSibling;
    if (children) children.style.display = '';
  }
}

function toggleNode(spanId) {
  if (expandedNodes.has(spanId)) {
    expandedNodes.delete(spanId);
  } else {
    expandedNodes.add(spanId);
  }
  // Re-render
  if (currentSession) buildTraceTree(currentSession);
}

/**
 * Side panel click handler
 */
function onSpanClick(span) {
  activeDetailSpan = span.id;

  // Highlight active node
  document.querySelectorAll('.vw-tree-node-active').forEach(el => el.classList.remove('vw-tree-node-active'));
  const activeNode = document.querySelector(`.vw-tree-node[data-span-id="${span.id}"]`);
  if (activeNode) activeNode.classList.add('vw-tree-node-active');

  openSidePanel(span);
}

let activeDetailSpan = null;

function openSidePanel(span) {
  const overlay = document.getElementById('sidePanelOverlay');
  const panel = document.getElementById('sidePanel');
  const iconEl = document.getElementById('spIcon');
  const titleEl = document.getElementById('spTitle');
  const badgeEl = document.getElementById('spBadge');
  const bodyEl = document.getElementById('spBody');

  if (!panel || !bodyEl) return;

  const raw = span.raw || {};
  const content = raw.content || '';
  let formattedContent = content;
  try {
    const parsed = JSON.parse(content);
    formattedContent = JSON.stringify(parsed, null, 2);
  } catch(e) { /* not JSON */ }

  const tokenInfo = span.tokenCount !== undefined
    ? `<div class="vw-side-panel-row"><span class="vw-spk">Token消耗</span><span class="vw-spv">${span.tokenCount}</span></div>`
    : '';

  const finishInfo = raw.finish_reason
    ? `<div class="vw-side-panel-row"><span class="vw-spk">结束原因</span><span class="vw-spv"><code>${raw.finish_reason}</code></span></div>`
    : '';

  const toolInfo = raw.tool_name
    ? `<div class="vw-side-panel-row"><span class="vw-spk">工具名称</span><span class="vw-spv"><code>${raw.tool_name}</code></span></div>`
    : '';

  const reasoningInfo = raw.reasoning
    ? `<div class="vw-side-panel-section"><div class="vw-side-panel-section-title">推理过程</div><pre class="vw-side-panel-content">${escapeHtml(raw.reasoning)}</pre></div>`
    : '';

  const timeFormatted = raw.timestamp_iso
    ? new Date(raw.timestamp_iso).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })
    : '--';

  const statusText = span.status === 'error' ? '❌ 失败' : span.status === 'success' ? '✅ 成功' : span.status === 'running' ? '⏳ 运行中' : '信息';

  iconEl.textContent = ROLE_ICONS[span.role] || '📌';
  titleEl.textContent = span.toolName || ROLE_LABELS[span.role] || '消息详情';
  badgeEl.textContent = span.duration ? formatDuration(span.duration) : '--';

  bodyEl.innerHTML = `
    <div class="vw-side-panel-section">
      <div class="vw-side-panel-section-title">基本信息</div>
      <div class="vw-side-panel-row"><span class="vw-spk">消息ID</span><span class="vw-spv vw-spv-mono">${raw.id || span.id}</span></div>
      <div class="vw-side-panel-row"><span class="vw-spk">角色类型</span><span class="vw-spv">${ROLE_LABELS[span.role] || span.role}</span></div>
      ${toolInfo}
      <div class="vw-side-panel-row"><span class="vw-spk">状态</span><span class="vw-spv">${statusText}</span></div>
      ${finishInfo}
      ${tokenInfo}
      <div class="vw-side-panel-row"><span class="vw-spk">时间戳</span><span class="vw-spv vw-spv-mono">${timeFormatted}</span></div>
      ${span.duration ? `<div class="vw-side-panel-row"><span class="vw-spk">持续时间</span><span class="vw-spv">${formatDuration(span.duration)}</span></div>` : ''}
      <div class="vw-side-panel-row"><span class="vw-spk">所属轮次</span><span class="vw-spv">Round ${span.round || '--'}</span></div>
    </div>
    <div class="vw-side-panel-section">
      <div class="vw-side-panel-section-title">内容详情</div>
      <pre class="vw-side-panel-content">${escapeHtml(formattedContent) || '(空)'}</pre>
    </div>
    ${reasoningInfo}
  `;

  overlay?.classList.add('visible');
  panel.classList.add('open');
}

function closeSidePanel() {
  const overlay = document.getElementById('sidePanelOverlay');
  const panel = document.getElementById('sidePanel');
  overlay?.classList.remove('visible');
  panel?.classList.remove('open');
  document.querySelectorAll('.vw-tree-node-active').forEach(el => el.classList.remove('vw-tree-node-active'));
  activeDetailSpan = null;
}

/* ════════════════════════════════════════════════════
   TAB SWITCHING
   ════════════════════════════════════════════════════ */
function switchTab(tabName) {
  document.querySelectorAll('.vw-tab').forEach(t => t.classList.remove('vw-tab-active'));
  document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('vw-tab-active');

  const traceContainer = document.getElementById('traceContainer');
  const searchBar = document.querySelector('.vw-search-bar');

  closeSidePanel();

  if (tabName === 'events' && currentSession) {
    if (traceContainer) traceContainer.style.display = 'none';
    if (searchBar) searchBar.style.display = 'none';
    renderEventsTab(currentSession.messages || []);
  } else if (tabName === 'trace') {
    if (traceContainer) traceContainer.style.display = 'block';
    if (searchBar) searchBar.style.display = 'block';
    const eventsList = document.getElementById('eventsList');
    if (eventsList) eventsList.remove();
    if (currentSession && currentSession.id) {
      loadSessionDetail(currentSession.id);
    } else {
      loadLatestSession();
    }
  } else if (tabName === 'streams') {
    if (traceContainer) traceContainer.style.display = 'none';
    if (searchBar) searchBar.style.display = 'none';
    renderStreamsTab();
  }
}

function renderEventsTab(messages) {
  let list = document.getElementById('eventsList');
  if (!list) {
    list = document.createElement('div');
    list.className = 'vw-events-list';
    list.id = 'eventsList';
    document.getElementById('dashboard-app')?.appendChild(list);
  }
  list.innerHTML = '';
  list.style.display = 'block';

  messages.forEach((msg) => {
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
  document.querySelectorAll('.vw-tree-node').forEach(node => {
    const spanId = node.dataset.spanId;
    const span = currentSpans.find(s => s.id === spanId);
    const match = !query || (span && (
      span.label.toLowerCase().includes(query) ||
      span.role.toLowerCase().includes(query) ||
      (span.toolName || '').toLowerCase().includes(query) ||
      (span.content || '').toLowerCase().includes(query)
    ));
    node.style.display = match ? '' : 'none';
  });
}

/* ════════════════════════════════════════════════════
   SUMMARY BAR
   ════════════════════════════════════════════════════ */
function renderSummaryBar(spans, session) {
  const summaryEl = document.getElementById('traceSummary');
  if (!summaryEl) return;

  const toolCount = spans.filter(s => s.role === 'tool').length;
  const errorCount = spans.filter(s => s.status === 'error').length;
  const totalTokens = spans.reduce((sum, s) => sum + (s.tokenCount || 0), 0);
  const rounds = new Set(spans.map(s => s.round).filter(r => r > 0)).size;
  const toolSpans = spans.filter(s => s.role === 'tool');
  const avgToolDur = toolSpans.length > 0 && toolSpans.some(t => t.duration)
    ? toolSpans.filter(t => t.duration).reduce((sum, s) => sum + s.duration, 0) / toolSpans.filter(t => t.duration).length
    : 0;

  summaryEl.innerHTML = `
    <span class="vw-summary-item" title="对话轮次数">📋 ${rounds} 轮</span>
    <span class="vw-summary-divider">|</span>
    <span class="vw-summary-item" title="工具调用次数">🔧 ${toolCount} 次</span>
    <span class="vw-summary-divider">|</span>
    ${errorCount > 0 ? `<span class="vw-summary-item vw-summary-error" title="失败的工具调用">❌ ${errorCount} 错误</span><span class="vw-summary-divider">|</span>` : ''}
    <span class="vw-summary-item" title="总Token消耗">💰 ${formatTokenCount(totalTokens)}</span>
    <span class="vw-summary-divider">|</span>
    <span class="vw-summary-item" title="平均工具耗时">⏱️ ${formatDuration(avgToolDur)}</span>
  `;
  summaryEl.style.display = '';
}

/* ════════════════════════════════════════════════════
   STREAMS TAB
   ════════════════════════════════════════════════════ */
let streamEventSource = null;

function renderStreamsTab() {
  let container = document.getElementById('streamsContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'streamsContainer';
    container.style.cssText = 'padding: 16px 24px;';
    document.getElementById('dashboard-app')?.appendChild(container);
  }
  container.innerHTML = '';
  container.style.display = 'block';

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <div style="font-size: 14px; color: #94a3b8;">SSE 实时流 — 监控会话活动</div>
      <button class="vw-btn-outline" onclick="toggleStream()" id="streamToggleBtn" style="font-size: 12px; padding: 4px 12px;">连接</button>
    </div>
    <div id="streamStatus" style="font-size: 12px; color: #64748b; margin-bottom: 8px;">未连接</div>
    <div id="streamEventsList" style="max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px;"></div>
  `;

  if (streamEventSource) {
    streamEventSource.close();
    streamEventSource = null;
  }
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
    streamEventSource = new EventSource('./api/dashboard/stream');
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
          if (data.latest_session.ended_at) detail += ` [已完成]`;
        }

        const entry = document.createElement('div');
        entry.style.cssText = 'padding: 6px 8px; border-bottom: 1px solid #1f2937; display: flex; gap: 8px;';
        entry.innerHTML = `
          <span style="color: #64748b; white-space: nowrap;">${time}</span>
          <span style="color: ${typeColor}; white-space: nowrap;">${typeLabel}</span>
          <span style="color: #cbd5e1; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(detail)}</span>
        `;
        list.insertBefore(entry, list.firstChild);
        while (list.children.length > 100) list.removeChild(list.lastChild);

        if (data.type === 'new_session') loadLatestSession();
        if (status) status.textContent = `已连接 — ${time}`;
      } catch (e) { console.error('Stream parse error:', e); }
    };

    streamEventSource.onerror = () => {
      if (status) status.textContent = '连接断开 — 3秒后重连...';
    };
  } catch (e) {
    if (status) status.textContent = '连接失败: ' + e.message;
  }
}

/* ════════════════════════════════════════════════════
   MENU
   ════════════════════════════════════════════════════ */
function toggleMenu() {
  let menu = document.getElementById('vwContextMenu');
  if (menu) { menu.remove(); return; }

  menu = document.createElement('div');
  menu.id = 'vwContextMenu';
  menu.style.cssText = 'position: fixed; top: 50%; right: 24px; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 4px; z-index: 1000; min-width: 160px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);';

  const items = [
    { label: '🔄 刷新数据', action: () => loadLatestSession() },
    { label: '📊 查看全部会话', action: () => window.location.href = '/sessions' },
    { label: '⏱️ 自动刷新: 开', action: (el) => {
      if (refreshInterval) {
        clearInterval(refreshInterval); refreshInterval = null;
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
    if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener('click', closeHandler); }
  };
  setTimeout(() => document.addEventListener('click', closeHandler), 10);
}

/* ════════════════════════════════════════════════════
   UTILITIES
   ════════════════════════════════════════════════════ */
function showLoadingSpinner() {
  const container = document.getElementById('traceTree');
  if (!container) return;
  container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;padding:80px 20px;flex-direction:column;gap:12px;"><div style="width:40px;height:40px;border:4px solid #334155;border-top:#667eea solid;border-radius:50%;animation:vwDashSpin 0.8s linear infinite;"></div><span style="color:#94a3b8;font-size:14px;">正在加载数据...</span></div>';
  if (!document.getElementById('vwDashSpinStyle')) {
    const s = document.createElement('style');
    s.id = 'vwDashSpinStyle';
    s.textContent = '@keyframes vwDashSpin { to { transform: rotate(360deg); } }';
    document.head.appendChild(s);
  }
}

function renderEmptyState() {
  const container = document.getElementById('traceTree');
  if (container) container.innerHTML = '<div class="vw-empty-state">🔍 暂无会话数据</div>';

  document.getElementById('taskName').textContent = 'Hermes 会话追踪';
  document.getElementById('statusPill').className = 'vw-status-pill vw-status-warning';
  document.getElementById('statusText').textContent = '等待数据';
  ['metaCreated', 'metaCompleted', 'metaDuration', 'metaTokens', 'metaMessages', 'metaSource'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = '--';
  });
  const summaryEl = document.getElementById('traceSummary');
  if (summaryEl) summaryEl.style.display = 'none';
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
  if (!seconds || seconds < 0.5) return '--';
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

function formatTimestamp(timestamp) {
  if (!timestamp) return '--';
  const d = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp);
  if (isNaN(d.getTime())) return '--';
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 2 });
}

function formatTokenCount(count) {
  if (!count || count === 0) return '0';
  if (count < 1000) return String(count);
  if (count < 1000000) return `${(count / 1000).toFixed(1)}K`;
  return `${(count / 1000000).toFixed(1)}M`;
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
