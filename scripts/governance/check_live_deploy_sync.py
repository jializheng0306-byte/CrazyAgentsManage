#!/usr/bin/env python3
"""Compare local repo files against live deploy copies over SSH."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

REMOTE_CONFIG_REL = Path("src/webui/remote_config.json")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_manifest(path: Path) -> dict:
    return json.loads(read_text(path))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def remote_sha256(
    workspace_root: Path,
    user: str,
    host: str,
    remote_file: str,
    batch_mode: str,
    password_env: str | None,
) -> tuple[str | None, str | None]:
    command = (
        f"if [ -f {shlex.quote(remote_file)} ]; then "
        f"sha256sum {shlex.quote(remote_file)} | awk '{{print $1}}'; "
        "else echo __MISSING__; fi"
    )
    ssh_args = ["ssh"]
    if batch_mode in {"yes", "no"}:
        ssh_args.extend(["-o", f"BatchMode={batch_mode}"])
    ssh_args.extend([f"{user}@{host}", command])
    env = dict(os.environ)
    script_path: str | None = None
    password = resolve_password(workspace_root, password_env)
    if password:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write("#!/bin/sh\n")
            handle.write(f"echo {shlex.quote(password)}\n")
            script_path = handle.name
        os.chmod(script_path, 0o700)
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["SSH_ASKPASS"] = script_path
        env["SSH_ASKPASS_REQUIRE"] = "force"
        ssh_args = [
            "setsid",
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            f"{user}@{host}",
            command,
        ]
    try:
        result = subprocess.run(ssh_args, text=True, capture_output=True, check=False, env=env)
    finally:
        if script_path:
            try:
                os.unlink(script_path)
            except FileNotFoundError:
                pass
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout).strip() or "ssh failed"
        return None, stderr
    value = result.stdout.strip()
    if value == "__MISSING__":
        return None, None
    return value, None


def build_row(workspace_root: Path, profile: dict, rel_path: str, batch_mode: str) -> dict:
    source_root = (workspace_root / profile["sourceRepoRoot"]).resolve()
    local_file = (source_root / rel_path).resolve()
    remote_file = str(Path(profile["deployRoot"]) / rel_path)
    row = {
        "profile": profile["id"],
        "sourceRepoRoot": str(source_root),
        "path": rel_path,
        "remoteFile": remote_file,
        "localExists": local_file.exists(),
        "remoteExists": False,
        "inSync": False,
        "error": None,
    }

    if not local_file.exists():
        row["error"] = f"local file missing: {local_file}"
        return row

    row["localSha256"] = sha256_file(local_file)
    remote_hash, remote_error = remote_sha256(
        workspace_root,
        profile["user"],
        profile["host"],
        remote_file,
        batch_mode,
        profile.get("passwordEnv"),
    )
    if remote_error:
        row["error"] = remote_error
        return row
    if remote_hash is None:
        return row

    row["remoteExists"] = True
    row["remoteSha256"] = remote_hash
    row["inSync"] = row["localSha256"] == row["remoteSha256"]
    return row


def render_text(results: list[dict]) -> str:
    lines = []
    for item in results:
        state = "OK" if item["inSync"] else "DRIFT"
        if item.get("error"):
            state = "ERROR"
        elif item["localExists"] and not item["remoteExists"]:
            state = "MISSING"
        lines.append(f"[{state}] {item['profile']} :: {item['path']}")
        if item.get("error"):
            lines.append(f"  error: {item['error']}")
        elif not item["remoteExists"]:
            lines.append(f"  remote missing: {item['remoteFile']}")
        elif not item["inSync"]:
            lines.append(f"  local : {item['localSha256']}")
            lines.append(f"  remote: {item['remoteSha256']}")
    if not lines:
        return "SKIP: no live deploy sync profiles selected"
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument(
        "--manifest",
        default="scripts/governance/live-deploy-sync.manifest.json",
    )
    parser.add_argument("--profile", action="append", default=[])
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--batch-mode", choices=["yes", "no"], default="yes")
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root).resolve()
    manifest_path = (workspace_root / args.manifest).resolve()
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = load_manifest(manifest_path)
    profiles = resolve_profiles(manifest, args.profile)

    if args.list_profiles:
        payload = [
            {
                "id": profile["id"],
                "sourceRepoRoot": profile["sourceRepoRoot"],
                "host": profile["host"],
                "deployRoot": profile["deployRoot"],
                "compareFiles": profile["compareFiles"],
            }
            for profile in profiles
        ]
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for profile in payload:
                print(
                    f"{profile['id']}: {profile['sourceRepoRoot']} -> "
                    f"{profile['host']}:{profile['deployRoot']}"
                )
        return 0

    rows: list[dict] = []
    for profile in profiles:
        for rel_path in profile.get("compareFiles", []):
            rows.append(build_row(workspace_root, profile, rel_path, args.batch_mode))

    ok = all(
        row["localExists"] and row["remoteExists"] and row["inSync"] and not row.get("error")
        for row in rows
    )
    payload = {
        "manifestVersion": manifest.get("manifestVersion"),
        "ok": ok,
        "results": rows,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(rows))

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
