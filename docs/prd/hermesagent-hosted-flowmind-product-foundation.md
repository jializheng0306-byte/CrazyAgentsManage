# CrazyAgentsManage 产品基础文档

## 版本信息

| 字段 | 值 |
|------|-------|
| 产品 | CrazyAgentsManage |
| 文档类型 | 上位产品基础文档 |
| 版本 | v0.1.0 |
| 状态 | 当前生效的规范性母文档 |
| Owner | Codex |
| 运营评审方 | HermesAgent |
| 最后更新 | 2026-04-26 |

## 文档目的

本文档是 CrazyAgentsManage 的上位产品定义。

后续 PRD 应继承本文档，而不是重新打开以下顶层问题：

- 产品的顶层定位
- 一级信息架构
- 运营策略
- Hermes 运行时、CrazyAgentsManage 与 FlowMind 之间的叙事边界

本文档有意停留在以下层级之上：

- 底层 API 设计
- 表结构设计
- 页面字段级原型

这些内容应放在下游实现型 PRD 中定义。

## 规范性产品定位

CrazyAgentsManage 的规范性定位是：

`一个以 HermesAgent 为宿主的 FlowMind 运营产品`

更具体地说：

- `HermesAgent` 是运行时宿主与运营执行面
- `FlowMind` 是治理引擎与规范真相层
- `CrazyAgentsManage` 是产品层，负责让运行态可见、让运营对象可管理、让治理闭环可执行

## 叙事边界

CrazyAgentsManage 不应再被主要定义为：

- 一个通用的多智能体协作平台
- 一个 Hermes WebUI demo 或仅仅是增强外壳
- 一个以角色扩张为核心叙事的 agent playground

这些能力仍然可以存在，但它们只是从属能力，不是产品的一号身份。

因此，当以下文档仍将产品表述为通用多智能体协作平台时：

- `docs/prd/product-requirements.md`

应以本文档为新的顶层覆盖口径。

## 产品问题定义

仓库里已经存在真实的运行时数据面、协作规则以及 FlowMind 桥接概念，但它们仍散落在多份设计文档中，并携带部分互相竞争的顶层叙事。

这个产品真正要解决的问题，不只是“如何增加更多 Agent”。

它要解决的是：

- 如何让 Hermes 的运行态具备运营可读性
- 如何把运行对象变成可管理的运营表面
- 如何把 Hermes 侧运营动作接到 FlowMind 侧治理真相
- 如何把 Codex 到 Hermes 的协作闭环沉淀为仓库中的持久事实

## 产品框架

CrazyAgentsManage 应被理解为一个四层产品。

### 1. 运行时层（Runtime）

这一层回答：

- 现在有什么在运行
- 什么卡住了
- 什么失败了
- 什么代价过高
- 什么正在退化

核心对象：

- sessions
- 子运行 / 委派任务
- 工具执行
- token、延迟、成本
- gateway 与平台连接状态
- cron 状态
- 运行时异常

### 2. 运营层（Operations）

这一层回答：

- 我们在运营什么对象
- 哪些对象可以配置
- 哪些对象可以操作
- 哪些例行机制正在运转

核心对象：

- roles
- skills
- team memory
- scheduled jobs
- alerts
- integration endpoints

### 3. 治理层（Governance）

这一层回答：

- 什么还只是 candidate
- 什么已经是 canonical truth
- 什么需要 review
- 哪里出现 drift 或 blockage

核心对象：

- candidate ingress
- truth query
- feedback
- review queue
- drift / stale / blocked 状态
- provenance

### 4. 协作层（Collaboration）

这一层回答：

- Codex 交付了什么
- HermesAgent 评审了什么
- 什么被接受或拒绝
- 什么被提升为仓库中的持久事实

核心对象：

- handoff packets
- runtime state snapshots
- closeout records
- PRD / roadmap 更新
- harness artifacts

## 规范性信息架构

一级信息架构应按产品责任组织，而不是按底层实现模块平铺。

### 1. `Overview`

目的：

- 顶层系统健康概览
- 关键运行时指标
- 未解决治理事项摘要
- 运营注意力聚合入口

### 2. `Runtime`

目的：

- session pipeline
- traces
- 子 Agent 树
- 工具执行
- 错误
- token、延迟、性能、成本

### 3. `Operations`

目的：

- roles
- skills
- team memory
- cron
- alerts
- 平台连接状态

### 4. `Governance`

目的：

- candidate 状态
- truth 状态
- feedback
- review 工作流
- drift / blocked 项

### 5. `Collaboration`

目的：

- Codex/HermesAgent handoff artifacts
- review 状态
- closeout evidence
- 关联到仓库事实的证据链

## FlowMind 架构可视化表面

当前 `src/` 下存在三个设计预览入口：

- `src/ProductPhilosophyPreviewPage.tsx`
- `src/ProductArchitecturePreviewPage.tsx`
- `src/TechArchitecturePreviewPage.tsx`

当前仓库里尚未看到对应组件实现一并落库，因此不能把它们视为已完整实现页面；但从命名已经可以确认三类产品意图：

1. 产品哲学层
2. 产品架构层
3. 技术架构层

这三类页面应被正式吸收到产品体系中，作为“FlowMind 架构与实施动态可视化表面”，而不是独立说明页。

### 规范性角色

这三类页面的规范性角色应为：

- 让用户看见 FlowMind 与外界交互的边界
- 让用户看见 FlowMind 内部关键操作链条
- 让用户看见从输入、治理、执行到回写的实施动态

### 与一级 IA 的映射

- `ProductPhilosophyPreviewPage`
  - 主归属：`Overview`
  - 次归属：`Governance`
  - 负责解释 FlowMind 为什么存在、它治理什么、它与 HermesAgent 的角色边界

- `ProductArchitecturePreviewPage`
  - 主归属：`Governance`
  - 次归属：`Operations`
  - 负责展示 FlowMind、Hermes、用户、平台输入、集成端之间的业务交互图

- `TechArchitecturePreviewPage`
  - 主归属：`Runtime`
  - 次归属：`Collaboration`
  - 负责展示内部技术链路、状态流、治理回写与协作工件的连接关系

### 演进要求

这些页面未来不应只是静态架构图，而应逐步成为“架构图 + 动态状态”的混合表面：

- 对外可看见交互对象和交互状态
- 对内可看见 candidate、truth、review、feedback、handoff、closeout 等关键操作状态
- 可区分已落地链路、运行中链路、异常链路和规划链路

## UI 方向

UI 应是一个运营产品表面，而不是一个 demo shell。

### 产品级 UI 原则

- 深色、信息密集、适合扫描
- 动作优先，而不是装饰优先
- 既要看见 runtime，也要看见 governance
- 面向高频重复运营使用
- 结构上遵循五个一级 IA 分区
- 架构展示页必须与真实动态状态绑定，而不是纯静态示意图

### 视觉方向

保留目前最强的两条方向：

- Hermes 原生的运营气质
- Vercel 风格的 runtime trace / timeline 表达方式，只在它真正提升诊断效率时使用

但不要让 runtime trace 反过来成为整个产品的唯一身份。

它只是更大运营产品里的一个重要表面。

### 页面归属规则

每个页面都必须明确归属于以下五类之一：

- Overview
- Runtime
- Operations
- Governance
- Collaboration

如果一个新页面不能明确归类，就说明它还没有被产品化地定义清楚。

### 架构展示页规则

架构展示页属于正式产品页面，不属于附属说明页。

它们必须满足：

- 能解释对象边界
- 能呈现实时或准实时状态
- 能区分已实现链路与规划链路
- 能跳转到对应的 Runtime / Operations / Governance / Collaboration 详情表面

## 功能策略

产品应围绕五个闭环来设计。

### 1. Observe

- 发现健康、失败、drift、成本和 stuck 状态

### 2. Organize

- 管理 roles、skills、memory、jobs 和 integrations

### 3. Govern

- 把 candidate 状态推进到 reviewed / canonical 状态

### 4. Operate

- 触发例行机制
- 处理 alerts
- 检查并跟进运行时异常

### 5. Close the loop

- 把决策和结果回写成持久事实

## 运营策略

CrazyAgentsManage 应被定义为三个相连闭环的收口点。

### 运行时闭环

- Hermes 输出运行时状态
- CrazyAgentsManage 让它变得可见、可诊断、可操作

### 治理闭环

- Hermes 侧事件和输入进入 FlowMind 侧治理对象
- candidate、truth、review 三种状态必须显式区分

### 协作闭环

- Codex 的实现输出
- HermesAgent 的运营评审
- 仓库事实回写

这三者共同构成产品真正的增长飞轮。

## 产品优先级

优先级应由闭环价值决定，而不是由表面新颖度决定。

### 优先顺序

1. 真实可用的运行时可观测性
2. 治理状态可见性与状态边界
3. 运营动作与周期性工作流
4. 协作证据和 closeout 纪律
5. 次级自动化与便利层

### 明确的反优先项

不要优先做：

- 没有真实运营用途的角色扩张
- 一级导航蔓延
- mock 控制面
- 把推测中的治理 API 包装成当前现实

## 当前状态解释

基于当前仓库文档，可以做出以下判断：

- runtime 与 WebUI 观察基础是真实存在的
- Codex/HermesAgent 协作边界已经明确
- FlowMind 的治理角色在概念上已经清楚
- 治理闭环在实现上仍不完整
- 旧产品叙事比当前仓库共识更宽泛、更松散

这意味着后续 PRD 的主要任务，不再是重新发现产品身份。

它们的任务，是从这里已经固定的产品身份继续往下拆成可执行计划。

## 下游 PRD 派生规则

### Technical PRD 必须派生：

- runtime adapters
- controls
- bridge-aware data surfaces
- UI/API implementation work

但不得重定义产品身份。

### Operations PRD 必须派生：

- operator personas
- views
- workflows
- action surfaces
- acceptance gates

但不得重开一级 IA 或治理边界。

### Roadmap 必须派生：

- phase 顺序
- workstream 顺序
- merge gates
- 文档更新节奏

这些都应从本文档定义的产品优先级继续展开。

## 非目标

本文档不定义：

- 底层 API endpoints
- 表结构细节
- 字段级 wireframes
- 后端模块边界
- 最终视觉组件规格

## 可复用规范表述

后续文档默认使用以下表述：

`CrazyAgentsManage 是一个以 HermesAgent 为宿主的 FlowMind 运营产品，负责为 AI Agent 运行系统提供运行时可观测性、运营对象管理和治理闭环执行能力。`
