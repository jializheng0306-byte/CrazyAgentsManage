# CrazyAgentsManage 架构可视化页面 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 页面级 PRD / Architecture Visualization |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 最后更新 | 2026-04-27 |

## 页面范围

本 PRD 统一约束 3 个架构展示页：

- `ProductPhilosophyPreviewPage`
- `ProductArchitecturePreviewPage`
- `TechArchitecturePreviewPage`

## 页面目标

这三类页面的共同目标不是“静态说明架构”，而是让用户直观看见：

- FlowMind 与外界交互的边界
- FlowMind 内部关键操作链条
- 从输入、治理、执行到回写的实施动态

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

## 三类页面的分工

### 1. Product Philosophy

归属：

- 主：`Overview`
- 次：`Governance`

页面目标：

- 解释 FlowMind 为什么存在
- 解释它治理什么
- 解释它与 HermesAgent 的边界
- 把产品哲学与当前状态连接起来

### 2. Product Architecture

归属：

- 主：`Governance`
- 次：`Operations`

页面目标：

- 展示用户、Hermes、FlowMind、外部平台、输入端、桥接面的关系
- 展示跨系统治理交互图
- 区分已落地链路与规划链路

### 3. Tech Architecture

归属：

- 主：`Runtime`
- 次：`Collaboration`

页面目标：

- 展示内部技术链路
- 展示状态流和实施轨迹
- 展示协作工件与回写链路

## 页面信息架构

三类页面都应遵循：

1. 架构图主画布
2. 状态图例区
3. 节点详情区
4. 跳转入口区

## 页面模块树

- ProductPhilosophyPage
  - PhilosophyCanvas
  - StatusLegend
  - NodeInsightPanel
  - JumpRouter
- ProductArchitecturePage
  - ProductArchitectureCanvas
  - StatusLegend
  - CrossSystemNodePanel
  - JumpRouter
- TechArchitecturePage
  - TechArchitectureCanvas
  - StatusLegend
  - FlowNodePanel
  - JumpRouter

## 页面共性要求

### 1. 必须是动态架构图

要求：

- 节点可承载状态
- 链路可承载状态
- 已实现 / 运行中 / 异常 / 规划中必须可区分

### 2. 必须可跳转

要求：

- 节点可跳转到真实详情页
- 链路可跳转到证据或相关工作流页

### 3. 必须区分事实与设计

要求：

- 当前真实状态与设计意图不能混写
- 规划能力必须显式标注

## 与其他页面的关系

- `Overview` 消费 Product Philosophy 的高层状态表达
- `Governance` 消费 Product Architecture 的治理链路
- `Runtime` / `Collaboration` 消费 Tech Architecture 的实施链路

## 非目标

本文档不定义：

- 图形组件细节
- 动画与视觉细节
- 节点字段级布局

## 完成标准

1. 三类架构页都不再只是静态示意图
2. 用户可以从架构图直接进入真实产品详情页
3. 页面能表达 FlowMind 与外界交互及内部操作的实施动态
