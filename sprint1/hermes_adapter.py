"""
Hermes Web UI -- Data source adapter for hermes-agent.

Provides a unified interface to read data from hermes-agent's
state.db, cron/jobs.json, gateway_state.json, and tools/registry.
All methods are read-only and wrapped in try/except.
"""
import json
import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_hermes_home() -> Path:
    try:
        from api.profiles import get_active_hermes_home
        return Path(get_active_hermes_home()).expanduser().resolve()
    except Exception:
        return Path(os.getenv('HERMES_HOME', str(Path.home() / '.hermes'))).expanduser().resolve()


class HermesAdapter:
    """Read-only adapter for hermes-agent data sources."""

    def __init__(self, hermes_home=None):
        if hermes_home:
            self._hermes_home = Path(hermes_home).expanduser().resolve()
        else:
            self._hermes_home = _get_hermes_home()

    @property
    def state_db_path(self):
        return self._hermes_home / 'state.db'

    @property
    def cron_jobs_path(self):
        return self._hermes_home / 'cron' / 'jobs.json'

    @property
    def gateway_state_path(self):
        return self._hermes_home / 'gateway_state.json'

    @property
    def memory_dir(self):
        return self._hermes_home / 'memory'

    @property
    def skills_dir(self):
        return self._hermes_home / 'skills'

    def get_db_connection(self):
        if not self.state_db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.state_db_path), timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            return conn
        except Exception:
            return None

    def get_session_stats(self):
        conn = self.get_db_connection()
        if not conn:
            return {"total_sessions": 0, "total_messages": 0, "total_tokens": 0}
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM sessions")
            total_sessions = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM messages")
            total_messages = cur.fetchone()['cnt']
            cur.execute(
                "SELECT COALESCE(SUM(input_tokens), 0) as inp, "
                "COALESCE(SUM(output_tokens), 0) as out FROM sessions"
            )
            row = cur.fetchone()
            total_tokens = row['inp'] + row['out']
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_tokens": total_tokens,
            }
        except Exception:
            return {"total_sessions": 0, "total_messages": 0, "total_tokens": 0}
        finally:
            conn.close()

    def get_sessions_list(self, limit=50, offset=0, source=None):
        conn = self.get_db_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            if source:
                cur.execute(
                    "SELECT id, source, model, title, started_at, ended_at, "
                    "message_count, tool_call_count, input_tokens, output_tokens "
                    "FROM sessions WHERE source = ? "
                    "ORDER BY started_at DESC LIMIT ? OFFSET ?",
                    (source, limit, offset),
                )
            else:
                cur.execute(
                    "SELECT id, source, model, title, started_at, ended_at, "
                    "message_count, tool_call_count, input_tokens, output_tokens "
                    "FROM sessions ORDER BY started_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def get_session_detail(self, session_id):
        conn = self.get_db_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, source, user_id, model, title, system_prompt, "
                "parent_session_id, started_at, ended_at, end_reason, "
                "message_count, tool_call_count, "
                "input_tokens, output_tokens, "
                "cache_read_tokens, cache_write_tokens, reasoning_tokens, "
                "billing_provider, billing_model, cost_usd, estimated_cost_usd "
                "FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            session = dict(row)
            cur.execute(
                "SELECT id, role, content, tool_call_id, tool_calls, tool_name, "
                "timestamp, token_count, finish_reason "
                "FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            )
            session['messages'] = [dict(m) for m in cur.fetchall()]
            return session
        except Exception:
            return None
        finally:
            conn.close()

    def search_messages(self, query, limit=20):
        conn = self.get_db_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT m.id, m.session_id, m.role, m.content, m.timestamp, "
                "s.title as session_title, s.source as session_source "
                "FROM messages_fts f "
                "JOIN messages m ON m.id = f.rowid "
                "JOIN sessions s ON s.id = m.session_id "
                "WHERE messages_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, limit),
            )
            return [dict(row) for row in cur.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def get_session_tree(self, session_id, depth=5):
        session = self.get_session_detail(session_id)
        if not session:
            return {}
        tree = {"session": session, "children": []}
        if depth <= 0:
            return tree
        conn = self.get_db_connection()
        if not conn:
            return tree
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM sessions WHERE parent_session_id = ?", (session_id,))
            for row in cur.fetchall():
                child = self.get_session_tree(row['id'], depth - 1)
                tree['children'].append(child)
            return tree
        except Exception:
            return tree
        finally:
            conn.close()

    def get_token_stats(self):
        conn = self.get_db_connection()
        if not conn:
            return {"total_input": 0, "total_output": 0, "total_cost": 0.0, "by_provider": [], "by_model": []}
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(SUM(input_tokens), 0) as total_input, "
                "COALESCE(SUM(output_tokens), 0) as total_output, "
                "COALESCE(SUM(cost_usd), 0) as total_cost FROM sessions"
            )
            row = cur.fetchone()
            cur.execute(
                "SELECT billing_provider, SUM(input_tokens) as inp, "
                "SUM(output_tokens) as out, SUM(cost_usd) as cost "
                "FROM sessions GROUP BY billing_provider ORDER BY cost DESC"
            )
            by_provider = [dict(r) for r in cur.fetchall()]
            cur.execute(
                "SELECT model, SUM(input_tokens) as inp, "
                "SUM(output_tokens) as out, SUM(cost_usd) as cost "
                "FROM sessions GROUP BY model ORDER BY cost DESC"
            )
            by_model = [dict(r) for r in cur.fetchall()]
            return {
                "total_input": row['total_input'],
                "total_output": row['total_output'],
                "total_cost": row['total_cost'],
                "by_provider": by_provider,
                "by_model": by_model,
            }
        except Exception:
            return {"total_input": 0, "total_output": 0, "total_cost": 0.0, "by_provider": [], "by_model": []}
        finally:
            conn.close()

    def get_cron_jobs(self):
        if not self.cron_jobs_path.exists():
            return []
        try:
            data = json.loads(self.cron_jobs_path.read_text(encoding='utf-8'))
            return data.get('jobs', [])
        except Exception:
            return []

    def get_gateway_status(self):
        if not self.gateway_state_path.exists():
            return {"gateway_state": "unknown", "platforms": {}}
        try:
            return json.loads(self.gateway_state_path.read_text(encoding='utf-8'))
        except Exception:
            return {"gateway_state": "unknown", "platforms": {}}

    def get_teams(self):
        if not self.memory_dir.exists():
            return []
        teams = []
        for team_dir in sorted(self.memory_dir.iterdir()):
            if team_dir.is_dir() and not team_dir.name.startswith('.'):
                teams.append({
                    "name": team_dir.name,
                    "path": str(team_dir),
                    "shared_files": self._list_md_files(team_dir / "shared"),
                    "roles": self._list_subdirs(team_dir),
                })
        return teams

    def get_team_memory(self, team_name):
        team_dir = self.memory_dir / team_name
        if not team_dir.exists():
            return None
        result = {"name": team_name, "shared": {}, "roles": {}}
        shared_dir = team_dir / "shared"
        if shared_dir.exists():
            for f in shared_dir.glob("*.md"):
                result["shared"][f.name] = f.read_text(encoding='utf-8')
        for role_dir in team_dir.iterdir():
            if role_dir.is_dir() and role_dir.name != "shared" and not role_dir.name.startswith('.'):
                role_files = {}
                for f in role_dir.glob("*.md"):
                    role_files[f.name] = f.read_text(encoding='utf-8')
                result["roles"][role_dir.name] = role_files
        return result

    def get_skills_list(self):
        if not self.skills_dir.exists():
            return []
        skills = []
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                info = {"name": skill_dir.name, "path": str(skill_dir)}
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    info["has_skill_md"] = True
                    info["description"] = skill_md.read_text(encoding='utf-8')[:200]
                else:
                    info["has_skill_md"] = False
                skills.append(info)
        return skills

    def get_overview_stats(self):
        session_stats = self.get_session_stats()
        cron_jobs = self.get_cron_jobs()
        gateway = self.get_gateway_status()
        teams = self.get_teams()
        skills = self.get_skills_list()
        active_platforms = {
            k: v for k, v in gateway.get("platforms", {}).items()
            if v.get("state") == "connected"
        }
        return {
            "sessions": session_stats,
            "cron_jobs": {
                "total": len(cron_jobs),
                "enabled": sum(1 for j in cron_jobs if j.get("enabled", True)),
                "paused": sum(1 for j in cron_jobs if j.get("state") == "paused"),
            },
            "gateway": {
                "state": gateway.get("gateway_state", "unknown"),
                "active_platforms": len(active_platforms),
                "platforms": list(active_platforms.keys()),
            },
            "teams": len(teams),
            "skills": len(skills),
        }

    def _list_md_files(self, directory):
        if not directory.exists():
            return []
        return [f.name for f in sorted(directory.glob("*.md"))]

    def _list_subdirs(self, directory):
        if not directory.exists():
            return []
        return [d.name for d in sorted(directory.iterdir()) if d.is_dir() and not d.name.startswith('.')]


adapter = HermesAdapter()
