#!/usr/bin/env python3
"""Install the Hermes AI cron guard into a Hermes runtime checkout."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


IMPORT_NEEDLE = "import re\nimport sys\n"
IMPORT_REPLACEMENT = "import re\nimport subprocess\nimport sys\n"

CONSTANT_NEEDLE = "_CRON_INVISIBLE_CHARS = {\n    '\\u200b', '\\u200c', '\\u200d', '\\u2060', '\\ufeff',\n    '\\u202a', '\\u202b', '\\u202c', '\\u202d', '\\u202e',\n}\n"
CONSTANT_APPEND = """

_PROMPT_LOCAL_SCRIPT_REF_RE = re.compile(
    r"(?P<path>(?:~/|/|\\./|\\.\\./|[A-Za-z0-9._-]+/)[^\\s`\\\"'<>]+\\.(?:py|sh|bash))"
)
_SCRIPT_MIRROR_MANIFEST_FILENAME = ".mirror-manifest.json"
"""

SCRIPT_VALIDATION_NEEDLE = """def _validate_cron_script_path(script: Optional[str]) -> Optional[str]:
    \"\"\"Validate a cron job script path at the API boundary.

    Scripts must be relative paths that resolve within HERMES_HOME/scripts/.
    Absolute paths and ~ expansion are rejected to prevent arbitrary script
    execution via prompt injection.

    Returns an error string if blocked, else None (valid).
    \"\"\"
    if not script or not script.strip():
        return None  # empty/None = clearing the field, always OK

    from hermes_constants import get_hermes_home

    raw = script.strip()

    # Reject absolute paths and ~ expansion at the API boundary.
    # Only relative paths within ~/.hermes/scripts/ are allowed.
    if raw.startswith((\"/\", \"~\")) or (len(raw) >= 2 and raw[1] == \":\"):
        return (
            f\"Script path must be relative to ~/.hermes/scripts/. \"
            f\"Got absolute or home-relative path: {raw!r}. \"
            f\"Place scripts in ~/.hermes/scripts/ and use just the filename.\"
        )

    # Validate containment after resolution
    from tools.path_security import validate_within_dir

    scripts_dir = get_hermes_home() / \"scripts\"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    containment_error = validate_within_dir(scripts_dir / raw, scripts_dir)
    if containment_error:
        return (
            f\"Script path escapes the scripts directory via traversal: {raw!r}\"
        )

    return None
"""

SCRIPT_VALIDATION_REPLACEMENT = """def _validate_cron_script_path(script: Optional[str]) -> Optional[str]:
    \"\"\"Validate a cron job script path at the API boundary.

    Scripts must be relative paths that resolve within HERMES_HOME/scripts/.
    Absolute paths and ~ expansion are rejected to prevent arbitrary script
    execution via prompt injection.

    Returns an error string if blocked, else None (valid).
    \"\"\"
    if not script or not script.strip():
        return None  # empty/None = clearing the field, always OK

    from hermes_constants import get_hermes_home

    raw = script.strip()

    # Reject absolute paths and ~ expansion at the API boundary.
    # Only relative paths within ~/.hermes/scripts/ are allowed.
    if raw.startswith((\"/\", \"~\")) or (len(raw) >= 2 and raw[1] == \":\"):
        return (
            f\"Script path must be relative to ~/.hermes/scripts/. \"
            f\"Got absolute or home-relative path: {raw!r}. \"
            f\"Place scripts in ~/.hermes/scripts/ and use just the filename.\"
        )

    # Validate containment after resolution
    from tools.path_security import validate_within_dir

    scripts_dir = get_hermes_home() / \"scripts\"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    containment_error = validate_within_dir(scripts_dir / raw, scripts_dir)
    if containment_error:
        return (
            f\"Script path escapes the scripts directory via traversal: {raw!r}\"
        )

    resolved = (scripts_dir / raw).resolve()
    if not resolved.exists():
        return (
            f\"Script path does not exist under ~/.hermes/scripts/: {resolved}\"
        )
    if not resolved.is_file():
        return (
            f\"Script path is not a file under ~/.hermes/scripts/: {resolved}\"
        )

    return None
"""

HELPER_BLOCK = """

def _load_script_mirror_manifest() -> Dict[str, Any]:
    from hermes_constants import get_hermes_home

    scripts_dir = get_hermes_home() / "scripts"
    manifest_path = scripts_dir / _SCRIPT_MIRROR_MANIFEST_FILENAME
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to read script mirror manifest %s: %s", manifest_path, exc)
        return {}
    return data if isinstance(data, dict) else {}


def _find_git_repo_root(path: Path) -> Optional[Path]:
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def _is_git_tracked(repo_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "-c", f"safe.directory={repo_root}", "ls-files", "--error-unmatch", "--", relative_path],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0


def _validate_mirrored_script_registration(script: Optional[str]) -> Optional[str]:
    if not script or not script.strip():
        return None

    manifest = _load_script_mirror_manifest()
    scripts = manifest.get("scripts", {}) if isinstance(manifest, dict) else {}
    entry = scripts.get(script)
    if not isinstance(entry, dict):
        return (
            f"Script {script!r} is not registered in ~/.hermes/scripts/{_SCRIPT_MIRROR_MANIFEST_FILENAME}. "
            "Mirror scripts used by AI cron jobs must declare a repo source-of-truth."
        )

    repo_root = str(entry.get("repo_root") or "").strip()
    source_relpath = str(entry.get("source_relpath") or "").strip()
    if not repo_root or not source_relpath:
        return (
            f"Script {script!r} has an incomplete mirror manifest entry. "
            "Expected repo_root and source_relpath."
        )

    repo_root_path = Path(repo_root).expanduser().resolve()
    source_path = (repo_root_path / source_relpath).resolve()
    if not source_path.exists():
        return f"Mirror source does not exist for {script!r}: {source_path}"
    if not source_path.is_file():
        return f"Mirror source is not a file for {script!r}: {source_path}"
    if not _is_git_tracked(repo_root_path, source_relpath):
        return f"Mirror source is not git-tracked for {script!r}: {source_path}"
    return None


def _iter_prompt_local_script_refs(prompt: str) -> List[str]:
    seen = set()
    refs: List[str] = []
    for match in _PROMPT_LOCAL_SCRIPT_REF_RE.finditer(prompt or ""):
        candidate = match.group("path").strip().strip("`'\\\"()[]{}<>.,;:")
        if not candidate or "://" in candidate or candidate in seen:
            continue
        seen.add(candidate)
        refs.append(candidate)
    return refs


def _resolve_prompt_local_script_ref(path_text: str, workdir: Optional[str]) -> tuple[Optional[Path], Optional[str]]:
    raw = str(path_text or "").strip()
    if not raw:
        return None, None
    if raw.startswith(("/", "~")):
        return Path(raw).expanduser().resolve(), None
    if not workdir:
        return None, (
            f"Relative script reference {raw!r} requires workdir so Hermes can "
            "resolve and validate it before cron creation."
        )
    return (Path(workdir).expanduser() / raw).resolve(), None


def _validate_prompt_local_script_refs(prompt: str, workdir: Optional[str]) -> Optional[str]:
    refs = _iter_prompt_local_script_refs(prompt)
    if not refs:
        return None

    errors: List[str] = []
    from hermes_constants import get_hermes_home
    scripts_dir = (get_hermes_home() / "scripts").resolve()
    for raw in refs:
        resolved, resolve_error = _resolve_prompt_local_script_ref(raw, workdir)
        if resolve_error:
            errors.append(resolve_error)
            continue
        if resolved is None:
            continue
        if not resolved.exists():
            errors.append(f"Referenced script does not exist: {resolved}")
            continue
        if not resolved.is_file():
            errors.append(f"Referenced script is not a file: {resolved}")
            continue
        try:
            relative_to_scripts = resolved.relative_to(scripts_dir)
        except ValueError:
            relative_to_scripts = None
        if relative_to_scripts is not None:
            registration_error = _validate_mirrored_script_registration(str(relative_to_scripts))
            if registration_error:
                errors.append(registration_error)
            continue
        repo_root = _find_git_repo_root(resolved)
        if repo_root is None:
            errors.append(f"Referenced script is outside any git repository: {resolved}")
            continue
        relative_path = str(resolved.relative_to(repo_root))
        if not _is_git_tracked(repo_root, relative_path):
            errors.append(f"Referenced script is not git-tracked in {repo_root}: {resolved}")

    if errors:
        details = "; ".join(errors)
        return (
            "Blocked: cron prompts may only reference existing, git-tracked "
            f"local scripts. {details}"
        )
    return None


def _validate_ai_cron_script(script: Optional[str]) -> Optional[str]:
    path_error = _validate_cron_script_path(script)
    if path_error:
        return path_error
    return _validate_mirrored_script_registration(script)
"""

OLD_IS_GIT_TRACKED = """def _is_git_tracked(repo_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", relative_path],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0
"""

NEW_IS_GIT_TRACKED = """def _is_git_tracked(repo_root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "-c", f"safe.directory={repo_root}", "ls-files", "--error-unmatch", "--", relative_path],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0
"""

OLD_VALIDATE_PROMPT_LOCAL_SCRIPT_REFS = """def _validate_prompt_local_script_refs(prompt: str, workdir: Optional[str]) -> Optional[str]:
    refs = _iter_prompt_local_script_refs(prompt)
    if not refs:
        return None

    errors: List[str] = []
    for raw in refs:
        resolved, resolve_error = _resolve_prompt_local_script_ref(raw, workdir)
        if resolve_error:
            errors.append(resolve_error)
            continue
        if resolved is None:
            continue
        if not resolved.exists():
            errors.append(f"Referenced script does not exist: {resolved}")
            continue
        if not resolved.is_file():
            errors.append(f"Referenced script is not a file: {resolved}")
            continue
        repo_root = _find_git_repo_root(resolved)
        if repo_root is None:
            errors.append(f"Referenced script is outside any git repository: {resolved}")
            continue
        relative_path = str(resolved.relative_to(repo_root))
        if not _is_git_tracked(repo_root, relative_path):
            errors.append(f"Referenced script is not git-tracked in {repo_root}: {resolved}")

    if errors:
        details = "; ".join(errors)
        return (
            "Blocked: cron prompts may only reference existing, git-tracked "
            f"local scripts. {details}"
        )
    return None
"""

NEW_VALIDATE_PROMPT_LOCAL_SCRIPT_REFS = """def _validate_prompt_local_script_refs(prompt: str, workdir: Optional[str]) -> Optional[str]:
    refs = _iter_prompt_local_script_refs(prompt)
    if not refs:
        return None

    errors: List[str] = []
    from hermes_constants import get_hermes_home
    scripts_dir = (get_hermes_home() / "scripts").resolve()
    for raw in refs:
        resolved, resolve_error = _resolve_prompt_local_script_ref(raw, workdir)
        if resolve_error:
            errors.append(resolve_error)
            continue
        if resolved is None:
            continue
        if not resolved.exists():
            errors.append(f"Referenced script does not exist: {resolved}")
            continue
        if not resolved.is_file():
            errors.append(f"Referenced script is not a file: {resolved}")
            continue
        try:
            relative_to_scripts = resolved.relative_to(scripts_dir)
        except ValueError:
            relative_to_scripts = None
        if relative_to_scripts is not None:
            registration_error = _validate_mirrored_script_registration(str(relative_to_scripts))
            if registration_error:
                errors.append(registration_error)
            continue
        repo_root = _find_git_repo_root(resolved)
        if repo_root is None:
            errors.append(f"Referenced script is outside any git repository: {resolved}")
            continue
        relative_path = str(resolved.relative_to(repo_root))
        if not _is_git_tracked(repo_root, relative_path):
            errors.append(f"Referenced script is not git-tracked in {repo_root}: {resolved}")

    if errors:
        details = "; ".join(errors)
        return (
            "Blocked: cron prompts may only reference existing, git-tracked "
            f"local scripts. {details}"
        )
    return None
"""


def ensure_contains(text: str, needle: str, insert_after: str) -> str:
    if needle in text:
        return text
    marker = insert_after
    if marker not in text:
        raise RuntimeError(f"expected marker not found: {insert_after[:80]!r}")
    return text.replace(marker, marker + needle, 1)


def patch_cronjob_tools(text: str) -> str:
    if IMPORT_REPLACEMENT not in text:
        if IMPORT_NEEDLE not in text:
            raise RuntimeError("failed to locate import block")
        text = text.replace(IMPORT_NEEDLE, IMPORT_REPLACEMENT, 1)

    text = ensure_contains(text, CONSTANT_APPEND, CONSTANT_NEEDLE)

    if "_validate_ai_cron_script" not in text:
        if SCRIPT_VALIDATION_NEEDLE not in text and SCRIPT_VALIDATION_REPLACEMENT not in text:
            raise RuntimeError("failed to locate _validate_cron_script_path")
        if SCRIPT_VALIDATION_REPLACEMENT not in text:
            text = text.replace(SCRIPT_VALIDATION_NEEDLE, SCRIPT_VALIDATION_REPLACEMENT, 1)
        anchor = SCRIPT_VALIDATION_REPLACEMENT
        if anchor not in text:
            anchor = SCRIPT_VALIDATION_NEEDLE
        text = text.replace(anchor, anchor + HELPER_BLOCK, 1)

    if OLD_IS_GIT_TRACKED in text and NEW_IS_GIT_TRACKED not in text:
        text = text.replace(OLD_IS_GIT_TRACKED, NEW_IS_GIT_TRACKED, 1)

    if OLD_VALIDATE_PROMPT_LOCAL_SCRIPT_REFS in text and NEW_VALIDATE_PROMPT_LOCAL_SCRIPT_REFS not in text:
        text = text.replace(
            OLD_VALIDATE_PROMPT_LOCAL_SCRIPT_REFS,
            NEW_VALIDATE_PROMPT_LOCAL_SCRIPT_REFS,
            1,
        )

    create_old = """            canonical_skills = _canonical_skills(skill, skills)\n            _no_agent = bool(no_agent)\n"""
    create_new = """            canonical_skills = _canonical_skills(skill, skills)\n            _no_agent = bool(no_agent)\n            effective_workdir = _normalize_optional_job_value(workdir)\n"""
    if create_new not in text:
        if create_old not in text:
            raise RuntimeError("failed to locate create preamble")
        text = text.replace(create_old, create_new, 1)

    prompt_old = """            if prompt:\n                scan_error = _scan_cron_prompt(prompt)\n                if scan_error:\n                    return tool_error(scan_error, success=False)\n\n            # Validate script path before storing\n            if script:\n                script_error = _validate_cron_script_path(script)\n                if script_error:\n                    return tool_error(script_error, success=False)\n"""
    prompt_new = """            if prompt:\n                scan_error = _scan_cron_prompt(prompt)\n                if scan_error:\n                    return tool_error(scan_error, success=False)\n                prompt_script_error = _validate_prompt_local_script_refs(prompt, effective_workdir)\n                if prompt_script_error:\n                    return tool_error(prompt_script_error, success=False)\n\n            # Validate script path before storing\n            if script:\n                script_error = _validate_ai_cron_script(script)\n                if script_error:\n                    return tool_error(script_error, success=False)\n"""
    if prompt_new not in text:
        if prompt_old in text:
            text = text.replace(prompt_old, prompt_new, 1)
        else:
            create_marker = """            if prompt:\n                scan_error = _scan_cron_prompt(prompt)\n                if scan_error:\n                    return tool_error(scan_error, success=False)\n"""
            create_marker_with_guard = create_marker + """                prompt_script_error = _validate_prompt_local_script_refs(prompt, effective_workdir)\n                if prompt_script_error:\n                    return tool_error(prompt_script_error, success=False)\n"""
            if create_marker in text and create_marker_with_guard not in text:
                text = text.replace(create_marker, create_marker_with_guard, 1)
            text = text.replace(
                "script_error = _validate_cron_script_path(script)",
                "script_error = _validate_ai_cron_script(script)",
            )
            if "prompt_script_error = _validate_prompt_local_script_refs(prompt, effective_workdir)" not in text:
                raise RuntimeError("failed to apply create prompt guard")
            if "script_error = _validate_ai_cron_script(script)" not in text:
                raise RuntimeError("failed to apply create script guard")

    workdir_old = """                context_from=context_from,\n                enabled_toolsets=enabled_toolsets or None,\n                workdir=_normalize_optional_job_value(workdir),\n                no_agent=_no_agent,\n"""
    workdir_new = """                context_from=context_from,\n                enabled_toolsets=enabled_toolsets or None,\n                workdir=effective_workdir,\n                no_agent=_no_agent,\n"""
    if workdir_new not in text:
        if workdir_old not in text:
            raise RuntimeError("failed to locate create_job call workdir block")
        text = text.replace(workdir_old, workdir_new, 1)

    update_old = """        if normalized == \"update\":\n            updates: Dict[str, Any] = {}\n            if prompt is not None:\n                scan_error = _scan_cron_prompt(prompt)\n                if scan_error:\n                    return tool_error(scan_error, success=False)\n                updates[\"prompt\"] = prompt\n"""
    update_new = """        if normalized == \"update\":\n            updates: Dict[str, Any] = {}\n            effective_workdir = job.get(\"workdir\")\n            if prompt is not None:\n                scan_error = _scan_cron_prompt(prompt)\n                if scan_error:\n                    return tool_error(scan_error, success=False)\n                updates[\"prompt\"] = prompt\n"""
    if update_new not in text:
        if update_old not in text:
            raise RuntimeError("failed to locate update preamble")
        text = text.replace(update_old, update_new, 1)

    update_script_old = """            if script is not None:\n                # Pass empty string to clear an existing script\n                if script:\n                    script_error = _validate_cron_script_path(script)\n                    if script_error:\n                        return tool_error(script_error, success=False)\n                updates[\"script\"] = _normalize_optional_job_value(script) if script else None\n"""
    update_script_new = """            if script is not None:\n                # Pass empty string to clear an existing script\n                if script:\n                    script_error = _validate_ai_cron_script(script)\n                    if script_error:\n                        return tool_error(script_error, success=False)\n                updates[\"script\"] = _normalize_optional_job_value(script) if script else None\n"""
    if update_script_new not in text:
        if update_script_old in text:
            text = text.replace(update_script_old, update_script_new, 1)
        else:
            text = text.replace(
                "script_error = _validate_cron_script_path(script)",
                "script_error = _validate_ai_cron_script(script)",
            )
            if "script_error = _validate_ai_cron_script(script)" not in text:
                raise RuntimeError("failed to locate update script validation block")

    update_workdir_old = """            if workdir is not None:\n                # Empty string clears the field (restores old behaviour);\n                # otherwise pass raw — update_job() validates / normalizes.\n                updates[\"workdir\"] = _normalize_optional_job_value(workdir) or None\n            if no_agent is not None:\n"""
    update_workdir_new = """            if workdir is not None:\n                # Empty string clears the field (restores old behaviour);\n                # otherwise pass raw — update_job() validates / normalizes.\n                effective_workdir = _normalize_optional_job_value(workdir) or None\n                updates[\"workdir\"] = effective_workdir\n            effective_prompt = prompt if prompt is not None else job.get(\"prompt\")\n            if effective_prompt and (prompt is not None or workdir is not None):\n                prompt_script_error = _validate_prompt_local_script_refs(\n                    effective_prompt,\n                    effective_workdir,\n                )\n                if prompt_script_error:\n                    return tool_error(prompt_script_error, success=False)\n            if no_agent is not None:\n"""
    if update_workdir_new not in text:
        if update_workdir_old in text:
            text = text.replace(update_workdir_old, update_workdir_new, 1)
        else:
            legacy_workdir = """            if workdir is not None:\n                # Empty string clears the field (restores old behaviour);\n                # otherwise pass raw — update_job() validates / normalizes.\n                updates[\"workdir\"] = _normalize_optional_job_value(workdir) or None\n"""
            replacement_workdir = """            if workdir is not None:\n                # Empty string clears the field (restores old behaviour);\n                # otherwise pass raw — update_job() validates / normalizes.\n                effective_workdir = _normalize_optional_job_value(workdir) or None\n                updates[\"workdir\"] = effective_workdir\n"""
            if legacy_workdir in text:
                text = text.replace(legacy_workdir, replacement_workdir, 1)
            prompt_guard_block = """            effective_prompt = prompt if prompt is not None else job.get(\"prompt\")\n            if effective_prompt and (prompt is not None or workdir is not None):\n                prompt_script_error = _validate_prompt_local_script_refs(\n                    effective_prompt,\n                    effective_workdir,\n                )\n                if prompt_script_error:\n                    return tool_error(prompt_script_error, success=False)\n"""
            insert_after = replacement_workdir if replacement_workdir in text else "                updates[\"workdir\"] = effective_workdir\n"
            if prompt_guard_block not in text and insert_after in text:
                text = text.replace(insert_after, insert_after + prompt_guard_block, 1)
            if "effective_workdir = _normalize_optional_job_value(workdir) or None" not in text:
                raise RuntimeError("failed to apply update workdir normalization")
            if "effective_prompt = prompt if prompt is not None else job.get(\"prompt\")" not in text:
                raise RuntimeError("failed to apply update prompt guard")

    return text


def install(runtime_root: Path, repo_root: Path, hermes_home: Path, manifest_source: Path) -> dict:
    target = runtime_root / "tools" / "cronjob_tools.py"
    original = target.read_text(encoding="utf-8")
    patched = patch_cronjob_tools(original)
    changed = patched != original
    if changed:
        backup = target.with_name(f"{target.name}.bak-managed-20260516")
        if not backup.exists():
            shutil.copy2(target, backup)
        target.write_text(patched, encoding="utf-8")

    scripts_dir = hermes_home / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    manifest_target = scripts_dir / ".mirror-manifest.json"
    shutil.copy2(manifest_source, manifest_target)

    return {
        "changed": changed,
        "target": str(target),
        "manifest_target": str(manifest_target),
        "repo_root": str(repo_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument(
        "--manifest-source",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "shared-context" / "hermes-script-mirror-manifest.json",
    )
    args = parser.parse_args()
    result = install(args.runtime_root, args.repo_root, args.hermes_home, args.manifest_source)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
