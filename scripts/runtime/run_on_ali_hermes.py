#!/usr/bin/env python3
"""Run a command on ALI-HERMES using the repo's tracked remote config."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REMOTE_CONFIG_PATH = ROOT / "src" / "webui" / "remote_config.json"


def load_remote_config() -> dict:
    if not REMOTE_CONFIG_PATH.exists():
        raise FileNotFoundError(f"remote config not found: {REMOTE_CONFIG_PATH}")
    data = json.loads(REMOTE_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "host": os.environ.get("ALI_HERMES_HOST", data.get("host", "")),
        "user": os.environ.get("ALI_HERMES_USER", data.get("user", "root")),
        "password": os.environ.get("ALI_HERMES_PASSWORD")
        or os.environ.get("CRAZY_LIVE_WEBUI_PASSWORD")
        or data.get("password", ""),
    }


def build_askpass(password: str) -> tuple[dict, list[str], str | None]:
    env = dict(os.environ)
    ssh_prefix = ["ssh", "-o", "StrictHostKeyChecking=no"]
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
        ssh_prefix = [
            "setsid",
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
        ]
    return env, ssh_prefix, temp_script


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default="", help="remote working directory before running the command")
    parser.add_argument("--json", action="store_true", help="emit a JSON payload instead of raw stdout")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command_parts = [part for part in args.command if part != "--"]
    if not command_parts:
        print("ERROR: missing remote command", file=sys.stderr)
        return 1

    remote = load_remote_config()
    command = " ".join(command_parts).strip()
    if args.cwd:
        command = f"cd {shlex.quote(args.cwd)} && {command}"

    env, ssh_prefix, temp_script = build_askpass(remote["password"])
    try:
        result = subprocess.run(
            [*ssh_prefix, f"{remote['user']}@{remote['host']}", command],
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

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if args.json:
        payload = {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "host": remote["host"],
            "user": remote["user"],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif stdout:
        print(stdout)
    elif stderr:
        print(stderr, file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
