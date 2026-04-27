# CrazyAgentsManage Runtime 页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Runtime |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-04-27 |

## 页面目标

`Runtime` 页面负责让用户看见系统实际执行过程，而不仅是结果摘要。

它要回答：

- 什么正在运行
- 谁派生了谁
- 哪个环节失败、卡住或代价过高
- 哪些工具执行构成了当前结果

## 继承关系

本文档继承：

- `docs/prd/runtime-observability-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

## 页面应承载的核心信息

### 1. Session 列表与状态

内容：

- 根会话列表
- 子会话数量 / 层级
- active / completed / suspect / failed 状态
- 来源、时间、标题摘要

### 2. Trace 与 Lineage

内容：

- parent / child lineage
- 执行链路
- tool execution timeline
- 状态切换节点

### 3. 工具证据

内容：

- 工具名称
- 输入摘要
- 输出摘要
- 成功 / 失败 / 异常

### 4. 性能与成本

内容：

- token
- latency
- tool duration
- error details
- cost indicators

## 页面信息架构

建议页面结构自上而下为：

1. session 列表与筛选区
2. session 详情区
3. trace / lineage 区
4. tool evidence 区
5. 性能与成本区

## 页面模块树

- RuntimePage
  - SessionFilterBar
  - SessionListPanel
  - SessionDetailPanel
  - LineageTracePanel
  - ToolEvidencePanel
  - RuntimeMetricsPanel

## 关键交互

- 选中一个 session 查看详情
- 从 lineage 节点跳转到关联 session
- 从异常工具调用跳转到证据
- 从 runtime 异常跳转到 governance 或 collaboration 相关链路

## 依赖来源

- session 管线数据面
- trace / lineage 数据面
- tool execution evidence
- runtime observability 指标

## 非目标

本文档不定义：

- tool row 字段级布局
- timeline 视觉规范
- 数据埋点实现细节

## 完成标准

1. 用户能看见会话执行链路，而不只是原始日志碎片
2. runtime 异常具备可追溯路径
3. 页面可作为 `TechArchitecturePreviewPage` 的底层详情依托
