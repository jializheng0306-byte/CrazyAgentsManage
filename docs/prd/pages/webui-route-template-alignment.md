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

## 当前模板集合

来自 `src/webui/templates/`：

- `agent.html`
- `alerts.html`
- `cron.html`
- `dashboard.html`
- `graph.html`
- `home.html`
- `overview.html`
- `sessions.html`
- `skills.html`
- `tasks.html`
- `team-memory.html`
- `tokens.html`

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

当前缺口：

- 还没有直接对齐 `Governance` 的模板

建议：

- 新增治理主模板，或先由 `graph.html` 过渡承载
- 后续把 candidate / truth / review / feedback / drift 表面聚合进去

### `Collaboration`

当前缺口：

- 还没有直接对齐 `Collaboration` 的模板

建议：

- 新增协作主模板
- 先通过 `dashboard.html` 或 `graph.html` 临时挂载协作链路入口

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

架构页建议路由：

- `/architecture/philosophy`
- `/architecture/product`
- `/architecture/tech`

## 当前差距

1. 旧功能页仍然保留原有平铺路由，导航本身尚未整体切换到新 IA
2. 新增的 IA 页面目前是过渡壳层，尚未把旧模板真正聚合为一个统一界面
3. 3 个架构页已接入当前 WebUI 路由体系，但仍是占位性接入，尚未挂载真实 TSX 展示实现

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
