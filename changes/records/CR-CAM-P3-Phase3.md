# CR-CAM-P3-Phase3: TrustGraph P3 + Phase 3 (CAM 侧 AgentChat 流式 + 数据资源治理 + 跨仓消费)

**Date**: 2026-07-24
**Phase**: TrustGraph 能力吸收 P3 调整 + Phase 3（CAM 侧）
**Branch**: `feat/trustgraph-p3-streaming`（基于 `main`）
**方法论依据**: [07-methodology-relation-gtd-talisman-trustgraph.md](file:///D:/bkn_docs/07-methodology-relation-gtd-talisman-trustgraph.md)
**实施方案**: [08-trustgraph-absorption-implementation-plan.md](file:///D:/bkn_docs/08-trustgraph-absorption-implementation-plan.md) P3 + Phase 3
**复杂度**: L3（多文件跨层改动，无语义契约变更）

## 变更概述

实现 TrustGraph 能力吸收 P3 调整 + Phase 3 的 CAM 侧：
- **P3.1 AgentChat 流式**：`/api/v2/agent/chat/stream` SSE 端点，对接 FMD semantic-query 获取上下文，流式 token 输出
- **P3.2 数据资源治理**：`/api/v2/data-resources` + `/api/v2/dsl-entries` 只读投影 FMD DSL
- **Phase 3.2 跨仓消费**：`DslChangeConsumer` 消费 `flow:fmd:dsl-changed` 事件刷新投影缓存（Pulsar + 轮询双轨）

## GTD 层级判定

| 组件 | GTD 层级 | 守卫 |
|------|---------|------|
| AgentChat 流式 | H0（执行，Agent full_participation） | Invariant 1（不写 truth） |
| 数据资源治理 | H0-H2（基础设施，无意义赋予） | Invariant 1（只读投影） |
| DSL Change Consumer | H2（系统维护） | Invariant 1（只刷新缓存） |

## 变更内容

### 新增文件

1. `src/integrations/fmd_semantic_client.py` — FMD DSL 只读投影客户端
   - TTL 缓存（60s 默认），可被 DslChangeConsumer 主动失效
   - `list_data_resources()` — 查询数据资源维度
   - `list_dsl_entries()` — 查询全量 DSL 条目
   - `query_context_pack()` — 查询 FMD bridge context-pack
   - 支持文件系统直读回退（当 FMD HTTP API 不可用时）

2. `src/integrations/dsl_change_consumer.py` — DSL 变更消费者
   - 双轨策略：Pulsar 消费（如果可用）+ 轮询回退（默认）
   - `start_consumer()` / `stop_consumer()` — 生命周期管理
   - `get_consumer_status()` — 状态查询
   - Invariant 1 守卫：只刷新缓存，不写 truth

3. `src/webui/api_v2.py` — v2 API Blueprint
   - `GET /api/v2/data-resources` — 数据资源只读投影
   - `GET /api/v2/dsl-entries` — DSL 条目只读投影
   - `GET /api/v2/dsl-change-status` — Consumer 状态
   - `POST /api/v2/dsl-change/refresh` — 手动缓存刷新
   - `GET /api/v2/agent/chat/stream` — AgentChat SSE 流式

4. `src/integrations/__init__.py` — integrations 包初始化

5. `tests/test_trustgraph_p3.py` — 12 个测试
   - P3.2: 数据资源端点 / DSL 条目端点
   - Phase 3.2: Consumer 状态 / 缓存刷新
   - P3.1: SSE 流式 / token 事件 / 上下文获取
   - Invariant 1 守卫: 只读端点不提供 POST / Client 不暴露 truth 写入方法

### 修改文件

6. `src/webui/app.py` — 注册 v2 Blueprint（+2 行）

## 守卫验证

- ✅ Invariant 1：数据资源/DSL 条目端点只读（POST 返回 405）
- ✅ Invariant 1：FmdSemanticClient 不暴露 writeTruth/setTruthStatus/promoteTruth
- ✅ Invariant 1：DslChangeConsumer 只刷新缓存，不写 truth
- ✅ SSE 事件 payload 不含 truth/status 裁定字段

## 验证标准

- [x] `python3 -m pytest tests/test_trustgraph_p3.py` ✅（12 tests passed）
- [x] P3.1 AgentChat SSE 端点正确返回 text/event-stream
- [x] P3.2 数据资源只读投影正确返回
- [x] Phase 3.2 Consumer 状态端点正确返回
- [x] Invariant 1 守卫测试通过

## 下游依赖

- FMD Phase 3.1 `DslChangeEmitter`（PR #58）— 事件源
- FMD semantic-query API — 只读投影数据源

## 参考

- TrustGraph streaming-llm-responses（SSE 模式参考）
- TrustGraph PubSubBackend（Pulsar 消费模式参考）
- CAM dashboard/stream（现有 SSE 模式参考）
