"""Action Types API — projects DSL kind=action entries (10 entries).

Action types carry input/output/authority_profile — key for execution governance.
"""

from flask import Blueprint, jsonify
from .fmd_client import list_dsl_entries, get_dsl_entry, make_cache, cached

bp = Blueprint('action_types', __name__, url_prefix='/api/v2/action-types')
_CACHE = make_cache()
_CACHE_TTL = 60


@bp.route('')
@bp.route('/')
def list_action_types():
    def produce():
        entries = list_dsl_entries(kind='action')
        return {
            'total': len(entries),
            'items': [{
                'id': e['id'], 'title': e['title'], 'owner': e['owner'],
                'status': e['status'], 'evidence_class': e['evidence_class'],
                'input': e.get('frontmatter', {}).get('input', []),
                'output': e.get('frontmatter', {}).get('output', []),
                'authority_profile': e.get('frontmatter', {}).get('authority_profile', {}),
            } for e in entries],
            'read_only': True,
        }
    return jsonify(cached(_CACHE, _CACHE_TTL, produce))


@bp.route('/<path:entry_id>')
def get_action_type(entry_id):
    entry = get_dsl_entry(entry_id)
    if not entry or entry.get('kind') != 'action':
        return jsonify({'error': 'not found', 'entry_id': entry_id}), 404
    return jsonify(entry)
