# Crazy × executor：1页决策摘要

## 一句话结论

`executor` **不适合**作为 `CrazyAgentsManage` 的完整产品底座，
但**非常适合**作为其 **外部集成与受控执行能力底座**。

> 建议采用策略：**Adopt capabilities, not identity**。

也就是说：
- Crazy 保持自己的产品壳、运行态真相、治理真相和协作闭环
- executor 下沉为：
  - source / integration substrate
  - tool catalog substrate
  - secret / credential substrate
  - MCP substrate
  - optional execution substrate

---

## 为什么不能把 executor 当完整底座

### 1. 产品定位不一致

### Crazy 的定位
- Hermes-hosted FlowMind operating product
- 核心是：
  - Runtime
  - Operations
  - Governance
  - Collaboration
- 目标是：让 Hermes 运行态、FlowMind 治理真值、协作闭环和仓库事实形成统一 operator product

### executor 的定位
- AI execution + integration platform
- 核心是：
  - Tool
  - Source
  - Secret
  - Plugin
  - Execution
- 目标是：统一接入、统一调用、统一扩展和统一执行外部能力

### 结论
- executor 更像“能力平台”
- Crazy 更像“运营治理产品”
- 两者不是同一层级的问题域

---

## executor 最适合承接 Crazy 的哪些能力

### 强推荐优先接入

#### 1. Integration Layer
- OpenAPI
- GraphQL
- MCP
- Google Discovery
- source onboarding
- tool catalog generation

#### 2. Storage / Secrets Layer
- file / keychain / 1Password / vault secret provider
- scoped credentials
- provider bindings

#### 3. Plugin / Extensibility Layer
- source/tool/secret/connections 扩展契约
- plugin substrate

#### 4. MCP Layer
- local / stdio / hosted MCP host
- 作为 external capability gateway

#### 5. Optional Execution Layer
- 仅用于 external tool orchestration
- 不替代 Hermes runtime

---

## 明确不要让 executor 接管的部分

### 不要替代 Crazy 的产品壳
- 不替代 Crazy 的五个一级 IA
- 不替代 Crazy 的 WebUI / operator mental model

### 不要替代 Runtime truth
- session
- trace
- token telemetry
- tool usage
- agent runtime state

### 不要替代 Governance truth
- candidate
- truth
- review
- provenance
- drift / blocked

### 不要替代 Collaboration truth
- handoff package
- runtime snapshot
- closeout
- repo writeback
- harness trace

---

## 最小风险落地策略

### Phase 1：只接 Operations
把 executor 先接进 Crazy 的 `Operations` 域：
- Integrations
- Sources
- Tool Catalog
- Credential Health
- Provider Health

### Phase 2：只让 Crazy 消费 executor 的能力目录
Crazy 调 executor：
- source list
- tool catalog
- secret/connection status
- MCP-exposed capabilities

### Phase 3：有选择地引入 execution engine
只用于：
- external-tool orchestration
- operator automation
- integration glue code

### 不做的事
- 不把 executor execution engine 变成 Crazy 的主运行时
- 不把 governance / collaboration / repo truth 迁进去

---

## 最终建议

### 推荐决策

| 方向 | 建议 |
|---|---|
| Full foundation | ❌ 不建议 |
| Partial capability substrate | ✅ 强建议 |
| Reference only | ⚠️ 不够 |

### 最推荐的一句话

> **把 executor 作为 CrazyAgentsManage 的 Operations / Integrations capability substrate，而不是作为 Crazy 本身的产品底座。**

---

## 下一步

如果进入实施前规划，最推荐的下一份文档是：

### `Crazy Operations × executor integrations` 接入方案

至少定义：
- Crazy 的 Operations 里新增哪些对象
- executor 哪些包先接
- source/tool/secret 如何映射到 Crazy 的 UI 语言
- 哪些接口先桥接，哪些留到第二阶段
