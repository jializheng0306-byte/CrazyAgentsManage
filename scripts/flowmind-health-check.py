#!/usr/bin/env python3
"""Repo-tracked FlowMind health probe wrapper for ALI-HERMES."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import time
from pathlib import Path
from typing import Optional


DEFAULT_SSH_KEY = "/root/.ssh/id_ed25519_hermes_flowmind"
DEFAULT_SSH_HOST = "ubuntu@111.229.194.203"
DEFAULT_LOG_FILE = "/var/log/flowmind/ops-health.log"
DEFAULT_JSON_FILE = "/home/ubuntu/FlowMindDeploy-newhost/scripts/pilot/output/current/reports/ops-runtime-health.json"
DEFAULT_LATEST_RUN_FILE = "/home/ubuntu/FlowMindDeploy-newhost/scripts/pilot/output/current/latest-run.json"
DEFAULT_RUNS_ROOT = "/home/ubuntu/FlowMindDeploy-newhost/scripts/pilot/output/runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssh-key", default=DEFAULT_SSH_KEY)
    parser.add_argument("--ssh-host", default=DEFAULT_SSH_HOST)
    parser.add_argument("--log-file", default=DEFAULT_LOG_FILE)
    parser.add_argument("--json-file", default=DEFAULT_JSON_FILE)
    parser.add_argument("--latest-run-file", default=DEFAULT_LATEST_RUN_FILE)
    parser.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--ssh-timeout", type=int, default=30)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of STATUS lines")
    return parser.parse_args()


def ssh_cmd(
    *,
    ssh_key: str,
    ssh_host: str,
    command: str,
    timeout: int = 30,
) -> tuple[str, int, str]:
    result = subprocess.run(
        [
            "ssh",
            "-i",
            ssh_key,
            "-o",
            "ConnectTimeout=10",
            "-o",
            "StrictHostKeyChecking=no",
            ssh_host,
            command,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip(), result.returncode, result.stderr.strip()


def load_remote_json(
    *,
    ssh_key: str,
    ssh_host: str,
    path: str,
    timeout: int = 30,
    attempts: int = 4,
    delay_seconds: float = 0.5,
) -> tuple[Optional[dict], Optional[str]]:
    last_error: Optional[str] = None
    quoted = shlex.quote(path)
    for attempt in range(attempts):
        output, rc, stderr = ssh_cmd(
            ssh_key=ssh_key,
            ssh_host=ssh_host,
            command=f"cat {quoted}",
            timeout=timeout,
        )
        if rc == 0 and output.strip():
            try:
                return json.loads(output), None
            except json.JSONDecodeError as exc:
                last_error = f"JSON decode failed for {path}: {exc}"
        else:
            last_error = stderr or output or f"cat {path} failed with rc={rc}"
        if attempt + 1 < attempts:
            time.sleep(delay_seconds)
    return None, last_error


def parse_latest_json_block(text: str) -> Optional[dict]:
    if not text.strip():
        return None

    lines = text.splitlines()
    blocks = []
    current = []
    for line in lines:
        if line.startswith("=== ") and line.endswith(" ==="):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current).strip())

    for block in reversed(blocks):
        if not block:
            continue
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue

    json_text = ""
    brace_count = 0
    for line in reversed(lines):
        json_text = line + "\n" + json_text
        brace_count += line.count("{") - line.count("}")
        if brace_count == 0 and "{" in json_text:
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                return None
    return None


def resolve_latest_run_report_path(
    *,
    ssh_key: str,
    ssh_host: str,
    latest_run_file: str,
    runs_root: str,
    timeout: int,
) -> tuple[Optional[str], Optional[str]]:
    latest_run, error = load_remote_json(
        ssh_key=ssh_key,
        ssh_host=ssh_host,
        path=latest_run_file,
        timeout=timeout,
        attempts=3,
        delay_seconds=0.3,
    )
    if latest_run is None:
        return None, error
    run_id = latest_run.get("runId")
    if not run_id:
        return None, "latest-run.json is missing runId"
    return f"{runs_root}/{run_id}/reports/ops-runtime-health.json", None


def load_report(
    *,
    ssh_key: str,
    ssh_host: str,
    json_file: str,
    latest_run_file: str,
    runs_root: str,
    log_file: str,
    timeout: int,
) -> tuple[Optional[dict], list[str]]:
    errors: list[str] = []

    report, error = load_remote_json(
        ssh_key=ssh_key,
        ssh_host=ssh_host,
        path=json_file,
        timeout=timeout,
        attempts=5,
        delay_seconds=0.5,
    )
    if report is not None:
        return report, []
    if error:
        errors.append(error)

    latest_run_report, latest_error = resolve_latest_run_report_path(
        ssh_key=ssh_key,
        ssh_host=ssh_host,
        latest_run_file=latest_run_file,
        runs_root=runs_root,
        timeout=timeout,
    )
    if latest_run_report:
        report, error = load_remote_json(
            ssh_key=ssh_key,
            ssh_host=ssh_host,
            path=latest_run_report,
            timeout=timeout,
            attempts=4,
            delay_seconds=0.3,
        )
        if report is not None:
            return report, []
        if error:
            errors.append(error)
    elif latest_error:
        errors.append(latest_error)

    output, rc, stderr = ssh_cmd(
        ssh_key=ssh_key,
        ssh_host=ssh_host,
        command=f"tail -n 400 {shlex.quote(log_file)}",
        timeout=timeout,
    )
    if rc == 0:
        report = parse_latest_json_block(output)
        if report is not None:
            return report, []
        errors.append("failed to parse latest JSON block from ops-health.log")
    else:
        errors.append(stderr or output or f"tail {log_file} failed with rc={rc}")

    return None, errors


def build_status_payload(report: dict) -> dict:
    passed = bool(report.get("passed", False))
    checked_at = str(report.get("checkedAt", "unknown"))
    run_id = str(report.get("runId", "unknown"))

    checks = list(report.get("checks", []) or [])
    failed_checks = [item for item in checks if not item.get("ok", False)]

    review_queue = dict(report.get("reviewQueue", {}) or {})
    queue_ok = bool(review_queue.get("ok", False))
    pending_count = int(review_queue.get("pendingCount", 0) or 0)
    pending_operational_count = int(review_queue.get("pendingOperationalCount", pending_count) or 0)
    pending_validation_count = int(review_queue.get("pendingValidationCount", 0) or 0)

    status = "OK"
    if not (passed and not failed_checks and queue_ok and pending_operational_count == 0):
        status = "ABNORMAL"

    return {
        "status": status,
        "checkedAt": checked_at,
        "runId": run_id,
        "passed": passed,
        "failedChecks": failed_checks,
        "checks": checks,
        "reviewQueue": {
            "ok": queue_ok,
            "pendingCount": pending_count,
            "pendingOperationalCount": pending_operational_count,
            "pendingValidationCount": pending_validation_count,
            "groups": review_queue.get("groups", []) or [],
        },
    }


def render_status_lines(payload: dict) -> list[str]:
    status = payload["status"]
    if status == "OK":
        lines = [
            "STATUS: OK",
            f"检查时间: {payload['checkedAt']}",
            f"所有检查项通过，待处理队列: {payload['reviewQueue']['pendingCount']}",
        ]
        if payload["reviewQueue"]["pendingValidationCount"] > 0:
            lines.append(f"Validation backlog: {payload['reviewQueue']['pendingValidationCount']} (warning only)")
        return lines

    lines = [
        "STATUS: ABNORMAL",
        f"检查时间: {payload['checkedAt']}",
        f"运行ID: {payload['runId']}",
        f"总体通过: {payload['passed']}",
    ]

    failed_checks = payload["failedChecks"]
    if failed_checks:
        lines.append("")
        lines.append(f"失败的检查项 ({len(failed_checks)}):")
        for item in failed_checks:
            lines.append(
                f"  - {item.get('url', 'unknown')}: status={item.get('status', 'N/A')}, ok={item.get('ok')}"
            )

    queue = payload["reviewQueue"]
    if (not queue["ok"]) or queue["pendingOperationalCount"] > 0 or queue["pendingValidationCount"] > 0:
        lines.append("")
        lines.append(
            "Review Queue: "
            f"ok={queue['ok']}, pending={queue['pendingCount']}, "
            f"pending_operational={queue['pendingOperationalCount']}, "
            f"pending_validation={queue['pendingValidationCount']}"
        )

    lines.append("")
    lines.append("所有检查项:")
    for item in payload["checks"]:
        marker = "✅" if item.get("ok") else "❌"
        lines.append(f"  {marker} {item.get('url', 'unknown')} ({item.get('elapsedMs', '?')}ms)")

    for group in queue.get("groups", []):
        lines.append("")
        lines.append(
            f"  Review Queue [{group.get('sourceAgent')}]: pending={group.get('pendingCount')}, "
            f"operational={group.get('pendingOperationalCount', group.get('pendingCount'))}, "
            f"validation={group.get('pendingValidationCount', 0)}"
        )

    return lines


def main() -> int:
    args = parse_args()
    try:
        report, errors = load_report(
            ssh_key=args.ssh_key,
            ssh_host=args.ssh_host,
            json_file=args.json_file,
            latest_run_file=args.latest_run_file,
            runs_root=args.runs_root,
            log_file=args.log_file,
            timeout=args.ssh_timeout,
        )
    except subprocess.TimeoutExpired:
        payload = {"status": "ERROR", "message": "SSH连接超时"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else "STATUS: ERROR\nSSH连接超时")
        return 1
    except Exception as exc:
        payload = {"status": "ERROR", "message": f"巡检脚本异常: {exc}"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"STATUS: ERROR\n巡检脚本异常: {exc}")
        return 1

    if report is None:
        payload = {
            "status": "ERROR",
            "message": "无法解析当前巡检报告JSON",
            "errors": errors,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("STATUS: ERROR")
            print("无法解析当前巡检报告JSON")
            if errors:
                print("细节:")
                for item in errors:
                    print(f"- {item}")
        return 1

    payload = build_status_payload(report)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("\n".join(render_status_lines(payload)))
    return 0 if payload["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
