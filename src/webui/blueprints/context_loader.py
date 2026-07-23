"""Context Loader API — proxies FlowMindDeploy context-pack bridge surface.

Read-only projection via FMD mcp-server HTTP channel.
"""

from flask import Blueprint, jsonify, request
from .fmd_client import safe_flowmind_request

bp = Blueprint('context_loader', __name__, url_prefix='/api/v2/context-loader')


@bp.route('/pack/<path:candidate_id>')
def get_context_pack(candidate_id):
    """Get context-pack for a candidate (proxies FMD bridge.context-pack)."""
    upstream = safe_flowmind_request(
        '/api/operator/context-pack',
        query={'candidateId': candidate_id},
        default=None,
    )
    if upstream is None:
        return jsonify({
            'candidateId': candidate_id,
            'error': 'FMD mcp-server unreachable',
            'read_only': True,
        }), 502
    if isinstance(upstream, dict) and isinstance(upstream.get('data'), dict):
        upstream = upstream['data']
    return jsonify({
        'candidateId': candidate_id,
        'contextPack': upstream,
        'read_only': True,
        'source': 'FlowMindDeploy mcp-server bridge.context-pack',
    })


@bp.route('/trace/<path:candidate_id>')
def get_trace(candidate_id):
    """Get trace events for a candidate (proxies FMD bridge.trace)."""
    upstream = safe_flowmind_request(
        '/api/operator/trace',
        query={'candidateId': candidate_id},
        default=None,
    )
    if upstream is None:
        return jsonify({'error': 'FMD mcp-server unreachable'}), 502
    return jsonify({
        'candidateId': candidate_id,
        'trace': upstream,
        'read_only': True,
        'source': 'FlowMindDeploy mcp-server bridge.trace',
    })
