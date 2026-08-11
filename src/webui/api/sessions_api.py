"""
Hermes Web UI -- Sessions API endpoints.

GET /api/sessions/list          -- Session index with pagination
GET /api/sessions/detail/<id>   -- Session detail with messages
GET /api/sessions/search        -- FTS5 full-text search
GET /api/sessions/tree/<id>     -- Sub-session tree
GET /api/sessions/stats         -- Session statistics
"""
import logging

from api.hermes_adapter import adapter
from api.helpers import j, bad

logger = logging.getLogger(__name__)


def handle_sessions_list(handler, params=None):
    limit = int(params.get("limit", [50])[0]) if params else 50
    offset = int(params.get("offset", [0])[0]) if params else 0
    source = params.get("source", [None])[0] if params else None
    if source == "":
        source = None
    sessions = adapter.get_sessions_list(limit=limit, offset=offset, source=source)
    j(handler, {"status": "ok", "data": sessions})


def handle_sessions_detail(handler, session_id, params=None):
    session = adapter.get_session_detail(session_id)
    if not session:
        bad(handler, "Session not found", status=404)
        return
    j(handler, {"status": "ok", "data": session})


def handle_sessions_search(handler, params=None):
    if not params or "q" not in params:
        bad(handler, "Missing required parameter: q")
        return
    query = params["q"][0]
    limit = int(params.get("limit", [20])[0]) if params else 20
    results = adapter.search_messages(query, limit=limit)
    j(handler, {"status": "ok", "data": results})


def handle_sessions_tree(handler, session_id, params=None):
    depth = int(params.get("depth", [5])[0]) if params else 5
    tree = adapter.get_session_tree(session_id, depth=depth)
    if not tree:
        bad(handler, "Session not found", status=404)
        return
    j(handler, {"status": "ok", "data": tree})


def handle_sessions_stats(handler, params=None):
    stats = adapter.get_session_stats()
    j(handler, {"status": "ok", "data": stats})
