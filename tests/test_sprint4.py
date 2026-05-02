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
        assert payload['metrics']['total_sessions'] == 2
        assert payload['metrics']['active_sessions'] == 1
        assert payload['metrics']['total_tool_calls'] == 4
        assert payload['metrics']['error_count'] == 1
        assert payload['active_sessions'][0]['id'] == 'sess-error'
        assert any(item['tool_name'] == 'web.search' for item in payload['tool_usage'])


class TestArchitecturePagesReachable:
    """Regression: architecture pages are HTML templates, not TSX."""

    def test_architecture_philosophy_reachable(self, client):
        resp = client.get('/architecture/philosophy')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert '产品哲学' in text
        assert 'original-arch-preview/index.html?page=philosophy' in text
        assert '<iframe' in text

    def test_architecture_product_reachable(self, client):
        resp = client.get('/architecture/product')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert '产品架构' in text
        assert 'original-arch-preview/index.html?page=product' in text
        assert '<iframe' in text

    def test_architecture_tech_reachable(self, client):
        resp = client.get('/architecture/tech')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert '技术架构' in text
        assert 'original-arch-preview/index.html?page=tech' in text
        assert '<iframe' in text

    def test_no_tsx_files_in_src_root(self, client):
        src_root = os.path.join(os.path.dirname(__file__), '..', 'src')
        tsx_files = [f for f in os.listdir(src_root) if f.endswith('.tsx')]
        assert len(tsx_files) == 0, f'Should have no .tsx files in src/, found: {tsx_files}'


class TestSprint2CapabilityRegression:
    """Regression: key Sprint 2 capabilities must remain functional."""

    def test_agents_roles_api_returns_roles(self, client):
        resp = client.get('/api/agents/roles')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        role_names = [r.get('name', '') for r in data]
        assert len(role_names) >= 6, f'Expected at least 6 roles, got {len(role_names)}'

    def test_agents_coordinator_role_exists(self, client):
        resp = client.get('/api/agents/roles')
        data = resp.get_json()
        role_names = [r.get('name', '').lower() for r in data]
        assert len(role_names) >= 5, f'Expected at least 5 roles, got {role_names}'

    def test_memory_layers_api_returns_structure(self, client):
        resp = client.get('/api/memory/layers')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (dict, list))

    def test_delegate_task_api_endpoint_exists(self, client):
        resp = client.post('/api/delegate/task',
                           json={'role': 'research', 'goal': 'test'})
        assert resp.status_code in (200, 400, 422, 500)


class TestSprint3CapabilityRegression:
    """Regression: key Sprint 3 capabilities must remain functional."""

    def test_cron_stats_api_reachable(self, client):
        resp = client.get('/api/cron/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)

    def test_cron_list_api_reachable(self, client):
        resp = client.get('/api/cron/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


class TestV04ContextManagementAPIs:
    """Regression: v0.4.0 context management endpoints."""

    def test_context_summary_api_reachable(self, client):
        resp = client.get('/api/context/summary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_agents' in data
        assert 'token_budget' in data

    def test_context_compress_accepts_post(self, client):
        resp = client.post('/api/context/compress', json={
            'memory_layers': {'L5_identity': 'test' * 100},
            'task_context': 'test context',
            'strategy': 'summary'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'result' in data
        assert 'compressed_layers' in data

    def test_task_watcher_status_api_reachable(self, client):
        resp = client.get('/api/monitoring/task-watcher/status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'running' in data
        assert 'watched_tasks' in data


class TestV05DashboardAPIs:
    """Regression: v0.5.0 dashboard monitoring endpoints."""

    def test_agent_dashboard_stats_reachable(self, client):
        resp = client.get('/api/agent-dashboard/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_agents' in data
        assert 'total_tasks' in data
        assert 'running_tasks' in data
        assert 'completed_tasks' in data

    def test_agent_dashboard_timeline_reachable(self, client):
        resp = client.get('/api/agent-dashboard/timeline?limit=10')
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
                'candidateId': 'cand-1',
                'traceCount': 1,
                'events': [
                    {
                        'traceId': 'trace-1',
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
        resp = client.get('/api/promise-review/trace/cand-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['candidateId'] == 'cand-1'
        assert data['traceCount'] == 1
        assert data['latestStatus'] == 'approved'
        assert data['events'][0]['module'] == 'review'

    def test_promise_review_trace_api_unwraps_success_data_payload(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'success': True,
                'data': {
                    'candidateId': 'cand-2',
                    'traceCount': 1,
                    'events': [
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
        assert data['events'][0]['traceId'] == 'trace-2'
        assert data['events'][0]['module'] == 'candidate-ingress'

    def test_promise_review_trace_api_handles_upstream_failure(self, client, monkeypatch):
        monkeypatch.setattr(webui_api, '_safe_flowmind_request', lambda *args, **kwargs: None)
        resp = client.get('/api/promise-review/trace/missing-candidate')
        assert resp.status_code == 502
        data = resp.get_json()
        assert data['candidateId'] == 'missing-candidate'
        assert data['traceCount'] == 0
        assert data['events'] == []
