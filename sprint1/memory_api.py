"""
Hermes Web UI -- Memory API endpoints.

GET /api/memory/teams          -- Team directory listing
GET /api/memory/team/<name>    -- Team memory content
GET /api/memory/role/<name>    -- Role-specific memory
POST /api/memory/update        -- Update memory file
GET /api/memory/search         -- Full-text search in memory files
"""
import logging

from api.hermes_adapter import adapter
from api.helpers import j, bad, read_body

logger = logging.getLogger(__name__)


def handle_memory_teams(handler, params=None):
    teams = adapter.get_teams()
    j(handler, {"status": "ok", "data": teams})


def handle_memory_team(handler, team_name, params=None):
    team = adapter.get_team_memory(team_name)
    if not team:
        bad(handler, "Team not found", status=404)
        return
    j(handler, {"status": "ok", "data": team})


def handle_memory_role(handler, role_name, params=None):
    teams = adapter.get_teams()
    role_data = {}
    for team in teams:
        team_mem = adapter.get_team_memory(team["name"])
        if team_mem and role_name in team_mem.get("roles", {}):
            role_data[team["name"]] = team_mem["roles"][role_name]
    if not role_data:
        bad(handler, "Role not found", status=404)
        return
    j(handler, {"status": "ok", "data": role_data})


def handle_memory_update(handler, params=None):
    body = read_body(handler)
    team = body.get("team")
    role = body.get("role")
    filename = body.get("filename")
    content = body.get("content")
    if not all([team, filename, content is not None]):
        bad(handler, "Missing required fields: team, filename, content")
        return
    if role:
        target_dir = adapter.memory_dir / team / role
    else:
        target_dir = adapter.memory_dir / team / "shared"
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / filename
    try:
        target_file.write_text(content, encoding='utf-8')
        j(handler, {"status": "ok", "message": f"Updated {target_file}"})
    except Exception as e:
        bad(handler, f"Failed to update: {e}", status=500)


def handle_memory_search(handler, params=None):
    if not params or "q" not in params:
        bad(handler, "Missing required parameter: q")
        return
    query = params["q"][0].lower()
    teams = adapter.get_teams()
    results = []
    for team in teams:
        team_mem = adapter.get_team_memory(team["name"])
        if not team_mem:
            continue
        for fname, content in team_mem.get("shared", {}).items():
            if query in content.lower():
                results.append({"team": team["name"], "type": "shared", "file": fname})
        for role, files in team_mem.get("roles", {}).items():
            for fname, content in files.items():
                if query in content.lower():
                    results.append({"team": team["name"], "type": "role", "role": role, "file": fname})
    j(handler, {"status": "ok", "data": results})
