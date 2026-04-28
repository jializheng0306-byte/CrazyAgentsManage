# CrazyAgentsManage Operations 表面实现 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 技术子 PRD / Operations Surface |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 继承自 | `docs/prd/technical-implementation-prd.md` |
| 最后更新 | 2026-04-27 |

## 文档目的

本文档将技术实现 PRD 中的 `Operations` 分区继续拆解为可执行实施范围，聚焦：

- roles / skills / team memory / cron / alerts / platform connectivity
- 外部系统交互状态的可见化
- 对应架构展示页中的外部交互状态投影

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`
- `docs/prd/operations-implementation-prd.md`

## Operations 分区的产品职责

`Operations` 分区负责回答：

- 我们在运营哪些对象
- 哪些对象正常、异常、缺失配置
- 哪些例行机制正在生效
- 外部系统连接是否健康

## 实施范围

### 1. Roles / Skills Inventory Surface

目标：

- 让 operator 清楚当前有哪些角色与技能资源可用

实现要求：

- 角色、技能、分类、可用性、失效状态需要标准化展示
- 缺失或失效的 skill 必须显式暴露

### 2. Cron / Routine Surface

目标：

- 让周期性运行机制具备可见状态与动作边界

实现要求：

- job 配置、last run、next run、状态必须可见
- pause / resume / trigger 只能在真实能力存在时暴露

### 3. Team Memory / Shared Context Surface

目标：

- 让 team memory、shared context、role memory 变成可检查对象

实现要求：

- memory 对象需区分团队级、角色级、共享级
- 读写边界必须可见

### 4. Platform Connectivity Surface

目标：

- 让 Hermes、FlowMind、外部平台与输入端之间的连接状态可见

实现要求：

- 至少支持在线、异常、未配置三类状态
- 可供 `ProductArchitecturePreviewPage` 投影外部交互状态

### 5. Operations Summary Aggregation

目标：

- 为 `Overview` 和 `Operations` 页面提供汇总层

实现要求：

- 汇总层至少提供 skills、cron、memory、connectivity 四类摘要
- 必须可复用，而不是单页面临时拼装

## 实施优先级

### P0

- roles / skills / cron / alerts / platform connectivity 具备真实状态
- 未配置与异常显式区分

### P1

- team memory / shared context 表面标准化
- `ProductArchitecturePreviewPage` 获得第一版外部交互状态覆盖层

### P2

- 更细粒度的运维摘要
- 更强的联动与自动化能力

## 非目标

本文档不定义：

- 具体 API 协议
- 页面字段级原型
- 最终视觉组件规范

## 完成标准

1. `Operations` 页面不再只是对象列表，而能表达运营状态
2. 外部连接状态可被清楚区分
3. 架构展示页能够复用 Operations 侧状态源
