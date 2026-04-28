/**
 * Sessions JavaScript - 会话流水线索引 (v0.5.0 Enhanced)
 * 数据源: /api/sessions/* + /api/dashboard/* + /api/agent-dashboard/*
 * 功能: 统计面板、根会话索引、流水线详情、会话画像、筛选/搜索/导出
 */

let currentSessionId = null;
let currentSource = null;
let currentStatus = null;
let searchTimeout = null;
let allSessions = [];
let currentPage = 0;
const PAGE_SIZE = 30;

document.addEventListener('DOMContentLoaded', () => {
  loadSessionStats();
  loadSessionList();
  initSearchHandler();
  loadSourceOptions();

  const params = new URLSearchParams(window.location.search);
  const searchQuery = params.get('search');
  if (searchQuery) {
    const searchInput = document.getElementById('sessionSearch');
    if (searchInput) {
      searchInput.value = searchQuery;
      searchSessions(searchQuery);
    }
  }
});

function initSearchHandler() {
  const searchInput = document.getElementById('sessionSearch');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        const query = e.target.value.trim();
        if (query.length >= 2) {
          searchSessions(query);
        } else if (query.length === 0) {
          loadSessionList();
        }
      }, 300);
    });
  }
}

async function loadSourceOptions() {
  try {
    const resp = await fetch('./api/overview/stats');
    const data = await resp.json();
    const sources = data.sources || [];
    const select = document.getElementById('sourceFilter');
    if (!select) return;

    sources.forEach(src => {
      const opt = document.createElement('option');
      opt.value = src;
      opt.textContent = `${getSourceEmoji(src)} ${src}`;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error('Failed to load source options:', e);
  }
}

async function loadSessionStats() {
  try {
    const resp = await fetch('./api/sessions/stats');
    const data = await resp.json();

    const el = (id) => document.getElementById(id);
    if (el('statTotal')) el('statTotal').textContent = (data.total_sessions || 0).toLocaleString();
    if (el('statChild')) el('statChild').textContent = (data.child_sessions || 0).toLocaleString();
    if (el('statMessages')) el('statMessages').textContent = (data.total_messages || 0).toLocaleString();
    if (el('statActive')) el('statActive').textContent = (data.active_sessions || 0).toLocaleString();
    if (el('statTokens')) el('statTokens').textContent = formatTokenCount(data.total_tokens || 0);

    const srcDist = data.source_distribution || {};
    const srcCount = Object.keys(srcDist).length;
    if (el('statSources')) el('statSources').textContent = srcCount;
  } catch (e) {
    console.error('Failed to load session stats:', e);
  }
}

async function loadSessionList(source, offset) {
  currentSource = source || currentSource;
  const os = offset || 0;

  try {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(os) });
    if (currentSource) params.set('source', currentSource);

    const resp = await fetch(`./api/sessions/list?${params}`);
    const sessions = await resp.json();
    allSessions = sessions;

    const container = document.getElementById('sessionList');
    if (!container) return;

    const countEl = document.getElementById('sessionCount');
    if (countEl) countEl.textContent = `${sessions.length} 条`;

    if (sessions.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无会话记录</div>';
      return;
    }

    container.innerHTML = sessions.map(s => {
      const isActive = currentSessionId === s.id;
      const statusClass = s.ended_at ? (s.end_reason === 'error' ? 'tag-error' : 'tag-success') : 'tag-running';
      const statusText = s.ended_at ? (s.end_reason === 'error' ? '异常' : '已完成') : '执行中';
      const sourceTag = s.source ? `<span class="tag tag-source">${getSourceEmoji(s.source)} ${s.source}</span>` : '';
      const errorTag = (s.end_reason === 'error') ? '<span class="tag tag-error">异常</span>' : '';
      const tokens = ((s.input_tokens || 0) + (s.output_tokens || 0));

      return `
        <div class="session-item ${isActive ? 'active' : ''}" onclick="selectSession('${s.id}')">
          <div class="session-item-title">${escapeHtml(s.title || s.preview || s.id)}</div>
          <div class="session-item-meta">
            ${sourceTag}
            <span class="tag ${statusClass}">${statusText}</span>
            ${errorTag}
          </div>
          <div class="session-time">
            ${formatTime(s.started_at)} · 消息: ${s.message_count || 0} · ${formatTokenCount(tokens)} tokens
          </div>
        </div>
      `;
    }).join('');

    renderPagination(sessions.length);
  } catch (e) {
    console.error('Failed to load session list:', e);
  }
}

function renderPagination(loadedCount) {
  const container = document.getElementById('sessionPagination');
  if (!container) return;

  if (loadedCount < PAGE_SIZE) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <div style="display:flex;justify-content:center;padding:8px;gap:8px;">
      <button class="vw-btn-outline" onclick="loadSessionList(null, ${Math.max(0, currentPage * PAGE_SIZE - PAGE_SIZE)})" ${currentPage === 0 ? 'disabled' : ''}>上一页</button>
      <span style="color:#94a3b8;font-size:13px;line-height:32px;">第 ${currentPage + 1} 页</span>
      <button class="vw-btn-outline" onclick="loadSessionList(null, ${(currentPage + 1) * PAGE_SIZE})">下一页</button>
    </div>
  `;
}

async function searchSessions(query) {
  try {
    const params = new URLSearchParams({ q: query, limit: '20' });
    if (currentSource) params.set('source', currentSource);

    const resp = await fetch(`./api/sessions/search?${params}`);
    const results = await resp.json();

    const container = document.getElementById('sessionList');
    if (!container) return;

    const countEl = document.getElementById('sessionCount');
    if (countEl) countEl.textContent = `${results.length} 条搜索结果`;

    if (results.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">未找到匹配的会话</div>';
      return;
    }

    container.innerHTML = results.map(r => `
      <div class="session-item" onclick="selectSession('${r.session_id || ''}')">
        <div class="session-item-title">${escapeHtml(r.snippet || '搜索结果')}</div>
        <div class="session-item-meta">
          <span class="tag tag-source">${getSourceEmoji(r.source)} ${r.source || '--'}</span>
        </div>
        <div class="session-time">${formatTime(r.timestamp)}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to search sessions:', e);
  }
}

async function selectSession(sessionId) {
  if (!sessionId) return;
  currentSessionId = sessionId;

  document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
  if (event && event.currentTarget) event.currentTarget.classList.add('active');

  try {
    const resp = await fetch(`./api/sessions/detail/${sessionId}`);
    const data = await resp.json();

    if (data.error) {
      console.error('Session detail error:', data.error);
      return;
    }

    renderSessionDetail(data);
  } catch (e) {
    console.error('Failed to load session detail:', e);
  }
}

function renderSessionDetail(session) {
  const detailPanel = document.getElementById('detailPanel');
  if (!detailPanel) return;

  const messages = session.messages || [];
  const userMsg = messages.find(m => m.role === 'user');
  const assistantMsgs = messages.filter(m => m.role === 'assistant');
  const lastAssistant = assistantMsgs[assistantMsgs.length - 1];
  const toolCalls = messages.filter(m => m.role === 'tool');
  const systemMsgs = messages.filter(m => m.role === 'system');

  const entryPrompt = userMsg ? (userMsg.content || '').substring(0, 300) : '（无用户消息）';
  const finalResult = lastAssistant ? (lastAssistant.content || '').substring(0, 500) : '（等待响应）';
  const toolNames = [...new Set(toolCalls.map(m => m.tool_name).filter(Boolean))];
  const totalTokens = (session.input_tokens || 0) + (session.output_tokens || 0);
  const duration = session.ended_at && session.started_at ? (session.ended_at - session.started_at) : null;

  detailPanel.innerHTML = `
    <div class="detail-grid">
      <div class="detail-section">
        <div class="detail-section-title">入口提示</div>
        <div class="detail-content">${escapeHtml(entryPrompt)}</div>
      </div>
      <div class="detail-section">
        <div class="detail-section-title">最终结果</div>
        <div class="detail-content">${escapeHtml(finalResult)}</div>
      </div>
      <div class="detail-section">
        <div class="detail-section-title">Token 统计</div>
        <div class="detail-content token-stats">
          输入: ${(session.input_tokens || 0).toLocaleString()} · 输出: ${(session.output_tokens || 0).toLocaleString()}<br>
          总计: ${formatTokenCount(totalTokens)} tokens
          ${session.estimated_cost_usd ? ` · $${Number(session.estimated_cost_usd).toFixed(4)}` : ''}
        </div>
      </div>
      <div class="detail-section">
        <div class="detail-section-title">会话元数据</div>
        <div class="detail-content">
          来源: ${getSourceEmoji(session.source)} ${session.source || 'unknown'}<br>
          模型: ${session.model || 'unknown'}<br>
          持续时间: ${duration ? formatDuration(duration) : '--'}<br>
          消息数: ${messages.length} · 工具调用: ${toolCalls.length}
        </div>
      </div>
    </div>

    <div class="profile-section">
      <div class="profile-title">会话画像</div>
      <div class="profile-grid">
        <div class="profile-field">
          <div class="profile-label">来源</div>
          <div class="profile-value">${getSourceEmoji(session.source)} ${session.source || 'unknown'}</div>
        </div>
        <div class="profile-field">
          <div class="profile-label">模型</div>
          <div class="profile-value">${session.model || 'unknown'}</div>
        </div>
        <div class="profile-field">
          <div class="profile-label">状态</div>
          <div class="profile-value">
            ${session.ended_at
              ? (session.end_reason === 'error'
                ? '<span style="color:#ef4444;">❌ 异常</span>'
                : '<span style="color:#10b981;">✓ 已完成</span>')
              : '<span style="color:#f59e0b;">⏳ 执行中</span>'}
          </div>
        </div>
        <div class="profile-field">
          <div class="profile-label">持续时间</div>
          <div class="profile-value">${duration ? formatDuration(duration) : '--'}</div>
        </div>
        <div class="profile-field profile-tools">
          <div class="profile-label">工具调用链</div>
          <div class="tools-list">
            ${toolNames.length > 0
              ? toolNames.map(n => `<span class="tool-item">🔧 ${n}</span>`).join(' ▶ ')
              : '无工具调用'}
          </div>
        </div>
        <div class="profile-field profile-tools">
          <div class="profile-label">子会话</div>
          <div class="tools-list" id="childSessionsArea">加载中...</div>
        </div>
      </div>
    </div>

    ${messages.length > 0 ? `
    <div class="profile-section" style="margin-top: 16px;">
      <div class="profile-title">消息流水线</div>
      <div class="pipeline-trace" id="pipelineTrace">
        ${messages.map((msg, i) => {
          const roleIcon = { user: '👤', assistant: '🤖', system: '⚙️', tool: '🔧' }[msg.role] || '📌';
          const roleLabel = { user: '用户', assistant: '助手', system: '系统', tool: '工具' }[msg.role] || msg.role;
          const content = (msg.content || '').substring(0, 200);
          const isTool = msg.role === 'tool';
          const toolLabel = isTool ? `<span style="color:#f59e0b;font-size:11px;">${msg.tool_name || ''}</span>` : '';
          return `
            <div class="pipeline-node ${msg.role}" style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <span style="font-size:14px;">${roleIcon}</span>
              <div style="flex:1;min-width:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="font-size:12px;color:#94a3b8;">${roleLabel}</span>
                  ${toolLabel}
                </div>
                <div style="font-size:13px;color:#cbd5e1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(content)}</div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
    ` : ''}
  `;

  loadSessionTree(session.id);
}

async function loadSessionTree(sessionId) {
  const area = document.getElementById('childSessionsArea');
  if (!area) return;

  try {
    const resp = await fetch(`./api/sessions/tree/${sessionId}`);
    const tree = await resp.json();

    const children = tree.filter(s => s.id !== sessionId && s.parent_session_id === sessionId);
    if (children.length === 0) {
      area.textContent = '无子会话';
      return;
    }

    area.innerHTML = children.map(child => {
      const statusColor = child.end_reason === 'error' ? '#ef4444' : child.ended_at ? '#10b981' : '#f59e0b';
      const statusText = child.end_reason === 'error' ? '失败' : child.ended_at ? '完成' : '运行中';
      return `<span class="tool-item" style="cursor:pointer;border-color:${statusColor}30;color:${statusColor};" onclick="selectSession('${child.id}')" title="${escapeHtml(child.title || child.id)}">${getSourceEmoji(child.source)} ${escapeHtml((child.title || child.id).substring(0, 20))} [${statusText}]</span>`;
    }).join(' ');
  } catch (e) {
    area.textContent = '加载失败';
  }
}

function filterBySource(source) {
  currentSource = source || null;
  currentPage = 0;
  loadSessionList(source, 0);
}

function filterByStatus(status) {
  currentStatus = status || null;
  currentPage = 0;
  if (status === 'active') {
    const container = document.getElementById('sessionList');
    if (!container) return;
    document.querySelectorAll('.session-item').forEach(el => {
      const hasRunning = el.querySelector('.tag-running');
      el.style.display = (!status || hasRunning) ? '' : 'none';
    });
  } else if (status === 'completed') {
    document.querySelectorAll('.session-item').forEach(el => {
      const hasCompleted = el.querySelector('.tag-success');
      el.style.display = (!status || hasCompleted) ? '' : 'none';
    });
  } else if (status === 'error') {
    document.querySelectorAll('.session-item').forEach(el => {
      const hasError = el.querySelector('.tag-error');
      el.style.display = (!status || hasError) ? '' : 'none';
    });
  } else {
    document.querySelectorAll('.session-item').forEach(el => {
      el.style.display = '';
    });
  }
}

function exportSessions() {
  const data = allSessions.map(s => ({
    id: s.id,
    source: s.source,
    title: s.title || '',
    started_at: s.started_at_iso || '',
    ended_at: s.ended_at_iso || '',
    status: s.ended_at ? (s.end_reason === 'error' ? 'error' : 'completed') : 'active',
    messages: s.message_count || 0,
    tokens: (s.input_tokens || 0) + (s.output_tokens || 0),
  }));

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sessions_export_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
