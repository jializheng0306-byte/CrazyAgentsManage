# -*- coding: utf-8 -*-
"""
Task Watcher -- Asynchronous task output file monitoring.

Watches task output files for changes and emits events when
new content is appended. Integrates with TaskOrchestrator for
real-time task progress tracking and with HarnessManager for
context-aware monitoring.
"""

from __future__ import annotations

import json
import logging
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

POLL_INTERVAL = 2.0
MAX_FILE_SIZE_MB = 50


class TaskEventType(Enum):
    OUTPUT_APPENDED = "output_appended"
    OUTPUT_CREATED = "output_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"


class TaskEvent:
    """Event emitted by TaskWatcher when task state changes."""

    def __init__(
        self,
        event_type: TaskEventType,
        task_id: str,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.event_type = event_type
        self.task_id = task_id
        self.data = data or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "task_id": self.task_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class TaskWatchEntry:
    """Tracks a single task's output file for changes."""

    def __init__(self, task_id: str, output_path: Path):
        self.task_id = task_id
        self.output_path = output_path
        self.last_size: int = 0
        self.last_modified: float = 0.0
        self.last_position: int = 0
        self.is_active: bool = True
        self.error_count: int = 0

        if output_path.exists():
            stat = output_path.stat()
            self.last_size = stat.st_size
            self.last_modified = stat.st_mtime
            self.last_position = stat.st_size

    def check_for_updates(self) -> Optional[TaskEvent]:
        """Check if the output file has been updated.

        Returns a TaskEvent if new content was detected, None otherwise.
        """
        if not self.is_active:
            return None

        try:
            if not self.output_path.exists():
                return None

            stat = self.output_path.stat()
            current_size = stat.st_size
            current_mtime = stat.st_mtime

            max_size = MAX_FILE_SIZE_MB * 1024 * 1024
            if current_size > max_size:
                self.is_active = False
                return TaskEvent(
                    TaskEventType.FILE_SIZE_EXCEEDED,
                    self.task_id,
                    {
                        "size": current_size,
                        "max_size": max_size,
                        "path": str(self.output_path),
                    },
                )

            if current_size > self.last_size and current_mtime > self.last_modified:
                new_bytes = current_size - self.last_position
                new_content = ""
                try:
                    with open(self.output_path, "r", encoding="utf-8") as f:
                        f.seek(self.last_position)
                        new_content = f.read()
                except (IOError, UnicodeDecodeError):
                    pass

                event = TaskEvent(
                    TaskEventType.OUTPUT_APPENDED,
                    self.task_id,
                    {
                        "new_bytes": new_bytes,
                        "new_content": new_content,
                        "total_size": current_size,
                        "path": str(self.output_path),
                    },
                )

                self.last_size = current_size
                self.last_modified = current_mtime
                self.last_position = current_size
                return event

            if current_size < self.last_size:
                self.last_size = current_size
                self.last_modified = current_mtime
                self.last_position = current_size

        except (OSError, IOError) as e:
            self.error_count += 1
            logger.warning(
                f"Error watching task {self.task_id}: {e} "
                f"(errors: {self.error_count})"
            )
            if self.error_count > 10:
                self.is_active = False

        return None


class TaskWatcher:
    """Watches task output files for changes and emits events.

    Usage:
        watcher = TaskWatcher(shared_context_dir=Path("~/.hermes/shared-context"))
        watcher.add_callback(my_callback)
        watcher.watch_task("task-abc123")
        watcher.start()  # starts polling thread
        # ... later ...
        watcher.stop()
    """

    def __init__(
        self,
        shared_context_dir: Optional[Path] = None,
        poll_interval: float = POLL_INTERVAL,
    ):
        self.shared_context_dir = shared_context_dir or Path.home() / ".hermes" / "shared-context"
        self.tasks_dir = self.shared_context_dir / "tasks"
        self.poll_interval = poll_interval
        self._watches: Dict[str, TaskWatchEntry] = {}
        self._callbacks: List[Callable[[TaskEvent], None]] = []
        self._running = False
        self._thread = None

    def add_callback(self, callback: Callable[[TaskEvent], None]) -> None:
        """Add a callback to be invoked when task events occur."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[TaskEvent], None]) -> None:
        """Remove a previously added callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def watch_task(self, task_id: str) -> None:
        """Start watching a task's output file for changes."""
        output_path = self.tasks_dir / f"{task_id}-output.md"
        self._watches[task_id] = TaskWatchEntry(task_id, output_path)
        logger.info(f"Now watching task {task_id}")

    def unwatch_task(self, task_id: str) -> None:
        """Stop watching a task."""
        if task_id in self._watches:
            self._watches[task_id].is_active = False
            del self._watches[task_id]
            logger.info(f"Stopped watching task {task_id}")

    def notify_task_event(
        self, event_type: TaskEventType, task_id: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Manually emit a task event (e.g., from TaskOrchestrator)."""
        event = TaskEvent(event_type, task_id, data)
        self._emit_event(event)

    def start(self) -> None:
        """Start the watcher polling loop in a background thread."""
        if self._running:
            return

        self._running = True
        import threading
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("TaskWatcher started")

    def stop(self) -> None:
        """Stop the watcher polling loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("TaskWatcher stopped")

    def poll_once(self) -> List[TaskEvent]:
        """Perform a single poll of all watched tasks.

        Returns list of events detected.
        Useful for testing or synchronous usage.
        """
        events = []
        inactive_tasks = []

        for task_id, watch in self._watches.items():
            if not watch.is_active:
                inactive_tasks.append(task_id)
                continue

            event = watch.check_for_updates()
            if event:
                events.append(event)
                self._emit_event(event)

        for task_id in inactive_tasks:
            del self._watches[task_id]

        return events

    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status."""
        active = sum(1 for w in self._watches.values() if w.is_active)
        return {
            "running": self._running,
            "watched_tasks": len(self._watches),
            "active_watches": active,
            "poll_interval": self.poll_interval,
            "tasks": {
                tid: {
                    "is_active": w.is_active,
                    "last_size": w.last_size,
                    "error_count": w.error_count,
                    "output_path": str(w.output_path),
                }
                for tid, w in self._watches.items()
            },
        }

    def _poll_loop(self) -> None:
        """Main polling loop (runs in background thread)."""
        while self._running:
            try:
                self.poll_once()
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")

            time.sleep(self.poll_interval)

    def _emit_event(self, event: TaskEvent) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Callback error for event {event.event_type}: {e}")

    def discover_tasks(self) -> List[str]:
        """Discover all tasks with output files in the shared context directory."""
        task_ids = set()
        if self.tasks_dir.exists():
            for f in self.tasks_dir.glob("*-output.md"):
                task_id = f.stem.replace("-output", "")
                task_ids.add(task_id)
            for f in self.tasks_dir.glob("task-*.json"):
                task_id = f.stem
                task_ids.add(task_id)
        return sorted(task_ids)
