# CrazyAgentsManage 运营实现 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 运营实现 PRD |
| 版本 | v0.1.0 |
| 状态 | 当前基线 |
| Owner | Codex（文档管理） |
| 运营评审方 | HermesAgent |
| 最后更新 | 2026-04-26 |

## 范围说明

本文档定义 operator-facing 系统必须暴露哪些能力，才能让“以 HermesAgent 为宿主的 FlowMind 运营产品”真正可用、可运营、可复核。

它继承以下文档中的产品身份、一级信息架构与运营策略：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`

本文档覆盖：

- operator personas
- 必须可见的 runtime objects
- operator workflows
- alerts、reports 与 action surfaces
- 运营验收标准

本文档不定义 backend implementation details。那些内容属于：

- `docs/prd/technical-implementation-prd.md`

## Operator 基线

### 上位定位

- `CrazyAgentsManage` 是一个以 HermesAgent 为宿主的 FlowMind 运营产品
- 本 PRD 负责把这个定位翻译为 operator views、workflows 和 acceptance criteria
- 它不应重新打开顶层产品身份或一级 IA

### 已接受的角色模型

- `HermesAgent` 是 operations lane
- `Codex` 是 development lane
- 运营工作应产出结构化反馈，而不是临时性的架构重写

### Operator 的核心问题

Operator 必须能回答：

1. 现在什么在运行？
2. 什么卡住了？
3. 什么失败了？
4. 什么需要人工介入？
5. 哪些 FlowMind 关联状态正在漂移？

## 主要运行对象

Operator console 必须显式暴露以下对象：

- sessions
- delegated tasks / child runs
- skills
- cron jobs
- runtime alerts
- gateway / platform connection state
- FlowMind bridge state
- token / cost usage

## 基于 IA 的运营模型

本 PRD 从上位 IA 派生 operator-facing 范围，而不是继续按旧页面名称做平铺。

### 1. `Overview`

Operator outcome：

- 一眼理解整个运行系统的当前状态
- 快速识别最先需要处理的事情

Operator needs：

- 顶层健康摘要
- 未解决治理事项计数
- active alerts 与 suspect sessions
- 到“下一步动作”的最短路径
- FlowMind 产品哲学与当前状态之间的对应关系

### 2. `Runtime`

Operator outcome：

- 检查实时或历史执行行为
- 判断哪里失败、卡住或成本异常

Operator needs：

- session pipeline
- child-run lineage
- trace evidence
- error 与 cost visibility

### 3. `Operations`

Operator outcome：

- 管理支撑 Hermes 日常工作的运营对象

Operator needs：

- skill inventory 与 failure visibility
- cron visibility 与 routine control
- role / team-memory awareness
- platform connectivity state
- FlowMind 与外部平台、输入端、集成端的交互状态

### 4. `Governance`

Operator outcome：

- 区分 candidate state 与 canonical truth
- 知道哪些事项需要 review、升级或跟进

Operator needs：

- candidate / truth separation
- review queue visibility
- feedback state
- drift / blocked-state visibility

### 5. `Collaboration`

Operator outcome：

- 检查 Codex 交付了什么、HermesAgent 接受了什么、哪些内容已经变成仓库中的持久事实

Operator needs：

- handoff visibility
- closeout evidence
- 从 runtime observation 跳转到 repository truth 的链接链路
- 从技术架构链路跳转到协作证据链

## 必需的 Operator 视图

这些视图必须归属于继承而来的一级 IA：

- `Overview`
- `Runtime`
- `Operations`
- `Governance`
- `Collaboration`

### Overview 视图

Operator 需要：

- 健康摘要
- 优先级最高的异常项
- governance attention summary
- 跳转到 runtime、operations 或 governance 详情的快捷入口

同时应容纳 `ProductPhilosophyPreviewPage` 这一类“产品哲学 + 当前状态”混合表面。

### 1. Session 视图

Operator 需要：

- active / completed / suspect session 区分
- parent/child task lineage
- message / tool / token summaries
- stuck indicators

### 2. Task / Delegation 视图

Operator 需要：

- pending / running / done / failed 状态
- dependency visibility
- child agent ownership
- 明确的 follow-up 路径

### 3. Skills 视图

Operator 需要：

- 已安装 skills
- 缺失或无效的 skills
- 按角色或领域分组
- 哪些 skill failure 会阻断真实工作

### 4. Cron 视图

Operator 需要：

- 已配置 jobs
- last run / next run
- success / failure state
- 当真实能力存在时，提供 pause / resume / trigger 入口

### 5. Alerts 视图

Operator 需要：

- 显式 anomaly records
- severity
- 受影响的 runtime object
- 建议的 next action

### 6. Governance 视图

Operator 需要：

- candidate 与 truth 的显式区分
- pending review visibility
- feedback 与 drift 指示器
- 对“当前可执行动作”的明确解释

并应支撑 `ProductArchitecturePreviewPage` 这一类跨系统治理交互图。

### 7. Collaboration 视图

Operator 需要：

- handoff packets 与 closeout records 的可见性
- 检查 repository truth 发生了什么变化
- 从 runtime observation 回链到文档化验收结论的证据链

并应支撑 `TechArchitecturePreviewPage` 这一类展示内部实施链路和协作链路的技术架构页。

### 8. 架构展示视图

Operator 需要：

- 看见 FlowMind 与外界交互的完整边界
- 看见 FlowMind 内部关键操作链条
- 看见每个链路节点当前是“已实现 / 运行中 / 异常 / 规划中”
- 能从图上跳转到真实详情页或证据页

## 必需的 Operator 动作

系统最终必须支持以下结构化动作：

- acknowledge alert
- 打开受影响的 runtime object
- dispatch 或 re-dispatch 一个任务
- 检查 session / task evidence
- 触发 review routine
- 在真实 runtime capability 存在时操作 cron jobs
- 检查 handoff 与 closeout evidence
- 跳转到当前规范性 PRD 或 roadmap 表面
- 从架构图节点跳转到相应对象详情或运行证据

如果某个动作尚不存在，UI 不得暗示它已经存在。

## FlowMind 侧的 Operator 需求

从 operator 视角，CrazyAgentsManage 必须区分：

- Hermes runtime truth
- FlowMind governance truth
- pending 或尚未确认的 candidate state

### 对 FlowMind 关联状态的期望

- candidate state 必须能与 canonical truth 清晰区分
- review 与 feedback loop 必须可见
- drift 或 blockage 应作为 operator 问题显式暴露，而不是藏在 logs 里

## 报告需求

Operator 需要周期性输出，例如：

- daily runtime digest
- weekly operational audit
- pending/stuck review list
- failed task / failed cron summaries

这些报告可以从 manual 或 semi-manual 开始，但在产品上必须被视为明确需求。

## 运营验收标准

### P0

- operator 在不打开 shell 的情况下即可识别 runtime health
- stuck 或 failed 状态显式可见
- FlowMind 关联状态不会被误标为 canonical truth
- 关键 operator-facing 视图不再是 mock-only

### P1

- operator 能执行基本结构化 follow-up actions
- reports 与 recurring review workflows 一致
- skill / cron / session surfaces 互相 cross-link
- governance 与 collaboration surfaces 不再只是隐含的或 chat-only

### P2

- 更丰富的自动化
- predictive alerts
- governance assistance 与 optimization loops
- 更强的 collaboration / acceptance workflow automation

## 非目标

本文档不授权以下事项：

- 重新定义一级产品 IA
- 让 HermesAgent 直接拥有代码实现职责
- 用 chat-only 运营决策替代仓库事实
- 把所有概念上的未来能力都表述成当前承诺

## 变更控制

当一次迭代改变 operator-facing 含义时，至少更新：

1. 本运营 PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. 如果协作状态变化，更新相关 harness closeout records
