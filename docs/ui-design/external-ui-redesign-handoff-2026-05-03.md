# External UI Redesign — Handoff Package

> 日期: 2026-05-03  
> 类型: 对外 UI 评估交接包  
> 仓库: `CrazyAgentsManage`（feat/auto-capture-trace）  
> 基于: 2026-05-03 live 复验结果（timeline + handoff 两消费面均已稳定）

---

## 1. 当前一级 IA（6 页）

| 路由 | 页面标题 | PRD 规格 | Live 状态 |
|---|---|---|---|
| `/overview` | 总览 | [overview-page-prd.md](../prd/pages/overview-page-prd.md) | ✅ 200，可访问 |
| `/runtime` | 运行态 | [runtime-page-prd.md](../prd/pages/runtime-page-prd.md) | ✅ 200，可访问 |
| `/operations` | 运营面 | [operations-page-prd.md](../prd/pages/operations-page-prd.md) | ✅ 200，可访问 |
| `/governance` | 治理面 | [governance-page-prd.md](../prd/pages/governance-page-prd.md) | ✅ 200，可访问 |
| `/collaboration` | 协作面 | [collaboration-page-prd.md](../prd/pages/collaboration-page-prd.md) | ✅ 200，可访问 |
| `/timeline` | 承诺时序图 | 动态页面，数据来自 FlowMind trace | ✅ 200，真实 traceEvents[] 数据 |

---

## 2. 数据消费面（已验证）

### 2.1 Timeline 面

```
Crazy /api/promise-review/trace/:candidateId
  → FlowMind GET /api/bridge/trace/:candidateId
  → 新契约: semanticContext + traceEvents[]
```

| 字段 | 状态 | 示例值 |
|---|---|---|
| `traceEvents[]` | ✅ | 7 条事件（create/clarify/confirm/approve/update） |
| `semanticContext` | ✅ | entries + fieldMappings + consumerHints |
| `module` 归一化 | ✅ | candidate-ingress, review, truth, bridge, feedback（无 unknown） |
| 验证 candidateId | `219a5914-6c85-43df-ad5e-1d1d36241b39` | C-1 承诺审查改造完成（approved） |

### 2.2 Handoff 面

```
Crazy /api/flowmind/records/:recordId/replay
  → FlowMind GET /api/operator/records/:recordId/replay
  → moduleDetails.handoff（sections 结构）
```

| 字段 | 状态 |
|---|---|
| Truth Status | ✅ approved |
| Latest Evidence Summary | ✅ 已填充 |
| Latest Evidence Class | ✅ EXTRACTED |
| Latest Evidence Source Type | ✅ OPERATOR_ACCEPTANCE |
| Latest Evidence Refs | ✅ bitable + timeline |
| Semantic Refs | ✅ 6 个语义引用 |
| Trace Events | ✅ 7 |
| Latest Trace Action | ✅ update |
| Latest Trace Summary | ✅ 已填充 |
| Consumer Hints | ✅ 7 条 |

---

## 3. 当前技术栈

| 层 | 技术 |
|---|---|
| 前端 | Flask Jinja2 模板 + 原生 HTML/CSS/JS |
| 后端 | Flask (Python 3) |
| 数据上游 | FlowMind REST API（`111.229.194.203:3301`） |
| 部署 | `/opt/crazyagentsmanage`（cam_launcher 管理） |
| 设计系统 | 暗色主题，Inter 字体，Vercel Workflow 风格 |

---

## 4. 已知缺口（供 UI 团队评估参考）

| 缺口 | 分类 | 说明 |
|---|---|---|
| 页面以 Jinja2 模板平铺为主 | 架构 | 各页面独立模板，共享组件较少；无前端框架 |
| 无客户端路由 | 架构 | 每次导航刷新整页 |
| traceNodeCount=0 | 数据 | replay 的 steps 为 derived 模式，非 trace graph |
| webui README 与当前 IA 不同步 | 文档 | README 仍描述旧 5 页模型（Dashboard/Tasks/Team Memory/Cron/Skills） |
| 无 WebSocket/SSE 实时更新 | 功能 | 数据为静态渲染，无实时推送 |
| 响应式已实现 | ✅ | 三断点 480/768/1024 |
| 无障碍已覆盖 | ✅ | labels + focus + reduced-motion |

---

## 5. 评估建议方向

1. **IA 评价**: 当前 6 页 + 1 动态页（timeline）的一级 IA 是否清晰
2. **数据消费面**: timeline（traceEvents[]）和 handoff（moduleDetails.handoff）是否可作为 UI 的数据合同
3. **页面分工**: overview/runtime/operations/governance/collaboration 的职责划分是否合理
4. **重设计范围**: 是否需要框架化（React/Vue）、是否需要组件库、是否需要客户端路由
5. **旧页面残留**: 是否存在需要清理的旧模板/路由
