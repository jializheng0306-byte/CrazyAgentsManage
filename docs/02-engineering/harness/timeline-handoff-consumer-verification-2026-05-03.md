# 真实 Round 验证：Timeline / Handoff 新消费面

> 日期: 2026-05-03  
> 类型: 运营验收 — 新消费面真实验证  
> 仓库视角: `CrazyAgentsManage`  
> 分支: `feat/auto-capture-trace`

---

## 1. 验证对象

| 字段 | 值 |
|---|---|
| candidateId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| recordId | `219a5914-6c85-43df-ad5e-1d1d36241b39`（同 candidateId） |
| 标题 | C-1 承诺审查改造完成 |
| 状态 | `approved` |
| 实例 | `hermes-agent` |

---

## 2. Timeline 面验证

### 2.1 数据链路

```
Crazy /api/promise-review/trace/:candidateId
  → FlowMind /api/bridge/trace/:candidateId
  → _normalize_bridge_trace() 归一化
```

### 2.2 验证结果

| 检查项 | 结果 |
|---|---|
| 页面数据是否来自 `/bridge/trace/:candidateId` | ✅ **是** — upstream 字段确认为 `http://111.229.194.203:3301` |
| 动作顺序 | ✅ 按时间排序（create → status_change → update） |
| 状态变化 | ✅ fromStatus/toStatus 穿插在事件中 |
| 模块归属 | ⚠️ 所有事件 `module: "unknown"` — FlowMind trace 端 module 字段未填充 |
| 时间戳 | ✅ 7 events 全部带 ISO 时间戳 |
| 摘要 | ✅ summary 字段有实际内容 |
| traceCount | ✅ 7 |
| 是否有"自己重排事件"痕迹 | ❌ **无** — 数据完全来自 FlowMind |
| 是否有"自己猜 action 类型"痕迹 | ❌ **无** — action/actor 字段来自上游 |

### 2.3 Timeline 结论

> ✅ **Timeline 已成功切换到新上游。**  
> 仅剩一个数据缺口：所有 trace events 的 `module` 字段为 `"unknown"`，  
> FlowMind 侧需要为 `/bridge/trace` 的事件填充正确的 module 归属。

---

## 3. Handoff 面验证

### 3.1 数据链路（当前实际路径）

```
Crazy /api/flowmind/records/:id/replay
  → 尝试 FlowMind /api/operator/records/:id/replay（可达，但 mode=derived）
  → 尝试 /api/trace/query/proposal/:id（返回空 nodes）
  → 回退到 _build_derived_replay() 推导模式
```

### 3.2 FlowMind operator/replay 端点分析

| 字段 | 值 |
|---|---|
| 端点 | `GET /api/operator/records/:id/replay` |
| HTTP 状态 | 200 |
| mode | `derived` |
| traceNodeCount | `0` |
| provenanceCount | `7` |
| **moduleDetails** | **`{}`（空对象）** |
| **moduleDetails.handoff** | ❌ **不存在** |
| latestEvidence in response | ❌ 不存在 |
| semanticContext in response | ❌ 不存在 |

### 3.3 缺失字段清单（期望 vs 实际）

| 期望字段 | 实际状态 |
|---|---|
| Truth Status | ❌ 不在 operator/replay 响应中（truth read 单独可查） |
| Latest Evidence Summary | ❌ 不在 operator/replay 响应中 |
| Latest Evidence Class | ❌ 不在 |
| Latest Evidence Source Type | ❌ 不在 |
| Latest Evidence Refs | ❌ 不在 |
| Semantic Refs | ❌ 不在 |
| Trace Events | ⚠️ traceNodeCount=0 |
| Latest Trace Action | ❌ 不在 |
| Latest Trace Summary | ❌ 不在 |
| Consumer Hints | ❌ 不在 |
| **moduleDetails.handoff** | ❌ **不存在** |

### 3.4 Handoff 结论

> ❌ **moduleDetails.handoff 尚未接线。**  
> FlowMind 的 `/api/operator/records/:id/replay` 端点已部署但 `moduleDetails` 为空，  
> 没有返回 handoff 相关的任何字段。  
> Crazy 的 replay 面因此回退到 `derived` 模式（从 candidate 元数据推导步骤），  
> 而不是从 `moduleDetails.handoff` 读取运营摘要。

---

## 4. Crazy Runtime Handoff 面

| 端点 | `/api/runtime/handoffs` |
|---|---|
| 数据来源 | `.omx/crazyagents/outbox/*.md`（本地文件） |
| 当前状态 | 空（无本地 handoff 文件） |
| 是否消费 moduleDetails.handoff | ❌ **否** — 这是独立的本地文件读取 |

---

## 5. 剩余缺口汇总

| 缺口 | 分类 | 影响 |
|---|---|---|
| FlowMind trace events 的 module 字段 = "unknown" | **数据缺口** | Timeline 无法按模块分组 |
| FlowMind operator/replay 的 moduleDetails 为空 | **实现缺口** | Handoff 摘要无法从新面消费 |
| moduleDetails.handoff 不存在 | **实现缺口** | 运营团队仍需从别处获取 handoff 信息 |
| latestEvidence / semanticContext 未进入 replay | **接线缺口** | 这些数据在 truth read 中有，但未透传到 replay |
| traceNodeCount = 0 | **实现缺口** | trace graph 未填充，replay 回退 derived |

---

## 6. 运营结论

> **Timeline 面可切换为默认流程 ✅，Handoff 面仍有阻塞 ❌。**  
> 
> Timeline 已成功消费 `/bridge/trace/:candidateId`，不再手工拼接。  
> Handoff 面（`moduleDetails.handoff`）尚未在 FlowMind 侧落地，  
> 运营团队目前还不能从该面获取 Truth Status + Evidence + Trace 的整合摘要。  
> 在 moduleDetails.handoff 接线完成前，推荐继续使用 `generate_hermes_handoff.py`  
> 从 truth read surface 生成 handoff packet 作为过渡方案。
