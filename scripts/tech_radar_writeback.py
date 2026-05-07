#!/usr/bin/env python3
"""
Tech Radar 回写脚本

从 Bitable 读取人工确认后的状态，回写 shared-context/tech-radar.json，
让 radar 不再长期停留在 pending。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRAZY_ROOT = Path(os.environ.get("CRAZY_ROOT", os.path.expanduser("~/CrazyAgentsManage")))
RADAR_FILE = CRAZY_ROOT / "shared-context" / "tech-radar.json"
BITABLE_CONFIG = CRAZY_ROOT / "shared-context" / "bitable-config.json"
SYNC_STATE_FILE = CRAZY_ROOT / "shared-context" / "bitable-sync-state.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write Bitable review state back into tech-radar.json")
    parser.add_argument("--record-id", help="只回写指定的 Bitable record_id")
    parser.add_argument("--dry-run", action="store_true", help="仅打印回写结果，不落盘 tech-radar.json")
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


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_bitable_config() -> dict[str, Any]:
    if not BITABLE_CONFIG.exists():
        raise FileNotFoundError("bitable-config.json 不存在")
    return json.loads(BITABLE_CONFIG.read_text(encoding="utf-8"))


def normalize_radar_status(bitable_status: Any) -> str:
    value = str(bitable_status or "").strip().lower()
    status_map = {
        "pending": "pending",
        "待确认": "pending",
        "待处理": "pending",
        "confirmed": "confirmed",
        "已确认": "confirmed",
        "approved": "confirmed",
        "rejected": "rejected",
        "已拒绝": "rejected",
        "dismissed": "rejected",
        "implemented": "implemented",
        "已实施": "implemented",
        "done": "implemented",
    }
    return status_map.get(value, "pending")


def extract_bitable_records(config: dict[str, Any], target_record_id: str | None = None) -> list[dict[str, Any]]:
    app_token = config["app_token"]
    table_id = config["table_id"]

    if target_record_id:
        data = run_lark_json(
            [
                "lark-cli",
                "api",
                "GET",
                f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{target_record_id}",
            ]
        )
        record = data.get("data", {}).get("record", {})
        return [normalize_bitable_record(record)] if record else []

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
            "200",
        ],
        timeout=60,
    )
    return [normalize_bitable_record(item) for item in data.get("data", {}).get("items", [])]


def normalize_bitable_record(record: dict[str, Any]) -> dict[str, Any]:
    fields = record.get("fields", {})
    return {
        "record_id": record.get("record_id", ""),
        "name": fields.get("价值点名称", ""),
        "status": fields.get("状态", ""),
        "priority": fields.get("优先级", ""),
        "impact_assessment": fields.get("影响评估", ""),
        "action_suggested": fields.get("建议行动", ""),
        "notes": fields.get("备注", ""),
        "flowmind_sync": fields.get("FlowMind同步", ""),
        "url": fields.get("关联任务", ""),
    }


def build_record_lookup(sync_state: dict[str, Any]) -> dict[str, str]:
    record_map = sync_state.get("record_map", {})
    return record_map if isinstance(record_map, dict) else {}


def find_radar_entry(
    radar_entries: list[dict[str, Any]],
    bitable_record: dict[str, Any],
    record_lookup: dict[str, str],
) -> dict[str, Any] | None:
    record_id = bitable_record.get("record_id")
    name = bitable_record.get("name")

    for entry in radar_entries:
        if entry.get("bitable_record_id") == record_id:
            return entry

    if name and record_lookup.get(name) == record_id:
        for entry in radar_entries:
            if entry.get("name") == name:
                return entry

    if name:
        for entry in radar_entries:
            if entry.get("name") == name:
                return entry

    return None


def apply_bitable_to_radar(entry: dict[str, Any], bitable_record: dict[str, Any]) -> bool:
    updates = {
        "status": normalize_radar_status(bitable_record.get("status")),
        "priority": bitable_record.get("priority") or entry.get("priority", "P2"),
        "impact_assessment": bitable_record.get("impact_assessment") or entry.get("impact_assessment", ""),
        "action_suggested": bitable_record.get("action_suggested") or entry.get("action_suggested", ""),
        "notes": bitable_record.get("notes") or entry.get("notes", ""),
        "bitable_record_id": bitable_record.get("record_id", ""),
        "bitable_status": bitable_record.get("status", ""),
        "flowmind_sync_status": bitable_record.get("flowmind_sync", ""),
        "writeback_last_synced_at": now_iso(),
    }
    changed = False
    for key, value in updates.items():
        if entry.get(key) != value:
            entry[key] = value
            changed = True
    return changed


def run_writeback_for_records(records: list[dict[str, Any]], dry_run: bool = False) -> dict[str, Any]:
    radar = load_json(RADAR_FILE, {"entries": []})
    sync_state = load_json(SYNC_STATE_FILE, {"synced_ids": []})
    record_lookup = build_record_lookup(sync_state)

    results = {
        "scanned": len(records),
        "matched": 0,
        "updated": 0,
        "unmatched": [],
        "details": [],
    }

    entries = radar.get("entries", [])
    for record in records:
        entry = find_radar_entry(entries, record, record_lookup)
        if not entry:
            if record.get("name"):
                results["unmatched"].append(record["name"])
            continue
        results["matched"] += 1
        changed = apply_bitable_to_radar(entry, record)
        if changed:
            results["updated"] += 1
        results["details"].append(
            {
                "name": record.get("name", ""),
                "record_id": record.get("record_id", ""),
                "status": entry.get("status"),
                "flowmind_sync_status": entry.get("flowmind_sync_status"),
                "updated": changed,
            }
        )

    radar["last_writeback"] = now_iso()
    radar["writeback_source"] = "bitable"
    if not dry_run:
        save_json(RADAR_FILE, radar)

    return results


def run_writeback(target_record_id: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    config = load_bitable_config()
    records = extract_bitable_records(config, target_record_id)
    return run_writeback_for_records(records, dry_run=dry_run)


def main() -> int:
    args = parse_args()
    try:
        result = run_writeback(args.record_id, args.dry_run)
    except Exception as exc:
        print(f"❌ Tech Radar 回写失败: {exc}")
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
