import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'webui'))

from app import app
from executor_bridge import HttpExecutorProvider


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestExecutorHttpProvider:
    def test_get_credentials_returns_binding_health_only(self, monkeypatch):
        provider = HttpExecutorProvider(base_url='http://executor.local', scope_id='scope-1')

        monkeypatch.setattr(
            provider,
            'get_sources',
            lambda: [
                {
                    'id': 'src-openapi',
                    'type': 'openapi',
                    'scope': 'scope-1',
                    'status': 'healthy',
                    'toolCount': 2,
                    'provider': 'openapi',
                    'isControl': False,
                }
            ],
        )
        monkeypatch.setattr(
            provider,
            '_list_source_bindings',
            lambda source: [
                {
                    'sourceId': source['id'],
                    'sourceScopeId': source['scope'],
                    'scopeId': 'scope-1',
                    'slot': 'header:authorization',
                    'value': {
                        'kind': 'secret',
                        'secretId': 'secret-1',
                        'secretScopeId': 'scope-1',
                    },
                }
            ],
        )
        monkeypatch.setattr(
            provider,
            '_get',
            lambda path, timeout=5: {'status': 'healthy'} if path.endswith('/secrets/secret-1/status') else None,
        )

        creds = provider.get_credentials()

        assert len(creds) == 1
        assert creds[0]['targetType'] == 'source'
        assert creds[0]['targetId'] == 'src-openapi'
        assert creds[0]['slot'] == 'header:authorization'
        assert creds[0]['status'] == 'healthy'

    def test_get_providers_distinguishes_failed_from_degraded(self, monkeypatch):
        provider = HttpExecutorProvider(base_url='http://executor.local', scope_id='scope-1')
        monkeypatch.setattr(
            provider,
            'get_sources',
            lambda: [
                {'id': 'src-a', 'provider': 'openapi', 'status': 'failed', 'toolCount': 2},
                {'id': 'src-b', 'provider': 'openapi', 'status': 'failed', 'toolCount': 1},
                {'id': 'src-c', 'provider': 'graphql', 'status': 'healthy', 'toolCount': 4},
                {'id': 'src-d', 'provider': 'graphql', 'status': 'missing-auth', 'toolCount': 2},
            ],
        )

        providers = {item['provider']: item for item in provider.get_providers()}

        assert providers['openapi']['status'] == 'failed'
        assert providers['graphql']['status'] == 'degraded'
        assert providers['openapi']['issueSummary']
        assert providers['graphql']['issueSummary']

    def test_get_tools_derives_schema_summary_from_input_schema(self, monkeypatch):
        provider = HttpExecutorProvider(base_url='http://executor.local', scope_id='scope-1')
        monkeypatch.setattr(
            provider,
            '_get',
            lambda path, timeout=5: [
                {
                    'id': 'tool-1',
                    'sourceId': 'src-openapi',
                    'name': 'Create Widget',
                    'description': 'Create a widget via OpenAPI',
                    'requiresApproval': False,
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'priority': {'type': 'string'},
                        },
                    },
                }
            ],
        )

        tools = provider.get_tools(source_id='src-openapi')

        assert len(tools) == 1
        assert tools[0]['schemaSummary'] == 'object · 2 fields (name, priority)'
        assert tools[0]['status'] == 'available'

    def test_get_summary_counts_failed_providers(self, monkeypatch):
        provider = HttpExecutorProvider(base_url='http://executor.local', scope_id='scope-1')
        monkeypatch.setattr(
            provider,
            'get_sources',
            lambda: [
                {'id': 'src-a', 'provider': 'openapi', 'status': 'failed', 'toolCount': 2},
                {'id': 'src-b', 'provider': 'graphql', 'status': 'healthy', 'toolCount': 4},
            ],
        )
        monkeypatch.setattr(
            provider,
            'get_tools',
            lambda source_id='': [
                {'id': 'tool-1'},
                {'id': 'tool-2'},
                {'id': 'tool-3'},
            ],
        )
        monkeypatch.setattr(
            provider,
            'get_credentials',
            lambda: [
                {'id': 'cred-1', 'status': 'missing'},
                {'id': 'cred-2', 'status': 'healthy'},
            ],
        )
        monkeypatch.setattr(
            provider,
            'get_providers',
            lambda: [
                {'provider': 'openapi', 'status': 'failed'},
                {'provider': 'graphql', 'status': 'reachable'},
            ],
        )

        summary = provider.get_summary()

        assert summary['providerCount'] == 2
        assert summary['failedProviderCount'] == 1
        assert summary['missingCredentialCount'] == 1


class TestExecutorOperationsUiAssets:
    def test_operations_js_exposes_schema_summary_language(self, client):
        resp = client.get('/static/js/operations.js')
        assert resp.status_code == 200
        data = resp.data.decode('utf-8', errors='replace')
        assert 'Schema 摘要' in data
        assert '/api/operations/integrations/summary' in data
        assert 'Credential Health' in data
