# CrazyAgentsManage Governance 运营工作流 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 运营子 PRD / Governance Workflow |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex（文档管理） |
| 运营评审方 | HermesAgent |
| 继承自 | `docs/prd/operations-implementation-prd.md` |
| 最后更新 | 2026-04-27 |

## 文档目的

本文档将运营实现 PRD 中的 `Governance` 分区继续拆解为 operator workflow，聚焦：

- candidate 到 truth 的运营判断路径
- review / feedback 的处理流程
- drift / blocked / awaiting-confirmation 的运营分流
- 架构展示页中的治理动态如何被 operator 消费

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/operations-implementation-prd.md`
- `docs/prd/governance-surface-implementation-prd.md`

## Operator 目标

Operator 在 `Governance` 分区中必须能完成：

1. 判断一个对象只是 candidate 还是已成 truth
2. 找到哪些事项等待 review
3. 识别 drift / blocked / stale / awaiting-confirmation 状态
4. 决定下一步是跟进、升级、等待还是回写

## 核心工作流

### 1. Candidate Intake Workflow

目标：

- 让 operator 能看到新进入治理系统的 candidate

关键步骤：

1. 看到 candidate 列表或架构图节点变化
2. 判断来源和当前状态
3. 决定是否需要进一步 clarify / review / follow-up

验收标准：

- candidate 不会被误看成 canonical truth
- 来源、状态、后续动作建议清晰可见

### 2. Review Queue Workflow

目标：

- 让 operator 能系统性处理待 review 事项

关键步骤：

1. 进入 review queue
2. 按优先级、阻塞程度、风险查看事项
3. 执行 follow-up 或转交

验收标准：

- pending review 项可排序、可筛选、可跟踪
- 处理后的状态变化可见

### 3. Feedback Closure Workflow

目标：

- 让 operator 能看到 feedback 是否完成闭环

关键步骤：

1. 查看 feedback 是否已提交
2. 判断是否已回写 / 已接受 / 仍待处理
3. 标记未闭环项

验收标准：

- operator 能直接发现未闭环项
- feedback 状态不再隐含在日志或 chat 中

### 4. Drift / Blocked Triage Workflow

目标：

- 让治理异常具备统一运营处理路径

关键步骤：

1. 识别 drift / blocked / stale / awaiting-confirmation
2. 判断是 runtime 问题还是 governance 问题
3. 分流到相应详情页或协作链路

验收标准：

- operator 能明确知道问题归属
- 每种状态至少有一个规范 follow-up 路径

### 5. Loop Stage / Gate Projection Workflow

目标：

- 让 operator 能看到治理闭环当前卡在哪个显式 gate，而不是只从 trace / closeout / feedback 文本里反推

关键步骤：

1. 判断当前对象属于哪类 gate stage
2. 识别下一步动作归属给谁
3. 区分该 stage 是运营投影还是治理 authority

验收标准：

- `Loop Stage` 只表达运营闭环，不新增 `truth.status`
- operator 能分清 `review decision`、`operational gate`、`feedback closure`
- 页面可为后续 `Loop Surface` 子表面提供治理侧输入

## 与架构展示页的关系

`ProductArchitecturePreviewPage` 应成为 Governance 工作流的高层入口之一。

Operator 在这类页面中需要看到：

- 哪些治理链路已落地
- 哪些节点处于 review / feedback / blocked 状态
- 哪些桥接面仍是规划状态

## 非目标

本文档不定义：

- 底层 API 协议
- Clarify / Review engine 的实现细节
- 页面字段级原型

## 完成标准

1. Governance 分区不再只是状态展示，而具备 operator 可执行的处理路径
2. candidate / truth / review / feedback / drift 状态边界可直接被 operator 使用
3. 架构展示页可以承载治理工作流的高层动态入口
