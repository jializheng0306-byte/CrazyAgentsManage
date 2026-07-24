#!/usr/bin/env python3
"""
CAM WebUI v2 API Blueprint — TrustGraph 能力吸收 P3 + Phase 3

新增端点：
- GET  /api/v2/data-resources         — 只读投影 FMD DSL 数据资源维度 (P3.2)
- GET  /api/v2/dsl-entries             — 只读投影 FMD DSL 全量条目
- GET  /api/v2/dsl-change-status       — DSL Change Consumer 状态
- POST /api/v2/dsl-change/refresh      — 手动触发缓存刷新
- GET  /api/v2/agent/chat/stream       — AgentChat 流式 SSE (P3.1)

GTD 层级判定：
- P3.1 AgentChat 流式: H0（执行，Agent full_participation）
- P3.2 数据资源治理: H0-H2（基础设施，无意义赋予）
- Phase 3.2 消费 dsl-changed: H2（系统维护）

Invariant 1 守卫：只读投影，不写 truth

@see plan: 08-trustgraph-absorption-implementation-plan.md P3 + Phase 3
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# Ensure src/ is in path for integrations package
_SRC_DIR = os.path.join(os.path.dirname(__file__), "..")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from flask import Blueprint, Response, jsonify, request

from integrations.fmd_semantic_client import get_client
from integrations.dsl_change_consumer import get_consumer_status

api_v2 = Blueprint("api_v2", __name__, url_prefix="/api/v2")


# ── P3.2: 数据资源只读投影 ──

@api_v2.route("/data-resources")
def data_resources():
    """只读投影 FMD DSL 数据资源维度

    Invariant 1 守卫：只读，不写 truth
    """
    client = get_client()
    resources = client.list_data_resources()
    return jsonify({
        "success": True,
        "data": resources,
        "total": len(resources),
        "projection": client.get_projection_metadata(),
    })


@api_v2.route("/dsl-entries")
def dsl_entries():
    """只读投影 FMD DSL 全量条目

    Invariant 1 守卫：只读，不写 truth
    """
    client = get_client()
    entries = client.list_dsl_entries()
    return jsonify({
        "success": True,
        "data": entries,
        "total": len(entries),
        "projection": client.get_projection_metadata(),
    })


# ── Phase 3.2: DSL Change Consumer 状态 ──

@api_v2.route("/dsl-change-status")
def dsl_change_status():
    """返回 DSL Change Consumer 状态"""
    return jsonify({
        "success": True,
        "data": get_consumer_status(),
    })


@api_v2.route("/dsl-change/refresh", methods=["POST"])
def dsl_change_refresh():
    """手动触发缓存刷新"""
    client = get_client()
    client.invalidate_cache()
    return jsonify({
        "success": True,
        "message": "Cache invalidated. Next request will re-fetch from FMD.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── P3.1: AgentChat 流式 SSE ──

@api_v2.route("/agent/chat/stream")
def agent_chat_stream():
    """AgentChat 流式 SSE 端点

    对接 FMD semantic-query 获取上下文，流式返回响应。
    支持参数:
    - message: 用户消息
    - context: 上下文过滤（可选）

    GTD 层级：H0 执行（Agent full_participation）
    """
    message = request.args.get("message", "")
    context_filter = request.args.get("context", "")

    if not message:
        return jsonify({"success": False, "error": "message parameter required"}), 400

    def generate():
        # 1. 获取 FMD 语义上下文
        yield _sse_event("status", {"phase": "context_retrieval", "message": "Querying FMD semantic context..."})

        client = get_client()
        context_pack = {}
        try:
            context_pack = client.query_context_pack(
                query_params={"message": message, "context": context_filter}
            )
            yield _sse_event("context", {
                "source": "fmd-semantic-client",
                "data": context_pack,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            yield _sse_event("error", {"phase": "context_retrieval", "error": str(e)})

        # 2. 流式输出响应（token by token）
        yield _sse_event("status", {"phase": "streaming", "message": "Streaming response..."})

        # 构建响应文本（基于语义上下文）
        response_text = _build_response(message, context_pack)

        # 模拟 token 流（实际环境可对接 LLM streaming API）
        tokens = response_text.split()
        for i, token in enumerate(tokens):
            chunk = token + (" " if i < len(tokens) - 1 else "")
            yield _sse_event("token", {
                "content": chunk,
                "index": i,
                "total": len(tokens),
            })
            time.sleep(0.05)  # 流式延迟

        # 3. 完成
        yield _sse_event("done", {
            "total_tokens": len(tokens),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _sse_event(event_type, data):
    """格式化 SSE 事件"""
    return f"event: {event_type}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"


def _build_response(message, context):
    """基于 FMD 语义上下文构建响应文本

    在实际环境中，这里可以对接 LLM API（如 OpenAI/Claude/Xiaomi MiMo）。
    当前实现：基于上下文生成结构化响应。
    """
    lines = [
        f"Received message: {message}",
        "",
        "Semantic context from FMD:",
    ]

    if isinstance(context, dict):
        if "error" in context:
            lines.append(f"  [FMD context unavailable: {context.get('error')}]")
        else:
            # 提取上下文摘要
            entries = context.get("entries", context.get("data", []))
            if isinstance(entries, list) and entries:
                lines.append(f"  Found {len(entries)} relevant DSL entries:")
                for entry in entries[:5]:
                    if isinstance(entry, dict):
                        eid = entry.get("id", entry.get("entryId", "unknown"))
                        title = entry.get("title", "")
                        lines.append(f"    - {eid}: {title}")
            else:
                lines.append("  No specific entries found in context.")
    else:
        lines.append("  Context format not recognized.")

    lines.extend([
        "",
        "This response was generated using FMD semantic projection.",
        "Invariant 1 guard: this is a read-only projection, no truth was modified.",
    ])

    return "\n".join(lines)
