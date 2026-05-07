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

LARK_CLI = os.environ.get("LARK_CLI", "lark-cli")
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
    "blocked": "blocked",
    "deferred": "deferred",
    "cancelled": "cancelled",
}

PRIORITY_MAP = {
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
}

FLOWMIND_STATUS_VALUES = {"draft", "submitted", "approved", "committed", "rejected"}
FEEDBACK_STATUS_MAP = {
    "blocked": "blocked",
    "deferred": "deferred",
    "cancelled": "cancelled",
}


def run_cmd(cmd, timeout=30):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip(), result.returncode


def run_json_cmd(args, timeout=30):
    env = os.environ.copy()
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
    output = result.stdout.strip()
    if result.returncode != 0 or not output:
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {}


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
            or "http://47.99.217.1/manage/timeline"
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


def flowmind_truth_request(config, candidate_id):
    encoded = urlparse.quote(candidate_id)
    url = f"{config['flowmind_trace_api_base_url']}/api/bridge/truth/{encoded}"
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


def flowmind_feedback_request(config, instance_id):
    if not instance_id:
        return {}
    encoded = urlparse.quote(instance_id)
    url = f"{config['flowmind_trace_api_base_url']}/api/bridge/feedback/{encoded}"
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


def unwrap_flowmind_payload(response):
    if not isinstance(response, dict):
        return {}
    payload = response.get("data")
    if isinstance(payload, dict):
        return payload
    return response


def normalize_trace_events(candidate_id, trace_response):
    trace_payload = unwrap_flowmind_payload(trace_response)
    raw_events = []
    if isinstance(trace_payload, dict):
        if isinstance(trace_payload.get("traceEvents"), list):
            raw_events = trace_payload.get("traceEvents", [])
        elif isinstance(trace_payload.get("events"), list):
            raw_events = trace_payload.get("events", [])
        elif isinstance(trace_payload.get("trace"), list):
            raw_events = trace_payload.get("trace", [])
        elif isinstance(trace_payload.get("data"), list):
            raw_events = trace_payload.get("data", [])

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
                "actor": event.get("actor") or "system",
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
                "semantic_refs": event.get("semanticRefs") or [],
            }
        )

    events.sort(key=lambda item: item.get("timestamp") or "")
    return events


def normalize_feedback_events(candidate_id, feedback_response):
    feedback_payload = unwrap_flowmind_payload(feedback_response)
    raw_events = feedback_payload.get("feedbackEvents", []) if isinstance(feedback_payload, dict) else []
    events = []
    for event in raw_events:
        if not isinstance(event, dict):
            continue
        if candidate_id and event.get("candidateId") != candidate_id:
            continue
        payload = event.get("payload") or {}
        events.append({
            "event_id": event.get("eventId"),
            "candidate_id": event.get("candidateId"),
            "event_type": event.get("eventType"),
            "timestamp": event.get("createdAt"),
            "candidate_status": payload.get("candidateStatus"),
            "summary": payload.get("notes") or payload.get("decision") or event.get("eventType") or "",
            "payload": payload,
            "semantic_refs": event.get("semanticRefs") or [],
        })
    events.sort(key=lambda item: item.get("timestamp") or "")
    return events


def build_feedback_summary(feedback_events):
    if not feedback_events:
        return {
            "latest_feedback_type": "",
            "latest_feedback_summary": "",
            "notes_text": "",
        }
    latest = feedback_events[-1]
    lines = []
    for event in feedback_events:
        event_type = str(event.get("event_type") or "").strip()
        timestamp = event.get("timestamp") or "--"
        summary = event.get("summary") or ""
        if event_type:
            lines.append(f"{timestamp} {event_type}: {summary}")
    return {
        "latest_feedback_type": latest.get("event_type") or "",
        "latest_feedback_summary": latest.get("summary") or "",
        "notes_text": " | ".join(lines)[:1000],
    }


def resolve_local_status(status_raw, feedback_summary, flowmind_status=""):
    latest_feedback_type = str(feedback_summary.get("latest_feedback_type") or "").strip().lower()
    if latest_feedback_type in FEEDBACK_STATUS_MAP:
        return FEEDBACK_STATUS_MAP[latest_feedback_type]
    if str(flowmind_status or "").strip().lower() == "committed":
        return STATUS_MAP["done"]
    return STATUS_MAP.get(status_raw, "待处理")


def build_trace_summary(truth_payload, trace_events):
    truth_payload = unwrap_flowmind_payload(truth_payload)
    truth_status = str(truth_payload.get("status") or "").strip().lower()
    if truth_status not in FLOWMIND_STATUS_VALUES:
        truth_status = ""
    latest_evidence_summary = ""
    if isinstance(truth_payload.get("latestEvidence"), dict):
        latest_evidence_summary = str(truth_payload["latestEvidence"].get("summary") or "").strip()

    if not trace_events:
        return {
            "flowmind_status": truth_status,
            "last_trace_at": None,
            "trace_summary": "",
            "trace_event_count": 0,
            "last_trace_summary": "",
            "latest_evidence_summary": latest_evidence_summary,
            "trace_empty": True,
        }

    latest = trace_events[-1]
    latest_summary = latest.get("summary") or latest.get("response_summary") or ""
    trace_summary_parts = []
    if latest_evidence_summary:
        trace_summary_parts.append(latest_evidence_summary)
    if latest_summary and latest_summary not in trace_summary_parts:
        trace_summary_parts.append(latest_summary)

    return {
        "flowmind_status": truth_status,
        "last_trace_at": datetime_to_ms(latest.get("timestamp")),
        "trace_summary": " | ".join(trace_summary_parts)[:500],
        "trace_event_count": len(trace_events),
        "last_trace_summary": latest_summary[:500],
        "latest_evidence_summary": latest_evidence_summary,
        "trace_empty": False,
    }


def list_fields(app_token, table_id):
    result = run_json_cmd(
        [
            LARK_CLI,
            "base",
            "+field-list",
            "--as",
            "bot",
            "--base-token",
            app_token,
            "--table-id",
            table_id,
            "--limit",
            "200",
        ],
        timeout=30,
    )
    return result.get("data", {}).get("fields", []) if isinstance(result, dict) else []


def ensure_main_table_fields(app_token, table_id):
    if DRY_RUN or not app_token or not table_id:
        return set()

    existing_fields = {field.get("name") for field in list_fields(app_token, table_id)}
    required_specs = [
        {"name": "flowmind_status", "type": "text"},
        {"name": "last_trace_at", "type": "datetime", "style": {"format": "yyyy/MM/dd HH:mm"}},
        {"name": "trace_summary", "type": "text"},
        {"name": "last_governance_status", "type": "text"},
        {"name": "last_governance_feedback", "type": "text"},
    ]

    for spec in required_specs:
        if spec["name"] in existing_fields:
            continue
        run_json_cmd(
            [
                LARK_CLI,
                "base",
                "+field-create",
                "--as",
                "bot",
                "--base-token",
                app_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps(spec, ensure_ascii=False),
            ],
            timeout=30,
        )
        existing_fields.add(spec["name"])

    return existing_fields


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
    main_fields = ensure_main_table_fields(app_token, main_table_id)

    main_sync_count = 0
    trace_sync_count = 0
    trace_summary_by_promise = {}

    for promise in promises:
        promise_id = str(promise.get("id", "")).strip()
        if not promise_id:
            continue

        truth_payload = {}
        trace_events = []
        feedback_events = []
        feedback_summary = build_feedback_summary([])
        trace_summary = build_trace_summary({}, [])
        flowmind_id = str(promise.get("flowmind_candidate_id", "")).strip()
        instance_id = str(
            promise.get("instance_id")
            or promise.get("flowmind_instance_id")
            or promise.get("source_instance_id")
            or ""
        ).strip()
        if flowmind_id:
            truth_payload = flowmind_truth_request(config, flowmind_id)
            trace_response = flowmind_trace_request(config, flowmind_id)
            trace_events = normalize_trace_events(flowmind_id, trace_response)
            truth_core = unwrap_flowmind_payload(truth_payload)
            instance_id = instance_id or str(truth_core.get("instanceId") or "").strip()
            feedback_response = flowmind_feedback_request(config, instance_id)
            feedback_events = normalize_feedback_events(flowmind_id, feedback_response)
            feedback_summary = build_feedback_summary(feedback_events)
            trace_summary = build_trace_summary(truth_payload, trace_events)
            trace_summary_by_promise[promise_id] = trace_summary

            if trace_table_id:
                for event in trace_events:
                    fields = {
                        "trace_id": event["trace_id"],
                        "promise_id": promise_id,
                        "candidate_id": event["candidate_id"],
                        "module": event["flowmind_module"],
                        "action": event["action"],
                        "actor": event["actor"],
                        "summary": event["summary"][:500],
                        "from_status": str(event.get("from_status") or "")[:100],
                        "to_status": str(event.get("to_status") or "")[:100],
                        "多行文本": json.dumps(event.get("request_payload") or {}, ensure_ascii=False)
                        if event.get("request_payload")
                        else "",
                    }
                    timestamp_ms = datetime_to_ms(event.get("timestamp"))
                    if timestamp_ms:
                        fields["timestamp"] = timestamp_ms
                    if upsert_record(
                        app_token,
                        trace_table_id,
                        existing_trace,
                        event["trace_id"],
                        fields,
                    ):
                        trace_sync_count += 1

                for event in feedback_events:
                    fields = {
                        "trace_id": f"feedback:{event['event_id']}",
                        "promise_id": promise_id,
                        "candidate_id": flowmind_id,
                        "module": "feedback",
                        "action": event["event_type"],
                        "actor": "human" if event["event_type"] in {"confirmed", "clarified"} else "system",
                        "summary": str(event.get("summary") or event.get("event_type") or "")[:500],
                        "from_status": "",
                        "to_status": str(event.get("candidate_status") or "")[:100],
                        "多行文本": json.dumps(event.get("payload") or {}, ensure_ascii=False) if event.get("payload") else "",
                    }
                    timestamp_ms = datetime_to_ms(event.get("timestamp"))
                    if timestamp_ms:
                        fields["timestamp"] = timestamp_ms
                    if upsert_record(
                        app_token,
                        trace_table_id,
                        existing_trace,
                        fields["trace_id"],
                        fields,
                    ):
                        trace_sync_count += 1

        status_raw = str(promise.get("status", "pending")).lower()
        priority_raw = str(promise.get("priority", "P3")).upper()
        note_parts = []
        existing_note = str(promise.get("notes") or promise.get("remark") or promise.get("remarks") or "").strip()
        if existing_note:
            note_parts.append(existing_note)
        if trace_summary["trace_empty"]:
            note_parts.append("trace empty")
        if feedback_summary["notes_text"]:
            note_parts.append(f"FlowMind feedback: {feedback_summary['notes_text']}")
        fields = {
            "promise_id": promise_id,
            "title": str(promise.get("title", ""))[:200],
            "description": str(promise.get("description", ""))[:500],
            "source": str(promise.get("source", ""))[:100],
            "status": resolve_local_status(
                status_raw,
                feedback_summary,
                trace_summary["flowmind_status"],
            ),
            "priority": PRIORITY_MAP.get(priority_raw, "P3"),
            "flowmind_status": trace_summary["flowmind_status"],
            "trace_summary": trace_summary["trace_summary"],
            "trace_event_count": trace_summary["trace_event_count"],
            "last_trace_summary": trace_summary["last_trace_summary"],
            "备注": " | ".join(note_parts)[:1000],
        }
        if "last_governance_status" in main_fields:
            fields["last_governance_status"] = trace_summary["flowmind_status"]
        if "last_governance_feedback" in main_fields:
            fields["last_governance_feedback"] = feedback_summary["latest_feedback_type"]

        created_at = datetime_to_ms(promise.get("created_at", ""))
        if created_at:
            fields["created_at"] = created_at

        due_date = date_to_ms(promise.get("due_date", promise.get("deadline", "")))
        if due_date:
            fields["due_date"] = due_date

        completed_at = datetime_to_ms(promise.get("completed_at", ""))
        if not completed_at and trace_summary["flowmind_status"] == "committed":
            completed_at = trace_summary["last_trace_at"]
        if completed_at:
            fields["completed_at"] = completed_at

        if flowmind_id:
            fields["flowmind_candidate_id"] = flowmind_id
            if "timeline_url" in main_fields:
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
