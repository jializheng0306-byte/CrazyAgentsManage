#!/usr/bin/env python3
"""Sync tracked repo files into non-git live deploy copies over SSH/SCP."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parent
REMOTE_CONFIG_REL = Path("src/webui/remote_config.json")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_manifest(path: Path) -> dict:
    return json.loads(read_text(path))


def resolve_profiles(manifest: dict, requested: list[str]) -> list[dict]:
    profiles = manifest.get("profiles", [])
    if not requested:
        return profiles
    wanted: set[str] = set()
    for item in requested:
        wanted.update(part.strip() for part in item.split(",") if part.strip())
    resolved = [profile for profile in profiles if profile.get("id") in wanted]
    missing = sorted(wanted - {profile.get("id") for profile in resolved})
    if missing:
        raise ValueError(f"unknown profile(s): {', '.join(missing)}")
    return resolved


def resolve_password(workspace_root: Path, password_env: str | None) -> str:
    if password_env:
        value = os.environ.get(password_env, "")
        if value:
            return value
    config_path = workspace_root / REMOTE_CONFIG_REL
    if config_path.exists():
        try:
            data = json.loads(read_text(config_path))
            return str(data.get("password", "") or "")
        except Exception:
            return ""
    return ""


def build_ssh_env_and_args(
    workspace_root: Path,
    user: str,
    host: str,
    password_env: str | None,
) -> tuple[dict, list[str], list[str], str | None]:
    env = dict(os.environ)
    ssh_prefix = ["ssh"]
    scp_prefix = ["scp"]
    password = resolve_password(workspace_root, password_env)
    temp_script: str | None = None
    if password:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("#!/bin/sh\n")
            handle.write(f"echo {shlex.quote(password)}\n")
            temp_script = handle.name
        os.chmod(temp_script, 0o700)
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["SSH_ASKPASS"] = temp_script
        env["SSH_ASKPASS_REQUIRE"] = "force"
        common = [
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
        ]
        ssh_prefix = ["setsid", "ssh", *common]
        scp_prefix = ["setsid", "scp", *common]
    return env, ssh_prefix, scp_prefix, temp_script


def string_result(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or result.stderr or "").strip()


def run_remote_command(
    workspace_root: Path,
    user: str,
    host: str,
    command: str,
    password_env: str | None,
) -> tuple[bool, str]:
    env, ssh_prefix, _, temp_script = build_ssh_env_and_args(workspace_root, user, host, password_env)
    try:
        result = subprocess.run(
            [*ssh_prefix, f"{user}@{host}", command],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
    finally:
        if temp_script:
            try:
                os.unlink(temp_script)
            except FileNotFoundError:
                pass
    return result.returncode == 0, string_result(result)


def copy_file_to_remote(
    workspace_root: Path,
    local_file: Path,
    user: str,
    host: str,
    remote_file: str,
    password_env: str | None,
) -> tuple[bool, str]:
    env, _, scp_prefix, temp_script = build_ssh_env_and_args(workspace_root, user, host, password_env)
    try:
        result = subprocess.run(
            [*scp_prefix, str(local_file), f"{user}@{host}:{remote_file}"],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
    finally:
        if temp_script:
            try:
                os.unlink(temp_script)
            except FileNotFoundError:
                pass
    return result.returncode == 0, string_result(result)


def sync_profile(workspace_root: Path, profile: dict, dry_run: bool) -> dict:
    source_root = (workspace_root / profile["sourceRepoRoot"]).resolve()
    rows: list[dict] = []
    for rel_path in profile.get("compareFiles", []):
        local_file = (source_root / rel_path).resolve()
        remote_file = str(Path(profile["deployRoot"]) / rel_path)
        row = {
            "profile": profile["id"],
            "path": rel_path,
            "localFile": str(local_file),
            "remoteFile": remote_file,
            "ok": False,
            "skipped": False,
            "error": None,
        }
        if not local_file.exists():
            row["error"] = f"local file missing: {local_file}"
            rows.append(row)
            continue
        if dry_run:
            row["ok"] = True
            row["skipped"] = True
            rows.append(row)
            continue
        remote_dir = shlex.quote(str(Path(remote_file).parent))
        ok, output = run_remote_command(
            workspace_root,
            profile["user"],
            profile["host"],
            f"mkdir -p {remote_dir}",
            profile.get("passwordEnv"),
        )
        if not ok:
            row["error"] = output or f"failed to create remote directory for {remote_file}"
            rows.append(row)
            continue
        ok, output = copy_file_to_remote(
            workspace_root,
            local_file,
            profile["user"],
            profile["host"],
            remote_file,
            profile.get("passwordEnv"),
        )
        if not ok:
            row["error"] = output or f"failed to copy {local_file} -> {remote_file}"
            rows.append(row)
            continue
        row["ok"] = True
        rows.append(row)
    return {
        "id": profile["id"],
        "description": profile.get("description", ""),
        "rows": rows,
    }


def render_text(results: list[dict], verify_payload: dict | None) -> str:
    lines = []
    for profile in results:
        lines.append(f"[PROFILE] {profile['id']}")
        for row in profile["rows"]:
            if row["error"]:
                lines.append(f"  [ERROR] {row['path']}: {row['error']}")
            elif row["skipped"]:
                lines.append(f"  [DRY-RUN] {row['path']} -> {row['remoteFile']}")
            else:
                lines.append(f"  [SYNCED] {row['path']}")
    if verify_payload is not None:
        lines.append("")
        lines.append(f"[VERIFY] ok={verify_payload.get('ok')}")
    if not lines:
        lines.append("SKIP: no live deploy sync profiles selected")
    return "\n".join(lines)


def run_verify(workspace_root: Path, manifest_path: Path, requested_profiles: list[str], batch_mode: str) -> dict:
    args = [
        "python3",
        str((SCRIPT_DIR / "check_live_deploy_sync.py").resolve()),
        "--workspace-root",
        str(workspace_root),
        "--manifest",
        str(manifest_path),
        "--json",
        "--batch-mode",
        batch_mode,
    ]
    for profile in requested_profiles:
        args.extend(["--profile", profile])
    result = subprocess.run(args, text=True, capture_output=True, check=False, cwd=workspace_root)
    raw = (result.stdout or "").strip()
    if not raw:
        raise RuntimeError((result.stderr or f"verify failed: exit {result.returncode}").strip())
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument(
        "--manifest",
        default="scripts/governance/live-deploy-sync.manifest.json",
    )
    parser.add_argument("--profile", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--verify-batch-mode", choices=["yes", "no"], default="yes")
    parser.add_argument("--json", action="store_true")
    argv = [arg for arg in sys.argv[1:] if arg != "--"]
    args = parser.parse_args(argv)

    workspace_root = Path(args.workspace_root).resolve()
    manifest_path = (workspace_root / args.manifest).resolve()
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = load_manifest(manifest_path)
    profiles = resolve_profiles(manifest, args.profile)
    results = [sync_profile(workspace_root, profile, args.dry_run) for profile in profiles]
    ok = all(row["ok"] and not row["error"] for profile in results for row in profile["rows"])
    verify_payload = None
    if ok and not args.dry_run and not args.skip_verify:
        verify_payload = run_verify(workspace_root, manifest_path, args.profile, args.verify_batch_mode)
        ok = ok and bool(verify_payload.get("ok"))

    payload = {
        "ok": ok,
        "dryRun": args.dry_run,
        "verified": verify_payload is not None,
        "verifyOk": verify_payload.get("ok") if verify_payload is not None else None,
        "results": results,
        "verify": verify_payload,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(results, verify_payload))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
