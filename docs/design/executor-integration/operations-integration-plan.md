# Crazy Operations × executor integrations 接入方案

## 文档目的

本文档定义：在不改变 `CrazyAgentsManage` 现有产品定位和一级 IA 的前提下，如何将 `executor` 的集成、工具目录、secret/provider 与 optional execution 能力，优先接入 Crazy 的 `Operations` 分区，作为最小风险、最大收益的第一阶段落地方向。

---

# 1. 背景与前提

## 1.1 Crazy 当前定位

Crazy 当前是：
> **Hermes-hosted FlowMind operating product**

固定 IA：
- Overview
- Runtime
- Operations
- Governance
- Collaboration

其中：
- Runtime = Hermes 运行态与观测真相
- Governance = FlowMind 治理真值
- Collaboration = handoff / closeout / repo truth 闭环
- Operations = operator 可操作对象与平台能力面

## 1.2 executor 的适配定位

executor 不作为 Crazy 的产品底座，而作为：
> **Operations / Integrations capability substrate**

也就是承接：
- source onboarding
- tool catalog
- secret / credentials
- MCP / OpenAPI / GraphQL integrations
- optional external execution

---

# 2. 第一阶段目标

## 2.1 接入目标

只在 `Operations` 里引入 executor 的能力，形成一个新的 integrations capability plane。

### 第一阶段不碰
- Runtime truth
- Governance truth
- Collaboration 闭环
- Crazy 一级 IA
- Crazy 主产品壳

### 第一阶段要得到的能力
- 外部 source 的统一接入
- source 对应的 tool catalog 可见
- source / provider / credentials 健康态可见
- 为未来 external automation 扩展 execution plane 预留位置

---

# 3. 建议新增/增强的 Operations 对象

当前 `Operations` 已有：
- Skills
- Cron
- Team Memory
- Alerts

建议在 `Operations` 下新增一组 integrations 相关对象：

## 3.1 Integrations
表示外部能力域的总入口。

### 职责
- source 列表
- provider 分类
- 接入状态概览
- 入口不直接执行工具，只做集成健康与能力浏览

## 3.2 Sources
表示外部 source 对象。

### 职责
- source 名称
- source 类型（OpenAPI / GraphQL / MCP / Discovery）
- source 当前状态
- source 作用域
- source 下游工具数量

## 3.3 Tool Catalog
表示 source 暴露出来的工具目录。

### 职责
- 工具列表
- 工具 schema / 参数要求
- 工具所属 source
- 工具是否可用
- 工具是否需要 credential

## 3.4 Credential Health
表示 source / provider 所需凭证的健康状态。

### 职责
- credential 是否已绑定
- secret provider 类型
- 凭证是否失效
- 哪些 source 受影响

## 3.5 Provider Health
表示集成平台整体状态。

### 职责
- provider reachable / degraded / failed
- source 数量
- tool 数量
- auth 问题
- 近期失败情况

---

# 4. executor 能力到 Crazy UI 的映射

## 4.1 Source 模型映射

### executor
- Source
- Plugin-backed source definition
- Source lifecycle

### Crazy UI 中的表达
不要直接叫 “source record”，建议在 UI 中表达为：
- 集成源
- 外部来源
- 接入对象

推荐 UI 映射：
- `Operations > Integrations > Sources`

---

## 4.2 Tool 模型映射

### executor
- tool catalog
- source-derived tool definitions
- invoke-capable tool registry

### Crazy UI 中的表达
不要直接把整个产品语言切成 executor 风格，建议表达为：
- 外部工具目录
- 可调用能力
- 集成工具清单

推荐 UI 映射：
- `Operations > Integrations > Tool Catalog`

---

## 4.3 Secret / Credential 模型映射

### executor
- secret providers
- scoped credentials
- provider bindings

### Crazy UI 中的表达
建议表达为：
- 凭证健康
- 连接凭据
- 接入密钥状态

推荐 UI 映射：
- `Operations > Integrations > Credential Health`

---

## 4.4 MCP / Host 模型映射

### executor
- MCP host
- local/cloud/stdio MCP surfaces

### Crazy UI 中的表达
建议表达为：
- 协议接入层
- MCP 接入能力
- 外部能力网关

推荐 UI 映射：
- `Operations > Integrations > Provider Health`
- 或单独的 MCP provider 区块

---

## 4.5 Execution 模型映射

### executor
- Execution engine
- sandbox runtime

### Crazy 中的使用边界
第一阶段不做主页面入口，只作为后续“外部自动化执行面”的保留能力。

建议先不做独立 UI，只在：
- tool detail
- operator automation
- future workflow actions
中逐步接入。

---

# 5. 推荐优先接入的 executor 包

## 第一优先级（建议第一阶段就评估/接入）

### `packages/core/sdk`
用途：
- capability substrate 核心抽象

### `packages/plugins/openapi`
用途：
- OpenAPI source onboarding
- 最容易形成直观看得见的价值

### `packages/plugins/graphql`
用途：
- GraphQL source onboarding

### `packages/plugins/mcp`
用途：
- MCP source / capability integration

### `packages/plugins/file-secrets`
用途：
- 本地 secret provider 起步最快

### `packages/plugins/keychain`
用途：
- 如果 Crazy 继续偏本地 operator 模式，非常适合

### `packages/hosts/mcp`
用途：
- 作为统一 capability gateway 的基础设施

---

## 第二优先级（视需求接入）

### `packages/plugins/google-discovery`
场景：
- Google 生态 source 接入需求

### `packages/plugins/onepassword`
场景：
- 企业级凭证管理

### `packages/plugins/workos-vault`
场景：
- hosted / multi-tenant 凭证体系

### `packages/core/execution`
场景：
- 需要 external-tool orchestration 时再接

### `packages/kernel/runtime-quickjs`
场景：
- 本地 external execution sandbox

---

## 不建议第一阶段接入的

### `apps/local`
### `apps/cloud`
### `packages/react`

原因：
- 这些承载的是 executor 自己的产品壳
- Crazy 不应借壳，只应借能力

---

# 6. 第一阶段技术实现方式建议

## 6.1 接入方式

### 推荐模式：sidecar / capability service
Crazy 不嵌入 executor 全 UI，而是：
- 在 Crazy 中新增 integrations surface
- Crazy 调 executor 提供的 source/tool/secret 数据
- Crazy 继续自己渲染 UI 和 IA

即：
- Crazy = product shell
- executor = capability backend/substrate

---

## 6.2 最小桥接 API 范围

第一阶段只桥接以下查询型能力：

### A. Sources
- 列表
- 类型
- 状态
- 作用域
- 关联工具数

### B. Tools
- source 下工具列表
- 工具 schema 摘要
- 工具是否可调用

### C. Credentials
- credential/provider 状态
- 哪些 source 缺失凭证

### D. Provider health
- provider reachable / degraded / failed

> 第一阶段不先桥接写操作，不先接 tool invoke。

---

## 6.3 Crazy 页面落点建议

### `Operations` 页面新增区块

#### 1. Integrations 概览卡
- 外部接入源数量
- 活跃 provider 数量
- 异常 provider 数量
- 工具总数

#### 2. Sources 列表
- source 名称
- 类型
- 状态
- 作用域
- 工具数量

#### 3. Tool Catalog 面板
- 当前选中 source 的工具列表
- 工具 schema 简报

#### 4. Credential Health 面板
- 缺失凭证的 source
- credential provider 类型
- auth 错误

#### 5. Provider Health 面板
- MCP / OpenAPI / GraphQL provider 健康态

---

# 7. 明确不要做的事情

## 7.1 不要让 executor 接管 Crazy 的主模型
不迁移：
- Runtime
- Governance
- Collaboration
主对象语义

## 7.2 不要把 executor 的 UI 直接嵌进 Crazy 当主界面
最多借：
- 组件思路
- capability surface pattern

## 7.3 不要第一阶段就接 execution engine
因为这样会过早扩范围。

第一阶段只做：
- source
- tool catalog
- secret
- provider health

---

# 8. 第一阶段验收标准

当以下条件成立时，说明 `Operations × executor` 第一期接入成立：

## 业务层
- Crazy 的产品定位没有变化
- Runtime / Governance / Collaboration 没有被 executor 侵入

## 技术层
- source/tool/secret/provider 数据能被 Crazy 拉取
- Crazy 仍自己控制 UI 和 IA
- 没有引入新的真相源冲突

## UI 层
- `Operations` 下能看到：
  - Integrations
  - Sources
  - Tool Catalog
  - Credential Health
  - Provider Health
- 用户不会误以为这是另一个独立产品

---

# 9. 推荐的下一步文档

如果要继续进入实施前规划，建议再产出一份：

## `Crazy Operations Integrations UI/IA Spec`

内容包括：
- `Operations` 页里新增哪几个 object family
- 左侧对象树如何容纳 integrations
- 列表/详情/状态卡怎么排布
- source / tool / credential / provider 各自的最小工作面是什么

这样就能把这份接入方案继续推进到真正可开发的页面规格阶段。
