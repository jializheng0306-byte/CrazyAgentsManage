#!/usr/bin/env python3
"""
承诺审查脚本 v2 — Bitable 版本
每日 09:00 执行
功能：扫描活跃承诺、写入飞书多维表格、发送群通知摘要
"""

import json
import os
import shlex
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
PROMISE_ACTIVE_DIR = os.path.expanduser("~/.hermes/promises/active")
PROMISE_ROOT_DIR = os.path.expanduser("~/.hermes/promises")
REPORT_DIR = os.path.expanduser("~/.hermes/promises/reviews")

# Bitable 配置
BITABLE_APP_TOKEN = "EpeXbhpF9a0s0wsh6axce9PknFg"
BITABLE_TABLE_ID = "tblJRMmjbyKEDZY1"
BITABLE_TRACE_TABLE_ID = "tbltwMndeV5O2YkR"
BITABLE_URL = f"https://bcn7uazoofu0.feishu.cn/base/{BITABLE_APP_TOKEN}"

# FlowMind 配置
FLOWMIND_TRACE_API = "http://111.229.194.203:3301/api/bridge/trace"
FLOWMIND_AUTH = "Bearer flowmind-dev-token"

# 飞书配置
CHAT_ID = "oc_bbde428675a7c267d55c3f0663ca701d"  # CrazyAgentsManage群
DRY_RUN = os.environ.get("HERMES_CRON_DRY_RUN", "0") == "1"

# 状态映射：JSON status → Bitable option name
STATUS_MAP = {
    "pending": "待处理",
    "in_progress": "进行中",
    "completed": "已完成",
    "done": "已完成",
    "overdue": "已过期",
    "rejected": "已拒绝",
    "blocked": "进行中",
}

# 优先级映射
PRIORITY_MAP = {
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
}


def run_cmd(cmd, timeout=30):
    """执行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def scan_promises():
    """扫描所有承诺文件（active 目录 + 根目录兼容）"""
    promises = []

    # 扫描 active 目录（新格式）
    active_dir = Path(PROMISE_ACTIVE_DIR)
    if active_dir.exists():
        for json_file in active_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data["_source_file"] = json_file.name
                        data["_source_dir"] = "active"
                        promises.append(data)
            except Exception:
                continue

    # 扫描根目录（旧格式兼容）
    root_dir = Path(PROMISE_ROOT_DIR)
    if root_dir.exists():
        for json_file in root_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data["_source_file"] = json_file.name
                        data["_source_dir"] = "root"
                        promises.append(data)
                    elif isinstance(data, list):
                        for p in data:
                            p["_source_file"] = json_file.name
                            p["_source_dir"] = "root"
                        promises.extend(data)
            except Exception:
                continue

    return promises


def classify_promises(promises):
    """分类承诺状态"""
    today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    result = {
        "total": len(promises),
        "overdue": [],
        "due_today": [],
        "due_soon": [],
        "in_progress": [],
        "completed": [],
        "blocked": [],
        "pending_count": 0,
    }

    for p in promises:
        status = p.get("status", "pending").lower()
        due = p.get("due_date", p.get("deadline", ""))

        if status in ("done", "completed", "已完成"):
            result["completed"].append(p)
        elif status in ("blocked", "阻塞"):
            result["blocked"].append(p)
        elif due:
            if due < today:
                result["overdue"].append(p)
            elif due == today:
                result["due_today"].append(p)
            elif due <= next_week:
                result["due_soon"].append(p)
            else:
                result["in_progress"].append(p)
        else:
            if status in ("in_progress", "进行中"):
                result["in_progress"].append(p)
            else:
                result["pending_count"] += 1

    return result


def datetime_to_ms(dt_str):
    """将 ISO datetime 字符串转为 Unix 毫秒时间戳"""
    if not dt_str:
        return None
    try:
        # 处理多种格式
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]:
            try:
                dt = datetime.strptime(dt_str[:26], fmt)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
        # 尝试解析带时区的
        dt_str_clean = dt_str.split("+")[0].split("Z")[0]
        dt = datetime.fromisoformat(dt_str_clean)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def date_to_ms(date_str):
    """将日期字符串转为 Unix 毫秒时间戳"""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def sync_to_bitable(promises):
    """将承诺同步到 Bitable"""
    if DRY_RUN:
        print("  DRY RUN: 跳过 Bitable 同步")
        return 0

    # 先获取现有记录（按 promise_id 去重）
    existing_records = {}
    cmd = f'lark-cli api GET "/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records" --params \'{{"page_size":500}}\' '
    output, code = run_cmd(cmd, timeout=30)
    if code == 0:
        try:
            data = json.loads(output)
            for item in data.get("data", {}).get("items", []):
                pid_field = item.get("fields", {}).get("promise_id")
                if pid_field:
                    existing_records[pid_field[0]["text"] if isinstance(pid_field, list) else pid_field] = item.get("record_id")
        except Exception:
            pass

    sync_count = 0
    for promise in promises:
        pid = promise.get("id", "")
        status_raw = promise.get("status", "pending").lower()
        priority_raw = promise.get("priority", "P3")

        # 映射状态和优先级
        status = STATUS_MAP.get(status_raw, "待处理")
        priority = PRIORITY_MAP.get(priority_raw, "P3")

        # 构建字段
        fields = {
            "promise_id": pid,
            "title": promise.get("title", "")[:200],
            "description": promise.get("description", "")[:500],
            "source": promise.get("source", ""),
            "status": status,
            "priority": priority,
        }

        # 时间字段（毫秒时间戳）
        created_at = datetime_to_ms(promise.get("created_at", ""))
        if created_at:
            fields["created_at"] = created_at

        due_date = date_to_ms(promise.get("due_date", promise.get("deadline", "")))
        if due_date:
            fields["due_date"] = due_date

        completed_at = datetime_to_ms(promise.get("completed_at", ""))
        if completed_at:
            fields["completed_at"] = completed_at

        flowmind_id = promise.get("flowmind_candidate_id")
        if flowmind_id:
            fields["flowmind_candidate_id"] = flowmind_id

        # 更新或创建
        if pid in existing_records:
            record_id = existing_records[pid]
            update_cmd = f'''lark-cli api PUT "/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/{record_id}" \
                --data '{json.dumps({"fields": fields}, ensure_ascii=False)}' '''
            _, code = run_cmd(update_cmd, timeout=15)
            if code == 0:
                sync_count += 1
                print(f"  🔄 更新: {promise.get('title', '')[:50]}...")
        else:
            create_cmd = f'''lark-cli api POST "/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records" \
                --data '{json.dumps({"fields": fields}, ensure_ascii=False)}' '''
            _, code = run_cmd(create_cmd, timeout=15)
            if code == 0:
                sync_count += 1
                print(f"  ✅ 新增: {promise.get('title', '')[:50]}...")

    return sync_count


def fetch_trace(candidate_id):
    """从 FlowMind 获取 trace 数据"""
    import urllib.request
    url = f"{FLOWMIND_TRACE_API}/{candidate_id}"
    req = urllib.request.Request(url, headers={"Authorization": FLOWMIND_AUTH})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️ trace 查询失败 ({candidate_id[:8]}...): {e}")
        return None


def sync_trace_events(promise_id, candidate_id):
    """同步 trace 事件到交互轨迹子表"""
    trace_data = fetch_trace(candidate_id)
    if not trace_data or not trace_data.get("success"):
        return 0

    events = trace_data.get("data", {}).get("events", [])
    if not events:
        return 0

    synced = 0
    for event in events:
        ts = event.get("timestamp", "")
        ts_ms = datetime_to_ms(ts)

        fields = {
            "trace_id": event.get("traceId", ""),
            "candidate_id": candidate_id,
            "promise_id": promise_id,
            "action": event.get("action", ""),
            "actor": event.get("actor", ""),
            "module": event.get("module", "unknown"),
            "from_status": event.get("fromStatus"),
            "to_status": event.get("toStatus"),
            "summary": event.get("summary", "")[:200],
        }
        if ts_ms:
            fields["timestamp"] = ts_ms

        cmd = f'''lark-cli api POST "/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TRACE_TABLE_ID}/records" \
            --data '{json.dumps({"fields": fields}, ensure_ascii=False)}' '''
        _, code = run_cmd(cmd, timeout=15)
        if code == 0:
            synced += 1
        else:
            # 可能已存在，跳过
            pass

    return synced


def update_trace_fields(record_id, candidate_id):
    """更新承诺主表的 trace 派生字段"""
    trace_data = fetch_trace(candidate_id)
    if not trace_data or not trace_data.get("success"):
        return

    events = trace_data.get("data", {}).get("events", [])
    event_count = len(events)
    last_summary = events[-1].get("summary", "") if events else ""

    update_fields = {
        "trace_event_count": event_count,
        "last_trace_summary": last_summary[:200],
    }

    update_cmd = f'''lark-cli api PUT "/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/{record_id}" \
        --data '{json.dumps({"fields": update_fields}, ensure_ascii=False)}' '''
    run_cmd(update_cmd, timeout=15)
    print(f"  📊 trace: {event_count} 事件 | {last_summary[:40]}...")


def send_to_feishu(classified, sync_count):
    """发送审查摘要到飞书群"""
    today = datetime.now().strftime("%Y-%m-%d")

    total = classified["total"]
    in_progress = len(classified["in_progress"])
    done = len(classified["completed"])
    overdue = len(classified["overdue"])
    due_today = len(classified["due_today"])
    due_soon = len(classified["due_soon"])
    blocked = len(classified["blocked"])
    pending = classified.get("pending_count", 0)

    # 构建告警部分
    alert = ""
    if overdue > 0:
        alert += f"🚨 已过期: {overdue} 项\n"
    if due_today > 0:
        alert += f"⚠️ 今日到期: {due_today} 项\n"
    if blocked > 0:
        alert += f"🚧 阻塞: {blocked} 项\n"

    message = f"""📋 承诺审查报告 ({today})
━━━━━━━━━━━━━━━━━━━

📊 统计:
- 总承诺: {total} | 进行中: {in_progress} | 已完成: {done}
- 待处理: {pending} | 7天内到期: {due_soon}
{alert}🔄 本次同步: {sync_count} 条到 Bitable

━━━━━━━━━━━━━━━━━━━
📊 查看承诺主表: {BITABLE_URL}
📊 甘特图: {BITABLE_URL}?table={BITABLE_TABLE_ID}&view=gantt"""

    if DRY_RUN:
        print("  DRY RUN: 跳过飞书群发送")
        print(message)
        return True

    cmd = f'lark-cli im +messages-send --chat-id {shlex.quote(CHAT_ID)} --text {shlex.quote(message)}'
    output, code = run_cmd(cmd)
    print(f"  群消息: {'✅' if code == 0 else '❌'}")
    return code == 0


def main():
    print("📋 开始承诺审查 v2 (Bitable)...")

    os.makedirs(REPORT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")

    # 1. 扫描承诺
    print("\n1. 扫描承诺文件...")
    promises = scan_promises()
    print(f"  找到 {len(promises)} 条承诺")

    # 2. 分类统计
    print("2. 分类统计...")
    classified = classify_promises(promises)

    # 3. 同步到 Bitable
    print("3. 同步到 Bitable...")
    sync_count = sync_to_bitable(promises)
    print(f"  同步 {sync_count} 条记录")

    # 3.5. 同步 FlowMind trace 数据
    print("3.5. 同步 FlowMind trace...")
    trace_synced = 0
    for promise in promises:
        cid = promise.get("flowmind_candidate_id")
        if cid:
            pid = promise.get("id", "")
            trace_synced += sync_trace_events(pid, cid)
    if trace_synced:
        print(f"  🔗 同步 {trace_synced} 条交互轨迹")

    # 4. 保存本地报告（可选备份）
    report_file = os.path.join(REPORT_DIR, f"review-{today}.md")
    report = f"""# 承诺审查报告 {today}
- 总承诺: {classified['total']}
- 已完成: {len(classified['completed'])}
- 进行中: {len(classified['in_progress'])}
- 已过期: {len(classified['overdue'])}
- 同步到 Bitable: {sync_count} 条
- Bitable: {BITABLE_URL}
"""
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  备份报告: {report_file}")

    # 5. 发送到飞书群
    print("4. 发送审查摘要到飞书群...")
    send_to_feishu(classified, sync_count)

    print("\n✅ 承诺审查完成！")
    return report_file


if __name__ == "__main__":
    main()
