# CrazyAgentsManage 技术实现 PRD

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 技术实现 PRD |
| 版本 | v0.1.0 |
| 状态 | 当前基线 |
| Owner | Codex |
| 运营评审方 | HermesAgent |
| 最后更新 | 2026-04-26 |

## 范围说明

本文档定义将 CrazyAgentsManage 落地为“以 HermesAgent 为宿主的 FlowMind 运营产品”所需的工程实现范围。

它继承以下文档中的产品身份、一级信息架构与运营策略：

- `docs/prd/hermesagent-hosted-flowmind-product-foundation.md`

本文档覆盖：

- runtime data ingestion
- API 与 adapter surfaces
- 前后端实现范围
- 技术验收标准
- phased implementation ordering

本文档不细化 operator policy。那部分属于：

- `docs/prd/operations-implementation-prd.md`

## 产品边界

### 上位定位

- `CrazyAgentsManage` 是一个以 HermesAgent 为宿主的 FlowMind 运营产品
- 本 PRD 可以继续拆分技术工作，但不能重开这一顶层定位
- 一级 IA 在上位文档中继承而来，不在这里重新定义

### 当前共享边界

- `CrazyAgentsManage` 是 Hermes runtime/operator console 所在的产品层
- `FlowMind` 是治理引擎与 canonical truth 层
- `CrazyAgentsManage` 可以展示、转译并 operationalize 面向 FlowMind 的状态
- `CrazyAgentsManage` 不能临时性地重新定义 FlowMind 语义

### 技术含义

实现上必须始终保持三个 seam 显式存在：

1. Hermes runtime 与 session substrate
2. CrazyAgentsManage operator console 与 adapters
3. FlowMind governance 与 truth interfaces

## 当前技术基线

### 已有的运行时事实

- Hermes runtime 数据源已经存在且可读取：
  - `state.db`
  - `gateway_state.json`
  - `~/.hermes/skills/`
  - `~/.hermes/memories/`
  - cron / runtime process state
- CrazyAgentsManage 已经具备 WebUI/API demo，可用于 runtime observation
- Codex/Hermes 角色分工已经被接受，实施工作不应重新争论这一点

### 仍然成立的关键缺口

- session stuck / zombie inference 仍需要更强的技术处理
- runtime signals 仍需标准化后才能对 operator 真正可用
- 一些 control surface 仍是 mock 或不完整
- 面向 FlowMind 的接口必须对齐真实 bridge contracts，而不是想象中的 endpoints

## 基于 IA 的技术拆解

本 PRD 从上位 IA 派生实现范围，而不是继续只按旧模块清单分解。

### 1. `Overview` 实现面

技术职责：

- 聚合顶层 runtime health
- 汇总未解决的 governance items
- 用低查询成本暴露 operator-attention 指标

实现含义：

- 建立 summary aggregators，而不是每个页面各自做临时查询
- 定义可复用的共享 metrics surface
- 显式区分“当前 runtime 事实”与“推断出来的健康结论”

### 2. `Runtime` 实现面

技术职责：

- session pipeline 与 trace 渲染
- parent/child lineage
- tool execution evidence
- token、latency、error、cost 可见性

实现含义：

- 把 SessionDB 与 runtime 文件状态标准化为 frontend-safe view models
- 用分页、渐进加载或虚拟化处理大规模 trace / lineage 数据
- 当前 runtime 数据不足时，补 observability capture
- 为 `TechArchitecturePreviewPage` 一类技术架构页提供可叠加的动态状态节点数据

### 3. `Operations` 实现面

技术职责：

- roles 与 skills inventory
- cron 状态与 controls
- team memory 与 shared context
- platform connectivity 与 alerts

实现含义：

- 为每类 operating object 建立明确的 adapter boundary
- 确保每个 control surface 都映射到真实 runtime capability 或明确说明其非动作状态
- 保留“未配置”和“已损坏”之间的区分
- 为 `ProductArchitecturePreviewPage` 一类跨系统交互图提供外部系统状态摘要

### 4. `Governance` 实现面

技术职责：

- candidate 与 canonical truth 的显式分离
- bridge-aware state display
- feedback 与 review 可见性
- drift / blocked state 的显式暴露

实现含义：

- 除非明确标记为 proposed surface，否则只对齐真实存在的 FlowMind bridge surface
- 在数据模型层保留 source-of-truth labels
- 让 governance state 能在没有 shell 或 chat-log 解释的前提下被直接查询
- 为 `ProductPhilosophyPreviewPage` / `ProductArchitecturePreviewPage` 提供 candidate、truth、review、feedback 的状态投影

### 5. `Collaboration` 实现面

技术职责：

- Codex/HermesAgent handoff 可见性
- runtime snapshot 可见性
- closeout traceability
- `.omx/`、`docs/` 与 `harness/` 之间的文档链接完整性

实现含义：

- 将协作产物暴露为可审阅 metadata，而不是隐藏的流程残留
- 让 runtime-local artifacts 与 durable repo artifacts 显式分离
- 让 evidence 能回链到被接受的仓库事实
- 为技术架构图中的协作节点提供 handoff / closeout 状态数据

## 架构展示页技术要求

`src/` 下的三个架构预览页，应纳入正式技术范围，而不是独立 demo：

- `ProductPhilosophyPreviewPage.tsx`
- `ProductArchitecturePreviewPage.tsx`
- `TechArchitecturePreviewPage.tsx`

当前仓库中未看到对应组件实现，因此现阶段先固定以下技术要求：

1. 为三类页面定义统一的数据注入模型
2. 区分静态结构节点与动态状态节点
3. 允许架构节点跳转到真实产品分区
4. 区分“已实现链路”“运行中链路”“规划链路”

## 实施领域

### 1. Runtime State Adapters

构建并加固以下对象的只读 adapter：

- session state
- message / token accounting
- task/delegation lineage
- skills inventory
- cron job state
- alerts 与 anomaly indicators

验收标准：

- adapter 能容忍 partial / missing runtime files
- adapter 能区分“未配置”和“已损坏”
- adapter 输出可以直接被 frontend 正常消费

### 2. Task / Delegation Substrate

实现或补完以下底层能力：

- role-aware delegation
- shared context / task state files
- task graph lineage
- cross-session task tracking

验收标准：

- delegated tasks 能产出持久状态 artifacts
- parent/child lineage 可被查询并渲染
- failure state 是显式状态，不应靠“长时间无响应”间接推断

### 3. Team / Memory Substrate

实现仓库侧所需能力：

- team memory
- shared context directories
- role memory loading
- post-iteration memory writeback

验收标准：

- team 与 shared-context 结构能可预测地创建
- read/write boundary 明确
- memory update 可审查、可归因

### 4. Runtime Controls

实现真实可用的 operator controls：

- cron visibility 与 actions
- session inspection
- task dispatch entry
- bridge status inspection
- runtime alert acknowledgement

验收标准：

- UI 中暴露的每个 control 都有真实动作，或有明确的“非动作”说明
- mock endpoints 要么被替换，要么被清晰标记

### 5. Observability UI

实现 operator-facing UI：

- sessions
- task graph / lineage
- runtime health
- skills inventory
- cron surfaces
- token/cost visibility
- alerts 与 exceptions

一级 UI 组织必须映射回上位文档定义的 IA：

- `Overview`
- `Runtime`
- `Operations`
- `Governance`
- `Collaboration`

同时，架构展示页必须共享同一套状态源，而不是复制一套脱离真实系统的独立数据。

验收标准：

- source/runtime state 在不打开 shell 的情况下可见
- abnormal state 具备 root-cause breadcrumbs
- 高频页面在大数据量下仍然可用

### 6. Collaboration Workflow Substrate

实现产品可见的协作底座：

- handoff packet discovery
- runtime snapshot inspection
- closeout evidence linkage
- runtime-local artifacts 与 durable repo documents 的交叉引用

验收标准：

- 不依赖 tmux 或 shell 也能检查 collaboration artifacts
- runtime-local state 与 durable repository truth 清晰分离
- closeout evidence 能链接到相应 PRD 与 roadmap 表面

### 7. Architecture Visualization Substrate

实现三类架构展示页的共用底座：

- 产品哲学节点模型
- 产品架构关系模型
- 技术架构链路模型
- 动态状态覆盖层

验收标准：

- 架构页能表达外部交互与内部操作链路
- 核心节点可映射到真实产品分区或状态源
- 页面能区分设计意图与当前实施状态

## FlowMind 集成契约

CrazyAgentsManage 必须对齐 `FlowMindDeploy` 中已经存在的真实 FlowMind-facing interface。

### 当前已对齐的 bridge surfaces

- candidate ingress
- truth query
- context compilation
- truth change feedback

### 规则

除非明确标记为 proposed surface，否则不要在实施规划中虚构新的 API 名称，更不能把它们和已实现 bridge surface 混在一起。

## 下一级技术子 PRD

为了继续拆细技术实施面，当前技术 PRD 之下先行派生四份子 PRD：

- `docs/prd/runtime-observability-implementation-prd.md`
- `docs/prd/governance-surface-implementation-prd.md`
- `docs/prd/operations-surface-implementation-prd.md`
- `docs/prd/collaboration-workflow-implementation-prd.md`

它们分别负责把 `Runtime`、`Governance`、`Operations` 与 `Collaboration` 四个一级分区进一步落到可执行范围。

## 非目标

本文档不授权以下事项：

- 重新定义一级产品 IA
- 重新定义 FlowMind 产品语义
- 把 Hermes 当成 canonical truth 的来源
- 把 HermesAgent 变成第二开发 lane
- 只通过 chat 临时做架构决策而不落仓库事实

## 技术验收门槛

### P0

- runtime state adapters 稳定可靠
- 真实 runtime signals 已暴露
- session / task anomaly 可识别
- 关键 operator surface 不再是 mock-only

### P1

- task dispatch entry 可用
- skill scanning 一致
- memory / team substrate 可工作
- 关键 UI 页面具备运营可导航性
- 一级 IA 分区都已有明确 backing data source

### P2

- 更高级的自动化与优化层
- 长尾 dashboard
- 次级集成与便利工具
- collaboration workflow surfaces 更快、更自动化

## 变更控制

当任务改变技术范围时，至少更新：

1. 本技术 PRD
2. `docs/roadmap/prd-execution-roadmap.md`
3. 如果角色协作状态变化，更新 harness closeout artifacts
