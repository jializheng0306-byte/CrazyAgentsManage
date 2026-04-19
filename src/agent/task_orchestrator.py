# -*- coding: utf-8 -*-
"""
Task Orchestrator -- DAG-based task execution with 3-state protocol.

Provides task definition, state management, dependency resolution,
and execution orchestration for multi-agent task workflows.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .agent_factory import AgentRole

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task states (3-state protocol + failed)
# ---------------------------------------------------------------------------

class TaskState(Enum):
    """Standardized task lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Task definition
# ---------------------------------------------------------------------------

@dataclass
class TaskDef:
    """Task definition with dependency tracking."""

    id: str
    goal: str
    role: AgentRole
    state: TaskState = TaskState.PENDING
    context: str = ""
    dependencies: List[str] = field(default_factory=list)
    output: str = ""
    error: str = ""
    team: str = ""
    model: str = ""
    toolsets: List[str] = field(default_factory=list)
    max_iterations: int = 50
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Return task execution duration in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON persistence."""
        return {
            "id": self.id,
            "goal": self.goal,
            "role": self.role.value,
            "state": self.state.value,
            "context": self.context,
            "dependencies": self.dependencies,
            "output": self.output,
            "error": self.error,
            "team": self.team,
            "model": self.model,
            "toolsets": self.toolsets,
            "max_iterations": self.max_iterations,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskDef":
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            goal=data["goal"],
            role=AgentRole(data["role"]),
            state=TaskState(data["state"]),
            context=data.get("context", ""),
            dependencies=data.get("dependencies", []),
            output=data.get("output", ""),
            error=data.get("error", ""),
            team=data.get("team", ""),
            model=data.get("model", ""),
            toolsets=data.get("toolsets", []),
            max_iterations=data.get("max_iterations", 50),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at", 0.0),
            completed_at=data.get("completed_at", 0.0),
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Task Graph (DAG)
# ---------------------------------------------------------------------------

class TaskGraph:
    """Directed Acyclic Graph for task dependencies."""

    def __init__(self):
        self.tasks: Dict[str, TaskDef] = {}
        self.edges: List[tuple[str, str]] = []  # (from_id, to_id)

    def add_task(self, task: TaskDef) -> None:
        """Add a task to the graph."""
        self.tasks[task.id] = task

    def add_dependency(self, from_id: str, to_id: str) -> None:
        """Add a dependency edge: to_id depends on from_id."""
        if from_id not in self.tasks or to_id not in self.tasks:
            raise ValueError(f"Task not found: {from_id} or {to_id}")
        self.edges.append((from_id, to_id))
        self.tasks[to_id].dependencies.append(from_id)

    def get_ready_tasks(self) -> List[TaskDef]:
        """Return tasks that are pending and have all dependencies satisfied."""
        ready = []
        for task in self.tasks.values():
            if task.state != TaskState.PENDING:
                continue
            deps_done = all(
                self.tasks[dep_id].state == TaskState.DONE
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            if deps_done:
                ready.append(task)
        return ready

    def get_failed_tasks(self) -> List[TaskDef]:
        """Return tasks that have failed."""
        return [t for t in self.tasks.values() if t.state == TaskState.FAILED]

    def is_complete(self) -> bool:
        """Check if all tasks are done or failed."""
        return all(
            t.state in (TaskState.DONE, TaskState.FAILED)
            for t in self.tasks.values()
        )

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the task graph."""
        states = {"pending": 0, "running": 0, "done": 0, "failed": 0}
        for task in self.tasks.values():
            states[task.state.value] += 1
        return {
            "total": len(self.tasks),
            "by_state": states,
            "edges": len(self.edges),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire graph."""
        return {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "edges": self.edges,
            "summary": self.get_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        """Deserialize from dict."""
        graph = cls()
        for tid, tdata in data.get("tasks", {}).items():
            graph.add_task(TaskDef.from_dict(tdata))
        graph.edges = data.get("edges", [])
        return graph


# ---------------------------------------------------------------------------
# Task Orchestrator
# ---------------------------------------------------------------------------

class TaskOrchestrator:
    """Orchestrates task execution based on DAG dependencies."""

    def __init__(self, shared_context_dir: Optional[Path] = None):
        self.graph = TaskGraph()
        self.shared_context_dir = shared_context_dir or Path.home() / ".hermes" / "shared-context"
        self.shared_context_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir = self.shared_context_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self._executor: Optional[Callable] = None
        self._progress_callback: Optional[Callable] = None

    def set_executor(self, executor: Callable) -> None:
        """Set the function that executes individual tasks."""
        self._executor = executor

    def set_progress_callback(self, callback: Callable) -> None:
        """Set a callback for task progress updates."""
        self._progress_callback = callback

    def create_task(
        self,
        goal: str,
        role: AgentRole,
        context: str = "",
        dependencies: Optional[List[str]] = None,
        team: str = "",
        model: str = "",
        toolsets: Optional[List[str]] = None,
        max_iterations: int = 50,
    ) -> TaskDef:
        """Create a new task and add it to the graph."""
        task = TaskDef(
            id=f"task-{uuid.uuid4().hex[:8]}",
            goal=goal,
            role=role,
            context=context,
            dependencies=dependencies or [],
            team=team,
            model=model,
            toolsets=toolsets or [],
            max_iterations=max_iterations,
        )
        self.graph.add_task(task)
        self._persist_task(task)
        return task

    def execute_all(self) -> Dict[str, Any]:
        """Execute all tasks respecting dependencies."""
        if not self._executor:
            raise RuntimeError("No executor set. Call set_executor() first.")

        while not self.graph.is_complete():
            ready = self.graph.get_ready_tasks()
            if not ready:
                # Check for circular dependencies or all pending
                pending = [t for t in self.graph.tasks.values() if t.state == TaskState.PENDING]
                if pending:
                    logger.error("Circular dependency or blocked tasks detected")
                    for t in pending:
                        t.state = TaskState.FAILED
                        t.error = "Circular dependency or blocked"
                        self._persist_task(t)
                break

            for task in ready:
                task.state = TaskState.RUNNING
                task.started_at = time.time()
                self._persist_task(task)
                self._notify_progress(task)

                try:
                    result = self._executor(task)
                    task.output = result
                    task.state = TaskState.DONE
                except Exception as e:
                    task.error = str(e)
                    task.state = TaskState.FAILED
                    logger.error(f"Task {task.id} failed: {e}")

                task.completed_at = time.time()
                self._persist_task(task)
                self._notify_progress(task)

        return self.graph.to_dict()

    def get_task(self, task_id: str) -> Optional[TaskDef]:
        """Get a task by ID."""
        return self.graph.tasks.get(task_id)

    def get_task_graph(self) -> Dict[str, Any]:
        """Get the current task graph as dict."""
        return self.graph.to_dict()

    def load_from_disk(self) -> None:
        """Load task graph from disk."""
        graph_file = self.shared_context_dir / "task-graph.json"
        if graph_file.exists():
            data = json.loads(graph_file.read_text(encoding="utf-8"))
            self.graph = TaskGraph.from_dict(data)

    def _persist_task(self, task: TaskDef) -> None:
        """Persist task state to disk."""
        task_file = self.tasks_dir / f"{task.id}.json"
        task_file.write_text(
            json.dumps(task.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # Also persist the graph
        graph_file = self.shared_context_dir / "task-graph.json"
        graph_file.write_text(
            json.dumps(self.graph.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _notify_progress(self, task: TaskDef) -> None:
        """Notify progress callback if set."""
        if self._progress_callback:
            self._progress_callback(task)
