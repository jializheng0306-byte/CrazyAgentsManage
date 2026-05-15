"""
CrazyAgentsManage WebUI API Layer
Connects to Hermes-Agent's real data sources: state.db, cron/jobs.json, gateway_state.json, tools/registry
Supports both local and remote (SSH) data access modes
"""

import json
import os
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from flask import Blueprint, jsonify, request

api = Blueprint('api', __name__, url_prefix='/api')

_hermes_home = None
_remote_config = None
_skills_cache = {'data': None, 'timestamp': 0}
_skills_cache_ttl = 300
_overview_stats_cache = {'data': None, 'timestamp': 0}
_overview_stats_cache_ttl = 60
_overview_dashboard_cache = {'data': None, 'timestamp': 0}
_overview_dashboard_cache_ttl = 60
_dashboard_cache = {'data': None, 'timestamp': 0}
_dashboard_cache_ttl = 30
_local_db_cache = {}
_local_db_lock = threading.Lock()


def _get_repo_root():
    return Path(__file__).resolve().parents[2]


def _get_hermes_home():
    global _hermes_home
    if _hermes_home is None:
        _hermes_home = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
    return _hermes_home


def _get_remote_config():
    global _remote_config
    if _remote_config is None:
        config_path = Path(__file__).resolve().parent / 'remote_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    _remote_config = json.load(f)
            except Exception:
                _remote_config = {}
        else:
            _remote_config = {}
    return _remote_config


def _is_remote_mode():
    cfg = _get_remote_config()
    return bool(cfg.get('host'))


def _get_local_db():
    db_path = _get_hermes_home() / 'state.db'
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=1")
        return conn
    except Exception:
        return None


def _fetch_remote_db_data(query, params=()):
    cfg = _get_remote_config()
    host = cfg.get('host', '')
    user = cfg.get('user', 'root')
    password = cfg.get('password', '')
    hermes_home = cfg.get('hermes_home', '/root/.hermes')

    if not host:
        return []

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=30)

        py_script = f'''
import sqlite3, json
conn = sqlite3.connect("{hermes_home}/state.db")
conn.row_factory = sqlite3.Row
try:
    c = conn.execute(%s, {list(params)})
    cols = [d[0] for d in c.description] if c.description else []
    rows = [dict(zip(cols, row)) for row in c.fetchall()]
    print(json.dumps(rows, default=str))
except Exception as e:
    print(json.dumps([]))
finally:
    conn.close()
''' % repr(query)
        sftp = client.open_sftp()
        with sftp.file('/tmp/_webui_query.py', 'w') as f:
            f.write(py_script)
        sftp.close()

        python_path = cfg.get('python_path', '/root/hermes-agent/venv/bin/python3')
        stdin, stdout, stderr = client.exec_command(f'{python_path} /tmp/_webui_query.py', timeout=30)
        out = stdout.read().decode('utf-8', errors='replace')
        client.close()

        if out.strip():
            return json.loads(out.strip())
        return []
    except Exception:
        return []


def _db_query(query, params=()):
    if _is_remote_mode():
        return _fetch_remote_db_data(query, params)

    conn = _get_local_db()
    if not conn:
        return []
    try:
        c = conn.execute(query, params)
        cols = [d[0] for d in c.description] if c.description else []
        return [dict(zip(cols, row)) for row in c.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def _fetch_remote_json(path):
    cfg = _get_remote_config()
    host = cfg.get('host', '')
    user = cfg.get('user', 'root')
    password = cfg.get('password', '')
    hermes_home = cfg.get('hermes_home', '/root/.hermes')

    if not host:
        return {}

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=30)
        full_path = f"{hermes_home}/{path}"
        stdin, stdout, stderr = client.exec_command(f"cat '{full_path}' 2>/dev/null", timeout=15)
        out = stdout.read().decode('utf-8', errors='replace')
        client.close()
        if out.strip():
            return json.loads(out.strip())
        return {}
    except Exception:
        return {}


def _fetch_remote_dir(path, pattern='*'):
    cfg = _get_remote_config()
    host = cfg.get('host', '')
    user = cfg.get('user', 'root')
    password = cfg.get('password', '')
    hermes_home = cfg.get('hermes_home', '/root/.hermes')

    if not host:
        return []

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=30)
        full_path = f"{hermes_home}/{path}"
        cmd = f"find '{full_path}' -maxdepth 1 -type d 2>/dev/null | sort"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
        out = stdout.read().decode('utf-8', errors='replace')
        client.close()
        dirs = [d.strip().split('/')[-1] for d in out.strip().split('\n') if d.strip() and d.strip() != full_path]
        return dirs
    except Exception:
        return []


def _fetch_remote_file_list(path, ext='*.md'):
    cfg = _get_remote_config()
    host = cfg.get('host', '')
    user = cfg.get('user', 'root')
    password = cfg.get('password', '')
    hermes_home = cfg.get('hermes_home', '/root/.hermes')

    if not host:
        return []

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=30)
        full_path = f"{hermes_home}/{path}"
        cmd = f"find '{full_path}' -name '{ext}' -type f 2>/dev/null | sort"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
        out = stdout.read().decode('utf-8', errors='replace')
        client.close()
        files = [f.strip() for f in out.strip().split('\n') if f.strip()]
        return files
    except Exception:
        return []


def _read_json(path, default=None):
    if _is_remote_mode():
        result = _fetch_remote_json(path)
        return result if result else (default if default is not None else {})

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _read_file(path, default=''):
    if _is_remote_mode():
        cfg = _get_remote_config()
        host = cfg.get('host', '')
        user = cfg.get('user', 'root')
        password = cfg.get('password', '')
        hermes_home = cfg.get('hermes_home', '/root/.hermes')

        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=user, password=password, timeout=30)
            rel_path = str(path).replace(str(_get_hermes_home()) + '/', '').replace(str(_get_hermes_home()) + '\\', '')
            full_path = f"{hermes_home}/{rel_path}"
            stdin, stdout, stderr = client.exec_command(f"cat '{full_path}' 2>/dev/null", timeout=15)
            out = stdout.read().decode('utf-8', errors='replace')
            client.close()
            return out if out else default
        except Exception:
            return default

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default


def _list_dir(base_path, sub_path=''):
    if _is_remote_mode():
        dirs = _fetch_remote_dir(f"{sub_path}" if sub_path else ".")
        return dirs

    full_path = base_path / sub_path if sub_path else base_path
    if not full_path.exists():
        return []
    return [d.name for d in sorted(full_path.iterdir()) if d.is_dir()]


def _list_files(base_path, sub_path='', ext='*.md'):
    if _is_remote_mode():
        files = _fetch_remote_file_list(sub_path or '.', ext)
        return [f.split('/')[-1] for f in files]

    full_path = base_path / sub_path if sub_path else base_path
    if not full_path.exists():
        return []
    return [f.name for f in sorted(full_path.glob(ext))]


def _read_optional_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _get_flowmind_base_url():
    return os.environ.get('FLOWMIND_API_BASE_URL', 'http://127.0.0.1:3001').rstrip('/')


def _get_flowmind_api_key():
    return os.environ.get('FLOWMIND_API_KEY', 'flowmind-dev-token')


def _get_flowmind_source_agent():
    return os.environ.get('FLOWMIND_SOURCE_AGENT', 'HermesAgent').strip()


def _flowmind_request(path, query=None, method='GET', data=None):
    url = f"{_get_flowmind_base_url()}{path}"
    if query:
        url = f"{url}?{urlparse.urlencode(query)}"

    payload = None
    headers = {
        'Accept': 'application/json',
        'Authorization': f"Bearer {_get_flowmind_api_key()}",
    }
    if data is not None:
        payload = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urlrequest.Request(url, method=method, data=payload, headers=headers)
    with urlrequest.urlopen(req, timeout=8) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        body = response.read().decode(charset, errors='replace')
        return json.loads(body) if body else {}


def _safe_flowmind_request(path, query=None, method='GET', data=None, default=None):
    try:
        return _flowmind_request(path, query=query, method=method, data=data)
    except (urlerror.URLError, urlerror.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return default


def _normalize_bridge_trace(candidate_id, upstream):
    if not isinstance(upstream, dict):
        return {
            'candidateId': candidate_id,
            'candidateStatus': '',
            'semanticContext': {},
            'traceCount': 0,
            'traceEvents': [],
            'latestStatus': '',
            'upstream': _get_flowmind_base_url(),
        }

    payload = upstream.get('data')
    if isinstance(payload, dict):
        upstream = payload

    if isinstance(upstream.get('traceEvents'), list):
        trace_events = [event for event in upstream.get('traceEvents', []) if isinstance(event, dict)]
        latest_status = upstream.get('candidateStatus') or (trace_events[-1].get('toStatus') if trace_events else '')
        return {
            'candidateId': upstream.get('candidateId') or candidate_id,
            'candidateStatus': upstream.get('candidateStatus') or '',
            'semanticContext': upstream.get('semanticContext') or {},
            'traceCount': upstream.get('traceCount') if isinstance(upstream.get('traceCount'), int) else len(trace_events),
            'traceEvents': trace_events,
            'latestStatus': latest_status or '',
            'upstream': _get_flowmind_base_url(),
        }

    raw_events = []
    if isinstance(upstream.get('events'), list):
        raw_events = upstream.get('events', [])
    elif isinstance(upstream.get('trace'), list):
        raw_events = upstream.get('trace', [])
    elif isinstance(upstream.get('data'), list):
        raw_events = upstream.get('data', [])

    trace_events = []
    for index, event in enumerate(raw_events):
        if not isinstance(event, dict):
            continue
        summary = event.get('summary') or event.get('detail') or event.get('label') or event.get('action') or ''
        trace_events.append({
            'traceId': event.get('traceId') or event.get('id') or f'{candidate_id}:{index}',
            'candidateId': event.get('candidateId') or candidate_id,
            'action': event.get('action') or event.get('eventType') or 'query',
            'actor': event.get('actor') or 'system',
            'fromStatus': event.get('fromStatus'),
            'toStatus': event.get('toStatus') or event.get('status'),
            'module': event.get('module') or event.get('moduleId') or 'bridge',
            'timestamp': event.get('timestamp') or event.get('createdAt') or event.get('occurredAt'),
            'summary': summary,
            'payload': event.get('payload') or event.get('requestPayload') or {},
            'semanticRefs': event.get('semanticRefs') or [],
        })

    trace_events.sort(key=lambda item: item.get('timestamp') or '')
    latest_status = trace_events[-1].get('toStatus') if trace_events else ''
    return {
        'candidateId': upstream.get('candidateId') or candidate_id,
        'candidateStatus': upstream.get('candidateStatus') or latest_status or '',
        'semanticContext': upstream.get('semanticContext') or {},
        'traceCount': upstream.get('traceCount') if isinstance(upstream.get('traceCount'), int) else len(trace_events),
        'traceEvents': trace_events,
        'latestStatus': latest_status or '',
        'upstream': _get_flowmind_base_url(),
    }


def _handoff_field_map(sections):
    field_map = {}
    for section in sections or []:
        for item in section.get('items') or []:
            label = item.get('label')
            if not label:
                continue
            field_map[label] = item.get('value')
    return field_map


def _execution_boundary_from_handoff_sections(sections):
    for section in sections or []:
        if section.get('title') != 'Execution Boundary':
            continue
        items = section.get('items') or []
        boundary = {
            'canonicalAuthority': None,
            'localWritableTargets': None,
            'humanGateActions': None,
            'forbiddenMutations': None,
        }
        for item in items:
            label = item.get('label')
            value = item.get('value')
            if label == 'Canonical Authority':
                boundary['canonicalAuthority'] = value
            elif label == 'Local Writable Targets':
                boundary['localWritableTargets'] = value
            elif label == 'Human Gate Actions':
                boundary['humanGateActions'] = value
            elif label == 'Forbidden Mutations':
                boundary['forbiddenMutations'] = value
        return boundary
    return None


def _execution_boundary_from_semantic_context(semantic_context):
    if not isinstance(semantic_context, dict):
        return None
    boundary = semantic_context.get('executionBoundary')
    if not isinstance(boundary, dict):
        return None
    return {
        'canonicalAuthority': boundary.get('canonicalAuthority'),
        'localWritableTargets': boundary.get('localWritableTargets'),
        'humanGateActions': boundary.get('humanGateActions'),
        'forbiddenMutations': boundary.get('forbiddenMutations'),
    }


def _normalize_runtime_handoff_summary(record_id, replay):
    module_details = replay.get('moduleDetails') or {}
    handoff = module_details.get('handoff')
    steps = [step for step in (replay.get('steps') or []) if isinstance(step, dict)]
    latest_step = steps[-1] if steps else {}
    semantic_context = replay.get('semanticContext') or {}

    required_fields = [
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
    boundary_required_fields = [
        'Canonical Authority',
        'Local Writable Targets',
        'Human Gate Actions',
        'Forbidden Mutations',
    ]

    if isinstance(handoff, dict):
        sections = handoff.get('sections') or []
        field_map = _handoff_field_map(sections)
        missing_fields = [field for field in required_fields if field not in field_map or field_map.get(field) in (None, '')]
        handoff_boundary = _execution_boundary_from_handoff_sections(sections)
        semantic_boundary = _execution_boundary_from_semantic_context(semantic_context)
        execution_boundary = handoff_boundary or semantic_boundary
        missing_boundary_fields = []
        if execution_boundary is None:
            missing_boundary_fields = list(boundary_required_fields)
        else:
            missing_boundary_fields = [
                field for field, key in (
                    ('Canonical Authority', 'canonicalAuthority'),
                    ('Local Writable Targets', 'localWritableTargets'),
                    ('Human Gate Actions', 'humanGateActions'),
                    ('Forbidden Mutations', 'forbiddenMutations'),
                )
                if execution_boundary.get(key) in (None, '', [])
            ]
        gaps = list(replay.get('gaps') or [])
        if execution_boundary is None:
            gaps.append('executionBoundary is missing from moduleDetails.handoff and semanticContext.')

        # ── Build unified handoffContract ──
        truth_status = field_map.get('Truth Status', '')
        candidate_status = field_map.get('Candidate Status', '')
        is_ready = truth_status in ('approved', 'committed')
        blocking_issues = list(gaps)
        if missing_fields:
            blocking_issues.append(f'missingFields: {", ".join(missing_fields)}')
        if missing_boundary_fields:
            blocking_issues.append(f'executionBoundaryMissingFields: {", ".join(missing_boundary_fields)}')
        if not is_ready and truth_status:
            blocking_issues.insert(0, f'Truth Status is "{truth_status}" (not ready for handoff)')
        if not is_ready and candidate_status:
            blocking_issues.insert(0, f'Candidate Status is "{candidate_status}" (not ready)')

        handoff_contract = {
            'ready': is_ready,
            'blockingIssues': blocking_issues,
            'missingFields': missing_fields,
            'executionBoundaryMissingFields': missing_boundary_fields,
        }

        return {
            'recordId': record_id,
            'source': 'moduleDetails.handoff',
            'mode': replay.get('mode'),
            'title': handoff.get('title') or 'Handoff Summary',
            'summary': handoff.get('summary') or '',
            'sections': sections,
            'fieldMap': field_map,
            'semanticContext': semantic_context,
            'executionBoundary': execution_boundary,
            'executionBoundarySource': 'moduleDetails.handoff.Execution Boundary' if handoff_boundary else ('semanticContext.executionBoundary' if semantic_boundary else None),
            'executionBoundaryMissingFields': missing_boundary_fields,
            'traceEventCount': len(steps),
            'latestTraceAction': field_map.get('Latest Trace Action'),
            'latestTraceSummary': field_map.get('Latest Trace Summary'),
            'consumerHints': field_map.get('Consumer Hints'),
            'missingFields': missing_fields,
            'gaps': gaps,
            'handoffContract': handoff_contract,
        }

    semantic_boundary = _execution_boundary_from_semantic_context(semantic_context)

    # handoffContract for the missing-handoff fallback
    fallback_contract = {
        'ready': False,
        'blockingIssues': ['moduleDetails.handoff is missing from the current replay payload.'] + list(replay.get('gaps') or []),
        'missingFields': required_fields,
        'executionBoundaryMissingFields': boundary_required_fields,
    }

    return {
        'recordId': record_id,
        'source': 'replay_without_moduleDetails.handoff',
        'mode': replay.get('mode'),
        'title': 'Handoff Summary',
        'summary': '',
        'sections': [],
        'fieldMap': {},
        'semanticContext': semantic_context,
        'executionBoundary': semantic_boundary,
        'executionBoundarySource': 'semanticContext.executionBoundary' if semantic_boundary else None,
        'executionBoundaryMissingFields': [
            field for field, key in (
                ('Canonical Authority', 'canonicalAuthority'),
                ('Local Writable Targets', 'localWritableTargets'),
                ('Human Gate Actions', 'humanGateActions'),
                ('Forbidden Mutations', 'forbiddenMutations'),
            )
            if (semantic_boundary or {}).get(key) in (None, '', [])
        ] or boundary_required_fields,
        'traceEventCount': len(steps),
        'latestTraceAction': latest_step.get('action'),
        'latestTraceSummary': latest_step.get('summary') or latest_step.get('detail') or latest_step.get('label'),
        'consumerHints': None,
        'missingFields': required_fields,
        'gaps': (replay.get('gaps') or []) + [
            'moduleDetails.handoff is missing from the current replay payload.',
            'executionBoundary is missing from moduleDetails.handoff and semanticContext.',
        ],
        'handoffContract': fallback_contract,
    }
def _flowmind_records(limit=80, source_agent=None):
    agent_filter = source_agent if source_agent is not None else _get_flowmind_source_agent()
    sessions_resp = _safe_flowmind_request(
        '/api/integrations/sessions',
        query={'page': 1, 'limit': max(limit, 20)},
        default={'data': []},
    ) or {'data': []}

    records = []
    for session in sessions_resp.get('data', []):
        session_id = session.get('sessionId')
        if not session_id:
            continue
        candidates_resp = _safe_flowmind_request(
            f'/api/integrations/sessions/{session_id}/candidates',
            default={'data': []},
        ) or {'data': []}
        for candidate in candidates_resp.get('data', []):
            source = candidate.get('sourceAgent') or session.get('sourceAgent')
            if agent_filter and source != agent_filter:
                continue
            records.append({
                'id': candidate.get('id'),
                'title': candidate.get('title') or 'Untitled candidate',
                'status': candidate.get('status') or 'unknown',
                'sourceAgent': source,
                'instanceId': candidate.get('instanceId') or session.get('instanceId'),
                'sessionId': candidate.get('sessionId') or session_id,
                'confidence': candidate.get('confidence'),
                'createdAt': candidate.get('createdAt'),
                'updatedAt': candidate.get('updatedAt'),
                'rawText': candidate.get('rawText'),
                'replayMode': 'derived',
                'candidate': candidate,
                'session': session,
            })

    records.sort(key=lambda item: item.get('createdAt') or '', reverse=True)
    return records[:limit]


def _find_flowmind_record(record_id, source_agent=None):
    for record in _flowmind_records(limit=200, source_agent=source_agent):
        if record.get('id') == record_id:
            return record
    return None


def _node_label(node_id):
    for node in (
        ('agent', 'External Agent'),
        ('inbox', 'Inbox Service'),
        ('classify', 'Classification'),
        ('clarify', 'Clarification Loop'),
        ('writegate', 'WriteGate Governance'),
        ('truth', 'Canonical Truth'),
        ('review', 'Review Sessions'),
        ('provenance', 'Provenance'),
        ('memory', '9-Layer Memory'),
        ('trust', 'Trust Score'),
        ('sqlite', 'SQLite / PG'),
        ('vector', 'Qdrant Vector'),
        ('files', 'File System'),
        ('webui', 'Web UI'),
    ):
        if node[0] == node_id:
            return node[1]
    return node_id


def _detail_items_from_mapping(mapping):
    items = []
    for key, value in mapping.items():
        if value is None or value == '':
            continue
        items.append({'label': key, 'value': str(value)})
    return items


def _build_derived_replay(record):
    candidate = record.get('candidate', {})
    session = record.get('session', {})
    status = candidate.get('status') or 'unknown'
    created_at = candidate.get('createdAt')
    updated_at = candidate.get('updatedAt')
    decision = candidate.get('decisionMetadata') or {}
    source_context = candidate.get('sourceContext') or {}

    steps = [
        {
            'key': f"{record['id']}-agent",
            'moduleId': 'agent',
            'label': 'HermesAgent 发起记录',
            'detail': f"来源 {record.get('sourceAgent') or 'unknown'} 通过 integration bridge 将记录送入 FlowMind。",
            'timestamp': created_at,
            'kind': 'derived',
        },
        {
            'key': f"{record['id']}-inbox",
            'moduleId': 'inbox',
            'label': 'Inbox 接收候选记录',
            'detail': '记录被写入候选池，形成 Candidate 对象并关联集成会话。',
            'timestamp': created_at,
            'kind': 'derived',
        },
        {
            'key': f"{record['id']}-classify",
            'moduleId': 'classify',
            'label': 'Classification 归并语义上下文',
            'detail': '当前版本仅能读取候选记录状态与上下文，尚未拿到细粒度分类 trace。',
            'timestamp': created_at,
            'kind': 'derived',
        },
    ]

    if status in ('submitted', 'approved', 'rejected', 'committed') or decision:
        steps.append({
            'key': f"{record['id']}-clarify",
            'moduleId': 'clarify',
            'label': 'Clarification / 确认闭环',
            'detail': '记录已进入人工确认或澄清阶段。',
            'timestamp': decision.get('confirmedAt') or decision.get('rejectedAt') or updated_at,
            'kind': 'derived',
        })
        steps.append({
            'key': f"{record['id']}-writegate",
            'moduleId': 'writegate',
            'label': 'WriteGate 治理判定',
            'detail': f"当前候选状态为 {status}，说明治理层已对记录做出阶段性处理。",
            'timestamp': decision.get('confirmedAt') or decision.get('rejectedAt') or updated_at,
            'kind': 'derived',
        })

    if status in ('approved', 'committed'):
        steps.append({
            'key': f"{record['id']}-truth",
            'moduleId': 'truth',
            'label': '写入 Canonical Truth',
            'detail': '记录已经成为可查询的真实承诺对象。',
            'timestamp': decision.get('confirmedAt') or updated_at,
            'kind': 'derived',
        })
        steps.append({
            'key': f"{record['id']}-provenance",
            'moduleId': 'provenance',
            'label': '生成审计与溯源锚点',
            'detail': '当前 UI 还没有拿到逐步 provenance event，仅能确认该对象已进入可追踪真值域。',
            'timestamp': updated_at,
            'kind': 'derived',
        })
    elif status == 'rejected':
        steps.append({
            'key': f"{record['id']}-review",
            'moduleId': 'review',
            'label': '进入 Review / Rejection 分支',
            'detail': '记录被驳回，保留在治理评审闭环中。',
            'timestamp': decision.get('rejectedAt') or updated_at,
            'kind': 'derived',
        })

    module_details = {
        'agent': {
            'title': 'External Agent / HermesAgent',
            'summary': '记录的外部入口与原始发送上下文。',
            'sections': [
                {'title': 'Ingress', 'items': _detail_items_from_mapping({
                    'Source Agent': record.get('sourceAgent'),
                    'Instance ID': record.get('instanceId'),
                    'Session ID': record.get('sessionId'),
                    'Created At': created_at,
                })},
                {'title': 'Source Context', 'items': _detail_items_from_mapping(source_context if isinstance(source_context, dict) else {'Raw': source_context})},
            ],
        },
        'inbox': {
            'title': 'Inbox Service',
            'summary': 'FlowMind 接收 HermesAgent 发送的记录后，在候选池中的落点。',
            'sections': [
                {'title': 'Candidate', 'items': _detail_items_from_mapping({
                    'Candidate ID': record.get('id'),
                    'Title': record.get('title'),
                    'Status': status,
                    'Confidence': record.get('confidence'),
                })},
                {'title': 'Raw Text', 'items': [{'label': 'Content', 'value': candidate.get('rawText') or '暂无'}]},
            ],
        },
        'classify': {
            'title': 'Classification',
            'summary': '当前上游尚未暴露逐步分类结果，本页只能展示候选记录级别的真实字段。',
            'sections': [
                {'title': 'Available Fields', 'items': _detail_items_from_mapping({
                    'Description': candidate.get('description'),
                    'Updated At': updated_at,
                })},
            ],
        },
        'clarify': {
            'title': 'Clarification Loop',
            'summary': '确认、澄清、驳回等人工治理动作汇聚在这里。',
            'sections': [
                {'title': 'Decision Metadata', 'items': _detail_items_from_mapping({
                    'Confirmed By': decision.get('confirmedBy'),
                    'Confirmed At': decision.get('confirmedAt'),
                    'Rejected By': decision.get('rejectedBy'),
                    'Rejected At': decision.get('rejectedAt'),
                    'Rejected Reason': decision.get('rejectedReason'),
                    'Clarified Questions': ', '.join(decision.get('clarifiedQuestions') or []),
                })},
            ],
        },
        'writegate': {
            'title': 'WriteGate Governance',
            'summary': '当前能确定治理层已经处理过该记录，但还没有拿到逐条 policy / validation / confirmation 的细粒度事件。',
            'sections': [
                {'title': 'Governance State', 'items': _detail_items_from_mapping({
                    'Current Status': status,
                    'Last Updated': updated_at,
                })},
            ],
        },
        'truth': {
            'title': 'Canonical Truth',
            'summary': '记录已经进入 FlowMind 的承诺真值域，可作为下游查询基准。',
            'sections': [
                {'title': 'Truth Record', 'items': _detail_items_from_mapping({
                    'Candidate ID': record.get('id'),
                    'Status': status,
                    'Confirmed At': decision.get('confirmedAt'),
                })},
            ],
        },
        'review': {
            'title': 'Review Sessions',
            'summary': '被驳回或仍需治理处理的记录会继续留在评审闭环中。',
            'sections': [
                {'title': 'Review Context', 'items': _detail_items_from_mapping({
                    'Session Status': session.get('status'),
                    'Decisions Made': session.get('decisionsMade'),
                    'Feedback Events': session.get('feedbackEventsReceived'),
                })},
            ],
        },
        'provenance': {
            'title': 'Provenance',
            'summary': '上游已经有 provenance / trace 基础设施，但当前 Hermes ingress 记录还没有暴露成 UI 可消费的逐步节点和边。',
            'sections': [
                {'title': 'Known Facts', 'items': _detail_items_from_mapping({
                    'Replay Mode': 'derived',
                    'Candidate ID': record.get('id'),
                    'Trace Gap': '缺少 record-level trace replay API',
                })},
            ],
        },
        'memory': {
            'title': '9-Layer Memory',
            'summary': '该产品架构图中保留了内存层位置，但当前记录接口还未提供此对象的 memory hops。',
            'sections': [],
        },
        'trust': {
            'title': 'Trust Score',
            'summary': '当前记录未暴露 trust 维度明细。',
            'sections': [
                {'title': 'Trust', 'items': _detail_items_from_mapping({
                    'Trust Score': (candidate.get('trustScore') or {}).get('total') if isinstance(candidate.get('trustScore'), dict) else None,
                })},
            ],
        },
        'sqlite': {'title': 'SQLite / PG', 'summary': '当前对象最终落库位置。', 'sections': []},
        'vector': {'title': 'Qdrant Vector', 'summary': '语义向量存储落点。', 'sections': []},
        'files': {'title': 'File System', 'summary': 'Memory substrate 文件层。', 'sections': []},
        'webui': {'title': 'Web UI', 'summary': '当前页面作为该记录的运营可视化消费面。', 'sections': []},
    }

    return {
        'recordId': record.get('id'),
        'mode': 'derived',
        'gaps': [
            '当前 FlowMind 只暴露了候选记录、会话和状态字段；还没有对 HermesAgent ingress 记录提供逐步 trace replay API。',
            '页面现在使用真实记录状态做最小回放，后续接入 record replay API 后可直接切换为真实逐步事件。',
        ],
        'steps': steps,
        'moduleDetails': module_details,
    }

# ═══════════════════════════════════════════
# Overview APIs
# ═══════════════════════════════════════════

@api.route('/overview/stats')
def overview_stats():
    now = time.time()
    if _overview_stats_cache['data'] is not None and (now - _overview_stats_cache['timestamp']) < _overview_stats_cache_ttl:
        return jsonify(_overview_stats_cache['data'])

    stats = {
        'teams': 0,
        'roles': 0,
        'memory_files': 0,
        'team_memories': 0,
        'sessions': 0,
        'active_sessions': 0,
        'messages': 0,
        'total_tokens': 0,
        'skills': 0,
        'sources': [],
    }

    combined = _db_query(
        "SELECT "
        "COUNT(*) as sessions, "
        "SUM(CASE WHEN ended_at IS NULL THEN 1 ELSE 0 END) as active, "
        "(SELECT COUNT(*) FROM messages) as messages, "
        "COALESCE(SUM(input_tokens), 0) + COALESCE(SUM(output_tokens), 0) as total_tokens, "
        "COUNT(DISTINCT source) as source_count "
        "FROM sessions"
    )
    if combined:
        row = combined[0]
        stats['sessions'] = row.get('sessions', 0) or 0
        stats['active_sessions'] = row.get('active', 0) or 0
        stats['messages'] = row.get('messages', 0) or 0
        stats['total_tokens'] = row.get('total_tokens', 0) or 0

    sources = _db_query("SELECT DISTINCT source FROM sessions WHERE source IS NOT NULL AND source != ''")
    if sources:
        stats['sources'] = [s['source'] for s in sources if s.get('source')]

    home = _get_hermes_home()

    memory_dirs = _list_dir(home, 'memory')
    stats['teams'] = len(memory_dirs)

    if stats['teams'] == 0:
        stats['teams'] = len(stats['sources'])

    memory_files = _list_files(home, 'memories', '*.md')
    stats['memory_files'] = len(memory_files)

    soul_file = _list_files(home, '', 'SOUL.md')
    if soul_file:
        stats['memory_files'] += len(soul_file)

    team_memory_files = _list_files(home, 'memory', '*.md')
    stats['team_memories'] = len(team_memory_files)

    skills_dirs = _list_dir(home, 'skills')
    stats['skills'] = len(skills_dirs)
    stats['roles'] = stats['skills']

    _overview_stats_cache['data'] = stats
    _overview_stats_cache['timestamp'] = now
    return jsonify(stats)


@api.route('/overview/teams')
def overview_teams():
    home = _get_hermes_home()
    teams = []

    memory_dirs = _list_dir(home, 'memory')
    for team_name in memory_dirs:
        md_files = _list_files(home, f'memory/{team_name}', '*.md')
        sub_dirs = _list_dir(home, f'memory/{team_name}')
        teams.append({
            'name': team_name,
            'memory_count': len(md_files),
            'role_count': len(sub_dirs),
            'path': f'memory/{team_name}',
            'type': 'team',
        })

    if not teams:
        sources = _db_query("SELECT source, COUNT(*) as cnt FROM sessions GROUP BY source")
        for src in sources:
            if src.get('source'):
                teams.append({
                    'name': src['source'],
                    'memory_count': 0,
                    'role_count': 0,
                    'path': '',
                    'session_count': src['cnt'],
                    'type': 'source',
                })

    return jsonify(teams)


@api.route('/overview/memories')
def overview_memories():
    home = _get_hermes_home()
    memories = []

    memory_files = _list_files(home, 'memories', '*.md')
    for fname in memory_files:
        content = _read_file(home / 'memories' / fname, '')
        preview = content[:100].replace('\n', ' ') if content else '(empty)'
        memories.append({
            'name': fname.replace('.md', ''),
            'path': f'memories/{fname}',
            'preview': preview,
            'size': len(content),
        })

    soul_content = _read_file(home / 'SOUL.md', '')
    if soul_content:
        memories.insert(0, {
            'name': 'SOUL',
            'path': 'SOUL.md',
            'preview': soul_content[:100].replace('\n', ' '),
            'size': len(soul_content),
        })

    return jsonify(memories)


# ═══════════════════════════════════════════
# Dashboard APIs
# ═══════════════════════════════════════════

@api.route('/dashboard/stats')
def dashboard_stats():
    result = {
        'total_sessions': 0,
        'child_sessions': 0,
        'total_messages': 0,
        'active_sessions': 0,
        'error_sessions': 0,
        'source_distribution': {},
        'total_tokens': 0,
        'total_cost': 0.0,
    }

    sessions = _db_query("SELECT COUNT(*) as cnt FROM sessions")
    if sessions:
        result['total_sessions'] = sessions[0].get('cnt', 0)

    messages = _db_query("SELECT COUNT(*) as cnt FROM messages")
    if messages:
        result['total_messages'] = messages[0].get('cnt', 0)

    child = _db_query("SELECT COUNT(*) as cnt FROM sessions WHERE parent_session_id IS NOT NULL")
    if child:
        result['child_sessions'] = child[0].get('cnt', 0)

    active = _db_query("SELECT COUNT(*) as cnt FROM sessions WHERE ended_at IS NULL")
    if active:
        result['active_sessions'] = active[0].get('cnt', 0)

    errors = _db_query("SELECT COUNT(*) as cnt FROM sessions WHERE end_reason = 'error'")
    if errors:
        result['error_sessions'] = errors[0].get('cnt', 0)

    src_dist = _db_query("SELECT source, COUNT(*) as cnt FROM sessions GROUP BY source")
    for row in src_dist:
        if row.get('source'):
            result['source_distribution'][row['source']] = row['cnt']

    tokens = _db_query(
        "SELECT COALESCE(SUM(input_tokens), 0) as inp, COALESCE(SUM(output_tokens), 0) as outp, "
        "COALESCE(SUM(estimated_cost_usd), 0) as cost FROM sessions"
    )
    if tokens:
        result['total_tokens'] = (tokens[0].get('inp', 0) or 0) + (tokens[0].get('outp', 0) or 0)
        result['total_cost'] = tokens[0].get('cost', 0) or 0

    return jsonify(result)


@api.route('/dashboard/sessions')
def dashboard_sessions():
    source = request.args.get('source', None)
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    cache_key = f"dash_sess_{source}_{limit}_{offset}"
    now = time.time()
    if (_dashboard_cache.get('data') and
            _dashboard_cache.get('key') == cache_key and
            (now - _dashboard_cache['timestamp']) < _dashboard_cache_ttl):
        return jsonify(_dashboard_cache['data'])

    params = []
    where = ""
    if source:
        where = "WHERE source = ?"
        params.append(source)

    rows = _db_query(
        f"SELECT id, source, model, started_at, ended_at, end_reason, title, "
        f"message_count, tool_call_count, input_tokens, output_tokens, "
        f"estimated_cost_usd, parent_session_id, user_id "
        f"FROM sessions {where} ORDER BY started_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    )

    for row in rows:
        if row.get('started_at'):
            row['started_at_iso'] = datetime.fromtimestamp(row['started_at'], tz=timezone.utc).isoformat()
        if row.get('ended_at'):
            row['ended_at_iso'] = datetime.fromtimestamp(row['ended_at'], tz=timezone.utc).isoformat()
        first_msg = _db_query(
            "SELECT substr(content, 1, 200) as preview FROM messages "
            "WHERE session_id = ? AND role = 'user' ORDER BY timestamp ASC LIMIT 1",
            (row.get('id', ''),)
        )
        row['preview'] = first_msg[0].get('preview', '') if first_msg else ''

    _dashboard_cache['data'] = rows
    _dashboard_cache['key'] = cache_key
    _dashboard_cache['timestamp'] = now
    return jsonify(rows)


@api.route('/dashboard/session/<session_id>')
def dashboard_session_detail(session_id):
    sessions = _db_query(
        "SELECT id, source, model, started_at, ended_at, end_reason, title, "
        "message_count, tool_call_count, input_tokens, output_tokens, "
        "cache_read_tokens, cache_write_tokens, reasoning_tokens, "
        "estimated_cost_usd, actual_cost_usd, cost_status, billing_provider, "
        "parent_session_id, user_id "
        "FROM sessions WHERE id = ?",
        (session_id,)
    )

    if not sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = sessions[0]

    if session.get('started_at'):
        session['started_at_iso'] = datetime.fromtimestamp(session['started_at'], tz=timezone.utc).isoformat()
    if session.get('ended_at'):
        session['ended_at_iso'] = datetime.fromtimestamp(session['ended_at'], tz=timezone.utc).isoformat()

    messages = _db_query(
        "SELECT id, session_id, role, content, tool_call_id, tool_calls, tool_name, "
        "timestamp, token_count, finish_reason, reasoning "
        "FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )

    for msg in messages:
        if msg.get('timestamp'):
            msg['timestamp_iso'] = datetime.fromtimestamp(msg['timestamp'], tz=timezone.utc).isoformat()

    session['messages'] = messages
    return jsonify(session)


@api.route('/dashboard/stream')
def dashboard_stream():
    from flask import Response

    def generate():
        last_count = 0
        while True:
            sessions = _db_query(
                "SELECT COUNT(*) as cnt FROM sessions WHERE ended_at IS NULL"
            )
            active_count = sessions[0].get('cnt', 0) if sessions else 0

            recent = _db_query(
                "SELECT id, source, model, started_at, title, ended_at, end_reason "
                "FROM sessions ORDER BY started_at DESC LIMIT 1"
            )

            event_data = {
                'type': 'heartbeat',
                'active_sessions': active_count,
                'timestamp': time.time(),
            }

            if recent:
                r = recent[0]
                event_data['latest_session'] = {
                    'id': r.get('id', ''),
                    'source': r.get('source', ''),
                    'title': r.get('title', ''),
                    'ended_at': r.get('ended_at'),
                    'end_reason': r.get('end_reason', ''),
                }

                total_now = _db_query("SELECT COUNT(*) as cnt FROM sessions")
                current_total = total_now[0].get('cnt', 0) if total_now else 0
                if current_total != last_count and last_count > 0:
                    event_data['type'] = 'new_session'
                last_count = current_total

            yield f"data: {json.dumps(event_data, default=str)}\n\n"
            time.sleep(3)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@api.route('/dashboard/gateway-status')
def dashboard_gateway_status():
    home = _get_hermes_home()
    status = {
        'running': False,
        'pid': None,
        'gateway_state': 'unknown',
        'platforms': {},
        'active_agents': 0,
    }

    pid_data = _read_json(home / 'gateway.pid') if not _is_remote_mode() else _fetch_remote_json('gateway.pid')
    if pid_data:
        status['pid'] = pid_data.get('pid')
        if not _is_remote_mode():
            try:
                os.kill(pid_data['pid'], 0)
                status['running'] = True
            except (OSError, KeyError, ProcessLookupError):
                status['running'] = False
        else:
            status['running'] = True

    state_data = _read_json(home / 'gateway_state.json') if not _is_remote_mode() else _fetch_remote_json('gateway_state.json')
    if state_data:
        status['gateway_state'] = state_data.get('gateway_state', 'unknown')
        status['platforms'] = state_data.get('platforms', {})
        status['active_agents'] = state_data.get('active_agents', 0)
        if state_data.get('gateway_state') == 'running':
            status['running'] = True

    return jsonify(status)


# ═══════════════════════════════════════════
# CrazyAgents runtime / handoff APIs
# ═══════════════════════════════════════════

@api.route('/runtime/state')
def runtime_state():
    repo_root = _get_repo_root()
    state_path = repo_root / '.omx' / 'crazyagents' / 'runtime-state.json'
    data = _read_optional_json(state_path)
    if not data:
        return jsonify({
            'exists': False,
            'path': str(state_path),
            'data': {},
        })
    return jsonify({
        'exists': True,
        'path': str(state_path),
        'data': data,
    })


def _resolve_handoff_replay(record_id):
    """Resolve a Bitable recordId to a FlowMind replay payload.

    Returns (replay_dict, resolution_source) or (None, None).
    resolution_source is one of: 'operator_replay', 'candidate_trace', 'bitable_mapped'
    """
    # Path 1: Already a FlowMind UUID → try operator replay directly
    if record_id and '-' in record_id and not record_id.startswith('rec'):
        replay = _safe_flowmind_request(
            f'/api/operator/records/{record_id}/replay',
            default=None,
        )
        if isinstance(replay, dict) and replay.get('moduleDetails'):
            return replay, 'operator_replay'

    # Path 2: Bitable recordId → fetch candidateId from cache or Bitable
    candidate_id = None
    try:
        # Try local cache first (updated by cron: refresh-bitable-cache.sh)
        import json as _json
        cache_path = os.path.join(os.path.dirname(__file__), 'bitable_candidate_cache.json')
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                cache = _json.load(f)
            candidate_id = cache.get('mapping', {}).get(record_id)
        if not candidate_id:
            # Fallback: query Bitable directly via lark-cli
            import subprocess as _sp
            app_token = os.environ.get('BITABLE_APP_TOKEN', 'EpeXbhpF9a0s0wsh6axce9PknFg')
            main_table = os.environ.get('BITABLE_MAIN_TABLE', 'tblJRMmjbyKEDZY1')
            params = _json.dumps({'page_size': 200})
            cmd = [
                '/usr/local/bin/lark-cli', 'api', 'GET',
                f'/open-apis/bitable/v1/apps/{app_token}/tables/{main_table}/records',
                '--params', params,
            ]
            r = _sp.run(cmd, capture_output=True, text=True, timeout=15, env={**os.environ, 'HOME': os.path.expanduser('~')})
            raw = (r.stdout + r.stderr).strip()
            if raw:
                data = _json.loads(raw) if raw else {}
                for item in data.get('data', {}).get('items', []):
                    if item.get('record_id') == record_id:
                        fields = item.get('fields', {})
                        cid = fields.get('flowmind_candidate_id')
                        if isinstance(cid, list) and len(cid) > 0:
                            cid = cid[0].get('text', '')
                        candidate_id = str(cid).strip() if cid else None
                        break
    except Exception as e:
        import sys as _sys
        print(f'[handoff] Bitable resolution error for {record_id}: {e}', file=_sys.stderr, flush=True)

    if not candidate_id:
        # Path 3: Try direct operator replay with record_id as-is (last resort)
        replay = _safe_flowmind_request(
            f'/api/operator/records/{record_id}/replay',
            default=None,
        )
        return (replay, 'operator_replay') if isinstance(replay, dict) else (None, None)

    # Fetch candidate detail + trace and build synthetic replay
    candidate = _safe_flowmind_request(
        f'/api/candidates/{candidate_id}',
        default=None,
    )
    trace = _safe_flowmind_request(
        f'/api/bridge/trace/{candidate_id}',
        default=None,
    )

    if not isinstance(candidate, dict) or not candidate.get('success'):
        return None, None

    cand_data = candidate.get('data', candidate)
    trace_data = trace.get('data', trace) if isinstance(trace, dict) else {}
    trace_events = trace_data.get('traceEvents', []) if isinstance(trace_data, dict) else []

    # Build synthetic replay with moduleDetails.handoff
    truth_status = cand_data.get('status', '')  # candidate status IS truth status
    decision = cand_data.get('decisionMetadata', {}) or {}
    source_ctx = cand_data.get('sourceContext', {}) or {}

    synthetic_replay = {
        'mode': 'derived',
        'gaps': [
            'Replay synthesized from candidate + trace data (operator record not yet linked).',
            'Upstream operator replay endpoint returned Record not found for Bitable recordId.',
        ],
        'steps': trace_events if trace_events else [
            {'moduleId': 'candidate', 'label': 'Candidate created',
             'detail': cand_data.get('title', ''), 'timestamp': cand_data.get('createdAt', ''),
             'kind': 'derived'},
        ],
        'moduleDetails': {
            'handoff': {
                'title': 'Synthetic Handoff (Candidate-based)',
                'summary': f'Built from candidate {candidate_id} + bridge trace.',
                'sections': [
                    {
                        'title': 'Semantic Core',
                        'items': [
                            {'label': 'Candidate Status', 'value': truth_status},
                            {'label': 'Truth Status', 'value': truth_status},
                            {'label': 'Semantic Refs', 'value': 'flowmind.candidate, flowmind.truth_commitment'},
                        ],
                    },
                    {
                        'title': 'Trace Summary',
                        'items': [
                            {'label': 'Trace Events', 'value': str(len(trace_events))},
                            {'label': 'Latest Trace Action', 'value': trace_events[-1].get('action', '') if trace_events else 'create'},
                            {'label': 'Latest Trace Summary', 'value': trace_events[-1].get('summary', '') if trace_events else cand_data.get('title', '')},
                        ],
                    },
                    {
                        'title': 'Context Summary',
                        'items': [
                            {'label': 'Consumer Hints', 'value': 'Synthesized from candidate bridge. Full operator replay pending record linkage.'},
                        ],
                    },
                ],
            }
        },
        'semanticContext': trace_data.get('semanticContext', {}),
    }

    return synthetic_replay, 'bitable_mapped'


@api.route('/runtime/handoffs')
def runtime_handoffs():
    record_id = (request.args.get('recordId') or '').strip()
    if record_id:
        replay, resolution_source = _resolve_handoff_replay(record_id)
        if isinstance(replay, dict):
            result = _normalize_runtime_handoff_summary(record_id, replay)
            if isinstance(result, dict):
                result['resolutionSource'] = resolution_source
            return jsonify(result)
        return jsonify({
            'recordId': record_id,
            'source': 'flowmind_unavailable',
            'mode': '',
            'title': 'Handoff Summary',
            'summary': '',
            'sections': [],
            'fieldMap': {},
            'traceEventCount': 0,
            'latestTraceAction': None,
            'latestTraceSummary': None,
            'consumerHints': None,
            'missingFields': [
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
            ],
            'gaps': ['FlowMind replay upstream unavailable for the provided recordId.'],
        }), 502

    repo_root = _get_repo_root()
    outbox = repo_root / '.omx' / 'crazyagents' / 'outbox'
    if not outbox.exists():
        return jsonify([])

    items = []
    for path in sorted(outbox.glob('*.md'), reverse=True):
        try:
            content = path.read_text(encoding='utf-8')
        except FileNotFoundError:
            continue
        items.append({
            'name': path.name,
            'path': str(path),
            'updated_at': datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
            'preview': content[:300],
            'size': len(content),
        })
    return jsonify(items[:20])


@api.route('/runtime/harness-summary')
def runtime_harness_summary():
    repo_root = _get_repo_root()
    success_dir = repo_root / 'harness' / 'trace' / 'successes'
    failure_dir = repo_root / 'harness' / 'trace' / 'failures'
    summary = {
        'success_count': 0,
        'failure_count': 0,
        'latest_success': None,
        'latest_failure': None,
    }

    success_files = sorted(
        [p for p in success_dir.glob('*.json') if p.name != 'TEMPLATE.json'],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if success_dir.exists() else []
    failure_files = sorted(
        [p for p in failure_dir.glob('*.json') if p.name != 'TEMPLATE.json'],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if failure_dir.exists() else []

    summary['success_count'] = len(success_files)
    summary['failure_count'] = len(failure_files)

    if success_files:
        summary['latest_success'] = _read_optional_json(success_files[0])
    if failure_files:
        summary['latest_failure'] = _read_optional_json(failure_files[0])

    return jsonify(summary)

@api.route('/flowmind/records')
def flowmind_records():
    limit = int(request.args.get('limit', 80))
    source_agent = request.args.get('sourceAgent', _get_flowmind_source_agent())
    upstream = _safe_flowmind_request(
        '/api/operator/records',
        query={'limit': max(1, min(limit, 200)), 'sourceAgent': source_agent},
        default=None,
    )
    if isinstance(upstream, dict) and isinstance(upstream.get('records'), list):
        return jsonify(upstream)

    records = _flowmind_records(limit=max(1, min(limit, 200)), source_agent=source_agent)
    safe_records = []
    for record in records:
        safe_records.append({
            'id': record.get('id'),
            'title': record.get('title'),
            'status': record.get('status'),
            'sourceAgent': record.get('sourceAgent'),
            'instanceId': record.get('instanceId'),
            'sessionId': record.get('sessionId'),
            'confidence': record.get('confidence'),
            'createdAt': record.get('createdAt'),
            'updatedAt': record.get('updatedAt'),
            'rawText': record.get('rawText'),
            'replayMode': record.get('replayMode', 'derived'),
        })
    return jsonify({
        'records': safe_records,
        'sourceAgent': source_agent,
        'upstream': _get_flowmind_base_url(),
    })


@api.route('/flowmind/records/<record_id>/replay')
def flowmind_record_replay(record_id):
    source_agent = request.args.get('sourceAgent', _get_flowmind_source_agent())
    upstream = _safe_flowmind_request(
        f'/api/operator/records/{record_id}/replay',
        default=None,
    )
    if isinstance(upstream, dict) and upstream.get('record', {}).get('id') == record_id:
        return jsonify(upstream)

    record = _find_flowmind_record(record_id, source_agent=source_agent)
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    trace_nodes_resp = _safe_flowmind_request(
        f'/api/trace/query/proposal/{record_id}',
        default={'nodes': []},
    ) or {'nodes': []}
    trace_nodes = trace_nodes_resp.get('nodes', [])

    if trace_nodes:
        trace_nodes = sorted(trace_nodes, key=lambda node: node.get('createdAt') or '')
        steps = []
        module_details = {}
        mapping = {
            'candidate': 'inbox',
            'review_session': 'review',
            'review_finding': 'review',
            'provenance_event': 'provenance',
            'governance_decision': 'writegate',
            'commitment': 'truth',
            'session_memory': 'memory',
        }
        for node in trace_nodes:
            module_id = mapping.get(node.get('nodeType'), 'provenance')
            steps.append({
                'key': node.get('nodeId'),
                'moduleId': module_id,
                'label': _node_label(module_id),
                'detail': node.get('label') or node.get('traceRef') or module_id,
                'timestamp': node.get('createdAt'),
                'kind': 'trace',
            })
            module_details[module_id] = {
                'title': _node_label(module_id),
                'summary': '该模块细节来自 FlowMind trace graph 的真实节点。',
                'sections': [
                    {'title': 'Trace Node', 'items': _detail_items_from_mapping({
                        'Node ID': node.get('nodeId'),
                        'Node Type': node.get('nodeType'),
                        'Label': node.get('label'),
                        'Trace Ref': node.get('traceRef'),
                        'Created At': node.get('createdAt'),
                        'Immutable': node.get('immutable'),
                    })},
                ],
            }
        return jsonify({
            'recordId': record_id,
            'mode': 'trace',
            'gaps': [],
            'steps': steps,
            'moduleDetails': module_details,
        })

    return jsonify(_build_derived_replay(record))


@api.route('/promise-review/trace/<candidate_id>')
def promise_review_trace(candidate_id):
    upstream = _safe_flowmind_request(
        f"/api/bridge/trace/{urlparse.quote(candidate_id)}",
        default=None,
    )
    if upstream is None:
        payload = _normalize_bridge_trace(candidate_id, None)
        payload['error'] = 'FlowMind trace upstream unavailable'
        return jsonify(payload), 502

    return jsonify(_normalize_bridge_trace(candidate_id, upstream))
# ═══════════════════════════════════════════
# Cron APIs
# ═══════════════════════════════════════════

@api.route('/cron/list')
def cron_list():
    home = _get_hermes_home()
    jobs_file = home / 'cron' / 'jobs.json'

    if _is_remote_mode():
        data = _fetch_remote_json('cron/jobs.json')
    else:
        data = _read_json(jobs_file, {'jobs': []})

    jobs = data.get('jobs', []) if isinstance(data, dict) else data

    for job in jobs:
        output_dir = home / 'cron' / 'output' / job.get('id', '')
        if not _is_remote_mode() and output_dir.exists():
            outputs = sorted(output_dir.glob('*.md'), reverse=True)
            job['output_count'] = len(outputs)
            if outputs:
                job['last_output'] = outputs[0].name
        else:
            job['output_count'] = 0

    return jsonify(jobs)


@api.route('/cron/create', methods=['POST'])
def cron_create():
    data = request.get_json()
    if not data or not data.get('prompt') or not data.get('schedule'):
        return jsonify({'error': 'prompt and schedule are required'}), 400

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
        from cron.jobs import create_job
        job = create_job(
            prompt=data['prompt'],
            schedule=data['schedule'],
            name=data.get('name'),
            repeat=data.get('repeat'),
            deliver=data.get('deliver', 'local'),
            skills=data.get('skills'),
            model=data.get('model'),
            provider=data.get('provider'),
        )
        return jsonify(job)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/cron/<job_id>/pause', methods=['POST'])
def cron_pause(job_id):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
        from cron.jobs import pause_job
        job = pause_job(job_id)
        if job:
            return jsonify(job)
        return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/cron/<job_id>/resume', methods=['POST'])
def cron_resume(job_id):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
        from cron.jobs import resume_job
        job = resume_job(job_id)
        if job:
            return jsonify(job)
        return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/cron/<job_id>/run', methods=['POST'])
def cron_run(job_id):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
        from cron.jobs import trigger_job
        job = trigger_job(job_id)
        if job:
            return jsonify(job)
        return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/cron/<job_id>', methods=['DELETE'])
def cron_delete(job_id):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
        from cron.jobs import remove_job
        success = remove_job(job_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/cron/<job_id>/output')
def cron_output(job_id):
    home = _get_hermes_home()
    output_dir = home / 'cron' / 'output' / job_id
    outputs = []

    if not _is_remote_mode() and output_dir.exists():
        for f in sorted(output_dir.glob('*.md'), reverse=True)[:20]:
            content = _read_file(f, '')
            outputs.append({
                'filename': f.name,
                'content': content[:5000],
                'size': f.stat().st_size,
                'modified': f.stat().st_mtime,
            })

    return jsonify(outputs)


# ═══════════════════════════════════════════
# Sessions APIs
# ═══════════════════════════════════════════

@api.route('/sessions/list')
def sessions_list():
    source = request.args.get('source', None)
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    params = []
    where = ""
    if source:
        where = "WHERE source = ?"
        params.append(source)

    rows = _db_query(
        f"SELECT id, source, model, started_at, ended_at, end_reason, title, "
        f"message_count, tool_call_count, input_tokens, output_tokens, "
        f"estimated_cost_usd, parent_session_id "
        f"FROM sessions {where} ORDER BY started_at DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    )

    for row in rows:
        if row.get('started_at'):
            row['started_at_iso'] = datetime.fromtimestamp(row['started_at'], tz=timezone.utc).isoformat()
        if row.get('ended_at'):
            row['ended_at_iso'] = datetime.fromtimestamp(row['ended_at'], tz=timezone.utc).isoformat()
        first_msg = _db_query(
            "SELECT substr(content, 1, 200) as preview FROM messages "
            "WHERE session_id = ? AND role = 'user' ORDER BY timestamp ASC LIMIT 1",
            (row.get('id', ''),)
        )
        row['preview'] = first_msg[0].get('preview', '') if first_msg else ''

    return jsonify(rows)


@api.route('/sessions/search')
def sessions_search():
    query = request.args.get('q', '')
    source = request.args.get('source', None)
    limit = int(request.args.get('limit', 20))

    if not query:
        return jsonify([])

    results = _db_query(
        "SELECT m.session_id, m.role, substr(m.content, 1, 300) as snippet, m.timestamp, s.source "
        "FROM messages_fts fts JOIN messages m ON fts.rowid = m.id "
        "LEFT JOIN sessions s ON m.session_id = s.id "
        "WHERE messages_fts MATCH ? "
        "ORDER BY m.timestamp DESC LIMIT ?",
        (query, limit)
    )

    return jsonify(results)


@api.route('/sessions/detail/<session_id>')
def sessions_detail(session_id):
    sessions = _db_query(
        "SELECT id, source, model, started_at, ended_at, end_reason, title, "
        "message_count, tool_call_count, input_tokens, output_tokens, "
        "cache_read_tokens, cache_write_tokens, reasoning_tokens, "
        "estimated_cost_usd, actual_cost_usd, cost_status, billing_provider, "
        "parent_session_id, user_id "
        "FROM sessions WHERE id = ?",
        (session_id,)
    )

    if not sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = sessions[0]

    if session.get('started_at'):
        session['started_at_iso'] = datetime.fromtimestamp(session['started_at'], tz=timezone.utc).isoformat()
    if session.get('ended_at'):
        session['ended_at_iso'] = datetime.fromtimestamp(session['ended_at'], tz=timezone.utc).isoformat()

    messages = _db_query(
        "SELECT id, session_id, role, content, tool_call_id, tool_calls, tool_name, "
        "timestamp, token_count, finish_reason, reasoning "
        "FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )

    for msg in messages:
        if msg.get('timestamp'):
            msg['timestamp_iso'] = datetime.fromtimestamp(msg['timestamp'], tz=timezone.utc).isoformat()

    session['messages'] = messages
    return jsonify(session)


@api.route('/sessions/tree/<session_id>')
def sessions_tree(session_id):
    rows = _db_query(
        "SELECT id, source, started_at, ended_at, title, message_count, tool_call_count, "
        "input_tokens, output_tokens, parent_session_id, end_reason "
        "FROM sessions WHERE id = ? OR parent_session_id = ?",
        (session_id, session_id)
    )
    return jsonify(rows)


@api.route('/sessions/stats')
def sessions_stats():
    return dashboard_stats()


# ═══════════════════════════════════════════
# Memory APIs
# ═══════════════════════════════════════════

@api.route('/memory/teams')
def memory_teams():
    return overview_teams()


@api.route('/memory/team/<path:team_name>')
def memory_team_detail(team_name):
    home = _get_hermes_home()
    files = []

    if _is_remote_mode():
        cfg = _get_remote_config()
        hermes_home = cfg.get('hermes_home', '/root/.hermes')
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(cfg['host'], username=cfg.get('user', 'root'), password=cfg.get('password', ''), timeout=30)
            cmd = f"find '{hermes_home}/memory/{team_name}' -name '*.md' -type f 2>/dev/null | sort"
            stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
            file_list = [f.strip() for f in stdout.read().decode('utf-8', errors='replace').strip().split('\n') if f.strip()]

            for fpath in file_list:
                fname = fpath.split('/')[-1]
                stdin2, stdout2, stderr2 = client.exec_command(f"cat '{fpath}' 2>/dev/null", timeout=15)
                content = stdout2.read().decode('utf-8', errors='replace')
                files.append({
                    'name': fname.replace('.md', ''),
                    'path': fpath.replace(f'{hermes_home}/memory/', ''),
                    'content': content,
                    'size': len(content),
                })
            client.close()
        except Exception:
            pass
    else:
        team_dir = home / 'memory' / team_name
        if team_dir.exists():
            for f in sorted(team_dir.rglob('*.md')):
                content = _read_file(f, '')
                files.append({
                    'name': f.stem,
                    'path': str(f.relative_to(team_dir)),
                    'content': content,
                    'size': len(content),
                })

    return jsonify({'team': team_name, 'files': files})


@api.route('/memory/file/<path:file_path>')
def memory_file_detail(file_path):
    home = _get_hermes_home()
    content = _read_file(home / 'memory' / file_path, '')
    if not content:
        return jsonify({'error': 'File not found'}), 404
    return jsonify({
        'path': file_path,
        'content': content,
        'size': len(content),
    })


@api.route('/memory/update', methods=['PUT'])
def memory_update():
    data = request.get_json()
    if not data or not data.get('path') or data.get('content') is None:
        return jsonify({'error': 'path and content are required'}), 400

    home = _get_hermes_home()
    full_path = home / 'memory' / data['path']

    if _is_remote_mode():
        return jsonify({'error': 'Remote mode does not support file editing'}), 400

    if not full_path.exists():
        return jsonify({'error': 'File not found'}), 404

    try:
        import shutil
        backup_path = full_path.with_suffix('.md.bak')
        if full_path.exists():
            shutil.copy2(full_path, backup_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(data['content'])
        return jsonify({'success': True, 'backup': str(backup_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════
# Skills APIs
# ═══════════════════════════════════════════

CATEGORY_DISPLAY_NAMES = {
    'academic': '学术', 'apple': 'Apple 生态', 'autonomous-ai-agents': '自主AI代理',
    'blender': 'Blender', 'creative': '创意', 'data-science': '数据科学',
    'design': '设计', 'devops': 'DevOps', 'diagramming': '图表',
    'dogfood': '内部工具', 'domain': '领域', 'email': '邮件',
    'engineering': '工程', 'feeds': '信息源', 'finance': '金融',
    'game-development': '游戏开发', 'gaming': '游戏', 'gifs': 'GIF',
    'github': 'GitHub', 'godot': 'Godot', 'hr': '人力资源',
    'inference-sh': '推理服务', 'legal': '法律', 'leisure': '休闲',
    'marketing': '营销', 'mcp': 'MCP', 'media': '媒体',
    'mlops': 'MLOps', 'note-taking': '笔记', 'paid-media': '付费媒体',
    'product': '产品', 'productivity': '生产力', 'project-management': '项目管理',
    'red-teaming': '红队测试', 'research': '研究', 'roblox-studio': 'Roblox',
    'sales': '销售', 'smart-home': '智能家居', 'social-media': '社交媒体',
    'software-development': '软件开发', 'spatial-computing': '空间计算',
    'specialized': '专业领域', 'supply-chain': '供应链', 'support': '技术支持',
    'testing': '测试', 'unity': 'Unity', 'unreal-engine': 'Unreal Engine',
}


def _parse_skill_md(content):
    desc = ''
    for line in content.split('\n')[:10]:
        if line.startswith('# '):
            desc = line[2:].strip()
            break
    if not desc:
        desc = content[:120].replace('\n', ' ').strip()
    return desc


def _scan_local_skills(skills_dir):
    skills = []
    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue
        category_name = category_dir.name
        display_name = CATEGORY_DISPLAY_NAMES.get(category_name, category_name)

        sub_dirs = [d for d in category_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if sub_dirs:
            for skill_dir in sorted(sub_dirs):
                description = ''
                skill_md = skill_dir / 'SKILL.md'
                config_yaml = skill_dir / 'config.yaml'
                if skill_md.exists():
                    description = _parse_skill_md(_read_file(skill_md, ''))
                elif config_yaml.exists():
                    for line in _read_file(config_yaml, '').split('\n'):
                        if line.startswith('description:'):
                            description = line.split(':', 1)[1].strip().strip('"\'')
                            break
                if not description:
                    description = skill_dir.name.replace('-', ' ').replace('_', ' ')

                skills.append({
                    'name': skill_dir.name,
                    'category': category_name,
                    'category_display': display_name,
                    'description': description,
                    'path': str(skill_dir),
                    'has_config': (skill_dir / 'SKILL.md').exists() or (skill_dir / 'config.yaml').exists(),
                })
        else:
            description = ''
            skill_md = category_dir / 'SKILL.md'
            config_yaml = category_dir / 'config.yaml'
            if skill_md.exists():
                description = _parse_skill_md(_read_file(skill_md, ''))
            elif config_yaml.exists():
                for line in _read_file(config_yaml, '').split('\n'):
                    if line.startswith('description:'):
                        description = line.split(':', 1)[1].strip().strip('"\'')
                        break
            if not description:
                description = category_name.replace('-', ' ').replace('_', ' ')

            skills.append({
                'name': category_name,
                'category': category_name,
                'category_display': display_name,
                'description': description,
                'path': str(category_dir),
                'has_config': skill_md.exists() or config_yaml.exists(),
            })
    return skills


def _scan_remote_skills(cfg):
    skills = []
    hermes_home = cfg.get('hermes_home', '/root/.hermes')
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(cfg['host'], username=cfg.get('user', 'root'), password=cfg.get('password', ''), timeout=30)

        cmd = f"ls -1 '{hermes_home}/skills/' 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
        top_dirs = [d.strip() for d in stdout.read().decode('utf-8', errors='replace').strip().split('\n') if d.strip()]

        for category_name in top_dirs:
            display_name = CATEGORY_DISPLAY_NAMES.get(category_name, category_name)

            list_cmd = f"ls -1 '{hermes_home}/skills/{category_name}/' 2>/dev/null"
            stdin2, stdout2, stderr2 = client.exec_command(list_cmd, timeout=10)
            items = [i.strip() for i in stdout2.read().decode('utf-8', errors='replace').strip().split('\n') if i.strip()]

            sub_dirs = []
            for item in items:
                check_cmd = f"test -d '{hermes_home}/skills/{category_name}/{item}' && echo DIR || echo FILE"
                stdin3, stdout3, stderr3 = client.exec_command(check_cmd, timeout=5)
                if stdout3.read().decode().strip() == 'DIR':
                    sub_dirs.append(item)

            if sub_dirs:
                for skill_name in sub_dirs:
                    description = ''
                    md_cmd = f"cat '{hermes_home}/skills/{category_name}/{skill_name}/SKILL.md' 2>/dev/null | head -10"
                    stdin4, stdout4, stderr4 = client.exec_command(md_cmd, timeout=10)
                    md_content = stdout4.read().decode('utf-8', errors='replace').strip()
                    if md_content:
                        description = _parse_skill_md(md_content)
                    if not description:
                        description = skill_name.replace('-', ' ').replace('_', ' ')

                    skills.append({
                        'name': skill_name,
                        'category': category_name,
                        'category_display': display_name,
                        'description': description,
                        'path': f'{hermes_home}/skills/{category_name}/{skill_name}',
                        'has_config': bool(md_content),
                    })
            else:
                description = ''
                md_cmd = f"cat '{hermes_home}/skills/{category_name}/SKILL.md' 2>/dev/null | head -10"
                stdin4, stdout4, stderr4 = client.exec_command(md_cmd, timeout=10)
                md_content = stdout4.read().decode('utf-8', errors='replace').strip()
                if md_content:
                    description = _parse_skill_md(md_content)
                if not description:
                    description = category_name.replace('-', ' ').replace('_', ' ')

                skills.append({
                    'name': category_name,
                    'category': category_name,
                    'category_display': display_name,
                    'description': description,
                    'path': f'{hermes_home}/skills/{category_name}',
                    'has_config': bool(md_content),
                })

        client.close()
    except Exception:
        pass
    return skills


@api.route('/skills/list')
def skills_list():
    now = time.time()
    if _skills_cache['data'] is not None and (now - _skills_cache['timestamp']) < _skills_cache_ttl:
        return jsonify(_skills_cache['data'])

    if _is_remote_mode():
        skills = _scan_remote_skills(_get_remote_config())
    else:
        home = _get_hermes_home()
        skills_dir = home / 'skills'
        if skills_dir.exists():
            skills = _scan_local_skills(skills_dir)
        else:
            skills = []

    categories = {}
    for s in skills:
        cat = s.get('category', 'other')
        if cat not in categories:
            categories[cat] = {'name': cat, 'display': s.get('category_display', cat), 'count': 0}
        categories[cat]['count'] += 1

    result = {
        'skills': skills,
        'total': len(skills),
        'categories': sorted(categories.values(), key=lambda x: -x['count']),
    }
    _skills_cache['data'] = result
    _skills_cache['timestamp'] = now
    return jsonify(result)


@api.route('/skills/detail/<path:skill_path>')
def skills_detail(skill_path):
    home = _get_hermes_home()

    if _is_remote_mode():
        cfg = _get_remote_config()
        hermes_home = cfg.get('hermes_home', '/root/.hermes')
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(cfg['host'], username=cfg.get('user', 'root'), password=cfg.get('password', ''), timeout=30)

            full_path = f'{hermes_home}/skills/{skill_path}'
            md_cmd = f"cat '{full_path}/SKILL.md' 2>/dev/null"
            stdin, stdout, stderr = client.exec_command(md_cmd, timeout=10)
            content = stdout.read().decode('utf-8', errors='replace').strip()

            if not content:
                alt_path = f'{hermes_home}/skills/{skill_path.split("/")[-1]}'
                md_cmd2 = f"cat '{alt_path}/SKILL.md' 2>/dev/null"
                stdin2, stdout2, stderr2 = client.exec_command(md_cmd2, timeout=10)
                content = stdout2.read().decode('utf-8', errors='replace').strip()

            client.close()

            if not content:
                return jsonify({'error': 'Skill not found'}), 404

            return jsonify({
                'name': skill_path.split('/')[-1],
                'content': content,
                'size': len(content),
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        skill_full = home / 'skills' / skill_path
        content = _read_file(skill_full / 'SKILL.md', '')
        if not content:
            content = _read_file(home / 'skills' / skill_path.split('/')[-1] / 'SKILL.md', '')
        if not content:
            return jsonify({'error': 'Skill not found'}), 404
        return jsonify({
            'name': skill_path.split('/')[-1],
            'content': content,
            'size': len(content),
        })


# ═══════════════════════════════════════════
# Alerts APIs
# ═══════════════════════════════════════════

@api.route('/alerts/list')
def alerts_list():
    alerts = []

    if _is_remote_mode():
        state_data = _fetch_remote_json('gateway_state.json')
    else:
        home = _get_hermes_home()
        state_data = _read_json(home / 'gateway_state.json')

    if state_data:
        platforms = state_data.get('platforms', {})
        for platform_name, platform_state in platforms.items():
            p_state = platform_state.get('state', 'unknown')
            if p_state in ('error', 'fatal'):
                alerts.append({
                    'level': 'critical',
                    'source': platform_name,
                    'message': f'{platform_name} 连接错误: {platform_state.get("error_message", "未知错误")}',
                    'time': platform_state.get('updated_at', ''),
                    'error_code': platform_state.get('error_code'),
                })
            elif p_state in ('disconnected', 'stopped'):
                alerts.append({
                    'level': 'warning',
                    'source': platform_name,
                    'message': f'{platform_name} 已断开连接',
                    'time': platform_state.get('updated_at', ''),
                })
            elif p_state == 'connected':
                alerts.append({
                    'level': 'info',
                    'source': platform_name,
                    'message': f'{platform_name} 正常运行',
                    'time': platform_state.get('updated_at', ''),
                })

        gw_state = state_data.get('gateway_state', '')
        if gw_state == 'stopped':
            alerts.append({
                'level': 'critical',
                'source': 'gateway',
                'message': 'Gateway 进程已停止',
                'time': state_data.get('updated_at', ''),
            })
        elif gw_state == 'running':
            alerts.append({
                'level': 'info',
                'source': 'gateway',
                'message': f'Gateway 正常运行 (PID: {state_data.get("pid", "N/A")})',
                'time': state_data.get('updated_at', ''),
            })

    return jsonify(alerts)


@api.route('/alerts/platform-status')
def alerts_platform_status():
    return dashboard_gateway_status()


# ═══════════════════════════════════════════
# Tokens APIs
# ═══════════════════════════════════════════

@api.route('/tokens/stats')
def tokens_stats():
    result = {
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'total_cost_usd': 0.0,
        'session_count': 0,
        'budget_usd': None,
        'active_days': 0,
        'by_provider': {},
        'by_source': {},
        'daily_trend': [],
    }

    totals = _db_query(
        "SELECT COALESCE(SUM(input_tokens), 0) as inp, COALESCE(SUM(output_tokens), 0) as outp, "
        "COALESCE(SUM(estimated_cost_usd), 0) as cost, COUNT(*) as cnt FROM sessions"
    )
    if totals:
        result['total_input_tokens'] = totals[0].get('inp', 0) or 0
        result['total_output_tokens'] = totals[0].get('outp', 0) or 0
        result['total_cost_usd'] = round(totals[0].get('cost', 0) or 0, 2)
        result['session_count'] = totals[0].get('cnt', 0) or 0

    active_days = _db_query(
        "SELECT COUNT(DISTINCT date(started_at, 'unixepoch')) as days FROM sessions WHERE started_at IS NOT NULL"
    )
    if active_days:
        result['active_days'] = active_days[0].get('days', 0) or 0

    home = _get_hermes_home()
    try:
        config_content = _read_file(home / 'config.yaml', '')
        if config_content:
            for line in config_content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('monthly_budget:') or stripped.startswith('budget:'):
                    try:
                        budget_val = float(stripped.split(':', 1)[1].strip().strip('"\''))
                        result['budget_usd'] = budget_val
                    except (ValueError, IndexError):
                        pass
                    break
    except Exception:
        pass

    by_provider = _db_query(
        "SELECT billing_provider, SUM(input_tokens) as inp, SUM(output_tokens) as outp, "
        "SUM(estimated_cost_usd) as cost FROM sessions "
        "WHERE billing_provider IS NOT NULL GROUP BY billing_provider"
    )
    for row in by_provider:
        if row.get('billing_provider'):
            result['by_provider'][row['billing_provider']] = {
                'input_tokens': row['inp'] or 0,
                'output_tokens': row['outp'] or 0,
                'cost_usd': round(row['cost'] or 0, 2),
            }

    by_source = _db_query(
        "SELECT source, SUM(input_tokens) as inp, SUM(output_tokens) as outp, "
        "SUM(estimated_cost_usd) as cost FROM sessions GROUP BY source"
    )
    for row in by_source:
        if row.get('source'):
            result['by_source'][row['source']] = {
                'input_tokens': row['inp'] or 0,
                'output_tokens': row['outp'] or 0,
                'cost_usd': round(row['cost'] or 0, 2),
            }

    daily = _db_query(
        "SELECT date(started_at, 'unixepoch') as day, "
        "COALESCE(SUM(input_tokens), 0) as inp, COALESCE(SUM(output_tokens), 0) as outp, "
        "COALESCE(SUM(estimated_cost_usd), 0) as cost, COUNT(*) as cnt "
        "FROM sessions WHERE started_at IS NOT NULL GROUP BY day ORDER BY day DESC LIMIT 30"
    )
    for row in daily:
        result['daily_trend'].append({
            'date': row.get('day', ''),
            'input_tokens': row.get('inp', 0) or 0,
            'output_tokens': row.get('outp', 0) or 0,
            'cost_usd': round(row.get('cost', 0) or 0, 2),
            'sessions': row.get('cnt', 0) or 0,
        })

    return jsonify(result)


@api.route('/tokens/recent')
def tokens_recent():
    limit = int(request.args.get('limit', 20))

    rows = _db_query(
        "SELECT id, source, title, started_at, ended_at, "
        "input_tokens, output_tokens, estimated_cost_usd, billing_provider, "
        "message_count, tool_call_count "
        "FROM sessions ORDER BY started_at DESC LIMIT ?",
        (limit,)
    )

    results = []
    for row in rows:
        results.append({
            'session_id': row.get('id', ''),
            'source': row.get('source', ''),
            'title': row.get('title') or '(untitled)',
            'started_at': row.get('started_at'),
            'ended_at': row.get('ended_at'),
            'input_tokens': row.get('input_tokens', 0) or 0,
            'output_tokens': row.get('output_tokens', 0) or 0,
            'cost_usd': round(row.get('estimated_cost_usd', 0) or 0, 4),
            'provider': row.get('billing_provider') or 'unknown',
            'message_count': row.get('message_count', 0) or 0,
            'tool_call_count': row.get('tool_call_count', 0) or 0,
        })

    return jsonify(results)


# ═══════════════════════════════════════════
# Agents APIs
# ═══════════════════════════════════════════

@api.route('/agents/list')
def agents_list():
    sources = _db_query(
        "SELECT source, COUNT(*) as session_count, "
        "COALESCE(SUM(input_tokens), 0) as input_tokens, "
        "COALESCE(SUM(output_tokens), 0) as output_tokens, "
        "COALESCE(SUM(message_count), 0) as total_messages, "
        "COALESCE(SUM(tool_call_count), 0) as total_tool_calls, "
        "COALESCE(SUM(estimated_cost_usd), 0) as total_cost "
        "FROM sessions GROUP BY source"
    )

    agents = []
    agent_meta = {
        'cli': {'name': 'CLI 智能体', 'icon': '🖥️', 'gradient': '#667eea,#764ba2', 'description': '命令行交互智能体，处理终端操作、代码编写和系统管理任务'},
        'feishu': {'name': '飞书智能体', 'icon': '🐦', 'gradient': '#06b6d4,#3b82f6', 'description': '飞书平台交互智能体，处理消息推送、审批流程和团队协作'},
        'telegram': {'name': 'Telegram 智能体', 'icon': '📱', 'gradient': '#f59e0b,#ef4444', 'description': 'Telegram 平台交互智能体，处理即时通讯和通知推送'},
        'discord': {'name': 'Discord 智能体', 'icon': '💬', 'gradient': '#8b5cf6,#7c3aed', 'description': 'Discord 平台交互智能体，处理社区管理和内容审核'},
        'api_server': {'name': 'API 服务智能体', 'icon': '🔌', 'gradient': '#10b981,#059669', 'description': 'REST API 服务智能体，提供 OpenAI 兼容接口服务'},
        'cron': {'name': '定时任务智能体', 'icon': '⏰', 'gradient': '#f97316,#ea580c', 'description': '定时任务调度智能体，执行周期性自动化任务'},
        'acp': {'name': '编辑器智能体', 'icon': '📝', 'gradient': '#ec4899,#db2777', 'description': '编辑器集成智能体，支持 VS Code/Zed/JetBrains'},
    }

    for src in sources:
        source = src.get('source', '')
        meta = agent_meta.get(source, {
            'name': f'{source} 智能体',
            'icon': '🤖',
            'gradient': '#64748b,#475569',
            'description': f'{source} 平台交互智能体',
        })

        total_tokens = (src.get('input_tokens', 0) or 0) + (src.get('output_tokens', 0) or 0)
        success_rate = 100.0
        if src.get('session_count', 0) > 0:
            ended = _db_query(
                "SELECT COUNT(*) as cnt FROM sessions WHERE source = ? AND ended_at IS NOT NULL",
                (source,)
            )
            if ended:
                ended_count = ended[0].get('cnt', 0)
                success_rate = round((ended_count / src['session_count']) * 100, 1)

        agents.append({
            'source': source,
            'name': meta['name'],
            'icon': meta['icon'],
            'gradient': meta['gradient'],
            'description': meta['description'],
            'session_count': src.get('session_count', 0),
            'total_tokens': total_tokens,
            'total_messages': src.get('total_messages', 0) or 0,
            'total_tool_calls': src.get('total_tool_calls', 0) or 0,
            'total_cost': round(src.get('total_cost', 0) or 0, 4),
            'success_rate': success_rate,
        })

    gateway_status = dashboard_gateway_status()
    gw_data = json.loads(gateway_status.get_data(as_text=True))

    for platform_name, platform_state in gw_data.get('platforms', {}).items():
        existing = [a for a in agents if a['source'] == platform_name]
        if not existing:
            meta = agent_meta.get(platform_name, {
                'name': f'{platform_name} 智能体',
                'icon': '🤖',
                'gradient': '#64748b,#475569',
                'description': f'{platform_name} 平台交互智能体',
            })
            agents.append({
                'source': platform_name,
                'name': meta['name'],
                'icon': meta['icon'],
                'gradient': meta['gradient'],
                'description': meta['description'],
                'session_count': 0,
                'total_tokens': 0,
                'total_messages': 0,
                'total_tool_calls': 0,
                'total_cost': 0,
                'success_rate': 100.0,
                'platform_state': platform_state.get('state', 'unknown'),
            })
        else:
            existing[0]['platform_state'] = platform_state.get('state', 'unknown')

    return jsonify(agents)


@api.route('/agents/stats')
def agents_stats():
    return agents_list()


# ═══════════════════════════════════════════
# Graph APIs
# ═══════════════════════════════════════════

@api.route('/graph/data')
def graph_data():
    agents_resp = agents_list()
    agents_data = json.loads(agents_resp.get_data(as_text=True))

    nodes = []
    edges = []

    center_node = {
        'id': 'coordinator',
        'name': 'Hermes Gateway',
        'icon': '🎯',
        'type': 'coordinator',
        'gradient': '#667eea,#764ba2',
        'session_count': sum(a.get('session_count', 0) for a in agents_data),
    }
    nodes.append(center_node)

    for agent in agents_data:
        node = {
            'id': agent['source'],
            'name': agent['name'],
            'icon': agent['icon'],
            'type': 'agent',
            'gradient': agent['gradient'],
            'session_count': agent.get('session_count', 0),
            'platform_state': agent.get('platform_state', 'unknown'),
        }
        nodes.append(node)

        edges.append({
            'source': 'coordinator',
            'target': agent['source'],
            'type': 'coordinator',
            'label': '协调调度',
        })

    for i, agent_a in enumerate(agents_data):
        for agent_b in agents_data[i+1:]:
            shared_sessions = _db_query(
                "SELECT COUNT(*) as cnt FROM sessions s1 "
                "JOIN sessions s2 ON s1.parent_session_id = s2.id "
                "WHERE s1.source = ? AND s2.source = ?",
                (agent_a['source'], agent_b['source'])
            )
            if shared_sessions and shared_sessions[0].get('cnt', 0) > 0:
                edges.append({
                    'source': agent_a['source'],
                    'target': agent_b['source'],
                    'type': 'dataflow',
                    'label': f"数据流 ({shared_sessions[0]['cnt']})",
                })

    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'agent_nodes': len(nodes),
            'connections': len(edges),
            'total_sessions': center_node['session_count'],
        }
    })


# ═══════════════════════════════════════════
# Tasks APIs
# ═══════════════════════════════════════════

@api.route('/tasks/list')
def tasks_list():
    sessions = _db_query(
        "SELECT id, source, model, started_at, ended_at, end_reason, title, "
        "message_count, tool_call_count, input_tokens, output_tokens, "
        "parent_session_id "
        "FROM sessions ORDER BY started_at DESC LIMIT 50"
    )

    tasks = []
    for s in sessions:
        status = 'pending'
        if s.get('ended_at'):
            if s.get('end_reason') == 'error':
                status = 'failed'
            elif s.get('end_reason') == 'compression':
                status = 'completed'
            else:
                status = 'completed'
        else:
            status = 'running'

        duration = None
        if s.get('started_at'):
            end = s.get('ended_at') or time.time()
            duration = end - s['started_at']

        tasks.append({
            'id': s.get('id', ''),
            'name': s.get('title') or s.get('id', '')[:16],
            'source': s.get('source', ''),
            'status': status,
            'duration': duration,
            'started_at': s.get('started_at'),
            'ended_at': s.get('ended_at'),
            'message_count': s.get('message_count', 0) or 0,
            'tool_call_count': s.get('tool_call_count', 0) or 0,
            'parent_session_id': s.get('parent_session_id'),
            'model': s.get('model', ''),
        })

    stats = {
        'total': len(tasks),
        'running': len([t for t in tasks if t['status'] == 'running']),
        'completed': len([t for t in tasks if t['status'] == 'completed']),
        'failed': len([t for t in tasks if t['status'] == 'failed']),
        'pending': len([t for t in tasks if t['status'] == 'pending']),
    }

    return jsonify({'tasks': tasks, 'stats': stats})


# ═══════════════════════════════════════════
# Config APIs
# ═══════════════════════════════════════════

@api.route('/config')
def get_config():
    home = _get_hermes_home()
    if _is_remote_mode():
        content = ''
        cfg = _get_remote_config()
        try:
            import paramiko
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(cfg['host'], username=cfg.get('user', 'root'), password=cfg.get('password', ''), timeout=30)
            stdin, stdout, stderr = client.exec_command(f"cat '{cfg.get('hermes_home', '/root/.hermes')}/config.yaml' 2>/dev/null", timeout=15)
            content = stdout.read().decode('utf-8', errors='replace')
            client.close()
        except Exception:
            pass
    else:
        content = _read_file(home / 'config.yaml', '')

    return jsonify({'content': content, 'remote': _is_remote_mode()})


@api.route('/server/info')
def server_info():
    cfg = _get_remote_config()
    if not _is_remote_mode():
        return jsonify({'mode': 'local', 'hermes_home': str(_get_hermes_home())})

    return jsonify({
        'mode': 'remote',
        'host': cfg.get('host', ''),
        'hermes_home': cfg.get('hermes_home', '/root/.hermes'),
        'connected': True,
    })


# ═══════════════════════════════════════════
# Overview APIs (Macro-level Dashboard)
# ═══════════════════════════════════════════

@api.route('/overview')
def overview_data():
    """Aggregated overview data for the macro-level monitoring dashboard"""

    now = time.time()
    if _overview_dashboard_cache['data'] and (now - _overview_dashboard_cache['timestamp']) < _overview_dashboard_cache_ttl:
        return jsonify(_overview_dashboard_cache['data'])

    result = {
        'metrics': {
            'total_sessions': 0,
            'active_sessions': 0,
            'total_input': 0,
            'total_output': 0,
            'total_tool_calls': 0,
            'error_count': 0,
            'avg_tps': None,
        },
        'active_sessions': [],
        'tool_usage': [],
        'performance': {},
        'recent_errors': [],
        'sources': [],
        'subagents': [],
        'tool_registry': [],
    }

    # ---- Global Metrics ----
    totals = _db_query(
        "SELECT "
        "COUNT(*) as total_sessions, "
        "COUNT(CASE WHEN ended_at IS NULL THEN 1 END) as active_sessions, "
        "COALESCE(SUM(input_tokens), 0) as total_input, "
        "COALESCE(SUM(output_tokens), 0) as total_output, "
        "COALESCE(SUM(tool_call_count), 0) as total_tool_calls "
        "FROM sessions"
    )
    if totals:
        t = totals[0]
        result['metrics'].update({
            'total_sessions': t.get('total_sessions', 0) or 0,
            'active_sessions': t.get('active_sessions', 0) or 0,
            'total_input': t.get('total_input', 0) or 0,
            'total_output': t.get('total_output', 0) or 0,
            'total_tool_calls': t.get('total_tool_calls', 0) or 0,
        })

    # Error count
    errors = _db_query(
        "SELECT COUNT(DISTINCT session_id) as cnt FROM messages WHERE error_message IS NOT NULL"
    )
    if errors:
        result['metrics']['error_count'] = errors[0].get('cnt', 0) or 0

    # Average TPS
    tps_data = _db_query(
        "SELECT AVG(tps) as avg_tps FROM messages WHERE tps IS NOT NULL AND tps > 0"
    )
    if tps_data and tps_data[0].get('avg_tps'):
        result['metrics']['avg_tps'] = round(tps_data[0]['avg_tps'], 1)

    # ---- Active Sessions ----
    active = _db_query(
        "SELECT id, source, model, started_at, ended_at, end_reason, title, "
        "input_tokens, output_tokens, tool_call_count, "
        "(SELECT GROUP_CONCAT(DISTINCT tool_name) FROM messages WHERE session_id = s.id AND tool_name IS NOT NULL) as tool_names_str "
        "FROM sessions s "
        "WHERE ended_at IS NULL OR end_reason = 'error' "
        "ORDER BY started_at DESC LIMIT 12"
    )
    for row in active:
        tool_names = []
        if row.get('tool_names_str'):
            tool_names = [t.strip() for t in row['tool_names_str'].split(',') if t.strip()]
        result['active_sessions'].append({
            'id': row.get('id', ''),
            'source': row.get('source', ''),
            'model': row.get('model', ''),
            'title': row.get('title') or row.get('id', '')[:20],
            'started_at': row.get('started_at'),
            'ended_at': row.get('ended_at'),
            'end_reason': row.get('end_reason'),
            'input_tokens': row.get('input_tokens', 0) or 0,
            'output_tokens': row.get('output_tokens', 0) or 0,
            'tool_call_count': row.get('tool_call_count', 0) or 0,
            'tool_names': tool_names,
        })

    # ---- Tool Usage ----
    tool_usage = _db_query(
        "SELECT tool_name, COUNT(*) as call_count, "
        "AVG(tool_duration_ms) as avg_duration, "
        "COUNT(CASE WHEN tool_result_status = 'error' THEN 1 END) as errors, "
        "COALESCE(SUM(token_count), 0) as total_tokens "
        "FROM messages "
        "WHERE role = 'tool' AND tool_name IS NOT NULL "
        "GROUP BY tool_name "
        "ORDER BY call_count DESC LIMIT 10"
    )
    for row in tool_usage:
        result['tool_usage'].append({
            'tool_name': row.get('tool_name', ''),
            'call_count': row.get('call_count', 0) or 0,
            'avg_duration': row.get('avg_duration'),
            'errors': row.get('errors', 0) or 0,
            'total_tokens': row.get('total_tokens', 0) or 0,
        })

    # If no tool data from messages, fall back to tool_call analysis
    if not result['tool_usage']:
        tc_data = _db_query(
            "SELECT finish_reason, COUNT(*) as cnt FROM messages GROUP BY finish_reason ORDER BY cnt DESC LIMIT 10"
        )
        if tc_data:
            result['tool_usage'] = [{
                'tool_name': row.get('finish_reason', 'unknown'),
                'call_count': row.get('cnt', 0),
                'avg_duration': None,
                'errors': 0,
                'total_tokens': 0,
            } for row in tc_data]

    # ---- Performance ----
    perf_ttft = _db_query(
        "SELECT AVG(ttft_ms) as avg_ttft, MIN(ttft_ms) as min_ttft, MAX(ttft_ms) as max_ttft "
        "FROM messages WHERE ttft_ms IS NOT NULL AND ttft_ms > 0"
    )
    perf_tps = _db_query(
        "SELECT AVG(tps) as avg_tps FROM messages WHERE tps IS NOT NULL AND tps > 0"
    )
    perf_duration = _db_query(
        "SELECT AVG(CASE WHEN ended_at IS NOT NULL THEN ended_at - started_at END) as avg_duration "
        "FROM sessions"
    )

    result['performance'] = {
        'avg_ttft': perf_ttft[0].get('avg_ttft') if perf_ttft else None,
        'min_ttft': perf_ttft[0].get('min_ttft') if perf_ttft else None,
        'max_ttft': perf_ttft[0].get('max_ttft') if perf_ttft else None,
        'avg_tps': perf_tps[0].get('avg_tps') if perf_tps else None,
        'avg_duration': perf_duration[0].get('avg_duration') if perf_duration else None,
        'error_rate': result['metrics']['error_count'] / max(result['metrics']['total_sessions'], 1),
    }

    # ---- Recent Errors ----
    recent_err = _db_query(
        "SELECT m.id, m.session_id, m.role, m.error_message, m.error_traceback, "
        "m.tool_name, m.timestamp "
        "FROM messages m "
        "WHERE m.error_message IS NOT NULL "
        "ORDER BY m.timestamp DESC LIMIT 10"
    )
    for row in recent_err:
        result['recent_errors'].append({
            'id': row.get('id'),
            'session_id': row.get('session_id', ''),
            'error_message': row.get('error_message', ''),
            'tool_name': row.get('tool_name', ''),
            'timestamp': row.get('timestamp'),
        })

    # If no error data, check sessions with error end_reason
    if not result['recent_errors']:
        session_err = _db_query(
            "SELECT id, end_reason, started_at "
            "FROM sessions WHERE end_reason IS NOT NULL "
            "ORDER BY started_at DESC LIMIT 5"
        )
        for row in session_err:
            result['recent_errors'].append({
                'session_id': row.get('id', ''),
                'error_message': row.get('end_reason', ''),
                'timestamp': row.get('started_at'),
            })

    # ---- Source Distribution ----
    sources = _db_query(
        "SELECT COALESCE(source, 'unknown') as src, COUNT(*) as cnt, "
        "COALESCE(SUM(input_tokens + output_tokens), 0) as total_tokens "
        "FROM sessions GROUP BY source ORDER BY cnt DESC"
    )
    for row in sources:
        result['sources'].append({
            'src': row.get('src', ''),
            'cnt': row.get('cnt', 0) or 0,
            'total_tokens': row.get('total_tokens', 0) or 0,
        })

    # ---- Subagents ----
    roles = _db_query(
        "SELECT DISTINCT SUBSTR(role, 1, 20) as role FROM messages WHERE role != 'user'"
    )
    result['subagents'] = [{'role': r.get('role', '')} for r in (roles or []) if r.get('role')]

    # ---- Tool Registry ----
    tools = _db_query(
        "SELECT DISTINCT tool_name FROM messages WHERE tool_name IS NOT NULL LIMIT 10"
    )
    result['tool_registry'] = [{'tool_name': t.get('tool_name', '')} for t in (tools or []) if t.get('tool_name')]

    _overview_dashboard_cache['data'] = result
    _overview_dashboard_cache['timestamp'] = now
    return jsonify(result)


# ═══════════════════════════════════════════
# Operations Integrations APIs (executor façade)
# ═══════════════════════════════════════════

from executor_bridge import get_executor_provider, get_provider_mode


@api.route('/operations/integrations/sources')
def ops_integrations_sources():
    data = get_executor_provider().get_sources()
    return jsonify(data)


@api.route('/operations/integrations/tools')
def ops_integrations_tools():
    source_id = request.args.get('sourceId', '')
    data = get_executor_provider().get_tools(source_id=source_id)
    return jsonify(data)


@api.route('/operations/integrations/credentials')
def ops_integrations_credentials():
    data = get_executor_provider().get_credentials()
    return jsonify(data)


@api.route('/operations/integrations/providers')
def ops_integrations_providers():
    data = get_executor_provider().get_providers()
    return jsonify(data)


@api.route('/operations/integrations/summary')
def ops_integrations_summary():
    data = get_executor_provider().get_summary()
    return jsonify(data)


@api.route('/operations/integrations/provider-mode')
def ops_integrations_provider_mode():
    provider = get_executor_provider()
    mode = get_provider_mode()
    return jsonify({
        'mode': mode,
        'executor_url': os.environ.get('EXECUTOR_API_BASE_URL', ''),
        'capabilities': provider.get_capabilities(),
    })


# ═══════════════════════════════════════════
# Phase 2 — Write operations
# ═══════════════════════════════════════════


@api.route('/operations/integrations/sources', methods=['POST'])
def ops_integrations_create_source():
    data = request.get_json()
    if not data or not data.get('type'):
        return jsonify({'error': 'type is required'}), 400
    source_type = data.get('type')
    if source_type == 'openapi' and not data.get('spec'):
        return jsonify({'error': 'spec is required for openapi source creation'}), 400
    if source_type == 'graphql' and not data.get('endpoint'):
        return jsonify({'error': 'endpoint is required for graphql source creation'}), 400
    if source_type == 'mcp':
        transport = data.get('transport', 'remote')
        if transport == 'remote' and not data.get('endpoint'):
            return jsonify({'error': 'endpoint is required for remote mcp source creation'}), 400
        if transport == 'stdio' and not data.get('command'):
            return jsonify({'error': 'command is required for stdio mcp source creation'}), 400
    if source_type == 'discovery' and not data.get('discoveryUrl'):
        return jsonify({'error': 'discoveryUrl is required for discovery source creation'}), 400
    provider = get_executor_provider()
    try:
        source = provider.create_source(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 409
    return jsonify(source), 201


@api.route('/operations/integrations/sources/<source_id>', methods=['PATCH'])
def ops_integrations_update_source(source_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'request body is required'}), 400
    provider = get_executor_provider()
    try:
        result = provider.update_source(source_id, data)
    except Exception as e:
        return jsonify({'error': str(e)}), 409
    if result is None:
        return jsonify({'error': 'Source not found'}), 404
    return jsonify(result)


@api.route('/operations/integrations/sources/<source_id>', methods=['DELETE'])
def ops_integrations_delete_source(source_id):
    provider = get_executor_provider()
    ok = provider.delete_source(source_id)
    if not ok:
        return jsonify({'error': 'Source not found'}), 404
    return jsonify({'success': True})


@api.route('/operations/integrations/credentials', methods=['POST'])
def ops_integrations_bind_credential():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'request body is required'}), 400
    source_type = data.get('sourceType')
    slot = data.get('slot')
    if source_type and slot and not data.get('targetId'):
        return jsonify({'error': 'targetId is required for source binding'}), 400
    if (not source_type or not slot) and (not data.get('provider') or not data.get('targetId')):
        return jsonify({'error': 'provider and targetId are required'}), 400
    provider = get_executor_provider()
    try:
        credential = provider.bind_credential(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 409
    return jsonify(credential), 201


@api.route('/operations/integrations/credentials/<credential_id>', methods=['DELETE'])
def ops_integrations_unbind_credential(credential_id):
    provider = get_executor_provider()
    ok = provider.unbind_credential(credential_id)
    if not ok:
        return jsonify({'error': 'Credential not found'}), 404
    return jsonify({'success': True})
