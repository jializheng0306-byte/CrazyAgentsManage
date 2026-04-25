let currentSkill = null;
let allSkills = [];
let allCategories = [];
let currentCategory = 'all';

document.addEventListener('DOMContentLoaded', () => {
  loadSkillsList();
});

async function loadSkillsList() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const resp = await fetch('./api/skills/list', {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const data = await resp.json();

    allSkills = data.skills || [];
    allCategories = data.categories || [];

    const statValues = document.querySelectorAll('.stat-value');
    if (statValues[0]) statValues[0].textContent = data.total || allSkills.length;

    renderCategoryFilter();
    renderSkillsGrid();
  } catch (e) {
    console.error('Failed to load skills list:', e);
  }
}

function renderCategoryFilter() {
  const filterBar = document.getElementById('categoryFilter');
  if (!filterBar) return;

  let html = `<button class="btn ${currentCategory === 'all' ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="filterByCategory('all')">全部 (${allSkills.length})</button>`;
  for (const cat of allCategories) {
    const active = currentCategory === cat.name;
    html += `<button class="btn ${active ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="filterByCategory('${escapeHtml(cat.name)}')" title="${escapeHtml(cat.name)}">${escapeHtml(cat.display)} (${cat.count})</button>`;
  }
  filterBar.innerHTML = html;
}

function filterByCategory(category) {
  currentCategory = category;
  renderCategoryFilter();
  renderSkillsGrid();
}

function renderSkillsGrid() {
  const container = document.querySelector('.skills-list') || document.querySelector('.skills-grid');
  if (!container) return;

  let filtered = allSkills;
  if (currentCategory !== 'all') {
    filtered = allSkills.filter(s => s.category === currentCategory);
  }

  if (filtered.length === 0) {
    container.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无已安装技能</div>';
    return;
  }

  container.innerHTML = filtered.map(skill => {
    const catBadge = skill.category_display
      ? `<span style="font-size: 10px; padding: 2px 6px; background: #667eea22; color: #667eea; border-radius: 4px; margin-right: 4px;">${escapeHtml(skill.category_display)}</span>`
      : '';
    const configBadge = skill.has_config
      ? '<span style="font-size: 10px; padding: 2px 6px; background: #10b98122; color: #10b981; border-radius: 4px;">已配置</span>'
      : '';

    return `
      <div class="card skill-card" style="padding: 16px; cursor: pointer; transition: border-color 0.2s;" onclick="selectSkill('${escapeHtml(skill.category)}/${escapeHtml(skill.name)}')" onmouseover="this.style.borderColor='#667eea'" onmouseout="this.style.borderColor=''">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <h4 style="font-size: 14px; font-weight: 600; color: white; margin: 0;">${escapeHtml(skill.name)}</h4>
          <div>${catBadge}${configBadge}</div>
        </div>
        <p style="font-size: 12px; color: #94a3b8; line-height: 1.4; margin: 0;">${escapeHtml(skill.description)}</p>
      </div>
    `;
  }).join('');

  if (filtered.length > 0 && !currentSkill) {
    selectSkill(filtered[0].category + '/' + filtered[0].name);
  }
}

async function selectSkill(skillPath) {
  currentSkill = skillPath;

  document.querySelectorAll('.skill-card').forEach(el => {
    el.style.borderColor = '';
  });

  const skillName = skillPath.includes('/') ? skillPath.split('/').pop() : skillPath;
  const category = skillPath.includes('/') ? skillPath.split('/')[0] : '';

  const skillInfo = allSkills.find(s => s.name === skillName && (!category || s.category === category));

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);
    const resp = await fetch(`./api/skills/detail/${encodeURIComponent(skillPath)}`, { signal: controller.signal });
    clearTimeout(timeoutId);
    const data = await resp.json();

    if (data.error) {
      renderSkillDetail({ name: skillName, content: skillInfo?.description || '技能详情加载失败', size: 0, category_display: skillInfo?.category_display || '' });
      return;
    }

    renderSkillDetail({ ...data, category_display: skillInfo?.category_display || '', category: skillInfo?.category || '' });
  } catch (e) {
    console.error('Failed to load skill detail:', e);
    renderSkillDetail({ name: skillName, content: skillInfo?.description || '加载失败', size: 0, category_display: skillInfo?.category_display || '' });
  }
}

function renderSkillDetail(skill) {
  const container = document.querySelector('.skill-detail') || document.querySelector('.skill-content');
  if (!container) return;

  const content = skill.content || '';
  const lines = content.split('\n');
  let title = skill.name;
  let description = '';

  for (const line of lines.slice(0, 10)) {
    if (line.startsWith('# ')) {
      title = line.substring(2).trim();
    } else if (line.startsWith('## ') && !description) {
      description = line.substring(3).trim();
    }
  }

  let renderedContent = escapeHtml(content);
  renderedContent = renderedContent.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre style="background: #0d1117; border: 1px solid #1f2937; border-radius: 6px; padding: 12px; overflow-x: auto; font-size: 12px; line-height: 1.5;"><code>${code}</code></pre>`;
  });
  renderedContent = renderedContent.replace(/^### (.+)$/gm, '<h3 style="font-size: 15px; font-weight: 600; color: white; margin: 16px 0 8px;">$1</h3>');
  renderedContent = renderedContent.replace(/^## (.+)$/gm, '<h2 style="font-size: 16px; font-weight: 600; color: #667eea; margin: 20px 0 10px;">$1</h2>');
  renderedContent = renderedContent.replace(/^# (.+)$/gm, '<h1 style="font-size: 20px; font-weight: 700; color: white; margin: 0 0 16px;">$1</h1>');
  renderedContent = renderedContent.replace(/\*\*(.+?)\*\*/g, '<strong style="color: white;">$1</strong>');
  renderedContent = renderedContent.replace(/^- (.+)$/gm, '<div style="padding-left: 16px; position: relative; margin: 4px 0;"><span style="position: absolute; left: 4px; color: #667eea;">•</span>$1</div>');
  renderedContent = renderedContent.replace(/\n\n/g, '<br><br>');
  renderedContent = renderedContent.replace(/\n/g, '<br>');

  const catBadge = skill.category_display
    ? `<span style="font-size: 11px; padding: 3px 8px; background: #667eea22; color: #667eea; border-radius: 4px;">${escapeHtml(skill.category_display)}</span>`
    : '';

  container.innerHTML = `
    <div style="margin-bottom: 20px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <h3 style="font-size: 18px; font-weight: 600; color: white; margin: 0;">${escapeHtml(title)}</h3>
        ${catBadge}
      </div>
      ${description ? `<p style="font-size: 13px; color: #94a3b8;">${escapeHtml(description)}</p>` : ''}
      <div style="font-size: 11px; color: #64748b; margin-top: 4px;">${formatSize(skill.size || 0)}</div>
    </div>
    <div style="font-size: 13px; color: #cbd5e1; line-height: 1.7;">
      ${renderedContent}
    </div>
  `;
}

