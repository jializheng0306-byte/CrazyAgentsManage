import pytest
import json
import os
import sys
import tempfile
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'webui'))

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_hermes_home(tmp_path):
    db_path = tmp_path / 'state.db'
    conn = sqlite3.connect(str(db_path))
    conn.execute('''CREATE TABLE sessions (
        id TEXT PRIMARY KEY,
        source TEXT,
        model TEXT,
        created_at REAL,
        updated_at REAL,
        status TEXT DEFAULT 'active'
    )''')
    conn.execute('''CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        content TEXT,
        timestamp REAL,
        tokens INTEGER DEFAULT 0,
        model TEXT,
        cost REAL DEFAULT 0
    )''')
    conn.execute('''CREATE TABLE tool_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        tool_name TEXT,
        timestamp REAL
    )''')

    for i in range(3):
        conn.execute(
            'INSERT INTO sessions (id, source, model, created_at, updated_at, status) VALUES (?, ?, ?, ?, ?, ?)',
            (f'sess-{i}', 'cli' if i % 2 == 0 else 'telegram', 'gpt-4o',
             1700000000 + i * 1000, 1700001000 + i * 1000, 'active')
        )
    for i in range(6):
        conn.execute(
            'INSERT INTO messages (session_id, role, content, timestamp, tokens, model, cost) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (f'sess-{i % 3}', 'user' if i % 2 == 0 else 'assistant',
             f'message {i}', 1700000500 + i * 100, 100 * (i + 1), 'gpt-4o', 0.001 * (i + 1))
        )
    conn.commit()
    conn.close()

    jobs_path = tmp_path / 'cron' / 'jobs.json'
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(json.dumps([
        {'id': 'job-1', 'name': 'Test Job', 'schedule': '0 * * * *', 'status': 'active'}
    ]))

    gw_path = tmp_path / 'gateway_state.json'
    gw_path.write_text(json.dumps({
        'platforms': {'cli': {'connected': True}, 'telegram': {'connected': False}}
    }))

    memory_dir = tmp_path / 'memory'
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / 'default').mkdir(parents=True, exist_ok=True)
    (memory_dir / 'default' / 'role.md').write_text('# Default Role\nTest content')

    skills_dir = tmp_path / 'skills'
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / 'test-skill.md').write_text('# Test Skill\nSkill content')

    return tmp_path


class TestPageRoutes:
    def test_home_page(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'home.js' in resp.data

    def test_dashboard_page(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 200
        assert b'dashboard.js' in resp.data

    def test_sessions_page(self, client):
        resp = client.get('/sessions')
        assert resp.status_code == 200
        assert b'sessions.js' in resp.data

    def test_agent_page(self, client):
        resp = client.get('/agent')
        assert resp.status_code == 200
        assert b'agent.js' in resp.data

    def test_graph_page(self, client):
        resp = client.get('/graph')
        assert resp.status_code == 200
        assert b'graph.js' in resp.data

    def test_tokens_page(self, client):
        resp = client.get('/tokens')
        assert resp.status_code == 200
        assert b'tokens.js' in resp.data

    def test_alerts_page(self, client):
        resp = client.get('/alerts')
        assert resp.status_code == 200
        assert b'alerts.js' in resp.data

    def test_team_memory_page(self, client):
        resp = client.get('/team-memory')
        assert resp.status_code == 200
        assert b'team-memory.js' in resp.data

    def test_skills_page(self, client):
        resp = client.get('/skills')
        assert resp.status_code == 200
        assert b'skills.js' in resp.data

    def test_cron_page(self, client):
        resp = client.get('/cron')
        assert resp.status_code == 200
        assert b'cron.js' in resp.data

    def test_tasks_page(self, client):
        resp = client.get('/tasks')
        assert resp.status_code == 200
        assert b'tasks.js' in resp.data


class TestCommonJsIncluded:
    def test_home_includes_common(self, client):
        resp = client.get('/')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        home_pos = html.find('home.js')
        assert common_pos > 0
        assert home_pos > 0
        assert common_pos < home_pos

    def test_dashboard_includes_common(self, client):
        resp = client.get('/dashboard')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        dashboard_pos = html.find('dashboard.js')
        assert common_pos > 0
        assert dashboard_pos > 0
        assert common_pos < dashboard_pos

    def test_agent_includes_common(self, client):
        resp = client.get('/agent')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        agent_pos = html.find('agent.js')
        assert common_pos > 0
        assert agent_pos > 0
        assert common_pos < agent_pos

    def test_graph_includes_common(self, client):
        resp = client.get('/graph')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        graph_pos = html.find('graph.js')
        assert common_pos > 0
        assert graph_pos > 0
        assert common_pos < graph_pos

    def test_tokens_includes_common(self, client):
        resp = client.get('/tokens')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        tokens_pos = html.find('tokens.js')
        assert common_pos > 0
        assert tokens_pos > 0
        assert common_pos < tokens_pos

    def test_alerts_includes_common(self, client):
        resp = client.get('/alerts')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        alerts_pos = html.find('alerts.js')
        assert common_pos > 0
        assert alerts_pos > 0
        assert common_pos < alerts_pos

    def test_tasks_includes_common(self, client):
        resp = client.get('/tasks')
        html = resp.data.decode()
        common_pos = html.find('common.js')
        tasks_pos = html.find('tasks.js')
        assert common_pos > 0
        assert tasks_pos > 0
        assert common_pos < tasks_pos


class TestStaticAssets:
    def test_common_js_served(self, client):
        resp = client.get('/static/js/common.js')
        assert resp.status_code == 200
        data = resp.data.decode()
        assert 'function escapeHtml' in data
        assert 'function formatTokenCount' in data
        assert 'function formatDuration' in data
        assert 'function formatTime' in data
        assert 'function formatSize' in data
        assert 'function sanitizeColor' in data
        assert 'function getSourceEmoji' in data
        assert 'function truncate' in data

    def test_no_app_base_in_js(self, client):
        js_files = [
            '/static/js/home.js', '/static/js/dashboard.js', '/static/js/sessions.js',
            '/static/js/agent.js', '/static/js/graph.js', '/static/js/tokens.js',
            '/static/js/alerts.js', '/static/js/team-memory.js', '/static/js/skills.js',
            '/static/js/cron.js', '/static/js/tasks.js',
        ]
        for js_file in js_files:
            resp = client.get(js_file)
            if resp.status_code == 200:
                data = resp.data.decode()
                assert 'window.APP_BASE' not in data, f'{js_file} still contains window.APP_BASE'

    def test_no_dup_escape_html(self, client):
        js_files = [
            '/static/js/home.js', '/static/js/dashboard.js', '/static/js/sessions.js',
            '/static/js/agent.js', '/static/js/graph.js', '/static/js/tokens.js',
            '/static/js/alerts.js', '/static/js/team-memory.js', '/static/js/skills.js',
            '/static/js/cron.js', '/static/js/tasks.js',
        ]
        for js_file in js_files:
            resp = client.get(js_file)
            if resp.status_code == 200:
                data = resp.data.decode()
                assert 'function escapeHtml' not in data, f'{js_file} still has duplicate escapeHtml'

    def test_design_system_css_served(self, client):
        resp = client.get('/static/css/design-system.css')
        assert resp.status_code == 200


class TestAPIEndpoints:
    def test_overview_stats(self, client):
        resp = client.get('/api/overview/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_dashboard_stats(self, client):
        resp = client.get('/api/dashboard/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_sessions_list(self, client):
        resp = client.get('/api/sessions/list')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, (list, dict))

    def test_tokens_stats(self, client):
        resp = client.get('/api/tokens/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_alerts_list(self, client):
        resp = client.get('/api/alerts/list')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, (list, dict))

    def test_agents_list(self, client):
        resp = client.get('/api/agents/list')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, (list, dict))

    def test_graph_data(self, client):
        resp = client.get('/api/graph/data')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_tasks_list(self, client):
        resp = client.get('/api/tasks/list')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_cron_list(self, client):
        resp = client.get('/api/cron/list')
        assert resp.status_code == 200

    def test_skills_list(self, client):
        resp = client.get('/api/skills/list')
        assert resp.status_code == 200

    def test_memory_teams(self, client):
        resp = client.get('/api/overview/teams')
        assert resp.status_code == 200

    def test_config(self, client):
        resp = client.get('/api/config')
        assert resp.status_code == 200


class TestAgentPageEnhancements:
    def test_agent_js_has_detail_modal(self, client):
        resp = client.get('/static/js/agent.js')
        data = resp.data.decode()
        assert 'showAgentDetail' in data
        assert 'agentDetailModal' in data

    def test_agent_js_has_source_filter(self, client):
        resp = client.get('/static/js/agent.js')
        data = resp.data.decode()
        assert 'filterSource' in data or 'loadAgentCards(' in data


class TestTasksPageEnhancements:
    def test_tasks_js_has_detail_modal(self, client):
        resp = client.get('/static/js/tasks.js')
        data = resp.data.decode()
        assert 'showTaskDetail' in data
        assert 'taskDetailModal' in data

    def test_tasks_js_has_status_filter(self, client):
        resp = client.get('/static/js/tasks.js')
        data = resp.data.decode()
        assert 'filterTasks' in data
        assert 'currentStatusFilter' in data


class TestGraphPageEnhancements:
    def test_graph_js_has_node_detail(self, client):
        resp = client.get('/static/js/graph.js')
        data = resp.data.decode()
        assert 'showNodeDetail' in data
        assert 'nodeDetailModal' in data

    def test_graph_js_no_app_base(self, client):
        resp = client.get('/static/js/graph.js')
        data = resp.data.decode()
        assert 'window.APP_BASE' not in data
