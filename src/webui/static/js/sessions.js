/**
 * Sessions JavaScript - 会话流水线索引
 * 数据源: /api/sessions/* (读取 state.db + FTS5搜索)
 */

let currentSessionId = null;
let currentSource = null;
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
  loadSessionStats();
  loadSessionList();
  initSearchHandler();
});

function initSearchHandler() {
  const searchInput = document.querySelector('.session-search') || document.querySelector('input[placeholder*="搜索"]');
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

async function loadSessionStats() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/sessions/stats');
    const data = await resp.json();

    const statNumbers = document.querySelectorAll('.stat-number');
    const statLabels = document.querySelectorAll('.stat-label');

    const mappings = [
      { value: data.total_sessions || 0, label: '会话总数' },
      { value: data.child_sessions || 0, label: '子会话' },
      { value: data.total_messages || 0, label: '消息总数' },
      { value: data.active_sessions || 0, label: '活跃会话' },
    ];

    mappings.forEach((m, i) => {
      if (statNumbers[i]) statNumbers[i].textContent = m.value.toLocaleString();
      if (statLabels[i]) statLabels[i].textContent = m.label;
    });

    const srcDist = data.source_distribution || {};
    const srcContainer = document.querySelector('.source-distribution') || document.querySelectorAll('.stat-item')[4];
    if (srcContainer) {
      const total = Object.values(srcDist).reduce((a, b) => a + b, 0);
      const parts = Object.entries(srcDist).map(([k, v]) => `${k}: ${v}`).join(' · ');
      if (statNumbers[4]) statNumbers[4].textContent = total.toLocaleString();
      if (statLabels[4]) statLabels[4].textContent = '来源分布';
    }
  } catch (e) {
    console.error('Failed to load session stats:', e);
  }
}

async function loadSessionList(source) {
  currentSource = source || null;
  try {
    const params = new URLSearchParams({ limit: '30' });
    if (source) params.set('source', source);

    const resp = await fetch(window.APP_BASE + `/api/sessions/list?${params}`);
    const sessions = await resp.json();

    const container = document.querySelector('.session-list') || document.querySelector('.session-items');
    if (!container) return;

    if (sessions.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无会话记录</div>';
      return;
    }

    container.innerHTML = sessions.map(s => {
      const isActive = currentSessionId === s.id;
      const statusTag = s.ended_at
        ? '<span class="tag tag-success">已完成</span>'
        : '<span class="tag tag-running">执行中</span>';
      const sourceTag = s.source
        ? `<span class="tag tag-source">${getSourceEmoji(s.source)} ${s.source}</span>`
        : '';
      const errorTag = (s.end_reason === 'error')
        ? '<span class="tag tag-error">异常</span>'
        : '';

      return `
        <div class="session-item ${isActive ? 'active' : ''}" onclick="selectSession('${s.id}')">
          <div class="session-title">${escapeHtml(s.title || s.preview || s.id)}</div>
          <div class="session-desc">${escapeHtml(s.preview || '')}</div>
          <div class="session-tags">
            ${sourceTag}${errorTag}${statusTag}
          </div>
          <div class="session-meta">
            ${formatTime(s.started_at)} · 消息: ${s.message_count || 0} · Token: ${((s.input_tokens || 0) + (s.output_tokens || 0)).toLocaleString()}
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Failed to load session list:', e);
  }
}

async function searchSessions(query) {
  try {
    const params = new URLSearchParams({ q: query, limit: '20' });
    if (currentSource) params.set('source', currentSource);

    const resp = await fetch(window.APP_BASE + `/api/sessions/search?${params}`);
    const results = await resp.json();

    const container = document.querySelector('.session-list') || document.querySelector('.session-items');
    if (!container) return;

    if (results.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">未找到匹配的会话</div>';
      return;
    }

    container.innerHTML = results.map(r => `
      <div class="session-item" onclick="selectSession('${r.session_id || ''}')">
        <div class="session-title">${escapeHtml(r.snippet || r.content?.substring(0, 80) || '搜索结果')}</div>
        <div class="session-meta">
          来源: ${r.source || '--'} · ${formatTime(r.timestamp)}
        </div>
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
    const resp = await fetch(window.APP_BASE + `/api/sessions/detail/${sessionId}`);
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
  const detailPanel = document.querySelector('.detail-panel');
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

  detailPanel.innerHTML = `
    <div class="detail-section">
      <div class="detail-header">会话详情</div>
      <div class="detail-grid">
        <div class="detail-col">
          <div class="detail-label">入口提示</div>
          <div class="detail-value">${escapeHtml(entryPrompt)}</div>
        </div>
        <div class="detail-col">
          <div class="detail-label">最终结果</div>
          <div class="detail-value">${escapeHtml(finalResult)}</div>
        </div>
        <div class="detail-col">
          <div class="detail-label">系统提示</div>
          <div class="detail-value text-muted">${systemMsgs.length > 0 ? escapeHtml((systemMsgs[0].content || '').substring(0, 200)) + '...' : '无'}</div>
        </div>
        <div class="detail-col">
          <div class="detail-label">Token 统计</div>
          <div class="detail-value mono-small">
            输入: ${(session.input_tokens || 0).toLocaleString()} · 输出: ${(session.output_tokens || 0).toLocaleString()}<br>
            总计: ${((session.input_tokens || 0) + (session.output_tokens || 0)).toLocaleString()} tokens
          </div>
        </div>
      </div>
    </div>

    <div class="session-profile">
      <div class="profile-header">会话画像</div>
      <div class="profile-grid">
        <div class="profile-item">
          <span class="profile-label">来源：</span>
          <span class="tag tag-source">${getSourceEmoji(session.source)} ${session.source || 'unknown'}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">模型：</span>
          <span class="profile-value">${session.model || 'unknown'}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">状态：</span>
          ${session.ended_at
            ? '<span class="tag tag-success">✓ 已完成</span>'
            : '<span class="tag tag-running">执行中</span>'}
        </div>
        <div class="profile-item">
          <span class="profile-label">消息数：</span>
          <span class="profile-value">${messages.length}</span>
        </div>
        <div class="profile-item full-width">
          <span class="profile-label">工具调用链：</span>
          <span class="tools-list">${toolNames.length > 0 ? toolNames.map(n => `${n} ▶`).join(' ') : '无工具调用'}</span>
        </div>
        <div class="profile-item full-width">
          <span class="profile-label">子会话：</span>
          <span class="tools-list" id="childSessionsArea">加载中...</span>
        </div>
      </div>
    </div>
  `;

  loadSessionTree(session.id);
}

async function loadSessionTree(sessionId) {
  const area = document.getElementById('childSessionsArea');
  if (!area) return;

  try {
    const resp = await fetch(window.APP_BASE + `/api/sessions/tree/${sessionId}`);
    const tree = await resp.json();

    const children = tree.filter(s => s.id !== sessionId && s.parent_session_id === sessionId);
    if (children.length === 0) {
      area.textContent = '无子会话';
      return;
    }

    area.innerHTML = children.map(child => {
      const statusColor = child.end_reason === 'error' ? '#ef4444' : child.ended_at ? '#10b981' : '#f59e0b';
      const statusText = child.end_reason === 'error' ? '失败' : child.ended_at ? '完成' : '运行中';
      return `<span style="display: inline-block; padding: 2px 8px; margin: 2px; background: ${statusColor}15; color: ${statusColor}; border-radius: 4px; font-size: 11px; cursor: pointer;" onclick="selectSession('${child.id}')" title="${escapeHtml(child.title || child.id)}">${getSourceEmoji(child.source)} ${escapeHtml((child.title || child.id).substring(0, 20))} [${statusText}]</span>`;
    }).join(' ');
  } catch (e) {
    area.textContent = '加载失败';
  }
}

function filterBySource(source) {
  loadSessionList(source);
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

function getSourceEmoji(source) {
  if (typeof window.getSourceEmoji === 'function') return window.getSourceEmoji(source);
  const map = { cli: '🖥️', cron: '⏰', telegram: '📱', discord: '💬', feishu: '🐦', slack: '💼', api_server: '🔌', acp: '📝' };
  return map[source] || '📡';
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
