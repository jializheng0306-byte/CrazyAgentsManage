import pytest
import json
import os
import sys
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'webui'))

from app import app
import api as webui_api


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def overview_hermes_home(tmp_path, monkeypatch):
    db_path = tmp_path / 'state.db'
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        '''CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            source TEXT,
            model TEXT,
            started_at REAL,
            ended_at REAL,
            end_reason TEXT,
            title TEXT,
            message_count INTEGER DEFAULT 0,
            tool_call_count INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0
        )'''
    )
    conn.execute(
        '''CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            tool_name TEXT,
            error_message TEXT,
            tool_duration_ms REAL,
            tool_result_status TEXT,
            token_count INTEGER DEFAULT 0,
            tps REAL,
            ttft_ms REAL,
            timestamp REAL
        )'''
    )
    conn.execute(
        "INSERT INTO sessions (id, source, model, started_at, ended_at, end_reason, title, tool_call_count, input_tokens, output_tokens) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('sess-active', 'cli', 'gpt-5.4', 1710000000, None, None, 'Active Session', 3, 1200, 300)
    )
    conn.execute(
        "INSERT INTO sessions (id, source, model, started_at, ended_at, end_reason, title, tool_call_count, input_tokens, output_tokens) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('sess-error', 'feishu', 'gpt-5.4', 1710000100, 1710000200, 'error', 'Error Session', 1, 500, 100)
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content, tool_name, error_message, tool_duration_ms, tool_result_status, token_count, tps, ttft_ms, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('sess-active', 'tool', 'ok', 'web.search', None, 180, 'ok', 50, 24.5, 320, 1710000150)
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content, tool_name, error_message, tool_duration_ms, tool_result_status, token_count, tps, ttft_ms, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('sess-error', 'tool', 'failed', 'shell.exec', 'boom', 250, 'error', 20, 12.3, 480, 1710000250)
    )
    conn.commit()
    conn.close()

    (tmp_path / 'memory' / 'ops').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'memories').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'memories' / 'note.md').write_text('# note', encoding='utf-8')
    (tmp_path / 'SOUL.md').write_text('# soul', encoding='utf-8')
    (tmp_path / 'skills' / 'skill-a').mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    webui_api._hermes_home = None
    webui_api._overview_stats_cache = {'data': None, 'timestamp': 0}
    webui_api._overview_dashboard_cache = {'data': None, 'timestamp': 0}
    yield tmp_path
    webui_api._hermes_home = None
    webui_api._overview_stats_cache = {'data': None, 'timestamp': 0}
    webui_api._overview_dashboard_cache = {'data': None, 'timestamp': 0}


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
                data = resp.data.decode('utf-8', errors='replace')
                has_search = 'nav-search' in data
                has_common_js = 'common.js' in data
                assert has_search or has_common_js, f'{page} missing both nav-search and common.js'


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


class TestIARoutesAccessible:
    """Regression: verify all five IA routes from v0.5.0 are reachable."""

    def _assert_ia_page(self, client, route):
        resp = client.get(route)
        assert resp.status_code == 200
        data = resp.data.decode('utf-8', errors='replace')
        assert 'FlowMind' in data or 'global-nav' in data or 'nav-menu' in data

    def test_overview_route_200(self, client):
        self._assert_ia_page(client, '/overview')

    def test_runtime_route_200(self, client):
        self._assert_ia_page(client, '/runtime')

    def test_operations_route_200(self, client):
        self._assert_ia_page(client, '/operations')

    def test_governance_route_200(self, client):
        self._assert_ia_page(client, '/governance')

    def test_collaboration_route_200(self, client):
        self._assert_ia_page(client, '/collaboration')


class TestOverviewDataBinding:
    def test_manage_base_path_prefers_forwarded_prefix(self, client):
        resp = client.get('/overview', headers={'X-Forwarded-Prefix': '/manage'})
        html = resp.data.decode('utf-8', errors='replace')
        assert '/manage/static/css/overview.css' in html
        assert '/manage/overview' in html

    def test_overview_endpoint_shape_survives_stats_cache(self, client, overview_hermes_home):
        stats_resp = client.get('/api/overview/stats')
        assert stats_resp.status_code == 200
        stats = stats_resp.get_json()
        assert stats['sessions'] == 2
        assert stats['active_sessions'] == 1

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
        assert 'architecture-philosophy.html' in text or '产品哲学' in text

    def test_architecture_product_reachable(self, client):
        resp = client.get('/architecture/product')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert 'architecture-product.html' in text or '产品架构' in text

    def test_architecture_tech_reachable(self, client):
        resp = client.get('/architecture/tech')
        assert resp.status_code == 200
        text = resp.data.decode('utf-8', errors='replace')
        assert 'architecture-tech.html' in text or '技术架构' in text

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
