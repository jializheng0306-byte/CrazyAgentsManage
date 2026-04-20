"""
Hermes Web UI -- Alerts API endpoints.

GET /api/alerts/list             -- Alert list from gateway state
GET /api/alerts/platform-status  -- Platform connection status
GET /api/alerts/process-check    -- Gateway process health check
"""
import logging
import os

from api.hermes_adapter import adapter
from api.helpers import j
from pathlib import Path

logger = logging.getLogger(__name__)


def handle_alerts_list(handler, params=None):
    gateway = adapter.get_gateway_status()
    alerts = []
    if gateway.get("gateway_state") != "running":
        alerts.append({
            "level": "critical",
            "source": "gateway",
            "message": f"Gateway is {gateway.get('gateway_state', 'unknown')}",
            "timestamp": gateway.get("updated_at"),
        })
    for platform, info in gateway.get("platforms", {}).items():
        if info.get("state") != "connected":
            alerts.append({
                "level": "warning",
                "source": f"platform:{platform}",
                "message": f"Platform {platform} is {info.get('state', 'unknown')}: {info.get('error_message', '')}",
                "timestamp": info.get("updated_at"),
            })
    j(handler, {"status": "ok", "data": alerts})


def handle_alerts_platform_status(handler, params=None):
    gateway = adapter.get_gateway_status()
    platforms = gateway.get("platforms", {})
    status_list = []
    for name, info in platforms.items():
        status_list.append({
            "name": name,
            "state": info.get("state", "unknown"),
            "error": info.get("error_message"),
            "updated_at": info.get("updated_at"),
        })
    j(handler, {"status": "ok", "data": status_list})


def handle_alerts_process_check(handler, params=None):
    gateway = adapter.get_gateway_status()
    pid = gateway.get("pid")
    is_alive = False
    if pid:
        try:
            os.kill(pid, 0)
            is_alive = True
        except (ProcessLookupError, PermissionError, OSError):
            is_alive = False
    j(handler, {
        "status": "ok",
        "data": {
            "gateway_running": gateway.get("gateway_state") == "running",
            "pid": pid,
            "process_alive": is_alive,
        },
    })
