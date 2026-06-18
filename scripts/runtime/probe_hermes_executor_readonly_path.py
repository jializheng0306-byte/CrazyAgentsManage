#!/usr/bin/env python3
"""Probe Hermes-host read-only delegation readiness against executor on ALI-HERMES."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib import request as urlrequest
from urllib import error as urlerror


ROOT = Path(__file__).resolve().parents[2]
RUN_ON_ALI = ROOT / "scripts" / "runtime" / "run_on_ali_hermes.py"
ENSURE_SOURCE = ROOT / "scripts" / "runtime" / "ensure_executor_validation_source.py"


def run_local(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def run_remote(command: str) -> subprocess.CompletedProcess[str]:
    return run_local(["python3", str(RUN_ON_ALI), "--json", "--", command])


def remote_executor_prefix() -> str:
    return (
        'EXECUTOR_BIN="$(command -v executor 2>/dev/null || true)"; '
        'if [ -z "$EXECUTOR_BIN" ] && command -v npm >/dev/null 2>&1; then '
        'EXECUTOR_PREFIX="$(npm prefix -g 2>/dev/null || true)"; '
        'if [ -n "$EXECUTOR_PREFIX" ] && [ -x "$EXECUTOR_PREFIX/bin/executor" ]; then '
        'EXECUTOR_BIN="$EXECUTOR_PREFIX/bin/executor"; fi; fi; '
        'if [ -z "$EXECUTOR_BIN" ]; then '
        'for candidate in /usr/local/bin/executor /usr/bin/executor /opt/homebrew/bin/executor "$HOME/.nvm/versions/node"/*/bin/executor; do '
        'if [ -x "$candidate" ]; then EXECUTOR_BIN="$candidate"; break; fi; done; fi; '
        'if [ -z "$EXECUTOR_BIN" ]; then echo "executor CLI not found on remote host" >&2; exit 127; fi; '
    )


def run_remote_executor(command: str) -> subprocess.CompletedProcess[str]:
    return run_remote(f'{remote_executor_prefix()} "$EXECUTOR_BIN" {command}')


def http_json(url: str, attempts: int = 4) -> dict:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            req = urlrequest.Request(url, method="GET", headers={"Accept": "application/json"})
            with urlrequest.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return json.loads(body) if body else {}
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == attempts:
                raise
            time.sleep(min(1.5 * attempt, 4))
    raise last_error  # pragma: no cover


def parse_json_output(result: subprocess.CompletedProcess[str]) -> dict:
    raw = (result.stdout or "").strip()
    if not raw:
        return {
            "ok": False,
            "returncode": result.returncode,
            "stdout": "",
            "stderr": (result.stderr or "").strip(),
        }
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": raw,
            "stderr": (result.stderr or "").strip(),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://47.99.217.1/manage")
    parser.add_argument("--namespace", default="petstore-readonly-validation")
    parser.add_argument("--tool-group", default="pet")
    parser.add_argument("--tool-name", default="getPetById")
    parser.add_argument("--tool-args", default='{"petId":1}')
    parser.add_argument("--skip-invoke", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {
        "ok": False,
        "baseUrl": args.base_url,
        "namespace": args.namespace,
        "host": "ALI-HERMES",
        "toolPath": f"{args.namespace}.{args.tool_group}.{args.tool_name}",
        "checks": [],
    }

    def add_check(name: str, result: object, ok: bool) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": result})

    ensure = run_local(["python3", str(ENSURE_SOURCE), "--base-url", args.base_url, "--namespace", args.namespace])
    ensure_payload = parse_json_output(ensure)
    add_check("ensure-validation-source", ensure_payload, ensure.returncode == 0)
    if ensure.returncode != 0:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    provider = {}
    try:
        provider = http_json(args.base_url.rstrip("/") + "/api/operations/integrations/provider-mode")
    except Exception:
        provider = {}
    add_check("crazy-provider-mode", provider, provider.get("mode") == "http")

    cli_sources = parse_json_output(run_remote_executor("tools sources"))
    add_check(
        "executor-tools-sources-cli",
        cli_sources,
        bool(cli_sources.get("ok")) and args.namespace in (cli_sources.get("stdout") or ""),
    )

    source_help = parse_json_output(run_remote_executor(f"call {args.namespace} --help"))
    add_check(
        "executor-source-help",
        source_help,
        bool(source_help.get("ok")) and "Subcommands:" in (source_help.get("stdout") or ""),
    )

    tool_help = parse_json_output(
        run_remote_executor(f"call {args.namespace} {args.tool_group} {args.tool_name} --help")
    )
    add_check(
        "executor-tool-help",
        tool_help,
        bool(tool_help.get("ok")) and "Input:" in (tool_help.get("stdout") or ""),
    )

    tool_path = f"{args.namespace}.{args.tool_group}.{args.tool_name}"
    describe = parse_json_output(run_remote_executor(f"tools describe {tool_path}"))
    describe_ok = bool(describe.get("ok"))
    if describe_ok:
        try:
            body = json.loads(describe.get("stdout") or "{}")
            describe_ok = body.get("path") == tool_path
            describe["parsed"] = body
        except json.JSONDecodeError:
            describe_ok = False
    add_check("executor-tools-describe", describe, describe_ok)

    invoke_payload = None
    if not args.skip_invoke:
        invoke = parse_json_output(
            run_remote_executor(
                f'call {args.namespace} {args.tool_group} {args.tool_name} '
                f"'{args.tool_args}' --log-level debug"
            )
        )
        invoke_ok = bool(invoke.get("ok"))
        invoke_payload = invoke
        add_check("executor-readonly-call", invoke, invoke_ok)

    checks = report["checks"]
    discovery_ready = all(
        item["ok"]
        for item in checks
        if item["name"] in (
            "ensure-validation-source",
            "crazy-provider-mode",
            "executor-tools-sources-cli",
            "executor-source-help",
            "executor-tool-help",
            "executor-tools-describe",
        )
    )
    invocation_ready = None
    invocation_checked = False
    if invoke_payload is not None:
        invocation_checked = True
        invocation_ready = next(
            item["ok"] for item in checks if item["name"] == "executor-readonly-call"
        )

    report["summary"] = {
        "discoveryReady": discovery_ready,
        "invocationChecked": invocation_checked,
        "invocationReady": invocation_ready,
        "phaseBReady": discovery_ready and (invocation_ready is True),
    }
    report["ok"] = bool(report["summary"]["phaseBReady"])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
