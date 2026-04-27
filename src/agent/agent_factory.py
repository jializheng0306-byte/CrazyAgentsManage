# -*- coding: utf-8 -*-
"""
Agent Factory -- Role-based subagent creation.

Provides AgentRole enum and factory functions to create specialized
child agents based on role configuration. Integrates with the existing
delegate_tool.py subagent system.

v0.1.0: Core role definitions, toolset mapping, prompt templates
v0.3.0: Config-driven roles, Cron agent role, team memory integration
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Pre-defined agent roles for specialized task delegation."""

    COORDINATOR = "coordinator"
    EXPERT = "expert"
    RESEARCH = "research"
    CODE = "code"
    OPS = "ops"
    CRON = "cron"
    TEAM = "team"


ROLE_TOOLSETS: Dict[AgentRole, List[str]] = {
    AgentRole.EXPERT: ["terminal", "file", "web", "mcp"],
    AgentRole.RESEARCH: ["web", "file"],
    AgentRole.CODE: ["terminal", "file", "code_execution"],
    AgentRole.OPS: ["terminal", "file"],
    AgentRole.CRON: ["terminal", "file", "web", "memory"],
    AgentRole.TEAM: ["file", "memory", "send_message"],
}

ROLE_DESCRIPTIONS: Dict[AgentRole, str] = {
    AgentRole.EXPERT: "Expert analyst for complex reasoning, debugging, and code review.",
    AgentRole.RESEARCH: "Research specialist for web search, information gathering, and synthesis.",
    AgentRole.CODE: "Coding expert for writing, testing, and debugging code.",
    AgentRole.OPS: "System operations expert for deployment, monitoring, and system maintenance.",
    AgentRole.CRON: "Scheduled task executor for periodic jobs and report generation.",
    AgentRole.TEAM: "Team coordinator for shared memory management and role coordination.",
}

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
        "Always produce structured output suitable for delivery. "
        "Write your output to the team memory if a team is specified."
    ),
    AgentRole.TEAM: (
        "You are a team coordinator subagent. "
        "Focus on shared memory management, role coordination, and "
        "cross-team knowledge sharing. Maintain team memory files."
    ),
}

BLOCKED_TOOLS = frozenset([
    "delegate_task",
    "clarify",
    "memory",
    "send_message",
    "execute_code",
])

BLOCKED_TOOLSET_NAMES = frozenset([
    "delegation",
    "clarify",
    "memory",
    "code_execution",
])

_ROLE_ALIASES: Dict[str, AgentRole] = {
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
    "定时": AgentRole.CRON,
    "team_agent": AgentRole.TEAM,
    "coordinator": AgentRole.COORDINATOR,
    "专家": AgentRole.EXPERT,
    "研究": AgentRole.RESEARCH,
    "编程": AgentRole.CODE,
    "团队": AgentRole.TEAM,
}


def _load_config() -> Dict[str, Any]:
    """Load role configuration from config/schema.yaml if available."""
    config_path = Path(__file__).resolve().parents[2] / "config" / "schema.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        logger.debug("PyYAML not available, using default config")
        return {}
    except Exception as e:
        logger.warning(f"Failed to load config: {e}")
        return {}


def _get_role_config_from_yaml(role_name: str) -> Dict[str, Any]:
    """Get role-specific config from YAML."""
    config = _load_config()
    roles = config.get("multi_agent", {}).get("roles", {})
    return roles.get(role_name, {})


def get_role_toolsets(role: AgentRole) -> List[str]:
    """Return the toolset list for a given role, with config overrides."""
    yaml_config = _get_role_config_from_yaml(role.value)
    if yaml_config and "toolsets" in yaml_config:
        return list(yaml_config["toolsets"])
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
    (e.g. "researcher" -> RESEARCH, "运维" -> OPS).
    """
    role_str = role_str.lower().strip()
    for role in AgentRole:
        if role.value == role_str:
            return role
    return _ROLE_ALIASES.get(role_str, AgentRole.EXPERT)


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
    toolsets = [t for t in toolsets if t not in BLOCKED_TOOLSET_NAMES]

    yaml_config = _get_role_config_from_yaml(role.value)
    model = override_model or yaml_config.get("model")

    return {
        "role": role.value,
        "goal": goal,
        "context": context,
        "toolsets": toolsets,
        "system_prompt": get_role_prompt(role, goal, context),
        "model": model,
        "max_iterations": max_iterations,
    }


def available_roles() -> List[Dict[str, str]]:
    """Return a list of available roles with descriptions for UI display."""
    return [
        {
            "name": role.value,
            "description": ROLE_DESCRIPTIONS[role],
            "toolsets": get_role_toolsets(role),
        }
        for role in AgentRole
        if role != AgentRole.COORDINATOR
    ]


def create_cron_agent_config(
    prompt: str,
    schedule: str,
    team: str = "",
    name: str = "",
    skills: Optional[List[str]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a Cron agent configuration for scheduled task execution.

    v0.3.0: Cron-Team binding -- cron agents can be bound to a team
    and their output is automatically sedimented to team memory.

    Args:
        prompt: The task prompt for the cron job.
        schedule: Cron schedule expression (e.g. "0 9 * * *").
        team: Team name for output sedimentation.
        name: Optional name for the cron job.
        skills: Optional list of skill names to enable.
        model: Optional model override.

    Returns:
        Complete cron agent configuration dict.
    """
    config = build_role_config(
        role=AgentRole.CRON,
        goal=prompt,
        context=f"Schedule: {schedule}" + (f"\nTeam: {team}" if team else ""),
        override_model=model,
    )
    config["schedule"] = schedule
    config["cron_team"] = team
    config["cron_name"] = name or f"cron-{os.urandom(3).hex()}"
    config["skills"] = skills or []
    config["sediment_to_team"] = bool(team)
    return config
