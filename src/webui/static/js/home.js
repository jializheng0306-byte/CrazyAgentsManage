document.addEventListener('DOMContentLoaded', () => {
  loadOverviewStats();
  loadTeamCards();
  loadMemoryGrid();
  loadRoleGrid();
});

async function loadOverviewStats() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/overview/stats');
    const data = await resp.json();

    const statValues = document.querySelectorAll('.stat-value');
    const statLabels = document.querySelectorAll('.stat-label');

    const mappings = [
      { value: data.teams || 0, label: '团队' },
      { value: data.roles || 0, label: '角色' },
      { value: data.memory_files || 0, label: '记忆文件' },
      { value: data.team_memories || 0, label: '团队记忆' },
      { value: data.sessions || 0, label: '会话总数' },
    ];

    mappings.forEach((m, i) => {
      if (statValues[i]) statValues[i].textContent = m.value;
      if (statLabels[i]) statLabels[i].textContent = m.label;
    });
  } catch (e) {
    console.error('Failed to load overview stats:', e);
  }
}

async function loadTeamCards() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/overview/teams');
    const teams = await resp.json();

    const container = document.getElementById('teamCards');
    if (!container) return;

    if (teams.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无团队数据</div>';
      return;
    }

    container.innerHTML = teams.map(team => `
      <div class="team-card" onclick="window.location.href='/team-memory'" style="cursor: pointer;">
        <div class="team-card-header">
          <div class="team-name">🏢 ${escapeHtml(team.name)}</div>
          <div class="team-stats-right">
            <span><span class="team-stat-num">${team.memory_count || 0}</span> 记忆</span>
            <span><span class="team-stat-num">${team.role_count || 0}</span> 角色</span>
            ${team.session_count ? `<span><span class="team-stat-num">${team.session_count}</span> 会话</span>` : ''}
          </div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load team cards:', e);
  }
}

async function loadMemoryGrid() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/overview/memories');
    const memories = await resp.json();

    const container = document.getElementById('memoryGrid');
    if (!container) return;

    if (memories.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无记忆文件</div>';
      return;
    }

    container.innerHTML = memories.slice(0, 12).map(mem => `
      <div class="memory-card">
        <div class="memory-icon">📄</div>
        <div class="memory-title">${escapeHtml(mem.name)}</div>
        <div class="memory-desc">${escapeHtml(mem.preview)}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load memory grid:', e);
  }
}

async function loadRoleGrid() {
  try {
    const resp = await fetch(window.APP_BASE + '/api/overview/teams');
    const teams = await resp.json();

    const container = document.getElementById('roleGrid');
    if (!container) return;

    if (teams.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无角色数据</div>';
      return;
    }

    const allRoles = [];
    for (const team of teams) {
      if (team.role_count > 0) {
        const detailResp = await fetch(window.APP_BASE + `/api/memory/team/${encodeURIComponent(team.name)}`);
        const detail = await detailResp.json();
        const files = detail.files || [];
        files.forEach(f => {
          allRoles.push({
            name: f.name,
            team: team.name,
            size: f.size || 0,
            preview: (f.content || '').substring(0, 100).replace('\n', ' '),
          });
        });
      }
    }

    if (allRoles.length === 0) {
      container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无角色记忆</div>';
      return;
    }

    container.innerHTML = allRoles.slice(0, 16).map(role => `
      <div class="role-card">
        <div class="role-header">
          <span class="role-name">🎯 ${escapeHtml(role.name)}</span>
          <span class="role-badge">${role.team}</span>
        </div>
        <div class="role-desc">${escapeHtml(role.preview)}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load role grid:', e);
  }
}

function expandAll() {
  document.querySelectorAll('.team-card, .memory-card, .role-card').forEach(el => {
    el.style.display = '';
  });
}

function collapseAll() {
  document.querySelectorAll('.memory-card, .role-card').forEach(el => {
    el.style.display = 'none';
  });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
