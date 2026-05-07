#!/usr/bin/env python3
"""
Bitable 同步脚本 — 将 Tech Radar 条目同步到飞书多维表格 + @通知用户

功能：
1. 读取 shared-context/tech-radar.json
2. 读取 shared-context/bitable-config.json 获取表格配置
3. 检查哪些条目尚未同步到 Bitable
4. 写入新条目到 Bitable
5. 发送 @通知到飞书群
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CRAZY_ROOT = Path(os.environ.get("CRAZY_ROOT", os.path.expanduser("~/CrazyAgentsManage")))
RADAR_FILE = CRAZY_ROOT / "shared-context" / "tech-radar.json"
BITABLE_CONFIG = CRAZY_ROOT / "shared-context" / "bitable-config.json"
SYNC_STATE_FILE = CRAZY_ROOT / "shared-context" / "bitable-sync-state.json"


def run_cmd(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode


def load_config():
    if not BITABLE_CONFIG.exists():
        print("❌ bitable-config.json 不存在，请先创建多维表格")
        sys.exit(1)
    return json.loads(BITABLE_CONFIG.read_text())


def load_sync_state():
    if SYNC_STATE_FILE.exists():
        return json.loads(SYNC_STATE_FILE.read_text())
    return {"synced_ids": [], "record_map": {}}


def save_sync_state(state):
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_tech_radar():
    if not RADAR_FILE.exists():
        return []
    radar = json.loads(RADAR_FILE.read_text())
    return radar.get("entries", [])


def create_record(config, entry):
    """在 Bitable 中创建一条记录"""
    app_token = config["app_token"]
    table_id = config["table_id"]

    # 转换日期为 Unix 毫秒时间戳
    discovered = entry.get("discovered_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt = datetime.strptime(discovered, "%Y-%m-%d")
        date_ms = int(dt.timestamp() * 1000)
    except Exception:
        date_ms = int(datetime.now().timestamp() * 1000)

    fields = {
        "价值点名称": entry.get("name", ""),
        "来源": entry.get("source", "其他"),
        "优先级": entry.get("priority", "P2"),
        "影响评估": entry.get("impact_assessment", ""),
        "建议行动": entry.get("action_suggested", ""),
        "状态": entry.get("status", "pending"),
        "发现日期": date_ms,
        "关联任务": entry.get("url", ""),
        "FlowMind同步": "未同步",
        "备注": entry.get("notes", ""),
    }

    payload = json.dumps({"fields": fields}, ensure_ascii=False)
    cmd = (
        f"lark-cli api POST "
        f"'/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records' "
        f"--data '{payload}'"
    )
    output, code = run_cmd(cmd)
    if code == 0:
        result = json.loads(output)
        record_id = result.get("data", {}).get("record", {}).get("record_id", "")
        return record_id
    else:
        print(f"  ❌ 创建记录失败: {output[:200]}")
        return None


def notify_feishu(config, new_entries):
    """在飞书群发送 @通知"""
    if not new_entries:
        return

    chat_id = config["chat_id"]
    user_id = config["user_open_id"]

    entry_list = ""
    for e in new_entries:
        entry_list += f"  • {e['name']} ({e['priority']}) — {e.get('action_suggested', '')}\n"

    post_content = {
        "zh_cn": {
            "title": f"📊 情报价值追踪 — {datetime.now().strftime('%Y-%m-%d')}",
            "content": [
                [
                    {"tag": "at", "user_id": user_id},
                    {"tag": "text", "text": f" 有 {len(new_entries)} 个新价值点需要关注："}
                ],
                [{"tag": "text", "text": ""}],
                [{"tag": "text", "text": entry_list}],
                [{"tag": "text", "text": ""}],
                [
                    {"tag": "text", "text": "📎 表格地址："},
                    {"tag": "a", "text": "情报价值追踪", "href": config["url"]}
                ],
            ]
        }
    }

    content_json = json.dumps(post_content, ensure_ascii=False)
    escaped = content_json.replace("'", "'\\''")
    cmd = f"lark-cli im +messages-send --chat-id {chat_id} --msg-type post --content '{escaped}'"
    run_cmd(cmd)
    print(f"  ✅ 已发送 @通知到飞书群")


def main():
    config = load_config()
    state = load_sync_state()
    entries = load_tech_radar()

    if not entries:
        print("Tech Radar 无条目")
        return

    # 找出尚未同步的条目
    new_entries = [e for e in entries if e.get("name") not in state["synced_ids"]]

    if not new_entries:
        print("无新条目需要同步")
        return

    print(f"发现 {len(new_entries)} 个新条目，同步到 Bitable...")

    synced_names = []
    record_map = state.get("record_map", {})
    for entry in new_entries:
        record_id = create_record(config, entry)
        if record_id:
            print(f"  ✅ {entry['name']} → {record_id}")
            synced_names.append(entry["name"])
            record_map[entry["name"]] = record_id
        else:
            print(f"  ❌ {entry['name']} 同步失败")

    # 更新同步状态
    state["synced_ids"].extend(synced_names)
    state["record_map"] = record_map
    state["last_sync"] = datetime.now().isoformat()
    save_sync_state(state)

    # 发送 @通知
    notify_feishu(config, new_entries)

    print(f"\n同步完成: {len(synced_names)}/{len(new_entries)} 条")


if __name__ == "__main__":
    main()
