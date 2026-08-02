/**
 * Knowledge Harvest Pipeline — visualization + triggers + table
 * Vanilla JS, no frameworks.
 */
(function () {
  'use strict';

  var BASE = window.BASE || '';
  var currentCandidates = [];
  var currentTriggers = {};

  // ── API helpers ──
  function api(path, opts) {
    opts = opts || {};
    var url = BASE + '/api' + path;
    return fetch(url, {
      method: opts.method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (r) {
      if (!r.ok) throw new Error(path + ' ' + r.status);
      return r.json();
    });
  }

  // ── Render: metrics ──
  function renderMetrics(data) {
    var cs = data.candidates || {};
    document.getElementById('gv-hv-total').textContent = cs.total ?? '--';
    document.getElementById('gv-hv-accepted').textContent = (cs.by_status || {}).accepted ?? '--';
    document.getElementById('gv-hv-pending').textContent = (cs.by_status || {}).candidate ?? '--';
    document.getElementById('gv-hv-reviews').textContent = data.review_log_count ?? '--';
  }

  // ── Render: pipeline SVG ──
  function renderPipeline() {
    var container = document.getElementById('gv-hv-pipeline');
    var w = 880, h = 160;

    var stages = [
      { id: 'capture', label: '1. Capture', sub: 'Agent 会话记录 (jsonl)', actor: 'Agent', x: 10, color: '#3B82F6' },
      { id: 'extract', label: '2. Extract', sub: '五原语建模 → mc-*.md', actor: 'Agent', x: 170, color: '#8B5CF6' },
      { id: 'resolve', label: '3. Resolve', sub: 'semantic-query 去重', actor: 'Agent', x: 330, color: '#22C55E' },
      { id: 'review', label: '4. Review', sub: 'memory-review.py', actor: '人类', x: 490, color: '#F59E0B' },
      { id: 'writegate', label: 'WriteGate', sub: '提升至 Layer A', actor: '系统', x: 650, color: '#EF4444' },
    ];

    var bw = 150, bh = 65;

    var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
    svg += '<defs><marker id="arrhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#475569"/></marker></defs>';

    for (var i = 0; i < stages.length - 1; i++) {
      var sx = stages[i].x + bw;
      var sy = bh / 2;
      var ex = stages[i + 1].x;
      svg += '<line x1="' + sx + '" y1="' + sy + '" x2="' + (ex - 4) + '" y2="' + sy + '" stroke="#475569" stroke-width="2" marker-end="url(#arrhead)"/>';
    }

    stages.forEach(function (st) {
      svg += '<rect x="' + st.x + '" y="0" width="' + bw + '" height="' + bh + '" rx="8" ry="8" fill="' + st.color + '15" stroke="' + st.color + '" stroke-width="1.5"/>';
      svg += '<text x="' + (st.x + bw / 2) + '" y="20" text-anchor="middle" fill="' + st.color + '" font-size="11" font-weight="600">' + st.label + '</text>';
      svg += '<text x="' + (st.x + bw / 2) + '" y="37" text-anchor="middle" fill="#94A3B8" font-size="9">' + st.sub + '</text>';
      svg += '<text x="' + (st.x + bw / 2) + '" y="53" text-anchor="middle" fill="#64748B" font-size="9">执行者: ' + st.actor + '</text>';
    });

    svg += '</svg>';
    container.innerHTML = svg;
  }

  // ── Render: charts ──
  function renderCharts(data) {
    var container = document.getElementById('gv-hv-charts');
    var cs = data.candidates || {};
    var byStatus = cs.by_status || {};
    var byGrade = cs.by_grade || {};
    var byType = cs.by_type || {};

    var statusColors = { accepted: '#22C55E', rejected: '#EF4444', deferred: '#F59E0B', candidate: '#94A3B8' };
    var gradeColors = { A: '#22C55E', B: '#EAB308', C: '#F97316', D: '#EF4444' };
    var typeColors = { decision: '#3B82F6', workflow_upgrade: '#8B5CF6', failure_pattern: '#EF4444', dsl_new: '#22C55E', negative_knowledge: '#F59E0B', reflection: '#06B6D4', action_new: '#F97316' };

    // Status pie chart
    function pieSvg(title, items, colors) {
      var total = 0;
      Object.keys(items).forEach(function (k) { total += items[k]; });
      if (!total) return '<p style="color:#64748B;font-size:11px;">' + title + ': 无数据</p>';

      var svg = '<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">';
      var cx = 60, cy = 60, r = 48;
      var cum = 0;
      Object.keys(items).forEach(function (k) {
        if (!items[k]) return;
        var pct = items[k] / total;
        var startAngle = cum * 2 * Math.PI - Math.PI / 2;
        cum += pct;
        var endAngle = cum * 2 * Math.PI - Math.PI / 2;
        var x1 = cx + r * Math.cos(startAngle), y1 = cy + r * Math.sin(startAngle);
        var x2 = cx + r * Math.cos(endAngle), y2 = cy + r * Math.sin(endAngle);
        var largeArc = pct > 0.5 ? 1 : 0;
        var d = 'M ' + cx + ' ' + cy + ' L ' + x1.toFixed(1) + ' ' + y1.toFixed(1) + ' A ' + r + ' ' + r + ' 0 ' + largeArc + ' 1 ' + x2.toFixed(1) + ' ' + y2.toFixed(1) + ' Z';
        svg += '<path d="' + d + '" fill="' + (colors[k] || '#64748B') + '"/>';
      });
      svg += '<text x="' + cx + '" y="' + (cy - 4) + '" text-anchor="middle" fill="#F8FAFC" font-size="14" font-weight="700">' + total + '</text>';
      svg += '<text x="' + cx + '" y="' + (cy + 14) + '" text-anchor="middle" fill="#94A3B8" font-size="9">' + title + '</text>';
      svg += '</svg>';
      return svg;
    }

    // Bar chart
    function barSvg(title, items, colors) {
      var keys = Object.keys(items).filter(function (k) { return items[k] > 0; });
      if (!keys.length) return '<p style="color:#64748B;font-size:11px;">' + title + ': 无数据</p>';

      var maxVal = 1;
      keys.forEach(function (k) { maxVal = Math.max(maxVal, items[k]); });
      var barH = 14, gap = 6, w = 180, h = keys.length * (barH + gap) + 20;

      var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg">';
      keys.forEach(function (k, i) {
        var pct = Math.round(items[k] / maxVal * 100);
        var y = 10 + i * (barH + gap);
        svg += '<text x="2" y="' + (y + 10) + '" fill="#94A3B8" font-size="9">' + k + '</text>';
        svg += '<rect x="52" y="' + y + '" width="' + (pct * 1.1) + '" height="' + barH + '" rx="3" fill="' + (colors[k] || '#64748B') + '"/>';
        svg += '<text x="' + (54 + pct * 1.1) + '" y="' + (y + 10) + '" fill="#F8FAFC" font-size="10">' + items[k] + '</text>';
      });
      svg += '<text x="' + (w / 2) + '" y="' + (h - 4) + '" text-anchor="middle" fill="#64748B" font-size="9">' + title + '</text>';
      svg += '</svg>';
      return svg;
    }

    var html = '';
    html += '<div class="gv-hv-chart-box">' + pieSvg('状态分布', byStatus, statusColors) + '<div class="gv-hv-chart-title">状态分布</div></div>';
    html += '<div class="gv-hv-chart-box">' + barSvg('评分等级', byGrade, gradeColors) + '<div class="gv-hv-chart-title">评分等级</div></div>';
    html += '<div class="gv-hv-chart-box">' + barSvg('候选类型', byType, typeColors) + '<div class="gv-hv-chart-title">候选类型</div></div>';
    container.innerHTML = html;
  }

  // ── Render: trigger toggles ──
  function renderTriggers(triggers) {
    currentTriggers = triggers || {};
    var container = document.getElementById('gv-hv-triggers');
    var keys = ['decision_milestone', 'user_correction', 'session_milestone', 'context_compression'];
    var icons = ['🔵', '🟡', '🟢', '🟣'];

    var html = '';
    keys.forEach(function (k, i) {
      var t = triggers[k] || { enabled: true, description: k };
      html += '<div class="gv-hv-toggle-panel">';
      html += '<div class="gv-hv-toggle-info">';
      html += '<div class="gv-hv-toggle-title">' + icons[i] + ' ' + (t.description || k) + '</div>';
      html += '<div class="gv-hv-toggle-desc">触发信号: ' + (t.signal || '—') + '</div>';
      html += '<div class="gv-hv-toggle-desc">预期产出: ' + ((t.expected_types || []).join(', ') || '—') + '</div>';
      html += '<div class="gv-hv-toggle-meta">上次触发: ' + (t.last_triggered || '尚未触发') + '</div>';
      html += '</div>';
      html += '<label class="gv-hv-toggle-switch">';
      html += '<input type="checkbox" data-trigger="' + k + '"' + (t.enabled ? ' checked' : '') + '>';
      html += '<span class="gv-hv-toggle-track"><span class="gv-hv-toggle-thumb"></span></span>';
      html += '</label>';
      html += '</div>';
    });
    container.innerHTML = html;

    // bind toggle events
    setTimeout(function () {
      var inputs = container.querySelectorAll('input[data-trigger]');
      inputs.forEach(function (input) {
        input.addEventListener('change', function () {
          var key = this.getAttribute('data-trigger');
          var payload = {};
          payload[key] = this.checked;
          api('/harvest/triggers', { method: 'PUT', body: payload }).then(function (res) {
            currentTriggers[key].enabled = payload[key];
          }).catch(function (err) {
            // revert
            input.checked = !input.checked;
          });
        });
      });
    }, 50);
  }

  // ── Render: candidate table ──
  function renderTable(candidates) {
    currentCandidates = candidates || [];
    var container = document.getElementById('gv-hv-table');
    var countEl = document.getElementById('gv-hv-table-count');
    countEl.textContent = currentCandidates.length + ' 条';

    if (!currentCandidates.length) {
      container.innerHTML = '<div class="gv-empty"><div class="gv-empty-icon"></div><p>暂无候选</p></div>';
      return;
    }

    var cols = ['ID', '类型', '置信', '评分', '等级', '状态', '裁定时间', '去向'];
    var html = '<table class="gv-hv-table"><thead><tr>';
    cols.forEach(function (c) {
      html += '<th>' + c + '</th>';
    });
    html += '</tr></thead><tbody>';

    currentCandidates.forEach(function (c) {
      var sc = c.score || {};
      html += '<tr data-id="' + c.id + '">';
      html += '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;" title="' + c.id + '">' + (c.id || '').replace('mc-20260722-', '') + '</td>';
      html += '<td>' + (c.type || '') + '</td>';
      html += '<td>' + (c.confidence || 0) + '</td>';
      html += '<td>' + (sc.total || 0) + '</td>';
      html += '<td><span class="gv-hv-grade ' + (c.grade || 'D') + '">' + (c.grade || 'D') + '</span></td>';
      html += '<td><span class="gv-hv-badge ' + (c.status || 'candidate') + '">' + (c.status || 'candidate') + '</span></td>';
      html += '<td>' + (c.resolved_at ? c.resolved_at.substring(0, 16) : '—') + '</td>';
      html += '<td>' + (c.promotion || 'none') + '</td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;

    // row click → detail
    container.querySelectorAll('tbody tr').forEach(function (row) {
      row.addEventListener('click', function () {
        var id = this.getAttribute('data-id');
        // toggle
        var wasExpanded = this.classList.contains('expanded');
        container.querySelectorAll('tbody tr').forEach(function (r) { r.classList.remove('expanded'); });
        if (wasExpanded) {
          document.getElementById('gv-hv-detail').style.display = 'none';
          return;
        }
        this.classList.add('expanded');
        showDetail(id);
      });
    });
  }

  // ── Detail panel ──
  function showDetail(candidateId) {
    var detailPanel = document.getElementById('gv-hv-detail');
    var detailInner = document.getElementById('gv-hv-detail-inner');

    var c = null;
    for (var i = 0; i < currentCandidates.length; i++) {
      if (currentCandidates[i].id === candidateId) { c = currentCandidates[i]; break; }
    }
    if (!c) { detailPanel.style.display = 'none'; return; }

    var sc = c.score || {};
    var dims = ['clarity', 'specificity', 'resourceEvidence', 'alignment', 'recency'];
    var dimColors = ['#3B82F6', '#22C55E', '#F59E0B', '#8B5CF6', '#06B6D4'];

    var html = '';
    html += '<div class="gv-hv-detail-head">';
    html += '<div class="gv-hv-detail-id">' + c.id + '</div>';
    html += '<button class="gv-hv-detail-close" onclick="document.getElementById(\'gv-hv-detail\').style.display=\'none\'">✕ 关闭</button>';
    html += '</div>';

    html += '<div class="gv-hv-detail-section"><h4>Summary</h4><p>' + (c.summary || '无摘要') + '</p></div>';

    html += '<div class="gv-hv-detail-section"><h4>五维评分分解 (总评: ' + (sc.total || 0) + ' / ' + (c.grade || 'D') + ')</h4>';
    dims.forEach(function (d, i) {
      var val = sc[d] || 0;
      html += '<div class="gv-hv-score-bar">';
      html += '<span class="gv-hv-score-label">' + d + '</span>';
      html += '<div class="gv-hv-score-fill" style="width:' + val + '%;background:' + dimColors[i] + '"></div>';
      html += '<span class="gv-hv-score-val">' + val + '</span>';
      html += '</div>';
    });
    html += '</div>';

    html += '<div class="gv-hv-detail-section"><h4>元数据</h4><p>';
    html += '类型: ' + (c.type || '—') + ' | 置信度: ' + (c.confidence || '—') + ' | 状态: ' + (c.status || '—');
    html += ' | 去向: ' + (c.promotion || 'none') + ' | Tags: ' + ((c.tags || []).join(', ') || '—');
    html += '</p></div>';

    html += '<div class="gv-hv-detail-section"><h4>裁定操作</h4>';
    html += '<textarea class="gv-hv-review-notes" id="gv-hv-review-notes" placeholder="裁定备注（可选）..." rows="2"></textarea>';
    html += '<div class="gv-hv-action-buttons">';
    html += '<button class="gv-hv-btn accept" id="gv-hv-btn-accept">✓ 接受 (Accept)</button>';
    html += '<button class="gv-hv-btn reject" id="gv-hv-btn-reject">✕ 拒绝 (Reject)</button>';
    html += '<button class="gv-hv-btn defer" id="gv-hv-btn-defer">↩ 延后 (Defer)</button>';
    html += '</div></div>';

    html += '<div class="gv-hv-detail-section"><h4>锚点证据</h4><div class="gv-hv-anchor-snippet" id="gv-hv-anchor-content">加载中...</div></div>';

    detailInner.innerHTML = html;
    detailPanel.style.display = 'block';

    // bind review buttons
    var btns = ['accept', 'reject', 'defer'];
    btns.forEach(function (d) {
      var btn = document.getElementById('gv-hv-btn-' + d);
      if (btn) {
        btn.addEventListener('click', function () { reviewCandidate(candidateId, d); });
      }
    });

    // async load anchor
    var anchor = c.anchor || {};
    if (anchor.session_id && (anchor.line_range || []).length === 2) {
      api('/harvest/candidates/' + encodeURIComponent(c.id) + '/anchor').then(function (data) {
        var ac = document.getElementById('gv-hv-anchor-content');
        if (!ac) return;
        if (data.error) { ac.textContent = '无法加载锚点: ' + data.error; return; }
        var snip = data.snippet || [];
        var text = '';
        snip.forEach(function (s) {
          text += '<div class="gv-hv-anchor-line"><span class="gv-hv-anchor-lineno">' + s.line + '</span><span class="gv-hv-anchor-content">' + escapeHtml(s.content) + '</span></div>';
        });
        ac.innerHTML = text || '(空锚点)';
      }).catch(function () {
        var ac = document.getElementById('gv-hv-anchor-content');
        if (ac) ac.textContent = '锚点加载失败';
      });
    } else {
      document.getElementById('gv-hv-anchor-content').textContent = '(无锚点)';
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function reviewCandidate(candidateId, decision) {
    var notesEl = document.getElementById('gv-hv-review-notes');
    var notes = notesEl ? notesEl.value : '';

    var btns = ['accept', 'reject', 'defer'];
    btns.forEach(function (d) {
      var btn = document.getElementById('gv-hv-btn-' + d);
      if (btn) btn.disabled = true;
    });

    api('/harvest/candidates/' + encodeURIComponent(candidateId) + '/review', {
      method: 'POST',
      body: { decision: decision, notes: notes },
    }).then(function (res) {
      if (res.ok) {
        document.getElementById('gv-hv-detail').style.display = 'none';
        loadAll();
      }
    }).catch(function (err) {
      alert('裁定失败: ' + err.message);
      btns.forEach(function (d) {
        var btn = document.getElementById('gv-hv-btn-' + d);
        if (btn) btn.disabled = false;
      });
    });
  }

  // ── Main load ──
  function loadAll() {
    api('/harvest/status').then(function (data) {
      renderMetrics(data);
      renderCharts(data);
      renderTriggers(data.triggers || {});
    }).catch(function (err) {
      console.error('Harvest status load failed:', err);
    });

    api('/harvest/candidates').then(function (data) {
      renderTable(data.candidates || []);
    }).catch(function (err) {
      console.error('Candidates load failed:', err);
    });
  }

  // ── Init ──
  document.addEventListener('DOMContentLoaded', function () {
    renderPipeline();
    loadAll();
  });
})();
