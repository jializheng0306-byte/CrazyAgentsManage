"""Knowledge Networks API — DSL overview projection.

Projects FlowMindDeploy ontology (111 DSL entries) as knowledge-network summaries.
Read-only: CAM never writes truth (Invariant 1).
"""

from flask import Blueprint, jsonify

from .fmd_client import count_dsl_by_kind, count_okf, list_dsl_entries, make_cache, cached

bp = Blueprint('knowledge_networks', __name__, url_prefix='/api/v2/knowledge-networks')

_CACHE = make_cache()
_CACHE_TTL = 60

DOMAIN_STATS = {
    'D1_GTD': {'primary_consumer': 'QoderCLI/CodeBuddy'},
    'D2_MetaOntology': {'primary_consumer': 'QoderCLI/Codex'},
    'D3_OKF': {'primary_consumer': 'QoderCLI'},
    'D4_KG': {'primary_consumer': 'CodeBuddy'},
    'D5_Memory': {'primary_consumer': 'QoderCLI/CodeBuddy'},
    'Horizontal': {'primary_consumer': 'All agents'},
}


@bp.route('')
@bp.route('/')
def list_networks():
    """List knowledge networks (DSL overview by domain + kind)."""
    def produce():
        by_kind = count_dsl_by_kind()
        total = sum(by_kind.values())
        okf_total = count_okf()
        entries = list_dsl_entries()
        # Group by owner domain
        by_owner = {}
        for e in entries:
            owner = e.get('owner', 'unknown')
            by_owner.setdefault(owner, []).append({
                'id': e['id'], 'kind': e['kind'], 'title': e['title'],
                'status': e['status'], 'evidence_class': e['evidence_class'],
            })
        return {
            'total': total,
            'by_kind': by_kind,
            'okf_projections': okf_total,
            'domains': DOMAIN_STATS,
            'by_owner': by_owner,
            'read_only': True,
            'source': 'FlowMindDeploy ontology DSL (file direct-read)',
        }
    return jsonify(cached(_CACHE, _CACHE_TTL, produce))


@bp.route('/<path:entry_id>')
def get_network(entry_id):
    """Get a single DSL entry (knowledge network element)."""
    from .fmd_client import get_dsl_entry
    entry = get_dsl_entry(entry_id)
    if not entry:
        return jsonify({'error': 'not found', 'entry_id': entry_id}), 404
    return jsonify(entry)
