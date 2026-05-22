var LOOP_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
};
var LOOP_STATE = {
  loops: [],
  selectedLoopId: '',
};

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function domSafeId(value) {
  return String(value || '').replace(/[^a-zA-Z0-9_-]/g, '-');
}

function loopFetchJSON(url) {
  return fetch(LOOP_CONFIG.apiBase + url)
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
}

function loopPostJSON(url, payload) {
  return fetch(LOOP_CONFIG.apiBase + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {}),
  }).then(function(r) {
    return r.json().catch(function() { return {}; }).then(function(data) {
      if (!r.ok) {
        throw new Error(data && data.error ? data.error : ('HTTP ' + r.status));
      }
      return data;
    });
  });
}

function showLoopBanner(message, isError) {
  var banner = document.getElementById('loop-action-banner');
  if (!banner) return;
  if (!message) {
    banner.style.display = 'none';
    banner.textContent = '';
    banner.style.borderLeft = '';
    banner.style.color = '';
    return;
  }
  banner.style.display = 'block';
  banner.style.borderLeft = isError ? '4px solid #ef4444' : '4px solid #22c55e';
  banner.style.color = isError ? '#fecaca' : '#bbf7d0';
  banner.textContent = message;
}

function loopSetText(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function formatStage(stage) {
  if (!stage) return '--';
  return String(stage).replace(/_/g, ' ');
}

function renderLoopMetrics(loop) {
  loopSetText('loop-count', LOOP_STATE.loops.length ? String(LOOP_STATE.loops.length) : '0');
  loopSetText('loop-stage-count', loop ? formatStage(loop.stage) : '--');
  loopSetText('loop-promise-count', loop ? String(loop.objectCount || 0) : '0');
  loopSetText('loop-followup-count', loop ? String(loop.followUpCount || 0) : '0');
}

function currentLoop() {
  return LOOP_STATE.loops.find(function(item) {
    return item.loopId === LOOP_STATE.selectedLoopId;
  }) || null;
}

function selectLoop(loopId) {
  LOOP_STATE.selectedLoopId = loopId;
  var loop = currentLoop();
  renderLoopMetrics(loop);
  renderLoopList(loop);
  renderLoopDetail(loop);
}

function renderLoopList(activeLoop) {
  var container = document.getElementById('loop-list');
  if (!container) return;
  if (!LOOP_STATE.loops.length) {
    container.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">📭</div><p>暂无 cycle 对象</p></div>';
    return;
  }
  container.innerHTML = LOOP_STATE.loops.map(function(loop) {
    var active = activeLoop && activeLoop.loopId === loop.loopId ? ' is-active' : '';
    return '<div class="loop-card' + active + '" onclick="selectLoop(\'' + escapeHtml(loop.loopId) + '\')">' +
      '<div class="loop-card-head">' +
        '<div>' +
          '<div class="loop-card-title">' + escapeHtml(loop.sourceJobName || '--') + '</div>' +
          '<div class="loop-card-subtitle">' + escapeHtml(loop.cycleType || '--') + ' · round ' + escapeHtml(loop.roundNumber || '--') + '</div>' +
        '</div>' +
        '<span class="cl-handoff-badge">' + escapeHtml(formatStage(loop.stage)) + '</span>' +
      '</div>' +
      '<p class="loop-card-summary">' + escapeHtml(loop.summary || '—') + '</p>' +
    '</div>';
  }).join('');
}

function renderLoopDetail(loop) {
  loopSetText('loop-detail-title', loop ? loop.sourceJobName : '暂无 cycle');
  loopSetText('loop-detail-summary', loop ? (loop.summary || '—') : '当前没有可展示的 cycle 对象。');
  loopSetText('loop-next-action', loop ? (loop.nextAction || '—') : '当前没有下一步动作。');

  var detailGrid = document.getElementById('loop-detail-grid');
  var evidenceList = document.getElementById('loop-evidence-list');
  if (!detailGrid || !evidenceList) return;

  if (!loop) {
    detailGrid.innerHTML = '';
    evidenceList.innerHTML = '';
    renderFeedbackInputs(null);
    renderMemoryCandidates(null);
    return;
  }

  detailGrid.innerHTML = [
    ['Stage', formatStage(loop.stage)],
    ['Owner', loop.stageOwner || '--'],
    ['Status', loop.status || '--'],
    ['Feedback', loop.feedbackStatus || '--'],
    ['Memory Candidate', loop.memoryCandidateStatus || '--'],
    ['Updated At', loop.updatedAt || '--'],
  ].map(function(item) {
    return '<div class="loop-detail-row"><span class="loop-detail-label">' + escapeHtml(item[0]) + '</span><span class="loop-detail-value">' + escapeHtml(item[1]) + '</span></div>';
  }).join('');

  evidenceList.innerHTML = (loop.evidenceRefs || []).map(function(ref) {
    return '<div class="loop-evidence-item">' + escapeHtml(ref) + '</div>';
  }).join('');

  renderFeedbackInputs(loop);
  renderMemoryCandidates(loop);
}

function renderFeedbackInputs(loop) {
  var container = document.getElementById('loop-feedback-list');
  if (!container) return;
  var items = (loop && loop.feedbackInputs) || [];
  if (!items.length) {
    container.innerHTML = '<div class="cl-empty"><p>当前没有待补的 feedback 输入。</p></div>';
    return;
  }

  container.innerHTML = items.map(function(item) {
    var domId = domSafeId(item.inputId);
    var evidenceValue = (item.lastSubmissionEvidenceRefs || item.sourceRefs || []).join(', ');
    var reasonValue = item.lastSubmissionReason || item.prefillText || '';
    var noteValue = item.lastSubmissionNote || '';
    var latestRecord = item.lastSubmissionAt
      ? '<div style="margin-top:8px;color:#94a3b8;font-size:12px;">最近留痕: ' + escapeHtml(item.lastSubmissionAt) + ' · boundary=' + escapeHtml(item.lastSubmissionBoundary || 'local-operator-queue') + '</div>'
      : '';
    var eventOptions = (item.allowedEventTypes || []).map(function(eventType) {
      var selected = (item.lastSubmissionEventType || item.defaultEventType) === eventType ? ' selected' : '';
      return '<option value="' + escapeHtml(eventType) + '"' + selected + '>' + escapeHtml(eventType) + '</option>';
    }).join('');
    return '<div class="loop-evidence-item" style="display:flex;flex-direction:column;gap:8px;">' +
      '<div><strong>' + escapeHtml(item.followUpKind || 'follow-up') + '</strong></div>' +
      '<div style="color:#94a3b8;font-size:12px;">mode=' + escapeHtml(item.inputMode || '--') + ' · status=' + escapeHtml(item.status || '--') + ' · next actor=' + escapeHtml(item.nextActor || '--') + '</div>' +
      '<div style="font-size:13px;">' + escapeHtml(item.prefillText || '—') + '</div>' +
      '<div style="display:grid;gap:8px;">' +
        '<div>' +
          '<label for="feedback-event-' + domId + '" style="display:block;margin-bottom:4px;color:#94a3b8;font-size:12px;">Event Type</label>' +
          '<select class="input" id="feedback-event-' + domId + '">' + eventOptions + '</select>' +
        '</div>' +
        '<div>' +
          '<label for="feedback-reason-' + domId + '" style="display:block;margin-bottom:4px;color:#94a3b8;font-size:12px;">Reason</label>' +
          '<input class="input" id="feedback-reason-' + domId + '" value="' + escapeHtml(reasonValue) + '" placeholder="一句话说明为什么记录这条输入">' +
        '</div>' +
        '<div>' +
          '<label for="feedback-note-' + domId + '" style="display:block;margin-bottom:4px;color:#94a3b8;font-size:12px;">Note</label>' +
          '<textarea class="input" id="feedback-note-' + domId + '" rows="3" placeholder="补充上下文或人工说明">' + escapeHtml(noteValue) + '</textarea>' +
        '</div>' +
        '<div>' +
          '<label for="feedback-evidence-' + domId + '" style="display:block;margin-bottom:4px;color:#94a3b8;font-size:12px;">Evidence Refs</label>' +
          '<input class="input" id="feedback-evidence-' + domId + '" value="' + escapeHtml(evidenceValue) + '" placeholder="逗号分隔，例如 promise:123, report:review-20260522.md">' +
        '</div>' +
      '</div>' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;">' +
        '<button type="button" class="btn btn-primary btn-sm" data-input-id="' + escapeHtml(item.inputId) + '" onclick="submitFeedbackInput(this.getAttribute(\'data-input-id\'))">记录输入</button>' +
      '</div>' +
      '<div style="color:#94a3b8;font-size:12px;">当前只把 operator 输入记到本地 queue，不直接调用 FlowMind 写接口。</div>' +
      latestRecord +
    '</div>';
  }).join('');
}

function renderMemoryCandidates(loop) {
  var container = document.getElementById('loop-memory-candidate-list');
  if (!container) return;
  var items = (loop && loop.memoryCandidates) || [];
  if (!items.length) {
    container.innerHTML = '<div class="cl-empty"><p>当前没有待确认的 memory candidate。</p></div>';
    return;
  }

  container.innerHTML = items.map(function(item) {
    var domId = domSafeId(item.candidateId);
    var evidenceValue = (item.decisionEvidenceRefs || item.sourceRefs || []).join(', ');
    var noteValue = item.decisionNote || '';
    var decisionMeta = item.decidedAt
      ? '<div style="margin-top:8px;color:#94a3b8;font-size:12px;">最近决策: ' + escapeHtml(item.status || '--') + ' @ ' + escapeHtml(item.decidedAt) + '</div>'
      : '';
    return '<div class="loop-evidence-item" style="display:flex;flex-direction:column;gap:8px;">' +
      '<div><strong>' + escapeHtml(item.candidateType || 'candidate') + '</strong></div>' +
      '<div style="color:#94a3b8;font-size:12px;">status=' + escapeHtml(item.status || '--') + ' · target=' + escapeHtml(item.proposedTarget || '--') + ' · plane=' + escapeHtml(item.targetMemoryPlane || '--') + '</div>' +
      '<div style="font-size:13px;">' + escapeHtml(item.proposedLesson || '—') + '</div>' +
      '<div>' +
        '<label for="memory-note-' + domId + '" style="display:block;margin-bottom:4px;color:#94a3b8;font-size:12px;">Decision Note</label>' +
        '<textarea class="input" id="memory-note-' + domId + '" rows="3" placeholder="说明为什么 confirm / reject / defer">' + escapeHtml(noteValue) + '</textarea>' +
      '</div>' +
      '<div>' +
        '<label for="memory-evidence-' + domId + '" style="display:block;margin-bottom:4px;color:#94a3b8;font-size:12px;">Evidence Refs</label>' +
        '<input class="input" id="memory-evidence-' + domId + '" value="' + escapeHtml(evidenceValue) + '" placeholder="逗号分隔，例如 promise:123, state:promises/reviews/daily-promise-review-state.json">' +
      '</div>' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;">' +
        '<button type="button" class="btn btn-primary btn-sm" data-candidate-id="' + escapeHtml(item.candidateId) + '" onclick="submitMemoryDecision(this.getAttribute(\'data-candidate-id\'), \'confirm\')">Confirm</button>' +
        '<button type="button" class="btn btn-secondary btn-sm" data-candidate-id="' + escapeHtml(item.candidateId) + '" onclick="submitMemoryDecision(this.getAttribute(\'data-candidate-id\'), \'reject\')">Reject</button>' +
        '<button type="button" class="btn btn-secondary btn-sm" data-candidate-id="' + escapeHtml(item.candidateId) + '" onclick="submitMemoryDecision(this.getAttribute(\'data-candidate-id\'), \'defer\')">Defer</button>' +
      '</div>' +
      '<div style="color:#94a3b8;font-size:12px;">确认结果只作用于 host-memory 候选留痕，不等于 repo-side canonical memory accept。</div>' +
      decisionMeta +
    '</div>';
  }).join('');
}

function collectInputValue(id) {
  var el = document.getElementById(id);
  return el ? String(el.value || '').trim() : '';
}

function refreshLoopSurface(preferredLoopId) {
  return loopFetchJSON('/api/collaboration/loops').then(function(data) {
    LOOP_STATE.loops = Array.isArray(data) ? data : [];
    var loop = null;
    if (preferredLoopId) {
      loop = LOOP_STATE.loops.find(function(item) { return item.loopId === preferredLoopId; }) || null;
    }
    if (!loop && LOOP_STATE.selectedLoopId) {
      loop = LOOP_STATE.loops.find(function(item) { return item.loopId === LOOP_STATE.selectedLoopId; }) || null;
    }
    if (!loop) {
      loop = LOOP_STATE.loops.length ? LOOP_STATE.loops[0] : null;
    }
    LOOP_STATE.selectedLoopId = loop ? loop.loopId : '';
    renderLoopMetrics(loop);
    renderLoopList(loop);
    renderLoopDetail(loop);
    return loop;
  }).catch(function(err) {
    LOOP_STATE.loops = [];
    LOOP_STATE.selectedLoopId = '';
    renderLoopMetrics(null);
    renderLoopList(null);
    renderLoopDetail(null);
    showLoopBanner(err && err.message ? err.message : 'Loop Surface 加载失败。', true);
    return null;
  });
}

function submitFeedbackInput(inputId) {
  var loop = currentLoop();
  var inputItem = loop && (loop.feedbackInputs || []).find(function(item) {
    return item.inputId === inputId;
  });
  if (!inputItem) {
    showLoopBanner('未找到目标 feedback input。', true);
    return;
  }

  var domId = domSafeId(inputId);
  var payload = {
    mode: inputItem.inputMode,
    eventType: collectInputValue('feedback-event-' + domId) || inputItem.defaultEventType,
    reason: collectInputValue('feedback-reason-' + domId),
    note: collectInputValue('feedback-note-' + domId),
    evidenceRefs: collectInputValue('feedback-evidence-' + domId),
  };
  if (!payload.reason) {
    showLoopBanner('反馈输入至少需要一条 reason。', true);
    return;
  }

  loopPostJSON('/api/collaboration/feedback-inputs/' + encodeURIComponent(inputId) + '/submit', payload)
    .then(function() {
      showLoopBanner('反馈输入已记录到本地 operator queue。', false);
      return refreshLoopSurface(loop ? loop.loopId : '');
    })
    .catch(function(err) {
      showLoopBanner(err && err.message ? err.message : '记录 feedback input 失败。', true);
    });
}

function submitMemoryDecision(candidateId, action) {
  var loop = currentLoop();
  var candidate = loop && (loop.memoryCandidates || []).find(function(item) {
    return item.candidateId === candidateId;
  });
  if (!candidate) {
    showLoopBanner('未找到目标 memory candidate。', true);
    return;
  }

  var domId = domSafeId(candidateId);
  var payload = {
    action: action,
    note: collectInputValue('memory-note-' + domId),
    evidenceRefs: collectInputValue('memory-evidence-' + domId),
  };

  loopPostJSON('/api/collaboration/memory-candidates/' + encodeURIComponent(candidateId) + '/decision', payload)
    .then(function() {
      showLoopBanner('memory candidate 决策已记录。', false);
      return refreshLoopSurface(loop ? loop.loopId : '');
    })
    .catch(function(err) {
      showLoopBanner(err && err.message ? err.message : '记录 memory candidate 决策失败。', true);
    });
}

function initLoopSurface() {
  showLoopBanner('', false);
  refreshLoopSurface('');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLoopSurface);
} else {
  initLoopSurface();
}
