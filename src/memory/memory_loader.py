# -*- coding: utf-8 -*-
"""
Memory Loader -- Five-layer hierarchical memory loading.

Implements the L1-L5 memory architecture:
- L1: Instant memory (SessionDB conversation history)
- L2: Working memory (current task files)
- L3: Reference memory (API docs, project specs, architecture docs)
- L4: Experience memory (patterns, lessons, verified solutions)
- L5: Identity memory (role definitions, behavioral guidelines, user preferences)

Also loads team memory when a team context is provided.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryLayer:
    """Represents a single memory layer."""

    L1_INSTANT = "L1_instant"
    L2_WORKING = "L2_working"
    L3_REFERENCE = "L3_reference"
    L4_EXPERIENCE = "L4_experience"
    L5_IDENTITY = "L5_identity"
    TEAM = "team"

    ALL_LAYERS = [L1_INSTANT, L2_WORKING, L3_REFERENCE, L4_EXPERIENCE, L5_IDENTITY]

    @classmethod
    def display_name(cls, layer: str) -> str:
        names = {
            cls.L1_INSTANT: "瞬时记忆",
            cls.L2_WORKING: "工作记忆",
            cls.L3_REFERENCE: "参考记忆",
            cls.L4_EXPERIENCE: "经验记忆",
            cls.L5_IDENTITY: "身份记忆",
            cls.TEAM: "团队记忆",
        }
        return names.get(layer, layer)


class MemoryLoader:
    """Loads and manages five-layer hierarchical memory."""

    def __init__(self, hermes_home: Optional[Path] = None):
        self.hermes_home = hermes_home or Path(
            os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
        )
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure all memory directories exist."""
        dirs = [
            self.hermes_home / "references",
            self.hermes_home / "experiences",
            self.hermes_home / "teams",
            self.hermes_home / "shared-context",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def load_identity(self) -> str:
        """Load L5 identity memory."""
        identity_file = self.hermes_home / "identity.md"
        if identity_file.exists():
            return identity_file.read_text(encoding="utf-8")
        return ""

    def load_working_memory(self, task_id: str = "") -> str:
        """Load L2 working memory from current task context."""
        parts = []
        shared_ctx = self.hermes_home / "shared-context" / "tasks"

        if task_id:
            context_file = shared_ctx / f"{task_id}-context.md"
            output_file = shared_ctx / f"{task_id}-output.md"
            if context_file.exists():
                parts.append(context_file.read_text(encoding="utf-8"))
            if output_file.exists():
                parts.append(output_file.read_text(encoding="utf-8"))
        else:
            active_file = self.hermes_home / "shared-context" / "active-task.json"
            if active_file.exists():
                import json
                try:
                    data = json.loads(active_file.read_text(encoding="utf-8"))
                    active_task_id = data.get("task_id", "")
                    if active_task_id:
                        return self.load_working_memory(active_task_id)
                except (json.JSONDecodeError, IOError):
                    pass

        return "\n\n".join(p for p in parts if p.strip())

    def load_references(self, max_files: int = 5) -> str:
        """Load L3 reference memory files."""
        ref_dir = self.hermes_home / "references"
        if not ref_dir.exists():
            return ""

        parts = []
        for ref_file in sorted(ref_dir.glob("*.md"))[:max_files]:
            content = ref_file.read_text(encoding="utf-8")
            if content.strip():
                parts.append(f"### {ref_file.stem}\n\n{content}")

        return "\n\n---\n\n".join(parts)

    def load_experiences(
        self, context: str = "", max_files: int = 5
    ) -> str:
        """Load L4 experience memory files, optionally filtered by context."""
        exp_dir = self.hermes_home / "experiences"
        if not exp_dir.exists():
            return ""

        experiences = []
        for exp_file in sorted(exp_dir.glob("*.md")):
            content = exp_file.read_text(encoding="utf-8")
            if not content.strip():
                continue

            if context:
                score = self._relevance_score(content, context)
                experiences.append((score, exp_file.stem, content))
            else:
                experiences.append((1.0, exp_file.stem, content))

        experiences.sort(key=lambda x: x[0], reverse=True)
        experiences = experiences[:max_files]

        parts = []
        for score, name, content in experiences:
            parts.append(f"### {name}\n\n{content}")

        return "\n\n---\n\n".join(parts)

    def load_team_memory(self, team_name: str) -> str:
        """Load team memory for a specific team."""
        from src.memory.team_memory import TeamMemoryManager

        manager = TeamMemoryManager(base_dir=self.hermes_home / "teams")
        memory = manager.get_memory_for_role(team_name, "general")
        parts = []

        if memory.get("team_memory"):
            parts.append(f"## Team Memory\n\n{memory['team_memory']}")
        if memory.get("role_memory"):
            parts.append(f"## Role Memory\n\n{memory['role_memory']}")
        for doc_name, doc_content in memory.get("team_docs", {}).items():
            parts.append(f"## Doc: {doc_name}\n\n{doc_content}")

        return "\n\n---\n\n".join(parts)

    def load_all(
        self,
        task_id: str = "",
        team: str = "",
        context: str = "",
        layers: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Load all memory layers and return as a dict.

        Args:
            task_id: Current task ID for L2 working memory.
            team: Team name for team memory.
            context: Context string for L4 relevance filtering.
            layers: Optional list of specific layers to load.

        Returns:
            Dict mapping layer names to loaded content.
        """
        target_layers = layers or MemoryLayer.ALL_LAYERS
        result = {}

        if MemoryLayer.L5_IDENTITY in target_layers:
            content = self.load_identity()
            if content:
                result[MemoryLayer.L5_IDENTITY] = content

        if MemoryLayer.L2_WORKING in target_layers:
            content = self.load_working_memory(task_id)
            if content:
                result[MemoryLayer.L2_WORKING] = content

        if MemoryLayer.L3_REFERENCE in target_layers:
            content = self.load_references()
            if content:
                result[MemoryLayer.L3_REFERENCE] = content

        if MemoryLayer.L4_EXPERIENCE in target_layers:
            content = self.load_experiences(context)
            if content:
                result[MemoryLayer.L4_EXPERIENCE] = content

        if team:
            content = self.load_team_memory(team)
            if content:
                result[MemoryLayer.TEAM] = content

        return result

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of available memory across all layers."""
        summary = {}

        identity_file = self.hermes_home / "identity.md"
        summary["L5_identity"] = {
            "exists": identity_file.exists(),
            "size": identity_file.stat().st_size if identity_file.exists() else 0,
        }

        ref_dir = self.hermes_home / "references"
        ref_files = list(ref_dir.glob("*.md")) if ref_dir.exists() else []
        summary["L3_reference"] = {
            "file_count": len(ref_files),
            "total_size": sum(f.stat().st_size for f in ref_files),
        }

        exp_dir = self.hermes_home / "experiences"
        exp_files = list(exp_dir.glob("*.md")) if exp_dir.exists() else []
        summary["L4_experience"] = {
            "file_count": len(exp_files),
            "total_size": sum(f.stat().st_size for f in exp_files),
        }

        teams_dir = self.hermes_home / "teams"
        team_dirs = [d for d in teams_dir.iterdir() if d.is_dir()] if teams_dir.exists() else []
        summary["team"] = {
            "team_count": len(team_dirs),
            "teams": [d.name for d in team_dirs],
        }

        shared_ctx = self.hermes_home / "shared-context" / "tasks"
        task_files = list(shared_ctx.glob("task-*.json")) if shared_ctx.exists() else []
        summary["L2_working"] = {
            "task_count": len(task_files),
        }

        return summary

    def _relevance_score(self, content: str, context: str) -> float:
        """Simple keyword-based relevance scoring."""
        if not context:
            return 0.5

        content_lower = content.lower()
        context_words = set(context.lower().split())
        if not context_words:
            return 0.5

        matches = sum(1 for w in context_words if w in content_lower)
        return matches / len(context_words) if context_words else 0.0
