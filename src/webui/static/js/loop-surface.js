var LOOP_CONFIG = {
  apiBase: (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })(),
};

function loopFetchJSON(url) {
  return fetch(LOOP_CONFIG.apiBase + url)
    .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
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
  loopSetText('loop-count', loop ? '1' : '0');
  loopSetText('loop-stage-count', loop ? formatStage(loop.stage) : '--');
  loopSetText('loop-promise-count', loop && loop.classifiedCounts ? String(loop.classifiedCounts.total || 0) : '0');
  loopSetText('loop-followup-count', loop && loop.summary ? String((loop.summary.match(/needs_follow_up=(\\d+)/) || [])[1] || '0') : '0');
}

function renderLoopList(loop) {
  var container = document.getElementById('loop-list');
  if (!container) return;
  if (!loop) {
    container.innerHTML = '<div class="cl-empty"><div class="cl-empty-icon">📭</div><p>暂无 cycle 对象</p></div>';
    return;
  }
  container.innerHTML =
    '<div class="loop-card is-active">' +
      '<div class="loop-card-head">' +
        '<div>' +
          '<div class="loop-card-title">' + loop.sourceJobName + '</div>' +
          '<div class="loop-card-subtitle">' + loop.cycleType + ' · round ' + loop.roundNumber + '</div>' +
        '</div>' +
        '<span class="cl-handoff-badge">' + formatStage(loop.stage) + '</span>' +
      '</div>' +
      '<p class="loop-card-summary">' + (loop.summary || '—') + '</p>' +
    '</div>';
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
    return '<div class="loop-detail-row"><span class="loop-detail-label">' + item[0] + '</span><span class="loop-detail-value">' + item[1] + '</span></div>';
  }).join('');

  evidenceList.innerHTML = (loop.evidenceRefs || []).map(function(ref) {
    return '<div class="loop-evidence-item">' + ref + '</div>';
  }).join('');
}

function initLoopSurface() {
  loopFetchJSON('/api/collaboration/loops').then(function(data) {
    var loop = Array.isArray(data) && data.length ? data[0] : null;
    renderLoopMetrics(loop);
    renderLoopList(loop);
    renderLoopDetail(loop);
  }).catch(function() {
    renderLoopMetrics(null);
    renderLoopList(null);
    renderLoopDetail(null);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLoopSurface);
} else {
  initLoopSurface();
}
