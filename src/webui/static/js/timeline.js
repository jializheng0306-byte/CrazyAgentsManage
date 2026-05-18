(function() {
  var apiBase = (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })();

  var form = document.getElementById('timeline-form');
  var input = document.getElementById('candidateIdInput');
  var handoffForm = document.getElementById('handoff-form');
  var recordInput = document.getElementById('recordIdInput');
  var stateEl = document.getElementById('timeline-state');
  var candidateEl = document.getElementById('timeline-candidate');
  var countEl = document.getElementById('timeline-count');
  var statusEl = document.getElementById('timeline-status');
  var upstreamEl = document.getElementById('timeline-upstream');
  var eventsEl = document.getElementById('timeline-events');
  var handoffStateEl = document.getElementById('handoff-state');
  var handoffRecordEl = document.getElementById('handoff-record');
  var handoffSourceEl = document.getElementById('handoff-source');
  var handoffSummaryEl = document.getElementById('handoff-summary');
  var rawEl = document.getElementById('timeline-raw');

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function setState(text, kind) {
    stateEl.textContent = text;
    stateEl.className = 'tl-state' + (kind ? ' ' + kind : '');
  }

  function setHandoffState(text, kind) {
    handoffStateEl.textContent = text;
    handoffStateEl.className = 'tl-state' + (kind ? ' ' + kind : '');
  }

  function renderEmpty(message) {
    eventsEl.innerHTML = '<div class="tl-empty"><strong>无可展示事件</strong><p>' + escapeHtml(message) + '</p></div>';
  }

  function renderEvents(events) {
    if (!events || events.length === 0) {
      renderEmpty('FlowMind 已响应，但该 candidate 目前没有 trace event。');
      return;
    }

    eventsEl.innerHTML = events.map(function(event) {
      var payload = event.payload && Object.keys(event.payload).length
        ? '<details class="tl-payload"><summary>payload</summary><pre>' + escapeHtml(JSON.stringify(event.payload, null, 2)) + '</pre></details>'
        : '';
      return (
        '<article class="tl-event">' +
          '<div class="tl-event-rail"><span></span></div>' +
          '<div class="tl-event-body">' +
            '<div class="tl-event-meta">' +
              '<span class="tl-badge">' + escapeHtml(event.module || 'bridge') + '</span>' +
              '<span class="tl-event-time">' + escapeHtml(event.timestamp || '--') + '</span>' +
            '</div>' +
            '<h3>' + escapeHtml(event.action || 'query') + '</h3>' +
            '<p>' + escapeHtml(event.summary || '无摘要') + '</p>' +
            '<div class="tl-event-grid">' +
              '<span>actor: ' + escapeHtml(event.actor || 'system') + '</span>' +
              '<span>module: ' + escapeHtml(event.module || '--') + '</span>' +
              '<span>from: ' + escapeHtml(event.fromStatus || '--') + '</span>' +
              '<span>to: ' + escapeHtml(event.toStatus || '--') + '</span>' +
            '</div>' +
            payload +
          '</div>' +
        '</article>'
      );
    }).join('');
  }

  function renderResponse(data) {
    candidateEl.textContent = data.candidateId || '--';
    countEl.textContent = data.traceCount || 0;
    statusEl.textContent = data.candidateStatus || data.latestStatus || '--';
    upstreamEl.textContent = data.upstream || '--';
    rawEl.textContent = JSON.stringify(data, null, 2);
    renderEvents(data.traceEvents || []);
  }

  function renderHandoffEmpty(message) {
    handoffSummaryEl.className = 'tl-empty';
    handoffSummaryEl.innerHTML = '<strong>暂无 handoff 摘要</strong><p>' + escapeHtml(message) + '</p>';
  }

  function renderFieldRow(label, value) {
    var normalizedValue = value;
    if (Array.isArray(normalizedValue)) {
      normalizedValue = normalizedValue.join(' | ');
    } else if (normalizedValue && typeof normalizedValue === 'object') {
      normalizedValue = JSON.stringify(normalizedValue);
    }
    return (
      '<div class="tl-handoff-row">' +
        '<span class="tl-handoff-label">' + escapeHtml(label) + '</span>' +
        '<span class="tl-handoff-value">' + escapeHtml(normalizedValue == null || normalizedValue === '' ? '--' : normalizedValue) + '</span>' +
      '</div>'
    );
  }

  function renderBoundaryRow(label, value) {
    var normalizedValue = value;
    if (Array.isArray(normalizedValue)) {
      normalizedValue = normalizedValue.join(' | ');
    }
    return (
      '<div class="tl-boundary-row">' +
        '<span class="tl-boundary-label">' + escapeHtml(label) + '</span>' +
        '<span class="tl-boundary-value">' + escapeHtml(normalizedValue == null || normalizedValue === '' ? '--' : normalizedValue) + '</span>' +
      '</div>'
    );
  }

  function renderFollowUpRow(label, value) {
    return (
      '<div class="tl-follow-up-row">' +
        '<span class="tl-follow-up-label">' + escapeHtml(label) + '</span>' +
        '<span class="tl-follow-up-value">' + escapeHtml(value == null || value === '' ? '--' : value) + '</span>' +
      '</div>'
    );
  }

  function normalizeDisplayValue(value) {
    if (Array.isArray(value)) {
      return value.join(' | ');
    }
    if (value && typeof value === 'object') {
      return JSON.stringify(value);
    }
    return value;
  }

  function renderOperationalFollowUp(followUp) {
    if (!followUp) {
      return (
        '<div class="tl-gap-box">' +
          '<strong>Operational Follow-Up 缺失</strong>' +
          '<p>当前 replay 没有返回 follow-up projection，页面不会本地推断 follow-up judgment。</p>' +
        '</div>'
      );
    }

    var evidenceRefs = normalizeDisplayValue(followUp.evidenceRefs);
    var missingFields = normalizeDisplayValue(followUp.missingFields);
    var rows = [
      renderFollowUpRow('Projection State', normalizeDisplayValue(followUp.projectionState)),
      renderFollowUpRow('FlowMind Status', normalizeDisplayValue(followUp.flowmindStatus)),
      renderFollowUpRow('Last Governance Status', normalizeDisplayValue(followUp.lastGovernanceStatus)),
      renderFollowUpRow('Last Governance Feedback', normalizeDisplayValue(followUp.lastGovernanceFeedback)),
      renderFollowUpRow('Local Status', normalizeDisplayValue(followUp.localStatus)),
      renderFollowUpRow('Needs Follow-Up', normalizeDisplayValue(followUp.needsFollowUp)),
      renderFollowUpRow('Follow-Up Kind', normalizeDisplayValue(followUp.followUpKind)),
      renderFollowUpRow('Next Actor', normalizeDisplayValue(followUp.nextActor)),
      renderFollowUpRow('Is Terminal Local', normalizeDisplayValue(followUp.isTerminalLocal)),
      renderFollowUpRow('Reason', normalizeDisplayValue(followUp.reason)),
      renderFollowUpRow('Note', normalizeDisplayValue(followUp.note)),
      renderFollowUpRow('Evidence Refs', evidenceRefs),
      renderFollowUpRow('Missing Fields', missingFields)
    ].join('');

    return (
      '<div class="tl-follow-up-card">' +
        '<div class="tl-follow-up-head">' +
          '<h4 class="tl-follow-up-title">Operational Follow-Up</h4>' +
          '<span class="tl-follow-up-copy">Directly rendered from FlowMind Slice 1 projection.</span>' +
        '</div>' +
        '<div class="tl-follow-up-grid">' + rows + '</div>' +
      '</div>'
    );
  }

  function renderHandoff(data) {
    handoffRecordEl.textContent = data.recordId || '--';
    handoffSourceEl.textContent = data.source || '--';
    var contract = data.handoffContract || {};

    var fieldMap = data.fieldMap || {};
    var requiredFields = [
      'Truth Status',
      'Latest Evidence Summary',
      'Latest Evidence Class',
      'Latest Evidence Source Type',
      'Latest Evidence Refs',
      'Semantic Refs',
      'Trace Events',
      'Latest Trace Action',
      'Latest Trace Summary',
      'Consumer Hints'
    ];

    var rows = requiredFields.map(function(field) {
      return renderFieldRow(field, fieldMap[field]);
    }).join('');

    var meta = (
      '<div class="tl-handoff-meta">' +
        renderFieldRow('Replay Mode', data.mode || '--') +
        renderFieldRow('Trace Events', data.traceEventCount == null ? '--' : data.traceEventCount) +
        renderFieldRow('Latest Trace Action', data.latestTraceAction || '--') +
        renderFieldRow('Latest Trace Summary', data.latestTraceSummary || '--') +
      '</div>'
    );

    var gaps = '';
    if (contract.blockingIssues && contract.blockingIssues.length) {
      gaps += '<div class="tl-gap-box"><strong>契约阻塞</strong><p>' + escapeHtml(contract.blockingIssues.join('；')) + '</p></div>';
    }
    if (contract.missingFields && contract.missingFields.length) {
      gaps += '<div class="tl-gap-box"><strong>仍缺字段</strong><p>' + escapeHtml(contract.missingFields.join('，')) + '</p></div>';
    }
    if (contract.executionBoundaryMissingFields && contract.executionBoundaryMissingFields.length) {
      gaps += '<div class="tl-gap-box"><strong>边界缺口</strong><p>' + escapeHtml(contract.executionBoundaryMissingFields.join('，')) + '</p></div>';
    }
    if (data.gaps && data.gaps.length) {
      gaps += '<div class="tl-gap-box"><strong>上游缺口</strong><p>' + escapeHtml(data.gaps.join('；')) + '</p></div>';
    }

    var boundary = data.executionBoundary || null;
    var followUp = data.operationalFollowUp || null;
    var boundaryMarkup = '';
    if (boundary) {
      boundaryMarkup =
        '<div class="tl-boundary-card">' +
          '<div class="tl-boundary-head">' +
            '<h4 class="tl-boundary-title">Execution Boundary</h4>' +
            '<span class="tl-boundary-source">' + escapeHtml(data.executionBoundarySource || 'upstream') + '</span>' +
          '</div>' +
          '<div class="tl-boundary-grid">' +
            renderBoundaryRow('Canonical Authority', Array.isArray(boundary.canonicalAuthority) ? boundary.canonicalAuthority.join(' | ') : boundary.canonicalAuthority) +
            renderBoundaryRow('Local Writable Targets', Array.isArray(boundary.localWritableTargets) ? boundary.localWritableTargets.join(' | ') : boundary.localWritableTargets) +
            renderBoundaryRow('Human Gate Actions', Array.isArray(boundary.humanGateActions) ? boundary.humanGateActions.join(' | ') : boundary.humanGateActions) +
            renderBoundaryRow('Forbidden Mutations', Array.isArray(boundary.forbiddenMutations) ? boundary.forbiddenMutations.join(' | ') : boundary.forbiddenMutations) +
          '</div>' +
        '</div>';
    } else {
      boundaryMarkup =
        '<div class="tl-gap-box">' +
          '<strong>Execution Boundary 缺失</strong>' +
          '<p>当前 replay 与 semanticContext 都没有返回 executionBoundary，页面不会本地推断边界规则。</p>' +
        '</div>';
    }

    var followUpMarkup = renderOperationalFollowUp(followUp);

    handoffSummaryEl.className = 'tl-handoff-card';
    handoffSummaryEl.innerHTML =
      '<div class="tl-handoff-title-wrap">' +
        '<h3 class="tl-handoff-title">' + escapeHtml(data.title || 'Handoff Summary') + '</h3>' +
        '<p class="tl-handoff-copy">' + escapeHtml(data.summary || '模块摘要由 FlowMind replay 提供。') + '</p>' +
      '</div>' +
      meta +
      '<div class="tl-handoff-meta">' +
        renderFieldRow('Contract Ready', contract.ready ? 'yes' : 'no') +
        renderFieldRow('Primary Source', contract.primarySource || '--') +
        renderFieldRow('Execution Boundary Source', contract.executionBoundarySource || '--') +
      '</div>' +
      '<div class="tl-handoff-grid">' + rows + '</div>' +
      followUpMarkup +
      boundaryMarkup +
      gaps;
  }

  function fetchTrace(candidateId) {
    setState('加载中', 'loading');
    fetch(apiBase + '/api/promise-review/trace/' + encodeURIComponent(candidateId))
      .then(function(response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }
        return response.json();
      })
      .then(function(data) {
        renderResponse(data);
        setState('已加载', 'ok');
      })
      .catch(function(error) {
        rawEl.textContent = JSON.stringify({ error: String(error) }, null, 2);
        renderEmpty('无法读取 FlowMind trace，请检查 candidateId 或 upstream 连通性。');
        setState('加载失败', 'error');
      });
  }

  function fetchHandoff(recordId) {
    setHandoffState('加载中', 'loading');
    fetch(apiBase + '/api/runtime/handoffs?recordId=' + encodeURIComponent(recordId))
      .then(function(response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }
        return response.json();
      })
      .then(function(data) {
        renderHandoff(data);
        rawEl.textContent = JSON.stringify(data, null, 2);
        var ready = data.handoffContract && data.handoffContract.ready === true;
        var stateText = ready ? '契约就绪' : '契约阻塞';
        setHandoffState(stateText, ready ? 'ok' : 'error');
      })
      .catch(function(error) {
        renderHandoffEmpty('无法读取 replay handoff，请检查 recordId 或 upstream 连通性。');
        setHandoffState('加载失败', 'error');
        rawEl.textContent = JSON.stringify({ error: String(error) }, null, 2);
      });
  }

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    var candidateId = (input.value || '').trim();
    if (!candidateId) {
        renderEmpty('请先输入 candidateId。');
      setState('缺少 candidateId', 'error');
      return;
    }
    var url = new URL(window.location.href);
    url.searchParams.set('candidateId', candidateId);
    window.history.replaceState({}, '', url.toString());
    fetchTrace(candidateId);
  });

  handoffForm.addEventListener('submit', function(event) {
    event.preventDefault();
    var recordId = (recordInput.value || '').trim();
    if (!recordId) {
      renderHandoffEmpty('请先输入 recordId。');
      setHandoffState('缺少 recordId', 'error');
      return;
    }
    var url = new URL(window.location.href);
    url.searchParams.set('recordId', recordId);
    window.history.replaceState({}, '', url.toString());
    fetchHandoff(recordId);
  });

  var params = new URLSearchParams(window.location.search);
  var initialCandidateId = params.get('candidateId');
  var initialRecordId = params.get('recordId');
  if (initialCandidateId) {
    input.value = initialCandidateId;
    fetchTrace(initialCandidateId);
  }
  if (initialRecordId) {
    recordInput.value = initialRecordId;
    fetchHandoff(initialRecordId);
  }
})();
