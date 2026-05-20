#!/usr/bin/env python3
"""Deterministic FlowMind health notification helper."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_SNAPSHOT_PATH = Path.home() / ".hermes" / "cron" / "state" / "flowmind-health-check-latest.json"
DEFAULT_CHAT_ID = "oc_27ce44a971bd3e171a5f36962a1dad3c"
DEFAULT_AT_USER_ID = "ou_da440c467fc95b66f090695a9972495a"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT_PATH))
    parser.add_argument("--chat-id", default=DEFAULT_CHAT_ID)
    parser.add_argument("--at-user-id", default=DEFAULT_AT_USER_ID)
    parser.add_argument("--title", default="⚠️ FlowMind巡检异常")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Allow notify even when status is not ABNORMAL/ERROR")
    return parser.parse_args()


def load_snapshot(path: str) -> dict[str, Any]:
    snapshot_path = Path(path).expanduser()
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def summarize_snapshot(snapshot: dict[str, Any]) -> str:
    status = snapshot.get("status", "UNKNOWN")
    if status == "OK":
        return "当前状态为 OK，无需发送异常通知。"

    lines = [
        f"状态: {status}",
        f"检查时间: {snapshot.get('checkedAt', 'unknown')}",
        f"运行ID: {snapshot.get('runId', 'unknown')}",
    ]

    failed_checks = snapshot.get("failedChecks") or []
    if failed_checks:
        lines.append("失败检查项:")
        for item in failed_checks:
            lines.append(
                f"- {item.get('url', 'unknown')}: status={item.get('status', 'N/A')}, ok={item.get('ok')}"
            )

    queue = snapshot.get("reviewQueue") or {}
    if queue:
        lines.append(
            "Review Queue: "
            f"ok={queue.get('ok')}, pending={queue.get('pendingCount')}, "
            f"pending_operational={queue.get('pendingOperationalCount')}, "
            f"pending_validation={queue.get('pendingValidationCount')}"
        )

    executor_probe = snapshot.get("executorProbe") or {}
    if executor_probe:
        lines.append(
            f"Executor probe: {executor_probe.get('source')} status={executor_probe.get('status')}"
        )

    if snapshot.get("message"):
        lines.append(f"Message: {snapshot['message']}")
    return "\n".join(lines)


def build_post_payload(snapshot: dict[str, Any], *, chat_id: str, at_user_id: str, title: str) -> dict[str, Any]:
    summary = summarize_snapshot(snapshot)
    return {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(
            {
                "zh_cn": {
                    "title": title,
                    "content": [[
                        {"tag": "at", "user_id": at_user_id},
                        {"tag": "text", "text": f" FlowMind 巡检发现异常，请检查：\n\n{summary}"},
                    ]]
                }
            },
            ensure_ascii=False,
        ),
    }


def send_post(payload: dict[str, Any]) -> tuple[int, str, str]:
    result = subprocess.run(
        [
            "lark-cli",
            "api",
            "POST",
            "/open-apis/im/v1/messages",
            "--params",
            json.dumps({"receive_id_type": "chat_id"}, ensure_ascii=False),
            "--data",
            json.dumps(payload, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main() -> int:
    args = parse_args()
    snapshot = load_snapshot(args.snapshot)
    status = str(snapshot.get("status") or "UNKNOWN").upper()
    if status == "OK" and not args.force:
        print(json.dumps({"skipped": True, "reason": "status is OK"}, ensure_ascii=False, indent=2))
        return 0
    if status not in {"ABNORMAL", "ERROR"} and not args.force:
        print(json.dumps({"skipped": True, "reason": f"status is {status}"}, ensure_ascii=False, indent=2))
        return 0

    payload = build_post_payload(snapshot, chat_id=args.chat_id, at_user_id=args.at_user_id, title=args.title)
    if args.dry_run:
        print(json.dumps({"dryRun": True, "payload": payload, "summary": summarize_snapshot(snapshot)}, ensure_ascii=False, indent=2))
        return 0

    code, stdout, stderr = send_post(payload)
    print(json.dumps({"ok": code == 0, "code": code, "stdout": stdout, "stderr": stderr}, ensure_ascii=False, indent=2))
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
