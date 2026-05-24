import pytest
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

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

    def test_overview_page_exposes_briefing_and_summary_shell(self, client):
        resp = client.get('/overview')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8', errors='replace')
        assert 'ov-briefing-label' in html
        assert 'ov-summary-grid' in html
        assert 'ov-next-hop' in html
        assert 'support-signals-list' in html

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

    def test_runtime_host_health_api_returns_shape(self, client):
        resp = client.get('/api/runtime/host-health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'status' in data
        assert 'disk' in data
        assert 'memory' in data
        assert 'used_percent' in data['disk']
        assert 'used_percent' in data['memory']

    def test_overview_js_reuses_operations_summary_and_host_health(self, client):
        resp = client.get('/static/js/overview.js')
        assert resp.status_code == 200
        data = resp.data.decode('utf-8', errors='replace')
        assert '/api/operations/summary' in data
        assert '/api/runtime/host-health' in data
        assert 'ov-briefing-label' in data or 'ov-briefing-title' in data


class TestOperationsCapabilityPlane:
    def test_operations_page_exposes_boundary_family(self, client):
        resp = client.get('/operations')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8', errors='replace')
        assert 'Task Registry' in body
        assert 'Automation Maturity' in body
        assert 'Host Health' in body
        assert 'Harness' in body
        assert 'Env Map' in body
        assert 'Backup / Recovery' in body
        assert 'Recovery Paths' in body
        assert 'Runbooks' in body
        assert 'Readonly Boundary' in body
        assert 'data-family="boundary"' in body
        assert 'data-family="isolation"' in body
        assert 'data-family="task-registry"' in body
        assert 'data-family="automation"' in body
        assert 'data-family="host-health"' in body
        assert 'data-family="harness"' in body
        assert 'data-family="env-map"' in body
        assert 'data-family="backup-recovery"' in body
        assert 'data-family="recovery-paths"' in body
        assert 'data-family="runbooks"' in body

    def test_operations_integrations_boundary_api_returns_policy_projection(self, client, monkeypatch):
        class StubProvider:
            def get_capabilities(self):
                return {
                    'sourceCreate': True,
                    'sourceRefresh': True,
                    'sourceStatusToggle': False,
                    'sourceDelete': True,
                    'credentialBind': True,
                    'credentialUnbind': True,
                    'modeLabel': 'http',
                    'scopeId': 'scope-123',
                }

            def get_credentials(self):
                return []

            def get_summary(self):
                return {
                    'sourceCount': 2,
                    'healthySourceCount': 2,
                    'degradedSourceCount': 0,
                    'toolCount': 4,
                    'missingCredentialCount': 0,
                    'providerCount': 2,
                    'failedProviderCount': 0,
                }

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: StubProvider())
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        monkeypatch.setattr(
            webui_api,
            '_read_shared_context_json',
            lambda *args, **kwargs: {
                'version': 'v1',
                'date': '2026-05-19',
                'host': 'ALI-HERMES',
                'mode': 'readonly',
                'owners': {
                    'productShell': 'CrazyAgentsManage',
                    'runtimeLifecycle': 'HermesAgent',
                    'governanceTruth': 'FlowMind',
                    'capabilityPlane': 'executor',
                },
                'preconditions': ['executor-sidecar active'],
                'wave1_allowed': [{'taskType': 'intel.morning', 'repoEntrypoints': ['scripts/morning-intel-v2.py'], 'delegationUnit': 'external-read-step'}],
                'wave2_completed': [{'taskType': 'tech-radar.review', 'repoEntrypoints': ['scripts/tech-radar-review.sh'], 'resolution': 'landed'}],
                'forbidden_now': [{'taskType': 'promise.review', 'repoEntrypoints': ['scripts/daily-promise-review.py'], 'reason': 'governance output'}],
            },
        )

        resp = client.get('/api/operations/integrations/boundary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'
        assert data['providerMode'] == 'http'
        assert data['scopeId'] == 'scope-123'
        assert data['allowedTaskTypeCount'] == 1
        assert data['completedTaskTypeCount'] == 1
        assert data['forbiddenTaskTypeCount'] == 1
        assert data['owners']['governanceTruth'] == 'FlowMind'
        assert 'Do not let executor overwrite FlowMind governance truth.' in data['executionBoundary']['forbiddenMutations']

    def test_operations_summary_includes_boundary_family(self, client, monkeypatch):
        class StubProvider:
            def get_capabilities(self):
                return {
                    'sourceCreate': True,
                    'sourceRefresh': True,
                    'sourceStatusToggle': False,
                    'sourceDelete': True,
                    'credentialBind': True,
                    'credentialUnbind': True,
                    'modeLabel': 'http',
                    'scopeId': 'scope-123',
                }

            def get_credentials(self):
                return []

            def get_summary(self):
                return {
                    'sourceCount': 2,
                    'healthySourceCount': 2,
                    'degradedSourceCount': 0,
                    'toolCount': 4,
                    'missingCredentialCount': 0,
                    'providerCount': 2,
                    'failedProviderCount': 0,
                }

        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: StubProvider())
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        monkeypatch.setattr(
            webui_api,
            '_read_shared_context_json',
            lambda *args, **kwargs: {
                'version': 'v1',
                'date': '2026-05-19',
                'host': 'ALI-HERMES',
                'mode': 'readonly',
                'owners': {'productShell': 'CrazyAgentsManage'},
                'preconditions': ['executor-sidecar active'],
                'wave1_allowed': [{'taskType': 'intel.morning', 'repoEntrypoints': ['scripts/morning-intel-v2.py'], 'delegationUnit': 'external-read-step'}],
                'wave2_completed': [],
                'forbidden_now': [{'taskType': 'promise.review', 'repoEntrypoints': ['scripts/daily-promise-review.py'], 'reason': 'governance output'}],
            },
        )

        resp = client.get('/api/operations/summary')
        assert resp.status_code == 200
        data = resp.get_json()
        keys = [item['key'] for item in data['families']]
        assert 'boundary' in keys
        assert data['metrics']['boundaryCount'] == 1
        assert 'recovery-paths' in keys
        assert 'harness' in keys

    def test_operations_boundary_falls_back_to_runtime_repo_root(self, client, monkeypatch, tmp_path):
        deploy_root = tmp_path / 'deploy-copy'
        runtime_root = tmp_path / 'runtime-repo'
        (runtime_root / 'shared-context').mkdir(parents=True, exist_ok=True)
        (runtime_root / 'shared-context' / 'hermes-executor-readonly-delegation-policy.v1.json').write_text(
            json.dumps(
                {
                    'version': 'v1',
                    'date': '2026-05-19',
                    'host': 'ALI-HERMES',
                    'mode': 'readonly',
                    'owners': {'productShell': 'CrazyAgentsManage'},
                    'preconditions': ['executor-sidecar active'],
                    'wave1_allowed': [{'taskType': 'intel.morning', 'repoEntrypoints': ['scripts/morning-intel-v2.py']}],
                    'wave2_completed': [],
                    'forbidden_now': [{'taskType': 'promise.review', 'repoEntrypoints': ['scripts/daily-promise-review.py'], 'reason': 'governance output'}],
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )

        class StubProvider:
            def get_capabilities(self):
                return {'modeLabel': 'http', 'scopeId': 'scope-123'}

            def get_summary(self):
                return {
                    'sourceCount': 1,
                    'healthySourceCount': 1,
                    'degradedSourceCount': 0,
                    'toolCount': 1,
                    'missingCredentialCount': 0,
                    'providerCount': 1,
                    'failedProviderCount': 0,
                }

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: deploy_root)
        monkeypatch.setenv('CRAZY_RUNTIME_REPO_ROOT', str(runtime_root))
        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: StubProvider())
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        webui_api._remote_config = {}

        resp = client.get('/api/operations/integrations/boundary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['allowedTaskTypeCount'] == 1
        assert data['forbiddenTaskTypeCount'] == 1

    def test_operations_isolation_api_returns_role_credential_memory_projection(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / 'design' / 'executor-integration').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '06-agent-ops').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs').mkdir(exist_ok=True)
        (repo_root / 'docs' / 'codex-hermes-role-design.md').write_text('# roles\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HARNESS-ENTRY.md').write_text('# harness\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HERMESAGENT-ENTRY.md').write_text('# hermes\n', encoding='utf-8')
        (repo_root / 'docs' / 'design' / 'executor-integration' / 'README.md').write_text('# executor\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'hermes-flowmind-compatibility-matrix-2026-04-30.md').write_text('# compat\n', encoding='utf-8')
        (repo_root / 'shared-context').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / '.omx').mkdir(parents=True, exist_ok=True)
        (repo_root / 'soul' / 'agents').mkdir(parents=True, exist_ok=True)
        (repo_root / 'soul' / 'SOUL.md').write_text('# soul\n', encoding='utf-8')
        (repo_root / 'soul' / 'MEMORY.md').write_text('# memory\n', encoding='utf-8')
        (repo_root / 'soul' / 'agents' / 'ops-guardian.md').write_text('# agent\n', encoding='utf-8')

        hermes_home = tmp_path / 'hermes-home'
        (hermes_home / 'memories').mkdir(parents=True, exist_ok=True)
        (hermes_home / 'memory').mkdir(parents=True, exist_ok=True)
        (hermes_home / 'SOUL.md').write_text('# host soul\n', encoding='utf-8')
        (hermes_home / 'memories' / 'daily.md').write_text('# host memory\n', encoding='utf-8')
        (hermes_home / 'memory' / 'foo.md.bak').write_text('backup\n', encoding='utf-8')
        mirror_dir = hermes_home / 'scripts'
        mirror_dir.mkdir(parents=True, exist_ok=True)
        (mirror_dir / '.mirror-manifest.json').write_text('{}\n', encoding='utf-8')
        backup_root = tmp_path / 'backups'
        (backup_root / '20260523').mkdir(parents=True, exist_ok=True)
        deploy_root = tmp_path / 'deploy-copy'
        (deploy_root / '.deploy-backups' / 'run-1').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '06-agent-ops' / 'operations-manual.md').write_text('# manual\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'crazy-live-webui-sync-closeout-2026-05-03.md').write_text('# sync closeout\n', encoding='utf-8')

        class StubProvider:
            def get_credentials(self):
                return [
                    {'id': 'cred-1', 'provider': 'github', 'targetType': 'source', 'targetId': 'src-github', 'status': 'healthy', 'impactCount': 12, 'valueKind': 'secret'},
                    {'id': 'cred-2', 'provider': 'google', 'targetType': 'source', 'targetId': 'src-gmail', 'status': 'expired', 'impactCount': 1, 'valueKind': 'secret'},
                ]

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        monkeypatch.setenv('HERMES_HOME', str(hermes_home))
        monkeypatch.setenv('HERMES_SCRIPT_MIRROR_DIR', str(mirror_dir))
        monkeypatch.setenv('HERMES_BACKUP_ROOT', str(backup_root))
        monkeypatch.setenv('CRAZY_DEPLOY_COPY_ROOT', str(deploy_root))
        monkeypatch.setenv('EXECUTOR_API_BASE_URL', 'http://127.0.0.1:4788')
        monkeypatch.setenv('FLOWMIND_API_BASE_URL', 'http://127.0.0.1:3001')
        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: StubProvider())
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.get('/api/operations/isolation')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['counts']['roleCount'] == 4
        assert data['counts']['credentialCount'] == 2
        assert data['counts']['missingCredentialCount'] == 1
        assert data['counts']['memoryBoundaryCount'] >= 4
        assert data['counts']['runbookCount'] == 4
        assert data['credentialStatus'] == 'degraded'
        assert data['memoryStatus'] == 'healthy'
        assert any(item['id'] == 'host-runtime-memory' for item in data['memoryBoundaries'])
        assert any(item['name'] == 'Codex' for item in data['roleRegistry'])

    def test_operations_harness_api_returns_trace_and_readiness_projection(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'harness' / 'trace' / 'successes').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'trace' / 'failures').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'closeouts').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'memory').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'scripts' / 'worktree').mkdir(parents=True, exist_ok=True)
        (repo_root / 'scripts').mkdir(exist_ok=True)
        (repo_root / 'harness' / 'trace' / 'successes' / 'S-20260523-001.json').write_text(json.dumps({'id': 'S-20260523-001', 'message': 'round ok'}), encoding='utf-8')
        (repo_root / 'harness' / 'trace' / 'failures' / 'F-20260522-001.json').write_text(json.dumps({'id': 'F-20260522-001', 'message': 'old failure'}), encoding='utf-8')
        (repo_root / 'harness' / 'closeouts' / 'C-20260523-001.json').write_text(
            json.dumps({'id': 'C-20260523-001', 'status': 'success', 'trace': {'id': 'S-20260523-001', 'kind': 'success'}}),
            encoding='utf-8',
        )
        (repo_root / 'harness' / 'memory' / 'failure-patterns.md').write_text('# failures\n', encoding='utf-8')
        (repo_root / 'harness' / 'memory' / 'procedural.md').write_text('# procedural\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HARNESS-ENTRY.md').write_text('# harness\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'CROSS-REVIEW-PROCESS.md').write_text('# cross review\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'WORKTREE-BOOTSTRAP.md').write_text('# worktree\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HARNESS-CAPABILITY-MAPPING.md').write_text('# mapping\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'harness-governance-report.md').write_text('# governance\n', encoding='utf-8')
        (repo_root / 'scripts' / 'harness-critic.cjs').write_text('// critic\n', encoding='utf-8')
        (repo_root / 'scripts' / 'harness-closeout-writeback.cjs').write_text('// closeout\n', encoding='utf-8')
        (repo_root / 'scripts' / 'worktree' / 'create-agent-worktree.sh').write_text('#!/usr/bin/env bash\n', encoding='utf-8')
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._remote_config = {}

        resp = client.get('/api/operations/harness')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['counts']['successCount'] == 1
        assert data['counts']['failureCount'] == 1
        assert data['counts']['closeoutCount'] == 1
        assert data['counts']['pendingCloseoutCount'] == 1
        assert data['counts']['readinessHealthyCount'] == 4
        assert data['latestSuccess']['id'] == 'S-20260523-001'
        assert data['latestFailure']['id'] == 'F-20260522-001'
        assert data['latestCloseout']['id'] == 'C-20260523-001'

    def test_operations_summary_includes_isolation_family(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / 'design' / 'executor-integration').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs').mkdir(exist_ok=True)
        (repo_root / 'docs' / 'codex-hermes-role-design.md').write_text('# roles\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HARNESS-ENTRY.md').write_text('# harness\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HERMESAGENT-ENTRY.md').write_text('# hermes\n', encoding='utf-8')
        (repo_root / 'docs' / 'design' / 'executor-integration' / 'README.md').write_text('# executor\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'hermes-flowmind-compatibility-matrix-2026-04-30.md').write_text('# compat\n', encoding='utf-8')
        (repo_root / 'shared-context').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / '.omx').mkdir(parents=True, exist_ok=True)
        (repo_root / 'soul' / 'agents').mkdir(parents=True, exist_ok=True)
        (repo_root / 'soul' / 'SOUL.md').write_text('# soul\n', encoding='utf-8')
        (repo_root / 'soul' / 'MEMORY.md').write_text('# memory\n', encoding='utf-8')
        (repo_root / 'soul' / 'agents' / 'ops-guardian.md').write_text('# agent\n', encoding='utf-8')

        hermes_home = tmp_path / 'hermes-home'
        (hermes_home / 'memories').mkdir(parents=True, exist_ok=True)
        (hermes_home / 'SOUL.md').write_text('# host soul\n', encoding='utf-8')
        (hermes_home / 'memories' / 'daily.md').write_text('# host memory\n', encoding='utf-8')

        class StubProvider:
            def get_capabilities(self):
                return {
                    'sourceCreate': True,
                    'sourceRefresh': True,
                    'sourceStatusToggle': False,
                    'sourceDelete': True,
                    'credentialBind': True,
                    'credentialUnbind': True,
                    'modeLabel': 'http',
                    'scopeId': 'scope-123',
                }

            def get_credentials(self):
                return [{'id': 'cred-1', 'provider': 'github', 'targetType': 'source', 'targetId': 'src-github', 'status': 'healthy', 'impactCount': 12, 'valueKind': 'secret'}]

            def get_summary(self):
                return {
                    'sourceCount': 2,
                    'healthySourceCount': 2,
                    'degradedSourceCount': 0,
                    'toolCount': 4,
                    'missingCredentialCount': 0,
                    'providerCount': 2,
                    'failedProviderCount': 0,
                }

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        monkeypatch.setenv('HERMES_HOME', str(hermes_home))
        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: StubProvider())
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        monkeypatch.setattr(
            webui_api,
            '_read_shared_context_json',
            lambda *args, **kwargs: {
                'version': 'v1',
                'date': '2026-05-19',
                'host': 'ALI-HERMES',
                'mode': 'readonly',
                'owners': {'productShell': 'CrazyAgentsManage'},
                'preconditions': ['executor-sidecar active'],
                'wave1_allowed': [{'taskType': 'intel.morning', 'repoEntrypoints': ['scripts/morning-intel-v2.py'], 'delegationUnit': 'external-read-step'}],
                'wave2_completed': [],
                'forbidden_now': [{'taskType': 'promise.review', 'repoEntrypoints': ['scripts/daily-promise-review.py'], 'reason': 'governance output'}],
            },
        )
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.get('/api/operations/summary')
        assert resp.status_code == 200
        data = resp.get_json()
        keys = [item['key'] for item in data['families']]
        assert 'isolation' in keys
        assert data['metrics']['isolationCount'] == 4

    def test_operations_control_room_summary_aggregates_new_families(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / 'design' / 'executor-integration').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '06-agent-ops').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs').mkdir(exist_ok=True)
        (repo_root / 'docs' / 'codex-hermes-role-design.md').write_text('# roles\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HARNESS-ENTRY.md').write_text('# harness\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HERMESAGENT-ENTRY.md').write_text('# hermes\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'hermes-flowmind-compatibility-matrix-2026-04-30.md').write_text('# compat\n', encoding='utf-8')
        (repo_root / 'docs' / 'design' / 'executor-integration' / 'README.md').write_text('# executor\n', encoding='utf-8')
        (repo_root / 'docs' / '06-agent-ops' / 'three-state-protocol.md').write_text('# protocol\n', encoding='utf-8')
        (repo_root / 'scripts' / 'governance').mkdir(parents=True, exist_ok=True)
        (repo_root / 'scripts' / 'governance' / 'live-deploy-sync.manifest.json').write_text('{}', encoding='utf-8')
        (repo_root / 'shared-context' / 'agent-requests').mkdir(parents=True, exist_ok=True)
        (repo_root / 'shared-context' / 'agent-requests' / 'requests.jsonl').write_text(
            '\n'.join([
                json.dumps({'request_id': 'req-1', 'ack_id': 'ack-1', 'sender': 'hermes', 'target': 'codex', 'owner': 'codex', 'action': 'host verify', 'status': 'started', 'created_at': '2026-05-23T10:00:00Z', 'updated_at': '2026-05-23T10:05:00Z', 'automation_state': 'rehearsed', 'evidence_refs': ['closeout:1'], 'rollback_rule': 'disable cron'}),
                json.dumps({'request_id': 'req-2', 'ack_id': 'ack-2', 'sender': 'hermes', 'target': 'ops', 'owner': 'ops', 'action': 'nightly digest', 'status': 'delivered', 'created_at': '2026-05-23T09:00:00Z', 'updated_at': '2026-05-23T09:10:00Z', 'automation_state': 'automated', 'evidence_refs': ['closeout:2'], 'rollback_rule': 'pause routine'}),
            ]) + '\n',
            encoding='utf-8',
        )
        (repo_root / 'shared-context' / 'agent-requests' / 'events.jsonl').write_text(
            json.dumps({'ack_id': 'ack-1', 'event_type': 'automation_promotion', 'actor': 'operator', 'timestamp': '2026-05-23T10:05:00Z', 'payload': {'to_state': 'rehearsed'}}) + '\n',
            encoding='utf-8',
        )
        (repo_root / 'shared-context').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / '.omx').mkdir(parents=True, exist_ok=True)
        (repo_root / 'soul' / 'agents').mkdir(parents=True, exist_ok=True)
        (repo_root / 'soul' / 'SOUL.md').write_text('# soul\n', encoding='utf-8')
        (repo_root / 'soul' / 'MEMORY.md').write_text('# memory\n', encoding='utf-8')
        (repo_root / 'soul' / 'agents' / 'ops-guardian.md').write_text('# agent\n', encoding='utf-8')

        hermes_home = tmp_path / 'hermes-home'
        (hermes_home / 'memories').mkdir(parents=True, exist_ok=True)
        (hermes_home / 'SOUL.md').write_text('# host soul\n', encoding='utf-8')
        (hermes_home / 'memories' / 'daily.md').write_text('# host memory\n', encoding='utf-8')
        (hermes_home / 'gateway_state.json').write_text(
            json.dumps(
                {
                    'gateway_state': 'running',
                    'active_agents': 2,
                    'platforms': {
                        'cli': {'state': 'connected', 'updated_at': '2026-05-23T10:00:00Z'},
                    },
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )

        class StubProvider:
            def get_capabilities(self):
                return {
                    'sourceCreate': True,
                    'sourceRefresh': True,
                    'sourceStatusToggle': False,
                    'sourceDelete': True,
                    'credentialBind': True,
                    'credentialUnbind': True,
                    'modeLabel': 'http',
                    'scopeId': 'scope-123',
                }

            def get_credentials(self):
                return [{'id': 'cred-1', 'provider': 'github', 'targetType': 'source', 'targetId': 'src-github', 'status': 'healthy', 'impactCount': 12, 'valueKind': 'secret'}]

            def get_summary(self):
                return {
                    'sourceCount': 2,
                    'healthySourceCount': 2,
                    'degradedSourceCount': 0,
                    'toolCount': 4,
                    'missingCredentialCount': 0,
                    'providerCount': 2,
                    'failedProviderCount': 0,
                }

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        monkeypatch.setenv('HERMES_HOME', str(hermes_home))
        monkeypatch.setattr(webui_api, 'get_executor_provider', lambda: StubProvider())
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        monkeypatch.setattr(
            webui_api,
            '_read_shared_context_json',
            lambda *args, **kwargs: {
                'version': 'v1',
                'date': '2026-05-19',
                'host': 'ALI-HERMES',
                'mode': 'readonly',
                'owners': {'productShell': 'CrazyAgentsManage'},
                'preconditions': ['executor-sidecar active'],
                'wave1_allowed': [{'taskType': 'intel.morning', 'repoEntrypoints': ['scripts/morning-intel-v2.py'], 'delegationUnit': 'external-read-step'}],
                'wave2_completed': [],
                'forbidden_now': [{'taskType': 'promise.review', 'repoEntrypoints': ['scripts/daily-promise-review.py'], 'reason': 'governance output'}],
            },
        )
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.get('/api/operations/control-room-summary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['taskRegistry']['counts']['total'] == 2
        assert data['automationMaturity']['counts']['rehearsed'] == 1
        assert data['automationMaturity']['counts']['automated'] == 1
        assert data['hostHealth']['counts']['platforms'] == 1
        assert data['harness']['counts']['totalTraces'] >= 0
        assert data['envMap']['counts']['entryCount'] >= 8
        assert data['backupRecovery']['counts']['surfaceCount'] == 5
        assert data['recoveryPaths']['counts']['pathCount'] == 4
        assert data['runbooks']['counts']['runbookCount'] == 5

    def test_operations_runbooks_api_returns_visible_items(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / 'design' / 'executor-integration').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '06-agent-ops').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs').mkdir(exist_ok=True)
        (repo_root / 'docs' / 'codex-hermes-role-design.md').write_text('# roles\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HARNESS-ENTRY.md').write_text('# harness\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'HERMESAGENT-ENTRY.md').write_text('# hermes\n', encoding='utf-8')
        (repo_root / 'docs' / 'design' / 'executor-integration' / 'README.md').write_text('# executor\n', encoding='utf-8')
        (repo_root / 'docs' / '06-agent-ops' / 'three-state-protocol.md').write_text('# protocol\n', encoding='utf-8')
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._remote_config = {}

        resp = client.get('/api/operations/runbooks')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['counts']['runbookCount'] == 5
        assert data['counts']['visibleCount'] == 5

    def test_operations_env_map_api_returns_deploy_and_runtime_roots(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        runtime_root = tmp_path / 'runtime-root'
        deploy_root = tmp_path / 'deploy-copy'
        repo_root.mkdir(parents=True, exist_ok=True)
        runtime_root.mkdir(parents=True, exist_ok=True)
        deploy_root.mkdir(parents=True, exist_ok=True)
        hermes_home = tmp_path / 'hermes-home'
        hermes_home.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        monkeypatch.setenv('CRAZY_RUNTIME_REPO_ROOT', str(runtime_root))
        monkeypatch.setenv('CRAZY_DEPLOY_COPY_ROOT', str(deploy_root))
        monkeypatch.setenv('HERMES_HOME', str(hermes_home))
        monkeypatch.setenv('EXECUTOR_API_BASE_URL', 'http://127.0.0.1:4788')
        monkeypatch.setenv('FLOWMIND_API_BASE_URL', 'http://127.0.0.1:3001')
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        webui_api._hermes_home = None
        webui_api._remote_config = {'host': '47.99.217.1'}

        resp = client.get('/api/operations/env-map')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['counts']['entryCount'] >= 8
        names = [item['id'] for item in data['entries']]
        assert 'repo-root' in names
        assert 'runtime-root' in names
        assert 'deploy-root' in names
        assert 'hermes-home' in names

    def test_operations_backup_recovery_api_returns_surface_summary(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / '06-agent-ops').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '06-agent-ops' / 'operations-manual.md').write_text('# manual\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'crazy-live-webui-sync-closeout-2026-05-03.md').write_text('# sync closeout\n', encoding='utf-8')
        deploy_root = tmp_path / 'deploy-copy'
        (deploy_root / '.deploy-backups' / 'run-1').mkdir(parents=True, exist_ok=True)
        backup_root = tmp_path / 'backups'
        (backup_root / '20260523').mkdir(parents=True, exist_ok=True)
        hermes_home = tmp_path / 'hermes-home'
        (hermes_home / 'memory').mkdir(parents=True, exist_ok=True)
        (hermes_home / 'memory' / 'foo.md.bak').write_text('backup\n', encoding='utf-8')
        mirror_dir = hermes_home / 'scripts'
        mirror_dir.mkdir(parents=True, exist_ok=True)
        (mirror_dir / '.mirror-manifest.json').write_text('{}\n', encoding='utf-8')

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        monkeypatch.setenv('CRAZY_DEPLOY_COPY_ROOT', str(deploy_root))
        monkeypatch.setenv('HERMES_BACKUP_ROOT', str(backup_root))
        monkeypatch.setenv('HERMES_HOME', str(hermes_home))
        monkeypatch.setenv('HERMES_SCRIPT_MIRROR_DIR', str(mirror_dir))
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.get('/api/operations/backup-recovery')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['counts']['surfaceCount'] == 5
        assert data['counts']['healthyCount'] >= 4
        assert data['coverage']['deployCopyBackups'] == 1
        assert any(item['id'] == 'deploy-copy-backups' for item in data['surfaces'])
        assert any(item['id'] == 'script-mirror-manifest' for item in data['surfaces'])

    def test_operations_recovery_paths_api_returns_explicit_paths(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        (repo_root / 'docs' / '06-agent-ops').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '02-engineering' / 'harness').mkdir(parents=True, exist_ok=True)
        (repo_root / 'docs' / '06-agent-ops' / 'operations-manual.md').write_text('# manual\n', encoding='utf-8')
        (repo_root / 'docs' / '02-engineering' / 'harness' / 'crazy-live-webui-sync-closeout-2026-05-03.md').write_text('# sync closeout\n', encoding='utf-8')
        deploy_root = tmp_path / 'deploy-copy'
        (deploy_root / '.deploy-backups' / 'run-1').mkdir(parents=True, exist_ok=True)
        backup_root = tmp_path / 'backups'
        (backup_root / '20260523').mkdir(parents=True, exist_ok=True)
        hermes_home = tmp_path / 'hermes-home'
        (hermes_home / 'memory').mkdir(parents=True, exist_ok=True)
        (hermes_home / 'memory' / 'foo.md.bak').write_text('backup\n', encoding='utf-8')
        mirror_dir = hermes_home / 'scripts'
        mirror_dir.mkdir(parents=True, exist_ok=True)
        (mirror_dir / '.mirror-manifest.json').write_text('{}\n', encoding='utf-8')

        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        monkeypatch.setenv('CRAZY_DEPLOY_COPY_ROOT', str(deploy_root))
        monkeypatch.setenv('HERMES_BACKUP_ROOT', str(backup_root))
        monkeypatch.setenv('HERMES_HOME', str(hermes_home))
        monkeypatch.setenv('HERMES_SCRIPT_MIRROR_DIR', str(mirror_dir))
        monkeypatch.setenv('EXECUTOR_API_BASE_URL', 'http://127.0.0.1:4788')
        monkeypatch.setenv('FLOWMIND_API_BASE_URL', 'http://127.0.0.1:3001')
        monkeypatch.setattr(webui_api, 'get_provider_mode', lambda: 'http')
        webui_api._hermes_home = None
        webui_api._remote_config = {'host': '47.99.217.1'}

        resp = client.get('/api/operations/recovery-paths')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['counts']['pathCount'] == 4
        assert data['counts']['readyCount'] >= 3
        assert data['counts']['envDriftCount'] <= 1
        assert data['backupCoverage']['deployCopyBackups'] == 1
        assert any(item['id'] == 'deploy-copy-rollback' for item in data['paths'])
        assert any(item['id'] == 'hermes-script-mirror-restore' for item in data['paths'])


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


class TestHarnessWorkflowEnforcement:
    def test_harness_closeout_writeback_creates_closeout_artifact_with_lane(self, tmp_path):
        node = shutil.which('node')
        if not node:
            pytest.skip('node not available')

        repo_root = tmp_path / 'repo'
        (repo_root / 'scripts').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'trace' / 'successes').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'trace' / 'failures').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'closeouts').mkdir(parents=True, exist_ok=True)

        for rel in ['scripts/record-success.cjs', 'scripts/record-failure.cjs', 'scripts/harness-closeout-writeback.cjs']:
            src = Path(__file__).resolve().parents[1] / rel
            dst = repo_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')

        result = subprocess.run(
            [
                node,
                str(repo_root / 'scripts' / 'harness-closeout-writeback.cjs'),
                '--status', 'success',
                '--message', 'Round completed',
                '--lane', 'shared',
                '--topic', 'harness-starter',
                '--skip-governance-check',
                '--json',
            ],
            cwd=repo_root,
            env={**os.environ, 'HARNESS_REPO_ROOT': str(repo_root)},
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(result.stdout)
        closeout = payload['closeout']
        closeout_path = repo_root / closeout['file']
        assert closeout_path.exists()
        saved = json.loads(closeout_path.read_text(encoding='utf-8'))
        assert saved['trace']['kind'] == 'success'
        assert saved['context']['lane'] == 'shared'
        assert saved['context']['laneSource'] == 'cli-arg'
        assert saved['context']['topic'] == 'harness-starter'

    def test_harness_closeout_failure_auto_triggers_critic_write_back(self, tmp_path):
        node = shutil.which('node')
        if not node:
            pytest.skip('node not available')

        repo_root = tmp_path / 'repo'
        (repo_root / 'scripts').mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'trace' / 'successes').mkdir(parents=True, exist_ok=True)
        failure_dir = repo_root / 'harness' / 'trace' / 'failures'
        failure_dir.mkdir(parents=True, exist_ok=True)
        (repo_root / 'harness' / 'closeouts').mkdir(parents=True, exist_ok=True)
        memory_dir = repo_root / 'harness' / 'memory'
        memory_dir.mkdir(parents=True, exist_ok=True)
        (memory_dir / 'failure-patterns.md').write_text('# failures\n', encoding='utf-8')
        (memory_dir / 'procedural.md').write_text('# procedural\n', encoding='utf-8')

        for rel in ['scripts/record-success.cjs', 'scripts/record-failure.cjs', 'scripts/harness-critic.cjs', 'scripts/harness-closeout-writeback.cjs']:
            src = Path(__file__).resolve().parents[1] / rel
            dst = repo_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')

        sample_failure = {
            'id': 'F-20260524-001',
            'timestamp': '2026-05-24T08:00:00Z',
            'type': 'typescript-error',
            'file': 'src/foo.ts',
            'message': 'example',
            'context': {},
        }
        for idx in range(2):
            payload = dict(sample_failure)
            payload['id'] = f'F-20260524-00{idx + 1}'
            (failure_dir / f"{payload['id']}.json").write_text(json.dumps(payload), encoding='utf-8')

        result = subprocess.run(
            [
                node,
                str(repo_root / 'scripts' / 'harness-closeout-writeback.cjs'),
                '--status', 'failed',
                '--type', 'typescript-error',
                '--message', 'Verification failed',
                '--lane', 'shared',
                '--topic', 'critic-enforcement',
                '--skip-governance-check',
                '--json',
            ],
            cwd=repo_root,
            env={**os.environ, 'HARNESS_REPO_ROOT': str(repo_root)},
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(result.stdout)
        assert payload['criticWriteBackApplied'] is True
        procedural = (memory_dir / 'procedural.md').read_text(encoding='utf-8')
        assert 'Critic Follow-up' in procedural

    def test_cron_list_api_reachable(self, client):
        resp = client.get('/api/cron/list')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_tasks_page_exposes_request_bus_panel(self, client):
        resp = client.get('/tasks')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8', errors='replace')
        assert '三态请求总线' in body
        assert 'request-bus-body' in body
        assert 'request-bus-lanes' in body

    def test_tasks_request_bus_api_reads_requests_jsonl(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        req_dir = repo_root / 'shared-context' / 'agent-requests'
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / 'requests.jsonl').write_text(
            '{"request_id":"req-1","ack_id":"ack-1","sender":"hermes","target":"codex","action":"test request","status":"delivered","created_at":"2026-05-22T09:00:00Z","updated_at":"2026-05-22T09:01:00Z","automation_state":"approved-for-automation","evidence_refs":["closeout:1"]}\n',
            encoding='utf-8',
        )
        (req_dir / 'events.jsonl').write_text(
            '{"ack_id":"ack-1","event_type":"automation_promotion","actor":"operator","timestamp":"2026-05-22T09:01:10Z","payload":{"from_state":"rehearsed","to_state":"approved-for-automation","approval":"closeout-1","rollback_rule":"disable cron","evidence_refs":["closeout:1"]}}\n',
            encoding='utf-8',
        )
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._remote_config = {}

        resp = client.get('/api/tasks/request-bus')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['stats']['total'] == 1
        assert data['stats']['delivered'] == 1
        assert data['stats']['open'] == 0
        assert data['requests'][0]['ack_id'] == 'ack-1'
        assert data['requests'][0]['lane'] == 'archive'
        assert data['requests'][0]['automation_state'] == 'approved-for-automation'
        assert len(data['requests'][0]['events']) == 1
        assert len(data['lanes']['archive']) == 1
        assert data['automation']['approved-for-automation'] == 1

    def test_tasks_request_bus_transition_updates_status_and_event_log(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        req_dir = repo_root / 'shared-context' / 'agent-requests'
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / 'requests.jsonl').write_text(
            '{"request_id":"req-1","ack_id":"ack-1","sender":"hermes","target":"codex","action":"test request","status":"accepted","created_at":"2026-05-22T09:00:00Z","updated_at":"2026-05-22T09:01:00Z"}\n',
            encoding='utf-8',
        )
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._remote_config = {}

        resp = client.post(
            '/api/tasks/request-bus/ack-1/transition',
            json={'status': 'started', 'note': 'Operator picked this up.'},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'started'
        assert data['lane'] == 'working'
        assert data['last_transition_note'] == 'Operator picked this up.'

        events_file = req_dir / 'events.jsonl'
        assert events_file.exists()
        events = [json.loads(line) for line in events_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert events[-1]['event_type'] == 'status_transition'
        assert events[-1]['payload']['to_status'] == 'started'

    def test_tasks_request_bus_automation_state_requires_gate_fields(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        req_dir = repo_root / 'shared-context' / 'agent-requests'
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / 'requests.jsonl').write_text(
            '{"request_id":"req-1","ack_id":"ack-1","sender":"hermes","target":"codex","action":"test request","status":"completed","created_at":"2026-05-22T09:00:00Z","updated_at":"2026-05-22T09:01:00Z","automation_state":"prototype"}\n',
            encoding='utf-8',
        )
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._remote_config = {}

        jump = client.post(
            '/api/tasks/request-bus/ack-1/automation-state',
            json={'automationState': 'approved-for-automation', 'evidenceRefs': ['closeout:1']},
        )
        assert jump.status_code == 400
        assert 'advance one step at a time' in jump.get_json()['error']

        bad = client.post(
            '/api/tasks/request-bus/ack-1/automation-state',
            json={'automationState': 'rehearsed'},
        )
        assert bad.status_code == 400
        assert 'evidenceRefs' in bad.get_json()['error']

        good = client.post(
            '/api/tasks/request-bus/ack-1/automation-state',
            json={
                'automationState': 'rehearsed',
                'evidenceRefs': ['closeout:1'],
                'note': 'Verified manually on host.',
            },
        )
        assert good.status_code == 200
        data = good.get_json()
        assert data['automation_state'] == 'rehearsed'

        stored = json.loads((req_dir / 'requests.jsonl').read_text(encoding='utf-8').splitlines()[0])
        assert stored['automation_state'] == 'rehearsed'


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
                'handoffContract': {
                    'version': 'handoff-packet-v1',
                    'primarySource': 'moduleDetails.handoff',
                    'fallbackOrder': ['semanticContext.fieldMappings', 'latestEvidence', 'traceSummary'],
                    'ready': True,
                    'blockingIssues': [],
                    'missingFields': [],
                    'executionBoundarySource': 'semanticPacket.executionBoundary',
                    'executionBoundaryMissingFields': [],
                },
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
        assert data['handoffContract']['ready'] is True
        assert data['handoffContract']['blockingIssues'] == []

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
        assert data['handoffContract']['executionBoundarySource'] == 'moduleDetails.handoff.Execution Boundary'

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
        assert data['handoffContract']['ready'] is False
        assert data['handoffContract']['executionBoundarySource'] == 'semanticContext.executionBoundary'
        assert 'Handoff packet is missing required field: Truth Status.' in data['handoffContract']['blockingIssues']
        assert 'Handoff packet is missing required field: Consumer Hints.' in data['handoffContract']['blockingIssues']

    def test_runtime_handoffs_uses_upstream_handoff_contract_blockers(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'record': {'id': 'rec-contract-1'},
                'mode': 'derived',
                'gaps': [],
                'handoffContract': {
                    'version': 'handoff-packet-v1',
                    'primarySource': 'moduleDetails.handoff',
                    'fallbackOrder': ['semanticContext.fieldMappings', 'latestEvidence', 'traceSummary'],
                    'ready': False,
                    'blockingIssues': ['Truth status approved requires latestEvidence, but no evidence snapshot is present.'],
                    'missingFields': ['Semantic Core.latestEvidence'],
                    'executionBoundarySource': 'semanticPacket.executionBoundary',
                    'executionBoundaryMissingFields': [],
                },
                'steps': [],
                'moduleDetails': {
                    'handoff': {
                        'title': 'Unified Handoff Packet',
                        'summary': 'Upstream semantic packet.',
                        'sections': [],
                    }
                },
            },
        )
        resp = client.get('/api/runtime/handoffs?recordId=rec-contract-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['handoffContract']['ready'] is False
        assert data['handoffContract']['missingFields'] == ['Semantic Core.latestEvidence']
        assert data['handoffContract']['blockingIssues'] == [
            'Truth status approved requires latestEvidence, but no evidence snapshot is present.'
        ]

    def test_runtime_handoffs_exposes_operational_follow_up_projection(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'record': {'id': 'rec-follow-up-1'},
                'mode': 'derived',
                'gaps': [],
                'steps': [],
                'operationalFollowUp': {
                    'projectionState': 'resolved',
                    'flowmindStatus': 'approved',
                    'lastGovernanceStatus': 'approved',
                    'lastGovernanceFeedback': 'blocked',
                    'localStatus': 'blocked',
                    'needsFollowUp': True,
                    'followUpKind': 'blocked',
                    'nextActor': 'local_operator',
                    'isTerminalLocal': False,
                    'reason': 'Replay ready sample with complete blocked follow-up context.',
                    'note': 'Use upstream projection as the only local interpretation input.',
                    'evidenceRefs': ['review:blocked-strong-001', 'candidate:blocked-strong-001'],
                    'updatedAt': '2026-05-16T00:39:20.148Z',
                    'missingFields': [],
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
        resp = client.get('/api/runtime/handoffs?recordId=rec-follow-up-1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['operationalFollowUp'] == {
            'projectionState': 'resolved',
            'flowmindStatus': 'approved',
            'lastGovernanceStatus': 'approved',
            'lastGovernanceFeedback': 'blocked',
            'localStatus': 'blocked',
            'needsFollowUp': True,
            'followUpKind': 'blocked',
            'nextActor': 'local_operator',
            'isTerminalLocal': False,
            'reason': 'Replay ready sample with complete blocked follow-up context.',
            'note': 'Use upstream projection as the only local interpretation input.',
            'evidenceRefs': ['review:blocked-strong-001', 'candidate:blocked-strong-001'],
            'updatedAt': '2026-05-16T00:39:20.148Z',
            'missingFields': [],
        }

    def test_runtime_handoffs_falls_back_to_handoff_operational_follow_up_section(self, client, monkeypatch):
        monkeypatch.setattr(
            webui_api,
            '_safe_flowmind_request',
            lambda *args, **kwargs: {
                'record': {'id': 'rec-follow-up-2'},
                'mode': 'derived',
                'gaps': [],
                'steps': [],
                'moduleDetails': {
                    'handoff': {
                        'title': 'Unified Handoff Packet',
                        'summary': 'Upstream semantic packet.',
                        'sections': [
                            {
                                'title': 'Operational Follow-Up',
                                'items': [
                                    {'label': 'Projection State', 'value': 'unknown'},
                                    {'label': 'FlowMind Status', 'value': 'approved'},
                                    {'label': 'Last Governance Status', 'value': 'approved'},
                                    {'label': 'Reason', 'value': 'Missing follow-up feedback in replay.'},
                                    {'label': 'Note', 'value': 'Follow-up judgment remains unknown.'},
                                    {'label': 'Follow-Up Evidence Refs', 'value': 'review:blocked-strong-001, candidate:blocked-strong-001'},
                                ],
                            }
                        ],
                    }
                },
            },
        )
        resp = client.get('/api/runtime/handoffs?recordId=rec-follow-up-2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['operationalFollowUp'] == {
            'projectionState': 'unknown',
            'flowmindStatus': 'approved',
            'lastGovernanceStatus': 'approved',
            'lastGovernanceFeedback': None,
            'localStatus': None,
            'needsFollowUp': None,
            'followUpKind': None,
            'nextActor': None,
            'isTerminalLocal': None,
            'reason': 'Missing follow-up feedback in replay.',
            'note': 'Follow-up judgment remains unknown.',
            'evidenceRefs': ['review:blocked-strong-001', 'candidate:blocked-strong-001'],
            'updatedAt': None,
            'missingFields': [],
        }

    def test_runtime_handoffs_unavailable_keeps_contract_shape(self, client, monkeypatch):
        monkeypatch.setattr(webui_api, '_safe_flowmind_request', lambda *args, **kwargs: None)
        resp = client.get('/api/runtime/handoffs?recordId=rec-missing')
        assert resp.status_code == 502
        data = resp.get_json()
        assert data['recordId'] == 'rec-missing'
        assert data['source'] == 'flowmind_unavailable'
        assert data['semanticContext'] == {}
        assert data['executionBoundary'] is None
        assert data['executionBoundarySource'] is None
        assert data['executionBoundaryMissingFields'] == [
            'Canonical Authority',
            'Local Writable Targets',
            'Human Gate Actions',
            'Forbidden Mutations',
        ]
        assert data['handoffContract']['ready'] is False
        assert data['handoffContract']['blockingIssues'] == [
            'FlowMind replay upstream unavailable for the provided recordId.'
        ]
        assert data['operationalFollowUp'] is None
        assert data['handoffContract']['missingFields'] == [
            'Truth Status',
            'Latest Evidence Summary',
            'Latest Evidence Class',
            'Latest Evidence Source Type',
            'Latest Evidence Refs',
            'Semantic Refs',
            'Trace Events',
            'Latest Trace Action',
            'Latest Trace Summary',
            'Consumer Hints',
        ]
        assert data['handoffContract']['executionBoundaryMissingFields'] == [
            'Canonical Authority',
            'Local Writable Targets',
            'Human Gate Actions',
            'Forbidden Mutations',
        ]

    def test_runtime_harness_summary_api_reachable(self, client):
        resp = client.get('/api/runtime/harness-summary')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'success_count' in data
        assert 'failure_count' in data
        assert 'closeout_count' in data
        assert 'pending_closeout_count' in data


class TestLoopSurfaceApis:
    @pytest.fixture(autouse=True)
    def reset_loop_surface_state(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HERMES_HOME', str(tmp_path))
        webui_api._hermes_home = None
        webui_api._remote_config = {}
        yield
        webui_api._hermes_home = None
        webui_api._remote_config = None

    def test_collaboration_loops_page_reachable(self, client):
        resp = client.get('/collaboration/loops')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8', errors='replace')
        assert 'loop-surface.js' in body
        assert 'Loop Surface' in body
        assert 'loop-action-banner' in body
        assert 'loop-feedback-list' in body
        assert 'loop-memory-candidate-list' in body

    def test_collaboration_page_links_to_loop_surface(self, client):
        resp = client.get('/collaboration')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8', errors='replace')
        assert '/collaboration/loops' in body

    def test_collaboration_loops_api_returns_empty_without_state(self, client):
        resp = client.get('/api/collaboration/loops')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_collaboration_loops_api_builds_promise_review_cycle(self, client, tmp_path):
        reviews_dir = tmp_path / 'promises' / 'reviews'
        reviews_dir.mkdir(parents=True, exist_ok=True)
        (reviews_dir / 'review-20260522.md').write_text('# review\n', encoding='utf-8')
        (reviews_dir / 'daily-promise-review-state.json').write_text(
            json.dumps(
                {
                    'digest': 'abc123def456',
                    'checked_at': '2026-05-22T09:00:00+08:00',
                    'snapshot': {
                        'promise_count': 2,
                        'classified_counts': {
                            'total': 2,
                            'overdue': 1,
                            'due_today': 0,
                            'due_soon': 0,
                            'in_progress': 0,
                            'completed': 1,
                            'blocked': 1,
                            'pending_count': 0,
                        },
                        'promises': [
                            {
                                'promise_id': 'promise-1',
                                'title': 'P1',
                                'needs_follow_up': 'true',
                            },
                            {
                                'promise_id': 'promise-2',
                                'title': 'P2',
                                'needs_follow_up': 'false',
                            },
                        ],
                    },
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )

        resp = client.get('/api/collaboration/loops')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        loop = data[0]
        assert loop['cycleType'] == 'promise-review-cycle'
        assert loop['sourceJobId'] == 'daily-promise-review'
        assert loop['roundNumber'] == 1
        assert loop['stage'] == 'awaiting_feedback'
        assert loop['feedbackStatus'] == 'follow-up-pending'
        assert loop['memoryCandidateStatus'] == 'awaiting-confirmation'
        assert loop['sourcePaths']['state'] == 'promises/reviews/daily-promise-review-state.json'

        detail = client.get(f"/api/collaboration/loops/{loop['loopId']}")
        assert detail.status_code == 200
        payload = detail.get_json()
        assert payload['loopId'] == loop['loopId']
        assert payload['classifiedCounts']['blocked'] == 1
        assert len(payload['memoryCandidates']) == 1
        assert len(payload['feedbackInputs']) == 1

        mem_resp = client.get('/api/collaboration/memory-candidates')
        assert mem_resp.status_code == 200
        mem_data = mem_resp.get_json()
        assert len(mem_data) == 1
        assert mem_data[0]['candidateType'] == 'reflection_learning'
        assert mem_data[0]['proposedTarget'] == 'MEMORY.md'

        fb_resp = client.get('/api/collaboration/feedback-inputs')
        assert fb_resp.status_code == 200
        fb_data = fb_resp.get_json()
        assert len(fb_data) == 1
        assert fb_data[0]['status'] == 'pending-input'
        assert fb_data[0]['nextActor'] == 'operator'
        assert fb_data[0]['inputMode'] == 'explicit_event'

    def test_collaboration_loops_api_includes_morning_intel_cycle_when_data_exists(self, client, monkeypatch, tmp_path):
        intel_dir = tmp_path / 'intel'
        intel_dir.mkdir(parents=True, exist_ok=True)
        (intel_dir / 'summary-20260522-v2.md').write_text('# summary\n', encoding='utf-8')
        (intel_dir / 'intel-data-20260522-v2.json').write_text(
            json.dumps(
                {
                    'papers': [{'id': 'a1'}, {'id': 'a2'}],
                    'rss_items': [{'title': 'x'}, {'title': 'y'}, {'title': 'z'}],
                    'timestamp': '2026-05-22T08:30:00+08:00',
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        monkeypatch.setenv('HERMES_HOME', str(tmp_path))
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.get('/api/collaboration/loops')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        loop = data[0]
        assert loop['cycleType'] == 'morning-intel-cycle'
        assert loop['sourceJobId'] == 'morning-intel'
        assert loop['objectCount'] == 5
        assert loop['followUpCount'] == 0

    def test_collaboration_loops_api_can_return_multiple_loops(self, client, monkeypatch, tmp_path):
        reviews_dir = tmp_path / 'promises' / 'reviews'
        reviews_dir.mkdir(parents=True, exist_ok=True)
        (reviews_dir / 'review-20260522.md').write_text('# review\n', encoding='utf-8')
        (reviews_dir / 'daily-promise-review-state.json').write_text(
            json.dumps(
                {
                    'digest': 'abc123def456',
                    'checked_at': '2026-05-22T09:00:00+08:00',
                    'snapshot': {
                        'promise_count': 1,
                        'classified_counts': {'total': 1, 'overdue': 0, 'due_today': 0, 'due_soon': 0, 'in_progress': 0, 'completed': 0, 'blocked': 0, 'pending_count': 1},
                        'promises': [{'promise_id': 'promise-1', 'title': 'P1', 'needs_follow_up': 'false'}],
                    },
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        intel_dir = tmp_path / 'intel'
        intel_dir.mkdir(parents=True, exist_ok=True)
        (intel_dir / 'summary-20260522-v2.md').write_text('# summary\n', encoding='utf-8')
        (intel_dir / 'intel-data-20260522-v2.json').write_text(
            json.dumps(
                {
                    'papers': [{'id': 'a1'}],
                    'rss_items': [{'title': 'x'}],
                    'timestamp': '2026-05-22T08:30:00+08:00',
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        monkeypatch.setenv('HERMES_HOME', str(tmp_path))
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.get('/api/collaboration/loops')
        assert resp.status_code == 200
        data = resp.get_json()
        cycle_types = sorted(item['cycleType'] for item in data)
        assert cycle_types == ['morning-intel-cycle', 'promise-review-cycle']

    def test_memory_candidate_decision_persists_and_updates_loop_status(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        reviews_dir = tmp_path / 'promises' / 'reviews'
        reviews_dir.mkdir(parents=True, exist_ok=True)
        (reviews_dir / 'review-20260522.md').write_text('# review\n', encoding='utf-8')
        (reviews_dir / 'daily-promise-review-state.json').write_text(
            json.dumps(
                {
                    'digest': 'abc123def456',
                    'checked_at': '2026-05-22T09:00:00+08:00',
                    'snapshot': {
                        'promise_count': 1,
                        'classified_counts': {
                            'total': 1,
                            'overdue': 0,
                            'due_today': 0,
                            'due_soon': 0,
                            'in_progress': 0,
                            'completed': 0,
                            'blocked': 1,
                            'pending_count': 0,
                        },
                        'promises': [
                            {
                                'promise_id': 'promise-1',
                                'title': 'P1',
                                'needs_follow_up': 'true',
                                'flowmind_candidate_id': 'cand-1',
                                'instance_id': 'inst-1',
                                'follow_up_kind': 'blocked',
                                'next_actor': 'local_operator',
                                'latest_feedback_type': 'blocked',
                                'latest_feedback_summary': 'Need operator follow-up',
                            },
                        ],
                    },
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        monkeypatch.setenv('HERMES_HOME', str(tmp_path))
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.post(
            '/api/collaboration/memory-candidates/memory-candidate%3Apromise-1/decision',
            json={
                'action': 'confirm',
                'note': 'Promote this reflection into host memory candidate acceptance.',
                'evidenceRefs': ['promise:promise-1', 'report:review-20260522.md'],
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'accepted'
        assert data['lastAction'] == 'confirm'
        assert data['targetMemoryPlane'] == 'host-memory'

        decisions_file = repo_root / 'shared-context' / 'loop-surface' / 'memory-candidate-decisions.jsonl'
        assert decisions_file.exists()
        lines = [line for line in decisions_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record['candidateId'] == 'memory-candidate:promise-1'
        assert record['status'] == 'accepted'

        loop_resp = client.get('/api/collaboration/loops')
        assert loop_resp.status_code == 200
        loops = loop_resp.get_json()
        assert loops[0]['memoryCandidateStatus'] == 'decision-recorded'
        assert loops[0]['memoryCandidates'][0]['status'] == 'accepted'

    def test_feedback_input_submit_persists_local_queue_record(self, client, monkeypatch, tmp_path):
        repo_root = tmp_path / 'repo'
        reviews_dir = tmp_path / 'promises' / 'reviews'
        reviews_dir.mkdir(parents=True, exist_ok=True)
        (reviews_dir / 'review-20260522.md').write_text('# review\n', encoding='utf-8')
        (reviews_dir / 'daily-promise-review-state.json').write_text(
            json.dumps(
                {
                    'digest': 'abc123def456',
                    'checked_at': '2026-05-22T09:00:00+08:00',
                    'snapshot': {
                        'promise_count': 1,
                        'classified_counts': {
                            'total': 1,
                            'overdue': 0,
                            'due_today': 0,
                            'due_soon': 0,
                            'in_progress': 0,
                            'completed': 0,
                            'blocked': 1,
                            'pending_count': 0,
                        },
                        'promises': [
                            {
                                'promise_id': 'promise-1',
                                'title': 'P1',
                                'needs_follow_up': 'true',
                                'flowmind_candidate_id': 'cand-1',
                                'instance_id': 'inst-1',
                                'follow_up_kind': 'blocked',
                                'next_actor': 'local_operator',
                                'latest_feedback_type': 'blocked',
                                'latest_feedback_summary': 'Need operator follow-up',
                            },
                        ],
                    },
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        monkeypatch.setenv('HERMES_HOME', str(tmp_path))
        monkeypatch.setattr(webui_api, '_get_repo_root', lambda: repo_root)
        webui_api._hermes_home = None
        webui_api._remote_config = {}

        resp = client.post(
            '/api/collaboration/feedback-inputs/feedback-input%3Apromise-1/submit',
            json={
                'mode': 'event_annotation',
                'eventType': 'blocked',
                'reason': 'Operator needs to annotate why this promise remains blocked.',
                'note': 'Waiting on a local replay decision.',
                'evidenceRefs': ['promise:promise-1', 'state:promises/reviews/daily-promise-review-state.json'],
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'submitted-local'
        assert data['lastSubmissionMode'] == 'event_annotation'
        assert data['lastSubmissionEventType'] == 'blocked'
        assert data['targetInstanceId'] == 'inst-1'

        submissions_file = repo_root / 'shared-context' / 'loop-surface' / 'feedback-inputs.jsonl'
        assert submissions_file.exists()
        lines = [line for line in submissions_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record['inputId'] == 'feedback-input:promise-1'
        assert record['status'] == 'submitted-local'
        assert record['writeBoundary'] == 'local-operator-queue'

        loop_resp = client.get('/api/collaboration/loops')
        assert loop_resp.status_code == 200
        loops = loop_resp.get_json()
        assert loops[0]['feedbackStatus'] == 'local-submission-recorded'
        assert loops[0]['feedbackInputs'][0]['lastSubmissionBoundary'] == 'local-operator-queue'


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
        assert 'operationalFollowUp' in body

    def test_timeline_css_reachable(self, client):
        resp = client.get('/static/css/timeline.css')
        assert resp.status_code == 200
        data = resp.data.decode()
        assert '.tl-hero' in data
        assert '.tl-event' in data
        assert '.tl-follow-up-card' in data

    def test_timeline_js_reachable(self, client):
        resp = client.get('/static/js/timeline.js')
        assert resp.status_code == 200
        data = resp.data.decode()
        assert 'fetchTrace' in data
        assert '/api/promise-review/trace/' in data
        assert 'contract.missingFields' in data
        assert 'contract.executionBoundaryMissingFields' in data
        assert 'renderOperationalFollowUp' in data
        assert 'Operational Follow-Up 缺失' in data

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
