# -*- coding: utf-8 -*-
"""
Agent Factory -- Role-based subagent creation.

Provides AgentRole enum and factory functions to create specialized
child agents based on role configuration. Integrates with the existing
delegate_tool.py subagent system.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------

class AgentRole(Enum):
    """Pre-defined agent roles for specialized task delegation."""

    COORDINATOR = "coordinator"
    EXPERT = "expert"
    RESEARCH = "research"
    CODE = "code"
    OPS = "ops"
    CRON = "cron"
    TEAM = "team"


# Default toolset assignments per role.
# These mirror the toolset restrictions already used in delegate_tool.py,
# but are expressed as role-level policy so the model can pick the right
# role for a subtask without needing to manually list toolsets.
ROLE_TOOLSETS: Dict[AgentRole, List[str]] = {
    AgentRole.EXPERT: ["terminal", "file", "web", "mcp"],
    AgentRole.RESEARCH: ["web", "file"],
    AgentRole.CODE: ["terminal", "file", "code_execution"],
    AgentRole.OPS: ["terminal", "file"],
    AgentRole.CRON: ["terminal", "file", "web", "memory"],
    AgentRole.TEAM: ["file", "memory", "send_message"],
}

# Role descriptions used in system prompts and WebUI display.
ROLE_DESCRIPTIONS: Dict[AgentRole, str] = {
    AgentRole.EXPERT: "Expert analyst for complex reasoning, debugging, and code review.",
    AgentRole.RESEARCH: "Research specialist for web search, information gathering, and synthesis.",
    AgentRole.CODE: "Coding expert for writing, testing, and debugging code.",
    AgentRole.OPS: "System operations expert for deployment, monitoring, and system maintenance.",
    AgentRole.CRON: "Scheduled task executor for periodic jobs and report generation.",
    AgentRole.TEAM: "Team coordinator for shared memory management and role coordination.",
}

# System prompt templates per role.
ROLE_PROMPTS: Dict[AgentRole, str] = {
    AgentRole.EXPERT: (
        "You are an expert analyst subagent. "
        "Focus on complex reasoning, debugging, and code review tasks. "
        "Provide thorough analysis with clear conclusions."
    ),
    AgentRole.RESEARCH: (
        "You are a research specialist subagent. "
        "Focus on web search, information gathering, and synthesis. "
        "Provide well-structured summaries with source references."
    ),
    AgentRole.CODE: (
        "You are a coding expert subagent. "
        "Focus on writing, testing, and debugging code. "
        "Ensure all code is production-ready with proper error handling."
    ),
    AgentRole.OPS: (
        "You are a system operations expert subagent. "
        "Focus on deployment, monitoring, and system maintenance tasks. "
        "Always verify operations with health checks."
    ),
    AgentRole.CRON: (
        "You are a scheduled task executor subagent. "
        "Focus on periodic jobs, report generation, and system maintenance. "
        "Always produce structured output suitable for delivery."
    ),
    AgentRole.TEAM: (
        "You are a team coordinator subagent. "
        "Focus on shared memory management, role coordination, and "
        "cross-team knowledge sharing. Maintain team memory files."
    ),
}

# Tools that are always blocked for child agents (inherited from delegate_tool.py).
# These are kept in sync with DELEGATE_BLOCKED_TOOLS.
BLOCKED_TOOLS = frozenset([
    "delegate_task",
    "clarify",
    "memory",
    "send_message",
    "execute_code",
])

# Blocked toolset names (used to strip entire toolsets).
BLOCKED_TOOLSET_NAMES = frozenset([
    "delegation",
    "clarify",
    "memory",
    "code_execution",
])


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def get_role_toolsets(role: AgentRole) -> List[str]:
    """Return the toolset list for a given role."""
    return list(ROLE_TOOLSETS.get(role, ["terminal", "file", "web"]))


def get_role_prompt(role: AgentRole, goal: str, context: str = "") -> str:
    """Build a system prompt for a role-based subagent."""
    base = ROLE_PROMPTS.get(role, ROLE_PROMPTS[AgentRole.EXPERT])
    parts = [
        base,
        "",
        f"YOUR TASK:\n{goal}",
    ]
    if context and context.strip():
        parts.append(f"\nCONTEXT:\n{context}")
    parts.append(
        "\nComplete this task using the tools available to you. "
        "When finished, provide a clear, concise summary of:\n"
        "- What you did\n"
        "- What you found or accomplished\n"
        "- Any files you created or modified\n"
        "- Any issues encountered\n\n"
        "Be thorough but concise -- your response is returned to the "
        "parent agent as a summary."
    )
    return "\n".join(parts)


def resolve_role(role_str: str) -> AgentRole:
    """Resolve a role string to an AgentRole enum value.

    Supports both exact enum values (e.g. "expert") and common aliases
    (e.g. "researcher" -> RESEARCH).
    """
    role_str = role_str.lower().strip()
    # Exact match
    for role in AgentRole:
        if role.value == role_str:
            return role
    # Common aliases
    aliases: Dict[str, AgentRole] = {
        "researcher": AgentRole.RESEARCH,
        "research_agent": AgentRole.RESEARCH,
        "coding": AgentRole.CODE,
        "code_agent": AgentRole.CODE,
        "developer": AgentRole.CODE,
        "dev": AgentRole.CODE,
        "operations": AgentRole.OPS,
        "运维": AgentRole.OPS,
        "cron_agent": AgentRole.CRON,
        "scheduler": AgentRole.CRON,
        "team_agent": AgentRole.TEAM,
        "coordinator": AgentRole.COORDINATOR,
    }
    return aliases.get(role_str, AgentRole.EXPERT)


def build_role_config(
    role: AgentRole,
    goal: str,
    context: str = "",
    override_toolsets: Optional[List[str]] = None,
    override_model: Optional[str] = None,
    max_iterations: int = 50,
) -> Dict[str, Any]:
    """Build a complete role configuration dict for subagent creation.

    This dict can be passed directly to the delegate_task handler
    or used by the task orchestrator to spawn a child agent.

    Returns:
        Dict with keys: role, goal, context, toolsets, system_prompt,
        model (optional), max_iterations.
    """
    toolsets = override_toolsets or get_role_toolsets(role)
    # Strip blocked toolsets
    toolsets = [t for t in toolsets if t not in BLOCKED_TOOLSET_NAMES]

    return {
        "role": role.value,
        "goal": goal,
        "context": context,
        "toolsets": toolsets,
        "system_prompt": get_role_prompt(role, goal, context),
        "model": override_model,
        "max_iterations": max_iterations,
    }


def available_roles() -> List[Dict[str, str]]:
    """Return a list of available roles with descriptions for UI display."""
    return [
        {
            "name": role.value,
            "description": ROLE_DESCRIPTIONS[role],
            "toolsets": ROLE_TOOLSETS[role],
        }
        for role in AgentRole
        if role != AgentRole.COORDINATOR
    ]
