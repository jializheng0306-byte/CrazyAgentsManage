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

当前实现已经收敛成**治理对象控制台**，因此页面重点不再是单纯的列表分区，而是：

- 左侧治理对象池
- 中央治理关系工作区
- 右侧 Agent 节点证据与架构参考

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

### 1. 治理节点对象池

内容：

- governance nodes
- agent nodes
- 节点分组与可达性
- 监控对象选择入口

### 2. 治理关系工作区

内容：

- 当前节点关系预览
- 节点类型摘要
- 关系类型摘要
- 当前应下钻的对象家族

### 3. Agent 节点证据

内容：

- 当前 agent snapshot
- 执行主体节点状态
- 与治理节点的对应关系

### 4. 架构交互入口

内容：

- 与 `ProductArchitecturePreviewPage` 的高层节点对照
- 外部桥接面状态
- 已落地能力 / 规划能力区分

## 页面信息架构

建议页面结构自上而下为：

1. 左侧治理对象池
2. 中央治理关系工作区
3. 右侧 agent 节点证据区
4. 架构交互入口区

## 页面模块树

- GovernancePage
  - GovernanceNodeListPanel
  - GovernanceGraphPreviewPanel
  - GovernanceMetaPanel
  - AgentEvidencePanel
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

1. 用户能围绕 graph node / agent node 识别治理对象和关系
2. 页面不再只是静态分类列表，而具备工作区语义
3. 页面可作为 `ProductArchitecturePreviewPage` 的治理详情依托
4. candidate / truth / review / feedback / drift 仍需通过后续真实数据面持续补强
