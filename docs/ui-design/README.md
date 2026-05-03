# UI Design Docs

## One-Page Summary

### 这个目录解决什么问题

- 收口 Crazy WebUI 的 UI 设计、页面 PRD、现状约束和外部重构交接入口
- 避免外部团队只看原型图或只看页面代码，忽略产品定位与双仓约束
- 给 UI 重构提供一条稳定的阅读顺序

### 谁应该读

- 外部 UI / UX 重构团队
- 需要接手 Crazy WebUI 前端的人
- 需要把页面设计与 PRD / 路线图重新对齐的人

### 先读哪三份

1. [external-ui-redesign-handoff-2026-05-03.md](./external-ui-redesign-handoff-2026-05-03.md)
2. [external-ui-redesign-team-prompt-2026-05-03.md](./external-ui-redesign-team-prompt-2026-05-03.md)
3. [06-high-fidelity-designs.md](./06-high-fidelity-designs.md)

### 典型工作流

1. 先读交接文档，理解 Crazy 当前不是通用 agent playground，而是 Hermes-hosted FlowMind operator product
2. 再读页面级 PRD 与路由对齐文档，确认必须保留的 IA、页面职责和现有模板映射
3. 最后再看高保真稿、模板代码和 live 状态，决定重构切口

### 常见误区

- 只看 `src/webui/templates/`，不看产品母文档和页面级 PRD
- 把 Crazy 重构成“独立多 Agent 控制台”，偏离 HermesAgent 宿主产品定位
- 忽略当前 live 副本与仓库基线可能存在漂移，直接拿线上页面当真相

## Current Baseline

- 当前活跃分支：`feat/auto-capture-trace`
- 当前规范性一级 IA：
  - `Overview`
  - `Runtime`
  - `Operations`
  - `Governance`
  - `Collaboration`
- 当前必须保留的架构展示路由：
  - `/architecture/philosophy`
  - `/architecture/product`
  - `/architecture/tech`

## Read In This Order

### 1. 产品与约束

- [../prd/hermesagent-hosted-flowmind-product-foundation.md](../prd/hermesagent-hosted-flowmind-product-foundation.md)
- [../prd/technical-implementation-prd.md](../prd/technical-implementation-prd.md)
- [../prd/operations-implementation-prd.md](../prd/operations-implementation-prd.md)

### 2. 页面与 IA

- [../prd/pages/overview-page-prd.md](../prd/pages/overview-page-prd.md)
- [../prd/pages/runtime-page-prd.md](../prd/pages/runtime-page-prd.md)
- [../prd/pages/operations-page-prd.md](../prd/pages/operations-page-prd.md)
- [../prd/pages/governance-page-prd.md](../prd/pages/governance-page-prd.md)
- [../prd/pages/collaboration-page-prd.md](../prd/pages/collaboration-page-prd.md)
- [../prd/pages/architecture-visualization-pages-prd.md](../prd/pages/architecture-visualization-pages-prd.md)
- [../prd/pages/webui-route-template-alignment.md](../prd/pages/webui-route-template-alignment.md)

### 3. 路线图与双仓协同

- [../roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md](../roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md)
- [../roadmap/prd-execution-roadmap.md](../roadmap/prd-execution-roadmap.md)
- [../roadmap/master-task-plan.md](../roadmap/master-task-plan.md)
- [../02-engineering/harness/hermes-flowmind-compatibility-matrix-2026-04-30.md](../02-engineering/harness/hermes-flowmind-compatibility-matrix-2026-04-30.md)

### 4. 设计稿与实现参考

- [01-design-system.md](./01-design-system.md)
- [02-dashboard-prototype.md](./02-dashboard-prototype.md)
- [03-tasks-prototype.md](./03-tasks-prototype.md)
- [04-team-memory-prototype.md](./04-team-memory-prototype.md)
- [05-cron-prototype.md](./05-cron-prototype.md)
- [06-high-fidelity-designs.md](./06-high-fidelity-designs.md)

## Current Live Fact

当前外部团队在开始前需要知道：

- 仓库基线与 Crazy live WebUI 部署副本并非完全一致
- 最新已知 live 漂移集中在：
  - `src/webui/templates/timeline.html`
  - `src/webui/static/js/timeline.js`
  - `src/webui/static/css/timeline.css`
  - `tests/test_sprint4.py`

因此，UI 团队的真相源应优先是：

1. 当前仓库受追踪文档
2. 当前仓库代码
3. 最新 live drift / closeout 说明

而不是直接把线上页面截图当成唯一基线
