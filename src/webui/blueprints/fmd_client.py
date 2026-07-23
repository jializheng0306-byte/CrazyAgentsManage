"""Shared client for accessing FlowMindDeploy ontology data.

Two channels (mirroring existing api.py patterns):
1. File direct-read: _FLOWMIND_ROOT / DSL / OKF directories
2. HTTP via mcp-server: _safe_flowmind_request

All access is READ-ONLY. CAM never writes truth (Invariant 1).
"""

import json
import os
import time
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

import yaml

# ── FMD path constants (mirrors api.py L6527-6530) ──
_FLOWMIND_ROOT = Path(__file__).resolve().parents[3] / '..' / 'FlowMindDeploy'
_DSL_DIR = _FLOWMIND_ROOT / 'packages' / 'ontology' / 'semantic-dsl'
_OKF_DIR = _FLOWMIND_ROOT / 'docs' / 'okf'

# ── HTTP channel (mirrors api.py L1657-1694) ──
def _get_flowmind_base_url():
    return os.environ.get('FLOWMIND_API_BASE_URL', 'http://127.0.0.1:3001').rstrip('/')


def _get_flowmind_api_key():
    return os.environ.get('FLOWMIND_API_KEY', 'flowmind-dev-token')


def flowmind_request(path, query=None, method='GET', data=None):
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


def safe_flowmind_request(path, query=None, method='GET', data=None, default=None):
    try:
        return flowmind_request(path, query=query, method=method, data=data)
    except (urlerror.URLError, urlerror.HTTPError, TimeoutError,
            json.JSONDecodeError, OSError):
        return default


# ── DSL file direct-read ──
KIND_DIRS = {
    'object': 'objects',
    'action': 'actions',
    'constraint': 'constraints',
    'context': 'contexts',
    'relation': 'relations',
    'risk': 'risks',
}


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file. Returns (dict, body)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.startswith('---'):
            return {}, content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        fm = yaml.safe_load(parts[1]) or {}
        return fm, parts[2]
    except Exception:
        return {}, ''


def list_dsl_entries(kind=None):
    """List DSL entries, optionally filtered by kind. Returns list of dicts."""
    entries = []
    kinds = [kind] if kind else list(KIND_DIRS.keys())
    for k in kinds:
        subdir = KIND_DIRS.get(k, k)
        d = _DSL_DIR / subdir
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix != '.md':
                continue
            fm, body = parse_frontmatter(f)
            entries.append({
                'kind': fm.get('kind', k),
                'id': fm.get('id', f.stem),
                'version': fm.get('version'),
                'title': fm.get('title', ''),
                'owner': fm.get('owner', ''),
                'status': fm.get('status', ''),
                'evidence_class': fm.get('evidence_class', ''),
                'aliases': fm.get('aliases', []),
                'filepath': str(f.relative_to(_FLOWMIND_ROOT)) if _FLOWMIND_ROOT.exists() else str(f),
                'frontmatter': fm,
            })
    return entries


def get_dsl_entry(entry_id):
    """Get a single DSL entry by id. Returns dict or None."""
    for k in KIND_DIRS:
        subdir = KIND_DIRS[k]
        d = _DSL_DIR / subdir
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.suffix != '.md':
                continue
            fm, body = parse_frontmatter(f)
            if fm.get('id') == entry_id or f.stem == entry_id:
                return {
                    'kind': fm.get('kind', k),
                    'id': fm.get('id', f.stem),
                    'version': fm.get('version'),
                    'title': fm.get('title', ''),
                    'owner': fm.get('owner', ''),
                    'status': fm.get('status', ''),
                    'evidence_class': fm.get('evidence_class', ''),
                    'aliases': fm.get('aliases', []),
                    'fields': fm.get('fields', []),
                    'input': fm.get('input', []),
                    'output': fm.get('output', []),
                    'authority_profile': fm.get('authority_profile', {}),
                    'g0_mapping': fm.get('g0_mapping', ''),
                    'frontmatter': fm,
                    'body': body,
                    'filepath': str(f),
                }
    return None


def count_dsl_by_kind():
    """Return {kind: count} summary."""
    result = {}
    for k, subdir in KIND_DIRS.items():
        d = _DSL_DIR / subdir
        result[k] = len([f for f in d.iterdir() if f.suffix == '.md']) if d.exists() else 0
    return result


def count_okf():
    """Count OKF projection files across all subdirs."""
    total = 0
    for sub in ['objects', 'actions', 'constraints', 'contexts', 'relations', 'risks']:
        subdir = _OKF_DIR / sub
        if subdir.exists():
            total += len([f for f in subdir.iterdir() if f.suffix == '.md'])
    return total


# ── Cache helpers ──
def make_cache():
    return {'data': None, 'timestamp': 0}


def cached(cache, ttl, producer):
    """Return cached data if fresh, else call producer() and cache it."""
    now = time.time()
    if cache['data'] is not None and (now - cache['timestamp']) < ttl:
        return cache['data']
    cache['data'] = producer()
    cache['timestamp'] = now
    return cache['data']
