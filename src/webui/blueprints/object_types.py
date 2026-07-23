"""Object Types API — projects DSL kind=object entries.

Read-only projection of FlowMindDeploy object-type DSL (31 entries).
"""

from flask import Blueprint, jsonify

from .fmd_client import list_dsl_entries, get_dsl_entry, make_cache, cached

bp = Blueprint('object_types', __name__, url_prefix='/api/v2/object-types')

_CACHE = make_cache()
_CACHE_TTL = 60


@bp.route('')
@bp.route('/')
def list_object_types():
    def produce():
        entries = list_dsl_entries(kind='object')
        return {
            'total': len(entries),
            'items': [{
                'id': e['id'], 'title': e['title'], 'owner': e['owner'],
                'status': e['status'], 'evidence_class': e['evidence_class'],
                'fields': e.get('frontmatter', {}).get('fields', []),
            } for e in entries],
            'read_only': True,
        }
    return jsonify(cached(_CACHE, _CACHE_TTL, produce))


@bp.route('/<path:entry_id>')
def get_object_type(entry_id):
    entry = get_dsl_entry(entry_id)
    if not entry or entry.get('kind') != 'object':
        return jsonify({'error': 'not found', 'entry_id': entry_id}), 404
    return jsonify(entry)
