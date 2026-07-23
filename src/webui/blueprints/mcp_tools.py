"""MCP Tools API — projects Hermes mcp_servers.json + tool listing.

Read-only projection of MCP instances and their tools.
"""

import json
import os
from pathlib import Path
from flask import Blueprint, jsonify

bp = Blueprint('mcp_tools', __name__, url_prefix='/api/v2/mcp-tools')


def _get_hermes_home():
    return Path(os.environ.get('HERMES_HOME', os.path.expanduser('~/.hermes')))


@bp.route('')
@bp.route('/')
def list_mcp_instances():
    """List MCP instances from mcp_servers.json."""
    home = _get_hermes_home()
    config_path = home / 'mcp_servers.json'
    if not config_path.exists():
        return jsonify({'instances': [], 'total': 0, 'read_only': True,
                        'note': f'mcp_servers.json not found at {config_path}'})
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({'error': str(e)}), 500
    instances = []
    if isinstance(config, dict):
        for name, cfg in config.items():
            if isinstance(cfg, dict):
                instances.append({
                    'id': name, 'name': name,
                    'command': cfg.get('command'),
                    'args': cfg.get('args', []),
                    'env': list(cfg.get('env', {}).keys()) if isinstance(cfg.get('env'), dict) else [],
                    'read_only': True,
                })
    return jsonify({'instances': instances, 'total': len(instances), 'read_only': True})


@bp.route('/<instance_id>/tools')
def list_instance_tools(instance_id):
    """List tools for an MCP instance (placeholder — requires MCP protocol call)."""
    return jsonify({
        'instance_id': instance_id,
        'tools': [],
        'note': 'Tool listing requires MCP protocol handshake — not yet implemented',
        'read_only': True,
    })
