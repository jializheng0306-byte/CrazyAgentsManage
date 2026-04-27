# CrazyAgentsManage Governance 表面实现 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 技术子 PRD / Governance Surface |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 继承自 | `docs/prd/technical-implementation-prd.md` |
| 最后更新 | 2026-04-26 |

## 文档目的

本文档将技术实现 PRD 中的 `Governance` 分区继续拆解为可执行实施范围，聚焦：

- candidate 与 truth 的状态边界
- FlowMind bridge-aware data surfaces
- feedback / review 可见性
- drift / blocked-state 暴露

它不扩展到：

- 最终业务策略本身的定义
- 页面字段级原型
- 未落地 API 的细粒度契约设计

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

本文档不得重开：

- 顶层产品定位
- 一级 IA
- “FlowMind 是 canonical truth layer” 这一边界

## Governance 分区的产品职责

`Governance` 分区负责回答：

- 什么只是 candidate
- 什么已经进入 canonical truth
- 什么等待 review 或反馈
- 什么处于漂移、阻塞或待确认状态

## 当前证据基线

来自现有仓库与前序分析的基线事实：

- Candidate ingress、truth query、context compilation、truth change feedback 已有基础桥接面
- Clarify、Review Trigger、Mutation Request、Provenance Inspection 仍未形成完整实现
- 当前仓库最大的风险之一，是 runtime truth 与 governance truth 容易在产品表面被混淆

## 实施范围

### 1. Candidate / Truth Boundary Modeling

目标：

- 在产品数据面上显式区分 candidate state 与 canonical truth

实现要求：

- view model 层必须保留状态来源标签
- UI 不得把 candidate 显示成已确认真相
- 未确认、待 review、已确认三类状态需要可区分

### 2. FlowMind Bridge Surface Mapping

目标：

- 让 CrazyAgentsManage 只依赖真实存在的 bridge surface 暴露治理状态

当前已存在的 surface：

- candidate ingress
- truth query
- context compilation
- truth change feedback

实现要求：

- 已存在 surface 与 proposed surface 必须分栏管理
- 页面层不能假设不存在的接口已可用
- 缺失接口应以“待实现能力”呈现，而不是伪装为当前现实

### 3. Feedback / Review Visibility

目标：

- 让 operator 看到治理闭环中的 review 与 feedback 状态

实现要求：

- 至少要能表达“是否已提交”“是否待 review”“是否已回写”
- 如果当前只有部分能力存在，也必须显式暴露缺口
- close-the-loop 状态要能与 Runtime / Collaboration 关联

### 4. Drift / Blocked-State Exposure

目标：

- 让治理异常成为显式产品状态，而不是文档或日志中的隐含问题

实现要求：

- drift、blocked、stale、awaiting-confirmation 至少应有统一状态口径
- operator 能知道“这是 runtime 问题还是 governance 问题”
- 状态暴露必须可聚合到 `Overview`

### 5. Governance Summary Aggregation

目标：

- 为 `Overview` 和 `Governance` 页面提供复用型治理摘要层

实现要求：

- 提供 candidate count、pending review count、blocked count 等概要能力
- 摘要层应基于真实 bridge state，而不是 chat 推断
- 汇总层应明确哪些项是事实，哪些项是推断

### 6. 产品架构动态投影

目标：

- 让 `ProductArchitecturePreviewPage` 成为 Governance 状态的跨系统交互投影面

实现要求：

- 用户、Hermes、FlowMind、外部平台、bridge surface 至少能映射为稳定节点
- candidate、truth、feedback、review 状态可映射到节点或链路
- 页面必须显式区分已实现桥接面与规划桥接面

## 实施优先级

### P0

- candidate / truth 边界显式存在
- 已落地 bridge surface 能稳定读到并映射到页面
- governance state 不再与 runtime truth 混写

### P1

- feedback / review 可见性增强
- drift / blocked-state 形成统一口径
- governance summary 可被 `Overview` 复用
- 产品架构页获得第一版动态治理状态覆盖层

### P2

- 更强的治理自动化
- clarify / review workflow 的更深整合
- 更细粒度的 provenance 可视化

## 依赖关系

上游依赖：

- FlowMind bridge state 的真实读取面
- runtime state 与 governance state 的边界定义
- 统一的状态标签系统

下游消费者：

- `Overview`
- `Governance`
- `Collaboration`

## 非目标

本文档不定义：

- 最终业务治理策略本身
- 未落地 API 的详细协议
- 页面字段级原型
- review 流程的人机交互细节

## 完成标准

当以下条件满足时，可认为 Governance 表面子 PRD 范围基本成立：

1. 产品表面上 candidate、truth、review、feedback 状态边界清晰
2. operator 能判断一个问题属于 runtime 还是 governance
3. `Overview` 能消费治理摘要，而不再只显示 runtime 指标
4. 缺失能力被当作缺口呈现，而不是被包装成当前现实
