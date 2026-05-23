# CrazyAgentsManage WebUI 路由与模板对齐文档

## 文档目的

本文档用于把当前 `src/webui/app.py` 与 `src/webui/templates/` 的实际路由/模板结构，对齐到新的一级 IA 与页面级 PRD 体系。

## 当前实际路由

来自 `src/webui/app.py`：

- `/` -> `home.html`
- `/agent` -> `agent.html`
- `/graph` -> `graph.html`
- `/alerts` -> `alerts.html`
- `/tokens` -> `tokens.html`
- `/sessions` -> `sessions.html`
- `/dashboard` -> `dashboard.html`
- `/tasks` -> `tasks.html`
- `/team-memory` -> `team-memory.html`
- `/cron` -> `cron.html`
- `/skills` -> `skills.html`
- `/overview` -> `overview.html`
- `/runtime` -> `runtime.html`
- `/runtime/sessions` -> `sessions.html`
- `/runtime/dashboard` -> `dashboard.html`
- `/runtime/tokens` -> `tokens.html`
- `/runtime/agents` -> `agent.html`
- `/operations` -> `operations.html`
- `/operations/skills` -> `skills.html`
- `/operations/cron` -> `cron.html`
- `/operations/team-memory` -> `team-memory.html`
- `/operations/alerts` -> `alerts.html`
- `/operations/timeline` -> `timeline.html`
- `/governance` -> `governance.html`
- `/governance/graph` -> `graph.html`
- `/collaboration` -> `collaboration.html`
- `/collaboration/tasks` -> `tasks.html`
- `/collaboration/loops` -> `loop-surface.html`
- `/architecture/philosophy` -> `architecture-philosophy.html`
- `/architecture/product` -> `architecture-product.html`
- `/architecture/tech` -> `architecture-tech.html`

## 当前模板集合

来自 `src/webui/templates/`：

- `agent.html`
- `alerts.html`
- `cron.html`
- `dashboard.html`
- `graph.html`
- `home.html`
- `governance.html`
- `collaboration.html`
- `loop-surface.html`
- `operations.html`
- `overview.html`
- `runtime.html`
- `sessions.html`
- `skills.html`
- `tasks.html`
- `team-memory.html`
- `timeline.html`
- `tokens.html`
- `architecture-philosophy.html`
- `architecture-product.html`
- `architecture-tech.html`

## 目标 IA

一级 IA：

- `Overview`
- `Runtime`
- `Operations`
- `Governance`
- `Collaboration`

以及一组架构可视化页面：

- `ProductPhilosophyPreviewPage`
- `ProductArchitecturePreviewPage`
- `TechArchitecturePreviewPage`

## 对齐映射

### `Overview`

现有可复用模板：

- `home.html`
- `overview.html`

建议：

- `home.html` 逐步退化为历史入口或导航壳
- `overview.html` 成为规范性的 `Overview` 主页面

### `Runtime`

现有可复用模板：

- `sessions.html`
- `dashboard.html`
- `tokens.html`
- `agent.html`

建议：

- `sessions.html` 作为 Runtime 主页面基础
- `dashboard.html` 吸收到 Runtime 的 trace / metrics 子表面
- `tokens.html` 与 `agent.html` 逐步并入 Runtime 详情体系

### `Operations`

现有可复用模板：

- `skills.html`
- `cron.html`
- `team-memory.html`
- `alerts.html`

建议：

- `skills.html`、`cron.html`、`team-memory.html` 继续保留为 Operations 子表面
- `alerts.html` 作为 Operations / Overview 共享异常入口

### `Governance`

当前状态：

- 已有 `governance.html` 作为治理一级分区模板
- `graph.html` 继续作为治理图谱子表面

建议：

- `governance.html` 继续承担一级治理入口
- `graph.html` 保持为对象关系与治理图谱详情子表面
- 后续只补真实 candidate / truth / review / feedback / drift 数据源，不再把“缺主模板”当成问题

### `Collaboration`

当前状态：

- 已有 `collaboration.html` 作为协作一级分区模板
- `tasks.html` 继续作为协作主工作台子表面
- 已有 `loop-surface.html` 作为 Sprint 2 第一条 vertical slice 的协作子表面

建议：

- `collaboration.html` 继续承担交接对象池 / 支持证据 / 子表面分流入口
- `tasks.html` 继续作为协作执行工作台
- `Loop Surface` 当前已经作为 `Collaboration` 主入口下的子表面接入：
  - `/collaboration/loops`
  - 后续如需从 `Governance` 提供次入口，仍不单独升成一级 IA

### 架构可视化页

当前缺口：

- 3 个 `tsx` 预览入口未与 `src/webui/templates/` 现有结构打通

建议：

- 先在页面级 PRD 中固定其产品归属
- 后续选择：
  1. 作为独立前端路由引入
  2. 作为现有模板中的嵌入式画布

## 推荐的目标路由组

- `/overview`
- `/runtime`
- `/operations`
- `/governance`
- `/collaboration`

辅助/子路由：

- `/runtime/sessions`
- `/runtime/dashboard`
- `/operations/skills`
- `/operations/cron`
- `/operations/team-memory`
- `/collaboration/loops`

架构页建议路由：

- `/architecture/philosophy`
- `/architecture/product`
- `/architecture/tech`

## 当前差距

1. 旧功能页仍然保留原有平铺路由，但一级 IA 路由与主模板已经全部建立
2. 新增的 IA 页面仍有“聚合深度不足”的问题；当前缺口不再是“有没有模板”，而是“真实数据和行为是否全部接入”
3. `Loop Surface` 已接入真实路由/模板实现，并已承接 `promise-review-cycle` + `morning-intel-cycle` 两条 cycle 对象，以及本地 `feedback input / memory candidate` 最小写面；`Tasks` 已承接 `task bus + promotion gate` 的最小控制面，`Operations` 已承接 `executor capability plane`、`role / credential / memory isolation`、`task registry / automation / host health / runbooks`，并已把第二批 `env map / backup-recovery / recovery paths` 拉进产品面
4. 3 个架构页已接入当前 WebUI 路由体系，但仍是占位性接入，尚未挂载真实 TSX 展示实现

## 对齐原则

1. 先保证 IA 对齐，再做模板合并
2. 先保留旧模板名和旧路由，逐步增加新路由
3. 架构展示页必须接入真实状态源，不能停留在静态展示

## 已落地的过渡实现

当前 `src/webui/app.py` 已新增以下 IA 对齐路由：

- `/runtime`
- `/runtime/sessions`
- `/runtime/dashboard`
- `/runtime/tokens`
- `/runtime/agents`
- `/operations`
- `/operations/skills`
- `/operations/cron`
- `/operations/team-memory`
- `/operations/alerts`
- `/governance`
- `/governance/graph`
- `/collaboration`
- `/collaboration/tasks`
- `/architecture/philosophy`
- `/architecture/product`
- `/architecture/tech`

对应策略：

1. 一级 IA 主路由使用新的过渡模板，作为新产品结构的入口壳层
2. 子路由优先复用现有旧模板，避免一次性重构全部页面
3. 旧路由继续保留，确保已有使用路径、调试入口与分享链接不失效
4. 架构页先建立稳定 URL，后续再把设计师 TSX 真实实现接入这些路由
5. `overview.html` 已改为基于 `{{ BASE }}` 的 IA 主入口，不再依赖旧的平铺导航或根路径 API 请求
