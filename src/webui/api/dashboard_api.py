"""
Hermes Web UI -- Dashboard API endpoints.

GET /api/dashboard/stats          -- Dashboard statistics
GET /api/dashboard/sessions       -- Active sessions list
GET /api/dashboard/session/<id>   -- Session detail
GET /api/dashboard/gateway-status -- Gateway status
"""
import logging

from api.hermes_adapter import adapter
from api.helpers import j, bad

logger = logging.getLogger(__name__)


def handle_dashboard_stats(handler, params=None):
    session_stats = adapter.get_session_stats()
    gateway = adapter.get_gateway_status()
    cron_jobs = adapter.get_cron_jobs()
    active_platforms = {
        k: v for k, v in gateway.get("platforms", {}).items()
        if v.get("state") == "connected"
    }
    j(handler, {
        "status": "ok",
        "data": {
            "sessions": session_stats,
            "gateway_state": gateway.get("gateway_state", "unknown"),
            "active_platforms": len(active_platforms),
            "platforms": list(active_platforms.keys()),
            "cron_jobs": {
                "total": len(cron_jobs),
                "enabled": sum(1 for job in cron_jobs if job.get("enabled", True)),
            },
        },
    })


def handle_dashboard_sessions(handler, params=None):
    limit = int(params.get("limit", [50])[0]) if params else 50
    offset = int(params.get("offset", [0])[0]) if params else 0
    source = params.get("source", [None])[0] if params else None
    if source == "":
        source = None
    sessions = adapter.get_sessions_list(limit=limit, offset=offset, source=source)
    j(handler, {"status": "ok", "data": sessions})


def handle_dashboard_session_detail(handler, session_id, params=None):
    session = adapter.get_session_detail(session_id)
    if not session:
        bad(handler, "Session not found", status=404)
        return
    j(handler, {"status": "ok", "data": session})


def handle_dashboard_gateway_status(handler, params=None):
    status = adapter.get_gateway_status()
    j(handler, {"status": "ok", "data": status})
