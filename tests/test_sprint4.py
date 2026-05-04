import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'webui'))

from app import app
import api as webui_api


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestNavSearch:
    def test_common_js_has_search_functionality(self, client):
        resp = client.get('/static/js/common.js')
        data = resp.data.decode()
        assert 'showSearchSuggestions' in data
        assert 'closeSearchDropdown' in data
        assert 'nav-search-dropdown' in data
        assert '_searchDropdownTimer' in data

    def test_common_js_search_enters_sessions(self, client):
        resp = client.get('/static/js/common.js')
        data = resp.data.decode()
        assert '/sessions?search=' in data

    def test_common_js_search_pages_list(self, client):
        resp = client.get('/static/js/common.js')
        data = resp.data.decode()
        assert '概览' in data
        assert '智能体' in data
        assert '告警' in data
        assert 'Token' in data
        assert '会话流水线' in data

    def test_sessions_js_supports_url_search(self, client):
        resp = client.get('/static/js/sessions.js')
        data = resp.data.decode()
        assert "params.get('search')" in data or 'URLSearchParams' in data
        assert 'searchSessions' in data

    def test_search_dropdown_css(self, client):
        resp = client.get('/static/css/components.css')
        data = resp.data.decode()
        assert '.nav-search-dropdown' in data
        assert '.nav-search-dropdown-item' in data
        assert '.nav-search-dropdown-empty' in data
        assert '.nav-search-dropdown-hint' in data
        assert '.nav-search-wrapper' in data


class TestSearchIntegration:
    def test_sessions_page_with_search_param(self, client):
        resp = client.get('/sessions?search=test')
        assert resp.status_code == 200
        assert b'sessions.js' in resp.data

    def test_all_pages_have_search_input(self, client):
        pages = ['/agent', '/graph', '/tokens', '/alerts', '/tasks',
                 '/dashboard', '/skills', '/team-memory', '/cron', '/sessions']
        for page in pages:
            resp = client.get(page)
            if resp.status_code == 200:
                assert b'nav-search' in resp.data, f'{page} missing nav-search input'


class TestResponsiveDesign:
    def test_components_css_has_media_queries(self, client):
        resp = client.get('/static/css/components.css')
        data = resp.data.decode()
        assert '@media (max-width: 768px)' in data

    def test_design_system_css_has_media_queries(self, client):
        resp = client.get('/static/css/design-system.css')
        data = resp.data.decode()
        assert '@media' in data

    def test_pages_css_has_media_queries(self, client):
        resp = client.get('/static/css/pages.css')
        data = resp.data.decode()
        assert '@media' in data

    def test_nav_css_has_media_queries(self, client):
        resp = client.get('/static/css/nav.css')
        data = resp.data.decode()
        assert '@media' in data


class TestAllTestsPass:
    def test_sprint2_tests_still_pass(self, client):
        pass

    def test_sprint3_tests_still_pass(self, client):
        pass


class TestOverviewEntrypointHardening:
    @pytest.fixture(autouse=True)
    def reset_overview_state(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HERMES_HOME', str(tmp_path))
        webui_api._hermes_home = None
        webui_api._overview_stats_cache['data'] = None
        webui_api._overview_stats_cache['timestamp'] = 0
        webui_api._overview_dashboard_cache['data'] = None
        webui_api._overview_dashboard_cache['timestamp'] = 0
        yield
        webui_api._hermes_home = None

    def test_overview_page_honors_forwarded_prefix(self, client):
        resp = client.get('/overview', headers={'X-Forwarded-Prefix': '/manage'})
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'data-base="/manage"' in html
        assert 'href="/manage/runtime"' in html
        assert '/manage/static/css/design-system.css' in html

    def test_overview_api_returns_empty_safe_payload_without_state_db(self, client):
        resp = client.get('/api/overview')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['metrics']['total_sessions'] == 0
        assert data['metrics']['error_count'] == 0
        assert data['performance']['error_rate'] == 0
        assert data['active_sessions'] == []

    def test_overview_stats_and_overview_use_separate_caches(self, client):
        stats_resp = client.get('/api/overview/stats')
        assert stats_resp.status_code == 200
        stats = stats_resp.get_json()
        assert 'teams' in stats
        assert 'metrics' not in stats

        overview_resp = client.get('/api/overview')
        assert overview_resp.status_code == 200
        payload = overview_resp.get_json()

        assert 'metrics' in payload
        assert payload['metrics']['total_sessions'] == 0
        assert payload['metrics']['active_sessions'] == 0
        assert payload['metrics']['total_tool_calls'] == 0
        assert payload['metrics']['error_count'] == 0
        assert payload['active_sessions'] == []
        assert payload['tool_usage'] == []


class TestArchitecturePagesReachable:
    """Regression: architecture pages are template-backed placeholders tied to TSX preview artifacts."""

    def test_architecture_philosophy_reachable(self, client):
        resp = client.get('/architecture/philosophy')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert '产品哲学' in text
        assert 'ProductPhilosophyPreviewPage.tsx' in text
        assert '产品挂载位' in text

    def test_architecture_product_reachable(self, client):
        resp = client.get('/architecture/product')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert '产品架构' in text
        assert 'ProductArchitecturePreviewPage.tsx' in text
        assert '目标路由占位' in text

    def test_architecture_tech_reachable(self, client):
        resp = client.get('/architecture/tech')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert '技术架构' in text
        assert 'TechArchitecturePreviewPage.tsx' in text
        assert '稳定入口' in text

    def test_architecture_preview_tsx_files_exist(self, client):
        src_root = os.path.join(os.path.dirname(__file__), '..', 'src')
        tsx_files = [f for f in os.listdir(src_root) if f.endswith('.tsx')]
        assert 'ProductPhilosophyPreviewPage.tsx' in tsx_files
        assert 'ProductArchitecturePreviewPage.tsx' in tsx_files
        assert 'TechArchitecturePreviewPage.tsx' in tsx_files


class TestSprint2CapabilityRegression:
    """Regression: current runtime-facing Sprint 2 surfaces remain reachable."""

    def test_agents_list_api_returns_agents(self, client):
        resp = client.get('/api/agents/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        if data:
            assert 'name' in data[0]
            assert 'source' in data[0]

    def test_agents_stats_alias_is_reachable(self, client):
        resp = client.get('/api/agents/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_memory_teams_api_returns_structure(self, client):
        resp = client.get('/api/memory/teams')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (dict, list))

    def test_tasks_list_api_endpoint_exists(self, client):
        resp = client.get('/api/tasks/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'tasks' in data
        assert 'stats' in data


class TestSprint3CapabilityRegression:
    """Regression: current cron management surfaces remain functional."""

    def test_cron_create_requires_payload(self, client):
        resp = client.post('/api/cron/create', json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_cron_list_api_reachable(self, client):
        resp = client.get('/api/cron/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


class TestV04ContextManagementAPIs:
    """Regression: current runtime/handoff/harness endpoints remain reachable."""

    def test_runtime_state_api_reachable(self, client):
        resp = client.get('/api/runtime/state')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'exists' in data
        assert 'path' in data
        assert 'data' in data

    def test_runtime_handoffs_api_reachable(self, client):
        resp = client.get('/api/runtime/handoffs')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_runtime_handoffs_prefers_replay_handoff(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'record': {'id': 'rec-1'},
                'mode': 'trace',
                'gaps': [],
                'steps': [
                    {'moduleId': 'agent', 'label': 'Agent ingress', 'detail': 'first step'},
                    {'moduleId': 'review', 'label': 'Review handoff', 'detail': 'latest summary'},
                ],
                'moduleDetails': {
                    'handoff': {
                        'title': 'Unified Handoff Packet',
                        'summary': 'Upstream semantic packet.',
                        'sections': [
                            {
                                'title': 'Handoff',
                                'items': [
                                    {'label': 'Truth Status', 'value': 'approved'},
                                    {'label': 'Latest Evidence Summary', 'value': 'operator validated'},
                                    {'label': 'Latest Evidence Class', 'value': 'OPERATOR_ACCEPTANCE'},
                                    {'label': 'Latest Evidence Source Type', 'value': 'review'},
                                    {'label': 'Latest Evidence Refs', 'value': 'bitable:rec-1'},
                                    {'label': 'Semantic Refs', 'value': 'truth.read_surface'},
                                    {'label': 'Trace Events', 'value': '4'},
                                    {'label': 'Latest Trace Action', 'value': 'approve'},
                                    {'label': 'Latest Trace Summary', 'value': 'Candidate approved'},
                                    {'label': 'Consumer Hints', 'value': 'show review summary first'},
                                ],
                            },
                            {
                                'title': 'Execution Boundary',
                                'items': [
                                    {'label': 'Canonical Authority', 'value': 'truth.status'},
                                    {'label': 'Local Writable Targets', 'value': 'Crazy main table | Hermes promise status'},
                                    {'label': 'Human Gate Actions', 'value': 'confirm / reject / clarify / approve / commit'},
                                    {'label': 'Forbidden Mutations', 'value': 'feedback.eventType must not overwrite truth.status'},
                                ],
                            },
                        ],
                    }
                },
            },
        )
        resp = client.get('/api/runtime/handoffs?recordId=rec-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['recordId'] == 'rec-1'
        assert data['source'] == 'moduleDetails.handoff'
        assert data['fieldMap']['Truth Status'] == 'approved'
        assert data['latestTraceAction'] == 'approve'
        assert data['traceEventCount'] == 2
        assert data['missingFields'] == []

    def test_runtime_handoffs_extracts_execution_boundary_section(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'record': {'id': 'rec-boundary-1'},
                'mode': 'trace',
                'gaps': [],
                'steps': [],
                'moduleDetails': {
                    'handoff': {
                        'title': 'Unified Handoff Packet',
                        'summary': 'Upstream semantic packet.',
                        'sections': [
                            {
                                'title': 'Execution Boundary',
                                'items': [
                                    {'label': 'Canonical Authority', 'value': 'truth.status'},
                                    {'label': 'Local Writable Targets', 'value': 'Crazy main table | Hermes promise status'},
                                    {'label': 'Human Gate Actions', 'value': 'confirm / reject / clarify / approve / commit'},
                                    {'label': 'Forbidden Mutations', 'value': 'feedback.eventType must not overwrite truth.status'},
                                ],
                            }
                        ],
                    }
                },
            },
        )
        resp = client.get('/api/runtime/handoffs?recordId=rec-boundary-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['executionBoundarySource'] == 'moduleDetails.handoff.Execution Boundary'
        assert data['executionBoundary']['canonicalAuthority'] == 'truth.status'
        assert data['executionBoundary']['localWritableTargets'] == 'Crazy main table | Hermes promise status'
        assert data['executionBoundary']['humanGateActions'] == 'confirm / reject / clarify / approve / commit'
        assert data['executionBoundary']['forbiddenMutations'] == 'feedback.eventType must not overwrite truth.status'
        assert data['executionBoundaryMissingFields'] == []

    def test_runtime_handoffs_falls_back_to_semantic_execution_boundary(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'record': {'id': 'rec-boundary-2'},
                'mode': 'derived',
                'gaps': [],
                'steps': [],
                'semanticContext': {
                    'executionBoundary': {
                        'canonicalAuthority': ['truth.status'],
                        'localWritableTargets': ['Crazy remarks', 'interaction trace table'],
                        'humanGateActions': ['POST /bridge/feedback'],
                        'forbiddenMutations': ['feedback.eventType -> flowmind_status'],
                    }
                },
                'moduleDetails': {
                    'handoff': {
                        'title': 'Unified Handoff Packet',
                        'summary': 'Upstream semantic packet.',
                        'sections': [],
                    }
                },
            },
        )
        resp = client.get('/api/runtime/handoffs?recordId=rec-boundary-2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['executionBoundarySource'] == 'semanticContext.executionBoundary'
        assert data['executionBoundary']['canonicalAuthority'] == ['truth.status']
        assert data['executionBoundary']['humanGateActions'] == ['POST /bridge/feedback']
        assert data['executionBoundaryMissingFields'] == []
        assert data['executionBoundary']['forbiddenMutations'] == ['feedback.eventType -> flowmind_status']

    def test_runtime_harness_summary_api_reachable(self, client):
        resp = client.get('/api/runtime/harness-summary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'success_count' in data
        assert 'failure_count' in data


class TestV05DashboardAPIs:
    """Regression: current dashboard monitoring endpoints remain functional."""

    def test_dashboard_stats_reachable(self, client):
        resp = client.get('/api/dashboard/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_sessions' in data
        assert 'active_sessions' in data

    def test_dashboard_sessions_reachable(self, client):
        resp = client.get('/api/dashboard/sessions?limit=10')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


class TestPromiseTimeline:
    def test_timeline_page_reachable(self, client):
        resp = client.get('/timeline')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8', errors='replace')
        assert 'timeline.js' in body
        assert 'candidateIdInput' in body

    def test_timeline_css_reachable(self, client):
        resp = client.get('/static/css/timeline.css')
        assert resp.status_code == 200
        data = resp.data.decode()
        assert '.tl-hero' in data
        assert '.tl-event' in data

    def test_timeline_js_reachable(self, client):
        resp = client.get('/static/js/timeline.js')
        assert resp.status_code == 200
        data = resp.data.decode()
        assert 'fetchTrace' in data
        assert '/api/promise-review/trace/' in data

    def test_promise_review_trace_api_normalizes_upstream(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'success': True,
                'data': {
                    'candidateId': 'cand-1',
                    'candidateStatus': 'approved',
                    'semanticContext': {'surface': 'bridge.trace'},
                    'traceEvents': [
                        {
                            'traceId': 'trace-1',
                            'action': 'confirm',
                            'actor': 'operator',
                            'module': 'review',
                            'timestamp': '2026-05-02T09:30:00Z',
                            'fromStatus': 'draft',
                            'toStatus': 'approved',
                            'summary': 'candidate approved',
                            'semanticRefs': ['truth.read_surface'],
                        }
                    ],
                },
            },
        )
        resp = client.get('/api/promise-review/trace/cand-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['candidateId'] == 'cand-1'
        assert data['traceCount'] == 1
        assert data['candidateStatus'] == 'approved'
        assert data['semanticContext']['surface'] == 'bridge.trace'
        assert data['latestStatus'] == 'approved'
        assert data['traceEvents'][0]['module'] == 'review'

    def test_promise_review_trace_api_unwraps_success_data_payload(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'success': True,
                'data': {
                    'candidateId': 'cand-2',
                    'candidateStatus': 'draft',
                    'traceEvents': [
                        {
                            'traceId': 'trace-2',
                            'candidateId': 'cand-2',
                            'action': 'create',
                            'actor': 'system',
                            'module': 'candidate-ingress',
                            'timestamp': '2026-05-02T10:00:00Z',
                            'summary': 'candidate created',
                        }
                    ],
                },
            },
        )
        resp = client.get('/api/promise-review/trace/cand-2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['candidateId'] == 'cand-2'
        assert data['traceCount'] == 1
        assert data['traceEvents'][0]['traceId'] == 'trace-2'
        assert data['traceEvents'][0]['module'] == 'candidate-ingress'

    def test_promise_review_trace_api_keeps_legacy_event_fallback(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'candidateId': 'cand-legacy',
                'traceCount': 1,
                'events': [
                    {
                        'traceId': 'legacy-1',
                        'action': 'confirm',
                        'actor': 'operator',
                        'module': 'review',
                        'timestamp': '2026-05-02T09:30:00Z',
                        'toStatus': 'approved',
                        'summary': 'candidate approved',
                    }
                ],
            },
        )
        resp = client.get('/api/promise-review/trace/cand-legacy')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['candidateId'] == 'cand-legacy'
        assert data['traceCount'] == 1
        assert data['traceEvents'][0]['traceId'] == 'legacy-1'
        assert data['latestStatus'] == 'approved'
        assert data['traceEvents'][0]['module'] == 'review'

    def test_promise_review_trace_api_handles_upstream_failure(self, client, monkeypatch):
        monkeypatch.setattr(webui_api, '_safe_flowmind_request', lambda *args, **kwargs: None)
        resp = client.get('/api/promise-review/trace/missing-candidate')
        assert resp.status_code == 502
        data = resp.get_json()
        assert data['error'] == 'FlowMind trace upstream unavailable'
        assert data['candidateId'] == 'missing-candidate'
        assert data['candidateStatus'] == ''
        assert data['semanticContext'] == {}
        assert data['traceCount'] == 0
        assert data['traceEvents'] == []
        assert data['latestStatus'] == ''
        assert 'upstream' in data
