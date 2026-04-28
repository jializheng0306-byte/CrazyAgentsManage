"""
Hermes Web UI -- Overview API endpoints.

GET /api/overview/stats  -- Aggregated statistics from all data sources
GET /api/overview/teams  -- Team directory listing
GET /api/overview/memories -- Memory files listing
"""
import logging

from api.hermes_adapter import adapter
from api.helpers import j

logger = logging.getLogger(__name__)


def handle_overview_stats(handler, params=None):
    stats = adapter.get_overview_stats()
    j(handler, {"status": "ok", "data": stats})


def handle_overview_teams(handler, params=None):
    teams = adapter.get_teams()
    j(handler, {"status": "ok", "data": teams})


def handle_overview_memories(handler, params=None):
    teams = adapter.get_teams()
    memories = []
    for team in teams:
        team_mem = adapter.get_team_memory(team["name"])
        if team_mem:
            for fname, content in team_mem.get("shared", {}).items():
                memories.append({
                    "team": team["name"],
                    "type": "shared",
                    "file": fname,
                    "preview": content[:200] if content else "",
                })
            for role, files in team_mem.get("roles", {}).items():
                for fname, content in files.items():
                    memories.append({
                        "team": team["name"],
                        "type": "role",
                        "role": role,
                        "file": fname,
                        "preview": content[:200] if content else "",
                    })
    j(handler, {"status": "ok", "data": memories})
