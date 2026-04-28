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
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CRAZY_ROOT = Path(os.environ.get("CRAZY_ROOT", os.path.expanduser("~/CrazyAgentsManage")))
BITABLE_CONFIG = CRAZY_ROOT / "shared-context" / "bitable-config.json"

FLOWMIND_API = "https://flowmind.app"
FLOWMIND_TOKEN = os.environ.get("FLOWMIND_API_KEY", "flowmind-dev-token")


def run_cmd(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode


def load_config():
    if not BITABLE_CONFIG.exists():
        print("❌ bitable-config.json 不存在")
        sys.exit(1)
    return json.loads(BITABLE_CONFIG.read_text())


def get_pending_records(config):
    """获取 Bitable 中待同步的记录"""
    app_token = config["app_token"]
    table_id = config["table_id"]

    cmd = f"lark-cli base +record-list --base-token '{app_token}' --table-id '{table_id}' --page-size 100"
    output, code = run_cmd(cmd)
    if code != 0:
        print(f"❌ 读取 Bitable 失败: {output[:200]}")
        return []

    data = json.loads(output)
    records = data.get("data", {}).get("items", [])

    pending = []
    for rec in records:
        fields = rec.get("fields", {})
        status = fields.get("状态", "")
        flowmind = fields.get("FlowMind同步", "")
        if status == "已确认" and flowmind == "未同步":
            pending.append({
                "record_id": rec["record_id"],
                "name": fields.get("价值点名称", ""),
                "priority": fields.get("优先级", "P2"),
                "impact": fields.get("影响评估", ""),
                "action": fields.get("建议行动", ""),
                "source": fields.get("来源", ""),
                "url": fields.get("关联任务", ""),
                "notes": fields.get("备注", ""),
            })

    return pending


def send_to_flowmind(record):
    """通过 Candidate Ingress API 发送到 FlowMind"""
    candidate = {
        "source": "hermes-intel-sentinel",
        "sourceAgent": "intel-sentinel",
        "type": "tech-discovery",
        "title": record["name"],
        "description": f"优先级: {record['priority']}\n影响评估: {record['impact']}\n建议行动: {record['action']}",
        "sourceContext": {
            "source": record["source"],
            "url": record["url"],
            "priority": record["priority"],
            "impact_assessment": record["impact"],
            "action_suggested": record["action"],
            "discovered_via": "tech-radar",
            "bitable_record_id": record["record_id"],
        },
        "confidence": 0.8 if record["priority"] == "P0" else 0.6 if record["priority"] == "P1" else 0.4,
    }

    payload = json.dumps(candidate, ensure_ascii=False)
    cmd = (
        f"curl -s -X POST '{FLOWMIND_API}/api/integrations/candidate-ingress' "
        f"-H 'Authorization: Bearer {FLOWMIND_TOKEN}' "
        f"-H 'Content-Type: application/json' "
        f"-d '{payload}'"
    )
    output, code = run_cmd(cmd, timeout=15)
    if code == 0:
        try:
            result = json.loads(output)
            if result.get("success"):
                return True, result
            else:
                return False, result
        except Exception:
            return False, {"error": output[:200]}
    return False, {"error": output[:200]}


def update_bitable_status(config, record_id, status):
    """更新 Bitable 记录的 FlowMind 同步状态"""
    app_token = config["app_token"]
    table_id = config["table_id"]

    payload = json.dumps({"fields": {"FlowMind同步": status}}, ensure_ascii=False)
    cmd = (
        f"lark-cli api PUT "
        f"'/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}' "
        f"--data '{payload}'"
    )
    run_cmd(cmd)


def main():
    config = load_config()

    # 如果指定了 record_id，只同步该记录
    target_record = sys.argv[1] if len(sys.argv) > 1 else None

    if target_record:
        # 从 Bitable 读取该记录
        app_token = config["app_token"]
        table_id = config["table_id"]
        cmd = f"lark-cli api GET '/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{target_record}'"
        output, code = run_cmd(cmd)
        if code != 0:
            print(f"❌ 读取记录失败: {output[:200]}")
            return
        data = json.loads(output)
        fields = data.get("data", {}).get("record", {}).get("fields", {})
        record = {
            "record_id": target_record,
            "name": fields.get("价值点名称", ""),
            "priority": fields.get("优先级", "P2"),
            "impact": fields.get("影响评估", ""),
            "action": fields.get("建议行动", ""),
            "source": fields.get("来源", ""),
            "url": fields.get("关联任务", ""),
        }
        records = [record]
    else:
        records = get_pending_records(config)

    if not records:
        print("无待同步记录")
        return

    print(f"同步 {len(records)} 条记录到 FlowMind...")

    for record in records:
        print(f"  同步: {record['name']} ({record['priority']})")
        success, result = send_to_flowmind(record)

        if success:
            update_bitable_status(config, record["record_id"], "已同步")
            print(f"    ✅ 同步成功")
        else:
            update_bitable_status(config, record["record_id"], "同步失败")
            print(f"    ❌ 同步失败: {result}")

    print(f"\n同步完成")


if __name__ == "__main__":
    main()
