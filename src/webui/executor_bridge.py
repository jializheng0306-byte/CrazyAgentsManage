"""
CrazyAgentsManage → executor capability bridge.

Provides a unified interface for consuming executor source/tool/credential/provider data.
Uses a Provider pattern so the backend can seamlessly switch between:
  - SampleExecutorProvider: built-in sample data (default, no external dependency)
  - HttpExecutorProvider: real executor HTTP API (when executor is running)

Auto-detects executor availability on first access.
"""

import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from urllib import request as urlrequest
from urllib import error as urlerror


class ExecutorBridgeUnsupported(Exception):
    pass


_EXECUTOR_ENV_VARS = ("EXECUTOR_BIN", "CRAZY_EXECUTOR_BIN")


# ============================================================
# Data models (matching the API façade spec)
# ============================================================

def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _is_executable(candidate):
    path = Path(candidate).expanduser()
    return path.is_file() and os.access(path, os.X_OK)


def _resolve_npm_global_executor():
    npm_bin = shutil.which("npm")
    if not npm_bin:
        return None

    result = subprocess.run(
        [npm_bin, "prefix", "-g"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    prefix = (result.stdout or "").strip()
    if not prefix:
        return None

    candidate = str(Path(prefix).expanduser() / "bin" / "executor")
    return candidate if _is_executable(candidate) else None


def resolve_executor_binary():
    """Resolve executor CLI in service/cron environments where PATH is sparse."""
    candidates = []

    for env_var in _EXECUTOR_ENV_VARS:
        value = os.environ.get(env_var, "").strip()
        if value:
            candidates.append(value)

    path = shutil.which("executor")
    if path:
        candidates.append(path)

    npm_candidate = _resolve_npm_global_executor()
    if npm_candidate:
        candidates.append(npm_candidate)

    candidates.extend(
        [
            "/usr/local/bin/executor",
            "/usr/bin/executor",
            "/opt/homebrew/bin/executor",
        ]
    )

    home_nvm = Path.home() / ".nvm" / "versions" / "node"
    if home_nvm.exists():
        candidates.extend(str(path) for path in sorted(home_nvm.glob("*/bin/executor")))

    seen = set()
    for candidate in candidates:
        normalized = str(Path(candidate).expanduser())
        if normalized in seen:
            continue
        seen.add(normalized)
        if _is_executable(normalized):
            return normalized

    raise FileNotFoundError(
        "executor CLI not found. Set EXECUTOR_BIN or install executor so the binary is available on PATH."
    )


def _executor_cli_capability():
    try:
        executor_bin = resolve_executor_binary()
        return {
            'executorCliAvailable': True,
            'executorBinary': executor_bin,
            'executorCliError': None,
        }
    except FileNotFoundError as exc:
        return {
            'executorCliAvailable': False,
            'executorBinary': '',
            'executorCliError': str(exc),
        }


def _schema_summary_from_schema(schema):
    if not isinstance(schema, dict):
        return ''

    schema_type = schema.get('type')
    properties = schema.get('properties')
    if schema_type == 'object' and isinstance(properties, dict):
        names = list(properties.keys())
        preview = ', '.join(names[:4])
        if len(names) > 4:
            preview += '…'
        return f"object · {len(names)} fields" + (f" ({preview})" if preview else '')

    if schema_type == 'array':
        items = schema.get('items')
        item_type = items.get('type') if isinstance(items, dict) else 'unknown'
        return f'array · items:{item_type}'

    if schema_type:
        return str(schema_type)

    return ''


def _tool_schema_summary(tool):
    if not isinstance(tool, dict):
        return ''
    existing = tool.get('schemaSummary') or tool.get('schema_summary')
    if isinstance(existing, str) and existing.strip():
        return existing.strip()
    for key in ('inputSchema', 'schema', 'parameters', 'jsonSchema'):
        summary = _schema_summary_from_schema(tool.get(key))
        if summary:
            return summary
    return ''


def _tool_status(tool):
    if not isinstance(tool, dict):
        return 'unknown'
    raw_status = tool.get('status')
    if raw_status in ('available', 'auth-required', 'disabled', 'invalid-schema', 'unknown'):
        return raw_status
    if tool.get('schemaValid') is False or tool.get('schemaError'):
        return 'invalid-schema'
    if tool.get('authMissing') or tool.get('requiresAuth') and tool.get('credentialStatus') in ('missing', 'expired', 'invalid'):
        return 'auth-required'
    if tool.get('disabled') is True:
        return 'disabled'
    return 'available'


def _provider_rollup_status(sources):
    if not sources:
        return 'unknown'
    failed = sum(1 for item in sources if item.get('status') == 'failed')
    degraded = sum(1 for item in sources if item.get('status') in ('degraded', 'missing-auth', 'disabled', 'unknown'))
    healthy = sum(1 for item in sources if item.get('status') == 'healthy')
    if failed == len(sources):
        return 'failed'
    if failed > 0 and healthy == 0 and degraded == 0:
        return 'failed'
    if failed > 0 or degraded > 0:
        return 'degraded'
    return 'reachable'


def _provider_issue_summary(status, sources):
    if status == 'failed':
        return '所有 source 当前都处于失败态'
    if status == 'degraded':
        failing = [item.get('name') or item.get('id') for item in sources if item.get('status') in ('failed', 'degraded', 'missing-auth', 'disabled', 'unknown')]
        if failing:
            return '异常 source: ' + ' / '.join(failing[:3]) + ('…' if len(failing) > 3 else '')
        return '部分 source 状态异常'
    return None


# ============================================================
# Abstract provider
# ============================================================

class ExecutorProvider(ABC):

    @abstractmethod
    def get_sources(self):
        """-> list[IntegrationSourceView]"""
        ...

    @abstractmethod
    def get_tools(self, source_id=''):
        """-> list[ExternalToolView]"""
        ...

    @abstractmethod
    def get_credentials(self):
        """-> list[CredentialHealthView]"""
        ...

    @abstractmethod
    def get_providers(self):
        """-> list[ProviderHealthView]"""
        ...

    @abstractmethod
    def get_summary(self):
        """-> IntegrationClusterSummary"""
        ...

    # ---- Write operations (Phase 2) ----

    @abstractmethod
    def create_source(self, data):
        """Create a new source. Returns the created source dict."""
        ...

    @abstractmethod
    def update_source(self, source_id, data):
        """Update source fields (status, name, etc). Returns updated source or None."""
        ...

    @abstractmethod
    def delete_source(self, source_id):
        """Delete a source. Returns True if deleted."""
        ...

    @abstractmethod
    def bind_credential(self, data):
        """Bind a credential to a source. Returns the created credential dict."""
        ...

    @abstractmethod
    def unbind_credential(self, credential_id):
        """Remove a credential binding. Returns True if removed."""
        ...

    @abstractmethod
    def get_capabilities(self):
        """Return bridge capability flags for the current provider."""
        ...


# ============================================================
# Sample provider (built-in demo data)
# ============================================================

_SAMPLE_SOURCES = [
    {'id': 'src-github-rest',   'name': 'GitHub REST API',     'type': 'openapi',   'scope': 'org',  'status': 'healthy',      'toolCount': 12, 'provider': 'openapi'},
    {'id': 'src-notion',        'name': 'Notion API',          'type': 'openapi',   'scope': 'user', 'status': 'healthy',      'toolCount': 8,  'provider': 'openapi'},
    {'id': 'src-slack',         'name': 'Slack Web API',       'type': 'openapi',   'scope': 'team', 'status': 'degraded',     'toolCount': 15, 'provider': 'openapi'},
    {'id': 'src-shopify',       'name': 'Shopify Storefront',  'type': 'graphql',   'scope': 'org',  'status': 'healthy',      'toolCount': 6,  'provider': 'graphql'},
    {'id': 'src-gh-graphql',    'name': 'GitHub GraphQL',      'type': 'graphql',   'scope': 'org',  'status': 'missing-auth', 'toolCount': 5,  'provider': 'graphql'},
    {'id': 'src-fs-mcp',        'name': 'Filesystem MCP',      'type': 'mcp',       'scope': 'local','status': 'healthy',      'toolCount': 4,  'provider': 'mcp'},
    {'id': 'src-pw-mcp',        'name': 'Playwright MCP',      'type': 'mcp',       'scope': 'local','status': 'disabled',     'toolCount': 3,  'provider': 'mcp'},
    {'id': 'src-gmail',         'name': 'Gmail API',           'type': 'discovery', 'scope': 'user', 'status': 'failed',       'toolCount': 0,  'provider': 'discovery'},
]

_SAMPLE_TOOLS_BY_SOURCE = {
    'src-github-rest': [
        {'id': 'gh-list-repos',     'name': 'List Repositories',      'requiresAuth': True,  'status': 'available',    'summary': '列出组织或用户的代码仓库'},
        {'id': 'gh-get-repo',       'name': 'Get Repository',         'requiresAuth': False, 'status': 'available',    'summary': '获取单个仓库详情'},
        {'id': 'gh-create-issue',   'name': 'Create Issue',           'requiresAuth': True,  'status': 'available',    'summary': '在仓库中创建 Issue'},
        {'id': 'gh-search-code',    'name': 'Search Code',            'requiresAuth': False, 'status': 'available',    'summary': '全局搜索代码片段'},
        {'id': 'gh-list-prs',       'name': 'List Pull Requests',     'requiresAuth': False, 'status': 'available',    'summary': '列出仓库的 Pull Request'},
        {'id': 'gh-merge-pr',       'name': 'Merge Pull Request',     'requiresAuth': True,  'status': 'available',    'summary': '合并 Pull Request'},
        {'id': 'gh-create-branch',  'name': 'Create Branch',          'requiresAuth': True,  'status': 'available',    'summary': '创建新分支'},
        {'id': 'gh-get-contents',   'name': 'Get Repository Contents','requiresAuth': False, 'status': 'available',    'summary': '获取仓库目录文件列表'},
        {'id': 'gh-list-workflows', 'name': 'List Workflows',         'requiresAuth': True,  'status': 'available',    'summary': '列出 Actions 工作流'},
        {'id': 'gh-trigger-workflow','name': 'Trigger Workflow',      'requiresAuth': True,  'status': 'available',    'summary': '触发 Actions 工作流运行'},
        {'id': 'gh-list-issues',    'name': 'List Issues',            'requiresAuth': False, 'status': 'available',    'summary': '列出仓库的 Issue'},
        {'id': 'gh-close-issue',    'name': 'Close Issue',            'requiresAuth': True,  'status': 'available',    'summary': '关闭 Issue'},
    ],
    'src-notion': [
        {'id': 'ntn-query-db',     'name': 'Query Database',     'requiresAuth': True, 'status': 'available',    'summary': '查询 Notion 数据库条目'},
        {'id': 'ntn-create-page',  'name': 'Create Page',        'requiresAuth': True, 'status': 'available',    'summary': '创建新页面'},
        {'id': 'ntn-update-page',  'name': 'Update Page',        'requiresAuth': True, 'status': 'available',    'summary': '更新页面属性与内容'},
        {'id': 'ntn-get-page',     'name': 'Get Page',           'requiresAuth': True, 'status': 'available',    'summary': '获取页面详情'},
        {'id': 'ntn-search',       'name': 'Search',             'requiresAuth': True, 'status': 'available',    'summary': '全局搜索 Notion 内容'},
        {'id': 'ntn-append-block', 'name': 'Append Block',       'requiresAuth': True, 'status': 'available',    'summary': '追加块内容到页面'},
        {'id': 'ntn-list-dbs',     'name': 'List Databases',     'requiresAuth': True, 'status': 'available',    'summary': '列出可访问的数据库'},
        {'id': 'ntn-get-db',       'name': 'Get Database',       'requiresAuth': True, 'status': 'auth-required','summary': '获取数据库元信息'},
    ],
    'src-slack': [
        {'id': 'sl-post-msg',      'name': 'Post Message',         'requiresAuth': True, 'status': 'available',    'summary': '发送消息到频道'},
        {'id': 'sl-list-channels', 'name': 'List Channels',        'requiresAuth': True, 'status': 'available',    'summary': '列出公开频道'},
        {'id': 'sl-get-history',   'name': 'Get Conversation History','requiresAuth': True,'status': 'available',   'summary': '获取会话历史消息'},
        {'id': 'sl-add-reaction',  'name': 'Add Reaction',         'requiresAuth': True, 'status': 'available',    'summary': '给消息添加表情反应'},
        {'id': 'sl-get-users',     'name': 'List Users',           'requiresAuth': True, 'status': 'available',    'summary': '列出工作区成员'},
        {'id': 'sl-open-convo',    'name': 'Open Conversation',    'requiresAuth': True, 'status': 'available',    'summary': '打开或创建直接消息会话'},
        {'id': 'sl-set-topic',     'name': 'Set Topic',            'requiresAuth': True, 'status': 'available',    'summary': '设置频道主题'},
        {'id': 'sl-upload-file',   'name': 'Upload File',          'requiresAuth': True, 'status': 'available',    'summary': '上传文件到频道'},
        {'id': 'sl-get-reminders', 'name': 'List Reminders',       'requiresAuth': True, 'status': 'available',    'summary': '列出提醒'},
        {'id': 'sl-schedule-msg',  'name': 'Schedule Message',     'requiresAuth': True, 'status': 'disabled',    'summary': '定时发送消息'},
        {'id': 'sl-search',        'name': 'Search Messages',      'requiresAuth': True, 'status': 'available',    'summary': '搜索消息和文件'},
        {'id': 'sl-get-emoji',     'name': 'List Emoji',           'requiresAuth': True, 'status': 'available',    'summary': '获取自定义表情列表'},
        {'id': 'sl-create-chan',   'name': 'Create Channel',       'requiresAuth': True, 'status': 'auth-required','summary': '创建新频道'},
        {'id': 'sl-archive-chan',  'name': 'Archive Channel',      'requiresAuth': True, 'status': 'available',    'summary': '归档频道'},
        {'id': 'sl-kick-user',     'name': 'Kick User',            'requiresAuth': True, 'status': 'disabled',    'summary': '从频道移除成员'},
    ],
    'src-shopify': [
        {'id': 'sp-get-products',  'name': 'Get Products',      'requiresAuth': True, 'status': 'available',    'summary': '查询商品列表'},
        {'id': 'sp-create-order',  'name': 'Create Order',      'requiresAuth': True, 'status': 'available',    'summary': '创建新订单'},
        {'id': 'sp-get-customers', 'name': 'Get Customers',     'requiresAuth': True, 'status': 'available',    'summary': '查询客户列表'},
        {'id': 'sp-get-collections','name': 'Get Collections',  'requiresAuth': True, 'status': 'available',    'summary': '查询集合列表'},
        {'id': 'sp-update-inventory','name': 'Update Inventory','requiresAuth': True, 'status': 'available',    'summary': '更新库存数量'},
        {'id': 'sp-get-orders',    'name': 'Get Orders',        'requiresAuth': True, 'status': 'available',    'summary': '查询订单列表'},
    ],
    'src-gh-graphql': [
        {'id': 'ghg-repo-query',   'name': 'Repository Query',    'requiresAuth': True, 'status': 'auth-required','summary': '通过 GraphQL 查询仓库数据'},
        {'id': 'ghg-user-query',   'name': 'User Profile Query',  'requiresAuth': True, 'status': 'auth-required','summary': '查询用户信息和贡献'},
        {'id': 'ghg-commit-graph', 'name': 'Commit Graph',        'requiresAuth': True, 'status': 'auth-required','summary': '获取提交历史图表数据'},
        {'id': 'ghg-issue-search', 'name': 'Issue Search',        'requiresAuth': True, 'status': 'auth-required','summary': '高级 Issue 搜索'},
        {'id': 'ghg-discussions',  'name': 'Discussion Query',    'requiresAuth': True, 'status': 'auth-required','summary': '查询仓库讨论'},
    ],
    'src-fs-mcp': [
        {'id': 'fs-read-file',     'name': 'Read File',         'requiresAuth': False, 'status': 'available',    'summary': '读取文件内容'},
        {'id': 'fs-write-file',    'name': 'Write File',        'requiresAuth': False, 'status': 'available',    'summary': '写入文件'},
        {'id': 'fs-list-dir',      'name': 'List Directory',    'requiresAuth': False, 'status': 'available',    'summary': '列出目录内容'},
        {'id': 'fs-get-info',      'name': 'Get File Info',     'requiresAuth': False, 'status': 'available',    'summary': '获取文件元信息'},
    ],
    'src-pw-mcp': [
        {'id': 'pw-navigate',      'name': 'Navigate',          'requiresAuth': False, 'status': 'disabled',     'summary': '导航到 URL'},
        {'id': 'pw-click',         'name': 'Click Element',     'requiresAuth': False, 'status': 'disabled',     'summary': '点击页面元素'},
        {'id': 'pw-screenshot',    'name': 'Screenshot',        'requiresAuth': False, 'status': 'disabled',     'summary': '截取页面截图'},
    ],
    'src-gmail': [],
}

_SAMPLE_CREDENTIALS = [
    {'id': 'cred-gh-rest',   'provider': 'github',    'targetType': 'source', 'targetId': 'src-github-rest',  'status': 'healthy',  'lastCheckedAt': '2026-05-13T08:00:00Z', 'impactCount': 12},
    {'id': 'cred-notion',    'provider': 'notion',    'targetType': 'source', 'targetId': 'src-notion',       'status': 'healthy',  'lastCheckedAt': '2026-05-13T08:00:00Z', 'impactCount': 8},
    {'id': 'cred-slack',     'provider': 'slack',     'targetType': 'source', 'targetId': 'src-slack',        'status': 'healthy',  'lastCheckedAt': '2026-05-13T08:00:00Z', 'impactCount': 15},
    {'id': 'cred-shopify',   'provider': 'shopify',   'targetType': 'source', 'targetId': 'src-shopify',      'status': 'healthy',  'lastCheckedAt': '2026-05-13T08:00:00Z', 'impactCount': 6},
    {'id': 'cred-gh-graphql','provider': 'github',    'targetType': 'source', 'targetId': 'src-gh-graphql',   'status': 'missing',  'lastCheckedAt': None,                    'impactCount': 5},
    {'id': 'cred-gmail',     'provider': 'google',    'targetType': 'source', 'targetId': 'src-gmail',        'status': 'expired',  'lastCheckedAt': '2026-04-01T12:00:00Z', 'impactCount': 1},
]

_SAMPLE_PROVIDERS = [
    {'id': 'prov-openapi',    'provider': 'openapi',    'status': 'reachable', 'sourceCount': 3, 'toolCount': 35, 'issueSummary': None},
    {'id': 'prov-graphql',    'provider': 'graphql',    'status': 'degraded',  'sourceCount': 2, 'toolCount': 11, 'issueSummary': 'GitHub GraphQL 缺少凭证配置'},
    {'id': 'prov-mcp',        'provider': 'mcp',        'status': 'reachable', 'sourceCount': 2, 'toolCount': 7,  'issueSummary': None},
    {'id': 'prov-discovery',  'provider': 'discovery',  'status': 'failed',    'sourceCount': 1, 'toolCount': 0,  'issueSummary': 'Gmail API 凭证已过期，重新认证后恢复'},
]


class SampleExecutorProvider(ExecutorProvider):

    def get_sources(self):
        return _SAMPLE_SOURCES

    def get_tools(self, source_id=''):
        all_tools = []
        for sid, tools in _SAMPLE_TOOLS_BY_SOURCE.items():
            for t in tools:
                entry = dict(t)
                entry['sourceId'] = sid
                entry['schemaSummary'] = _tool_schema_summary(entry)
                all_tools.append(entry)
        if source_id:
            all_tools = [t for t in all_tools if t.get('sourceId') == source_id]
        return all_tools

    def get_credentials(self):
        return _SAMPLE_CREDENTIALS

    def get_providers(self):
        return _SAMPLE_PROVIDERS

    def get_summary(self):
        healthy = sum(1 for s in _SAMPLE_SOURCES if s['status'] == 'healthy')
        degraded = sum(1 for s in _SAMPLE_SOURCES if s['status'] in ('degraded', 'missing-auth'))
        total_tools = sum(len(tools) for tools in _SAMPLE_TOOLS_BY_SOURCE.values())
        missing_cred = sum(1 for c in _SAMPLE_CREDENTIALS if c['status'] in ('missing', 'expired'))
        failed_providers = sum(1 for p in _SAMPLE_PROVIDERS if p['status'] == 'failed')
        return {
            'sourceCount': len(_SAMPLE_SOURCES),
            'healthySourceCount': healthy,
            'degradedSourceCount': degraded,
            'toolCount': total_tools,
            'missingCredentialCount': missing_cred,
            'providerCount': len(_SAMPLE_PROVIDERS),
            'failedProviderCount': failed_providers,
        }

    # ---- Write operations ----

    def create_source(self, data):
        src_id = 'src-' + data.get('name', 'unknown').lower().replace(' ', '-').replace('/', '-')
        src_id = src_id[:48]
        existing_ids = {s['id'] for s in _SAMPLE_SOURCES}
        if src_id in existing_ids:
            src_id = src_id + '-' + str(len(_SAMPLE_SOURCES) + 1)
        source = {
            'id': src_id,
            'name': data.get('name', 'New Source'),
            'type': data.get('type', 'openapi'),
            'scope': data.get('scope', 'user'),
            'status': 'healthy',
            'toolCount': 0,
            'provider': data.get('type', 'openapi'),
        }
        _SAMPLE_SOURCES.append(source)
        _SAMPLE_TOOLS_BY_SOURCE[src_id] = []
        return source

    def update_source(self, source_id, data):
        for s in _SAMPLE_SOURCES:
            if s['id'] == source_id:
                for key in ('name', 'type', 'scope', 'status', 'provider'):
                    if key in data:
                        s[key] = data[key]
                return s
        return None

    def delete_source(self, source_id):
        for i, s in enumerate(_SAMPLE_SOURCES):
            if s['id'] == source_id:
                _SAMPLE_SOURCES.pop(i)
                _SAMPLE_TOOLS_BY_SOURCE.pop(source_id, None)
                return True
        return False

    def bind_credential(self, data):
        cred_id = 'cred-' + data.get('provider', 'unknown').lower() + '-' + str(len(_SAMPLE_CREDENTIALS) + 1)
        credential = {
            'id': cred_id,
            'provider': data.get('provider', 'unknown'),
            'targetType': data.get('targetType', 'source'),
            'targetId': data.get('targetId', ''),
            'status': 'healthy',
            'lastCheckedAt': _now_iso(),
            'impactCount': data.get('impactCount', 0),
        }
        _SAMPLE_CREDENTIALS.append(credential)
        return credential

    def unbind_credential(self, credential_id):
        for i, c in enumerate(_SAMPLE_CREDENTIALS):
            if c['id'] == credential_id:
                _SAMPLE_CREDENTIALS.pop(i)
                return True
        return False

    def get_capabilities(self):
        capabilities = {
            'sourceCreate': True,
            'sourceStatusToggle': True,
            'sourceDelete': True,
            'credentialBind': True,
            'credentialUnbind': True,
            'modeLabel': 'sample',
        }
        capabilities.update(_executor_cli_capability())
        capabilities['executorHttpReachable'] = False
        return capabilities


# ============================================================
# HTTP provider (calls real executor API)
# ============================================================

class HttpExecutorProvider(ExecutorProvider):
    """
    Calls executor's local HTTP API.
    Real executor protocol details:
      - public API is mounted under /api/*
      - scope id should be discovered from GET /api/scope
      - generic reads are unified; writes are partly generic, partly plugin-specific
    """

    def __init__(self, base_url='http://127.0.0.1:4788', scope_id=''):
        self.base_url = base_url.rstrip('/')
        self.scope_id = scope_id or ''
        self._scope_info = None

    def _get(self, path, timeout=5):
        url = f'{self.base_url}{path}'
        try:
            req = urlrequest.Request(url, method='GET', headers={'Accept': 'application/json'})
            with urlrequest.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode('utf-8', errors='replace')
                return json.loads(body) if body else []
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
            return None

    def _mutate(self, path, method='POST', data=None):
        url = f'{self.base_url}{path}'
        try:
            payload = json.dumps(data).encode('utf-8') if data is not None else None
            req = urlrequest.Request(
                url,
                method=method,
                data=payload,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json' if data is not None else 'text/plain',
                },
            )
            with urlrequest.urlopen(req, timeout=8) as resp:
                body = resp.read().decode('utf-8', errors='replace')
                return json.loads(body) if body else {}
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
            return None

    def _ensure_scope(self):
        if self.scope_id:
            return self.scope_id
        info = self._get('/api/scope')
        if isinstance(info, dict) and info.get('id'):
            self._scope_info = info
            self.scope_id = info.get('id') or ''
        return self.scope_id

    def _normalize_source_type(self, source_id, raw_kind):
        if raw_kind in ('openapi', 'graphql', 'mcp'):
            return raw_kind
        if raw_kind in ('googleDiscovery', 'google-discovery'):
            return 'discovery'
        if raw_kind == 'control':
            if source_id == 'openapi':
                return 'openapi'
            if source_id == 'graphql':
                return 'graphql'
            if source_id == 'mcp':
                return 'mcp'
            if source_id in ('google-discovery', 'googleDiscovery'):
                return 'discovery'
        return raw_kind or 'unknown'

    def _plugin_route_key(self, source_type):
        mapping = {
            'openapi': 'openapi',
            'graphql': 'graphql',
            'mcp': 'mcp',
            'discovery': 'google-discovery',
        }
        return mapping.get(source_type, source_type)

    def _binding_id(self, source_type, source_id, source_scope, binding_scope, slot):
        from urllib.parse import quote
        return 'binding:' + '|'.join([
            quote(str(source_type or ''), safe=''),
            quote(str(source_id or ''), safe=''),
            quote(str(source_scope or ''), safe=''),
            quote(str(binding_scope or ''), safe=''),
            quote(str(slot or ''), safe=''),
        ])

    def _parse_binding_id(self, binding_id):
        from urllib.parse import unquote
        if not str(binding_id).startswith('binding:'):
            return None
        body = str(binding_id)[8:]
        parts = body.split('|')
        if len(parts) != 5:
            return None
        return {
            'sourceType': unquote(parts[0]),
            'sourceId': unquote(parts[1]),
            'sourceScope': unquote(parts[2]),
            'scope': unquote(parts[3]),
            'slot': unquote(parts[4]),
        }

    def _derive_source_status(self, source_data):
        raw_kind = source_data.get('kind', '')
        runtime = source_data.get('runtime', False)
        if raw_kind == 'mcp' and not runtime:
            return 'disabled'
        return 'healthy'

    def get_sources(self):
        scope_id = self._ensure_scope()
        if not scope_id:
            return None
        data = self._get(f'/api/scopes/{scope_id}/sources')
        if data is None:
            return None
        sources = []
        for s in data if isinstance(data, list) else data.get('data', data.get('sources', [])):
            source_id = s.get('id', '')
            raw_kind = s.get('kind', 'unknown')
            source_type = self._normalize_source_type(source_id, raw_kind)
            sources.append({
                'id': source_id,
                'name': s.get('name', ''),
                'type': source_type,
                'scope': s.get('scopeId') or scope_id,
                'status': self._derive_source_status(s),
                'toolCount': 0,
                'provider': source_type,
                'rawKind': raw_kind,
                'runtime': s.get('runtime'),
                'canRemove': s.get('canRemove', False),
                'canRefresh': s.get('canRefresh', False),
                'canEdit': s.get('canEdit', False),
                'isControl': raw_kind == 'control',
            })
        for src in sources:
            tools_data = self._get(f'/api/scopes/{scope_id}/sources/{src["id"]}/tools')
            if isinstance(tools_data, list):
                src['toolCount'] = len(tools_data)
        return sources

    def get_tools(self, source_id=''):
        scope_id = self._ensure_scope()
        if not scope_id:
            return None
        if source_id:
            data = self._get(f'/api/scopes/{scope_id}/sources/{source_id}/tools')
        else:
            data = self._get(f'/api/scopes/{scope_id}/tools')
        if data is None:
            return None
        tools = []
        for t in data if isinstance(data, list) else data.get('data', data.get('tools', [])):
            tools.append({
                'id': t.get('id', ''),
                'sourceId': t.get('sourceId', source_id),
                'name': t.get('name', ''),
                'summary': t.get('description', ''),
                'requiresAuth': t.get('requiresApproval', False),
                'status': _tool_status(t),
                'schemaSummary': _tool_schema_summary(t),
            })
        return tools

    def _list_source_bindings(self, source):
        scope_id = self._ensure_scope()
        if not scope_id:
            return []
        if source.get('isControl'):
            return []
        source_type = source.get('type')
        if source_type not in ('openapi', 'graphql', 'mcp'):
            return []
        route = self._plugin_route_key(source_type)
        source_id = source.get('id')
        source_scope = source.get('scope') or scope_id
        data = self._get(f'/api/scopes/{scope_id}/{route}/sources/{source_id}/base/{source_scope}/bindings')
        return data if isinstance(data, list) else []

    def get_credentials(self):
        scope_id = self._ensure_scope()
        if not scope_id:
            return None
        creds = []

        sources = self.get_sources() or []
        for source in sources:
            bindings = self._list_source_bindings(source)
            for binding in bindings:
                value = binding.get('value') or {}
                value_kind = value.get('kind')
                status = 'healthy'
                if value_kind == 'secret' and value.get('secretId'):
                    secret_scope = value.get('secretScopeId') or binding.get('scopeId') or scope_id
                    sec_status = self._get(f'/api/scopes/{secret_scope}/secrets/{value["secretId"]}/status')
                    if isinstance(sec_status, dict) and sec_status.get('status') == 'missing':
                        status = 'missing'
                creds.append({
                    'id': self._binding_id(source.get('type'), binding.get('sourceId'), binding.get('sourceScopeId'), binding.get('scopeId'), binding.get('slot')),
                    'provider': source.get('type', ''),
                    'targetType': 'source',
                    'targetId': binding.get('sourceId', ''),
                    'status': status,
                    'lastCheckedAt': _now_iso(),
                    'impactCount': 1,
                    'isBinding': True,
                    'sourceType': source.get('type'),
                    'sourceScope': binding.get('sourceScopeId') or source.get('scope') or scope_id,
                    'bindingScope': binding.get('scopeId') or scope_id,
                    'slot': binding.get('slot'),
                    'valueKind': value_kind,
                    'secretId': value.get('secretId'),
                    'connectionId': value.get('connectionId'),
                })
        return creds

    def get_providers(self):
        sources = self.get_sources()
        if sources is None:
            return None
        by_provider = {}
        for s in sources:
            provider = s.get('provider', 'unknown')
            bucket = by_provider.setdefault(provider, {'sources': []})
            bucket['sources'].append(s)
        provs = []
        for key, info in by_provider.items():
            bucket_sources = info['sources']
            status = _provider_rollup_status(bucket_sources)
            provs.append({
                'id': f'prov-{key}',
                'provider': key,
                'status': status,
                'sourceCount': len(bucket_sources),
                'toolCount': sum(item.get('toolCount', 0) for item in bucket_sources),
                'issueSummary': _provider_issue_summary(status, bucket_sources),
            })
        return provs

    def get_summary(self):
        sources = self.get_sources()
        if sources is None:
            return None
        tools = self.get_tools() or []
        creds = self.get_credentials() or []
        providers = self.get_providers() or []
        healthy = sum(1 for s in sources if s['status'] == 'healthy')
        degraded = sum(1 for s in sources if s['status'] != 'healthy')
        missing_cred = sum(1 for c in creds if c.get('status') in ('missing', 'expired', 'invalid'))
        return {
            'sourceCount': len(sources),
            'healthySourceCount': healthy,
            'degradedSourceCount': degraded,
            'toolCount': len(tools),
            'missingCredentialCount': missing_cred,
            'providerCount': len(providers),
            'failedProviderCount': sum(1 for provider in providers if provider.get('status') == 'failed'),
        }

    def create_source(self, data):
        scope_id = self._ensure_scope()
        if not scope_id:
            return None
        source_type = data.get('type')
        payload = None
        path = None
        if source_type == 'openapi':
            if not data.get('spec'):
                raise ExecutorBridgeUnsupported('openapi source creation requires spec text.')
            path = f'/api/scopes/{scope_id}/openapi/specs'
            payload = {
                'targetScope': scope_id,
                'spec': data.get('spec'),
                'name': data.get('name') or None,
                'baseUrl': data.get('baseUrl') or None,
                'namespace': data.get('namespace') or None,
            }
        elif source_type == 'graphql':
            if not data.get('endpoint'):
                raise ExecutorBridgeUnsupported('graphql source creation requires endpoint.')
            path = f'/api/scopes/{scope_id}/graphql/sources'
            payload = {
                'targetScope': scope_id,
                'endpoint': data.get('endpoint'),
                'name': data.get('name') or None,
                'namespace': data.get('namespace') or None,
                'introspectionJson': data.get('introspectionJson') or None,
            }
        elif source_type == 'mcp':
            transport = data.get('transport') or 'remote'
            path = f'/api/scopes/{scope_id}/mcp/sources'
            if transport == 'stdio':
                if not data.get('command'):
                    raise ExecutorBridgeUnsupported('mcp stdio source creation requires command.')
                payload = {
                    'targetScope': scope_id,
                    'transport': 'stdio',
                    'name': data.get('name') or 'MCP Source',
                    'command': data.get('command'),
                    'args': data.get('args') or None,
                    'cwd': data.get('cwd') or None,
                    'namespace': data.get('namespace') or None,
                }
            else:
                if not data.get('endpoint'):
                    raise ExecutorBridgeUnsupported('mcp remote source creation requires endpoint.')
                payload = {
                    'targetScope': scope_id,
                    'transport': 'remote',
                    'name': data.get('name') or 'MCP Source',
                    'endpoint': data.get('endpoint'),
                    'remoteTransport': data.get('remoteTransport') or 'auto',
                    'namespace': data.get('namespace') or None,
                }
        elif source_type == 'discovery':
            if not data.get('discoveryUrl'):
                raise ExecutorBridgeUnsupported('google discovery source creation requires discoveryUrl.')
            path = f'/api/scopes/{scope_id}/google-discovery/sources'
            payload = {
                'name': data.get('name') or 'Discovery Source',
                'discoveryUrl': data.get('discoveryUrl'),
                'namespace': data.get('namespace') or None,
                'auth': {'kind': 'none'},
            }
        else:
            raise ExecutorBridgeUnsupported(f'unsupported source type: {source_type}')

        result = self._mutate(path, method='POST', data=payload)
        if result is None:
            return None
        namespace = result.get('namespace') or data.get('namespace') or data.get('name', '')
        sources = self.get_sources() or []
        for source in sources:
            if source.get('id') == namespace:
                return source
        return {
            'id': namespace,
            'name': data.get('name') or namespace,
            'type': source_type,
            'scope': scope_id,
            'status': 'healthy',
            'toolCount': result.get('toolCount', 0),
            'provider': source_type,
            'canRemove': True,
            'canRefresh': True,
            'canEdit': True,
            'isControl': False,
        }

    def update_source(self, source_id, data):
        scope_id = self._ensure_scope()
        if not scope_id:
            return None
        if data.get('refresh'):
            result = self._mutate(f'/api/scopes/{scope_id}/sources/{source_id}/refresh', method='POST', data={})
            return {'id': source_id, 'refreshed': True} if result is not None else None
        if set(data.keys()) == {'status'}:
            raise ExecutorBridgeUnsupported('executor HTTP mode does not provide a generic source status toggle endpoint.')
        raise ExecutorBridgeUnsupported('executor HTTP mode currently supports source refresh, not generic source patch.')

    def delete_source(self, source_id):
        scope_id = self._ensure_scope()
        if not scope_id:
            return False
        result = self._mutate(f'/api/scopes/{scope_id}/sources/{source_id}', method='DELETE')
        return isinstance(result, dict) and result.get('removed', False)

    def bind_credential(self, data):
        scope_id = self._ensure_scope()
        if not scope_id:
            return None

        source_type = data.get('sourceType')
        slot = data.get('slot')
        if source_type and slot and data.get('targetId'):
            plugin = self._plugin_route_key(source_type)
            value_kind = data.get('valueKind') or 'secret'
            if value_kind == 'secret':
                secret_payload = {
                    'id': data.get('secretId') or f"secret-{data.get('provider', source_type)}-{int(datetime.now(timezone.utc).timestamp())}",
                    'name': data.get('secretName') or data.get('provider') or 'credential',
                    'value': data.get('secretValue', ''),
                    'provider': data.get('provider') or 'file',
                }
                secret_ref = self._mutate(f'/api/scopes/{scope_id}/secrets', method='POST', data=secret_payload)
                if not isinstance(secret_ref, dict) or not secret_ref.get('id'):
                    return None
                binding_value = {
                    'kind': 'secret',
                    'secretId': secret_ref.get('id'),
                    'secretScopeId': secret_ref.get('scopeId') or scope_id,
                }
            elif value_kind == 'text':
                binding_value = {
                    'kind': 'text',
                    'text': data.get('textValue', ''),
                }
            elif value_kind == 'connection':
                binding_value = {
                    'kind': 'connection',
                    'connectionId': data.get('connectionId', ''),
                }
            else:
                raise ExecutorBridgeUnsupported(f'unsupported binding value kind: {value_kind}')

            payload = {
                'sourceId': data.get('targetId'),
                'sourceScope': data.get('sourceScope') or scope_id,
                'scope': data.get('bindingScope') or scope_id,
                'slot': slot,
                'value': binding_value,
            }
            binding = self._mutate(f'/api/scopes/{scope_id}/{plugin}/source-bindings', method='POST', data=payload)
            if not isinstance(binding, dict):
                return None
            return {
                'id': self._binding_id(source_type, payload['sourceId'], payload['sourceScope'], payload['scope'], payload['slot']),
                'provider': source_type,
                'targetType': 'source',
                'targetId': payload['sourceId'],
                'status': 'healthy',
                'lastCheckedAt': _now_iso(),
                'impactCount': 1,
                'isBinding': True,
                'sourceType': source_type,
                'sourceScope': payload['sourceScope'],
                'bindingScope': payload['scope'],
                'slot': payload['slot'],
                'valueKind': value_kind,
                'secretId': binding_value.get('secretId'),
                'connectionId': binding_value.get('connectionId'),
            }

        payload = {
            'id': data.get('id') or f"secret-{data.get('provider', 'unknown')}-{int(datetime.now(timezone.utc).timestamp())}",
            'name': data.get('provider', 'credential'),
            'value': data.get('value', 'placeholder-secret'),
            'provider': data.get('provider') or 'file',
        }
        return self._mutate(f'/api/scopes/{scope_id}/secrets', method='POST', data=payload)

    def unbind_credential(self, credential_id):
        scope_id = self._ensure_scope()
        if not scope_id:
            return False
        parsed = self._parse_binding_id(credential_id)
        if parsed:
            plugin = self._plugin_route_key(parsed['sourceType'])
            payload = {
                'sourceId': parsed['sourceId'],
                'sourceScope': parsed['sourceScope'],
                'slot': parsed['slot'],
                'scope': parsed['scope'],
            }
            result = self._mutate(f'/api/scopes/{scope_id}/{plugin}/source-bindings/remove', method='POST', data=payload)
            return isinstance(result, dict) and result.get('removed', False)
        result = self._mutate(f'/api/scopes/{scope_id}/secrets/{credential_id}', method='DELETE')
        return isinstance(result, dict) and result.get('removed', False)

    def get_capabilities(self):
        scope_id = self._ensure_scope()
        capabilities = {
            'sourceCreate': True,
            'sourceCreateTypes': ['openapi', 'graphql', 'mcp', 'discovery'],
            'sourceRefresh': True,
            'sourceStatusToggle': False,
            'sourceDelete': True,
            'credentialBind': True,
            'credentialUnbind': True,
            'modeLabel': 'http',
            'scopeId': scope_id,
        }
        capabilities.update(_executor_cli_capability())
        capabilities['executorHttpReachable'] = True
        return capabilities


# ============================================================
# Provider registry & auto-detect
# ============================================================

_EXECUTOR_EXECUTOR_BASE_URL = os.environ.get('EXECUTOR_API_BASE_URL', '')
_EXECUTOR_SCOPE_ID = os.environ.get('EXECUTOR_SCOPE_ID', '')

_provider_instance = None
_provider_mode = None


def _probe_executor(url, timeout=2):
    """Check if executor local HTTP API is reachable."""
    try:
        req = urlrequest.Request(f'{url}/api/scope', method='GET', headers={'Accept': 'application/json'})
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_executor_provider():
    """
    Returns the appropriate ExecutorProvider based on executor availability.
    - If EXECUTOR_API_BASE_URL is set and reachable → HttpExecutorProvider
    - Otherwise → SampleExecutorProvider
    """
    global _provider_instance, _provider_mode

    if _provider_instance is not None:
        return _provider_instance

    base_url = _EXECUTOR_EXECUTOR_BASE_URL or 'http://127.0.0.1:4788'

    if _probe_executor(base_url):
        _provider_instance = HttpExecutorProvider(base_url=base_url, scope_id=_EXECUTOR_SCOPE_ID)
        _provider_mode = 'http'
    else:
        _provider_instance = SampleExecutorProvider()
        _provider_mode = 'sample'

    return _provider_instance


def get_provider_mode():
    """Returns 'http' or 'sample' — which provider is currently active."""
    if _provider_mode is None:
        get_executor_provider()
    return _provider_mode


def reset_provider():
    """Force re-detection on next access."""
    global _provider_instance, _provider_mode
    _provider_instance = None
    _provider_mode = None
