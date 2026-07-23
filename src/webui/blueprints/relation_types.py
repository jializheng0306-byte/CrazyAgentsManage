"""Relation Types API — projects DSL kind=relation entries."""

from flask import Blueprint, jsonify
from .fmd_client import list_dsl_entries, get_dsl_entry, make_cache, cached

bp = Blueprint('relation_types', __name__, url_prefix='/api/v2/relation-types')
_CACHE = make_cache()
_CACHE_TTL = 60


@bp.route('')
@bp.route('/')
def list_relation_types():
    def produce():
        entries = list_dsl_entries(kind='relation')
        return {
            'total': len(entries),
            'items': [{'id': e['id'], 'title': e['title'], 'owner': e['owner'],
                       'status': e['status']} for e in entries],
            'read_only': True,
        }
    return jsonify(cached(_CACHE, _CACHE_TTL, produce))
