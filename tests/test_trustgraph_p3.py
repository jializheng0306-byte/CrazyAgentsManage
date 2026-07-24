#!/usr/bin/env python3
"""
Tests for TrustGraph P3 + Phase 3 CAM side

验证：
- P3.2: 数据资源只读投影端点
- Phase 3.2: DSL Change Consumer 状态端点
- P3.1: AgentChat 流式 SSE 端点
- Invariant 1 守卫：只读投影，不写 truth

@see plan: 08-trustgraph-absorption-implementation-plan.md P3 + Phase 3
"""

import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def app():
    """Create Flask app with v2 blueprint"""
    from flask import Flask
    from webui.api_v2 import api_v2
    app = Flask(__name__)
    app.register_blueprint(api_v2)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _mock_client():
    """Create a mock FmdSemanticClient"""
    mc = MagicMock()
    mc.list_data_resources.return_value = []
    mc.list_dsl_entries.return_value = []
    mc.query_context_pack.return_value = {"entries": []}
    mc.get_projection_metadata.return_value = {"source": "test"}
    mc.invalidate_cache = MagicMock()
    return mc


# ── P3.2: Data Resources Projection ──

class TestDataResources:
    """P3.2: 数据资源只读投影"""

    def test_data_resources_endpoint_returns_200(self, client):
        """GET /api/v2/data-resources 返回 200"""
        with patch("webui.api_v2.get_client", return_value=_mock_client()):
            resp = client.get("/api/v2/data-resources")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert "data" in data
            assert "total" in data
            assert "projection" in data

    def test_data_resources_returns_list(self, client):
        """数据资源端点返回列表"""
        mc = _mock_client()
        mc.list_data_resources.return_value = [
            {"id": "flowmind.data_layer", "kind": "object", "title": "Data Layer"},
        ]
        with patch("webui.api_v2.get_client", return_value=mc):
            resp = client.get("/api/v2/data-resources")
            data = resp.get_json()
            assert data["total"] == 1
            assert data["data"][0]["id"] == "flowmind.data_layer"

    def test_dsl_entries_endpoint(self, client):
        """GET /api/v2/dsl-entries 返回 DSL 条目"""
        mc = _mock_client()
        mc.list_dsl_entries.return_value = [
            {"id": "test.entry", "kind": "concept"},
        ]
        with patch("webui.api_v2.get_client", return_value=mc):
            resp = client.get("/api/v2/dsl-entries")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["total"] == 1
            assert data["data"][0]["id"] == "test.entry"


# ── Phase 3.2: DSL Change Consumer ──

class TestDslChangeConsumer:
    """Phase 3.2: DSL Change Consumer 状态"""

    def test_dsl_change_status_endpoint(self, client):
        """GET /api/v2/dsl-change-status 返回 Consumer 状态"""
        with patch("webui.api_v2.get_consumer_status", return_value={
            "queue_id": "flow:fmd:dsl-changed",
            "backend": "memory",
            "poll_interval": 60,
            "polling_active": True,
        }):
            resp = client.get("/api/v2/dsl-change-status")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["data"]["queue_id"] == "flow:fmd:dsl-changed"

    def test_dsl_change_refresh_endpoint(self, client):
        """POST /api/v2/dsl-change/refresh 手动触发缓存刷新"""
        mc = _mock_client()
        with patch("webui.api_v2.get_client", return_value=mc):
            resp = client.post("/api/v2/dsl-change/refresh")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert "Cache invalidated" in data["message"]
            mc.invalidate_cache.assert_called_once()


# ── P3.1: AgentChat Streaming ──

class TestAgentChatStream:
    """P3.1: AgentChat 流式 SSE"""

    def test_stream_requires_message(self, client):
        """缺少 message 参数返回 400"""
        resp = client.get("/api/v2/agent/chat/stream")
        assert resp.status_code == 400

    def test_stream_returns_sse(self, client):
        """SSE 端点返回 text/event-stream"""
        mc = _mock_client()
        mc.query_context_pack.return_value = {"entries": []}
        with patch("webui.api_v2.get_client", return_value=mc):
            resp = client.get("/api/v2/agent/chat/stream?message=hello")
            assert resp.status_code == 200
            assert "text/event-stream" in resp.content_type

            # 解析 SSE 事件
            lines = resp.data.decode("utf-8").split("\n")
            event_types = [l[7:] for l in lines if l.startswith("event: ")]
            assert "status" in event_types
            assert "context" in event_types
            assert "token" in event_types
            assert "done" in event_types

    def test_stream_contains_tokens(self, client):
        """SSE 流包含 token 事件"""
        mc = _mock_client()
        mc.query_context_pack.return_value = {"entries": [{"id": "test"}]}
        with patch("webui.api_v2.get_client", return_value=mc):
            resp = client.get("/api/v2/agent/chat/stream?message=test")
            data = resp.data.decode("utf-8")

            # 应包含 token 事件
            assert "event: token" in data
            # 应包含 done 事件
            assert "event: done" in data

    def test_stream_context_retrieval(self, client):
        """SSE 流先获取 FMD 上下文"""
        mc = _mock_client()
        mc.query_context_pack.return_value = {"entries": [{"id": "test.entry"}]}
        with patch("webui.api_v2.get_client", return_value=mc):
            resp = client.get("/api/v2/agent/chat/stream?message=hello")
            _ = resp.data  # Force generator consumption
            mc.query_context_pack.assert_called_once()


# ── Invariant 1 守卫 ──

class TestInvariantGuards:
    """Invariant 1 守卫：只读投影，不写 truth"""

    def test_data_resources_is_readonly(self, client):
        """数据资源端点不提供写入方法"""
        with patch("webui.api_v2.get_client", return_value=_mock_client()):
            # POST 应该不允许（只读）
            resp = client.post("/api/v2/data-resources")
            assert resp.status_code == 405  # Method Not Allowed

    def test_dsl_entries_is_readonly(self, client):
        """DSL 条目端点不提供写入方法"""
        with patch("webui.api_v2.get_client", return_value=_mock_client()):
            resp = client.post("/api/v2/dsl-entries")
            assert resp.status_code == 405  # Method Not Allowed

    def test_fmd_semantic_client_no_write_methods(self):
        """FmdSemanticClient 不暴露 truth 写入方法"""
        from integrations.fmd_semantic_client import FmdSemanticClient
        client = FmdSemanticClient()
        # Invariant 1 守卫：不暴露 writeTruth / setTruthStatus / promoteTruth
        assert not hasattr(client, "write_truth")
        assert not hasattr(client, "set_truth_status")
        assert not hasattr(client, "promote_truth")
        assert not hasattr(client, "writeTruth")
        assert not hasattr(client, "setTruthStatus")
