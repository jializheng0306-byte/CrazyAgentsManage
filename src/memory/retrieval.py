# -*- coding: utf-8 -*-
"""
Memory Retrieval -- Optimized memory retrieval with relevance ranking.

Provides efficient memory search and retrieval across all memory layers
with keyword-based and semantic relevance scoring.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.memory.memory_loader import MemoryLoader

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """Optimized memory retrieval with relevance ranking."""

    def __init__(self, memory_loader: Optional[MemoryLoader] = None):
        self.memory_loader = memory_loader or MemoryLoader()
        self._index: Optional[Dict[str, List[Dict[str, Any]]]] = None
        self._index_mtime: float = 0.0

    def search(
        self,
        query: str,
        max_results: int = 10,
        layers: Optional[List[str]] = None,
        team: str = "",
    ) -> List[Dict[str, Any]]:
        """Search across memory layers for relevant content.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            layers: Optional list of layers to search.
            team: Team name for team memory search.

        Returns:
            List of results sorted by relevance score.
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        target_layers = layers or [
            "L3_reference",
            "L4_experience",
            "L5_identity",
        ]

        if "L3_reference" in target_layers:
            results.extend(self._search_directory(
                self.memory_loader.hermes_home / "references",
                query_words,
                "L3_reference",
            ))

        if "L4_experience" in target_layers:
            results.extend(self._search_directory(
                self.memory_loader.hermes_home / "experiences",
                query_words,
                "L4_experience",
            ))

        if "L5_identity" in target_layers:
            identity_file = self.memory_loader.hermes_home / "identity.md"
            if identity_file.exists():
                score = self._score_file(identity_file, query_words)
                if score > 0:
                    content = identity_file.read_text(encoding="utf-8")
                    results.append({
                        "layer": "L5_identity",
                        "name": "identity",
                        "score": score,
                        "preview": content[:500],
                        "path": str(identity_file),
                    })

        if team and "team" in target_layers:
            results.extend(self._search_team(team, query_words))

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:max_results]

    def get_relevant_context(
        self,
        goal: str,
        role: str = "",
        team: str = "",
        max_chars: int = 4000,
    ) -> str:
        """Get relevant memory context for a task goal.

        Returns a formatted string of the most relevant memory content,
        suitable for injection into a system prompt.
        """
        results = self.search(
            query=goal,
            max_results=5,
            team=team,
        )

        if not results:
            return ""

        parts = []
        total_chars = 0
        for result in results:
            entry = f"### [{result['layer']}] {result['name']}\n\n{result['preview']}\n"
            if total_chars + len(entry) > max_chars:
                break
            parts.append(entry)
            total_chars += len(entry)

        return "\n---\n".join(parts)

    def build_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build a search index over all memory files."""
        index: Dict[str, List[Dict[str, Any]]] = {
            "L3_reference": [],
            "L4_experience": [],
            "L5_identity": [],
        }

        ref_dir = self.memory_loader.hermes_home / "references"
        if ref_dir.exists():
            for f in ref_dir.glob("*.md"):
                index["L3_reference"].append({
                    "name": f.stem,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                })

        exp_dir = self.memory_loader.hermes_home / "experiences"
        if exp_dir.exists():
            for f in exp_dir.glob("*.md"):
                index["L4_experience"].append({
                    "name": f.stem,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                })

        identity_file = self.memory_loader.hermes_home / "identity.md"
        if identity_file.exists():
            index["L5_identity"].append({
                "name": "identity",
                "path": str(identity_file),
                "size": identity_file.stat().st_size,
                "modified": identity_file.stat().st_mtime,
            })

        self._index = index
        self._index_mtime = os.path.getmtime(str(self.memory_loader.hermes_home))
        return index

    def _search_directory(
        self,
        directory: Path,
        query_words: set,
        layer: str,
    ) -> List[Dict[str, Any]]:
        """Search files in a directory for query words."""
        results = []
        if not directory.exists():
            return results

        for f in directory.glob("*.md"):
            score = self._score_file(f, query_words)
            if score > 0:
                content = f.read_text(encoding="utf-8")
                results.append({
                    "layer": layer,
                    "name": f.stem,
                    "score": score,
                    "preview": content[:500],
                    "path": str(f),
                })

        return results

    def _search_team(
        self, team: str, query_words: set
    ) -> List[Dict[str, Any]]:
        """Search team memory files."""
        results = []
        team_dir = self.memory_loader.hermes_home / "teams" / team
        if not team_dir.exists():
            return results

        for f in team_dir.rglob("*.md"):
            score = self._score_file(f, query_words)
            if score > 0:
                content = f.read_text(encoding="utf-8")
                results.append({
                    "layer": "team",
                    "name": f.stem,
                    "score": score,
                    "preview": content[:500],
                    "path": str(f),
                })

        return results

    def _score_file(self, file_path: Path, query_words: set) -> float:
        """Score a file's relevance to query words."""
        try:
            content = file_path.read_text(encoding="utf-8").lower()
        except (IOError, UnicodeDecodeError):
            return 0.0

        if not query_words:
            return 0.5

        matches = sum(1 for w in query_words if w in content)
        total_words = len(content.split()) if content else 1

        tf_score = matches / len(query_words) if query_words else 0
        length_penalty = min(total_words / 100, 1.0)

        return tf_score * (0.5 + 0.5 * length_penalty)
