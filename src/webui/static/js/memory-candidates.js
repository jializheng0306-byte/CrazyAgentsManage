/**
 * Memory Candidate Console — AI Assistant + Context Graph + Decision Trace
 * Vanilla JS + force-graph (UMD) + deep-chat (web component).
 */
(function () {
  'use strict';

  var BASE = window.BASE || '';
  var state = {
    candidates: [],
    currentId: null,
    detail: null,
    alignment: null,
    excerpt: null,
    graph: null,
    graphInstance: null,
    tagExpanded: false,
    lastClick: { id: null, at: 0 },
  };

  var NODE_COLORS = {
    candidate: '#3B82F6',
    dsl_object: '#8B5CF6',
    session: '#F59E0B',
    decision: '#22C55E',
    commitment: '#EF4444',
    tag: '#64748B',
  };

  function api(path, opts) {
    opts = opts || {};
    return fetch(BASE + '/api' + path, {
      method: opts.method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (r) {
      if (!r.ok) {
        return r.json().catch(function () { return {}; }).then(function (payload) {
          throw new Error(payload.error || (path + ' ' + r.status));
        });
      }
      return r.json();
    });
  }

  function el(id) { return document.getElementById(id); }

  function esc(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  // ── 候选列表 ──
  function loadCandidates() {
    var status = el('mc-status-filter').value;
    var path = '/flowmind/memory-candidates' + (status ? '?status=' + encodeURIComponent(status) : '');
    return api(path).then(function (data) {
      state.candidates = data.candidates || [];
      var select = el('mc-candidate-select');
      select.innerHTML = '<option value="">— 选择候选（' + state.candidates.length + '）—</option>';
      state.candidates.forEach(function (c) {
        var opt = document.createElement('option');
        opt.value = c.mc_id;
        opt.textContent = c.mc_id + ' · ' + c.status + (c.confidence != null ? ' · ' + c.confidence + '%' : '');
        select.appendChild(opt);
      });
      if (state.currentId) select.value = state.currentId;
    }).catch(function (err) {
      el('mc-candidate-select').innerHTML = '<option value="">加载失败: ' + esc(err.message) + '</option>';
    });
  }

  // ── 候选详情 + Agent Context ──
  function renderContext() {
    var d = state.detail;
    var body = el('mc-context-body');
    if (!d) {
      body.innerHTML = '<p class="mc-empty">选择候选后加载摘要、详情与 session anchor。</p>';
      el('mc-context-hint').textContent = '未选择候选';
      return;
    }
    el('mc-context-hint').textContent = d.mc_id;

    var fm = d.frontmatter || {};
    var summary = fm.summary || (d.body || '').split('\n').slice(0, 3).join('\n');
    var html = '';
    html += '<div class="mc-context-section"><div class="mc-context-label">Summary</div><div class="mc-context-text">' + esc(summary) + '</div></div>';
    html += '<div class="mc-context-section"><div class="mc-context-label">Detail</div><div class="mc-context-text">' + esc((d.body || '').slice(0, 1200)) + '</div></div>';
    if ((d.tags || []).length) {
      html += '<div class="mc-context-section"><div class="mc-context-label">Tags</div><div class="mc-tags">'
        + d.tags.map(function (t) { return '<span class="mc-tag">' + esc(t) + '</span>'; }).join('')
        + '</div></div>';
    }
    if (d.session && d.session.session_id) {
      html += '<div class="mc-context-section"><div class="mc-context-label">Session Anchor</div><div class="mc-context-text">'
        + esc(d.session.session_id)
        + (d.session.line_range ? ' · L' + d.session.line_range[0] + '-' + d.session.line_range[1] : '')
        + '</div></div>';
      if (state.excerpt && state.excerpt.excerpt) {
        html += '<div class="mc-context-section"><div class="mc-context-label">Session Excerpt</div><div class="mc-context-text" style="max-height:90px;overflow:auto">' + esc(state.excerpt.excerpt.slice(0, 2000)) + '</div></div>';
      }
    }
    html += '<label class="mc-context-toggle"><input type="checkbox" id="mc-include-excerpt" checked> 带入上下文（候选内容 + session 摘录注入对话）</label>';
    body.innerHTML = html;
  }

  // ── Tool Calls（E5.3 对齐层） ──
  function renderToolCalls() {
    var a = state.alignment;
    var body = el('mc-toolcalls-body');
    if (!a || !(a.layers || []).length) {
      body.innerHTML = '<p class="mc-empty">无对齐数据。</p>';
      el('mc-toolcalls-hint').textContent = '(0)';
      return;
    }
    var stepCount = 0;
    var html = a.layers.map(function (layer) {
      var steps = layer.steps || [];
      stepCount += steps.length;
      var cls = layer.status === 'completed' ? 'ok' : (layer.status === 'drill' || layer.status === 'skipped' ? 'warn' : '');
      return '<div class="mc-toolcall-step ' + cls + '">'
        + '<div class="mc-toolcall-layer">Layer ' + layer.layer + ' · ' + esc(layer.name) + ' · ' + esc(layer.status) + '</div>'
        + '<div class="mc-toolcall-detail">' + esc(layer.summary || '') + '</div>'
        + steps.map(function (s) {
            return '<div class="mc-toolcall-detail">→ ' + esc(s.action) + ' ' + esc(s.target) + ' = ' + esc(s.result) + '</div>';
          }).join('')
        + '</div>';
    }).join('');
    if ((a.conflicts || []).length) {
      html += '<div class="mc-toolcall-step warn"><div class="mc-toolcall-layer">Conflicts</div><div class="mc-toolcall-detail">' + esc(a.conflicts.join(', ')) + '</div></div>';
    }
    body.innerHTML = html;
    el('mc-toolcalls-hint').textContent = '(' + stepCount + ')';
  }

  // ── Context Graph ──
  function inspectNode(node) {
    el('mc-inspector-title').textContent = node.type + ' · ' + node.label;
    el('mc-inspector-body').textContent = JSON.stringify(node.meta || {}, null, 2);
    el('mc-node-inspector').hidden = false;
  }

  function expandNode(node) {
    if (!state.graph) return;
    if (node.type === 'candidate' && !state.tagExpanded) {
      var tags = (node.meta && node.meta.tags) || [];
      tags.forEach(function (tag) {
        var id = 'tag:' + tag;
        if (state.graph.nodes.some(function (n) { return n.id === id; })) return;
        state.graph.nodes.push({ id: id, type: 'tag', label: tag, meta: {} });
        state.graph.links.push({ source: node.id, target: id, kind: 'TAGGED' });
      });
      state.tagExpanded = true;
      state.graphInstance.graphData({ nodes: state.graph.nodes, links: state.graph.links });
    } else if (node.type === 'session') {
      inspectNode(node);
    } else if (node.type === 'dsl_object') {
      inspectNode(node);
    }
  }

  function renderGraph() {
    var container = el('mc-graph');
    el('mc-node-inspector').hidden = true;
    if (!state.graph) {
      container.innerHTML = '<div class="mc-empty mc-empty-center">选择候选后加载图谱。<br><small>拖拽平移 · 滚轮缩放 · 单击查看 · 双击展开</small></div>';
      state.graphInstance = null;
      return;
    }
    if (typeof ForceGraph !== 'function') {
      container.innerHTML = '<div class="mc-empty mc-empty-center">force-graph 库未加载。</div>';
      return;
    }
    container.innerHTML = '';
    state.tagExpanded = false;

    var rect = container.getBoundingClientRect();
    var initW = Math.floor(rect.width) || 600;
    var initH = Math.floor(rect.height) || 420;

    var graph = ForceGraph()(container)
      .width(initW)
      .height(initH)
      .backgroundColor('rgba(0,0,0,0)')
      .nodeId('id')
      .nodeLabel(function (n) { return n.type + ': ' + n.label; })
      .nodeVal(function (n) { return n.type === 'candidate' ? 14 : (n.type === 'tag' ? 3 : 7); })
      .nodeColor(function (n) { return NODE_COLORS[n.type] || '#94A3B8'; })
      .nodeCanvasObjectMode(function () { return 'after'; })
      .nodeCanvasObject(function (node, ctx, globalScale) {
        var label = node.label.length > 26 ? node.label.slice(0, 24) + '…' : node.label;
        var fontSize = Math.max(10 / globalScale, 2.2);
        ctx.font = fontSize + 'px Sans-Serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = 'rgba(226,232,240,0.85)';
        ctx.fillText(label, node.x, node.y + 7);
      })
      .linkColor(function () { return 'rgba(100,116,139,0.5)'; })
      .linkLabel(function (l) { return l.kind; })
      .linkDirectionalParticles(1)
      .linkDirectionalParticleSpeed(0.004)
      .onNodeClick(function (node) {
        var now = Date.now();
        if (state.lastClick.id === node.id && now - state.lastClick.at < 350) {
          expandNode(node);
          state.lastClick = { id: null, at: 0 };
        } else {
          inspectNode(node);
          state.lastClick = { id: node.id, at: now };
        }
      })
      .onBackgroundClick(function () { el('mc-node-inspector').hidden = true; });

    graph.graphData({ nodes: state.graph.nodes, links: state.graph.links });
    state.graphInstance = graph;
    if (state.graphResizeObserver) state.graphResizeObserver.disconnect();
    if (window.ResizeObserver) {
      state.graphResizeObserver = new ResizeObserver(function (entries) {
        var r = entries[0].contentRect;
        if (r.width > 0 && r.height > 0 && state.graphInstance === graph) {
          graph.width(Math.floor(r.width)).height(Math.floor(r.height));
        }
      });
      state.graphResizeObserver.observe(container);
    }
  }

  // ── Decision Trace ──
  function renderTrace(entries) {
    var list = el('mc-trace-list');
    el('mc-trace-count').textContent = (entries || []).length + ' 条';
    if (!(entries || []).length) {
      list.innerHTML = '<p class="mc-empty">暂无决策痕迹。</p>';
      return;
    }
    list.innerHTML = entries.slice().reverse().map(function (e) {
      var score = e.scores && e.scores.total != null ? '综合 ' + e.scores.total : '';
      return '<div class="mc-trace-card">'
        + '<div class="mc-trace-top">'
        + '<span class="mc-trace-tag ' + esc(e.decision) + '">' + esc(e.decision) + '</span>'
        + '<span class="mc-trace-date">' + esc((e.timestamp || '').slice(0, 19).replace('T', ' ')) + '</span>'
        + '</div>'
        + '<div class="mc-trace-reason">' + esc(e.reason || '') + '</div>'
        + '<div class="mc-trace-meta">reviewer: ' + esc(e.reviewer || '—') + (score ? ' · ' + esc(score) : '') + '</div>'
        + '</div>';
    }).join('');
  }

  function loadTrace() {
    if (!state.currentId) { renderTrace([]); return Promise.resolve(); }
    return api('/flowmind/memory-candidates/' + encodeURIComponent(state.currentId) + '/review-log')
      .then(function (data) { renderTrace(data.entries || []); })
      .catch(function () { renderTrace([]); });
  }

  // ── Chat（deep-chat + SSE） ──
  function setupChat() {
    customElements.whenDefined('deep-chat').then(function () {
      var chat = el('mc-chat');
      chat.style.width = '100%';
      chat.style.height = '100%';
      chat.style.border = 'none';
      chat.style.backgroundColor = 'transparent';
      chat.introMessage = { text: '选择候选后，可就该 memory_candidate 提问。回答基于 INFERRED 级候选内容，不裁定 truth.status。' };
      chat.textInput = { placeholder: { text: '就当前候选提问…' } };
      chat.messageStyles = {
        default: {
          shared: { bubble: { maxWidth: '95%', fontSize: '13px' } },
        },
      };
      chat.connect = {
        stream: true,
        handler: function (body, signals) {
          if (!state.currentId) {
            signals.onResponse({ error: '请先在顶部选择一个候选。' });
            return;
          }
          var messages = (body && body.messages) || [];
          var last = messages[messages.length - 1];
          var history = messages.slice(0, -1).map(function (m) {
            return { role: m.role === 'ai' ? 'assistant' : 'user', content: m.text || '' };
          });
          var includeEl = el('mc-include-excerpt');
          signals.onOpen();
          fetch(BASE + '/api/flowmind/memory-candidates/' + encodeURIComponent(state.currentId) + '/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: (last && last.text) || '',
              history: history,
              includeSessionExcerpt: includeEl ? includeEl.checked : true,
            }),
          }).then(function (resp) {
            if (!resp.ok || !resp.body) throw new Error('chat upstream ' + resp.status);
            var reader = resp.body.getReader();
            var decoder = new TextDecoder();
            var buffer = '';
            function pump() {
              return reader.read().then(function (chunk) {
                if (chunk.done) { signals.onClose(); return; }
                buffer += decoder.decode(chunk.value, { stream: true });
                var parts = buffer.split('\n\n');
                buffer = parts.pop();
                parts.forEach(function (part) {
                  part.split('\n').forEach(function (line) {
                    if (line.indexOf('data: ') !== 0) return;
                    try {
                      var evt = JSON.parse(line.slice(6));
                      if (evt.text) signals.onResponse({ text: evt.text });
                      if (evt.error) signals.onResponse({ error: evt.error });
                      if (evt.done) signals.onClose();
                    } catch (e) { /* skip malformed frame */ }
                  });
                });
                return pump();
              });
            }
            return pump();
          }).catch(function (err) {
            signals.onResponse({ error: err.message });
            signals.onClose();
          });
        },
      };
    });
  }

  // ── Review 提交 ──
  function setupReviewForm() {
    el('mc-review-submit').addEventListener('click', function () {
      var msg = el('mc-review-msg');
      msg.className = 'mc-review-msg';
      if (!state.currentId) { msg.textContent = '请先选择候选'; msg.classList.add('err'); return; }
      var payload = {
        decision: el('mc-review-decision').value,
        reviewer: el('mc-review-reviewer').value.trim(),
        reason: el('mc-review-reason').value.trim(),
      };
      if (!payload.reviewer || !payload.reason) {
        msg.textContent = 'reviewer 与理由为必填';
        msg.classList.add('err');
        return;
      }
      el('mc-review-submit').disabled = true;
      api('/flowmind/memory-candidates/' + encodeURIComponent(state.currentId) + '/review', {
        method: 'POST', body: payload,
      }).then(function () {
        msg.textContent = '已写入 review-log';
        msg.classList.add('ok');
        el('mc-review-reason').value = '';
        return Promise.all([loadTrace(), loadGraph(), loadCandidates()]);
      }).catch(function (err) {
        msg.textContent = '提交失败: ' + err.message;
        msg.classList.add('err');
      }).then(function () {
        el('mc-review-submit').disabled = false;
      });
    });
  }

  // ── 数据加载编排 ──
  function loadGraph() {
    if (!state.currentId) { state.graph = null; renderGraph(); return Promise.resolve(); }
    return api('/flowmind/memory-candidates/' + encodeURIComponent(state.currentId) + '/graph')
      .then(function (data) { state.graph = data; renderGraph(); })
      .catch(function (err) {
        state.graph = null;
        el('mc-graph').innerHTML = '<div class="mc-empty mc-empty-center">图谱加载失败: ' + esc(err.message) + '</div>';
      });
  }

  function selectCandidate(mcId) {
    state.currentId = mcId || null;
    state.detail = null;
    state.alignment = null;
    state.excerpt = null;
    if (!mcId) {
      renderContext();
      renderToolCalls();
      renderGraph();
      renderTrace([]);
      return;
    }
    var encoded = encodeURIComponent(mcId);
    Promise.all([
      api('/flowmind/memory-candidates/' + encoded).catch(function () { return null; }),
      api('/flowmind/memory-candidates/' + encoded + '/alignment').catch(function () { return null; }),
      api('/flowmind/memory-candidates/' + encoded + '/session-excerpt').catch(function () { return null; }),
    ]).then(function (results) {
      state.detail = results[0];
      state.alignment = results[1];
      state.excerpt = results[2];
      renderContext();
      renderToolCalls();
    });
    loadGraph();
    loadTrace();
  }

  // ── 初始化 ──
  function init() {
    el('mc-status-filter').addEventListener('change', loadCandidates);
    el('mc-candidate-select').addEventListener('change', function (e) {
      selectCandidate(e.target.value);
    });
    el('mc-inspector-close').addEventListener('click', function () {
      el('mc-node-inspector').hidden = true;
    });
    window.addEventListener('resize', function () {
      if (state.graphInstance) {
        var c = el('mc-graph');
        state.graphInstance.width(c.clientWidth).height(c.clientHeight);
      }
    });
    setupChat();
    setupReviewForm();
    loadCandidates();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
