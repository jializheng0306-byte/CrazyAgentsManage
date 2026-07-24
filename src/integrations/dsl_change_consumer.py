#!/usr/bin/env python3
"""
DSL Change Consumer — 消费 flow:fmd:dsl-changed 事件刷新投影缓存

Phase 3.2 跨仓语义 Pipeline 的 CAM 侧消费者。

实现策略（双轨）：
1. Pulsar 消费（如果 pulsar-client 可用）：监听 flow:fmd:dsl-changed 事件
2. 轮询回退（默认）：定期比对 FMD DSL checksum，检测变更时刷新缓存

GTD 层级判定：H2 系统维护（Agent full_participation）
Invariant 1 守卫：只刷新缓存，不写 truth

@see plan: 08-trustgraph-absorption-implementation-plan.md Phase 3.2
@see FMD DslChangeEmitter: flow:fmd:dsl-changed 事件源
"""

import json
import os
import sys
import threading
import time
from datetime import datetime, timezone

# Ensure src/ is in path for integrations package
_SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from integrations.fmd_semantic_client import get_client

PUBSUB_BACKEND = os.getenv("PUBSUB_BACKEND", "memory")  # memory | pulsar
PULSAR_HOST = os.getenv("PULSAR_HOST", "pulsar://localhost:6650")
FMD_DSL_ROOT = os.getenv("FMD_DSL_ROOT", "")
POLL_INTERVAL = int(os.getenv("DSL_CHANGE_POLL_INTERVAL", "60"))  # 轮询间隔（秒）

_QUEUE_ID = "flow:fmd:dsl-changed"
_last_checksum = None
_poll_thread = None
_poll_stop = threading.Event()


def _compute_dsl_checksum():
    """计算当前 FMD DSL 的 checksum（简单版：文件数 + 总大小 + 最新修改时间）"""
    if not FMD_DSL_ROOT or not os.path.isdir(FMD_DSL_ROOT):
        return None

    total_size = 0
    file_count = 0
    latest_mtime = 0
    for root, _dirs, files in os.walk(FMD_DSL_ROOT):
        for fname in files:
            if fname.endswith(".md"):
                fpath = os.path.join(root, fname)
                try:
                    stat = os.stat(fpath)
                    total_size += stat.st_size
                    file_count += 1
                    if stat.st_mtime > latest_mtime:
                        latest_mtime = stat.st_mtime
                except OSError:
                    continue

    return f"files={file_count},size={total_size},mtime={latest_mtime}"


def _on_dsl_changed(event):
    """处理 dsl-changed 事件：刷新投影缓存

    Invariant 1 守卫：只刷新缓存，不写 truth
    """
    client = get_client()
    client.invalidate_cache()

    print(
        f"[DslChangeConsumer] dsl-changed event received, cache invalidated: "
        f"entryId={event.get('entryId')}, changeType={event.get('changeType')}, "
        f"checksum={event.get('checksum')}, acceptedSha={event.get('acceptedSha')}",
        flush=True,
    )


def _poll_loop():
    """轮询回退：定期比对 DSL checksum，检测变更时刷新缓存"""
    global _last_checksum

    while not _poll_stop.is_set():
        try:
            current_checksum = _compute_dsl_checksum()
            if current_checksum is None:
                _poll_stop.wait(POLL_INTERVAL)
                continue

            if _last_checksum is not None and current_checksum != _last_checksum:
                # 检测到变更
                _on_dsl_changed({
                    "entryId": "*",
                    "changeType": "modified",
                    "checksum": current_checksum,
                    "acceptedSha": None,
                    "changedAt": datetime.now(timezone.utc).isoformat(),
                    "source": "poll-detector",
                })

            _last_checksum = current_checksum
        except Exception as e:
            print(f"[DslChangeConsumer] poll error: {e}", flush=True)

        _poll_stop.wait(POLL_INTERVAL)


def start_consumer():
    """启动 DSL Change Consumer

    根据 PUBSUB_BACKEND 环境变量选择消费策略：
    - pulsar: 尝试使用 pulsar-client 监听事件
    - memory/其他: 使用轮询回退
    """
    global _poll_thread

    if PUBSUB_BACKEND == "pulsar":
        try:
            _start_pulsar_consumer()
            print(f"[DslChangeConsumer] Pulsar consumer started: {_QUEUE_ID}", flush=True)
            return
        except ImportError:
            print(
                "[DslChangeConsumer] pulsar-client not installed, falling back to polling",
                flush=True,
            )
        except Exception as e:
            print(f"[DslChangeConsumer] Pulsar consumer failed: {e}, falling back to polling", flush=True)

    # 轮询回退
    _poll_stop.clear()
    _poll_thread = threading.Thread(target=_poll_loop, daemon=True, name="dsl-change-poller")
    _poll_thread.start()
    print(
        f"[DslChangeConsumer] Polling consumer started (interval={POLL_INTERVAL}s, "
        f"dsl_root={FMD_DSL_ROOT})",
        flush=True,
    )


def stop_consumer():
    """停止 Consumer"""
    _poll_stop.set()
    if _poll_thread and _poll_thread.is_alive():
        _poll_thread.join(timeout=5)
    print("[DslChangeConsumer] Consumer stopped", flush=True)


def _start_pulsar_consumer():
    """启动 Pulsar 消费者（需要 pulsar-client 库）"""
    import pulsar  # type: ignore  # noqa: F401

    client = pulsar.Client(PULSAR_HOST)
    consumer = client.subscribe(
        _QUEUE_ID,
        subscription_name="cam-dsl-change-consumer",
        initial_position=pulsar.InitialPosition.Earliest,
    )

    def _listen():
        while not _poll_stop.is_set():
            try:
                msg = consumer.receive(timeout_millis=POLL_INTERVAL * 1000)
                event = json.loads(msg.data().decode("utf-8"))
                _on_dsl_changed(event)
                consumer.acknowledge(msg)
            except Exception:
                continue

    thread = threading.Thread(target=_listen, daemon=True, name="pulsar-dsl-consumer")
    thread.start()


def get_consumer_status():
    """返回 Consumer 状态信息"""
    return {
        "queue_id": _QUEUE_ID,
        "backend": PUBSUB_BACKEND,
        "poll_interval": POLL_INTERVAL,
        "polling_active": _poll_thread is not None and _poll_thread.is_alive(),
        "last_checksum": _last_checksum,
        "dsl_root": FMD_DSL_ROOT,
    }
