# -*- coding: utf-8 -*-
"""
Delegate Tool -- Role-based subagent delegation with shared context.

Enhanced delegate_task implementation that supports:
- Role-based subagent creation via AgentRole
- Shared context injection and output capture
- Task graph integration for DAG-based delegation
- Thread-safe concurrent subagent management
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.agent.agent_factory import (
    AgentRole,
    BLOCKED_TOOLSET_NAMES,
    BLOCKED_TOOLS,
    ROLE_TOOLSETS,
    build_role_config,
    get_role_prompt,
    resolve_role,
)
from src.agent.shared_context import SharedContextManager

logger = logging.getLogger(__name__)

MAX_CONCURRENT_CHILDREN = 3
MAX_DEPTH = 2
DEFAULT_MAX_ITERATIONS = 50


class DelegateTool:
    """Role-based subagent delegation with shared context support."""

    def __init__(
        self,
        shared_context: Optional[SharedContextManager] = None,
        max_concurrent: int = MAX_CONCURRENT_CHILDREN,
        max_depth: int = MAX_DEPTH,
    ):
        self.shared_context = shared_context or SharedContextManager()
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self._children: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._active_count = 0

    def delegate_task(
        self,
        role: str,
        goal: str,
        context: str = "",
        team: str = "",
        parent_task_id: str = "",
        dependencies: Optional[List[str]] = None,
        override_toolsets: Optional[List[str]] = None,
        override_model: Optional[str] = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> Dict[str, Any]:
        """Delegate a task to a role-based subagent.

        Args:
            role: Role name (e.g. "research", "expert", "code") or alias.
            goal: Task goal description.
            context: Additional context for the subagent.
            team: Team name for team memory integration.
            parent_task_id: Parent task ID for hierarchy tracking.
            dependencies: List of task IDs this task depends on.
            override_toolsets: Override default toolsets for the role.
            override_model: Override default model for the role.
            max_iterations: Maximum iterations for the subagent.

        Returns:
            Dict with task_id, role, status, and configuration.
        """
        with self._lock:
            if self._active_count >= self.max_concurrent:
                return {
                    "status": "rejected",
                    "error": f"Max concurrent children ({self.max_concurrent}) reached",
                }

        resolved_role = resolve_role(role)
        role_config = build_role_config(
            role=resolved_role,
            goal=goal,
            context=context,
            override_toolsets=override_toolsets,
            override_model=override_model,
            max_iterations=max_iterations,
        )

        task_id = f"task-{os.urandom(4).hex()}"
        role_config["task_id"] = task_id
        role_config["team"] = team
        role_config["parent_task_id"] = parent_task_id
        role_config["dependencies"] = dependencies or []

        if dependencies:
            dep_context = self.shared_context.get_context_for_dependent_task(
                task_id, dependencies
            )
            if dep_context:
                role_config["context"] = (
                    context + "\n\n---\nDependency Outputs:\n" + dep_context
                    if context
                    else dep_context
                )

        self.shared_context.init_task_context(task_id, role_config["context"])

        with self._lock:
            self._children[task_id] = {
                "task_id": task_id,
                "role": resolved_role.value,
                "goal": goal,
                "status": "pending",
                "started_at": time.time(),
                "config": role_config,
            }
            self._active_count += 1

        logger.info(
            f"Delegated task {task_id} to role={resolved_role.value}, goal={goal[:80]}"
        )

        return {
            "task_id": task_id,
            "role": resolved_role.value,
            "status": "delegated",
            "toolsets": role_config["toolsets"],
            "shared_context_path": str(self.shared_context.tasks_dir / task_id),
        }

    def complete_task(
        self, task_id: str, output: str, error: str = ""
    ) -> bool:
        """Mark a delegated task as completed and persist output."""
        with self._lock:
            if task_id not in self._children:
                return False
            child = self._children[task_id]
            child["status"] = "failed" if error else "done"
            child["completed_at"] = time.time()
            child["duration"] = child["completed_at"] - child["started_at"]
            self._active_count = max(0, self._active_count - 1)

        if output:
            self.shared_context.write_task_output(task_id, output)
        if error:
            self.shared_context.append_task_output(
                task_id, f"\n## Error\n{error}\n"
            )

        logger.info(
            f"Task {task_id} completed: status={child['status']}, "
            f"duration={child['duration']:.1f}s"
        )
        return True

    def get_child_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a delegated child task."""
        with self._lock:
            if task_id in self._children:
                child = self._children[task_id]
                return {
                    "task_id": task_id,
                    "role": child["role"],
                    "status": child["status"],
                    "duration": child.get("duration", 0),
                }
        return None

    def list_children(self) -> List[Dict[str, Any]]:
        """List all child tasks."""
        with self._lock:
            return [
                {
                    "task_id": c["task_id"],
                    "role": c["role"],
                    "goal": c["goal"][:80],
                    "status": c["status"],
                    "duration": c.get("duration", 0),
                }
                for c in self._children.values()
            ]

    def get_role_info(self, role_str: str) -> Dict[str, Any]:
        """Get role information including toolsets and description."""
        role = resolve_role(role_str)
        return build_role_config(role, goal="", context="")

    def available_roles(self) -> List[Dict[str, Any]]:
        """List all available roles with their configurations."""
        from src.agent.agent_factory import available_roles
        return available_roles()

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running child task."""
        with self._lock:
            if task_id not in self._children:
                return False
            child = self._children[task_id]
            if child["status"] in ("pending", "running"):
                child["status"] = "cancelled"
                child["completed_at"] = time.time()
                self._active_count = max(0, self._active_count - 1)
                return True
            return False

    def cleanup_completed(self) -> int:
        """Remove completed/failed/cancelled children from tracking."""
        with self._lock:
            to_remove = [
                tid
                for tid, child in self._children.items()
                if child["status"] in ("done", "failed", "cancelled")
            ]
            for tid in to_remove:
                del self._children[tid]
            return len(to_remove)
