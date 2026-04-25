let currentTeam = null;

document.addEventListener('DOMContentLoaded', () => {
  loadTeamList();
  loadMemories();
});

async function loadTeamList() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const resp = await fetch('./api/overview/teams', {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const teams = await resp.json();

    const container = document.querySelector('.team-sidebar') || document.querySelector('.team-list');
    if (!container) return;

    if (!Array.isArray(teams) || teams.length === 0) {
      container.innerHTML = '<div style="padding: 16px; text-align: center; color: #64748b;">暂无团队数据</div>';
      return;
    }

    container.innerHTML = teams.map((team, idx) => `
      <div class="team-item ${idx === 0 ? 'active' : ''}" onclick="selectTeam('${escapeHtml(team.name)}')" style="padding: 10px 14px; cursor: pointer; border-radius: 6px; margin-bottom: 4px; transition: background 0.2s; ${idx === 0 ? 'background: rgba(102,126,234,0.15);' : ''}" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='${idx === 0 ? 'rgba(102,126,234,0.15)' : 'transparent'}'">
        <div style="font-size: 14px; color: white; font-weight: 500;">${escapeHtml(team.name)}</div>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">
          ${team.memory_count || 0} 记忆 · ${team.role_count || 0} 角色
          ${team.session_count ? ` · ${team.session_count} 会话` : ''}
        </div>
      </div>
    `).join('');

    if (teams.length > 0) {
      selectTeam(teams[0].name);
    }
  } catch (e) {
    console.error('Failed to load team list:', e);
  }
}

async function selectTeam(teamName) {
  currentTeam = teamName;

  document.querySelectorAll('.team-item').forEach(el => {
    el.classList.remove('active');
    el.style.background = 'transparent';
  });
  event?.currentTarget?.classList.add('active');
  if (event?.currentTarget) event.currentTarget.style.background = 'rgba(102,126,234,0.15)';

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const resp = await fetch(`./api/memory/team/${encodeURIComponent(teamName)}`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const data = await resp.json();

    renderTeamMemory(data);
  } catch (e) {
    console.error('Failed to load team detail:', e);
    renderTeamMemory({ team: teamName, files: [] });
  }
}

function renderTeamMemory(data) {
  const contentArea = document.querySelector('.memory-content') || document.querySelector('.team-content');
  if (!contentArea) return;

  const files = data.files || [];

  if (files.length === 0) {
    contentArea.innerHTML = `
      <div style="padding: 24px; text-align: center; color: #64748b;">
        <div style="font-size: 32px; margin-bottom: 12px;">📁</div>
        <div>团队 "${escapeHtml(data.team || currentTeam)}" 暂无记忆文件</div>
        <div style="font-size: 12px; margin-top: 8px;">该团队尚未创建共享记忆</div>
      </div>
    `;
    return;
  }

  contentArea.innerHTML = `
    <div style="margin-bottom: 20px;">
      <h3 style="font-size: 16px; font-weight: 600; color: white; margin-bottom: 8px;">📝 ${escapeHtml(data.team)} - 团队记忆</h3>
      <div style="font-size: 12px; color: #94a3b8;">共 ${files.length} 个记忆文件</div>
    </div>
    <div style="display: flex; flex-direction: column; gap: 12px;">
      ${files.map(file => `
        <div class="card" style="padding: 16px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <h4 style="font-size: 14px; font-weight: 600; color: white; margin: 0;">${escapeHtml(file.name)}</h4>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span style="font-size: 11px; color: #64748b;">${formatSize(file.size || 0)}</span>
              <button onclick="editMemoryFile('${escapeHtml(data.team)}/${escapeHtml(file.path)}')" style="font-size: 11px; padding: 2px 8px; background: rgba(102,126,234,0.15); color: #667eea; border: 1px solid #667eea33; border-radius: 4px; cursor: pointer;">编辑</button>
            </div>
          </div>
          <div style="font-size: 12px; color: #94a3b8; line-height: 1.6; max-height: 120px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml((file.content || '').substring(0, 500))}${(file.content || '').length > 500 ? '...' : ''}</div>
        </div>
      `).join('')}
    </div>
  `;
}

async function loadMemories() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const resp = await fetch('./api/overview/memories', {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const memories = await resp.json();

    const container = document.querySelector('.memory-grid') || document.querySelector('.memories-list');
    if (!container || !Array.isArray(memories) || memories.length === 0) return;

    container.innerHTML = memories.slice(0, 12).map(mem => `
      <div class="card" style="padding: 12px;">
        <h4 style="font-size: 13px; font-weight: 600; color: white; margin-bottom: 4px;">${escapeHtml(mem.name)}</h4>
        <p style="font-size: 11px; color: #94a3b8; line-height: 1.4; margin: 0;">${escapeHtml(mem.preview)}</p>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load memories:', e);
  }
}

async function editMemoryFile(filePath) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    const resp = await fetch(`./api/memory/file/${encodeURIComponent(filePath)}`, { signal: controller.signal });
    clearTimeout(timeoutId);
    const data = await resp.json();

    if (data.error) {
      alert('无法加载文件: ' + data.error);
      return;
    }

    const contentArea = document.querySelector('.memory-content') || document.querySelector('.team-content');
    if (!contentArea) return;

    contentArea.innerHTML = `
      <div style="margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h3 style="font-size: 16px; font-weight: 600; color: white; margin: 0 0 4px;">编辑: ${escapeHtml(filePath.split('/').pop())}</h3>
          <div style="font-size: 12px; color: #64748b;">${escapeHtml(filePath)} · ${formatSize(data.size || 0)}</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button onclick="saveMemoryFile('${escapeHtml(filePath)}')" style="padding: 6px 16px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">保存</button>
          <button onclick="selectTeam('${escapeHtml(currentTeam || '')}')" style="padding: 6px 16px; background: #334155; color: #94a3b8; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">取消</button>
        </div>
      </div>
      <textarea id="memoryEditor" style="width: 100%; min-height: 400px; background: #0f172a; color: #e2e8f0; border: 1px solid #334155; border-radius: 8px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.6; resize: vertical; tab-size: 2;">${escapeHtml(data.content || '')}</textarea>
    `;
  } catch (e) {
    alert('加载文件失败: ' + e.message);
  }
}

async function saveMemoryFile(filePath) {
  const editor = document.getElementById('memoryEditor');
  if (!editor) return;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    const resp = await fetch('./api/memory/update', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: filePath, content: editor.value }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    const data = await resp.json();

    if (data.error) {
      alert('保存失败: ' + data.error);
    } else {
      alert('保存成功' + (data.backup ? ` (备份: ${data.backup})` : ''));
      if (currentTeam) selectTeam(currentTeam);
    }
  } catch (e) {
    alert('保存失败: ' + e.message);
  }
}

