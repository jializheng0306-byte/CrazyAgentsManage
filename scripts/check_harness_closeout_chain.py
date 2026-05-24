#!/usr/bin/env python3
"""Validate harness closeout artifacts against traces and lane metadata."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
TRACE_SUCCESS = ROOT / "harness" / "trace" / "successes"
TRACE_FAILURE = ROOT / "harness" / "trace" / "failures"
CLOSEOUTS = ROOT / "harness" / "closeouts"
ENFORCEMENT_START = "2026-05-24"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _trace_files(trace_dir: Path) -> list[Path]:
    if not trace_dir.exists():
        return []
    return sorted([path for path in trace_dir.glob("*.json") if path.name != "TEMPLATE.json"])


def _closeout_files() -> list[Path]:
    if not CLOSEOUTS.exists():
        return []
    return sorted([path for path in CLOSEOUTS.glob("*.json") if path.name != "TEMPLATE.json"])


def _is_enforced(record: dict) -> bool:
    stamp = str(record.get("timestamp") or "")
    return stamp[:10] >= ENFORCEMENT_START


def main() -> int:
    errors: list[str] = []
    success_files = _trace_files(TRACE_SUCCESS)
    failure_files = _trace_files(TRACE_FAILURE)
    closeout_files = _closeout_files()

    if not CLOSEOUTS.exists():
        errors.append("harness/closeouts 目录缺失")

    closeout_by_trace: dict[str, dict] = {}
    for path in closeout_files:
        payload = _load_json(path)
        if not isinstance(payload, dict):
            errors.append(f"closeout 文件不可解析: {path.relative_to(ROOT)}")
            continue
        trace = payload.get("trace") if isinstance(payload.get("trace"), dict) else {}
        trace_id = str(trace.get("id") or "").strip()
        if not trace_id:
            errors.append(f"closeout 缺少 trace.id: {path.relative_to(ROOT)}")
            continue
        closeout_by_trace[trace_id] = payload

        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        if _is_enforced(payload):
            lane = str(context.get("lane") or "").strip()
            lane_source = str(context.get("laneSource") or "").strip()
            worktree = str(context.get("worktree") or "").strip()
            if not lane or not lane_source or not worktree:
                errors.append(f"closeout 缺少 lane/worktree traceability: {path.relative_to(ROOT)}")
            if payload.get("status") == "success" and not payload.get("governance"):
                errors.append(f"success closeout 缺少 governance 结果: {path.relative_to(ROOT)}")
            if payload.get("status") == "failed" and payload.get("critic") is None:
                errors.append(f"failed closeout 缺少 critic 分析: {path.relative_to(ROOT)}")

    for path in success_files + failure_files:
        payload = _load_json(path)
        if not isinstance(payload, dict):
            errors.append(f"trace 文件不可解析: {path.relative_to(ROOT)}")
            continue
        trace_id = str(payload.get("id") or "").strip()
        if not trace_id:
            if _is_enforced(payload):
                errors.append(f"trace 缺少 id: {path.relative_to(ROOT)}")
            continue
        if _is_enforced(payload) and trace_id not in closeout_by_trace:
            errors.append(f"enforced trace 未绑定 closeout: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK: harness closeout chain is consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
