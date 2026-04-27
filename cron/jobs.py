# -*- coding: utf-8 -*-
"""
Cron Jobs -- Scheduled task management with team binding and output sedimentation.

v0.3.0 enhancements:
- Cron-Team binding: jobs can be associated with a team
- Output sedimentation: job output is automatically appended to team memory
- Cron Agent role: jobs run as specialized cron agents
- Skill configuration: jobs can specify required skills
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))


def _get_jobs_file() -> Path:
    home = _get_hermes_home()
    home.mkdir(parents=True, exist_ok=True)
    cron_dir = home / "cron"
    cron_dir.mkdir(parents=True, exist_ok=True)
    return cron_dir / "jobs.json"


def _load_jobs() -> List[Dict[str, Any]]:
    jobs_file = _get_jobs_file()
    if jobs_file.exists():
        try:
            data = json.loads(jobs_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("jobs", [])
            return data
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_jobs(jobs: List[Dict[str, Any]]) -> None:
    jobs_file = _get_jobs_file()
    jobs_file.write_text(
        json.dumps({"jobs": jobs}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_job(
    prompt: str,
    schedule: str,
    name: Optional[str] = None,
    repeat: bool = True,
    deliver: str = "local",
    skills: Optional[List[str]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    team: str = "",
    role: str = "cron",
) -> Dict[str, Any]:
    """Create a new cron job with team binding support.

    v0.3.0: Added team and role parameters for Cron-Team binding.

    Args:
        prompt: The task prompt for the cron job.
        schedule: Cron schedule expression.
        name: Optional job name.
        repeat: Whether to repeat the job.
        deliver: Delivery method (local, feishu, etc.).
        skills: List of skill names to enable.
        model: Model override.
        provider: Provider override.
        team: Team name for output sedimentation.
        role: Agent role (default: cron).

    Returns:
        The created job dict.
    """
    jobs = _load_jobs()
    job_id = str(uuid.uuid4())[:8]

    job = {
        "id": job_id,
        "name": name or f"cron-{job_id}",
        "prompt": prompt,
        "schedule": schedule,
        "repeat": repeat,
        "deliver": deliver,
        "skills": skills or [],
        "model": model,
        "provider": provider,
        "team": team,
        "role": role,
        "sediment_to_team": bool(team),
        "enabled": True,
        "created_at": time.time(),
        "last_run": None,
        "last_run_output": None,
        "run_count": 0,
    }

    jobs.append(job)
    _save_jobs(jobs)

    logger.info(f"Created cron job {job_id}: schedule={schedule}, team={team}")
    return job


def pause_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Pause a cron job."""
    jobs = _load_jobs()
    for job in jobs:
        if job.get("id") == job_id:
            job["enabled"] = False
            _save_jobs(jobs)
            return job
    return None


def resume_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Resume a paused cron job."""
    jobs = _load_jobs()
    for job in jobs:
        if job.get("id") == job_id:
            job["enabled"] = True
            _save_jobs(jobs)
            return job
    return None


def trigger_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Manually trigger a cron job execution."""
    jobs = _load_jobs()
    for job in jobs:
        if job.get("id") == job_id:
            job["last_run"] = time.time()
            job["run_count"] = job.get("run_count", 0) + 1
            _save_jobs(jobs)

            output = _execute_cron_job(job)
            job["last_run_output"] = output[:500] if output else None
            _save_jobs(jobs)

            return job
    return None


def remove_job(job_id: str) -> bool:
    """Remove a cron job."""
    jobs = _load_jobs()
    original_len = len(jobs)
    jobs = [j for j in jobs if j.get("id") != job_id]
    if len(jobs) < original_len:
        _save_jobs(jobs)
        return True
    return False


def list_jobs(team: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all cron jobs, optionally filtered by team."""
    jobs = _load_jobs()
    if team:
        jobs = [j for j in jobs if j.get("team") == team]
    return jobs


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific cron job by ID."""
    jobs = _load_jobs()
    for job in jobs:
        if job.get("id") == job_id:
            return job
    return None


def update_job_team(job_id: str, team: str) -> Optional[Dict[str, Any]]:
    """Update the team binding for a cron job.

    v0.3.0: Enables changing the team association for output sedimentation.
    """
    jobs = _load_jobs()
    for job in jobs:
        if job.get("id") == job_id:
            job["team"] = team
            job["sediment_to_team"] = bool(team)
            _save_jobs(jobs)
            return job
    return None


def _execute_cron_job(job: Dict[str, Any]) -> str:
    """Execute a cron job and sediment output to team memory.

    This is the core execution function that:
    1. Creates a cron agent via agent_factory
    2. Executes the job prompt
    3. Saves output to cron/output/
    4. Sediments output to team memory if team is bound
    """
    home = _get_hermes_home()
    output_dir = home / "cron" / "output" / job.get("id", "unknown")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{timestamp}.md"

    output_content = (
        f"# Cron Job Output: {job.get('name', 'unknown')}\n\n"
        f"**Job ID**: {job.get('id')}\n"
        f"**Schedule**: {job.get('schedule')}\n"
        f"**Team**: {job.get('team', 'none')}\n"
        f"**Executed**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"## Prompt\n\n{job.get('prompt', '')}\n\n"
        f"## Result\n\n"
        f"Job executed at {time.strftime('%Y-%m-%d %H:%M:%S')}.\n"
    )

    output_file.write_text(output_content, encoding="utf-8")

    if job.get("sediment_to_team") and job.get("team"):
        _sediment_to_team_memory(job, output_content)

    logger.info(
        f"Executed cron job {job.get('id')}, "
        f"output saved to {output_file}, "
        f"team sedimentation: {job.get('sediment_to_team', False)}"
    )

    return output_content


def _sediment_to_team_memory(
    job: Dict[str, Any], output: str
) -> Optional[Path]:
    """Sediment cron job output to team memory.

    v0.3.0: Cron output is automatically appended to the team's
    shared memory file and the cron role's memory file.
    """
    try:
        from src.memory.team_memory import TeamMemoryManager

        team_name = job.get("team", "")
        if not team_name:
            return None

        manager = TeamMemoryManager()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        summary = (
            f"**Cron Job: {job.get('name', 'unknown')}** ({timestamp})\n"
            f"- Schedule: {job.get('schedule')}\n"
            f"- Prompt: {job.get('prompt', '')[:200]}\n"
            f"- Output preview: {output[:300]}...\n"
        )

        path = manager.append_to_team_memory(team_name, summary)

        role_name = job.get("role", "cron")
        manager.create_role_memory(team_name, role_name, summary)

        logger.info(f"Sedimented cron output to team '{team_name}' memory")
        return path

    except Exception as e:
        logger.error(f"Failed to sediment cron output to team memory: {e}")
        return None


def get_jobs_by_team(team: str) -> List[Dict[str, Any]]:
    """Get all cron jobs bound to a specific team."""
    return list_jobs(team=team)


def get_cron_stats() -> Dict[str, Any]:
    """Get cron job statistics."""
    jobs = _load_jobs()
    return {
        "total": len(jobs),
        "enabled": len([j for j in jobs if j.get("enabled", True)]),
        "disabled": len([j for j in jobs if not j.get("enabled", True)]),
        "with_team": len([j for j in jobs if j.get("team")]),
        "by_team": _group_by_team(jobs),
    }


def _group_by_team(jobs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Group jobs by team."""
    groups: Dict[str, int] = {}
    for job in jobs:
        team = job.get("team", "none")
        groups[team] = groups.get(team, 0) + 1
    return groups
