# CrazyAgentsManage Runtime 可观测性实现 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 技术子 PRD / Runtime Observability |
| 版本 | v0.1.0 |
| 状态 | Draft |
| Owner | Codex |
| 继承自 | `docs/prd/technical-implementation-prd.md` |
| 最后更新 | 2026-04-26 |

## 文档目的

本文档将技术实现 PRD 中的 `Runtime` 分区继续拆解为可执行的实施范围，聚焦：

- session pipeline
- trace / lineage
- tool execution evidence
- token / latency / error / cost observability

它不扩展到：

- Governance 的业务状态建模
- 页面字段级原型
- 底层表结构 migration 细节

## 继承关系

本文档继承：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`
- `docs/prd/technical-implementation-prd.md`

本文档不得重开：

- 顶层产品定位
- 一级 IA
- Codex / HermesAgent lane boundary

## Runtime 分区的产品职责

`Runtime` 分区负责回答：

- 什么正在运行
- 什么已经完成
- 什么失败了
- 什么卡住了
- 哪些调用成本异常
- 哪些异常需要 operator 立即介入

## 当前证据基线

来自现有仓库和既有 PRD 的基线事实：

- Hermes 已有 SessionDB、tool calls、gateway、cron 和 child session 运行记录
- 现有 WebUI 已有 session / pipeline / dashboard 雏形
- 现有 observability 数据仍有明显缺口，尤其在 tool duration、message-level token、error detail、TTFT、TPS 上

## 实施范围

### 1. Session 管线数据面

目标：

- 统一读取根会话和子会话
- 提供 session 生命周期视图
- 暴露 active / completed / suspect / failed 分类

实现要求：

- 标题、时间、来源、状态、父子关系必须可稳定读取
- 会话状态不能只靠页面端临时推断
- 大规模会话列表必须支持分页或渐进加载

### 2. Trace 与 Lineage 数据面

目标：

- 支持 pipeline 详情页
- 支持 parent / child lineage 树
- 支持跨会话追踪 delegate_task 结果

实现要求：

- root / child / derived relation 必须可查询
- trace 数据必须支持按时间和层级组织
- lineage 关系需要能服务 Runtime 页面与后续 Collaboration 页面

### 3. Tool Execution Evidence

目标：

- 让 operator 能看见哪些工具被调用、何时调用、结果如何

实现要求：

- tool name、输入摘要、输出摘要、状态至少需要标准化暴露
- 异常工具调用必须可被高亮
- 后续可扩展 duration / token attribution，但当前至少要保留扩展位

### 4. 性能与成本指标

目标：

- 把 runtime observability 从“会话级汇总”推进到“可诊断粒度”

优先指标：

- session-level token
- message-level token
- tool duration
- API duration
- TTFT
- TPS
- error details
- model switch
- compression count

实现要求：

- 必须区分“当前已有数据”和“需要新增埋点的数据”
- 页面不得把缺失数据伪装成 0 或正常
- 任何推断指标都必须能说明来源

### 5. Runtime Summary Aggregation

目标：

- 为 `Overview` 提供可复用汇总层

实现要求：

- 汇总层不应依赖单个页面临时拼装
- 支持健康摘要、活动会话计数、异常计数、成本摘要
- 汇总结果应可被多个页面复用

### 6. 技术架构动态投影

目标：

- 让 `TechArchitecturePreviewPage` 不只是静态图，而是 Runtime 状态的架构投影面

实现要求：

- session、trace、lineage、tool execution 至少能映射到架构节点或链路
- 节点状态支持正常、运行中、异常、缺失四类基础状态
- 架构图状态必须复用 Runtime 数据源，而不是独立手填

## 实施优先级

### P0

- session 列表和详情具备真实状态
- root / child lineage 可见
- trace 基础证据可见
- error state 不再依赖模糊推断

### P1

- tool execution evidence 标准化
- token / latency / error metrics 扩展
- `Overview` 汇总层成型
- 技术架构页获得第一版动态状态覆盖层

### P2

- 更细粒度成本归因
- 更高级的性能可视化
- 趋势与分布分析

## 依赖关系

上游依赖：

- SessionDB 与 runtime 文件读取能力
- observability 埋点补齐
- frontend-safe view model 规范

下游消费者：

- `Overview`
- `Runtime`
- `Collaboration`

## 非目标

本文档不定义：

- Governance 业务逻辑
- review / feedback 工作流
- 页面字段级 wireframe
- 底层 SQL migration 细节

## 完成标准

当以下条件满足时，可认为 Runtime 可观测性子 PRD 范围基本成立：

1. Runtime 页面不再只是展示原始数据碎片，而能表达会话与执行链路
2. operator 能在不进 shell 的前提下发现主要运行异常
3. 关键 observability 缺口有明确补齐路径
4. 汇总层可为 `Overview` 提供稳定输入
