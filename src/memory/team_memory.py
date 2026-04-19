# -*- coding: utf-8 -*-
"""
Team Memory System -- Multi-team role-based memory management.

Manages team memory directory structure, role memories, and
automatic experience accumulation for multi-agent collaboration.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TeamMemoryManager:
    """Manages team memory directories and role-based memories."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.home() / ".hermes" / "teams"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # Initialize default team if not exists
        self._ensure_team("default")

    def _ensure_team(self, team_name: str) -> Path:
        """Ensure team directory structure exists."""
        team_dir = self.base_dir / team_name
        team_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        roles_dir = team_dir / "roles"
        roles_dir.mkdir(exist_ok=True)

        docs_dir = team_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Create team memory file if not exists
        team_memory = team_dir / "team-memory.md"
        if not team_memory.exists():
            team_memory.write_text(
                f"# {team_name} Team Memory\n\n"
                f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "## Overview\n\n"
                "This team's shared memory is automatically updated "
                "after each session.\n\n"
                "## Recent Updates\n\n",
                encoding="utf-8",
            )

        return team_dir

    def list_teams(self) -> List[Dict[str, Any]]:
        """List all teams with their metadata."""
        teams = []
        for team_dir in self.base_dir.iterdir():
            if not team_dir.is_dir():
                continue
            team_name = team_dir.name
            team_info = {
                "name": team_name,
                "path": str(team_dir),
                "roles": [],
                "docs": [],
                "memory_count": 0,
            }

            # Count roles
            roles_dir = team_dir / "roles"
            if roles_dir.exists():
                team_info["roles"] = [
                    {"name": f.stem, "path": str(f)}
                    for f in roles_dir.glob("*.md")
                ]
                team_info["memory_count"] += len(team_info["roles"])

            # Count docs
            docs_dir = team_dir / "docs"
            if docs_dir.exists():
                team_info["docs"] = [
                    {"name": f.stem, "path": str(f)}
                    for f in docs_dir.glob("*.md")
                ]
                team_info["memory_count"] += len(team_info["docs"])

            # Count team memory
            team_memory = team_dir / "team-memory.md"
            if team_memory.exists():
                team_info["memory_count"] += 1

            teams.append(team_info)
        return teams

    def get_team(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Get team details including roles and docs."""
        team_dir = self.base_dir / team_name
        if not team_dir.exists():
            return None

        team_info = {
            "name": team_name,
            "path": str(team_dir),
            "memory": "",
            "roles": {},
            "docs": {},
        }

        # Load team memory
        team_memory = team_dir / "team-memory.md"
        if team_memory.exists():
            team_info["memory"] = team_memory.read_text(encoding="utf-8")

        # Load roles
        roles_dir = team_dir / "roles"
        if roles_dir.exists():
            for role_file in roles_dir.glob("*.md"):
                team_info["roles"][role_file.stem] = role_file.read_text(
                    encoding="utf-8"
                )

        # Load docs
        docs_dir = team_dir / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.md"):
                team_info["docs"][doc_file.stem] = doc_file.read_text(
                    encoding="utf-8"
                )

        return team_info

    def create_role_memory(
        self, team_name: str, role_name: str, content: str = ""
    ) -> Path:
        """Create or update a role memory file."""
        team_dir = self._ensure_team(team_name)
        roles_dir = team_dir / "roles"
        roles_dir.mkdir(exist_ok=True)

        role_file = roles_dir / f"{role_name}.md"
        if not role_file.exists():
            role_file.write_text(
                f"# {role_name} Role Memory\n\n"
                f"Team: {team_name}\n"
                f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "## Responsibilities\n\n\n"
                "## Skills\n\n\n"
                "## Experience\n\n",
                encoding="utf-8",
            )

        # Append content if provided
        if content.strip():
            with open(role_file, "a", encoding="utf-8") as f:
                f.write(f"\n## Update ({time.strftime('%Y-%m-%d %H:%M:%S')})\n\n{content}\n")

        return role_file

    def get_role_memory(self, team_name: str, role_name: str) -> Optional[str]:
        """Get role memory content."""
        team_dir = self.base_dir / team_name
        role_file = team_dir / "roles" / f"{role_name}.md"
        if role_file.exists():
            return role_file.read_text(encoding="utf-8")
        return None

    def create_team_doc(
        self, team_name: str, doc_name: str, content: str
    ) -> Path:
        """Create or update a team document."""
        team_dir = self._ensure_team(team_name)
        docs_dir = team_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        doc_file = docs_dir / f"{doc_name}.md"
        doc_file.write_text(content, encoding="utf-8")
        return doc_file

    def get_team_doc(self, team_name: str, doc_name: str) -> Optional[str]:
        """Get team document content."""
        team_dir = self.base_dir / team_name
        doc_file = team_dir / "docs" / f"{doc_name}.md"
        if doc_file.exists():
            return doc_file.read_text(encoding="utf-8")
        return None

    def append_to_team_memory(self, team_name: str, content: str) -> Path:
        """Append content to team memory file."""
        team_dir = self._ensure_team(team_name)
        team_memory = team_dir / "team-memory.md"

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n### {timestamp}\n\n{content}\n"

        with open(team_memory, "a", encoding="utf-8") as f:
            f.write(entry)

        return team_memory

    def update_team_memory(self, team_name: str, content: str) -> Path:
        """Update team memory file (overwrite)."""
        team_dir = self._ensure_team(team_name)
        team_memory = team_dir / "team-memory.md"
        team_memory.write_text(content, encoding="utf-8")
        return team_memory

    def delete_team(self, team_name: str) -> bool:
        """Delete a team and all its memories."""
        if team_name == "default":
            logger.warning("Cannot delete default team")
            return False

        team_dir = self.base_dir / team_name
        if team_dir.exists():
            import shutil
            shutil.rmtree(team_dir)
            return True
        return False

    def get_memory_for_role(
        self, team_name: str, role_name: str
    ) -> Dict[str, str]:
        """Get all memory content relevant to a role."""
        result = {
            "team_memory": "",
            "role_memory": "",
            "team_docs": {},
        }

        # Team memory
        team_memory = self.base_dir / team_name / "team-memory.md"
        if team_memory.exists():
            result["team_memory"] = team_memory.read_text(encoding="utf-8")

        # Role memory
        role_memory = self.get_role_memory(team_name, role_name)
        if role_memory:
            result["role_memory"] = role_memory

        # Team docs
        docs_dir = self.base_dir / team_name / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.md"):
                result["team_docs"][doc_file.stem] = doc_file.read_text(
                    encoding="utf-8"
                )

        return result
