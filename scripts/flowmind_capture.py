#!/usr/bin/env python3
"""
FlowMind Capture 同步脚本 — 将 Bitable 中的价值点同步到 FlowMind

功能：
1. 读取 Bitable 中状态为"已确认"且 FlowMind同步="未同步"的记录
2. 通过 FlowMind Candidate Ingress API 发送候选数据
3. 更新 Bitable 记录的 FlowMind同步状态

用法：
  python flowmind_capture.py                    # 同步所有已确认未同步的记录
  python flowmind_capture.py <record_id>        # 同步指定记录
  python flowmind_capture.py --dry-run          # 仅打印即将发送的 payload
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRAZY_ROOT = Path(os.environ.get("CRAZY_ROOT", os.path.expanduser("~/CrazyAgentsManage")))
BITABLE_CONFIG = CRAZY_ROOT / "shared-context" / "bitable-config.json"
LINK_STATE_FILE = CRAZY_ROOT / "shared-context" / "flowmind-link-state.json"

DEFAULT_FLOWMIND_BASE_URL = os.environ.get("FLOWMIND_BASE_URL", "http://111.229.194.203:3301")
DEFAULT_FLOWMIND_API_KEY = os.environ.get("FLOWMIND_API_KEY", "flowmind-dev-token")
DEFAULT_FLOWMIND_INSTANCE_ID = os.environ.get("FLOWMIND_INSTANCE_ID", "crazyagentsmanage-intel-sentinel")
DEFAULT_FLOWMIND_SOURCE_AGENT = os.environ.get("FLOWMIND_SOURCE_AGENT", "hermes")
DEFAULT_FLOWMIND_SERVER_ID = os.environ.get("FLOWMIND_SERVER_ID", "ali-hermes")
DEFAULT_FLOWMIND_PLUGIN_VERSION = os.environ.get("FLOWMIND_PLUGIN_VERSION", "crazyagentsmanage-link-v1")
DEFAULT_FLOWMIND_ROUTE_ID = os.environ.get("FLOWMIND_ROUTE_ID", "crazyagentsmanage-bitable-capture")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync confirmed Bitable value items into FlowMind candidates")
    parser.add_argument("record_id", nargs="?", help="只同步指定的 Bitable record_id")
    parser.add_argument("--dry-run", action="store_true", help="打印将发送的 payload，不真正调用 FlowMind")
    parser.add_argument("--register-instance", action="store_true", help="在发送前向 FlowMind 注册/刷新 instance 并保存返回的 apiKey")
    parser.add_argument("--base-url", default=DEFAULT_FLOWMIND_BASE_URL, help="FlowMind base URL")
    parser.add_argument("--api-key", default=DEFAULT_FLOWMIND_API_KEY, help="FlowMind bearer token")
    parser.add_argument("--instance-id", default=DEFAULT_FLOWMIND_INSTANCE_ID, help="FlowMind integration instanceId")
    parser.add_argument("--source-agent", default=DEFAULT_FLOWMIND_SOURCE_AGENT, help="FlowMind sourceAgent")
    parser.add_argument("--server-id", default=DEFAULT_FLOWMIND_SERVER_ID, help="FlowMind integration serverId")
    parser.add_argument("--plugin-version", default=DEFAULT_FLOWMIND_PLUGIN_VERSION, help="FlowMind integration pluginVersion")
    parser.add_argument("--route-id", default=DEFAULT_FLOWMIND_ROUTE_ID, help="sourceContext.route_id")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_cmd(args: list[str], timeout: int = 30) -> tuple[str, int, str]:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode, result.stderr.strip()


def run_lark_json(args: list[str], timeout: int = 30) -> dict[str, Any]:
    output, code, stderr = run_cmd(args, timeout=timeout)
    if code != 0:
        detail = stderr or output or f"exit={code}"
        raise RuntimeError(detail)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from lark-cli: {exc}") from exc


def flowmind_json_request(
    *,
    base_url: str,
    api_key: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    instance_token: str | None = None,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    if instance_token:
        headers["x-instance-token"] = instance_token

    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> {exc.code} {raw}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {path} -> transport error: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{method} {path} -> invalid JSON response: {raw[:300]}") from exc


def load_bitable_config() -> dict[str, Any]:
    if not BITABLE_CONFIG.exists():
        raise FileNotFoundError("bitable-config.json 不存在")
    return json.loads(BITABLE_CONFIG.read_text(encoding="utf-8"))


def load_link_state() -> dict[str, Any]:
    if not LINK_STATE_FILE.exists():
        return {}
    try:
        return json.loads(LINK_STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_link_state(data: dict[str, Any]) -> None:
    LINK_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LINK_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_priority(value: Any) -> str:
    priority = str(value or "P2").strip().upper()
    return priority if priority in {"P0", "P1", "P2"} else "P2"


def priority_confidence(priority: str) -> int:
    return {"P0": 85, "P1": 70, "P2": 55}[priority]


def build_candidate_payload(record: dict[str, Any], runtime: dict[str, str]) -> dict[str, Any]:
    priority = normalize_priority(record.get("priority"))
    raw_text = json.dumps(
        {
            "name": record.get("name", ""),
            "priority": priority,
            "impact": record.get("impact", ""),
            "action": record.get("action", ""),
            "source": record.get("source", ""),
            "url": record.get("url", ""),
            "notes": record.get("notes", ""),
            "bitable_record_id": record.get("record_id", ""),
            "origin_system": "CrazyAgentsManage",
            "discovered_via": "tech-radar",
        },
        ensure_ascii=False,
    )

    description_lines = [
        f"优先级: {priority}",
        f"影响评估: {record.get('impact', '')}",
        f"建议行动: {record.get('action', '')}",
    ]

    return {
        "instanceId": runtime["instance_id"],
        "sourceAgent": runtime["source_agent"],
        "title": record.get("name", ""),
        "description": "\n".join(description_lines),
        "rawText": raw_text,
        "confidence": priority_confidence(priority),
        "sourceContext": {
            "route_id": runtime["route_id"],
            "sourceAgent": runtime["source_agent"],
            "source": record.get("source", ""),
            "url": record.get("url", ""),
            "priority": priority,
            "impact_assessment": record.get("impact", ""),
            "action_suggested": record.get("action", ""),
            "discovered_via": "tech-radar",
            "bitable_record_id": record.get("record_id", ""),
            "sync_mode": "manual_gate_before_capture",
            "origin_system": "CrazyAgentsManage",
        },
        "timestamp": now_iso(),
    }


def get_pending_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    app_token = config["app_token"]
    table_id = config["table_id"]
    data = run_lark_json(
        [
            "lark-cli",
            "base",
            "+record-list",
            "--base-token",
            app_token,
            "--table-id",
            table_id,
            "--limit",
            "100",
        ]
    )

    records = data.get("data", {}).get("items", [])
    pending = []
    for rec in records:
        fields = rec.get("fields", {})
        status = fields.get("状态", "")
        flowmind = fields.get("FlowMind同步", "")
        if status == "已确认" and flowmind == "未同步":
            pending.append(
                {
                    "record_id": rec["record_id"],
                    "name": fields.get("价值点名称", ""),
                    "priority": fields.get("优先级", "P2"),
                    "impact": fields.get("影响评估", ""),
                    "action": fields.get("建议行动", ""),
                    "source": fields.get("来源", ""),
                    "url": fields.get("关联任务", ""),
                    "notes": fields.get("备注", ""),
                }
            )
    return pending


def get_record_by_id(config: dict[str, Any], target_record: str) -> dict[str, Any]:
    app_token = config["app_token"]
    table_id = config["table_id"]
    data = run_lark_json(
        [
            "lark-cli",
            "api",
            "GET",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{target_record}",
        ]
    )
    fields = data.get("data", {}).get("record", {}).get("fields", {})
    return {
        "record_id": target_record,
        "name": fields.get("价值点名称", ""),
        "priority": fields.get("优先级", "P2"),
        "impact": fields.get("影响评估", ""),
        "action": fields.get("建议行动", ""),
        "source": fields.get("来源", ""),
        "url": fields.get("关联任务", ""),
        "notes": fields.get("备注", ""),
    }


def register_instance(runtime: dict[str, str]) -> dict[str, Any]:
    response = flowmind_json_request(
        base_url=runtime["base_url"],
        api_key=runtime["api_key"],
        method="POST",
        path="/api/integrations/instances",
        body={
            "instanceId": runtime["instance_id"],
            "serverId": runtime["server_id"],
            "pluginVersion": runtime["plugin_version"],
            "sourceAgent": runtime["source_agent"],
            "metadata": {
                "originSystem": "CrazyAgentsManage",
                "routeId": runtime["route_id"],
                "registeredAt": now_iso(),
            },
        },
    )
    data = response.get("data", {})
    link_state = load_link_state()
    link_state.update(
        {
            "instanceId": data.get("instanceId", runtime["instance_id"]),
            "sourceAgent": data.get("sourceAgent", runtime["source_agent"]),
            "serverId": data.get("serverId", runtime["server_id"]),
            "apiKey": data.get("apiKey"),
            "registeredAt": data.get("registeredAt"),
            "baseUrl": runtime["base_url"],
            "routeId": runtime["route_id"],
        }
    )
    save_link_state(link_state)
    return response


def send_to_flowmind(record: dict[str, Any], runtime: dict[str, str]) -> tuple[bool, dict[str, Any]]:
    payload = build_candidate_payload(record, runtime)
    response = flowmind_json_request(
        base_url=runtime["base_url"],
        api_key=runtime["api_key"],
        method="POST",
        path="/api/integrations/candidate-ingress",
        body=payload,
    )
    success = bool(response.get("success")) and bool(response.get("data", {}).get("candidateId"))
    return success, {"request": payload, "response": response}


def update_bitable_status(config: dict[str, Any], record_id: str, status: str) -> None:
    app_token = config["app_token"]
    table_id = config["table_id"]
    payload = json.dumps({"fields": {"FlowMind同步": status}}, ensure_ascii=False)
    output, code, stderr = run_cmd(
        [
            "lark-cli",
            "api",
            "PUT",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            "--data",
            payload,
        ]
    )
    if code != 0:
        detail = stderr or output or f"exit={code}"
        print(f"⚠️ 更新 Bitable 状态失败: {detail}")


def build_runtime_config(args: argparse.Namespace) -> dict[str, str]:
    return {
        "base_url": args.base_url,
        "api_key": args.api_key,
        "instance_id": args.instance_id,
        "source_agent": args.source_agent,
        "server_id": args.server_id,
        "plugin_version": args.plugin_version,
        "route_id": args.route_id,
    }


def main() -> int:
    args = parse_args()
    runtime = build_runtime_config(args)
    try:
        config = load_bitable_config()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 1

    if args.register_instance:
        try:
            registration = register_instance(runtime)
            instance = registration.get("data", {})
            print(f"已注册 FlowMind instance: {instance.get('instanceId')} ({instance.get('sourceAgent')})")
        except Exception as exc:
            print(f"❌ 注册 FlowMind instance 失败: {exc}")
            return 1

    try:
        records = [get_record_by_id(config, args.record_id)] if args.record_id else get_pending_records(config)
    except Exception as exc:
        print(f"❌ 读取 Bitable 失败: {exc}")
        return 1

    if not records:
        print("无待同步记录")
        return 0

    print(f"同步 {len(records)} 条记录到 FlowMind...")
    failures = 0
    for record in records:
        print(f"  同步: {record['name']} ({normalize_priority(record['priority'])})")

        if args.dry_run:
            print(json.dumps(build_candidate_payload(record, runtime), ensure_ascii=False, indent=2))
            continue

        try:
            success, result = send_to_flowmind(record, runtime)
        except Exception as exc:
            failures += 1
            update_bitable_status(config, record["record_id"], "同步失败")
            print(f"    ❌ 同步失败: {exc}")
            continue

        if success:
            update_bitable_status(config, record["record_id"], "已同步")
            response_data = result["response"].get("data", {})
            print(f"    ✅ 同步成功: candidateId={response_data.get('candidateId')}")
        else:
            failures += 1
            update_bitable_status(config, record["record_id"], "同步失败")
            print(f"    ❌ 同步失败: {json.dumps(result['response'], ensure_ascii=False)}")

    print("\n同步完成")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
