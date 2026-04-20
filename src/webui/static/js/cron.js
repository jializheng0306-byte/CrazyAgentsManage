/**
 * Cron JavaScript - 定时任务管理
 * 数据源: /api/cron/* (读取 cron/jobs.json + 执行操作)
 */

document.addEventListener('DOMContentLoaded', () => {
  loadCronJobs();
});

async function loadCronJobs() {
  try {
    const resp = await fetch('/api/cron/list');
    const jobs = await resp.json();

    const statsGrid = document.querySelector('.stats-grid');
    if (statsGrid) {
      const running = jobs.filter(j => j.enabled && j.state !== 'paused').length;
      const paused = jobs.filter(j => j.state === 'paused').length;
      const failed = jobs.filter(j => j.last_status === 'error').length;

      statsGrid.innerHTML = `
        <div class="stat-card">
          <div class="stat-value">${jobs.length}</div>
          <div class="stat-label">任务总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${running}</div>
          <div class="stat-label">运行中</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${paused}</div>
          <div class="stat-label">已暂停</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${failed}</div>
          <div class="stat-label">失败</div>
        </div>
      `;
    }

    const taskList = document.querySelector('.cron-task-list');
    if (!taskList) {
      const container = document.querySelector('.card .section-title');
      if (container) {
        const parent = container.closest('.card');
        if (parent) {
          const listDiv = document.createElement('div');
          listDiv.className = 'cron-task-list';
          listDiv.id = 'cronTaskList';
          parent.appendChild(listDiv);
        }
      }
    }

    const listEl = document.getElementById('cronTaskList') || document.querySelector('.cron-task-list');
    if (!listEl) return;

    if (jobs.length === 0) {
      listEl.innerHTML = '<div style="padding: 24px; text-align: center; color: #64748b;">暂无定时任务</div>';
      return;
    }

    listEl.innerHTML = jobs.map(job => {
      const stateClass = job.state === 'paused' ? 'paused' : (job.last_status === 'error' ? 'failed' : 'active');
      const stateText = job.state === 'paused' ? '已暂停' : (job.last_status === 'error' ? '失败' : '运行中');
      const statusDot = job.state === 'paused' ? 'paused' : (job.enabled ? 'active' : 'pending');

      return `
        <div class="cron-task-card">
          <div class="cron-task-header">
            <div class="cron-task-title">
              <span class="status-dot ${statusDot}"></span>
              <span class="cron-task-name">${escapeHtml(job.name || job.id)}</span>
              <span class="cron-task-role">${job.skills?.[0] || ''}</span>
            </div>
            <div class="cron-task-status ${stateClass}">${stateText}</div>
          </div>
          <div class="cron-task-body">
            <div class="cron-task-row">
              <span class="cron-task-label">执行计划：</span>
              <span class="cron-task-value">${escapeHtml(job.schedule_display || job.schedule?.display || '--')}</span>
            </div>
            <div class="cron-task-row">
              <span class="cron-task-label">上次执行：</span>
              <span class="cron-task-value">${job.last_run_at || '--'}</span>
              ${job.last_status === 'ok'
                ? '<span class="cron-task-value success">✓ 执行成功</span>'
                : job.last_status === 'error'
                  ? '<span class="cron-task-value error">✗ 执行失败</span>'
                  : ''}
            </div>
            <div class="cron-task-row">
              <span class="cron-task-label">下次执行：</span>
              <span class="cron-task-value">${job.next_run_at || '--'}</span>
            </div>
            <div class="cron-task-row">
              <span class="cron-task-label">投递目标：</span>
              <span style="color: var(--color-text-muted);">${escapeHtml(job.deliver || 'local')}</span>
            </div>
          </div>
          <div class="cron-task-actions">
            ${job.state === 'paused'
              ? `<button class="btn btn-primary btn-sm" onclick="resumeJob('${job.id}')">恢复任务</button>`
              : `<button class="btn btn-secondary btn-sm" onclick="pauseJob('${job.id}')">暂停任务</button>`
            }
            <button class="btn btn-primary btn-sm" onclick="runJob('${job.id}')">立即执行</button>
            <button class="btn btn-secondary btn-sm" onclick="viewOutput('${job.id}')">查看日志</button>
            <button class="btn btn-secondary btn-sm" onclick="deleteJob('${job.id}')" style="color: #ef4444;">删除</button>
          </div>
        </div>
      `;
    }).join('');

  } catch (e) {
    console.error('Failed to load cron jobs:', e);
  }
}

async function pauseJob(jobId) {
  try {
    const resp = await fetch(`/api/cron/${jobId}/pause`, { method: 'POST' });
    const data = await resp.json();
    if (data.error) {
      alert('暂停失败: ' + data.error);
    } else {
      loadCronJobs();
    }
  } catch (e) {
    alert('操作失败: ' + e.message);
  }
}

async function resumeJob(jobId) {
  try {
    const resp = await fetch(`/api/cron/${jobId}/resume`, { method: 'POST' });
    const data = await resp.json();
    if (data.error) {
      alert('恢复失败: ' + data.error);
    } else {
      loadCronJobs();
    }
  } catch (e) {
    alert('操作失败: ' + e.message);
  }
}

async function runJob(jobId) {
  if (!confirm('确定要立即执行此任务吗？')) return;
  try {
    const resp = await fetch(`/api/cron/${jobId}/run`, { method: 'POST' });
    const data = await resp.json();
    if (data.error) {
      alert('执行失败: ' + data.error);
    } else {
      alert('任务已触发执行');
      loadCronJobs();
    }
  } catch (e) {
    alert('操作失败: ' + e.message);
  }
}

async function deleteJob(jobId) {
  if (!confirm('确定要删除此任务吗？此操作不可恢复。')) return;
  try {
    const resp = await fetch(`/api/cron/${jobId}`, { method: 'DELETE' });
    const data = await resp.json();
    if (data.error) {
      alert('删除失败: ' + data.error);
    } else {
      loadCronJobs();
    }
  } catch (e) {
    alert('操作失败: ' + e.message);
  }
}

async function viewOutput(jobId) {
  try {
    const resp = await fetch(`/api/cron/${jobId}/output`);
    const outputs = await resp.json();

    if (outputs.length === 0) {
      alert('暂无执行输出');
      return;
    }

    const latest = outputs[0];
    const w = window.open('', '_blank');
    w.document.write(`<pre style="background:#111;color:#e2e8f0;padding:24px;font-family:monospace;font-size:13px;white-space:pre-wrap;">${escapeHtml(latest.content)}</pre>`);
    w.document.title = `输出: ${latest.filename}`;
  } catch (e) {
    alert('加载输出失败: ' + e.message);
  }
}

function showCreateJobForm() {
  const modal = document.getElementById('createJobModal');
  if (modal) {
    modal.style.display = 'flex';
  }
}

function hideCreateJobForm() {
  const modal = document.getElementById('createJobModal');
  if (modal) {
    modal.style.display = 'none';
  }
  const name = document.getElementById('cronName');
  const schedule = document.getElementById('cronSchedule');
  const prompt = document.getElementById('cronPrompt');
  if (name) name.value = '';
  if (schedule) schedule.value = '';
  if (prompt) prompt.value = '';
}

async function createJob() {
  const name = document.getElementById('cronName')?.value?.trim();
  const schedule = document.getElementById('cronSchedule')?.value?.trim();
  const prompt = document.getElementById('cronPrompt')?.value?.trim();
  const deliver = document.getElementById('cronDeliver')?.value || 'local';

  if (!schedule || !prompt) {
    alert('执行计划和提示词为必填项');
    return;
  }

  try {
    const resp = await fetch('/api/cron/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, schedule, prompt, deliver }),
    });
    const data = await resp.json();

    if (data.error) {
      alert('创建失败: ' + data.error);
    } else {
      hideCreateJobForm();
      loadCronJobs();
    }
  } catch (e) {
    alert('创建失败: ' + e.message);
  }
}

