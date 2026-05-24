# CrazyAgentsManage Collaboration 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Collaboration |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-05-24 |

## 页面目标

`Collaboration` 页面负责让用户看见 Codex / HermesAgent 协作链路是否真正闭环。

当前实现已经收敛成**协作工作台**，因此页面主体不再是“若干并列列表”，而是：

- 顶部协作状态摘要与 next hop
- reviewer / acceptance / PRD closeout 统一证据链
- 左侧交接对象池
- 中央协作执行语义
- 右侧 harness 证据面板
- 中部 `Collaboration Summary Aggregation`
- 证据跳转入口

它要回答：

- handoff 发起了什么
- HermesAgent 是否完成 review / acceptance
- closeout 是否形成仓库事实
- 哪条协作链路还没有闭环

## 继承关系

本文档继承：

- `docs/prd/collaboration-workflow-implementation-prd.md`
- `docs/prd/collaboration-operator-workflow-prd.md`

## 页面应承载的核心信息

### 1. 交接对象池

内容：

- handoff package 列表
- 目标
- artifacts
- 当前状态

### 2. 中央协作执行语义

内容：

- handoff → task workspace
- 会话链路 / 治理图谱作为 supporting evidence
- 主工作面与支持证据的分层说明

### 3. Harness 证据面板

内容：

- closeout / trace / snapshot 摘要
- 缺失 writeback 提示
- harness 证据入口

### 4. Collaboration Summary Aggregation

内容：

- open handoff
- pending closeout
- missing writeback
- unreviewed artifact

### 5. Evidence Jumps

内容：

- 跳到 task workspace
- 跳到 loop surface
- 跳到 runtime sessions
- 跳到 governance graph
- 跳到 operations > harness

### 6. Unified Evidence Chain

内容：

- reviewer stage
- Hermes acceptance stage
- PRD / roadmap / tracker closeout stage
- next actor
- next action

## 页面信息架构

建议页面结构自上而下为：

1. 顶部协作状态摘要
2. 协作分诊摘要
3. 统一证据链
4. 左侧交接对象池
5. 中央协作执行语义区
6. 证据跳转入口
7. 右侧 harness 证据面板
8. `Loop Surface` 子表面入口（当前已挂到 `/collaboration/loops`）

## 页面模块树

- CollaborationPage
  - CollaborationSummaryPanel
  - CollaborationEvidenceChainPanel
  - HandoffPoolPanel
  - CollaborationWorkspacePanel
  - EvidenceJumpPanel
  - SupportingEvidencePanel
  - HarnessEvidencePanel
  - LoopSurfaceEntryPanel

## 关键交互

- 从 handoff 跳到相关 artifact
- 从任务协作工作台跳到当前执行对象
- 从支持证据跳到 runtime sessions / governance graph
- 从 harness 证据跳到仓库事实文档
- 从 `Loop Surface` 入口跳到 cycle / feedback / memory candidate 子表面

## 依赖来源

- handoff surface
- runtime snapshot surface
- closeout evidence surface
- collaboration operator workflow

## 非目标

本文档不定义：

- 群聊消息格式
- tmux 操作细节
- 页面字段级原型

## 完成标准

1. 协作闭环可以作为页面级体验被直接检查
2. 页面能清楚区分主协作对象与 supporting evidence
3. `Loop Surface` 作为协作子表面有明确挂载点
4. 页面可作为 `TechArchitecturePreviewPage` 的协作详情依托
