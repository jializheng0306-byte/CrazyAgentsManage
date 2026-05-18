import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'webui'))

from app import app
import api as webui_api
from executor_bridge import HttpExecutorProvider, SampleExecutorProvider


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


class TestExecutorSampleProvider:
    def test_sample_provider_source_crud_round_trip(self):
        provider = SampleExecutorProvider()
        created = provider.create_source({
            'name': 'Local Demo Source',
            'type': 'openapi',
            'scope': 'user',
        })

        assert created['name'] == 'Local Demo Source'
        updated = provider.update_source(created['id'], {'status': 'disabled', 'provider': 'openapi'})
        assert updated is not None
        assert updated['status'] == 'disabled'
        assert provider.delete_source(created['id']) is True

    def test_sample_provider_credential_bind_unbind_round_trip(self):
        provider = SampleExecutorProvider()
        credential = provider.bind_credential({
            'provider': 'openapi',
            'targetType': 'source',
            'targetId': 'src-demo',
            'impactCount': 3,
        })

        assert credential['targetId'] == 'src-demo'
        assert credential['impactCount'] == 3
        assert provider.unbind_credential(credential['id']) is True


class TestExecutorIntegrationApi:
    def test_create_source_requires_type_specific_fields(self, client):
        resp = client.post('/api/operations/integrations/sources', json={'type': 'openapi'})
        assert resp.status_code == 400
        assert resp.get_json()['error'] == 'spec is required for openapi source creation'

    def test_create_source_returns_provider_result(self, client, monkeypatch):
        class FakeProvider:
            def create_source(self, data):
                return {'id': 'src-created', 'name': data['name'], 'type': data['type']}

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: FakeProvider())
        resp = client.post(
            '/api/operations/integrations/sources',
            json={'type': 'graphql', 'name': 'Graph Source', 'endpoint': 'https://example.com/graphql'},
        )
        assert resp.status_code == 201
        assert resp.get_json()['id'] == 'src-created'

    def test_update_source_404_when_provider_returns_none(self, client, monkeypatch):
        class FakeProvider:
            def update_source(self, source_id, data):
                return None

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: FakeProvider())
        resp = client.patch('/api/operations/integrations/sources/src-missing', json={'refresh': True})
        assert resp.status_code == 404

    def test_delete_source_returns_success(self, client, monkeypatch):
        class FakeProvider:
            def delete_source(self, source_id):
                return source_id == 'src-ok'

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: FakeProvider())
        resp = client.delete('/api/operations/integrations/sources/src-ok')
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_bind_credential_requires_target_or_provider(self, client):
        resp = client.post('/api/operations/integrations/credentials', json={'slot': 'header:authorization'})
        assert resp.status_code == 400
        assert 'required' in resp.get_json()['error']

    def test_bind_credential_returns_provider_payload(self, client, monkeypatch):
        class FakeProvider:
            def bind_credential(self, data):
                return {'id': 'cred-1', 'provider': data.get('provider') or data.get('sourceType')}

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: FakeProvider())
        resp = client.post(
            '/api/operations/integrations/credentials',
            json={
                'sourceType': 'openapi',
                'targetId': 'src-openapi',
                'slot': 'header:authorization',
                'provider': 'file',
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()['id'] == 'cred-1'

    def test_unbind_credential_404_when_missing(self, client, monkeypatch):
        class FakeProvider:
            def unbind_credential(self, credential_id):
                return False

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: FakeProvider())
        resp = client.delete('/api/operations/integrations/credentials/cred-missing')
        assert resp.status_code == 404


class TestExecutorOperationsUiAssets:
    def test_operations_js_exposes_schema_summary_language(self, client):
        resp = client.get('/static/js/operations.js')
        assert resp.status_code == 200
        data = resp.data.decode('utf-8', errors='replace')
        assert 'Schema 摘要' in data
        assert '/api/operations/integrations/summary' in data
        assert 'Credential Health' in data
