# -*- coding: utf-8 -*-
"""
Shared Context Manager -- File-based cross-agent communication.

Manages the shared-context/ directory structure for task context,
output, artifacts, and active task tracking.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SharedContextManager:
    """Manages shared context files for multi-agent collaboration."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.home() / ".hermes" / "shared-context"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir = self.base_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def init_task_context(self, task_id: str, context: str = "") -> Path:
        """Initialize context file for a task."""
        context_file = self.tasks_dir / f"{task_id}-context.md"
        if not context_file.exists():
            context_file.write_text(context, encoding="utf-8")
        return context_file

    def write_task_output(self, task_id: str, output: str) -> Path:
        """Write task output file."""
        output_file = self.tasks_dir / f"{task_id}-output.md"
        output_file.write_text(output, encoding="utf-8")
        return output_file

    def append_task_output(self, task_id: str, content: str) -> Path:
        """Append to task output file (for streaming output)."""
        output_file = self.tasks_dir / f"{task_id}-output.md"
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(content)
        return output_file

    def read_task_output(self, task_id: str, tail_lines: int = 0) -> str:
        """Read task output file. If tail_lines > 0, return only last N lines."""
        output_file = self.tasks_dir / f"{task_id}-output.md"
        if not output_file.exists():
            return ""
        content = output_file.read_text(encoding="utf-8")
        if tail_lines > 0:
            lines = content.splitlines()
            return "\n".join(lines[-tail_lines:])
        return content

    def create_artifacts_dir(self, task_id: str) -> Path:
        """Create artifacts directory for a task."""
        artifacts_dir = self.tasks_dir / f"{task_id}-artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir

    def get_artifacts_dir(self, task_id: str) -> Optional[Path]:
        """Get artifacts directory if it exists."""
        artifacts_dir = self.tasks_dir / f"{task_id}-artifacts"
        if artifacts_dir.exists():
            return artifacts_dir
        return None

    def set_active_task(self, task_id: str) -> None:
        """Set the currently active task."""
        active_file = self.base_dir / "active-task.json"
        active_file.write_text(
            json.dumps({
                "task_id": task_id,
                "activated_at": time.time(),
            }, indent=2),
            encoding="utf-8",
        )

    def get_active_task(self) -> Optional[str]:
        """Get the currently active task ID."""
        active_file = self.base_dir / "active-task.json"
        if active_file.exists():
            data = json.loads(active_file.read_text(encoding="utf-8"))
            return data.get("task_id")
        return None

    def clear_active_task(self) -> None:
        """Clear the active task."""
        active_file = self.base_dir / "active-task.json"
        if active_file.exists():
            active_file.unlink()

    def get_task_context(self, task_id: str) -> Optional[str]:
        """Read task context file."""
        context_file = self.tasks_dir / f"{task_id}-context.md"
        if context_file.exists():
            return context_file.read_text(encoding="utf-8")
        return None

    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all task metadata files."""
        tasks = []
        for task_file in self.tasks_dir.glob("task-*.json"):
            if "-context" in task_file.stem or "-output" in task_file.stem:
                continue
            try:
                data = json.loads(task_file.read_text(encoding="utf-8"))
                tasks.append(data)
            except (json.JSONDecodeError, IOError):
                continue
        return tasks

    def cleanup_task(self, task_id: str) -> None:
        """Remove all files related to a task."""
        for pattern in [f"{task_id}.json", f"{task_id}-context.md", f"{task_id}-output.md"]:
            file_path = self.tasks_dir / pattern
            if file_path.exists():
                file_path.unlink()
        artifacts_dir = self.tasks_dir / f"{task_id}-artifacts"
        if artifacts_dir.exists():
            import shutil
            shutil.rmtree(artifacts_dir)

    def get_all_outputs(self) -> Dict[str, str]:
        """Get all task outputs as a dict {task_id: output}."""
        outputs = {}
        for output_file in self.tasks_dir.glob("*-output.md"):
            task_id = output_file.stem.replace("-output", "")
            outputs[task_id] = output_file.read_text(encoding="utf-8")
        return outputs

    def get_context_for_dependent_task(
        self, task_id: str, dependency_ids: List[str]
    ) -> str:
        """Get combined context from dependency task outputs."""
        parts = []
        for dep_id in dependency_ids:
            output = self.read_task_output(dep_id)
            if output:
                parts.append(f"## Dependency: {dep_id}\n\n{output}\n")
        return "\n---\n".join(parts) if parts else ""
