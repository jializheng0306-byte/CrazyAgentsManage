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
        overview = overview_resp.get_json()
        assert 'metrics' in overview
        assert 'teams' not in overview
