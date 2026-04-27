# -*- coding: utf-8 -*-
"""
Hermes State DB -- Extended session database with tasks table.

Provides database access layer for SessionDB with the tasks table
schema and CRUD operations for task persistence.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HermesStateDB:
    """Extended SessionDB with tasks table for multi-agent task tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".hermes" / "state.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_tables(self) -> None:
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    state TEXT NOT NULL DEFAULT 'pending',
                    goal TEXT,
                    role TEXT,
                    team TEXT,
                    parent_task_id TEXT,
                    shared_context_path TEXT,
                    dependencies TEXT,
                    toolsets TEXT,
                    model TEXT,
                    max_iterations INTEGER DEFAULT 50,
                    result TEXT,
                    error TEXT,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_team ON tasks(team)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_role ON tasks(role)
            """)
            conn.commit()
        finally:
            conn.close()

    def create_task(
        self,
        task_id: str,
        goal: str,
        role: str,
        team: str = "",
        parent_task_id: str = "",
        shared_context_path: str = "",
        dependencies: Optional[List[str]] = None,
        toolsets: Optional[List[str]] = None,
        model: str = "",
        max_iterations: int = 50,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        conn = self._get_conn()
        try:
            now = time.time()
            conn.execute(
                """INSERT INTO tasks
                   (id, state, goal, role, team, parent_task_id,
                    shared_context_path, dependencies, toolsets, model,
                    max_iterations, result, error, created_at, started_at,
                    completed_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    "pending",
                    goal,
                    role,
                    team,
                    parent_task_id,
                    shared_context_path,
                    json.dumps(dependencies or [], ensure_ascii=False),
                    json.dumps(toolsets or [], ensure_ascii=False),
                    model,
                    max_iterations,
                    "",
                    "",
                    now,
                    0.0,
                    0.0,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
            return self.get_task(task_id)
        finally:
            conn.close()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if row:
                return self._row_to_dict(row)
            return None
        finally:
            conn.close()

    def update_task_state(
        self,
        task_id: str,
        state: str,
        result: str = "",
        error: str = "",
    ) -> bool:
        conn = self._get_conn()
        try:
            now = time.time()
            sets = ["state = ?"]
            params: List[Any] = [state]

            if state == "running":
                sets.append("started_at = ?")
                params.append(now)
            elif state in ("done", "failed"):
                sets.append("completed_at = ?")
                params.append(now)

            if result:
                sets.append("result = ?")
                params.append(result)
            if error:
                sets.append("error = ?")
                params.append(error)

            params.append(task_id)
            cursor = conn.execute(
                f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", params
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_tasks(
        self,
        state: Optional[str] = None,
        team: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            conditions = []
            params: List[Any] = []

            if state:
                conditions.append("state = ?")
                params.append(state)
            if team:
                conditions.append("team = ?")
                params.append(team)
            if role:
                conditions.append("role = ?")
                params.append(role)

            where = ""
            if conditions:
                where = "WHERE " + " AND ".join(conditions)

            rows = conn.execute(
                f"SELECT * FROM tasks {where} "
                f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def delete_task(self, task_id: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_task_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT state, COUNT(*) as cnt FROM tasks GROUP BY state"
            ).fetchall()
            stats = {"pending": 0, "running": 0, "done": 0, "failed": 0, "total": 0}
            for row in rows:
                state = row["state"]
                cnt = row["cnt"]
                if state in stats:
                    stats[state] = cnt
                stats["total"] += cnt
            return stats
        finally:
            conn.close()

    def get_tasks_by_parent(self, parent_task_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at",
                (parent_task_id,),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def cleanup_old_tasks(self, days: int = 30) -> int:
        conn = self._get_conn()
        try:
            cutoff = time.time() - (days * 86400)
            cursor = conn.execute(
                "DELETE FROM tasks WHERE completed_at > 0 AND completed_at < ?",
                (cutoff,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        for key in ("dependencies", "toolsets", "metadata"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    d[key] = []
        return d
