# CrazyAgentsManage Governance 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Governance |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-04-27 |

## 页面目标

`Governance` 页面负责让用户看见 FlowMind 治理状态，而不是把治理信息混在 runtime 里。

它要回答：

- 什么只是 candidate
- 什么已经进入 truth
- 什么等待 review / feedback
- 什么处于 drift / blocked / stale / awaiting-confirmation

## 继承关系

本文档继承：

- `docs/prd/governance-surface-implementation-prd.md`
- `docs/prd/governance-operator-workflow-prd.md`

## 页面应承载的核心信息

### 1. Candidate / Truth 边界

内容：

- candidate 列表
- truth 对象摘要
- 状态来源标签

### 2. Review / Feedback 队列

内容：

- pending review 项
- feedback 状态
- 已回写 / 未回写状态

### 3. 异常治理状态

内容：

- drift
- blocked
- stale
- awaiting-confirmation

### 4. 架构交互入口

内容：

- 与 `ProductArchitecturePreviewPage` 的高层节点对照
- 外部桥接面状态
- 已落地能力 / 规划能力区分

## 页面信息架构

建议页面结构自上而下为：

1. candidate / truth 边界区
2. review / feedback 队列区
3. 异常治理状态区
4. 架构交互入口区

## 页面模块树

- GovernancePage
  - CandidateTruthBoundaryPanel
  - ReviewQueuePanel
  - FeedbackStatusPanel
  - GovernanceExceptionPanel
  - ProductArchitectureEntryPanel

## 关键交互

- 从 candidate 跳到对应上下文
- 从 blocked / drift 项跳到处理链路
- 从治理节点跳到相关 collaboration 或 runtime 证据

## 依赖来源

- candidate / truth boundary modeling
- feedback / review visibility
- drift / blocked exposure
- governance operator workflow

## 非目标

本文档不定义：

- FlowMind 业务策略本身
- review engine 细节
- 页面字段级原型

## 完成标准

1. candidate、truth、review、feedback、drift 状态边界清楚
2. 用户能知道下一步应该处理哪种治理问题
3. 页面可作为 `ProductArchitecturePreviewPage` 的治理详情依托
