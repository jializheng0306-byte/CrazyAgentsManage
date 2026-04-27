# -*- coding: utf-8 -*-
"""
Cronjob Tools -- Enhanced cron job management tools for agents.

v0.3.0: Provides tools for agents to interact with the cron system:
- Create scheduled jobs with team binding
- List and manage cron jobs
- View cron job output
- Bind/unbind teams to cron jobs
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def cron_create(
    prompt: str,
    schedule: str,
    name: str = "",
    team: str = "",
    skills: Optional[List[str]] = None,
    model: Optional[str] = None,
    repeat: bool = True,
    deliver: str = "local",
) -> Dict[str, Any]:
    """Create a new cron job.

    Tool interface for agents to create scheduled tasks.

    Args:
        prompt: The task prompt for the cron job.
        schedule: Cron schedule expression (e.g. "0 9 * * *" for daily at 9am).
        name: Optional job name.
        team: Team name for output sedimentation.
        skills: List of skill names to enable.
        model: Model override.
        repeat: Whether to repeat the job.
        deliver: Delivery method.

    Returns:
        Created job configuration dict.
    """
    from cron.jobs import create_job

    return create_job(
        prompt=prompt,
        schedule=schedule,
        name=name or None,
        repeat=repeat,
        deliver=deliver,
        skills=skills,
        model=model,
        team=team,
    )


def cron_list(team: str = "") -> List[Dict[str, Any]]:
    """List cron jobs, optionally filtered by team.

    Args:
        team: Filter by team name.

    Returns:
        List of cron job dicts.
    """
    from cron.jobs import list_jobs

    return list_jobs(team=team or None)


def cron_pause(job_id: str) -> Dict[str, Any]:
    """Pause a cron job.

    Args:
        job_id: The cron job ID to pause.

    Returns:
        Updated job dict or error.
    """
    from cron.jobs import pause_job

    job = pause_job(job_id)
    if job:
        return job
    return {"error": f"Job {job_id} not found"}


def cron_resume(job_id: str) -> Dict[str, Any]:
    """Resume a paused cron job.

    Args:
        job_id: The cron job ID to resume.

    Returns:
        Updated job dict or error.
    """
    from cron.jobs import resume_job

    job = resume_job(job_id)
    if job:
        return job
    return {"error": f"Job {job_id} not found"}


def cron_run(job_id: str) -> Dict[str, Any]:
    """Manually trigger a cron job execution.

    Args:
        job_id: The cron job ID to trigger.

    Returns:
        Job execution result.
    """
    from cron.jobs import trigger_job

    job = trigger_job(job_id)
    if job:
        return job
    return {"error": f"Job {job_id} not found"}


def cron_delete(job_id: str) -> Dict[str, Any]:
    """Delete a cron job.

    Args:
        job_id: The cron job ID to delete.

    Returns:
        Success or error dict.
    """
    from cron.jobs import remove_job

    if remove_job(job_id):
        return {"success": True, "job_id": job_id}
    return {"error": f"Job {job_id} not found"}


def cron_output(job_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get output history for a cron job.

    Args:
        job_id: The cron job ID.
        limit: Maximum number of output entries to return.

    Returns:
        List of output entries.
    """
    import os

    hermes_home = Path(
        os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    )
    output_dir = hermes_home / "cron" / "output" / job_id
    outputs = []

    if output_dir.exists():
        for f in sorted(output_dir.glob("*.md"), reverse=True)[:limit]:
            content = f.read_text(encoding="utf-8")
            outputs.append({
                "filename": f.name,
                "content": content[:5000],
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
            })

    return outputs


def cron_bind_team(job_id: str, team: str) -> Dict[str, Any]:
    """Bind a cron job to a team for output sedimentation.

    v0.3.0: When a cron job is bound to a team, its output is
    automatically appended to the team's shared memory after execution.

    Args:
        job_id: The cron job ID.
        team: Team name to bind.

    Returns:
        Updated job dict or error.
    """
    from cron.jobs import update_job_team

    job = update_job_team(job_id, team)
    if job:
        return job
    return {"error": f"Job {job_id} not found"}


def cron_stats() -> Dict[str, Any]:
    """Get cron system statistics.

    Returns:
        Statistics dict with total/enabled/disabled counts and team grouping.
    """
    from cron.jobs import get_cron_stats

    return get_cron_stats()


CRON_TOOLS = {
    "cron_create": {
        "func": cron_create,
        "description": "Create a new cron job with optional team binding",
        "parameters": ["prompt", "schedule", "name", "team", "skills", "model"],
    },
    "cron_list": {
        "func": cron_list,
        "description": "List cron jobs, optionally filtered by team",
        "parameters": ["team"],
    },
    "cron_pause": {
        "func": cron_pause,
        "description": "Pause a cron job",
        "parameters": ["job_id"],
    },
    "cron_resume": {
        "func": cron_resume,
        "description": "Resume a paused cron job",
        "parameters": ["job_id"],
    },
    "cron_run": {
        "func": cron_run,
        "description": "Manually trigger a cron job execution",
        "parameters": ["job_id"],
    },
    "cron_delete": {
        "func": cron_delete,
        "description": "Delete a cron job",
        "parameters": ["job_id"],
    },
    "cron_output": {
        "func": cron_output,
        "description": "Get output history for a cron job",
        "parameters": ["job_id", "limit"],
    },
    "cron_bind_team": {
        "func": cron_bind_team,
        "description": "Bind a cron job to a team for output sedimentation",
        "parameters": ["job_id", "team"],
    },
    "cron_stats": {
        "func": cron_stats,
        "description": "Get cron system statistics",
        "parameters": [],
    },
}
