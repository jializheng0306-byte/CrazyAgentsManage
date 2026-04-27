# CrazyAgentsManage Overview 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Overview |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-04-27 |

## 页面目标

`Overview` 页面是整个产品的总入口。

它不是简单的数据看板，而是让用户在一次扫描中回答：

- 系统现在整体是否健康
- 哪些问题最值得优先处理
- FlowMind 治理侧是否有待办事项
- 应该跳到哪个分区继续操作

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

## 页面应承载的核心信息

### 1. 顶层健康摘要

内容：

- runtime health
- active / suspect / failed 摘要
- alerts 总览
- 平台连接状态概览

目标：

- 不打开任何细节页也能知道系统是不是处于异常态

### 2. 治理摘要

内容：

- candidate 数量
- pending review 数量
- blocked / drift 数量
- feedback 未闭环项

目标：

- 让用户知道 FlowMind 治理链路当前是否积压

### 3. 协作摘要

内容：

- open handoff 数量
- pending closeout 数量
- missing writeback 数量
- 未复核 artifacts 数量

目标：

- 让用户知道 Codex / HermesAgent 协作是否已闭环

### 4. 快捷跳转

内容：

- 跳转到 Runtime
- 跳转到 Operations
- 跳转到 Governance
- 跳转到 Collaboration
- 跳转到架构展示页

目标：

- 让 Overview 成为真正的路由中枢，而不是死数据页

## 页面信息架构

建议页面结构自上而下为：

1. 顶部全局状态带
2. runtime 健康摘要区
3. governance 摘要区
4. collaboration 摘要区
5. 快捷跳转区
6. 架构可视化入口区

## 页面模块树

- OverviewPage
  - GlobalStatusBar
  - RuntimeHealthSummary
  - GovernanceSummary
  - CollaborationSummary
  - QuickActionRouter
  - ArchitectureEntryPanel

## 关键交互

- 点击异常摘要，进入相应详情页
- 点击治理摘要，进入 `Governance`
- 点击协作摘要，进入 `Collaboration`
- 点击架构概览，进入架构展示页

## 依赖来源

- runtime summary aggregation
- governance summary aggregation
- collaboration summary aggregation
- operations summary aggregation

## 非目标

本文档不定义：

- 统计卡片字段级规格
- 图表样式细节
- API 协议

## 完成标准

1. 用户能在一个页面上看见 runtime、governance、collaboration 的顶层状态
2. 页面具备明确的下一步分流能力
3. 页面不与下一级详情页重复承担深度诊断职责
