#!/usr/bin/env python3
"""Audit Hermes AI cron jobs against local-script governance rules."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


PROMPT_LOCAL_SCRIPT_REF_RE = r"(?P<path>(?:~/|/|\./|\.\./|[A-Za-z0-9._-]+/)[^\s`\"'<>]+\.(?:py|sh|bash))"


@dataclass
class Finding:
    job_id: str
    job_name: str
    level: str
    message: str


def load_jobs(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("jobs", [])
    return data


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_git_repo_root(path: Path) -> Optional[Path]:
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def is_git_tracked(repo_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "-c", f"safe.directory={repo_root}", "ls-files", "--error-unmatch", "--", relative_path],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0


def normalize_prompt_refs(prompt: str) -> List[str]:
    import re

    refs: List[str] = []
    seen = set()
    for match in re.finditer(PROMPT_LOCAL_SCRIPT_REF_RE, prompt or ""):
        candidate = match.group("path").strip().strip("`'\"()[]{}<>.,;:")
        if not candidate or "://" in candidate or candidate in seen:
            continue
        seen.add(candidate)
        refs.append(candidate)
    return refs


def resolve_prompt_ref(raw: str, workdir: Optional[str]) -> tuple[Optional[Path], Optional[str]]:
    if raw.startswith(("/", "~")):
        return Path(raw).expanduser().resolve(), None
    if not workdir:
        return None, f"relative prompt script {raw!r} needs workdir"
    return (Path(workdir).expanduser() / raw).resolve(), None


def validate_manifest_entry(script_name: str, manifest: Dict[str, Any]) -> Optional[str]:
    scripts = manifest.get("scripts", {})
    entry = scripts.get(script_name)
    if not isinstance(entry, dict):
        return f"mirror script {script_name!r} is missing from manifest"
    repo_root = entry.get("repo_root")
    source_relpath = entry.get("source_relpath")
    if not repo_root or not source_relpath:
        return f"mirror script {script_name!r} has incomplete manifest entry"
    repo_path = Path(repo_root)
    source_path = repo_path / source_relpath
    if not source_path.exists():
        return f"manifest source does not exist: {source_path}"
    if not is_git_tracked(repo_path, source_relpath):
        return f"manifest source is not git-tracked: {source_path}"
    return None


def audit_jobs(jobs: List[Dict[str, Any]], manifest: Dict[str, Any], hermes_home: Path) -> List[Finding]:
    findings: List[Finding] = []
    scripts_dir = hermes_home / "scripts"
    scripts_dir_resolved = scripts_dir.resolve()

    for job in jobs:
        job_id = str(job.get("id") or "")
        job_name = str(job.get("name") or "")
        if not job.get("enabled", True):
            continue

        script = str(job.get("script") or "").strip()
        if script:
            script_path = (scripts_dir / script).resolve()
            if not script_path.exists():
                findings.append(Finding(job_id, job_name, "error", f"script file missing: {script_path}"))
            elif script_path.parent == scripts_dir.resolve():
                manifest_error = validate_manifest_entry(script, manifest)
                if manifest_error:
                    findings.append(Finding(job_id, job_name, "error", manifest_error))

        prompt = str(job.get("prompt") or "")
        workdir = job.get("workdir")
        for raw_ref in normalize_prompt_refs(prompt):
            resolved, resolve_error = resolve_prompt_ref(raw_ref, workdir)
            if resolve_error:
                findings.append(Finding(job_id, job_name, "error", resolve_error))
                continue
            if resolved is None:
                continue
            if not resolved.exists():
                findings.append(Finding(job_id, job_name, "error", f"prompt script missing: {resolved}"))
                continue
            try:
                relative_to_scripts = resolved.relative_to(scripts_dir_resolved)
            except ValueError:
                relative_to_scripts = None
            if relative_to_scripts is not None:
                manifest_error = validate_manifest_entry(str(relative_to_scripts), manifest)
                if manifest_error:
                    findings.append(Finding(job_id, job_name, "error", manifest_error))
                continue
            repo_root = find_git_repo_root(resolved)
            if repo_root is None:
                findings.append(Finding(job_id, job_name, "error", f"prompt script outside git repo: {resolved}"))
                continue
            rel = str(resolved.relative_to(repo_root))
            if not is_git_tracked(repo_root, rel):
                findings.append(Finding(job_id, job_name, "error", f"prompt script not git-tracked: {resolved}"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True, help="Path to ~/.hermes/cron/jobs.json")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to .mirror-manifest.json")
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--include-disabled", action="store_true")
    args = parser.parse_args()

    jobs = load_jobs(args.jobs)
    if args.include_disabled:
        pass
    else:
        jobs = [job for job in jobs if job.get("enabled", True)]
    manifest = load_manifest(args.manifest)
    findings = audit_jobs(jobs, manifest, args.hermes_home)

    print(
        json.dumps(
            {
                "ok": not findings,
                "count": len(findings),
                "findings": [finding.__dict__ for finding in findings],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
