#!/usr/bin/env python3
"""
承诺审查脚本 v3
每日 09:00 执行
功能：
1. 扫描活跃承诺
2. 主表同步到飞书多维表格
3. 按 FlowMind candidateId 拉取 trace 并同步子表
4. 保留本地 MD 备份，但 Bitable 是主输出
"""

import json
import os
import shlex
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

PROMISE_ACTIVE_DIR = Path(os.path.expanduser("~/.hermes/promises/active"))
PROMISE_ROOT_DIR = Path(os.path.expanduser("~/.hermes/promises"))
REPORT_DIR = Path(os.path.expanduser("~/.hermes/promises/reviews"))
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "shared-context" / "promise-bitable-config.json"

DRY_RUN = os.environ.get("HERMES_CRON_DRY_RUN", "0") == "1"

STATUS_MAP = {
    "pending": "待处理",
    "in_progress": "进行中",
    "completed": "已完成",
    "done": "已完成",
    "overdue": "已过期",
    "rejected": "已拒绝",
    "blocked": "进行中",
}

PRIORITY_MAP = {
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
}


def run_cmd(cmd, timeout=30):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_config():
    config_path = Path(os.environ.get("PROMISE_BITABLE_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    file_config = load_json(config_path)

    bitable = file_config.get("bitable", {})
    flowmind = file_config.get("flowmind", {})
    webui = file_config.get("webui", {})
    feishu = file_config.get("feishu", {})

    app_token = os.environ.get("PROMISE_BITABLE_APP_TOKEN") or bitable.get("app_token", "")
    main_table_id = os.environ.get("PROMISE_BITABLE_MAIN_TABLE_ID") or bitable.get("main_table_id", "")
    trace_table_id = os.environ.get("PROMISE_BITABLE_TRACE_TABLE_ID") or bitable.get("trace_table_id", "")
    bitable_url = bitable.get("url") or (
        f"https://bcn7uazoofu0.feishu.cn/base/{app_token}" if app_token else ""
    )

    return {
        "config_path": config_path,
        "bitable_app_token": app_token,
        "bitable_main_table_id": main_table_id,
        "bitable_trace_table_id": trace_table_id,
        "bitable_url": os.environ.get("PROMISE_BITABLE_URL") or bitable_url,
        "chat_id": os.environ.get("PROMISE_REVIEW_CHAT_ID") or feishu.get(
            "chat_id", "oc_bbde428675a7c267d55c3f0663ca701d"
        ),
        "flowmind_trace_api_base_url": (
            os.environ.get("FLOWMIND_TRACE_API_BASE_URL")
            or os.environ.get("FLOWMIND_API_BASE_URL")
            or flowmind.get("base_url")
            or "http://127.0.0.1:3001"
        ).rstrip("/"),
        "flowmind_trace_api_bearer_token": (
            os.environ.get("FLOWMIND_TRACE_API_BEARER_TOKEN")
            or os.environ.get("FLOWMIND_API_KEY")
            or flowmind.get("api_key")
            or "flowmind-dev-token"
        ),
        "timeline_base_url": (
            os.environ.get("PROMISE_TIMELINE_BASE_URL")
            or webui.get("timeline_base_url")
            or "http://47.99.217.1/timeline"
        ).rstrip("/"),
    }


def build_timeline_url(config, candidate_id):
    if not candidate_id:
        return ""
    base = config.get("timeline_base_url", "").rstrip("/")
    if not base:
        return ""
    return f"{base}?candidateId={urlparse.quote(candidate_id)}"


def scan_promises():
    promises = []

    if PROMISE_ACTIVE_DIR.exists():
        for json_file in PROMISE_ACTIVE_DIR.glob("*.json"):
            try:
                data = load_json(json_file)
                if isinstance(data, dict):
                    data["_source_file"] = json_file.name
                    data["_source_dir"] = "active"
                    promises.append(data)
            except Exception:
                continue

    if PROMISE_ROOT_DIR.exists():
        for json_file in PROMISE_ROOT_DIR.glob("*.json"):
            try:
                data = load_json(json_file)
                if isinstance(data, dict):
                    data["_source_file"] = json_file.name
                    data["_source_dir"] = "root"
                    promises.append(data)
                elif isinstance(data, list):
                    for promise in data:
                        promise["_source_file"] = json_file.name
                        promise["_source_dir"] = "root"
                    promises.extend(data)
            except Exception:
                continue

    return promises


def classify_promises(promises):
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

    for promise in promises:
        status = str(promise.get("status", "pending")).lower()
        due = promise.get("due_date", promise.get("deadline", ""))

        if status in ("done", "completed", "已完成"):
            result["completed"].append(promise)
        elif status in ("blocked", "阻塞"):
            result["blocked"].append(promise)
        elif due:
            if due < today:
                result["overdue"].append(promise)
            elif due == today:
                result["due_today"].append(promise)
            elif due <= next_week:
                result["due_soon"].append(promise)
            else:
                result["in_progress"].append(promise)
        else:
            if status in ("in_progress", "进行中"):
                result["in_progress"].append(promise)
            else:
                result["pending_count"] += 1

    return result


def datetime_to_ms(dt_str):
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except ValueError:
        pass

    try:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(str(dt_str)[:19], fmt)
                return int(dt.timestamp() * 1000)
            except ValueError:
                continue
    except Exception:
        return None
    return None


def date_to_ms(date_str):
    if not date_str:
        return None
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


def _bitable_api(path, method="GET", payload=None, params=None, timeout=20):
    if DRY_RUN:
        return {}

    parts = [f'lark-cli api {method} "{path}"']
    if params is not None:
        parts.append(f"--params {shlex.quote(json.dumps(params, ensure_ascii=False))}")
    if payload is not None:
        parts.append(f"--data {shlex.quote(json.dumps(payload, ensure_ascii=False))}")
    cmd = " ".join(parts)
    output, code = run_cmd(cmd, timeout=timeout)
    if code != 0 or not output:
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {}


def extract_bitable_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("text", "")
        return str(first)
    if isinstance(value, dict):
        return value.get("text", "")
    return ""


def list_existing_records(app_token, table_id, key_field):
    if not app_token or not table_id or DRY_RUN:
        return {}

    data = _bitable_api(
        f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        method="GET",
        params={"page_size": 500},
        timeout=30,
    )

    result = {}
    for item in data.get("data", {}).get("items", []):
        fields = item.get("fields", {})
        record_key = extract_bitable_text(fields.get(key_field))
        if record_key:
            result[str(record_key)] = item.get("record_id")
    return result


def upsert_record(app_token, table_id, existing_records, key, fields):
    if DRY_RUN or not app_token or not table_id or not key:
        return False

    if key in existing_records:
        path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{existing_records[key]}"
        response = _bitable_api(path, method="PUT", payload={"fields": fields})
        return bool(response)

    path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    response = _bitable_api(path, method="POST", payload={"fields": fields})
    if response.get("data", {}).get("record", {}).get("record_id"):
        existing_records[key] = response["data"]["record"]["record_id"]
    return bool(response)


def flowmind_trace_request(config, candidate_id):
    encoded = urlparse.quote(candidate_id)
    url = f"{config['flowmind_trace_api_base_url']}/api/bridge/trace/{encoded}"
    req = urlrequest.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {config['flowmind_trace_api_bearer_token']}",
        },
        method="GET",
    )
    try:
        with urlrequest.urlopen(req, timeout=10) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
            return json.loads(body) if body else {}
    except (urlerror.URLError, urlerror.HTTPError, TimeoutError, OSError, json.JSONDecodeError):
        return {}


def normalize_trace_events(candidate_id, trace_response):
    raw_events = []
    if isinstance(trace_response, dict):
        if isinstance(trace_response.get("events"), list):
            raw_events = trace_response.get("events", [])
        elif isinstance(trace_response.get("trace"), list):
            raw_events = trace_response.get("trace", [])
        elif isinstance(trace_response.get("data"), list):
            raw_events = trace_response.get("data", [])

    events = []
    for index, event in enumerate(raw_events):
        if not isinstance(event, dict):
            continue
        timestamp = event.get("timestamp") or event.get("createdAt") or event.get("occurredAt")
        summary = event.get("summary") or event.get("detail") or event.get("label") or event.get("action") or ""
        trace_id = event.get("traceId") or event.get("id") or f"{candidate_id}:{index}"
        events.append(
            {
                "trace_id": str(trace_id),
                "candidate_id": candidate_id,
                "direction": event.get("direction") or "FlowMind→Hermes",
                "flowmind_module": event.get("module") or event.get("moduleId") or "bridge",
                "action": event.get("action") or event.get("eventType") or "query",
                "request_payload": event.get("payload") or event.get("requestPayload") or {},
                "response_summary": summary,
                "status": event.get("status") or event.get("toStatus") or event.get("result") or "success",
                "timestamp": timestamp,
                "latency_ms": event.get("latencyMs") or event.get("durationMs"),
                "from_status": event.get("fromStatus"),
                "to_status": event.get("toStatus") or event.get("status"),
                "summary": summary,
            }
        )

    events.sort(key=lambda item: item.get("timestamp") or "")
    return events


def build_trace_summary(trace_events):
    if not trace_events:
        return {
            "flowmind_status": "",
            "last_trace_at": None,
            "trace_summary": "",
            "trace_event_count": 0,
            "last_trace_summary": "",
        }

    latest = trace_events[-1]
    latest_status = latest.get("to_status") or latest.get("status") or ""
    latest_summary = latest.get("summary") or latest.get("response_summary") or ""
    modules = []
    for event in trace_events:
        module = event.get("flowmind_module")
        if module and module not in modules:
            modules.append(module)

    return {
        "flowmind_status": latest_status,
        "last_trace_at": datetime_to_ms(latest.get("timestamp")),
        "trace_summary": " → ".join(modules[:4]),
        "trace_event_count": len(trace_events),
        "last_trace_summary": latest_summary[:500],
    }


def sync_to_bitable(promises, config):
    app_token = config["bitable_app_token"]
    main_table_id = config["bitable_main_table_id"]
    trace_table_id = config["bitable_trace_table_id"]
    if not app_token or not main_table_id:
        print("  ⚠️ 未配置 Bitable 主表，跳过同步")
        return {"main_sync_count": 0, "trace_sync_count": 0, "trace_summary_by_promise": {}}

    if DRY_RUN:
        print("  DRY RUN: 跳过 Bitable 同步")
        return {"main_sync_count": 0, "trace_sync_count": 0, "trace_summary_by_promise": {}}

    existing_main = list_existing_records(app_token, main_table_id, "promise_id")
    existing_trace = (
        list_existing_records(app_token, trace_table_id, "trace_id") if trace_table_id else {}
    )

    main_sync_count = 0
    trace_sync_count = 0
    trace_summary_by_promise = {}

    for promise in promises:
        promise_id = str(promise.get("id", "")).strip()
        if not promise_id:
            continue

        trace_summary = build_trace_summary([])
        flowmind_id = str(promise.get("flowmind_candidate_id", "")).strip()
        if flowmind_id:
            trace_response = flowmind_trace_request(config, flowmind_id)
            trace_events = normalize_trace_events(flowmind_id, trace_response)
            trace_summary = build_trace_summary(trace_events)
            trace_summary_by_promise[promise_id] = trace_summary

            if trace_table_id:
                for event in trace_events:
                    fields = {
                        "trace_id": event["trace_id"],
                        "promise_id": promise_id,
                        "candidate_id": event["candidate_id"],
                        "direction": event["direction"],
                        "flowmind_module": event["flowmind_module"],
                        "action": event["action"],
                        "request_payload": json.dumps(event["request_payload"], ensure_ascii=False)
                        if event["request_payload"]
                        else "",
                        "response_summary": event["response_summary"][:500],
                        "status": str(event["status"])[:100],
                    }
                    timestamp_ms = datetime_to_ms(event.get("timestamp"))
                    if timestamp_ms:
                        fields["timestamp"] = timestamp_ms
                    if event.get("latency_ms") is not None:
                        fields["latency_ms"] = event["latency_ms"]
                    if upsert_record(
                        app_token,
                        trace_table_id,
                        existing_trace,
                        event["trace_id"],
                        fields,
                    ):
                        trace_sync_count += 1

        status_raw = str(promise.get("status", "pending")).lower()
        priority_raw = str(promise.get("priority", "P3")).upper()
        fields = {
            "promise_id": promise_id,
            "title": str(promise.get("title", ""))[:200],
            "description": str(promise.get("description", ""))[:500],
            "source": str(promise.get("source", ""))[:100],
            "status": STATUS_MAP.get(status_raw, "待处理"),
            "priority": PRIORITY_MAP.get(priority_raw, "P3"),
            "flowmind_status": trace_summary["flowmind_status"],
            "trace_summary": trace_summary["trace_summary"],
            "trace_event_count": trace_summary["trace_event_count"],
            "last_trace_summary": trace_summary["last_trace_summary"],
        }

        created_at = datetime_to_ms(promise.get("created_at", ""))
        if created_at:
            fields["created_at"] = created_at

        due_date = date_to_ms(promise.get("due_date", promise.get("deadline", "")))
        if due_date:
            fields["due_date"] = due_date

        completed_at = datetime_to_ms(promise.get("completed_at", ""))
        if completed_at:
            fields["completed_at"] = completed_at

        if flowmind_id:
            fields["flowmind_candidate_id"] = flowmind_id
            fields["timeline_url"] = build_timeline_url(config, flowmind_id)
        if trace_summary["last_trace_at"]:
            fields["last_trace_at"] = trace_summary["last_trace_at"]

        if upsert_record(app_token, main_table_id, existing_main, promise_id, fields):
            main_sync_count += 1

    return {
        "main_sync_count": main_sync_count,
        "trace_sync_count": trace_sync_count,
        "trace_summary_by_promise": trace_summary_by_promise,
    }


def write_backup_report(report_path, classified, sync_result, config):
    report = f"""# 承诺审查报告 {datetime.now().strftime("%Y-%m-%d")}
- 总承诺: {classified['total']}
- 已完成: {len(classified['completed'])}
- 进行中: {len(classified['in_progress'])}
- 已过期: {len(classified['overdue'])}
- 主表同步: {sync_result['main_sync_count']} 条
- Trace 子表同步: {sync_result['trace_sync_count']} 条
- Bitable 主输出: {config['bitable_url'] or '未配置'}
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def send_to_feishu(classified, sync_result, config):
    today = datetime.now().strftime("%Y-%m-%d")
    total = classified["total"]
    in_progress = len(classified["in_progress"])
    done = len(classified["completed"])
    overdue = len(classified["overdue"])
    due_today = len(classified["due_today"])
    due_soon = len(classified["due_soon"])
    blocked = len(classified["blocked"])
    pending = classified.get("pending_count", 0)

    alerts = []
    if overdue > 0:
        alerts.append(f"🚨 已过期: {overdue} 项")
    if due_today > 0:
        alerts.append(f"⚠️ 今日到期: {due_today} 项")
    if blocked > 0:
        alerts.append(f"🚧 阻塞: {blocked} 项")
    alert_block = "\n".join(alerts)
    if alert_block:
        alert_block += "\n"

    bitable_url = config["bitable_url"] or "未配置"
    main_table_id = config["bitable_main_table_id"] or ""
    gantt_url = f"{bitable_url}?table={main_table_id}&view=gantt" if main_table_id and bitable_url else "未配置"

    message = f"""📋 承诺审查报告 ({today})
━━━━━━━━━━━━━━━━━━━

📊 统计:
- 总承诺: {total} | 进行中: {in_progress} | 已完成: {done}
- 待处理: {pending} | 7天内到期: {due_soon}
{alert_block}🔄 主表同步: {sync_result['main_sync_count']} 条
🔄 Trace 同步: {sync_result['trace_sync_count']} 条

━━━━━━━━━━━━━━━━━━━
📊 承诺主表: {bitable_url}
📊 甘特图: {gantt_url}
📝 本地备份: ~/.hermes/promises/reviews/
"""

    if DRY_RUN:
        print("  DRY RUN: 跳过飞书群发送")
        print(message)
        return True

    cmd = (
        f"lark-cli im +messages-send --chat-id {shlex.quote(config['chat_id'])} "
        f"--text {shlex.quote(message)}"
    )
    _, code = run_cmd(cmd)
    print(f"  群消息: {'✅' if code == 0 else '❌'}")
    return code == 0


def main():
    print("📋 开始承诺审查 v3 (Bitable 主输出 + Trace 子表)...")
    config = load_config()
    print(f"  配置文件: {config['config_path']}")

    print("\n1. 扫描承诺文件...")
    promises = scan_promises()
    print(f"  找到 {len(promises)} 条承诺")

    print("2. 分类统计...")
    classified = classify_promises(promises)

    print("3. 同步到 Bitable...")
    sync_result = sync_to_bitable(promises, config)
    print(
        f"  主表同步 {sync_result['main_sync_count']} 条，"
        f"Trace 子表同步 {sync_result['trace_sync_count']} 条"
    )

    report_path = REPORT_DIR / f"review-{datetime.now().strftime('%Y%m%d')}.md"
    print("4. 写本地 MD 备份...")
    write_backup_report(report_path, classified, sync_result, config)
    print(f"  备份报告: {report_path}")

    print("5. 发送审查摘要到飞书群...")
    send_to_feishu(classified, sync_result, config)

    print("\n✅ 承诺审查完成！")
    return str(report_path)


if __name__ == "__main__":
    main()
