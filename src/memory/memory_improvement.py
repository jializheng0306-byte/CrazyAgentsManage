# -*- coding: utf-8 -*-
"""
Memory Improvement -- Self-improvement loop for experience accumulation.

Implements automatic memory updates after sessions:
- Extract patterns from successful sessions
- Extract lessons from failed sessions
- Update experience memory files (L4)
- Update team memory with role-specific experiences
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.memory.team_memory import TeamMemoryManager

logger = logging.getLogger(__name__)


class SessionResult:
    """Represents the outcome of a session for memory improvement."""

    def __init__(
        self,
        session_id: str,
        success: bool,
        goal: str = "",
        role: str = "",
        team: str = "",
        output: str = "",
        error: str = "",
        duration: float = 0.0,
        tools_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.session_id = session_id
        self.success = success
        self.goal = goal
        self.role = role
        self.team = team
        self.output = output
        self.error = error
        self.duration = duration
        self.tools_used = tools_used or []
        self.metadata = metadata or {}


class SelfImprovementLoop:
    """Self-improvement loop that updates memory after each session.

    On success: Extract reusable patterns and write to L4 experience memory.
    On failure: Extract lessons learned and write to L4 experience memory.
    On session end: Update team memory if a team context is active.
    """

    def __init__(
        self,
        hermes_home: Optional[Path] = None,
        team_memory_manager: Optional[TeamMemoryManager] = None,
    ):
        self.hermes_home = hermes_home or Path.home() / ".hermes"
        self.experiences_dir = self.hermes_home / "experiences"
        self.experiences_dir.mkdir(parents=True, exist_ok=True)
        self.team_memory = team_memory_manager or TeamMemoryManager(
            base_dir=self.hermes_home / "teams"
        )

    def on_session_end(self, result: SessionResult) -> List[Path]:
        """Process a completed session and update memory.

        Returns list of files that were created/updated.
        """
        updated_files = []

        if result.success:
            paths = self._extract_pattern(result)
            updated_files.extend(paths)
        else:
            paths = self._extract_lesson(result)
            updated_files.extend(paths)

        if result.team:
            path = self._update_team_memory(result)
            if path:
                updated_files.append(path)

        return updated_files

    def _extract_pattern(self, result: SessionResult) -> List[Path]:
        """Extract a reusable pattern from a successful session."""
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        pattern_file = self.experiences_dir / f"pattern-{timestamp}.md"

        content_parts = [
            f"# Pattern: {result.goal[:80]}",
            "",
            f"**Type**: Success Pattern",
            f"**Role**: {result.role}",
            f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Duration**: {result.duration:.1f}s",
            f"**Session**: {result.session_id}",
            "",
            "## Goal",
            result.goal,
            "",
            "## Approach",
            result.output[:2000] if result.output else "No output recorded.",
        ]

        if result.tools_used:
            content_parts.extend([
                "",
                "## Tools Used",
                ", ".join(result.tools_used),
            ])

        content_parts.extend([
            "",
            "## Key Takeaway",
            "This approach was successful and can be reused for similar tasks.",
        ])

        pattern_file.write_text("\n".join(content_parts), encoding="utf-8")
        logger.info(f"Extracted success pattern to {pattern_file}")
        return [pattern_file]

    def _extract_lesson(self, result: SessionResult) -> List[Path]:
        """Extract a lesson from a failed session."""
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        lesson_file = self.experiences_dir / f"lesson-{timestamp}.md"

        content_parts = [
            f"# Lesson: {result.goal[:80]}",
            "",
            f"**Type**: Failure Lesson",
            f"**Role**: {result.role}",
            f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Duration**: {result.duration:.1f}s",
            f"**Session**: {result.session_id}",
            "",
            "## Goal",
            result.goal,
            "",
            "## Error",
            result.error[:2000] if result.error else "Unknown error.",
        ]

        if result.output:
            content_parts.extend([
                "",
                "## Partial Output",
                result.output[:1000],
            ])

        content_parts.extend([
            "",
            "## Lesson Learned",
            "This approach failed. Consider alternative strategies for similar tasks.",
        ])

        lesson_file.write_text("\n".join(content_parts), encoding="utf-8")
        logger.info(f"Extracted failure lesson to {lesson_file}")
        return [lesson_file]

    def _update_team_memory(self, result: SessionResult) -> Optional[Path]:
        """Update team memory with session experience."""
        if not result.team:
            return None

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        status = "succeeded" if result.success else "failed"

        content = (
            f"**Session {result.session_id}** ({status})\n"
            f"- Role: {result.role}\n"
            f"- Goal: {result.goal[:200]}\n"
            f"- Duration: {result.duration:.1f}s\n"
        )
        if result.error:
            content += f"- Error: {result.error[:200]}\n"

        try:
            path = self.team_memory.append_to_team_memory(result.team, content)
            logger.info(f"Updated team memory for {result.team}")

            if result.role:
                role_content = (
                    f"**{timestamp}** - {status}: {result.goal[:100]}\n"
                )
                self.team_memory.create_role_memory(
                    result.team, result.role, role_content
                )

            return path
        except Exception as e:
            logger.error(f"Failed to update team memory: {e}")
            return None

    def get_recent_experiences(
        self, limit: int = 10, experience_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent experience entries."""
        experiences = []
        for exp_file in sorted(self.experiences_dir.glob("*.md"), reverse=True):
            if experience_type == "pattern" and not exp_file.name.startswith("pattern-"):
                continue
            if experience_type == "lesson" and not exp_file.name.startswith("lesson-"):
                continue

            content = exp_file.read_text(encoding="utf-8")
            exp_type = "pattern" if exp_file.name.startswith("pattern-") else "lesson"

            experiences.append({
                "name": exp_file.stem,
                "type": exp_type,
                "size": exp_file.stat().st_size,
                "modified": exp_file.stat().st_mtime,
                "preview": content[:500],
            })

            if len(experiences) >= limit:
                break

        return experiences

    def cleanup_old_experiences(self, max_files: int = 50) -> int:
        """Remove old experience files when count exceeds max_files."""
        all_files = sorted(
            self.experiences_dir.glob("*.md"),
            key=lambda f: f.stat().st_mtime,
        )
        if len(all_files) <= max_files:
            return 0

        to_remove = all_files[: len(all_files) - max_files]
        for f in to_remove:
            f.unlink()

        logger.info(f"Cleaned up {len(to_remove)} old experience files")
        return len(to_remove)
