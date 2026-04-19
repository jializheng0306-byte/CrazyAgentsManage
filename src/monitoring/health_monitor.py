# -*- coding: utf-8 -*-
"""
Health Monitor -- Agent heartbeat monitoring and auto-recovery.

Monitors agent process health, detects failures, and triggers
automatic recovery with task context preservation.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors agent health and triggers auto-recovery."""

    def __init__(self, interval: int = 30, auto_recover: bool = True):
        self.interval = interval
        self.auto_recover = auto_recover
        self._last_heartbeat: float = time.time()
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._recovery_callback: Optional[Callable] = None

    def register_agent(self, agent_id: str, metadata: Dict[str, Any] = None) -> None:
        """Register an agent for monitoring."""
        self._agents[agent_id] = {
            "id": agent_id,
            "status": "active",
            "last_heartbeat": time.time(),
            "started_at": time.time(),
            "metadata": metadata or {},
            "error_count": 0,
        }

    def heartbeat(self, agent_id: str) -> None:
        """Record a heartbeat from an agent."""
        if agent_id in self._agents:
            self._agents[agent_id]["last_heartbeat"] = time.time()
            self._agents[agent_id]["status"] = "active"
            self._last_heartbeat = time.time()
        else:
            logger.warning(f"Unknown agent heartbeat: {agent_id}")

    def check_health(self, agent_id: str) -> Dict[str, Any]:
        """Check health status of an agent."""
        if agent_id not in self._agents:
            return {"status": "unknown", "agent_id": agent_id}

        agent = self._agents[agent_id]
        now = time.time()
        elapsed = now - agent["last_heartbeat"]

        if elapsed > self.interval * 3:
            agent["status"] = "dead"
            agent["error_count"] += 1
        elif elapsed > self.interval * 2:
            agent["status"] = "unhealthy"
        else:
            agent["status"] = "active"

        return {
            "agent_id": agent_id,
            "status": agent["status"],
            "last_heartbeat": agent["last_heartbeat"],
            "elapsed_seconds": elapsed,
            "error_count": agent["error_count"],
            "uptime_seconds": now - agent["started_at"],
        }

    def check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered agents."""
        return {aid: self.check_health(aid) for aid in self._agents}

    def set_recovery_callback(self, callback: Callable) -> None:
        """Set callback for auto-recovery."""
        self._recovery_callback = callback

    def trigger_recovery(self, agent_id: str, task_context: Dict[str, Any] = None) -> bool:
        """Trigger recovery for a failed agent."""
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        if agent["status"] != "dead":
            logger.info(f"Agent {agent_id} is not dead, skipping recovery")
            return False

        logger.info(f"Triggering recovery for agent {agent_id}")

        if self._recovery_callback:
            try:
                self._recovery_callback(agent_id, task_context)
                agent["status"] = "recovering"
                agent["last_heartbeat"] = time.time()
                return True
            except Exception as e:
                logger.error(f"Recovery failed for agent {agent_id}: {e}")
                return False
        else:
            logger.warning("No recovery callback set")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get health summary for all agents."""
        health = self.check_all()
        statuses = {"active": 0, "unhealthy": 0, "dead": 0, "unknown": 0}
        for h in health.values():
            statuses[h["status"]] += 1

        return {
            "total_agents": len(self._agents),
            "by_status": statuses,
            "monitoring_interval": self.interval,
            "auto_recover": self.auto_recover,
        }
