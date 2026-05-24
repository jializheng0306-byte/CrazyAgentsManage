"""
CrazyAgentsManage WebUI API Layer
Connects to Hermes-Agent's real data sources: state.db, cron/jobs.json, gateway_state.json, tools/registry
Supports both local and remote (SSH) data access modes
"""

import base64
import json
import os
import shlex
import shutil
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
_LOOP_SURFACE_MEMORY_DECISIONS = 'shared-context/loop-surface/memory-candidate-decisions.jsonl'
_LOOP_SURFACE_FEEDBACK_INPUTS = 'shared-context/loop-surface/feedback-inputs.jsonl'
_TASK_BUS_REQUESTS = 'shared-context/agent-requests/requests.jsonl'
_TASK_BUS_EVENTS = 'shared-context/agent-requests/events.jsonl'
_EXECUTOR_READONLY_POLICY = 'shared-context/hermes-executor-readonly-delegation-policy.v1.json'
_TASK_BUS_AUTOMATION_ORDER = ['prototype', 'rehearsed', 'approved-for-automation', 'automated']
_TASK_BUS_STATUS_TRANSITIONS = {
    'accepted': ['routed', 'queued', 'started', 'failed', 'timed_out'],
    'routed': ['queued', 'started', 'failed', 'timed_out'],
    'queued': ['started', 'failed', 'timed_out'],
    'started': ['completed', 'failed', 'timed_out'],
    'completed': ['delivered', 'failed'],
    'delivered': [],
    'timed_out': [],
    'failed': [],
}


def _get_repo_root():
    return Path(__file__).resolve().parents[2]


def _get_runtime_repo_root():
    env_root = os.environ.get('CRAZY_RUNTIME_REPO_ROOT', '').strip()
    if env_root:
        return Path(env_root)
    return Path('/root/CrazyAgentsManage')


def _get_deploy_copy_root():
    deploy_root = os.environ.get('CRAZY_DEPLOY_COPY_ROOT', '').strip()
    if deploy_root:
        return Path(deploy_root)
    return Path('/opt/crazyagentsmanage')


def _get_hermes_script_mirror_dir():
    mirror_dir = os.environ.get('HERMES_SCRIPT_MIRROR_DIR', '').strip()
    if mirror_dir:
        return Path(mirror_dir)
    return _get_hermes_home() / 'scripts'


def _get_backup_root():
    backup_root = os.environ.get('HERMES_BACKUP_ROOT', '').strip()
    if backup_root:
        return Path(backup_root)
    return Path('/root/backups')


def _resolve_repo_artifact_path(rel_path):
    primary = _get_repo_root() / rel_path
    if primary.exists():
        return primary
    runtime_path = _get_runtime_repo_root() / rel_path
    if runtime_path != primary:
        try:
            if runtime_path.exists():
                return runtime_path
        except PermissionError:
            pass
    return primary


def _resolve_shared_context_read_path(rel_path):
    return _resolve_repo_artifact_path(rel_path)


def _resolve_shared_context_write_path(rel_path):
    primary = _get_repo_root() / rel_path
    runtime_path = _get_runtime_repo_root() / rel_path
    if runtime_path != primary:
        try:
            if runtime_path.parent.exists() and not primary.exists():
                return runtime_path
        except PermissionError:
            pass
    return primary


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()


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


def _run_remote_command(command, timeout=15):
    cfg = _get_remote_config()
    host = cfg.get('host', '')
    user = cfg.get('user', 'root')
    password = cfg.get('password', '')

    if not host:
        return ''

    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password, timeout=30)
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        out = stdout.read().decode('utf-8', errors='replace')
        client.close()
        return out
    except Exception:
        return ''


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


def _read_optional_text(path, default=''):
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return default


def _get_remote_repo_root():
    cfg = _get_remote_config()
    return cfg.get('repo_root') or os.environ.get('CRAZY_REMOTE_REPO_ROOT') or '/root/CrazyAgentsManage'


def _read_shared_context_lines(rel_path):
    if _is_remote_mode():
        remote_repo_root = _get_remote_repo_root()
        out = _run_remote_command(f"cat '{remote_repo_root}/{rel_path}' 2>/dev/null", timeout=15)
        if not out.strip():
            return []
        return [line for line in out.splitlines() if line.strip()]

    full_path = _resolve_shared_context_read_path(rel_path)
    if not full_path.exists():
        return []
    return [line for line in full_path.read_text(encoding='utf-8').splitlines() if line.strip()]


def _read_shared_context_rows(rel_path):
    rows = []
    for line in _read_shared_context_lines(rel_path):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _latest_shared_context_rows_by_key(rel_path, key):
    latest = {}
    for row in _read_shared_context_rows(rel_path):
        row_key = str(row.get(key) or '').strip()
        if row_key:
            latest[row_key] = row
    return latest


def _append_shared_context_row(rel_path, payload):
    line = json.dumps(payload, ensure_ascii=False)
    if _is_remote_mode():
        remote_repo_root = _get_remote_repo_root()
        remote_file = str(Path(remote_repo_root) / rel_path)
        remote_dir = str(Path(remote_file).parent)
        command = (
            f"mkdir -p {shlex.quote(remote_dir)} && "
            f"printf '%s\\n' {shlex.quote(line)} >> {shlex.quote(remote_file)} && "
            "printf ok"
        )
        return _run_remote_command(command, timeout=15).strip() == 'ok'

    full_path = _resolve_shared_context_write_path(rel_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, 'a', encoding='utf-8') as handle:
        handle.write(line + '\n')
    return True


def _write_shared_context_lines(rel_path, lines):
    content = '\n'.join(lines)
    if content:
        content += '\n'
    if _is_remote_mode():
        remote_repo_root = _get_remote_repo_root()
        remote_file = str(Path(remote_repo_root) / rel_path)
        remote_dir = str(Path(remote_file).parent)
        encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
        command = (
            f"mkdir -p {shlex.quote(remote_dir)} && "
            "python3 -c "
            + shlex.quote(
                "from pathlib import Path; import base64; "
                f"Path({remote_file!r}).write_text(base64.b64decode({encoded!r}).decode('utf-8'), encoding='utf-8')"
            )
            + " && printf ok"
        )
        return _run_remote_command(command, timeout=20).strip() == 'ok'

    full_path = _resolve_shared_context_write_path(rel_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')
    return True


def _normalize_evidence_refs(raw_value):
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        return [part.strip() for part in raw_value.split(',') if part.strip()]
    return []


def _safe_exists(path):
    try:
        return path.exists()
    except PermissionError:
        return False


def _safe_glob_count(path, pattern='*'):
    try:
        if not path.exists():
            return 0
        return len(list(path.glob(pattern)))
    except PermissionError:
        return 0


def _safe_sorted_paths(path, pattern='*'):
    try:
        if not path.exists():
            return []
        return sorted(path.glob(pattern))
    except PermissionError:
        return []


def _parse_iso_datetime(raw_value):
    text = str(raw_value or '').strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        return None


def _artifact_root_candidates():
    roots = []
    seen = set()
    for root in (_get_repo_root(), _get_runtime_repo_root()):
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        roots.append(root)
    return roots


def _pick_runtime_collaboration_root():
    best_root = _get_repo_root()
    best_score = -1
    for root in _artifact_root_candidates():
        collab_root = root / '.omx' / 'crazyagents'
        score = 0
        if _safe_exists(collab_root / 'runtime-state.json'):
            score += 5
        try:
            score += len(list((collab_root / 'outbox').glob('*.md')))
        except FileNotFoundError:
            pass
        if score > best_score:
            best_root = root
            best_score = score
    return best_root


def _pick_harness_root():
    best_root = _get_repo_root()
    best_score = -1
    for root in _artifact_root_candidates():
        harness_root = root / 'harness'
        score = 0
        try:
            score += len([p for p in (harness_root / 'trace' / 'successes').glob('*.json') if p.name != 'TEMPLATE.json'])
            score += len([p for p in (harness_root / 'trace' / 'failures').glob('*.json') if p.name != 'TEMPLATE.json'])
            score += len([p for p in (harness_root / 'closeouts').glob('*.json') if p.name != 'TEMPLATE.json'])
        except FileNotFoundError:
            pass
        if score > best_score:
            best_root = root
            best_score = score
    return best_root


def _handoff_section_lines(content, heading):
    lines = content.splitlines()
    target = f'## {heading}'
    capture = False
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped == target:
            capture = True
            continue
        if capture and stripped.startswith('## '):
            break
        if capture:
            out.append(line.rstrip())
    return out


def _handoff_section_list(content, heading):
    items = []
    for line in _handoff_section_lines(content, heading):
        stripped = line.strip()
        if stripped.startswith('- '):
            value = stripped[2:].strip()
            if value:
                items.append(value)
    return items


def _handoff_section_value(content, label):
    prefix = f'- {label}:'
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return ''


def _handoff_preview_from_content(content):
    summary = _handoff_section_value(content, 'Current summary')
    goal = _handoff_section_value(content, 'Goal')
    if summary and summary != '(none)':
        return summary
    if goal:
        return goal
    compact = ' '.join(part.strip() for part in content.splitlines() if part.strip())
    return compact[:300]


def _collect_runtime_handoffs(limit=20):
    runtime_root = _pick_runtime_collaboration_root()
    outbox = runtime_root / '.omx' / 'crazyagents' / 'outbox'
    if not outbox.exists():
        return []

    items = []
    for path in sorted(outbox.glob('*.md'), reverse=True):
        content = _read_optional_text(path, '')
        title = _handoff_section_value(content, 'Title') or path.name
        runtime_status = (_handoff_section_value(content, 'Runtime status') or 'unknown').strip().lower()
        runtime_phase = (_handoff_section_value(content, 'Runtime phase') or 'unknown').strip()
        updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        artifacts = _handoff_section_list(content, 'Artifacts To Review')
        questions = _handoff_section_list(content, 'Questions')
        preview = _handoff_preview_from_content(content)
        queue_status = 'closed' if runtime_status in ('completed', 'accepted', 'delivered', 'validated') else 'open'
        severity = 'blocked' if runtime_status == 'blocked' else ('pending' if queue_status == 'open' else 'resolved')
        items.append({
            'name': path.name,
            'path': str(path),
            'relativePath': str(path.relative_to(runtime_root)),
            'updated_at': updated_at,
            'preview': preview,
            'size': len(content),
            'title': title,
            'goal': _handoff_section_value(content, 'Goal'),
            'runtimePhase': runtime_phase,
            'runtimeStatus': runtime_status or 'unknown',
            'currentSummary': _handoff_section_value(content, 'Current summary'),
            'artifactsToReview': artifacts,
            'questions': questions,
            'queueStatus': queue_status,
            'severity': severity,
        })
    return items[:limit]


def _build_runtime_state_view():
    runtime_root = _pick_runtime_collaboration_root()
    state_path = runtime_root / '.omx' / 'crazyagents' / 'runtime-state.json'
    data = _read_optional_json(state_path)
    if not data:
        return {
            'exists': False,
            'path': str(state_path),
            'data': {},
        }
    return {
        'exists': True,
        'path': str(state_path),
        'data': data,
    }


def _build_runtime_harness_summary():
    repo_root = _pick_harness_root()
    success_dir = repo_root / 'harness' / 'trace' / 'successes'
    failure_dir = repo_root / 'harness' / 'trace' / 'failures'
    closeout_dir = repo_root / 'harness' / 'closeouts'
    summary = {
        'success_count': 0,
        'failure_count': 0,
        'closeout_count': 0,
        'latest_success': None,
        'latest_failure': None,
        'latest_closeout': None,
        'pending_closeout_count': 0,
        'source_root': str(repo_root),
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
    closeout_files = sorted(
        [p for p in closeout_dir.glob('*.json') if p.name != 'TEMPLATE.json'],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if closeout_dir.exists() else []

    summary['success_count'] = len(success_files)
    summary['failure_count'] = len(failure_files)
    summary['closeout_count'] = len(closeout_files)

    if success_files:
        summary['latest_success'] = _read_optional_json(success_files[0])
    if failure_files:
        summary['latest_failure'] = _read_optional_json(failure_files[0])
    if closeout_files:
        summary['latest_closeout'] = _read_optional_json(closeout_files[0])

    closeout_trace_ids = set()
    for path in closeout_files:
        payload = _read_optional_json(path)
        if not isinstance(payload, dict):
            continue
        trace = payload.get('trace') if isinstance(payload.get('trace'), dict) else {}
        trace_id = str(trace.get('id') or '').strip()
        if trace_id:
            closeout_trace_ids.add(trace_id)
    trace_ids = [
        str((_read_optional_json(path) or {}).get('id') or '').strip()
        for path in success_files + failure_files
    ]
    summary['pending_closeout_count'] = len([trace_id for trace_id in trace_ids if trace_id and trace_id not in closeout_trace_ids])
    return summary


def _read_shared_context_json(rel_path, default=None):
    if _is_remote_mode():
        remote_repo_root = _get_remote_repo_root()
        out = _run_remote_command(f"cat '{remote_repo_root}/{rel_path}' 2>/dev/null", timeout=15)
        if not out.strip():
            return default if default is not None else {}
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return default if default is not None else {}

    full_path = _resolve_shared_context_read_path(rel_path)
    if not full_path.exists():
        return default if default is not None else {}
    try:
        return json.loads(full_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return default if default is not None else {}


def _task_bus_lane(status):
    status = str(status or '').lower()
    if status in ('accepted', 'routed', 'queued'):
        return 'inbox'
    if status in ('started',):
        return 'working'
    if status in ('completed',):
        return 'outbox'
    if status in ('delivered', 'failed', 'timed_out'):
        return 'archive'
    return 'inbox'


def _task_bus_allowed_transitions(status):
    return _TASK_BUS_STATUS_TRANSITIONS.get(str(status or '').lower(), [])


def _load_task_bus_events():
    rows = _read_shared_context_rows(_TASK_BUS_EVENTS)
    rows.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
    return rows


def _task_bus_events_by_ack_id():
    grouped = {}
    for event in _load_task_bus_events():
        ack_id = str(event.get('ack_id') or '').strip()
        if not ack_id:
            continue
        grouped.setdefault(ack_id, []).append(event)
    return grouped


def _task_bus_enrich_request(payload, events_by_ack_id=None):
    if not isinstance(payload, dict):
        return payload
    item = dict(payload)
    status = str(item.get('status') or 'accepted').lower()
    automation_state = str(item.get('automation_state') or 'prototype').lower()
    item['status'] = status
    item['lane'] = _task_bus_lane(status)
    item['allowedTransitions'] = _task_bus_allowed_transitions(status)
    item['automation_state'] = automation_state
    item['evidence_refs'] = _normalize_evidence_refs(item.get('evidence_refs'))
    item['owner'] = str(item.get('owner') or item.get('target') or '')
    if events_by_ack_id is not None:
        item['events'] = events_by_ack_id.get(str(item.get('ack_id') or ''), [])
    return item


def _load_task_bus_requests():
    events_by_ack_id = _task_bus_events_by_ack_id()
    rows = []
    for payload in _read_shared_context_rows(_TASK_BUS_REQUESTS):
        rows.append(_task_bus_enrich_request(payload, events_by_ack_id))
    rows.sort(key=lambda item: item.get('updated_at') or item.get('created_at') or '', reverse=True)
    return rows


def _task_bus_stats(requests):
    counts = {
        'total': len(requests),
        'accepted': 0,
        'routed': 0,
        'queued': 0,
        'started': 0,
        'completed': 0,
        'delivered': 0,
        'timed_out': 0,
        'failed': 0,
        'open': 0,
    }
    for item in requests:
        status = str(item.get('status') or '').lower()
        if status in counts:
            counts[status] += 1
        if status not in ('delivered', 'timed_out', 'failed'):
            counts['open'] += 1
    return counts


def _task_bus_lane_groups(requests):
    lanes = {'inbox': [], 'working': [], 'outbox': [], 'archive': []}
    for item in requests:
        lane = item.get('lane') or _task_bus_lane(item.get('status'))
        lanes.setdefault(lane, []).append(item)
    return lanes


def _task_bus_automation_stats(requests):
    counts = {state: 0 for state in _TASK_BUS_AUTOMATION_ORDER}
    for item in requests:
        state = str(item.get('automation_state') or 'prototype').lower()
        counts[state] = counts.get(state, 0) + 1
    return counts


def _save_task_bus_requests(requests):
    lines = [
        json.dumps({
            key: value
            for key, value in item.items()
            if key not in ('lane', 'allowedTransitions', 'events')
        }, ensure_ascii=False)
        for item in requests
    ]
    return _write_shared_context_lines(_TASK_BUS_REQUESTS, lines)


def _find_task_bus_request(ack_id):
    requests = _read_shared_context_rows(_TASK_BUS_REQUESTS)
    for index, item in enumerate(requests):
        if str(item.get('ack_id') or '') == ack_id:
            return requests, index, item
    return requests, -1, None


def _append_task_bus_event(ack_id, event_type, actor, payload):
    row = {
        'ack_id': ack_id,
        'event_type': event_type,
        'actor': actor,
        'timestamp': _now_iso(),
        'payload': payload,
    }
    return _append_shared_context_row(_TASK_BUS_EVENTS, row)


def _transition_task_bus_request(ack_id, next_status, actor='operator', note='', result=None, error=None):
    requests, index, item = _find_task_bus_request(ack_id)
    if index < 0 or not item:
        return None, 'Request not found'
    current_status = str(item.get('status') or 'accepted').lower()
    next_status = str(next_status or '').lower()
    allowed = _task_bus_allowed_transitions(current_status)
    if next_status not in allowed:
        return None, f'invalid transition: {current_status} -> {next_status}'

    item['status'] = next_status
    item['updated_at'] = _now_iso()
    item['last_transition_by'] = actor
    item['last_transition_note'] = note
    if result is not None:
        item['result'] = result
    if error is not None:
        item['error'] = error
    requests[index] = item
    if not _save_task_bus_requests(requests):
        return None, 'Failed to persist request bus transition'
    if not _append_task_bus_event(
        ack_id,
        'status_transition',
        actor,
        {
            'from_status': current_status,
            'to_status': next_status,
            'note': note,
            'result': result,
            'error': error,
        },
    ):
        return None, 'Failed to persist request bus event'
    return _task_bus_enrich_request(item, _task_bus_events_by_ack_id()), None


def _promote_task_bus_request(
    ack_id,
    next_state,
    actor='operator',
    approval='',
    rollback_rule='',
    evidence_refs=None,
    note='',
):
    requests, index, item = _find_task_bus_request(ack_id)
    if index < 0 or not item:
        return None, 'Request not found'
    current_state = str(item.get('automation_state') or 'prototype').lower()
    next_state = str(next_state or '').lower()
    if next_state not in _TASK_BUS_AUTOMATION_ORDER:
        return None, 'invalid automation_state'

    current_index = _TASK_BUS_AUTOMATION_ORDER.index(current_state) if current_state in _TASK_BUS_AUTOMATION_ORDER else 0
    next_index = _TASK_BUS_AUTOMATION_ORDER.index(next_state)
    moving_backward = next_index < current_index
    if next_index > current_index + 1:
        return None, 'automation promotion must advance one step at a time'
    if moving_backward and not note:
        return None, 'rollback note is required when moving automation_state backward'

    evidence_refs = _normalize_evidence_refs(evidence_refs)
    if next_state in ('rehearsed', 'approved-for-automation', 'automated') and not evidence_refs:
        return None, 'evidenceRefs are required from rehearsed onward'
    if next_state in ('approved-for-automation', 'automated') and not approval:
        return None, 'approval is required for approved-for-automation or automated'
    if next_state in ('approved-for-automation', 'automated') and not rollback_rule:
        return None, 'rollbackRule is required for approved-for-automation or automated'

    item['automation_state'] = next_state
    item['updated_at'] = _now_iso()
    item['owner'] = str(item.get('owner') or item.get('target') or '')
    item['approval'] = approval or item.get('approval') or ''
    item['rollback_rule'] = rollback_rule or item.get('rollback_rule') or ''
    item['evidence_refs'] = evidence_refs or _normalize_evidence_refs(item.get('evidence_refs'))
    item['note'] = note or item.get('note') or ''
    item['last_transition_by'] = actor
    item['last_transition_note'] = note
    requests[index] = item
    if not _save_task_bus_requests(requests):
        return None, 'Failed to persist automation state'
    if not _append_task_bus_event(
        ack_id,
        'automation_promotion',
        actor,
        {
            'from_state': current_state,
            'to_state': next_state,
            'approval': approval,
            'rollback_rule': rollback_rule,
            'evidence_refs': evidence_refs,
            'note': note,
        },
    ):
        return None, 'Failed to persist automation event'
    return _task_bus_enrich_request(item, _task_bus_events_by_ack_id()), None


def _list_review_report_files():
    home = _get_hermes_home()
    rel_path = 'promises/reviews'
    return _list_files(home, rel_path, 'review-*.md')


def _load_promise_review_state():
    home = _get_hermes_home()
    state_path = home / 'promises' / 'reviews' / 'daily-promise-review-state.json'
    return _read_json(state_path, default={})


def _promise_review_stage(snapshot):
    promise_count = snapshot.get('promise_count', 0) or 0
    classified = snapshot.get('classified_counts', {}) or {}
    promises = snapshot.get('promises', []) or []

    if promise_count == 0:
        return {
            'stage': 'collecting_governance_inputs',
            'stageOwner': 'operator',
            'nextAction': '等待新的 promise review 输入进入本轮 cycle。',
            'status': 'idle',
        }

    completed = classified.get('completed', 0) or 0
    blocked = classified.get('blocked', 0) or 0
    pending = classified.get('pending_count', 0) or 0
    due_today = classified.get('due_today', 0) or 0
    due_soon = classified.get('due_soon', 0) or 0
    overdue = classified.get('overdue', 0) or 0
    in_progress = classified.get('in_progress', 0) or 0
    has_follow_up = any(str(item.get('needs_follow_up') or '').lower() == 'true' for item in promises)

    if completed == promise_count and not has_follow_up:
        return {
            'stage': 'cycle_closed',
            'stageOwner': 'system',
            'nextAction': '当前 review cycle 已闭合，可等待下一轮输入。',
            'status': 'closed',
        }

    if has_follow_up:
        return {
            'stage': 'awaiting_feedback',
            'stageOwner': 'operator',
            'nextAction': '优先处理仍需 follow-up 的 promise，并判断是否需要新的治理反馈。',
            'status': 'open',
        }

    if blocked or pending or due_today or due_soon or overdue or in_progress:
        return {
            'stage': 'awaiting_operational_review',
            'stageOwner': 'operator',
            'nextAction': '检查 blocked / pending / due 项，并完成本轮承诺审查判断。',
            'status': 'open',
        }

    return {
        'stage': 'collecting_governance_inputs',
        'stageOwner': 'operator',
        'nextAction': '补齐治理输入并准备下一轮审查。',
        'status': 'open',
    }


def _build_promise_review_loop():
    state = _load_promise_review_state() or {}
    snapshot = state.get('snapshot') or {}
    if not snapshot:
        return None

    checked_at = state.get('checked_at')
    digest = str(state.get('digest') or '')
    digest_short = digest[:12] if digest else 'unknown'
    reports = _list_review_report_files()
    latest_report = reports[-1] if reports else ''
    round_number = len(reports) if reports else 1

    stage_info = _promise_review_stage(snapshot)
    promises = snapshot.get('promises', []) or []
    classified = snapshot.get('classified_counts', {}) or {}
    blocked = classified.get('blocked', 0) or 0
    overdue = classified.get('overdue', 0) or 0
    due_today = classified.get('due_today', 0) or 0
    needs_follow_up = len([
        item for item in promises
        if str(item.get('needs_follow_up') or '').lower() == 'true'
    ])

    evidence_refs = [
        ref for ref in [
            'state:promises/reviews/daily-promise-review-state.json',
            f'report:{latest_report}' if latest_report else '',
            'script:scripts/daily-promise-review.py',
        ] if ref
    ]

    summary_parts = [
        f'promises={snapshot.get("promise_count", 0) or 0}',
        f'blocked={blocked}',
        f'overdue={overdue}',
        f'due_today={due_today}',
        f'needs_follow_up={needs_follow_up}',
    ]

    return {
        'loopId': f'promise-review-cycle:{digest_short}',
        'cycleType': 'promise-review-cycle',
        'sourceJobId': 'daily-promise-review',
        'sourceJobName': 'daily-promise-review.py',
        'roundNumber': round_number,
        'stage': stage_info['stage'],
        'stageOwner': stage_info['stageOwner'],
        'openedAt': checked_at,
        'updatedAt': checked_at,
        'status': stage_info['status'],
        'nextAction': stage_info['nextAction'],
        'feedbackStatus': 'follow-up-pending' if needs_follow_up else 'no-follow-up-required',
        'memoryCandidateStatus': 'not-started',
        'summary': ' | '.join(summary_parts),
        'evidenceRefs': evidence_refs,
        'classifiedCounts': classified,
        'objectCount': snapshot.get('promise_count', 0) or 0,
        'followUpCount': needs_follow_up,
        'promises': promises,
        'sourcePaths': {
            'state': 'promises/reviews/daily-promise-review-state.json',
            'latestReport': latest_report,
        },
    }


def _list_intel_summary_files():
    home = _get_hermes_home()
    rel_path = 'intel'
    files = _list_files(home, rel_path, 'summary-*.md')
    return sorted(files)


def _list_intel_data_files():
    home = _get_hermes_home()
    rel_path = 'intel'
    files = _list_files(home, rel_path, 'intel-data-*.json')
    return sorted(files)


def _load_latest_intel_data():
    home = _get_hermes_home()
    files = _list_intel_data_files()
    if not files:
        return {}
    return _read_json(home / 'intel' / files[-1], default={})


def _build_morning_intel_loop():
    data = _load_latest_intel_data()
    if not isinstance(data, dict) or not data:
        return None

    papers = data.get('papers') or []
    rss_items = data.get('rss_items') or []
    summary_files = _list_intel_summary_files()
    latest_summary = summary_files[-1] if summary_files else ''
    timestamp = data.get('timestamp')
    round_number = len(summary_files) if summary_files else 1
    digest_date = ''
    if latest_summary:
        digest_date = latest_summary.replace('summary-', '').replace('.md', '')
    elif timestamp:
        digest_date = str(timestamp)[:10]

    return {
        'loopId': f'morning-intel-cycle:{digest_date or "latest"}',
        'cycleType': 'morning-intel-cycle',
        'sourceJobId': 'morning-intel',
        'sourceJobName': 'morning-intel-v2.py',
        'roundNumber': round_number,
        'stage': 'awaiting_operational_acceptance',
        'stageOwner': 'operator',
        'openedAt': timestamp,
        'updatedAt': timestamp,
        'status': 'open',
        'nextAction': '检查本轮情报摘要并决定是否需要 follow-up、纳入 radar、或沉淀成后续 memory candidate。',
        'feedbackStatus': 'not-started',
        'memoryCandidateStatus': 'not-started',
        'summary': f'papers={len(papers)} | feeds={len(rss_items)}',
        'evidenceRefs': [
            ref for ref in [
                f'report:{latest_summary}' if latest_summary else '',
                f'data:{_list_intel_data_files()[-1]}' if _list_intel_data_files() else '',
                'script:scripts/morning-intel-v2.py',
            ] if ref
        ],
        'objectCount': len(papers) + len(rss_items),
        'followUpCount': 0,
        'classifiedCounts': {
            'total': len(papers) + len(rss_items),
            'papers': len(papers),
            'feeds': len(rss_items),
        },
        'sourcePaths': {
            'latestReport': latest_summary,
            'latestData': _list_intel_data_files()[-1] if _list_intel_data_files() else '',
        },
    }


def _build_promise_review_memory_candidates(loop):
    if not isinstance(loop, dict):
        return []
    candidates = []
    for item in loop.get('promises') or []:
        if str(item.get('needs_follow_up') or '').lower() != 'true':
            continue
        promise_id = str(item.get('promise_id') or '')
        candidate_id = str(item.get('flowmind_candidate_id') or '')
        lesson = item.get('latest_feedback_summary') or item.get('last_trace_summary') or item.get('title') or ''
        if not lesson:
            lesson = 'Follow-up changed this promise review round and should be checked for durable learning value.'
        candidates.append({
            'candidateId': f'memory-candidate:{promise_id}',
            'loopId': loop.get('loopId'),
            'promiseId': promise_id,
            'flowmindCandidateId': candidate_id,
            'candidateType': 'reflection_learning',
            'sourcePlane': 'reflection',
            'status': 'candidate',
            'proposedTarget': 'MEMORY.md',
            'targetMemoryPlane': 'host-memory',
            'proposedLesson': str(lesson)[:300],
            'sourceRefs': [
                ref for ref in [
                    f'promise:{promise_id}',
                    f'candidate:{candidate_id}' if candidate_id else '',
                    'state:promises/reviews/daily-promise-review-state.json',
                ] if ref
            ],
        })
    return candidates


def _build_promise_review_feedback_inputs(loop):
    if not isinstance(loop, dict):
        return []
    inputs = []
    for item in loop.get('promises') or []:
        if str(item.get('needs_follow_up') or '').lower() != 'true':
            continue
        promise_id = str(item.get('promise_id') or '')
        follow_up_kind = str(item.get('follow_up_kind') or '')
        next_actor = str(item.get('next_actor') or '') or 'operator'
        latest_feedback_type = str(item.get('latest_feedback_type') or '')
        summary = item.get('latest_feedback_summary') or item.get('last_trace_summary') or item.get('title') or ''
        base_event_type = (latest_feedback_type or follow_up_kind).lower()
        if base_event_type in ('confirmed', 'blocked', 'clarified'):
            input_mode = 'event_annotation'
            allowed_event_types = [base_event_type]
            default_event_type = base_event_type
        else:
            input_mode = 'explicit_event'
            allowed_event_types = ['deferred', 'cancelled']
            default_event_type = 'deferred'
        inputs.append({
            'inputId': f'feedback-input:{promise_id}',
            'loopId': loop.get('loopId'),
            'promiseId': promise_id,
            'flowmindCandidateId': str(item.get('flowmind_candidate_id') or ''),
            'targetInstanceId': str(item.get('instance_id') or ''),
            'targetSourceAgent': 'HermesAgent',
            'followUpKind': follow_up_kind,
            'nextActor': next_actor,
            'status': 'pending-input',
            'latestFeedbackType': latest_feedback_type,
            'inputMode': input_mode,
            'allowedEventTypes': allowed_event_types,
            'defaultEventType': default_event_type,
            'prefillText': str(summary)[:300],
            'sourceRefs': [
                ref for ref in [
                    f'promise:{promise_id}',
                    f'candidate:{item.get("flowmind_candidate_id")}' if item.get('flowmind_candidate_id') else '',
                    'state:promises/reviews/daily-promise-review-state.json',
                ] if ref
            ],
        })
    return inputs


def _apply_memory_candidate_decision(candidate, decision_row):
    if not isinstance(candidate, dict):
        return candidate
    if not isinstance(decision_row, dict):
        return candidate
    candidate['status'] = str(decision_row.get('status') or candidate.get('status') or 'candidate')
    candidate['lastAction'] = str(decision_row.get('action') or '')
    candidate['decisionNote'] = str(decision_row.get('note') or '')
    candidate['decisionEvidenceRefs'] = decision_row.get('evidenceRefs') or []
    candidate['decidedAt'] = str(decision_row.get('recordedAt') or '')
    candidate['decidedBy'] = str(decision_row.get('recordedBy') or '')
    candidate['authorityPlane'] = str(decision_row.get('authorityPlane') or candidate.get('targetMemoryPlane') or '')
    return candidate


def _apply_feedback_input_submission(input_item, submission_row):
    if not isinstance(input_item, dict):
        return input_item
    if not isinstance(submission_row, dict):
        return input_item
    payload = submission_row.get('payload') if isinstance(submission_row.get('payload'), dict) else {}
    input_item['status'] = str(submission_row.get('status') or input_item.get('status') or 'pending-input')
    input_item['lastSubmissionMode'] = str(submission_row.get('mode') or '')
    input_item['lastSubmissionEventType'] = str(submission_row.get('eventType') or '')
    input_item['lastSubmissionReason'] = str(payload.get('reason') or '')
    input_item['lastSubmissionNote'] = str(payload.get('note') or '')
    input_item['lastSubmissionEvidenceRefs'] = payload.get('evidenceRefs') or []
    input_item['lastSubmissionAt'] = str(submission_row.get('recordedAt') or '')
    input_item['lastSubmissionBoundary'] = str(submission_row.get('writeBoundary') or 'local-operator-queue')
    input_item['lastRecordedBy'] = str(submission_row.get('recordedBy') or '')
    return input_item


def _summarize_memory_candidate_status(candidates):
    if not candidates:
        return 'not-started'
    settled = [
        item for item in candidates
        if str(item.get('status') or '') in ('accepted', 'rejected', 'deferred')
    ]
    if not settled:
        return 'awaiting-confirmation'
    if len(settled) == len(candidates):
        return 'decision-recorded'
    return 'partial-decision-recorded'


def _summarize_feedback_input_status(inputs, base_status):
    if not inputs:
        return base_status
    submitted = [
        item for item in inputs
        if str(item.get('status') or '') == 'submitted-local'
    ]
    if not submitted:
        return base_status
    if len(submitted) == len(inputs):
        return 'local-submission-recorded'
    return 'partial-local-submission'


def _build_enriched_promise_review_loop():
    loop = _build_promise_review_loop()
    if not loop:
        return None

    decision_map = _latest_shared_context_rows_by_key(_LOOP_SURFACE_MEMORY_DECISIONS, 'candidateId')
    submission_map = _latest_shared_context_rows_by_key(_LOOP_SURFACE_FEEDBACK_INPUTS, 'inputId')

    candidates = [
        _apply_memory_candidate_decision(candidate, decision_map.get(candidate.get('candidateId')))
        for candidate in _build_promise_review_memory_candidates(loop)
    ]
    inputs = [
        _apply_feedback_input_submission(input_item, submission_map.get(input_item.get('inputId')))
        for input_item in _build_promise_review_feedback_inputs(loop)
    ]

    loop['memoryCandidates'] = candidates
    loop['feedbackInputs'] = inputs
    loop['memoryCandidateStatus'] = _summarize_memory_candidate_status(candidates)
    loop['feedbackStatus'] = _summarize_feedback_input_status(inputs, loop.get('feedbackStatus'))
    return loop


def _build_collaboration_loops():
    loops = []
    promise_loop = _build_enriched_promise_review_loop()
    if promise_loop:
        loops.append(promise_loop)

    morning_loop = _build_morning_intel_loop()
    if morning_loop:
        morning_loop['memoryCandidates'] = []
        morning_loop['feedbackInputs'] = []
        loops.append(morning_loop)
    return loops


def _find_memory_candidate(candidate_id):
    loop = _build_enriched_promise_review_loop()
    if not loop:
        return None
    for candidate in loop.get('memoryCandidates') or []:
        if candidate.get('candidateId') == candidate_id:
            return candidate
    return None


def _find_feedback_input(input_id):
    loop = _build_enriched_promise_review_loop()
    if not loop:
        return None
    for input_item in loop.get('feedbackInputs') or []:
        if input_item.get('inputId') == input_id:
            return input_item
    return None


def _health_status_for_percent(used_percent):
    if used_percent is None:
        return 'unknown'
    if used_percent >= 90:
        return 'failed'
    if used_percent >= 80:
        return 'degraded'
    return 'healthy'


def _empty_host_health(source):
    return {
        'source': source,
        'status': 'unknown',
        'disk': {
            'mount': '/',
            'total_bytes': 0,
            'used_bytes': 0,
            'free_bytes': 0,
            'used_percent': None,
            'status': 'unknown',
        },
        'memory': {
            'total_bytes': 0,
            'used_bytes': 0,
            'available_bytes': 0,
            'used_percent': None,
            'status': 'unknown',
        },
    }


def _load_local_host_health():
    try:
        disk = shutil.disk_usage('/')
        disk_total = int(disk.total)
        disk_used = int(disk.used)
        disk_free = int(disk.free)
        disk_used_percent = round((disk_used / disk_total) * 100, 1) if disk_total else None
    except Exception:
        disk_total = disk_used = disk_free = 0
        disk_used_percent = None

    mem_total = mem_available = mem_used = 0
    mem_used_percent = None
    try:
        meminfo = {}
        with open('/proc/meminfo', 'r', encoding='utf-8') as handle:
            for line in handle:
                if ':' not in line:
                    continue
                key, raw_value = line.split(':', 1)
                value_kb = int(raw_value.strip().split()[0])
                meminfo[key] = value_kb * 1024
        mem_total = int(meminfo.get('MemTotal', 0))
        mem_available = int(meminfo.get('MemAvailable', 0))
        mem_used = max(mem_total - mem_available, 0)
        mem_used_percent = round((mem_used / mem_total) * 100, 1) if mem_total else None
    except Exception:
        pass

    disk_status = _health_status_for_percent(disk_used_percent)
    memory_status = _health_status_for_percent(mem_used_percent)
    overall_status = 'healthy'
    for status in (disk_status, memory_status):
        if status == 'failed':
            overall_status = 'failed'
            break
        if status == 'degraded':
            overall_status = 'degraded'

    return {
        'source': 'local',
        'status': overall_status,
        'disk': {
            'mount': '/',
            'total_bytes': disk_total,
            'used_bytes': disk_used,
            'free_bytes': disk_free,
            'used_percent': disk_used_percent,
            'status': disk_status,
        },
        'memory': {
            'total_bytes': mem_total,
            'used_bytes': mem_used,
            'available_bytes': mem_available,
            'used_percent': mem_used_percent,
            'status': memory_status,
        },
    }


def _load_remote_host_health():
    python_snippet = r"""python3 - <<'PY'
import json, shutil

def _status(value):
    if value is None:
        return 'unknown'
    if value >= 90:
        return 'failed'
    if value >= 80:
        return 'degraded'
    return 'healthy'

disk = shutil.disk_usage('/')
disk_total = int(disk.total)
disk_used = int(disk.used)
disk_free = int(disk.free)
disk_used_percent = round((disk_used / disk_total) * 100, 1) if disk_total else None

mem_total = mem_available = mem_used = 0
mem_used_percent = None
with open('/proc/meminfo', 'r', encoding='utf-8') as handle:
    info = {}
    for line in handle:
        if ':' not in line:
            continue
        key, raw = line.split(':', 1)
        info[key] = int(raw.strip().split()[0]) * 1024
mem_total = int(info.get('MemTotal', 0))
mem_available = int(info.get('MemAvailable', 0))
mem_used = max(mem_total - mem_available, 0)
mem_used_percent = round((mem_used / mem_total) * 100, 1) if mem_total else None

disk_status = _status(disk_used_percent)
memory_status = _status(mem_used_percent)
overall = 'healthy'
for status in (disk_status, memory_status):
    if status == 'failed':
        overall = 'failed'
        break
    if status == 'degraded':
        overall = 'degraded'

print(json.dumps({
    'source': 'remote',
    'status': overall,
    'disk': {
        'mount': '/',
        'total_bytes': disk_total,
        'used_bytes': disk_used,
        'free_bytes': disk_free,
        'used_percent': disk_used_percent,
        'status': disk_status,
    },
    'memory': {
        'total_bytes': mem_total,
        'used_bytes': mem_used,
        'available_bytes': mem_available,
        'used_percent': mem_used_percent,
        'status': memory_status,
    },
}))
PY"""
    out = _run_remote_command(python_snippet, timeout=20)
    try:
        return json.loads(out.strip()) if out.strip() else _empty_host_health('remote')
    except json.JSONDecodeError:
        return _empty_host_health('remote')


def _load_host_health():
    return _load_remote_host_health() if _is_remote_mode() else _load_local_host_health()

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


def _string_to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == 'true':
            return True
        if lowered == 'false':
            return False
    return value


def _normalize_operational_follow_up(replay, field_map):
    projection = replay.get('operationalFollowUp')
    if isinstance(projection, dict):
        return {
            'projectionState': projection.get('projectionState'),
            'flowmindStatus': projection.get('flowmindStatus'),
            'lastGovernanceStatus': projection.get('lastGovernanceStatus'),
            'lastGovernanceFeedback': projection.get('lastGovernanceFeedback'),
            'localStatus': projection.get('localStatus'),
            'needsFollowUp': projection.get('needsFollowUp'),
            'followUpKind': projection.get('followUpKind'),
            'nextActor': projection.get('nextActor'),
            'isTerminalLocal': projection.get('isTerminalLocal'),
            'reason': projection.get('reason'),
            'note': projection.get('note'),
            'evidenceRefs': list(projection.get('evidenceRefs') or []),
            'updatedAt': projection.get('updatedAt'),
            'missingFields': list(projection.get('missingFields') or []),
        }

    if not isinstance(field_map, dict):
        return None

    fallback_projection = {
        'projectionState': field_map.get('Projection State'),
        'flowmindStatus': field_map.get('FlowMind Status'),
        'lastGovernanceStatus': field_map.get('Last Governance Status'),
        'lastGovernanceFeedback': field_map.get('Last Governance Feedback'),
        'localStatus': field_map.get('Local Status'),
        'needsFollowUp': _string_to_bool(field_map.get('Needs Follow-Up')),
        'followUpKind': field_map.get('Follow-Up Kind'),
        'nextActor': field_map.get('Next Actor'),
        'isTerminalLocal': _string_to_bool(field_map.get('Is Terminal Local')),
        'reason': field_map.get('Reason'),
        'note': field_map.get('Note'),
        'evidenceRefs': [
            ref.strip()
            for ref in str(field_map.get('Follow-Up Evidence Refs') or '').split(',')
            if ref.strip()
        ],
        'updatedAt': None,
        'missingFields': [],
    }
    if not any(
        fallback_projection.get(key) not in (None, '', [])
        for key in (
            'projectionState',
            'flowmindStatus',
            'lastGovernanceStatus',
            'lastGovernanceFeedback',
            'localStatus',
            'needsFollowUp',
            'followUpKind',
            'nextActor',
            'isTerminalLocal',
            'reason',
            'note',
        )
    ):
        return None
    return fallback_projection


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


_HANDOFF_REQUIRED_FIELDS = [
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


_EXECUTION_BOUNDARY_REQUIRED_FIELDS = [
    'Canonical Authority',
    'Local Writable Targets',
    'Human Gate Actions',
    'Forbidden Mutations',
]


def _missing_execution_boundary_fields(execution_boundary):
    if not isinstance(execution_boundary, dict):
        return list(_EXECUTION_BOUNDARY_REQUIRED_FIELDS)
    return [
        field for field, key in (
            ('Canonical Authority', 'canonicalAuthority'),
            ('Local Writable Targets', 'localWritableTargets'),
            ('Human Gate Actions', 'humanGateActions'),
            ('Forbidden Mutations', 'forbiddenMutations'),
        )
        if execution_boundary.get(key) in (None, '', [])
    ]


def _normalize_handoff_contract(
    contract,
    execution_boundary_missing_fields,
    execution_boundary_source,
    missing_fields,
    replay_gaps,
    ready=False,
):
    fallback_order = [
        'semanticContext.fieldMappings',
        'latestEvidence',
        'traceSummary',
    ]
    if not isinstance(contract, dict):
        blocking_issues = list(replay_gaps or [])
        for field in list(missing_fields or []):
            blocking_issues.append(f'Handoff packet is missing required field: {field}.')
        if execution_boundary_missing_fields:
            blocking_issues.append(
                'Execution boundary is incomplete: ' + ', '.join(execution_boundary_missing_fields) + '.'
            )
        return {
            'version': 'handoff-packet-v1',
            'primarySource': 'moduleDetails.handoff',
            'fallbackOrder': fallback_order,
            'ready': bool(ready),
            'blockingIssues': blocking_issues or ['handoffContract is missing from replay response.'],
            'missingFields': list(missing_fields or []),
            'executionBoundarySource': execution_boundary_source or 'upstream',
            'executionBoundaryMissingFields': list(execution_boundary_missing_fields or []),
        }

    return {
        'version': contract.get('version') or 'handoff-packet-v1',
        'primarySource': contract.get('primarySource') or 'moduleDetails.handoff',
        'fallbackOrder': contract.get('fallbackOrder') or fallback_order,
        'ready': bool(contract.get('ready', ready)),
        'blockingIssues': list(contract.get('blockingIssues') or []),
        'missingFields': list(contract.get('missingFields') or []),
        'executionBoundarySource': contract.get('executionBoundarySource') or execution_boundary_source or 'upstream',
        'executionBoundaryMissingFields': list(
            contract.get('executionBoundaryMissingFields') or execution_boundary_missing_fields or []
        ),
    }


def _normalize_runtime_handoff_summary(record_id, replay):
    module_details = replay.get('moduleDetails') or {}
    handoff = module_details.get('handoff')
    steps = [step for step in (replay.get('steps') or []) if isinstance(step, dict)]
    latest_step = steps[-1] if steps else {}
    semantic_context = replay.get('semanticContext') or {}

    if isinstance(handoff, dict):
        sections = handoff.get('sections') or []
        field_map = _handoff_field_map(sections)
        missing_fields = [
            field for field in _HANDOFF_REQUIRED_FIELDS
            if field not in field_map or field_map.get(field) in (None, '')
        ]
        handoff_boundary = _execution_boundary_from_handoff_sections(sections)
        semantic_boundary = _execution_boundary_from_semantic_context(semantic_context)
        execution_boundary = handoff_boundary or semantic_boundary
        execution_boundary_source = (
            'moduleDetails.handoff.Execution Boundary'
            if handoff_boundary
            else ('semanticContext.executionBoundary' if semantic_boundary else None)
        )
        missing_boundary_fields = _missing_execution_boundary_fields(execution_boundary)
        gaps = list(replay.get('gaps') or [])
        if execution_boundary is None:
            gaps.append('executionBoundary is missing from moduleDetails.handoff and semanticContext.')
        truth_status = field_map.get('Truth Status', '')
        candidate_status = field_map.get('Candidate Status', '')
        is_ready = truth_status in ('approved', 'committed')
        if not is_ready and truth_status:
            gaps.insert(0, f'Truth Status is "{truth_status}" (not ready for handoff)')
        if not is_ready and candidate_status:
            gaps.insert(0, f'Candidate Status is "{candidate_status}" (not ready)')

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
            'executionBoundarySource': execution_boundary_source,
            'executionBoundaryMissingFields': missing_boundary_fields,
            'traceEventCount': len(steps),
            'latestTraceAction': field_map.get('Latest Trace Action'),
            'latestTraceSummary': field_map.get('Latest Trace Summary'),
            'consumerHints': field_map.get('Consumer Hints'),
            'missingFields': missing_fields,
            'gaps': gaps,
            'handoffContract': _normalize_handoff_contract(
                replay.get('handoffContract'),
                missing_boundary_fields,
                execution_boundary_source,
                missing_fields,
                gaps,
                ready=is_ready,
            ),
            'operationalFollowUp': _normalize_operational_follow_up(replay, field_map),
        }

    semantic_boundary = _execution_boundary_from_semantic_context(semantic_context)
    gaps = list(replay.get('gaps') or [])
    gaps.append('moduleDetails.handoff is missing from the current replay payload.')
    if semantic_boundary is None:
        gaps.append('executionBoundary is missing from moduleDetails.handoff and semanticContext.')
    execution_boundary_source = 'semanticContext.executionBoundary' if semantic_boundary else None
    missing_boundary_fields = _missing_execution_boundary_fields(semantic_boundary)
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
        'executionBoundarySource': execution_boundary_source,
        'executionBoundaryMissingFields': missing_boundary_fields,
        'traceEventCount': len(steps),
        'latestTraceAction': latest_step.get('action'),
        'latestTraceSummary': latest_step.get('summary') or latest_step.get('detail') or latest_step.get('label'),
        'consumerHints': None,
        'missingFields': list(_HANDOFF_REQUIRED_FIELDS),
        'gaps': gaps,
        'handoffContract': _normalize_handoff_contract(
            replay.get('handoffContract'),
            missing_boundary_fields,
            execution_boundary_source,
            _HANDOFF_REQUIRED_FIELDS,
            gaps,
        ),
        'operationalFollowUp': _normalize_operational_follow_up(replay, {}),
    }


def _runtime_handoff_unavailable_payload(record_id, gap_message):
    missing_boundary_fields = list(_EXECUTION_BOUNDARY_REQUIRED_FIELDS)
    gaps = [gap_message]
    handoff_contract = _normalize_handoff_contract(
        None,
        missing_boundary_fields,
        None,
        _HANDOFF_REQUIRED_FIELDS,
        gaps,
    )
    handoff_contract['blockingIssues'] = [gap_message]
    return {
        'recordId': record_id,
        'source': 'flowmind_unavailable',
        'mode': '',
        'title': 'Handoff Summary',
        'summary': '',
        'sections': [],
        'fieldMap': {},
        'semanticContext': {},
        'executionBoundary': None,
        'executionBoundarySource': None,
        'executionBoundaryMissingFields': missing_boundary_fields,
        'traceEventCount': 0,
        'latestTraceAction': None,
        'latestTraceSummary': None,
        'consumerHints': None,
        'missingFields': list(_HANDOFF_REQUIRED_FIELDS),
        'gaps': gaps,
        'handoffContract': handoff_contract,
        'operationalFollowUp': None,
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


def _load_overview_memories():
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

    return memories


@api.route('/overview/memories')
def overview_memories():
    return jsonify(_load_overview_memories())


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


def _load_gateway_status():
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

    return status


@api.route('/dashboard/gateway-status')
def dashboard_gateway_status():
    return jsonify(_load_gateway_status())


# ═══════════════════════════════════════════
# CrazyAgents runtime / handoff APIs
# ═══════════════════════════════════════════

@api.route('/runtime/state')
def runtime_state():
    return jsonify(_build_runtime_state_view())


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
        return jsonify(
            _runtime_handoff_unavailable_payload(
                record_id,
                'FlowMind replay upstream unavailable for the provided recordId.',
            )
        ), 502

    return jsonify(_collect_runtime_handoffs(limit=20))


@api.route('/runtime/harness-summary')
def runtime_harness_summary():
    return jsonify(_build_runtime_harness_summary())


def _build_collaboration_summary_view():
    handoffs = _collect_runtime_handoffs(limit=20)
    snapshot = _build_runtime_state_view()
    harness = _build_runtime_harness_summary()

    latest_closeout = harness.get('latest_closeout') if isinstance(harness.get('latest_closeout'), dict) else None
    latest_closeout_ts = _parse_iso_datetime((latest_closeout or {}).get('timestamp'))
    latest_snapshot_ts = _parse_iso_datetime(((snapshot.get('data') or {}) if snapshot.get('exists') else {}).get('updated_at'))

    open_handoffs = [item for item in handoffs if item.get('queueStatus') == 'open']
    blocked_handoffs = [item for item in open_handoffs if item.get('runtimeStatus') == 'blocked']
    stale_unreviewed = []
    now_utc = datetime.now(timezone.utc)
    for item in open_handoffs:
        item_ts = _parse_iso_datetime(item.get('updated_at'))
        if item_ts and (now_utc - item_ts).total_seconds() >= 24 * 3600:
            stale_unreviewed.append(item)

    snapshot_status = str(((snapshot.get('data') or {}) if snapshot.get('exists') else {}).get('status') or '').strip().lower()
    completed_snapshot = snapshot_status in ('completed', 'validated', 'accepted', 'delivered', 'blocked')
    missing_writeback = 1 if completed_snapshot and latest_snapshot_ts and (not latest_closeout_ts or latest_snapshot_ts > latest_closeout_ts) else 0

    triage = [
        {
            'id': 'open-handoff',
            'label': 'Open Handoffs',
            'count': len(open_handoffs),
            'status': 'degraded' if open_handoffs else 'healthy',
            'summary': '仍留在交接对象池中、未进入明确 closed runtime state 的 handoff 包。',
            'href': '/collaboration/tasks',
            'evidenceRefs': [
                {'label': 'Handoff queue', 'kind': 'runtime-local', 'path': '.omx/crazyagents/outbox'},
                {'label': 'Task workspace', 'kind': 'route', 'href': '/collaboration/tasks'},
            ],
        },
        {
            'id': 'pending-closeout',
            'label': 'Pending Closeout',
            'count': harness.get('pending_closeout_count', 0),
            'status': 'degraded' if harness.get('pending_closeout_count', 0) else 'healthy',
            'summary': '已写 trace 但仍未绑定 closeout artifact 的协作轮次。',
            'href': '/operations#harness',
            'evidenceRefs': [
                {'label': 'Harness readiness', 'kind': 'route', 'href': '/operations#harness'},
                {'label': 'Closeout artifacts', 'kind': 'repo-artifact', 'path': 'harness/closeouts/*.json'},
            ],
        },
        {
            'id': 'missing-writeback',
            'label': 'Missing Writeback',
            'count': missing_writeback,
            'status': 'degraded' if missing_writeback else 'healthy',
            'summary': 'runtime snapshot 已进入完成/验证态，但仓库 closeout 仍未追平。',
            'href': '/collaboration',
            'evidenceRefs': [
                {'label': 'Runtime snapshot', 'kind': 'runtime-local', 'path': '.omx/crazyagents/runtime-state.json'},
                {'label': 'Master task plan', 'kind': 'repo-artifact', 'path': 'docs/roadmap/master-task-plan.md'},
            ],
        },
        {
            'id': 'unreviewed-artifact',
            'label': 'Unreviewed Artifact',
            'count': len(stale_unreviewed),
            'status': 'degraded' if stale_unreviewed else 'healthy',
            'summary': '长期停留在 outbox 的旧 handoff artifact，说明 review / acceptance 没被系统性收口。',
            'href': '/runtime/sessions',
            'evidenceRefs': [
                {'label': 'Runtime sessions', 'kind': 'route', 'href': '/runtime/sessions'},
                {'label': 'Governance graph', 'kind': 'route', 'href': '/governance/graph'},
            ],
        },
    ]

    next_hop = next((item for item in triage if item.get('status') == 'degraded'), None)
    if not next_hop:
        next_hop = {
            'label': '进入 Loop Surface',
            'reason': '当前协作链没有显式缺口时，继续检查 cycle / gate / feedback / memory candidate。',
            'href': '/collaboration/loops',
        }
    else:
        next_hop = {
            'label': next_hop.get('label'),
            'reason': next_hop.get('summary'),
            'href': next_hop.get('href'),
        }

    status = 'healthy'
    if any(item.get('status') == 'degraded' for item in triage):
        status = 'degraded'
    elif not handoffs and not snapshot.get('exists') and not harness.get('closeout_count', 0):
        status = 'unknown'

    evidence_jumps = [
        {'label': '任务协作工作台', 'href': '/collaboration/tasks', 'desc': '从 handoff 进入执行工作面。'},
        {'label': 'Loop Surface', 'href': '/collaboration/loops', 'desc': '查看当前 cycle / gate / feedback / memory candidate。'},
        {'label': '运行态会话', 'href': '/runtime/sessions', 'desc': '查看 supporting runtime evidence。'},
        {'label': '治理图谱', 'href': '/governance/graph', 'desc': '查看关系与上下游参照。'},
        {'label': 'Harness Readiness', 'href': '/operations#harness', 'desc': '核对 closeout / trace / writeback evidence。'},
    ]

    return {
        'status': status,
        'counts': {
            'handoffCount': len(handoffs),
            'openHandoffCount': len(open_handoffs),
            'blockedHandoffCount': len(blocked_handoffs),
            'pendingCloseoutCount': harness.get('pending_closeout_count', 0),
            'missingWritebackCount': missing_writeback,
            'unreviewedArtifactCount': len(stale_unreviewed),
            'snapshotCount': 1 if snapshot.get('exists') else 0,
            'closeoutCount': harness.get('closeout_count', 0),
        },
        'briefing': {
            'label': 'Collaboration closeout chain',
            'title': '协作闭环状态已聚合为 handoff / snapshot / closeout / repo truth 的统一摘要。',
            'summary': '先看 open handoff、pending closeout、missing writeback 与 unreviewed artifact，再决定是进入任务工作台、Harness 证据面还是治理图谱。',
        },
        'nextHop': next_hop,
        'handoffs': handoffs,
        'runtimeSnapshot': snapshot,
        'harness': harness,
        'triage': triage,
        'evidenceJumps': evidence_jumps,
    }


def _build_collaboration_graph_projection():
    summary = _build_collaboration_summary_view()
    counts = summary.get('counts') or {}
    handoff_status = 'healthy'
    if counts.get('openHandoffCount', 0):
        handoff_status = 'degraded'
    elif not counts.get('handoffCount', 0):
        handoff_status = 'unknown'

    snapshot_status = 'healthy' if counts.get('snapshotCount', 0) else 'unknown'
    if counts.get('missingWritebackCount', 0):
        snapshot_status = 'degraded'

    closeout_status = 'healthy' if counts.get('closeoutCount', 0) else 'unknown'
    if counts.get('pendingCloseoutCount', 0):
        closeout_status = 'degraded'

    repo_truth_status = 'healthy' if counts.get('closeoutCount', 0) and not counts.get('missingWritebackCount', 0) else 'unknown'
    if counts.get('missingWritebackCount', 0):
        repo_truth_status = 'degraded'

    hermes_status = 'healthy'
    if counts.get('blockedHandoffCount', 0) or counts.get('unreviewedArtifactCount', 0):
        hermes_status = 'degraded'
    elif not counts.get('handoffCount', 0):
        hermes_status = 'unknown'

    return {
        'status': summary.get('status', 'unknown'),
        'nodes': [
            {'id': 'codex', 'label': 'Codex', 'status': 'healthy', 'summary': '实施、验证与仓库事实更新 owner。', 'href': '/collaboration/tasks'},
            {'id': 'handoff', 'label': 'Handoff', 'status': handoff_status, 'summary': f"Open={counts.get('openHandoffCount', 0)} / total={counts.get('handoffCount', 0)}", 'href': '/collaboration'},
            {'id': 'hermesagent', 'label': 'HermesAgent', 'status': hermes_status, 'summary': f"blocked={counts.get('blockedHandoffCount', 0)} / unreviewed={counts.get('unreviewedArtifactCount', 0)}", 'href': '/collaboration/tasks'},
            {'id': 'runtime-snapshot', 'label': 'Runtime Snapshot', 'status': snapshot_status, 'summary': '当前协作轮次的 runtime-local 阶段与状态。', 'href': '/collaboration'},
            {'id': 'closeout', 'label': 'Closeout', 'status': closeout_status, 'summary': f"pending={counts.get('pendingCloseoutCount', 0)} / total={counts.get('closeoutCount', 0)}", 'href': '/operations#harness'},
            {'id': 'repo-truth', 'label': 'Repo Truth', 'status': repo_truth_status, 'summary': f"missing writeback={counts.get('missingWritebackCount', 0)}", 'href': '/governance/graph'},
        ],
        'edges': [
            {'from': 'codex', 'to': 'handoff', 'label': 'produce handoff'},
            {'from': 'handoff', 'to': 'hermesagent', 'label': 'operations review'},
            {'from': 'hermesagent', 'to': 'runtime-snapshot', 'label': 'runtime acceptance signal'},
            {'from': 'runtime-snapshot', 'to': 'closeout', 'label': 'closeout writeback'},
            {'from': 'closeout', 'to': 'repo-truth', 'label': 'durable evidence'},
        ],
        'evidenceJumps': summary.get('evidenceJumps') or [],
    }


@api.route('/collaboration/summary')
def collaboration_summary():
    return jsonify(_build_collaboration_summary_view())


@api.route('/collaboration/graph-projection')
def collaboration_graph_projection():
    return jsonify(_build_collaboration_graph_projection())


@api.route('/collaboration/loops')
def collaboration_loops():
    loops = _build_collaboration_loops()
    if not loops:
        return jsonify([])
    return jsonify(loops)


@api.route('/collaboration/loops/<loop_id>')
def collaboration_loop_detail(loop_id):
    loops = _build_collaboration_loops()
    loop = next((item for item in loops if item.get('loopId') == loop_id), None)
    if not loop:
        return jsonify({'error': 'Loop not found', 'loopId': loop_id}), 404
    return jsonify(loop)


@api.route('/collaboration/memory-candidates')
def collaboration_memory_candidates():
    loop = _build_enriched_promise_review_loop()
    if not loop:
        return jsonify([])
    return jsonify(loop.get('memoryCandidates') or [])


@api.route('/collaboration/feedback-inputs')
def collaboration_feedback_inputs():
    loop = _build_enriched_promise_review_loop()
    if not loop:
        return jsonify([])
    return jsonify(loop.get('feedbackInputs') or [])


@api.route('/collaboration/memory-candidates/<path:candidate_id>/decision', methods=['POST'])
def collaboration_memory_candidate_decision(candidate_id):
    payload = request.get_json(silent=True) or {}
    action = str(payload.get('action') or '').strip().lower()
    action_to_status = {
        'confirm': 'accepted',
        'reject': 'rejected',
        'defer': 'deferred',
    }
    if action not in action_to_status:
        return jsonify({'error': 'action must be one of: confirm, reject, defer'}), 400

    candidate = _find_memory_candidate(candidate_id)
    if not candidate:
        return jsonify({'error': 'Memory candidate not found', 'candidateId': candidate_id}), 404

    record = {
        'recordId': f'memory-decision:{candidate_id}:{int(time.time() * 1000)}',
        'candidateId': candidate_id,
        'loopId': candidate.get('loopId'),
        'promiseId': candidate.get('promiseId'),
        'flowmindCandidateId': candidate.get('flowmindCandidateId'),
        'candidateType': candidate.get('candidateType'),
        'sourcePlane': candidate.get('sourcePlane'),
        'proposedTarget': candidate.get('proposedTarget'),
        'authorityPlane': candidate.get('targetMemoryPlane') or 'host-memory',
        'action': action,
        'status': action_to_status[action],
        'note': str(payload.get('note') or '').strip(),
        'evidenceRefs': _normalize_evidence_refs(payload.get('evidenceRefs')),
        'recordedBy': str(payload.get('recordedBy') or 'operator'),
        'recordedAt': _now_iso(),
    }
    if not _append_shared_context_row(_LOOP_SURFACE_MEMORY_DECISIONS, record):
        return jsonify({'error': 'Failed to persist memory candidate decision'}), 500

    candidate = _apply_memory_candidate_decision(candidate, record)
    return jsonify(candidate), 201


@api.route('/collaboration/feedback-inputs/<path:input_id>/submit', methods=['POST'])
def collaboration_feedback_input_submit(input_id):
    payload = request.get_json(silent=True) or {}
    input_item = _find_feedback_input(input_id)
    if not input_item:
        return jsonify({'error': 'Feedback input not found', 'inputId': input_id}), 404

    mode = str(payload.get('mode') or input_item.get('inputMode') or '').strip().lower()
    if mode not in ('explicit_event', 'event_annotation'):
        return jsonify({'error': 'mode must be explicit_event or event_annotation'}), 400

    event_type = str(payload.get('eventType') or input_item.get('defaultEventType') or '').strip().lower()
    allowed_event_types = [str(item).lower() for item in (input_item.get('allowedEventTypes') or [])]
    if allowed_event_types and event_type not in allowed_event_types:
        return jsonify({'error': 'eventType is not allowed for this feedback input', 'allowedEventTypes': allowed_event_types}), 400

    reason = str(payload.get('reason') or '').strip()
    if not reason:
        return jsonify({'error': 'reason is required'}), 400

    record = {
        'recordId': f'feedback-input:{input_id}:{int(time.time() * 1000)}',
        'inputId': input_id,
        'loopId': input_item.get('loopId'),
        'promiseId': input_item.get('promiseId'),
        'flowmindCandidateId': input_item.get('flowmindCandidateId'),
        'targetInstanceId': input_item.get('targetInstanceId'),
        'targetSourceAgent': input_item.get('targetSourceAgent'),
        'mode': mode,
        'eventType': event_type,
        'payload': {
            'reason': reason,
            'note': str(payload.get('note') or '').strip(),
            'evidenceRefs': _normalize_evidence_refs(payload.get('evidenceRefs')),
        },
        'status': 'submitted-local',
        'writeBoundary': 'local-operator-queue',
        'recordedBy': str(payload.get('recordedBy') or 'operator'),
        'recordedAt': _now_iso(),
    }
    if not _append_shared_context_row(_LOOP_SURFACE_FEEDBACK_INPUTS, record):
        return jsonify({'error': 'Failed to persist feedback input'}), 500

    input_item = _apply_feedback_input_submission(input_item, record)
    return jsonify(input_item), 201

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

def _load_cron_jobs():
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

    return jobs


@api.route('/cron/list')
def cron_list():
    return jsonify(_load_cron_jobs())


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


def _load_skills_inventory():
    now = time.time()
    if _skills_cache['data'] is not None and (now - _skills_cache['timestamp']) < _skills_cache_ttl:
        return _skills_cache['data']

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
    return result


@api.route('/skills/list')
def skills_list():
    return jsonify(_load_skills_inventory())


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

def _load_alerts():
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

    return alerts


@api.route('/alerts/list')
def alerts_list():
    return jsonify(_load_alerts())


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

    gw_data = _load_gateway_status()

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


@api.route('/tasks/request-bus')
def tasks_request_bus():
    requests = _load_task_bus_requests()
    return jsonify({
        'requests': requests,
        'stats': _task_bus_stats(requests),
        'lanes': _task_bus_lane_groups(requests),
        'automation': _task_bus_automation_stats(requests),
    })


@api.route('/tasks/request-bus/<ack_id>/transition', methods=['POST'])
def tasks_request_bus_transition(ack_id):
    payload = request.get_json(silent=True) or {}
    next_status = str(payload.get('status') or '').strip().lower()
    actor = str(payload.get('actor') or 'operator').strip() or 'operator'
    note = str(payload.get('note') or '').strip()
    result = payload.get('result')
    error = payload.get('error')
    if not next_status:
        return jsonify({'error': 'status is required'}), 400

    item, err = _transition_task_bus_request(
        ack_id,
        next_status,
        actor=actor,
        note=note,
        result=result,
        error=error,
    )
    if err == 'Request not found':
        return jsonify({'error': err, 'ack_id': ack_id}), 404
    if err:
        return jsonify({'error': err, 'ack_id': ack_id}), 400
    return jsonify(item), 200


@api.route('/tasks/request-bus/<ack_id>/automation-state', methods=['POST'])
def tasks_request_bus_automation_state(ack_id):
    payload = request.get_json(silent=True) or {}
    next_state = str(payload.get('automationState') or '').strip().lower()
    actor = str(payload.get('actor') or 'operator').strip() or 'operator'
    approval = str(payload.get('approval') or '').strip()
    rollback_rule = str(payload.get('rollbackRule') or '').strip()
    note = str(payload.get('note') or '').strip()
    evidence_refs = payload.get('evidenceRefs')
    if not next_state:
        return jsonify({'error': 'automationState is required'}), 400

    item, err = _promote_task_bus_request(
        ack_id,
        next_state,
        actor=actor,
        approval=approval,
        rollback_rule=rollback_rule,
        evidence_refs=evidence_refs,
        note=note,
    )
    if err == 'Request not found':
        return jsonify({'error': err, 'ack_id': ack_id}), 404
    if err:
        return jsonify({'error': err, 'ack_id': ack_id}), 400
    return jsonify(item), 200


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


@api.route('/runtime/host-health')
def runtime_host_health():
    return jsonify(_load_host_health())


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


def _ops_status_rank(status):
    if status in ('failed', 'missing', 'expired', 'invalid-schema'):
        return 3
    if status in ('degraded', 'missing-auth', 'auth-required', 'unknown', 'inactive', 'disabled'):
        return 2
    return 1


def _ops_pick_status(*statuses):
    picked = 'healthy'
    best_rank = _ops_status_rank(picked)
    for status in statuses:
        if not status:
            continue
        rank = _ops_status_rank(status)
        if rank > best_rank:
            picked = status
            best_rank = rank
    return picked


def _build_operations_next_hop(alert_status, connectivity_status, integrations_status, isolation_status, task_registry_status, host_health_status, harness_status, runbook_status, env_map_status, backup_recovery_status, recovery_path_status, cron_status, skills_status, memory_status):
    if alert_status == 'failed' or connectivity_status == 'failed':
        return {
            'href': '/operations/alerts',
            'label': '先处理告警与连接异常',
            'reason': '当前异常优先级高于对象库存巡检。',
        }
    if host_health_status == 'failed' or host_health_status == 'degraded':
        return {
            'href': '/operations#host-health',
            'label': '检查 Host Health',
            'reason': '当前宿主磁盘/内存或 gateway 证据存在异常，需要先确认运行宿主是否稳定。',
        }
    if harness_status == 'degraded':
        return {
            'href': '/operations#harness',
            'label': '检查 Harness Readiness',
            'reason': '当前 Harness 的 trace / critic / closeout / worktree 使用链仍存在缺口，需要先确认基础执行治理是否成立。',
        }
    if env_map_status == 'degraded':
        return {
            'href': '/operations#env-map',
            'label': '检查 Env Map',
            'reason': '当前部署根、runtime 根、API base 或 provider mode 映射存在缺口，先确认控制面的环境地图是否一致。',
        }
    if integrations_status == 'failed':
        return {
            'href': '/operations#providers',
            'label': '先处理 Provider Health',
            'reason': '集成能力面存在 provider 失败，需要先恢复外部能力。',
        }
    if task_registry_status == 'degraded':
        return {
            'href': '/operations#task-registry',
            'label': '检查 Task Registry',
            'reason': '当前 request bus 内存在失败、超时或卡住对象，需要先清理 task registry。',
        }
    if integrations_status == 'degraded':
        return {
            'href': '/operations#credentials',
            'label': '检查凭证与 Source 绑定',
            'reason': '集成能力面已降级，优先确认凭证缺失或 source 覆盖不足。',
        }
    if isolation_status == 'degraded':
        return {
            'href': '/operations#isolation',
            'label': '检查角色与记忆隔离',
            'reason': '当前需要先确认 role registry、credential ownership、memory boundary 或 runbook visibility 是否存在缺口。',
        }
    if runbook_status == 'degraded':
        return {
            'href': '/operations#runbooks',
            'label': '补齐 Runbooks',
            'reason': '当前控制面对象已可见，但仍有缺失 runbook，需要先补齐 operator 的下一跳指引。',
        }
    if backup_recovery_status == 'degraded':
        return {
            'href': '/operations#backup-recovery',
            'label': '检查 Backup / Recovery',
            'reason': '当前备份覆盖或恢复路径存在缺口，需要先确认 deploy backups、mirror manifest 与恢复 runbook 是否齐全。',
        }
    if recovery_path_status == 'degraded':
        return {
            'href': '/operations#recovery-paths',
            'label': '检查 Recovery Paths',
            'reason': '当前恢复路径对象存在未就绪项，需要先确认触发条件、步骤与回退前置证据是否完整。',
        }
    if cron_status == 'degraded':
        return {
            'href': '/operations/cron',
            'label': '检查定时任务状态',
            'reason': '存在暂停或未恢复的例行机制。',
        }
    if skills_status == 'unknown':
        return {
            'href': '/operations/skills',
            'label': '补齐技能库存基线',
            'reason': '当前技能库存为空，先确认 host 技能目录与装载情况。',
        }
    if memory_status == 'unknown':
        return {
            'href': '/operations/team-memory',
            'label': '检查 Team Memory',
            'reason': '当前没有可消费记忆文件，先确认 shared context 与角色记忆可见性。',
        }
    return {
        'href': '/operations#sources',
        'label': '继续巡检集成能力面',
        'reason': '当前基础对象健康，可继续沿 source / tool / credential 深入核对。',
    }


def _build_operations_summary():
    skills_payload = _load_skills_inventory() or {'skills': [], 'total': 0, 'categories': []}
    cron_jobs = _load_cron_jobs() or []
    memories = _load_overview_memories() or []
    alerts = _load_alerts() or []
    gateway = _load_gateway_status() or {'gateway_state': 'unknown', 'platforms': {}, 'running': False, 'active_agents': 0}
    integrations = get_executor_provider().get_summary() or {}
    boundary = _build_executor_boundary_view()
    isolation = _build_operations_isolation_view()
    task_registry = _build_operations_task_registry_view()
    automation = _build_operations_automation_maturity_view()
    host_health = _build_operations_host_health_view()
    harness = _build_operations_harness_view()
    runbooks = _build_operations_runbooks_view()
    env_map = _build_operations_env_map_view()
    backup_recovery = _build_operations_backup_recovery_view()
    recovery_paths = _build_operations_recovery_paths_view(env_map=env_map, backup_recovery=backup_recovery)

    skill_total = skills_payload.get('total', 0) or 0
    skill_categories = skills_payload.get('categories', []) or []
    top_skill_category = skill_categories[0]['display'] if skill_categories else '未分类'
    skills_status = 'healthy' if skill_total > 0 else 'unknown'

    cron_total = len(cron_jobs)
    cron_active = len([job for job in cron_jobs if job.get('active') is not False and job.get('paused') is not True])
    cron_paused = max(cron_total - cron_active, 0)
    cron_status = 'healthy'
    if cron_total == 0:
        cron_status = 'unknown'
    elif cron_paused > 0:
        cron_status = 'degraded'

    memory_total = len(memories)
    memory_status = 'healthy' if memory_total > 0 else 'unknown'

    critical_alerts = len([alert for alert in alerts if alert.get('level') == 'critical'])
    warning_alerts = len([alert for alert in alerts if alert.get('level') == 'warning'])
    info_alerts = len([alert for alert in alerts if alert.get('level') == 'info'])
    alert_status = 'healthy'
    if critical_alerts > 0:
        alert_status = 'failed'
    elif warning_alerts > 0:
        alert_status = 'degraded'

    platforms = gateway.get('platforms', {}) or {}
    platform_total = len(platforms)
    platform_connected = 0
    platform_warning = 0
    platform_failed = 0
    for platform_state in platforms.values():
        state = platform_state.get('state', 'unknown')
        if state == 'connected':
            platform_connected += 1
        elif state in ('error', 'fatal'):
            platform_failed += 1
        else:
            platform_warning += 1

    connectivity_status = 'healthy'
    gateway_state = gateway.get('gateway_state', 'unknown')
    if gateway_state != 'running' or platform_failed > 0:
        connectivity_status = 'failed'
    elif platform_warning > 0 or platform_total == 0:
        connectivity_status = 'degraded'

    integration_source_count = integrations.get('sourceCount', 0) or 0
    integration_tool_count = integrations.get('toolCount', 0) or 0
    integration_credential_count = integrations.get('credentialCount', 0) or 0
    integration_provider_count = integrations.get('providerCount', 0) or 0
    integration_missing_credentials = integrations.get('missingCredentialCount', 0) or 0
    integration_failed_providers = integrations.get('failedProviderCount', 0) or 0
    integrations_status = 'healthy'
    if integration_failed_providers > 0:
        integrations_status = 'failed'
    elif integration_missing_credentials > 0 or integration_source_count == 0:
        integrations_status = 'degraded'
    integrations_status = _ops_pick_status(integrations_status, boundary.get('status'))

    overall_status = _ops_pick_status(
        alert_status,
        connectivity_status,
        integrations_status,
        isolation.get('status'),
        task_registry.get('status'),
        automation.get('status'),
        host_health.get('status'),
        harness.get('status'),
        runbooks.get('status'),
        env_map.get('status'),
        backup_recovery.get('status'),
        recovery_paths.get('status'),
        cron_status,
        skills_status,
        memory_status,
    )

    next_hop = _build_operations_next_hop(
        alert_status,
        connectivity_status,
        integrations_status,
        isolation.get('status'),
        task_registry.get('status'),
        host_health.get('status'),
        harness.get('status'),
        runbooks.get('status'),
        env_map.get('status'),
        backup_recovery.get('status'),
        recovery_paths.get('status'),
        cron_status,
        skills_status,
        memory_status,
    )

    families = [
        {
            'key': 'skills',
            'title': 'Skills Inventory',
            'icon': '⚡',
            'status': skills_status,
            'count': skill_total,
            'summary': f'{len(skill_categories)} categories · top {top_skill_category}',
            'href': '/operations/skills',
        },
        {
            'key': 'cron',
            'title': 'Cron / Routines',
            'icon': '⏰',
            'status': cron_status,
            'count': cron_total,
            'summary': f'{cron_active} active · {cron_paused} paused',
            'href': '/operations/cron',
        },
        {
            'key': 'memory',
            'title': 'Team Memory',
            'icon': '📝',
            'status': memory_status,
            'count': memory_total,
            'summary': 'SOUL / memories / shared context visible',
            'href': '/operations/team-memory',
        },
        {
            'key': 'task-registry',
            'title': 'Task Registry',
            'icon': '📋',
            'status': task_registry.get('status', 'unknown'),
            'count': task_registry.get('counts', {}).get('total', 0),
            'summary': f'{task_registry.get("counts", {}).get("open", 0)} open · {task_registry.get("counts", {}).get("failed", 0)} failed · {task_registry.get("counts", {}).get("timedOut", 0)} timed out',
            'href': '/operations#task-registry',
        },
        {
            'key': 'automation',
            'title': 'Automation Maturity',
            'icon': '🤖',
            'status': automation.get('status', 'unknown'),
            'count': automation.get('counts', {}).get('tracked', 0),
            'summary': f'{automation.get("counts", {}).get("approved", 0)} approved · {automation.get("counts", {}).get("automated", 0)} automated · {automation.get("counts", {}).get("prototype", 0)} prototype',
            'href': '/operations#automation',
        },
        {
            'key': 'connectivity',
            'title': 'Platform Connectivity',
            'icon': '📡',
            'status': connectivity_status,
            'count': platform_total,
            'summary': f'gateway={gateway_state} · {platform_connected}/{platform_total} connected',
            'href': '/operations/alerts',
        },
        {
            'key': 'integrations',
            'title': 'Integrations Capability',
            'icon': '🔌',
            'status': integrations_status,
            'count': integration_source_count,
            'summary': f'{integration_tool_count} tools · {integration_provider_count} providers · {integration_missing_credentials} credential gaps',
            'href': '/operations#sources',
        },
        {
            'key': 'host-health',
            'title': 'Host Health',
            'icon': '🖥️',
            'status': host_health.get('status', 'unknown'),
            'count': host_health.get('counts', {}).get('evidenceSignals', 0),
            'summary': f'disk {host_health.get("diskStatus", "unknown")} · memory {host_health.get("memoryStatus", "unknown")} · alerts {host_health.get("counts", {}).get("alerts", 0)}',
            'href': '/operations#host-health',
        },
        {
            'key': 'harness',
            'title': 'Harness Readiness',
            'icon': '🧪',
            'status': harness.get('status', 'unknown'),
            'count': harness.get('counts', {}).get('totalTraces', 0),
            'summary': f'{harness.get("counts", {}).get("successCount", 0)} success · {harness.get("counts", {}).get("failureCount", 0)} failure · {harness.get("counts", {}).get("readinessHealthyCount", 0)} readiness green',
            'href': '/operations#harness',
        },
        {
            'key': 'env-map',
            'title': 'Env Map',
            'icon': '🗺️',
            'status': env_map.get('status', 'unknown'),
            'count': env_map.get('counts', {}).get('entryCount', 0),
            'summary': f'{env_map.get("counts", {}).get("configuredCount", 0)} configured · {env_map.get("counts", {}).get("missingCount", 0)} missing',
            'href': '/operations#env-map',
        },
        {
            'key': 'isolation',
            'title': 'Role / Memory Isolation',
            'icon': '🧱',
            'status': isolation.get('status', 'unknown'),
            'count': isolation.get('counts', {}).get('roleCount', 0),
            'summary': f'{isolation.get("counts", {}).get("credentialCount", 0)} credentials · {isolation.get("counts", {}).get("memoryBoundaryCount", 0)} memory planes · {isolation.get("counts", {}).get("missingRunbookCount", 0)} runbook gaps',
            'href': '/operations#isolation',
        },
        {
            'key': 'boundary',
            'title': 'Readonly Boundary',
            'icon': '🧭',
            'status': boundary.get('status', 'unknown'),
            'count': boundary.get('totalTaskTypeCount', 0),
            'summary': f'mode={boundary.get("providerMode", "unknown")} · {boundary.get("allowedTaskTypeCount", 0)} allowed · {boundary.get("forbiddenTaskTypeCount", 0)} forbidden',
            'href': '/operations#boundary',
        },
        {
            'key': 'backup-recovery',
            'title': 'Backup / Recovery',
            'icon': '🛟',
            'status': backup_recovery.get('status', 'unknown'),
            'count': backup_recovery.get('counts', {}).get('surfaceCount', 0),
            'summary': f'{backup_recovery.get("counts", {}).get("healthyCount", 0)} healthy · {backup_recovery.get("counts", {}).get("degradedCount", 0)} degraded',
            'href': '/operations#backup-recovery',
        },
        {
            'key': 'recovery-paths',
            'title': 'Recovery Paths',
            'icon': '🧭',
            'status': recovery_paths.get('status', 'unknown'),
            'count': recovery_paths.get('counts', {}).get('pathCount', 0),
            'summary': f'{recovery_paths.get("counts", {}).get("readyCount", 0)} ready · {recovery_paths.get("counts", {}).get("degradedCount", 0)} degraded',
            'href': '/operations#recovery-paths',
        },
        {
            'key': 'runbooks',
            'title': 'Runbooks',
            'icon': '📚',
            'status': runbooks.get('status', 'unknown'),
            'count': runbooks.get('counts', {}).get('runbookCount', 0),
            'summary': f'{runbooks.get("counts", {}).get("visibleCount", 0)} visible · {runbooks.get("counts", {}).get("missingCount", 0)} missing',
            'href': '/operations#runbooks',
        },
    ]

    return {
        'status': overall_status,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'briefing': {
            'label': 'Sprint 1 aggregation lane',
            'title': '运营对象摘要已收口到单一聚合层',
            'summary': '技能、定时任务、记忆、平台连接与 executor capability plane 现在通过同一份 summary payload 暴露给 Operations 页面。',
        },
        'nextHop': next_hop,
        'metrics': {
            'skillsCount': skill_total,
            'cronCount': cron_total,
            'memoryCount': memory_total,
            'integrationCount': integration_source_count,
            'alertCount': len(alerts),
            'taskRegistryCount': task_registry.get('counts', {}).get('total', 0),
            'automationCount': automation.get('counts', {}).get('tracked', 0),
            'toolCount': integration_tool_count,
            'credentialCount': integration_credential_count,
            'providerCount': integration_provider_count,
            'hostHealthCount': host_health.get('counts', {}).get('evidenceSignals', 0),
            'harnessCount': harness.get('counts', {}).get('totalTraces', 0),
            'envMapCount': env_map.get('counts', {}).get('entryCount', 0),
            'isolationCount': isolation.get('counts', {}).get('roleCount', 0),
            'boundaryCount': 1,
            'backupRecoveryCount': backup_recovery.get('counts', {}).get('surfaceCount', 0),
            'recoveryPathCount': recovery_paths.get('counts', {}).get('pathCount', 0),
            'runbookCount': runbooks.get('counts', {}).get('runbookCount', 0),
        },
        'alerts': {
            'status': alert_status,
            'total': len(alerts),
            'critical': critical_alerts,
            'warning': warning_alerts,
            'info': info_alerts,
        },
        'families': families,
    }


@api.route('/operations/summary')
def operations_summary():
    return jsonify(_build_operations_summary())


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


def _build_executor_boundary_view():
    provider = get_executor_provider()
    mode = get_provider_mode()
    capabilities = provider.get_capabilities() or {}
    policy = _read_shared_context_json(_EXECUTOR_READONLY_POLICY, default={}) or {}

    owners = policy.get('owners') if isinstance(policy.get('owners'), dict) else {}
    preconditions = policy.get('preconditions') if isinstance(policy.get('preconditions'), list) else []
    wave1_allowed = policy.get('wave1_allowed') if isinstance(policy.get('wave1_allowed'), list) else []
    wave2_completed = policy.get('wave2_completed') if isinstance(policy.get('wave2_completed'), list) else []
    forbidden_now = policy.get('forbidden_now') if isinstance(policy.get('forbidden_now'), list) else []
    status = 'healthy' if policy else 'unknown'
    if mode != 'http':
        status = _ops_pick_status(status, 'degraded')

    return {
        'status': status,
        'providerMode': mode,
        'modeLabel': capabilities.get('modeLabel', mode),
        'scopeId': capabilities.get('scopeId', ''),
        'policyPath': _EXECUTOR_READONLY_POLICY,
        'version': policy.get('version', ''),
        'date': policy.get('date', ''),
        'host': policy.get('host', ''),
        'readonlyMode': policy.get('mode', ''),
        'owners': owners,
        'preconditions': preconditions,
        'allowedTaskTypes': wave1_allowed,
        'completedTaskTypes': wave2_completed,
        'forbiddenTaskTypes': forbidden_now,
        'allowedTaskTypeCount': len(wave1_allowed),
        'completedTaskTypeCount': len(wave2_completed),
        'forbiddenTaskTypeCount': len(forbidden_now),
        'totalTaskTypeCount': len(wave1_allowed) + len(wave2_completed) + len(forbidden_now),
        'capabilities': capabilities,
        'executionBoundary': {
            'canonicalAuthority': [
                'CrazyAgentsManage owns operator-facing source onboarding and capability visibility.',
                'HermesAgent owns runtime lifecycle, trace, and task state.',
                'FlowMind owns candidate / truth / review / provenance authority.',
                'executor owns external capability execution only.',
            ],
            'localWritableTargets': [
                'Operations source / provider / credential inventory',
                'Executor capability visibility and refresh actions',
                'Repo-tracked readonly delegation policy projection',
            ],
            'humanGateActions': [
                'source onboarding',
                'credential bind / unbind',
                'readonly delegation lane selection',
                'provider health review',
            ],
            'forbiddenMutations': [
                'Do not let executor overwrite repo truth.',
                'Do not let executor overwrite Hermes runtime truth.',
                'Do not let executor overwrite FlowMind governance truth.',
                'Do not let executor directly mutate shared-context/tech-radar.json.',
            ],
        },
        'runbooks': [
            'docs/design/executor-integration/README.md',
            'docs/design/executor-integration/hermes-executor-readonly-delegation-spec-v1-2026-05-19.md',
            'docs/02-engineering/harness/hermes-executor-readonly-delegation-spec-freeze-closeout-2026-05-19.md',
        ],
    }


@api.route('/operations/integrations/boundary')
def ops_integrations_boundary():
    return jsonify(_build_executor_boundary_view())


def _build_operations_isolation_view():
    provider = get_executor_provider()
    credentials = provider.get_credentials() or []

    runbook_paths = [
        'docs/codex-hermes-role-design.md',
        'docs/02-engineering/harness/HARNESS-ENTRY.md',
        'docs/02-engineering/harness/HERMESAGENT-ENTRY.md',
        'docs/design/executor-integration/README.md',
    ]
    runbooks = []
    missing_runbooks = 0
    for rel_path in runbook_paths:
        resolved = _resolve_repo_artifact_path(rel_path)
        exists = _safe_exists(resolved)
        if not exists:
            missing_runbooks += 1
        runbooks.append({
            'id': rel_path,
            'name': Path(rel_path).name,
            'path': rel_path,
            'exists': exists,
            'sourceRoot': str(resolved.parent if exists else resolved.parent),
            'status': 'visible' if exists else 'missing',
        })

    hermes_home = _get_hermes_home()
    repo_soul_root = _resolve_repo_artifact_path('soul')
    repo_harness_root = _resolve_repo_artifact_path('harness')
    repo_shared_context_root = _resolve_repo_artifact_path('shared-context')
    repo_omx_root = _resolve_repo_artifact_path('.omx')

    memory_boundaries = [
        {
            'id': 'host-runtime-memory',
            'name': 'Host Runtime Memory',
            'owner': 'HermesAgent',
            'boundary': 'host-memory-plane',
            'status': 'healthy' if _safe_exists(hermes_home / 'SOUL.md') else 'degraded',
            'writeBoundary': 'Hermes runtime / memory maintenance',
            'roots': [str(hermes_home / 'SOUL.md'), str(hermes_home / 'memories')],
            'fileCount': (1 if _safe_exists(hermes_home / 'SOUL.md') else 0) + _safe_glob_count(hermes_home / 'memories', '*.md'),
            'notes': 'Host-side memory remains outside repo truth and should not be treated as canonical governance memory.',
        },
        {
            'id': 'repo-soul-mirror',
            'name': 'Repo Soul Mirror',
            'owner': 'CrazyAgentsManage',
            'boundary': 'repo-tracked-operator-memory',
            'status': 'healthy' if _safe_exists(repo_soul_root) else 'degraded',
            'writeBoundary': 'repo-tracked soul files only',
            'roots': [str(repo_soul_root)],
            'fileCount': _safe_glob_count(repo_soul_root, '*.md') + _safe_glob_count(repo_soul_root / 'agents', '*.md'),
            'notes': 'Tracked soul artifacts support operator semantics, but they do not replace host runtime memory.',
        },
        {
            'id': 'shared-context-plane',
            'name': 'Shared Context Plane',
            'owner': 'Crazy Operations',
            'boundary': 'repo-tracked-shared-operator-state',
            'status': 'healthy' if _safe_exists(repo_shared_context_root) else 'degraded',
            'writeBoundary': 'task bus / loop surface / monitored runtime outputs',
            'roots': [str(repo_shared_context_root)],
            'fileCount': _safe_glob_count(repo_shared_context_root, '*') + _safe_glob_count(repo_shared_context_root / 'agent-requests', '*.jsonl'),
            'notes': 'shared-context is repo-tracked shared operator state, not FlowMind truth and not host-local OMX state.',
        },
        {
            'id': 'repo-harness-facts',
            'name': 'Repo Harness Facts',
            'owner': 'Codex',
            'boundary': 'durable-repo-learning-layer',
            'status': 'healthy' if _safe_exists(repo_harness_root) else 'degraded',
            'writeBoundary': 'harness closeout / repo facts only',
            'roots': [str(repo_harness_root)],
            'fileCount': _safe_glob_count(repo_harness_root, '*.md') + _safe_glob_count(repo_harness_root / 'trace', '*.json'),
            'notes': 'harness/ and docs/ stay canonical repository facts; do not collapse them into .omx or host memory.',
        },
        {
            'id': 'omx-runtime-local',
            'name': 'OMX Runtime Local',
            'owner': 'OMX runtime',
            'boundary': 'runtime-local-state',
            'status': 'healthy' if _safe_exists(repo_omx_root) else 'unknown',
            'writeBoundary': '.omx is session-local only',
            'roots': [str(repo_omx_root)],
            'fileCount': _safe_glob_count(repo_omx_root, '*'),
            'notes': '.omx is runtime-local substrate and must not be promoted into shared project truth.',
        },
    ]

    missing_credentials = [item for item in credentials if str(item.get('status') or '') in ('missing', 'expired', 'invalid')]
    credential_ownership = []
    for item in credentials:
        status = str(item.get('status') or 'unknown')
        owner = 'executor capability plane'
        owner_role = 'Crazy / Operations'
        if item.get('targetId') == 'flowmind':
            owner = 'FlowMind bridge'
            owner_role = 'FlowMind'
        credential_ownership.append({
            'id': item.get('id', ''),
            'provider': item.get('provider', ''),
            'targetId': item.get('targetId', ''),
            'targetType': item.get('targetType', ''),
            'status': status,
            'owner': owner,
            'ownerRole': owner_role,
            'valueKind': item.get('valueKind', ''),
            'slot': item.get('slot', ''),
            'impactCount': item.get('impactCount', 0) or 0,
            'lastCheckedAt': item.get('lastCheckedAt'),
            'notes': 'Executor-bound credentials stay inside the capability plane and must not be mistaken for FlowMind truth authority.',
        })

    roles = [
        {
            'id': 'codex',
            'name': 'Codex',
            'lane': 'development',
            'status': 'healthy',
            'primaryScopes': ['repo code', 'docs', 'harness', 'tests'],
            'memoryBoundary': 'repo facts + runtime-local OMX',
            'credentialBoundary': 'developer-local tooling only',
            'runbooks': ['docs/codex-hermes-role-design.md', 'docs/02-engineering/harness/HARNESS-ENTRY.md'],
        },
        {
            'id': 'hermesagent',
            'name': 'HermesAgent',
            'lane': 'operations',
            'status': 'healthy',
            'primaryScopes': ['runtime host', 'cron', 'session operations', 'operator acceptance'],
            'memoryBoundary': 'host runtime memory plane',
            'credentialBoundary': 'host runtime / platform credentials',
            'runbooks': ['docs/codex-hermes-role-design.md', 'docs/02-engineering/harness/HERMESAGENT-ENTRY.md'],
        },
        {
            'id': 'flowmind',
            'name': 'FlowMind',
            'lane': 'governance truth',
            'status': 'healthy',
            'primaryScopes': ['candidate', 'truth', 'review', 'provenance'],
            'memoryBoundary': 'upstream governance memory only',
            'credentialBoundary': 'bridge / governance service auth',
            'runbooks': ['docs/02-engineering/harness/hermes-flowmind-compatibility-matrix-2026-04-30.md'],
        },
        {
            'id': 'executor',
            'name': 'executor',
            'lane': 'capability plane',
            'status': 'healthy' if get_provider_mode() == 'http' else 'degraded',
            'primaryScopes': ['external read capability', 'source catalog', 'tool catalog', 'bindings'],
            'memoryBoundary': 'no governance memory ownership',
            'credentialBoundary': 'source bindings / secrets only',
            'runbooks': ['docs/design/executor-integration/README.md'],
        },
    ]

    credential_status = 'healthy' if credentials and not missing_credentials else ('degraded' if missing_credentials else 'unknown')
    memory_status = 'healthy'
    if any(item.get('status') == 'degraded' for item in memory_boundaries):
        memory_status = 'degraded'
    elif not any(item.get('fileCount', 0) for item in memory_boundaries):
        memory_status = 'unknown'
    runbook_status = 'healthy' if missing_runbooks == 0 else 'degraded'
    role_status = 'healthy' if len(roles) >= 4 else 'degraded'
    status = _ops_pick_status(role_status, credential_status, memory_status, runbook_status)

    return {
        'status': status,
        'roleStatus': role_status,
        'credentialStatus': credential_status,
        'memoryStatus': memory_status,
        'runbookStatus': runbook_status,
        'roleRegistry': roles,
        'credentialOwnership': credential_ownership,
        'memoryBoundaries': memory_boundaries,
        'runbooks': runbooks,
        'counts': {
            'roleCount': len(roles),
            'credentialCount': len(credential_ownership),
            'missingCredentialCount': len(missing_credentials),
            'memoryBoundaryCount': len(memory_boundaries),
            'runbookCount': len(runbooks),
            'missingRunbookCount': missing_runbooks,
        },
    }


@api.route('/operations/isolation')
def operations_isolation():
    return jsonify(_build_operations_isolation_view())


def _build_operations_task_registry_view():
    requests = _load_task_bus_requests()
    lanes = _task_bus_lane_groups(requests)
    open_items = [item for item in requests if str(item.get('status') or '') not in ('delivered', 'failed', 'timed_out')]
    failed_items = [item for item in requests if str(item.get('status') or '') == 'failed']
    timed_out_items = [item for item in requests if str(item.get('status') or '') == 'timed_out']
    started_items = [item for item in requests if str(item.get('status') or '') == 'started']
    owners = {}
    for item in requests:
        owner = str(item.get('owner') or item.get('target') or 'unassigned')
        bucket = owners.setdefault(owner, {'owner': owner, 'total': 0, 'open': 0, 'pending': 0, 'failed': 0})
        bucket['total'] += 1
        if item in open_items:
            bucket['open'] += 1
        if str(item.get('status') or '') in ('accepted', 'routed', 'queued', 'started'):
            bucket['pending'] += 1
        if item in failed_items or item in timed_out_items:
            bucket['failed'] += 1
    status = 'unknown'
    if requests:
        status = 'healthy'
        if failed_items or timed_out_items:
            status = 'degraded'
    return {
        'status': status,
        'counts': {
            'total': len(requests),
            'open': len(open_items),
            'failed': len(failed_items),
            'timedOut': len(timed_out_items),
            'working': len(started_items),
        },
        'lanes': lanes,
        'owners': sorted(owners.values(), key=lambda item: (-item['open'], item['owner'])),
        'items': requests[:20],
        'runbooks': [
            'docs/06-agent-ops/three-state-protocol.md',
            'shared-context/agent-requests/requests.jsonl',
            'shared-context/agent-requests/events.jsonl',
        ],
    }


def _build_operations_automation_maturity_view():
    requests = _load_task_bus_requests()
    stats = _task_bus_automation_stats(requests)
    promoted = [
        item for item in requests
        if str(item.get('automation_state') or 'prototype') in ('rehearsed', 'approved-for-automation', 'automated')
    ]
    status = 'unknown'
    if requests:
        status = 'healthy' if promoted else 'degraded'
    return {
        'status': status,
        'counts': {
            'tracked': len(requests),
            'prototype': stats.get('prototype', 0),
            'rehearsed': stats.get('rehearsed', 0),
            'approved': stats.get('approved-for-automation', 0),
            'automated': stats.get('automated', 0),
        },
        'items': promoted[:20],
        'runbooks': [
            'docs/02-engineering/external-analysis/shann-holmberg-hermes-control-room-and-crazy-adaptation-2026-05-21.md',
            'shared-context/agent-requests/events.jsonl',
        ],
    }


def _build_operations_host_health_view():
    host = _load_host_health() or {}
    gateway = _load_gateway_status() or {}
    alerts = _load_alerts() or []
    disk_status = host.get('disk', {}).get('status', 'unknown')
    memory_status = host.get('memory', {}).get('status', 'unknown')
    gateway_state = gateway.get('gateway_state', 'unknown')
    alert_count = len(alerts)
    status = _ops_pick_status(host.get('status'), 'degraded' if gateway_state != 'running' else 'healthy')
    return {
        'status': status,
        'diskStatus': disk_status,
        'memoryStatus': memory_status,
        'gatewayState': gateway_state,
        'counts': {
            'alerts': alert_count,
            'platforms': len(gateway.get('platforms', {}) or {}),
            'activeAgents': gateway.get('active_agents', 0) or 0,
            'evidenceSignals': 4,
        },
        'host': host,
        'gateway': gateway,
        'alerts': alerts[:20],
        'runbooks': [
            'docs/02-engineering/harness/HARNESS-ENTRY.md',
            'scripts/governance/live-deploy-sync.manifest.json',
            'scripts/runtime/sync_hermes_script_mirror.py',
        ],
    }


def _build_operations_harness_view():
    repo_harness_root = _pick_harness_root() / 'harness'
    closeout_dir = repo_harness_root / 'closeouts'
    success_dir = repo_harness_root / 'trace' / 'successes'
    failure_dir = repo_harness_root / 'trace' / 'failures'
    memory_root = repo_harness_root / 'memory'
    docs_root = _resolve_repo_artifact_path('docs/02-engineering/harness')

    success_files = [p for p in _safe_sorted_paths(success_dir, '*.json') if p.name != 'TEMPLATE.json']
    failure_files = [p for p in _safe_sorted_paths(failure_dir, '*.json') if p.name != 'TEMPLATE.json']
    closeout_files = [p for p in _safe_sorted_paths(closeout_dir, '*.json') if p.name != 'TEMPLATE.json']
    latest_success_path = success_files[-1] if success_files else None
    latest_failure_path = failure_files[-1] if failure_files else None
    latest_closeout_path = closeout_files[-1] if closeout_files else None
    latest_success = _read_optional_json(latest_success_path) if latest_success_path else None
    latest_failure = _read_optional_json(latest_failure_path) if latest_failure_path else None
    latest_closeout = _read_optional_json(latest_closeout_path) if latest_closeout_path else None
    latest_success_mtime = latest_success_path.stat().st_mtime if latest_success_path else 0
    latest_failure_mtime = latest_failure_path.stat().st_mtime if latest_failure_path else 0

    readiness = [
        {
            'id': 'trace-layer',
            'name': 'Trace Layer',
            'status': 'healthy' if _safe_exists(success_dir) and _safe_exists(failure_dir) else 'degraded',
            'evidence': [str(success_dir), str(failure_dir)],
            'notes': 'Structured success/failure traces should always land in harness/trace.',
        },
        {
            'id': 'critic-layer',
            'name': 'Critic Layer',
            'status': 'healthy' if _safe_exists(_resolve_repo_artifact_path('scripts/harness-critic.cjs')) and _safe_exists(memory_root / 'failure-patterns.md') and _safe_exists(memory_root / 'procedural.md') else 'degraded',
            'evidence': [
                'scripts/harness-critic.cjs',
                'harness/memory/failure-patterns.md',
                'harness/memory/procedural.md',
            ],
            'notes': 'Critic must be able to analyze failures and write back durable memory.',
        },
        {
            'id': 'closeout-layer',
            'name': 'Closeout Layer',
            'status': 'healthy' if _safe_exists(_resolve_repo_artifact_path('scripts/harness-closeout-writeback.cjs')) and _safe_exists(docs_root / 'HARNESS-ENTRY.md') and _safe_exists(docs_root / 'harness-governance-report.md') and _safe_exists(closeout_dir) else 'degraded',
            'evidence': [
                'scripts/harness-closeout-writeback.cjs',
                'harness/closeouts/*.json',
                'docs/02-engineering/harness/HARNESS-ENTRY.md',
                'docs/02-engineering/harness/harness-governance-report.md',
            ],
            'notes': 'Success rounds should pass governance before closeout writeback completes.',
        },
        {
            'id': 'worktree-layer',
            'name': 'Worktree Bootstrap',
            'status': 'healthy' if _safe_exists(_resolve_repo_artifact_path('scripts/worktree/create-agent-worktree.sh')) and _safe_exists(docs_root / 'WORKTREE-BOOTSTRAP.md') else 'degraded',
            'evidence': [
                'scripts/worktree/create-agent-worktree.sh',
                'docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md',
            ],
            'notes': 'Independent worktree bootstrap remains part of the shared harness contract.',
        },
    ]

    healthy_readiness = len([item for item in readiness if item.get('status') == 'healthy'])
    failure_newer_than_success = latest_failure_mtime > latest_success_mtime if latest_failure_mtime and latest_success_mtime else False
    closeout_trace_ids = set()
    for payload in [(_read_optional_json(path) or {}) for path in closeout_files]:
        trace = payload.get('trace') if isinstance(payload.get('trace'), dict) else {}
        trace_id = str(trace.get('id') or '').strip()
        if trace_id:
            closeout_trace_ids.add(trace_id)
    unclosed_trace_count = len([
        record_id for record_id in [str((latest_success or {}).get('id') or '').strip()] + [str((latest_failure or {}).get('id') or '').strip()]
        if record_id and record_id not in closeout_trace_ids
    ])

    status = 'healthy'
    if healthy_readiness < len(readiness):
        status = 'degraded'
    elif failure_newer_than_success:
        status = 'degraded'
    elif unclosed_trace_count > 0:
        status = 'degraded'
    elif not success_files:
        status = 'unknown'

    return {
        'status': status,
        'counts': {
            'successCount': len(success_files),
            'failureCount': len(failure_files),
            'closeoutCount': len(closeout_files),
            'totalTraces': len(success_files) + len(failure_files),
            'readinessHealthyCount': healthy_readiness,
            'pendingCloseoutCount': unclosed_trace_count,
        },
        'latestSuccess': latest_success,
        'latestFailure': latest_failure,
        'latestCloseout': latest_closeout,
        'latestSuccessPath': str(latest_success_path) if latest_success_path else '',
        'latestFailurePath': str(latest_failure_path) if latest_failure_path else '',
        'latestCloseoutPath': str(latest_closeout_path) if latest_closeout_path else '',
        'failureNewerThanSuccess': failure_newer_than_success,
        'readiness': readiness,
        'runbooks': [
            'docs/02-engineering/harness/HARNESS-ENTRY.md',
            'docs/02-engineering/harness/CROSS-REVIEW-PROCESS.md',
            'docs/02-engineering/harness/WORKTREE-BOOTSTRAP.md',
            'docs/02-engineering/harness/HARNESS-CAPABILITY-MAPPING.md',
        ],
        'policy': {
            'defaultEntry': 'Non-trivial rounds must close via harness-closeout-writeback.',
            'directTracePolicy': 'record-success.cjs / record-failure.cjs are internal trace writers; direct use requires --allow-trivial-direct plus --probe-reason, and forged closeout env is rejected.',
        },
        'commands': [
            'node scripts/harness-closeout-writeback.cjs --status success --message \"Round completed\" --critic-write-back --json',
            'node scripts/harness-closeout-writeback.cjs --status failed --message \"Round failed\" --stage verification --json',
            'node scripts/harness-critic.cjs --json',
            'python3 scripts/check_harness_closeout_chain.py',
            'scripts/worktree/create-agent-worktree.sh --agent codex --lane shared --topic <topic>',
        ],
    }


def _build_operations_runbooks_view():
    runbook_defs = [
        ('task-registry', 'Task Registry Runbook', 'docs/06-agent-ops/three-state-protocol.md'),
        ('runtime-host', 'Harness Entry', 'docs/02-engineering/harness/HARNESS-ENTRY.md'),
        ('hermes-ops', 'HermesAgent Entry', 'docs/02-engineering/harness/HERMESAGENT-ENTRY.md'),
        ('executor-boundary', 'Executor Integration', 'docs/design/executor-integration/README.md'),
        ('role-design', 'Role Design', 'docs/codex-hermes-role-design.md'),
    ]
    items = []
    visible = 0
    for runbook_id, name, rel_path in runbook_defs:
        resolved = _resolve_repo_artifact_path(rel_path)
        exists = _safe_exists(resolved)
        if exists:
            visible += 1
        items.append({
            'id': runbook_id,
            'name': name,
            'path': rel_path,
            'exists': exists,
            'status': 'visible' if exists else 'missing',
        })
    status = 'healthy' if visible == len(items) else 'degraded'
    return {
        'status': status,
        'counts': {
            'runbookCount': len(items),
            'visibleCount': visible,
            'missingCount': len(items) - visible,
        },
        'items': items,
    }


def _build_operations_env_map_view():
    provider_mode = get_provider_mode()
    remote_cfg = _get_remote_config() or {}
    repo_root = _get_repo_root()
    runtime_root = _get_runtime_repo_root()
    deploy_root = _get_deploy_copy_root()
    hermes_home = _get_hermes_home()
    executor_url = os.environ.get('EXECUTOR_API_BASE_URL', 'http://127.0.0.1:4788').rstrip('/')
    flowmind_url = _get_flowmind_base_url()
    app_base = os.environ.get('APP_BASE_PATH', '').strip()

    entries = [
        {
            'id': 'repo-root',
            'name': 'Repo Root',
            'value': str(repo_root),
            'status': 'healthy' if _safe_exists(repo_root) else 'degraded',
            'owner': 'CrazyAgentsManage',
            'notes': 'Current shell reads product code from this root.',
        },
        {
            'id': 'runtime-root',
            'name': 'Runtime Repo Root',
            'value': str(runtime_root),
            'status': 'healthy' if _safe_exists(runtime_root) else 'degraded',
            'owner': 'ALI-HERMES runtime',
            'notes': 'Fallback root for deployed webui copies when repo-tracked facts live outside /opt shell copy.',
        },
        {
            'id': 'deploy-root',
            'name': 'Deploy Copy Root',
            'value': str(deploy_root),
            'status': 'healthy' if _safe_exists(deploy_root) else 'degraded',
            'owner': 'Crazy webui deploy shell',
            'notes': 'Public manage surface serves templates/static assets from this root.',
        },
        {
            'id': 'hermes-home',
            'name': 'Hermes Home',
            'value': str(hermes_home),
            'status': 'healthy' if _safe_exists(hermes_home) else 'degraded',
            'owner': 'HermesAgent',
            'notes': 'Host runtime state, memory, cron, and scripts live here.',
        },
        {
            'id': 'provider-mode',
            'name': 'Provider Mode',
            'value': provider_mode or 'unknown',
            'status': 'healthy' if provider_mode == 'http' else 'degraded',
            'owner': 'executor capability plane',
            'notes': 'sample mode is valid for local fallback but degraded for live capability-plane verification.',
        },
        {
            'id': 'executor-base-url',
            'name': 'Executor Base URL',
            'value': executor_url,
            'status': 'healthy' if executor_url else 'degraded',
            'owner': 'executor capability plane',
            'notes': 'Readonly capability calls route here when provider mode is http.',
        },
        {
            'id': 'flowmind-base-url',
            'name': 'FlowMind API Base URL',
            'value': flowmind_url,
            'status': 'healthy' if flowmind_url else 'degraded',
            'owner': 'FlowMind',
            'notes': 'Governance truth / trace / feedback bridge reads route here.',
        },
        {
            'id': 'remote-host-target',
            'name': 'Remote Host Target',
            'value': remote_cfg.get('host', ''),
            'status': 'healthy' if remote_cfg.get('host') else 'unknown',
            'owner': 'remote sync tooling',
            'notes': 'Tracked remote host config used by deploy/smoke scripts.',
        },
        {
            'id': 'app-base-path',
            'name': 'App Base Path',
            'value': app_base or '(auto)',
            'status': 'healthy',
            'owner': 'webui shell',
            'notes': 'If blank, BASE path is inferred from request path / forwarded prefix.',
        },
    ]
    drift_entries = []
    for item in entries:
        if item.get('status') == 'degraded':
            drift_entries.append({
                'id': item.get('id'),
                'name': item.get('name'),
                'value': item.get('value'),
                'reason': item.get('notes') or 'env entry degraded',
            })
    configured = len([item for item in entries if item.get('status') == 'healthy'])
    degraded = len(drift_entries)
    status = 'healthy' if degraded == 0 else 'degraded'
    return {
        'status': status,
        'entries': entries,
        'driftEntries': drift_entries,
        'counts': {
            'entryCount': len(entries),
            'configuredCount': configured,
            'missingCount': degraded,
            'driftCount': degraded,
        },
    }


def _build_operations_backup_recovery_view():
    deploy_backup_root = _get_deploy_copy_root() / '.deploy-backups'
    hermes_mirror_dir = _get_hermes_script_mirror_dir()
    mirror_manifest = hermes_mirror_dir / '.mirror-manifest.json'
    backup_root = _get_backup_root()
    operations_manual = _resolve_repo_artifact_path('docs/06-agent-ops/operations-manual.md')
    live_sync_closeout = _resolve_repo_artifact_path('docs/02-engineering/harness/crazy-live-webui-sync-closeout-2026-05-03.md')
    memory_backup_count = _safe_glob_count(_get_hermes_home() / 'memory', '*.bak') + _safe_glob_count(_get_hermes_home() / 'memory', '*.md.bak')
    deploy_backup_dirs = _safe_sorted_paths(deploy_backup_root, '*')
    backup_snapshots = _safe_sorted_paths(backup_root, '*')

    surfaces = [
        {
            'id': 'deploy-copy-backups',
            'name': 'Deploy Copy Backups',
            'status': 'healthy' if deploy_backup_dirs else 'degraded',
            'location': str(deploy_backup_root),
            'count': len(deploy_backup_dirs),
            'recoveryPath': 'Use sync_live_deploy_copy plus .deploy-backups rollback directory.',
        },
        {
            'id': 'script-mirror-manifest',
            'name': 'Hermes Script Mirror',
            'status': 'healthy' if _safe_exists(mirror_manifest) else 'degraded',
            'location': str(mirror_manifest),
            'count': 1 if _safe_exists(mirror_manifest) else 0,
            'recoveryPath': 'Use scripts/runtime/sync_hermes_script_mirror.py to restore tracked mirrors.',
        },
        {
            'id': 'backup-root',
            'name': 'Host Backup Root',
            'status': 'healthy' if backup_snapshots else 'degraded',
            'location': str(backup_root),
            'count': len(backup_snapshots),
            'recoveryPath': 'Use operations-manual backup / restore commands against dated backup root.',
        },
        {
            'id': 'memory-edit-backups',
            'name': 'Memory Edit Backups',
            'status': 'healthy' if memory_backup_count > 0 else 'unknown',
            'location': str(_get_hermes_home() / 'memory'),
            'count': memory_backup_count,
            'recoveryPath': 'Restore *.md.bak files when local memory edits need rollback.',
        },
        {
            'id': 'runbook-coverage',
            'name': 'Recovery Runbooks',
            'status': 'healthy' if _safe_exists(operations_manual) and _safe_exists(live_sync_closeout) else 'degraded',
            'location': 'docs/06-agent-ops/operations-manual.md + docs/02-engineering/harness/crazy-live-webui-sync-closeout-2026-05-03.md',
            'count': int(_safe_exists(operations_manual)) + int(_safe_exists(live_sync_closeout)),
            'recoveryPath': 'Follow repo-tracked backup and deploy sync closeout runbooks before host-side manual recovery.',
        },
    ]
    healthy = len([item for item in surfaces if item.get('status') == 'healthy'])
    degraded = len([item for item in surfaces if item.get('status') == 'degraded'])
    status = 'healthy' if degraded == 0 else 'degraded'
    coverage = {
        'deployCopyBackups': len(deploy_backup_dirs),
        'hostBackupSnapshots': len(backup_snapshots),
        'memoryEditBackups': memory_backup_count,
        'mirrorManifestPresent': _safe_exists(mirror_manifest),
        'runbookCoverage': int(_safe_exists(operations_manual)) + int(_safe_exists(live_sync_closeout)),
    }
    return {
        'status': status,
        'surfaces': surfaces,
        'coverage': coverage,
        'counts': {
            'surfaceCount': len(surfaces),
            'healthyCount': healthy,
            'degradedCount': degraded,
        },
        'runbooks': [
            'docs/06-agent-ops/operations-manual.md',
            'docs/02-engineering/harness/crazy-live-webui-sync-closeout-2026-05-03.md',
            'scripts/runtime/sync_hermes_script_mirror.py',
        ],
    }


def _build_operations_recovery_paths_view(env_map=None, backup_recovery=None):
    env_map = env_map or _build_operations_env_map_view()
    backup_recovery = backup_recovery or _build_operations_backup_recovery_view()
    surfaces = backup_recovery.get('surfaces') or []
    deploy_backup = next((item for item in surfaces if item.get('id') == 'deploy-copy-backups'), None)
    mirror_surface = next((item for item in surfaces if item.get('id') == 'script-mirror-manifest'), None)
    host_backup = next((item for item in surfaces if item.get('id') == 'backup-root'), None)
    memory_backup = next((item for item in surfaces if item.get('id') == 'memory-edit-backups'), None)

    paths = [
        {
            'id': 'deploy-copy-rollback',
            'name': 'Deploy Copy Rollback',
            'status': 'ready' if deploy_backup and deploy_backup.get('status') == 'healthy' else 'degraded',
            'trigger': 'public manage surface drift or static/template regression',
            'owner': 'Crazy webui deploy shell',
            'preconditions': [
                'deploy copy backup exists',
                'repo baseline can be re-synced',
            ],
            'recoveryPath': [
                'inspect /opt/crazyagentsmanage/.deploy-backups',
                'restore backup or rerun sync_live_deploy_copy',
                're-check public /manage surface and local 5002 route',
            ],
            'runbooks': [
                'docs/02-engineering/harness/crazy-live-webui-sync-closeout-2026-05-03.md',
                'scripts/governance/live-deploy-sync.manifest.json',
            ],
        },
        {
            'id': 'hermes-script-mirror-restore',
            'name': 'Hermes Script Mirror Restore',
            'status': 'ready' if mirror_surface and mirror_surface.get('status') == 'healthy' else 'degraded',
            'trigger': '~/.hermes/scripts drift or missing tracked mirror scripts',
            'owner': 'HermesAgent runtime',
            'preconditions': [
                '.mirror-manifest.json present',
                'repo-tracked script sources available under runtime repo root',
            ],
            'recoveryPath': [
                'inspect ~/.hermes/scripts/.mirror-manifest.json',
                'rerun scripts/runtime/sync_hermes_script_mirror.py',
                're-check mirrored script hashes and cron references',
            ],
            'runbooks': [
                'scripts/runtime/sync_hermes_script_mirror.py',
                'shared-context/hermes-script-mirror-manifest.json',
            ],
        },
        {
            'id': 'host-backup-restore',
            'name': 'Host Backup Restore',
            'status': 'ready' if host_backup and host_backup.get('status') == 'healthy' else 'degraded',
            'trigger': 'host-side state loss, corrupted Hermes data, or repo/runtime recovery',
            'owner': 'HermesAgent operations',
            'preconditions': [
                'dated host backup root exists',
                'operations manual backup commands remain visible',
            ],
            'recoveryPath': [
                'locate dated backup under backup root',
                'restore promises / learnings / memory assets',
                're-run operations smoke checks',
            ],
            'runbooks': [
                'docs/06-agent-ops/operations-manual.md',
            ],
        },
        {
            'id': 'memory-edit-rollback',
            'name': 'Memory Edit Rollback',
            'status': 'ready' if memory_backup and memory_backup.get('count', 0) > 0 else 'degraded',
            'trigger': 'local team-memory edit introduced incorrect content',
            'owner': 'Crazy operator',
            'preconditions': [
                '*.md.bak file exists under host memory plane',
            ],
            'recoveryPath': [
                'locate matching .md.bak artifact',
                'restore target memory file content',
                're-open Team Memory and verify preview',
            ],
            'runbooks': [
                'docs/06-agent-ops/operations-manual.md',
            ],
        },
    ]
    ready = len([item for item in paths if item.get('status') == 'ready'])
    degraded = len([item for item in paths if item.get('status') == 'degraded'])
    drift_count = env_map.get('counts', {}).get('driftCount', 0)
    status = 'healthy' if degraded == 0 and drift_count == 0 else 'degraded'
    return {
        'status': status,
        'paths': paths,
        'envDrift': env_map.get('driftEntries', []),
        'backupCoverage': backup_recovery.get('coverage', {}),
        'counts': {
            'pathCount': len(paths),
            'readyCount': ready,
            'degradedCount': degraded,
            'envDriftCount': drift_count,
        },
    }


def _build_operations_control_room_summary():
    return {
        'taskRegistry': _build_operations_task_registry_view(),
        'automationMaturity': _build_operations_automation_maturity_view(),
        'hostHealth': _build_operations_host_health_view(),
        'harness': _build_operations_harness_view(),
        'envMap': _build_operations_env_map_view(),
        'backupRecovery': _build_operations_backup_recovery_view(),
        'recoveryPaths': _build_operations_recovery_paths_view(),
        'runbooks': _build_operations_runbooks_view(),
    }


@api.route('/operations/task-registry')
def operations_task_registry():
    return jsonify(_build_operations_task_registry_view())


@api.route('/operations/automation-maturity')
def operations_automation_maturity():
    return jsonify(_build_operations_automation_maturity_view())


@api.route('/operations/host-health')
def operations_host_health():
    return jsonify(_build_operations_host_health_view())


@api.route('/operations/harness')
def operations_harness():
    return jsonify(_build_operations_harness_view())


@api.route('/operations/env-map')
def operations_env_map():
    return jsonify(_build_operations_env_map_view())


@api.route('/operations/backup-recovery')
def operations_backup_recovery():
    return jsonify(_build_operations_backup_recovery_view())


@api.route('/operations/recovery-paths')
def operations_recovery_paths():
    return jsonify(_build_operations_recovery_paths_view())


@api.route('/operations/runbooks')
def operations_runbooks():
    return jsonify(_build_operations_runbooks_view())


@api.route('/operations/control-room-summary')
def operations_control_room_summary():
    return jsonify(_build_operations_control_room_summary())


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
