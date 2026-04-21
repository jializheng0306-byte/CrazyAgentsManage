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
from flask import Blueprint, jsonify, request

api = Blueprint('api', __name__, url_prefix='/api')

_hermes_home = None
_remote_config = None
_skills_cache = {'data': None, 'timestamp': 0}
_skills_cache_ttl = 300
_overview_cache = {'data': None, 'timestamp': 0}
_overview_cache_ttl = 60
_local_db_cache = {}
_local_db_lock = threading.Lock()


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


# ═══════════════════════════════════════════
# Overview APIs
# ═══════════════════════════════════════════

@api.route('/overview/stats')
def overview_stats():
    now = time.time()
    if _overview_cache['data'] is not None and (now - _overview_cache['timestamp']) < _overview_cache_ttl:
        return jsonify(_overview_cache['data'])

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

    _overview_cache['data'] = stats
    _overview_cache['timestamp'] = now
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
