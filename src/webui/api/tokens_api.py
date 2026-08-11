"""
Hermes Web UI -- Token management API endpoints.

GET /api/tokens/stats       -- Token usage statistics
GET /api/tokens/by-provider -- Token usage by billing provider
GET /api/tokens/by-model    -- Token usage by model
GET /api/tokens/trend       -- Token usage trend (daily)
GET /api/tokens/recent      -- Recent token usage records
"""
import logging

from api.hermes_adapter import adapter
from api.helpers import j

logger = logging.getLogger(__name__)


def handle_tokens_stats(handler, params=None):
    stats = adapter.get_token_stats()
    j(handler, {"status": "ok", "data": stats})


def handle_tokens_by_provider(handler, params=None):
    stats = adapter.get_token_stats()
    j(handler, {"status": "ok", "data": stats.get("by_provider", [])})


def handle_tokens_by_model(handler, params=None):
    stats = adapter.get_token_stats()
    j(handler, {"status": "ok", "data": stats.get("by_model", [])})


def handle_tokens_trend(handler, params=None):
    conn = adapter.get_db_connection()
    if not conn:
        j(handler, {"status": "ok", "data": []})
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DATE(started_at) as date, "
            "SUM(input_tokens) as inp, SUM(output_tokens) as out, "
            "SUM(cost_usd) as cost, COUNT(*) as sessions "
            "FROM sessions GROUP BY DATE(started_at) ORDER BY date DESC LIMIT 30"
        )
        trend = [dict(row) for row in cur.fetchall()]
        j(handler, {"status": "ok", "data": trend})
    except Exception:
        j(handler, {"status": "ok", "data": []})
    finally:
        conn.close()


def handle_tokens_recent(handler, params=None):
    limit = int(params.get("limit", [20])[0]) if params else 20
    conn = adapter.get_db_connection()
    if not conn:
        j(handler, {"status": "ok", "data": []})
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, source, model, title, started_at, ended_at, "
            "input_tokens, output_tokens, cost_usd "
            "FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        recent = [dict(row) for row in cur.fetchall()]
        j(handler, {"status": "ok", "data": recent})
    except Exception:
        j(handler, {"status": "ok", "data": []})
    finally:
        conn.close()
