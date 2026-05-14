# CrazyAgentsManage × executor：能力借用与底座适配分析

## 文档目的

本文档汇总对 `D:/opensource/executor` 项目的深度技术分析，并结合 `E:/CrazyAgentsManage` 当前已明确的产品定位，回答以下问题：

1. `executor` 是否适合作为 `CrazyAgentsManage` 的完整底座？
2. 如果不适合，哪些能力可以借用？
3. 借用这些能力时，应该如何落地，风险最低？
4. 如果进入实施阶段，应该先接哪些包、不要接哪些包？

本文档聚焦技术与产品适配分析，不涉及代码修改。

---

# 1. 总结结论

## 1.1 一句话结论

`executor` **不适合**作为 `CrazyAgentsManage` 的**完整产品底座**，但**非常适合**作为其 **部分能力底座（capability substrate）**。

最推荐的方式不是：
- 把 Crazy 重构成 executor
- 或让 executor 接管 Crazy 的主产品模型

而是：

> **让 Crazy 保持自己的产品壳、运行时真相、治理真相和协作闭环；把 executor 下沉成 integrations / tools / secrets / plugin / MCP / optional execution 的能力层。**

## 1.2 结论分级

- **Full foundation / base**：不推荐
- **Partial capability substrate**：强推荐
- **Reference only**：不够，应高于参考、低于底座

---

# 2. CrazyAgentsManage 当前定位与硬边界

## 2.1 Crazy 的产品身份

`CrazyAgentsManage` 当前不是通用 agent playground，也不是单纯的 Hermes WebUI 壳，而是一个：

> **Hermes-hosted FlowMind operating product**

它的主轴是：
- HermesAgent = runtime host
- FlowMind = governance / canonical truth layer
- CrazyAgentsManage = operator product layer

## 2.2 Crazy 的一级 IA 是固定的

- Overview
- Runtime
- Operations
- Governance
- Collaboration

这些不是普通页面，而是产品职责分区。

## 2.3 Crazy 当前最不能失去的东西

以下是不得被 executor 替代的部分：

### Runtime truth
- session
- trace
- token telemetry
- tool usage
- agent runtime state

### Governance truth
- candidate
- truth
- review
- provenance
- drift / blocked

### Collaboration truth
- handoff package
- runtime snapshot
- closeout
- repo writeback
- harness trace

### 产品壳与仓库事实层
- Overview / Runtime / Operations / Governance / Collaboration 五分区
- docs / roadmap / harness 的 repo truth
- closeout / writeback discipline

---

# 3. executor 项目是什么

`executor` 是一个平台型 monorepo，而不是单一产品应用。

## 3.1 它的核心产品模型

它更像是：

> **AI agent execution + integration platform**

核心对象是：
- Tool
- Source
- Secret
- Scope
- Plugin
- Execution

## 3.2 它的主要宿主

`apps/*` 里有：
- `apps/cli`：CLI / daemon / stdio MCP
- `apps/local`：本地 Web UI + API + MCP
- `apps/cloud`：Cloudflare Workers 托管版
- `apps/desktop`：Electron 桌面壳
- `apps/marketing`：Astro 官网/文档站

## 3.3 它的平台核心

- `packages/core/sdk`：Executor 抽象
- `packages/core/execution`：执行引擎
- `packages/core/api`：HTTP API 层
- `packages/plugins/*`：集成插件层
- `packages/hosts/mcp`：MCP host 层
- `packages/kernel/*`：QuickJS / dynamic worker 等 runtime backend

---

# 4. 为什么 executor 不适合做 Crazy 的完整底座

## 4.1 业务问题域不一致

### Crazy 的问题域
Crazy 解决的是：
- Hermes runtime observability
- operator action surfaces
- governance truth workflow
- collaboration closeout/writeback
- repo truth durability

### executor 的问题域
executor 解决的是：
- source onboarding
- tool catalog
- plugin composition
- secret/provider abstraction
- sandboxed execution
- MCP/HTTP host exposure

### 结论
executor 更像“能力平台”，Crazy 更像“运营治理产品”。

---

## 4.2 核心对象模型不在同一层级

Crazy 的关键对象：
- session
- cron job
- graph node / truth candidate / review item
- handoff package / closeout artifact

executor 的关键对象：
- tool
- source
- secret
- plugin
- execution

executor 的模型可以作为 Crazy 的下层能力模型，但不能直接替代 Crazy 的上层产品模型。

---

## 4.3 真相源不能被替代

Crazy 的三层真相源必须保留：
- Hermes runtime truth
- FlowMind governance truth
- repo truth / closeout truth

executor 无法天然承接这些语义边界。

如果让 executor 接管这些模型，会出现：
- 双真相源
- candidate/truth 混淆
- closeout/writeback 语义丢失

---

# 5. executor 最适合作为哪些能力底座

---

## 5.1 Integration Layer

### 可借能力
- OpenAPI source 接入
- GraphQL source 接入
- MCP source 接入
- Google Discovery source 接入
- tool catalog 生成

### Crazy 中的落点
建议挂在：
- `Operations > Integrations`
- `Operations > Sources`
- `Operations > External Tools`

### 价值
这是 `executor` 最值得借的层之一，也是 Crazy 最不值得自己重造的一层。

### 判断
**Adopt / Adapt**

---

## 5.2 Execution Layer

### 可借能力
- 统一 tool invocation
- sandboxed execution（QuickJS）
- pause / resume / elicitation 机制

### Crazy 中的落点
只用于：
- external-tool orchestration
- operator automation
- custom integration glue

### 不要替代
- Hermes runtime session
- Crazy trace / token / runtime truth
- governance / collaboration 主流程

### 判断
**Adapt**

---

## 5.3 Plugin / Extensibility Layer

### 可借能力
- plugin contract
- source/tool/secret/connections extensibility
- route / UI extension hooks

### Crazy 中的落点
作为 Crazy 的：
- integration plugin substrate
- capability extension plane

### 不要让它定义 Crazy 的产品 IA
Crazy UI 应继续由 Crazy 的产品模型驱动。

### 判断
**Adopt / Adapt**

---

## 5.4 Storage / Secrets Layer

### 可借能力
- secret provider abstraction
- file / keychain / 1Password / vault provider
- scoped storage abstraction

### Crazy 中的落点
- source credentials
- provider auth bindings
- integration metadata persistence

### 不要替代
- Hermes runtime state
- FlowMind truth
- repo truth

### 判断
**Adopt / Adapt**

---

## 5.5 MCP Layer

### 可借能力
- local MCP host
- cloud MCP host
- stdio MCP host
- worker/DO session transport

### Crazy 中的落点
- 外部能力平面的统一入口
- `Operations` 域的一部分能力底座
- integration sidecar

### 不建议
- 让 MCP 成为 Crazy 的主产品入口

### 判断
**Adopt / Adapt**

---

## 5.6 UI / Product Layer

### 可借能力
- 局部组件思路
- 某些 layout / form / catalog 管理方式

### 不建议直接采用
- `apps/local`
- `apps/cloud`
- `packages/react` 的整套产品壳

因为它们承载的是 executor 自己的产品心智，不是 Crazy 的运营治理心智。

### 判断
**Avoid（整体） / Partial Adapt（零件）**

---

# 6. Adopt / Adapt / Avoid 决策矩阵

| 能力层 | 结论 | Crazy 中的落点 | 备注 |
|---|---|---|---|
| Integration layer | Adopt / Adapt | Operations / Integrations / Sources | 最适合优先落地 |
| Execution layer | Adapt | external execution plane | 不能替代 Hermes runtime |
| Plugin/extensibility | Adopt / Adapt | capability substrate | 适合中长期扩展 |
| Storage/secrets | Adopt / Adapt | credentials / source metadata | 不接管 repo/runtime truth |
| MCP layer | Adopt / Adapt | external capability gateway | 对外接入价值高 |
| UI/product layer | Avoid | 不作主壳 | 最多借组件，不借产品形态 |

---

# 7. Crazy × executor 技术接入蓝图

## 7.1 接入策略

### 总原则
> Crazy 保持 product shell 和 truth workflow；executor 作为 external capability plane 挂进去。

### 最低风险路径
**先接 Operations，再决定是否接 execution。**

---

## 7.2 分阶段接入路径

### Phase 0：边界冻结
先在 Crazy 内部冻结：
- 什么属于 Crazy 主模型
- 什么属于 executor 能力底座

冻结后：
- Crazy 不迁移 runtime truth
- Crazy 不迁移 governance truth
- Crazy 不迁移 collaboration truth

---

### Phase 1：Operations 内接入 executor 能力层

目标：只在 `Operations` 里引入 executor 能力。

建议新增/增强的子模块：
- Integrations
- Sources
- Tool Catalog
- Credential Health
- Provider Health

可对接 executor 的能力：
- `packages/plugins/openapi`
- `packages/plugins/graphql`
- `packages/plugins/mcp`
- `packages/plugins/google-discovery`
- `packages/plugins/file-secrets`
- `packages/plugins/keychain`
- `packages/plugins/onepassword`
- `packages/hosts/mcp`
- `packages/core/sdk`

Crazy 的 UI 表达应继续使用 Crazy 语言，不直接暴露 “executor source model” 的原始术语给最终用户。

---

### Phase 2：把 executor 作为外部工具平面

目标：让 Crazy 能消费 executor 产出的：
- source list
- tool catalog
- connection/secret 状态
- MCP-exposed capabilities

但 Crazy 仍自己负责：
- UI shell
- runtime diagnosis
- governance routing
- collaboration loop

---

### Phase 3：有选择地引入 execution engine

只有当你真的需要：
- operator automation
- external capability orchestration
- custom glue code execution

才建议接：
- `packages/core/execution`
- `packages/kernel/runtime-quickjs`

并且只用于 **external-tool execution plane**。

---

# 8. 包级落地清单（Package-level landing matrix）

| executor 包 / 目录 | Crazy 中建议落点 | 建议 | 说明 |
|---|---|---|---|
| `packages/core/sdk` | Operations capability substrate | Adopt / Adapt | 作为集成能力核心抽象 |
| `packages/core/execution` | external execution plane | Adapt | 仅用于外部工具编排 |
| `packages/core/api` | integration backend facade | Adapt | 若要服务化 executor 能力可借 |
| `packages/core/storage-core` | integration metadata persistence | Adapt | 只用于集成元数据 |
| `packages/core/storage-file` | local integration metadata / local secrets | Adapt | 本地模式优先 |
| `packages/core/storage-postgres` | hosted integration metadata | Adapt | 如果 Crazy 以后有 hosted 平台层 |
| `packages/plugins/openapi` | Operations > OpenAPI Sources | Adopt | 优先级最高 |
| `packages/plugins/graphql` | Operations > GraphQL Sources | Adopt | 很适合作为第二批 |
| `packages/plugins/mcp` | Operations > MCP Sources | Adopt | 和 Crazy 很契合 |
| `packages/plugins/google-discovery` | Operations > SaaS Discovery | Adapt | 看业务需要 |
| `packages/plugins/file-secrets` | local credential layer | Adopt | 最容易接入 |
| `packages/plugins/keychain` | desktop/local credential layer | Adopt | 很适合 Crazy 本地模式 |
| `packages/plugins/onepassword` | enterprise secret backend | Adapt | 后期引入 |
| `packages/plugins/workos-vault` | org/hosted secret backend | Adapt | 后期评估 |
| `packages/hosts/mcp` | external capability gateway | Adopt / Adapt | 很适合作为 sidecar host |
| `packages/kernel/runtime-quickjs` | optional external execution sandbox | Adapt | 不能替代 Hermes runtime |
| `packages/kernel/runtime-dynamic-worker` | hosted external execution | Adapt | 仅 cloud 场景评估 |
| `apps/local` | 不直接采用 | Avoid | 不要拿 executor UI 取代 Crazy |
| `apps/cloud` | 不直接采用 | Avoid | product shell 不匹配 |
| `packages/react` | 可借部分组件思路 | Partial Adapt | 不作主 UI 壳 |

---

# 9. 推荐阅读顺序（如果你要真正评估是否引入）

## 第一批：先看概念和边界
1. `D:/opensource/executor/README.md`
2. `D:/opensource/executor/vision.md`
3. `D:/opensource/executor/notes/research/product-model.md`
4. `E:/CrazyAgentsManage/docs/prd/hermesagent-hosted-flowmind-product-foundation.md`

目标：确认两个项目不是同类产品。

## 第二批：看 capability substrate
1. `D:/opensource/executor/packages/core/sdk/src/executor.ts`
2. `D:/opensource/executor/packages/core/sdk/src/plugin.ts`
3. `D:/opensource/executor/packages/plugins/openapi/README.md`
4. `D:/opensource/executor/packages/plugins/graphql/README.md`
5. `D:/opensource/executor/packages/plugins/mcp/README.md`

目标：判断能不能承接 Crazy 的 integration plane。

## 第三批：看 execution plane
1. `D:/opensource/executor/packages/core/execution/src/engine.ts`
2. `D:/opensource/executor/packages/core/execution/src/tool-invoker.ts`
3. `D:/opensource/executor/packages/kernel/runtime-quickjs/src/index.ts`

目标：判断是否接 external execution sandbox。

## 第四批：看 cloud/local 差异
1. `D:/opensource/executor/apps/local/src/server/executor.ts`
2. `D:/opensource/executor/apps/local/src/server/main.ts`
3. `D:/opensource/executor/apps/cloud/src/services/executor.ts`
4. `D:/opensource/executor/apps/cloud/src/services/execution-stack.ts`
5. `D:/opensource/executor/apps/cloud/src/api/request-scoped.ts`

目标：判断 Crazy 本地/远程模式与 executor 的宿主方式如何衔接。

---

# 10. 最终建议

## 不要做的事
- 不要把 Crazy 重构成 executor 的 UI / product shell
- 不要让 executor 接管 Crazy 的 runtime truth
- 不要让 executor 接管 FlowMind governance truth
- 不要让 executor 接管 collaboration closeout/writeback 模型

## 应该做的事
- 把 executor 作为 **Operations/Integrations capability substrate** 引入
- 先接 sources / tools / secrets / MCP
- 再决定是否引入 execution engine
- 始终让 Crazy 保持产品壳和主模型

## 最终一句话
> **executor 不是 CrazyAgentsManage 的产品底座，但它可以非常好地成为 Crazy 的集成与受控执行能力底座。**

---

# 11. 如果要进入实施前规划，下一步该做什么

最推荐的下一步不是直接改代码，而是先输出一份：

## `Crazy Operations × executor integrations` 接入方案

至少定义：
- Crazy 的 `Operations` 页里新增哪些对象
- executor 哪些包先接
- source/tool/secret 如何映射到 Crazy 的 UI 语言
- 哪些 API 先桥接，哪些留到第二阶段

这样才能在不破坏 Crazy 当前主产品结构的前提下，有秩序地吸收 executor 的能力。
