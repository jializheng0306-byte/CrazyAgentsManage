(function() {
  var apiBase = (function() {
    var path = window.location.pathname || '';
    return path === '/manage' || path.indexOf('/manage/') === 0 ? '/manage' : '';
  })();

  var form = document.getElementById('timeline-form');
  var input = document.getElementById('candidateIdInput');
  var stateEl = document.getElementById('timeline-state');
  var candidateEl = document.getElementById('timeline-candidate');
  var countEl = document.getElementById('timeline-count');
  var statusEl = document.getElementById('timeline-status');
  var upstreamEl = document.getElementById('timeline-upstream');
  var eventsEl = document.getElementById('timeline-events');
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
              '<span>status: ' + escapeHtml(event.status || '--') + '</span>' +
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
    statusEl.textContent = data.latestStatus || '--';
    upstreamEl.textContent = data.upstream || '--';
    rawEl.textContent = JSON.stringify(data, null, 2);
    renderEvents(data.events || []);
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

  var params = new URLSearchParams(window.location.search);
  var initialCandidateId = params.get('candidateId');
  if (initialCandidateId) {
    input.value = initialCandidateId;
    fetchTrace(initialCandidateId);
  }
})();
