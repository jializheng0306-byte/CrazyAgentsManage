"""
Execution Snapshot - CAM-P0 (OpenBKN absorption)

执行时配置快照：task 进入 running/started 状态时冻结配置，
作为 append-only 不可变证据锚点（对齐 OpenBKN ActionTypeSnapshot）。

边界：
- R13 (GTD): 不转移承诺 ownership。快照只记录，不改 task owner。
- append-only: 一旦写入不可修改。
- 不可变: checksum 冻结写入时刻配置。

@see CR-20260723-002 (CAM 执行时配置快照 + MCP/Skill 只读投影)
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def capture_execution_snapshot(
    task_id,
    task_config,
    automation_state,
    permission_hooks=None,
    duplicate_hooks=None,
):
    """
    组装执行时配置快照。

    Args:
        task_id: 任务标识
        task_config: 任务配置 dict
        automation_state: 自动化状态
            (prototype/rehearsed/approved-for-automation/automated)
        permission_hooks: 权限钩子列表
        duplicate_hooks: 去重钩子列表

    Returns:
        不可变快照 dict（含 checksum + frozen_at）。
        R13: 不含 owner 字段，不转移承诺 ownership。
    """
    payload = {
        "task_id": task_id,
        "task_config": task_config,
        "automation_state": automation_state,
        "permission_hooks": permission_hooks or [],
        "duplicate_hooks": duplicate_hooks or [],
    }
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    checksum = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    return {
        **payload,
        "checksum": checksum,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
    }


def append_snapshot(snapshot, storage_path):
    """
    Append-only 持久化快照（JSON Lines）。

    不可变：一旦写入不可修改。R13: 不转移 ownership。

    Args:
        snapshot: capture_execution_snapshot 返回的快照
        storage_path: JSONL 文件路径

    Returns:
        写入的行数（始终 1）
    """
    path = Path(storage_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    return 1


def load_snapshots(storage_path):
    """
    读取所有快照（append-only，按写入顺序）。

    Args:
        storage_path: JSONL 文件路径

    Returns:
        快照 list
    """
    path = Path(storage_path)
    if not path.exists():
        return []
    snapshots = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                snapshots.append(json.loads(line))
    return snapshots


def verify_snapshot(snapshot):
    """
    校验快照 checksum 不变性。

    Args:
        snapshot: 快照 dict

    Returns:
        True 若 checksum 与内容一致（未被篡改）
    """
    payload = {
        "task_id": snapshot["task_id"],
        "task_config": snapshot["task_config"],
        "automation_state": snapshot["automation_state"],
        "permission_hooks": snapshot.get("permission_hooks", []),
        "duplicate_hooks": snapshot.get("duplicate_hooks", []),
    }
    payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    expected = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    return expected == snapshot["checksum"]
