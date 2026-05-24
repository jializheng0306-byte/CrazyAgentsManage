# CrazyAgentsManage Collaboration 运营工作流 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 运营子 PRD / Collaboration Workflow |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex（文档管理） |
| 运营评审方 | HermesAgent |
| 继承自 | `docs/prd/operations-implementation-prd.md` |
| 最后更新 | 2026-05-24 |

## 文档目的

本文档将运营实现 PRD 中的 `Collaboration` 分区继续拆解为 operator workflow，聚焦：

- handoff packet 的运营消费方式
- runtime snapshot 到 closeout 的检查路径
- 仓库事实回写的验证路径
- 技术架构页中的协作动态如何被 operator 使用

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/operations-implementation-prd.md`
- `docs/prd/collaboration-workflow-implementation-prd.md`

## Operator 目标

Operator 在 `Collaboration` 分区中必须能完成：

1. 看见 Codex 发起的 handoff
2. 看见 HermesAgent 是否完成 review / acceptance
3. 看见 closeout 是否已写回仓库事实
4. 发现未闭环协作链路
5. 知道当前应该由谁继续处理，以及下一条标准动作是什么

## 核心工作流

### 1. Handoff Review Workflow

目标：

- 让 operator 可以把 handoff 当作正式工作对象处理

关键步骤：

1. 查看 handoff 标题、目标、artifacts、问题清单
2. 判断是否需要 review / accept / reject / defer
3. 记录处理状态

验收标准：

- handoff 不再只是上下文消息
- operator 能明确看到待处理和已处理 handoff

### 2. Runtime Snapshot Inspection Workflow

目标：

- 让 operator 能从 snapshot 判断当前协作轮次处于什么阶段

关键步骤：

1. 查看 runtime snapshot 的 phase、status、actor、summary
2. 判断当前轮次是否卡住、缺证据或待 closeout
3. 跳转到对应 artifact

验收标准：

- snapshot 可读、可跟踪
- runtime-local 状态边界清楚

### 3. Closeout Verification Workflow

目标：

- 让 operator 能验证这次协作是否真的形成仓库事实

关键步骤：

1. 查看 closeout 记录
2. 检查是否关联到 PRD、roadmap、相关文档
3. 标记缺失 writeback 或缺失 evidence 的轮次

验收标准：

- closeout 不只是结束标记，而是证据链起点
- operator 能发现“做了但没落库”的协作缺口

### 4. Unclosed Collaboration Triage Workflow

目标：

- 让未闭环协作链路可被系统性处理

关键步骤：

1. 发现 open handoff、pending closeout、missing writeback、unreviewed artifact
2. 判断属于 review 缺口、文档缺口还是实施缺口
3. 分流到 Governance、Runtime 或文档面
4. 根据 `next actor / next action` 直接继续推进，而不是再从聊天补推断

验收标准：

- operator 能快速定位闭环缺口
- 每类缺口至少有一个标准处理路径

## 与架构展示页的关系

`TechArchitecturePreviewPage` 应成为 Collaboration 工作流的高层入口之一。

Operator 在这类页面中需要看到：

- handoff、runtime snapshot、closeout、repo truth 之间的链路关系
- reviewer、Hermes acceptance、PRD closeout 三个中间阶段
- 当前哪一段链路处于进行中、异常或缺失状态
- 从架构节点跳转到证据页或文档页的能力

## 非目标

本文档不定义：

- 群聊交互细节
- tmux / shell 级操作流程
- 页面字段级原型

## 完成标准

1. Collaboration 分区不再只是 artifact 列表，而具备 operator 可执行的闭环路径
2. handoff -> reviewer -> Hermes acceptance -> closeout -> PRD closeout -> repo truth 的关系能被 operator 直接检查
3. 技术架构页可以承载协作工作流的动态入口
