#!/usr/bin/env python3
"""Run the focused Phase C live gate through a managed SSH tunnel to the live host."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_on_ali_hermes import build_askpass, load_remote_config

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = Path("/tmp/phase-c-live-gate")
DEFAULT_PUBLIC_URL = "http://111.229.194.203/manage"


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def choose_local_port(preferred_port: int) -> int:
    if preferred_port > 0 and not port_in_use("127.0.0.1", preferred_port):
        return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for {host}:{port} tunnel readiness")


def start_tunnel(local_port: int, remote_port: int, remote_bind_host: str) -> tuple[subprocess.Popen[str], str | None]:
    remote = load_remote_config()
    env, ssh_prefix, temp_script = build_askpass(remote["password"])
    cmd = [
        *ssh_prefix,
        "-o",
        "ExitOnForwardFailure=yes",
        "-N",
        "-L",
        f"{local_port}:{remote_bind_host}:{remote_port}",
        f"{remote['user']}@{remote['host']}",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        wait_for_port("127.0.0.1", local_port)
    except Exception:
        try:
            proc.terminate()
            stderr = ""
            try:
                _, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                _, stderr = proc.communicate()
            raise RuntimeError(stderr.strip() or "Failed to establish SSH tunnel")
        finally:
            if temp_script:
                try:
                    os.unlink(temp_script)
                except FileNotFoundError:
                    pass
    return proc, temp_script


def stop_tunnel(proc: subprocess.Popen[str], temp_script: str | None) -> None:
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    finally:
        if temp_script:
            try:
                os.unlink(temp_script)
            except FileNotFoundError:
                pass


def run_gate(base_url: str, output_dir: Path) -> subprocess.CompletedProcess[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["BASE_URL"] = base_url.rstrip("/")
    env["OUTPUT_DIR"] = str(output_dir)
    return subprocess.run(
        ["node", "tests/phase_c_collaboration_live_gate_check.js"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-port", type=int, default=58080)
    parser.add_argument("--remote-port", type=int, default=80)
    parser.add_argument("--remote-bind-host", default="127.0.0.1")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--probe-public-url",
        default="",
        help="Optional non-blocking public URL probe. Empty disables it.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    tunnel_dir = output_dir / "tunnel"
    public_dir = output_dir / "public"
    local_port = choose_local_port(args.local_port)
    canonical_base = f"http://127.0.0.1:{local_port}/manage"

    tunnel_proc = None
    temp_script = None
    try:
        tunnel_proc, temp_script = start_tunnel(local_port, args.remote_port, args.remote_bind_host)
        tunnel_result = run_gate(canonical_base, tunnel_dir)
    finally:
        if tunnel_proc is not None:
            stop_tunnel(tunnel_proc, temp_script)

    public_probe_url = args.probe_public_url.strip()
    public_result = None
    if public_probe_url:
        public_result = run_gate(public_probe_url, public_dir)

    print(f"[canonical-gate] {canonical_base}")

    if tunnel_result.stdout:
        print(tunnel_result.stdout.strip())
    if tunnel_result.stderr:
        print(tunnel_result.stderr.strip(), file=sys.stderr)

    if public_result and public_result.stdout:
        print("\n[public-probe]")
        print(public_result.stdout.strip())
    if public_result and public_result.stderr:
        print(public_result.stderr.strip(), file=sys.stderr)

    if tunnel_result.returncode != 0:
        return tunnel_result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
