#!/usr/bin/env python3
"""
FMD Semantic Client — 只读投影 FMD DSL 语义数据

通过 FMD mcp-server 的 HTTP API 查询 DSL 条目，提供只读投影供 CAM 消费。
支持 TTL 缓存，可被 DslChangeConsumer 主动失效。

GTD 层级判定：H0-H2（基础设施，无意义赋予）
Invariant 1 守卫：只读投影，不写 truth

@see plan: 08-trustgraph-absorption-implementation-plan.md P3.2
"""

import json
import os
import threading
import time
from datetime import datetime, timezone
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

FLOWMIND_URL = os.getenv("FLOWMIND_URL", "http://localhost:3001")
FLOWMIND_TOKEN = os.getenv("FLOWMIND_TOKEN", "flowmind-dev-token")
FMD_DSL_ROOT = os.getenv("FMD_DSL_ROOT", "")  # FMD DSL 文件系统路径（本地直读回退）

_DEFAULT_TTL = 60  # 默认缓存 TTL（秒）

_lock = threading.Lock()
_cache = {}  # key -> {"data": ..., "expires_at": float}


def _make_request(url, payload=None, method="GET", timeout=10):
    """发起 HTTP 请求到 FMD"""
    headers = {
        "Authorization": f"Bearer {FLOWMIND_TOKEN}",
        "Content-Type": "application/json",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers=headers, method=method)
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _read_dsl_from_filesystem():
    """从 FMD 文件系统直接读取 DSL 条目（本地回退方案）。

    当 FMD HTTP API 不可用时，直接读取 DSL markdown 文件的 frontmatter。
    """
    if not FMD_DSL_ROOT or not os.path.isdir(FMD_DSL_ROOT):
        return []

    entries = []
    for root, _dirs, files in os.walk(FMD_DSL_ROOT):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                # 解析 frontmatter
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        frontmatter = content[3:end].strip()
                        entry = _parse_frontmatter(frontmatter, fpath)
                        if entry:
                            entries.append(entry)
            except Exception:
                continue
    return entries


def _parse_frontmatter(text, filepath):
    """简单解析 YAML frontmatter 为字典"""
    entry = {"_source_file": filepath}
    for line in text.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if key and val:
                entry[key] = val
    return entry if "id" in entry else None


class FmdSemanticClient:
    """FMD DSL 只读投影客户端

    提供 TTL 缓存，可被 DslChangeConsumer 主动失效。
    """

    def __init__(self, ttl=_DEFAULT_TTL):
        self.ttl = ttl
        self._base_url = FLOWMIND_URL.rstrip("/")

    def _get_cached(self, key):
        """从缓存获取数据，过期返回 None"""
        with _lock:
            item = _cache.get(key)
            if item and item["expires_at"] > time.time():
                return item["data"]
        return None

    def _set_cached(self, key, data):
        """写入缓存"""
        with _lock:
            _cache[key] = {
                "data": data,
                "expires_at": time.time() + self.ttl,
            }

    def invalidate_cache(self):
        """主动失效所有缓存（由 DslChangeConsumer 调用）"""
        with _lock:
            _cache.clear()

    def query_context_pack(self, candidate_id=None, query_params=None):
        """查询 FMD bridge context-pack（含语义上下文）"""
        cache_key = "context_pack"
        if candidate_id:
            cache_key += f":{candidate_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        url = f"{self._base_url}/api/bridge/context-pack"
        payload = {}
        if candidate_id:
            payload["candidateId"] = candidate_id
        if query_params:
            payload.update(query_params)

        try:
            result = _make_request(url, payload=payload, method="POST")
            self._set_cached(cache_key, result)
            return result
        except (urlerror.URLError, OSError, json.JSONDecodeError):
            return {"error": "FMD context-pack unavailable", "status": "failed"}

    def list_data_resources(self):
        """查询 FMD DSL 数据资源维度（只读投影）

        优先通过 FMD HTTP API 查询，回退到文件系统直读。
        """
        cache_key = "data_resources"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # 方案 1：通过 FMD bridge API 查询
        try:
            result = _make_request(
                f"{self._base_url}/api/bridge/context-pack",
                payload={"dimension": "data_resources"},
                method="POST",
            )
            if "error" not in result:
                # 过滤出数据资源相关条目
                entries = result.get("entries", result.get("data", []))
                if isinstance(entries, list):
                    data_resources = [
                        e for e in entries
                        if "resource" in str(e).lower()
                        or "data" in str(e.get("kind", "")).lower()
                    ]
                    self._set_cached(cache_key, data_resources)
                    return data_resources
        except (urlerror.URLError, OSError, json.JSONDecodeError):
            pass

        # 方案 2：从文件系统直读 DSL
        entries = _read_dsl_from_filesystem()
        data_resources = [
            e for e in entries
            if "resource" in str(e).lower()
            or "data" in str(e.get("kind", "")).lower()
        ]
        self._set_cached(cache_key, data_resources)
        return data_resources

    def list_dsl_entries(self):
        """列出所有 DSL 条目（只读投影）"""
        cache_key = "dsl_entries"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # 从文件系统直读
        entries = _read_dsl_from_filesystem()
        self._set_cached(cache_key, entries)
        return entries

    def get_projection_metadata(self):
        """返回投影元数据（来源、更新时间、条目数）"""
        return {
            "source": "fmd-semantic-client",
            "fmd_url": self._base_url,
            "ttl_seconds": self.ttl,
            "projected_at": datetime.now(timezone.utc).isoformat(),
            "cache_entries": len(_cache),
        }


# 全局单例
_client = None
_client_lock = threading.Lock()


def get_client():
    """获取全局 FmdSemanticClient 单例"""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = FmdSemanticClient()
    return _client
