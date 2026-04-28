import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'webui'))

from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestComponentsCss:
    def test_components_css_served(self, client):
        resp = client.get('/static/css/components.css')
        assert resp.status_code == 200
        data = resp.data.decode()
        assert '.modal-overlay' in data
        assert '.modal-content' in data
        assert '.detail-grid' in data
        assert '.status-badge' in data
        assert '.filter-bar' in data
        assert '.empty-state' in data
        assert '.agent-card' in data
        assert '.token-bar-track' in data
        assert '.alert-item' in data
        assert '.dag-node' in data
        assert '.graph-node-wrapper' in data
        assert '.time-range-selector' in data

    def test_components_css_in_templates(self, client):
        pages = ['/', '/agent', '/graph', '/tokens', '/alerts', '/tasks']
        for page in pages:
            resp = client.get(page)
            if resp.status_code == 200:
                assert b'components.css' in resp.data, f'{page} missing components.css'


class TestCssClassUsage:
    def test_agent_js_uses_modal_classes(self, client):
        resp = client.get('/static/js/agent.js')
        data = resp.data.decode()
        assert 'modal-overlay' in data
        assert 'modal-content' in data
        assert 'modal-close' in data
        assert 'modal-header' in data
        assert 'detail-grid' in data
        assert 'detail-cell' in data
        assert 'detail-label' in data
        assert 'detail-value' in data
        assert 'status-badge' in data

    def test_tasks_js_uses_css_classes(self, client):
        resp = client.get('/static/js/tasks.js')
        data = resp.data.decode()
        assert 'modal-overlay' in data
        assert 'modal-content' in data
        assert 'dag-node' in data
        assert 'dag-node-header' in data
        assert 'dag-node-name' in data
        assert 'dag-layer-connector' in data
        assert 'task-row' in data
        assert 'task-row-name' in data
        assert 'filter-bar' in data
        assert 'empty-state' in data

    def test_graph_js_uses_css_classes(self, client):
        resp = client.get('/static/js/graph.js')
        data = resp.data.decode()
        assert 'modal-overlay' in data
        assert 'modal-content' in data
        assert 'graph-node-wrapper' in data
        assert 'graph-node-circle' in data
        assert 'graph-node-label' in data
        assert 'graph-node-status-dot' in data
        assert 'detail-grid' in data
        assert 'detail-cell' in data
        assert 'link-more' in data

    def test_tokens_js_uses_css_classes(self, client):
        resp = client.get('/static/js/tokens.js')
        data = resp.data.decode()
        assert 'token-bar-track' in data
        assert 'token-bar-fill' in data
        assert 'empty-state' in data
        assert 'time-range-selector' in data
        assert 'time-range-btn' in data
        assert 'setTimeRange' in data

    def test_alerts_js_has_actions(self, client):
        resp = client.get('/static/js/alerts.js')
        data = resp.data.decode()
        assert 'acknowledgeAlert' in data
        assert 'silenceAlert' in data
        assert 'alert-action-btn' in data
        assert 'alert-icon' in data
        assert 'alert-content' in data
        assert 'alert-actions' in data
        assert 'acknowledgedAlerts' in data
        assert 'silencedAlerts' in data


class TestInlineStyleReduction:
    def test_agent_js_fewer_inline_styles(self, client):
        resp = client.get('/static/js/agent.js')
        data = resp.data.decode()
        style_count = data.count('style=')
        assert style_count < 20, f'agent.js still has {style_count} inline styles (expected < 20)'

    def test_tasks_js_fewer_inline_styles(self, client):
        resp = client.get('/static/js/tasks.js')
        data = resp.data.decode()
        style_count = data.count('style=')
        assert style_count < 20, f'tasks.js still has {style_count} inline styles (expected < 20)'

    def test_graph_js_fewer_inline_styles(self, client):
        resp = client.get('/static/js/graph.js')
        data = resp.data.decode()
        style_count = data.count('style=')
        assert style_count < 25, f'graph.js still has {style_count} inline styles (expected < 25)'


class TestTokensTimeRange:
    def test_tokens_js_has_time_range(self, client):
        resp = client.get('/static/js/tokens.js')
        data = resp.data.decode()
        assert 'currentTimeRange' in data
        assert 'renderTimeRangeSelector' in data
        assert '24h' in data
        assert '7d' in data
        assert '30d' in data
        assert 'all' in data


class TestAlertsActions:
    def test_alerts_js_acknowledge(self, client):
        resp = client.get('/static/js/alerts.js')
        data = resp.data.decode()
        assert 'acknowledgeAlert' in data
        assert 'acknowledgedAlerts' in data

    def test_alerts_js_silence(self, client):
        resp = client.get('/static/js/alerts.js')
        data = resp.data.decode()
        assert 'silenceAlert' in data
        assert 'silencedAlerts' in data
