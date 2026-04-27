# -*- coding: utf-8 -*-
"""
Harness Manager -- Context lifecycle management for multi-agent workflows.

Manages context snapshots, budget allocation, and context recovery
across the agent lifecycle. Integrates with SharedContextManager,
PromptBuilder, and HealthMonitor for seamless context flow.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agent.shared_context import SharedContextManager
from src.monitoring.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_BUDGET = 128000
CONTEXT_WARNING_THRESHOLD = 0.8
CONTEXT_CRITICAL_THRESHOLD = 0.95


class ContextSnapshot:
    """Immutable snapshot of agent context state."""

    def __init__(
        self,
        agent_id: str,
        task_id: str,
        token_count: int,
        token_budget: int,
        memory_layers: Dict[str, str],
        task_context: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.task_id = task_id
        self.token_count = token_count
        self.token_budget = token_budget
        self.memory_layers = memory_layers
        self.task_context = task_context
        self.metadata = metadata or {}
        self.created_at = time.time()

    @property
    def utilization(self) -> float:
        if self.token_budget <= 0:
            return 0.0
        return self.token_count / self.token_budget

    @property
    def is_warning(self) -> bool:
        return self.utilization >= CONTEXT_WARNING_THRESHOLD

    @property
    def is_critical(self) -> bool:
        return self.utilization >= CONTEXT_CRITICAL_THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "token_count": self.token_count,
            "token_budget": self.token_budget,
            "utilization": round(self.utilization, 4),
            "is_warning": self.is_warning,
            "is_critical": self.is_critical,
            "memory_layers": list(self.memory_layers.keys()),
            "context_length": len(self.task_context),
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class HarnessManager:
    """Manages context lifecycle for multi-agent workflows.

    Responsibilities:
    - Track context utilization per agent/task
    - Trigger compression when thresholds are exceeded
    - Save/restore context snapshots for recovery
    - Coordinate with HealthMonitor for auto-recovery
    - Allocate token budgets across memory layers
    """

    def __init__(
        self,
        shared_context_dir: Optional[Path] = None,
        health_monitor: Optional[HealthMonitor] = None,
        token_budget: int = DEFAULT_TOKEN_BUDGET,
        warning_threshold: float = CONTEXT_WARNING_THRESHOLD,
        critical_threshold: float = CONTEXT_CRITICAL_THRESHOLD,
    ):
        self.shared_context = SharedContextManager(shared_context_dir)
        self.health_monitor = health_monitor
        self.token_budget = token_budget
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._snapshots: Dict[str, ContextSnapshot] = {}
        self._compression_callback = None
        self._budget_allocations: Dict[str, Dict[str, int]] = {}

    def set_compression_callback(self, callback) -> None:
        self._compression_callback = callback

    def allocate_budget(
        self,
        agent_id: str,
        role: str = "",
        layers: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Allocate token budget across memory layers for an agent.

        Default allocation strategy:
        - L5 Identity: 5% (always loaded, small)
        - L4 Experience: 15% (relevance-filtered)
        - L3 Reference: 15% (relevance-filtered)
        - L2 Working: 25% (current task context)
        - Team Memory: 10% (team-specific)
        - Task Context: 20% (goal + dependencies)
        - Reserve: 10% (safety margin)
        """
        default_alloc = {
            "L5_identity": 5,
            "L4_experience": 15,
            "L3_reference": 15,
            "L2_working": 25,
            "team_memory": 10,
            "task_context": 20,
            "reserve": 10,
        }

        target_layers = layers or list(default_alloc.keys())
        alloc = {k: v for k, v in default_alloc.items() if k in target_layers}

        total_pct = sum(alloc.values())
        if total_pct > 0:
            scale = 100.0 / total_pct
            alloc = {k: int(v * scale) for k, v in alloc.items()}

        budget_map = {
            k: int(self.token_budget * v / 100) for k, v in alloc.items()
        }

        self._budget_allocations[agent_id] = budget_map
        return budget_map

    def get_budget_for_layer(self, agent_id: str, layer: str) -> int:
        """Get token budget for a specific memory layer."""
        alloc = self._budget_allocations.get(agent_id, {})
        return alloc.get(layer, int(self.token_budget * 0.1))

    def create_snapshot(
        self,
        agent_id: str,
        task_id: str,
        token_count: int,
        memory_layers: Dict[str, str],
        task_context: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextSnapshot:
        """Create and store a context snapshot for an agent."""
        snapshot = ContextSnapshot(
            agent_id=agent_id,
            task_id=task_id,
            token_count=token_count,
            token_budget=self.token_budget,
            memory_layers=memory_layers,
            task_context=task_context,
            metadata=metadata,
        )

        self._snapshots[agent_id] = snapshot

        if snapshot.is_warning:
            logger.warning(
                f"Context warning for agent {agent_id}: "
                f"{snapshot.utilization:.1%} utilization "
                f"({token_count}/{self.token_budget} tokens)"
            )

        if snapshot.is_critical and self._compression_callback:
            logger.info(
                f"Triggering auto-compression for agent {agent_id} "
                f"at {snapshot.utilization:.1%} utilization"
            )
            self._compression_callback(agent_id, snapshot)

        return snapshot

    def get_snapshot(self, agent_id: str) -> Optional[ContextSnapshot]:
        return self._snapshots.get(agent_id)

    def restore_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Restore context from the latest snapshot for recovery."""
        snapshot = self._snapshots.get(agent_id)
        if not snapshot:
            logger.warning(f"No snapshot found for agent {agent_id}")
            return None

        return {
            "agent_id": snapshot.agent_id,
            "task_id": snapshot.task_id,
            "memory_layers": snapshot.memory_layers,
            "task_context": snapshot.task_context,
            "token_count": snapshot.token_count,
            "metadata": snapshot.metadata,
        }

    def check_and_compress(self, agent_id: str) -> bool:
        """Check if compression is needed and trigger it.

        Returns True if compression was triggered.
        """
        snapshot = self._snapshots.get(agent_id)
        if not snapshot:
            return False

        if snapshot.utilization >= self.warning_threshold:
            if self._compression_callback:
                self._compression_callback(agent_id, snapshot)
                return True
            logger.warning(
                f"Agent {agent_id} needs compression but no callback set"
            )

        return False

    def persist_snapshot(self, agent_id: str) -> Optional[Path]:
        """Persist a context snapshot to disk for durability."""
        snapshot = self._snapshots.get(agent_id)
        if not snapshot:
            return None

        snapshot_dir = self.shared_context.tasks_dir / f"{snapshot.task_id}-snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        snapshot_file = snapshot_dir / f"{agent_id}-{int(time.time())}.json"
        snapshot_file.write_text(
            json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return snapshot_file

    def load_snapshots(self, task_id: str) -> List[Dict[str, Any]]:
        """Load all persisted snapshots for a task."""
        snapshot_dir = self.shared_context.tasks_dir / f"{task_id}-snapshots"
        if not snapshot_dir.exists():
            return []

        snapshots = []
        for f in sorted(snapshot_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                snapshots.append(data)
            except (json.JSONDecodeError, IOError):
                continue

        return snapshots

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked contexts."""
        agents = []
        for agent_id, snapshot in self._snapshots.items():
            agents.append(snapshot.to_dict())

        warning_count = sum(1 for s in self._snapshots.values() if s.is_warning)
        critical_count = sum(1 for s in self._snapshots.values() if s.is_critical)

        return {
            "total_agents": len(self._snapshots),
            "warning_count": warning_count,
            "critical_count": critical_count,
            "token_budget": self.token_budget,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "agents": agents,
        }
