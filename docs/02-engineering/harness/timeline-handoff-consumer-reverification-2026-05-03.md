# 真实 Round 复验：Timeline / Handoff 新消费面（FlowMind Live Upstream 已修复）

> 日期: 2026-05-03  
> 类型: 运营复验 — 确认 live upstream 修复后两条消费面可用性  
> 仓库视角: `CrazyAgentsManage`  
> 分支: `feat/auto-capture-trace`  
> 前置验收: [timeline-handoff-consumer-verification-2026-05-03.md](./timeline-handoff-consumer-verification-2026-05-03.md)

---

## 1. 验证对象

| 字段 | 值 |
|---|---|
| candidateId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| recordId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| 标题 | C-1 承诺审查改造完成 |
| 状态 | `approved` |
| 实例 | `hermes-agent` |

---

## 2. Timeline 面复验

### 2.1 数据链路（已确认）

```
Crazy /api/promise-review/trace/:candidateId
  → FlowMind GET /api/bridge/trace/:candidateId
  → 新契约: data.semanticContext + data.traceEvents[]
```

### 2.2 新契约验证

| 检查项 | 上次（阻塞） | 本次（复验） |
|---|---|---|
| 数据源来自 `/bridge/trace` | ✅ 是 | ✅ 是 |
| 返回 `semanticContext` | ❌ 不存在 | ✅ 存在（entries + fieldMappings + consumerHints） |
| 返回 `traceEvents[]` | ❌ 走旧 `events[]` | ✅ 新契约 `traceEvents[]`（7 条） |
| 旧 `events[]` 残留 | ✅ 已在 fallback 路径 | ✅ 上游已移除 |
| module 归一化 | ❌ 全是 `unknown` | ✅ `candidate-ingress`, `review`, `truth`, `bridge`, `feedback` |
| candidateStatus | ❌ 不存在 | ✅ `approved` |
| traceCount | ✅ 7 | ✅ 7 |

### 2.3 页面展示验证（Crazy webui 实际返回）

| 事件 | action | module | fromStatus | toStatus | summary |
|---|---|---|---|---|---|
| 1 | create | candidate-ingress | — | draft | Ingress from openclaw |
| 2 | clarify | review | draft | draft | Human decision: clarify |
| 3 | confirm | review | draft | submitted | Human decision: confirm |
| 4 | approve | truth | submitted | approved | Status transition |
| 5 | update | bridge | approved | approved | Candidate status changed |
| 6 | update | bridge | — | approved | 运营验收已确认 |
| 7 | update | feedback | — | approved | Bitable 主表与时序图可用 |

### 2.4 Timeline 结论

> ✅ **已稳定消费 `traceEvents[]`。不再依赖旧 `events[]`。module 已恢复归一化，无 `unknown`。**

---

## 3. Handoff 面复验

### 3.1 数据链路（已确认）

```
Crazy /api/flowmind/records/:recordId/replay
  → FlowMind GET /api/operator/records/:recordId/replay
  → moduleDetails.handoff（sections 结构）
```

### 3.2 moduleDetails.handoff 字段逐项验证

| 期望字段 | 上次（阻塞） | 本次（复验） | 值 |
|---|---|---|---|
| Truth Status | ❌ | ✅ | `approved` |
| Latest Evidence Summary | ❌ | ✅ | "Crazy 验收已确认 Bitable 主表与时序图页面可用" |
| Latest Evidence Class | ❌ | ✅ | `EXTRACTED` |
| Latest Evidence Source Type | ❌ | ✅ | `OPERATOR_ACCEPTANCE` |
| Latest Evidence Refs | ❌ | ✅ | `bitable:EpeXbhpF9a0s0wsh6axce9PknFg, timeline:...` |
| Semantic Refs | ❌ | ✅ | 6 个语义引用 |
| Trace Events | ❌ | ✅ | `7` |
| Latest Trace Action | ❌ | ✅ | `update` |
| Latest Trace Summary | ❌ | ✅ | "Crazy 验收已确认 Bitable 主表与时序图页面可用" |
| Consumer Hints | ❌ | ✅ | 7 条消费提示 |

### 3.3 Handoff 结论

> ✅ **已稳定消费 `moduleDetails.handoff`。10/10 必需字段全部填充。不再需要以"上游没给 handoff"为理由退回手工拼摘要。**

---

## 4. 仍未关闭的真实缺口

| 缺口 | 分类 | 影响 | 阻塞切换？ |
|---|---|---|---|
| replay `mode` = `derived` | 实现缺口 | steps 从 candidate 元数据推导，非 trace graph | ❌ 不阻塞 handoff 消费 |
| `traceNodeCount` = 0 | 实现缺口 | trace graph 未为该 record 填充节点 | ❌ 不阻塞（traceEvents 在 timeline 面已可用） |
| "Current public API does not yet expose Hermes ingress trace nodes" | 已知限制 | operator/replay 的 steps 仍是 derived | ❌ 已在 gaps 中声明 |
| 无独立的 `/handoff` 端点 | 设计选择 | handoff 嵌套在 replay 中，非独立路由 | ❌ 不影响功能 |
| Crazy webui 部署路径 `/opt/crazyagentsmanage` 未纳入 git 管理 | 运维缺口 | 需手动同步 api.py（本次已修复） | ⚠️ 应纳入自动化部署 |

---

## 5. 验收结论

> ✅ **可切换为默认流程。**
>
> **Timeline** 已稳定消费 FlowMind 新契约 `traceEvents[]`，module 归一化完成。
> **Handoff** 已稳定消费 `moduleDetails.handoff`，10/10 字段全部可用。
> Crazy 运营侧现在可以把默认 handoff 路径正式切到 live replay 的 `moduleDetails.handoff`，
> 不再需要以 `generate_hermes_handoff.py` 作为唯一 handoff 入口。
>
> 剩余 `traceNodeCount=0` 和 `mode=derived` 属于 trace graph 填充的渐进工作，不阻塞当前运营流程切换。
>
> ⚠️ **附带发现**：Crazy webui 实际部署路径为 `/opt/crazyagentsmanage/`，
> 与开发仓库 `/root/CrazyAgentsManage/` 不同步，需建立自动部署或同步机制。
