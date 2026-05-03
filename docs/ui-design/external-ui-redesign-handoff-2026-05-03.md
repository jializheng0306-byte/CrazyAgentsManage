# CrazyAgentsManage 外部 UI 重构交接包

> 日期: 2026-05-03  
> 状态: active  
> 适用对象: 外部 UI / UX / 前端重构团队

---

## 一、先说清楚产品是什么

`CrazyAgentsManage` 当前不是一个通用多智能体 playground，也不是单纯的 Hermes WebUI 换皮项目。

当前规范性定位只有一句：

`一个以 HermesAgent 为宿主的 FlowMind 运营产品`

三层边界必须保持清楚：

1. `HermesAgent`
   - 运行时宿主
   - 运营执行面
2. `FlowMind`
   - 治理引擎
   - canonical truth 层
3. `CrazyAgentsManage`
   - operator console
   - 运营编排、观测、协作与治理闭环产品层

外部团队如果把 UI 重构成“另一个多 Agent 平台”，方向就是错的。

## 二、当前 UI 重构的目标

这轮 UI 重构不是从零发明新产品，而是把现有 WebUI 收口到已经确立的产品 IA 与页面职责：

- `Overview`
- `Runtime`
- `Operations`
- `Governance`
- `Collaboration`

以及三个架构展示页：

- `/architecture/philosophy`
- `/architecture/product`
- `/architecture/tech`

外部团队的任务是：

1. 让这套 IA 更清晰、更统一、更可用
2. 让现有页面从过渡壳层升级成正式产品页
3. 在不破坏 FlowMind 联动契约的前提下，重构视觉与交互层

## 三、必须先读的文档

### A. 产品母文档

1. `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
2. `docs/prd/technical-implementation-prd.md`
3. `docs/prd/operations-implementation-prd.md`

### B. 页面级 PRD

1. `docs/prd/pages/overview-page-prd.md`
2. `docs/prd/pages/runtime-page-prd.md`
3. `docs/prd/pages/operations-page-prd.md`
4. `docs/prd/pages/governance-page-prd.md`
5. `docs/prd/pages/collaboration-page-prd.md`
6. `docs/prd/pages/architecture-visualization-pages-prd.md`
7. `docs/prd/pages/webui-route-template-alignment.md`

### C. 路线图与主线状态

1. `docs/roadmap/HermesAgent-FlowMind-联合产品功能基线-2026-04-30.md`
2. `docs/roadmap/prd-execution-roadmap.md`
3. `docs/roadmap/master-task-plan.md`

### D. 设计与原型参考

1. `docs/ui-design/01-design-system.md`
2. `docs/ui-design/02-dashboard-prototype.md`
3. `docs/ui-design/03-tasks-prototype.md`
4. `docs/ui-design/04-team-memory-prototype.md`
5. `docs/ui-design/05-cron-prototype.md`
6. `docs/ui-design/06-high-fidelity-designs.md`

### E. FlowMind 联动约束

1. `docs/02-engineering/harness/hermes-flowmind-compatibility-matrix-2026-04-30.md`
2. `docs/02-engineering/harness/timeline-handoff-consumer-reverification-2026-05-03.md`
3. `docs/02-engineering/harness/handoff-generator-real-round-2026-05-03.md`

## 四、当前实现面事实

### 4.1 当前活跃分支

- `feat/auto-capture-trace`

外部团队默认应从这个分支开始，而不是旧 `main`。

### 4.2 当前 Flask 路由

当前 `src/webui/app.py` 已存在以下主路由：

- `/overview`
- `/runtime`
- `/operations`
- `/governance`
- `/collaboration`
- `/timeline`
- `/architecture/philosophy`
- `/architecture/product`
- `/architecture/tech`

同时保留旧兼容路由：

- `/`
- `/agent`
- `/graph`
- `/alerts`
- `/tokens`
- `/sessions`
- `/dashboard`
- `/tasks`
- `/team-memory`
- `/cron`
- `/skills`

### 4.3 当前模板集合

当前 `src/webui/templates/` 已存在：

- `overview.html`
- `runtime.html`
- `operations.html`
- `governance.html`
- `collaboration.html`
- `timeline.html`
- `architecture-philosophy.html`
- `architecture-product.html`
- `architecture-tech.html`

以及一批旧模板仍被子路由复用：

- `home.html`
- `dashboard.html`
- `sessions.html`
- `agent.html`
- `skills.html`
- `cron.html`
- `team-memory.html`
- `alerts.html`
- `graph.html`
- `tasks.html`
- `tokens.html`

## 五、当前 live 状态提醒

外部团队不要默认“线上正在跑的 UI = 当前仓库基线”。

截至最新治理核查，Crazy live WebUI 部署副本仍有漂移：

- `src/webui/templates/timeline.html`
- `src/webui/static/js/timeline.js`
- `src/webui/static/css/timeline.css`
- `tests/test_sprint4.py`

这意味着：

1. 设计与重构评估应优先基于仓库代码和 PRD
2. 若需要看 live，只能把它当作“当前部署状态参考”，不是唯一真相
3. 如果外部团队直接在 live 上观察页面，必须回到仓库确认是否已漂移

## 六、不可破坏的契约

### 6.1 产品契约

不要破坏五个一级 IA 的页面职责边界：

- `Overview` 负责总览和分流
- `Runtime` 负责执行过程与证据
- `Operations` 负责日常运营对象
- `Governance` 负责 FlowMind 治理状态
- `Collaboration` 负责 Codex / HermesAgent 协作闭环

### 6.2 技术契约

不要把以下契约重构掉：

1. `BASE` 感知的静态资源与链接生成
2. `/manage/static/*` 兼容路径
3. FlowMind trace 消费主路径
4. Hermes handoff 消费主路径

### 6.3 FlowMind 联动契约

当前已经稳定接上的两条消费面：

1. Timeline
   - 消费 `GET /api/bridge/trace/:candidateId`
2. Handoff
   - 消费 `moduleDetails.handoff`

外部团队可以重构 UI 表达，但不应擅自把它们改回本地拼装自由文本或旧数据形状。

## 七、建议的重构切口

建议不要“一次性全站重写”，而是按以下顺序：

1. `Overview`
   - 顶部导航
   - 全局状态摘要
   - 分区入口
2. `Runtime`
   - session / dashboard / timeline 的信息层级
3. `Governance` + `Collaboration`
   - 把 FlowMind 状态与 handoff / closeout 状态做清晰分离
4. `Operations`
   - skills / cron / team-memory / alerts 的统一视觉与操作模式
5. 架构页
   - 把说明页升级成“可跳转到真实状态”的结构页

## 八、交付时必须同时给出的内容

外部团队如果进入实施，不应只给视觉稿。

至少需要同时交付：

1. 页面结构说明
2. 组件分层方案
3. 与现有 PRD 的映射
4. 对现有模板/路由的替换策略
5. 哪些旧模板保留为兼容层
6. 哪些 FlowMind / Hermes 联动契约不能动

## 九、一句话总结

> 这次 UI 重构的正确目标，不是把 Crazy 做成一个更炫的 agent 控制台，而是把它收口成一个围绕 Hermes 运行态、FlowMind 治理态和 Codex/Hermes 协作态的正式 operator product。
