# Crazy Operations Integrations API/Boundary Spec

## 文档目的

本文档承接以下文档：
- `docs/design/executor-integration/capability-analysis.md`
- `docs/design/executor-integration/decision-summary.md`
- `docs/design/executor-integration/operations-integration-plan.md`
- `docs/design/executor-integration/operations-integrations-ui-ia-spec.md`

目标是把 `CrazyAgentsManage` 在 `Operations` 分区接入 `executor` 能力底座时，进一步收敛成：

- 明确的系统边界
- 可桥接的数据对象
- 推荐 API 形态
- Crazy UI 侧应消费的字段投影
- 哪些字段是 executor 原始真相，哪些字段是 Crazy 产品投影

本文档不直接定义代码实现，只定义接口边界与职责分层。

---

# 1. 边界总原则

## 1.1 系统职责划分

### CrazyAgentsManage 负责
- 产品壳与一级 IA
- Runtime / Governance / Collaboration 主模型
- operator-facing 交互系统
- external capability 的产品语义包装
- 将 executor 能力映射为 Crazy 的 Operations 对象

### executor 负责
- source onboarding
- tool catalog generation
- secret / provider abstraction
- MCP / OpenAPI / GraphQL / Discovery integration
- optional external execution substrate

## 1.2 不允许跨越的边界

executor **不应**：
- 直接定义 Crazy 的 Runtime truth
- 直接定义 Crazy 的 Governance truth
- 直接定义 Crazy 的 Collaboration truth
- 接管 Crazy 的产品路由与一级 IA

Crazy **不应**：
- 重造 source / tool / secret / plugin substrate
- 把外部集成能力重新硬编码进自身模型层

---

# 2. Integration 边界模型

## 2.1 核心对象层次

### executor 原始对象（source-of-capability truth）
- Source
- Tool
- Secret / Credential binding
- Provider Health
- Plugin / Integration Type

### Crazy UI 投影对象（operator-facing projection）
- Integration Source
- External Tool
- Credential Health Record
- Provider Health Record
- Integration Cluster Summary

注意：
- Crazy UI 不直接暴露 executor 的内部实现术语
- Crazy 对 executor 数据做轻量投影，但不重写底层真相

---

# 3. 推荐 API 边界

## 3.1 第一阶段：只读 API

第一阶段只桥接查询型接口，不做写操作。

### A. Source List API

#### executor 侧能力
返回 source 列表及最小状态信息。

#### Crazy 建议消费对象
```ts
interface IntegrationSourceView {
  id: string;
  name: string;
  type: 'openapi' | 'graphql' | 'mcp' | 'discovery' | string;
  scope: string;
  status: 'healthy' | 'degraded' | 'missing-auth' | 'disabled' | 'failed' | 'unknown';
  toolCount: number;
  provider?: string;
}
```

#### Crazy UI 落点
- `Operations > Integrations > Sources`
- 左树 object pool
- 中栏 source list
- 右栏 source detail

---

### B. Tool Catalog API

#### executor 侧能力
给定 source，返回对应工具目录与 schema 摘要。

#### Crazy 建议消费对象
```ts
interface ExternalToolView {
  id: string;
  sourceId: string;
  name: string;
  summary?: string;
  requiresAuth: boolean;
  status: 'available' | 'auth-required' | 'disabled' | 'invalid-schema' | 'unknown';
  schemaSummary?: string;
}
```

#### Crazy UI 落点
- `Operations > Integrations > Tool Catalog`
- source detail 下的子面板
- tool list / detail rail

---

### C. Credential Health API

#### executor 侧能力
返回 source/provider 的 credential 绑定状态。

#### Crazy 建议消费对象
```ts
interface CredentialHealthView {
  id: string;
  provider: string;
  targetType: 'source' | 'provider' | 'tool';
  targetId: string;
  status: 'healthy' | 'missing' | 'expired' | 'invalid' | 'unknown';
  lastCheckedAt?: string;
  impactCount?: number;
}
```

#### Crazy UI 落点
- `Operations > Integrations > Credential Health`
- source / provider 详情右栏

---

### D. Provider Health API

#### executor 侧能力
返回 integration provider 的整体状态。

#### Crazy 建议消费对象
```ts
interface ProviderHealthView {
  id: string;
  provider: string;
  status: 'reachable' | 'degraded' | 'failed' | 'unknown';
  sourceCount: number;
  toolCount: number;
  issueSummary?: string;
}
```

#### Crazy UI 落点
- `Operations > Integrations > Provider Health`
- provider card / summary panel

---

# 4. Crazy 侧推荐 API façade

## 4.1 不要让 UI 直接到处消费 executor 原始接口
建议增加 Crazy 自己的 façade 层，作用是：
- 统一 operator-facing 术语
- 做轻量字段投影
- 保留未来替换 executor 能力层的余地

也就是说：

### 不推荐
```text
React UI -> executor raw API
```

### 推荐
```text
React UI -> Crazy Operations façade API -> executor capability API
```

---

## 4.2 推荐 façade endpoints（建议命名）

### 1. `/api/operations/integrations/sources`
返回 `IntegrationSourceView[]`

### 2. `/api/operations/integrations/tools?sourceId=...`
返回 `ExternalToolView[]`

### 3. `/api/operations/integrations/credentials`
返回 `CredentialHealthView[]`

### 4. `/api/operations/integrations/providers`
返回 `ProviderHealthView[]`

### 5. `/api/operations/integrations/summary`
返回 `IntegrationClusterSummary`

```ts
interface IntegrationClusterSummary {
  sourceCount: number;
  healthySourceCount: number;
  degradedSourceCount: number;
  toolCount: number;
  missingCredentialCount: number;
  providerCount: number;
  failedProviderCount: number;
}
```

---

# 5. 字段投影原则

## 5.1 executor 字段直接透传的部分
适合透传：
- `id`
- `name`
- `type`
- `scope`
- `status`
- `provider`
- `toolCount`
- `sourceCount`
- `schemaSummary`
- `requiresAuth`

## 5.2 Crazy UI 应重新命名/包装的部分
例如：
- Source → 集成源
- Tool → 外部工具 / 可调用能力
- Secret binding → 凭证健康
- Provider issue → 接入异常 / 连接健康问题

## 5.3 不要在 Crazy UI 层伪造的内容
不要伪造：
- source ownership
- execution truth
- source-level success semantics if unavailable
- credential “safe to use” semantics if executor only knows binding status

---

# 6. 写操作边界（第二阶段再考虑）

## 6.1 第一阶段不做的写操作
- source create/import
- credential bind/update
- provider repair
- tool invoke

## 6.2 第二阶段可以开放的写操作
在只读接入稳定后，再考虑：

### A. Source onboarding
- import source
- enable / disable source

### B. Credential binding
- create / update binding
- rotate secret reference

### C. Tool invoke（可选）
只在 external execution plane 接入后考虑。

---

# 7. 错误与状态处理边界

## 7.1 executor 错误
executor 返回的集成错误，在 Crazy UI 中要投影成：
- missing credential
- source degraded
- provider failed
- schema invalid

## 7.2 Crazy 不要重写的错误含义
不要把 executor 的：
- auth failure
- provider unreachable
- schema issue
- integration disabled

重写成 Crazy Runtime / Governance / Collaboration 的错误语义。

---

# 8. UI 层与 API 边界对照

| UI 区块 | Crazy façade endpoint | 原始能力来源 |
|---|---|---|
| Integrations Summary | `/api/operations/integrations/summary` | executor source/tool/provider/credential aggregate |
| Sources list | `/api/operations/integrations/sources` | executor sources |
| Tool Catalog | `/api/operations/integrations/tools?sourceId=` | executor tools |
| Credential Health | `/api/operations/integrations/credentials` | executor secrets / bindings |
| Provider Health | `/api/operations/integrations/providers` | executor provider status |

---

# 9. 最低风险实施建议

## 第一步
只读桥接：
- summary
- sources
- tools
- credentials
- providers

## 第二步
Crazy `Operations` 主页面增加对应 object family

## 第三步
在 source detail / provider detail 中增加更深 detail rail

## 第四步
确认 UI 语言已稳定后，再考虑接入写操作

---

# 10. 验收标准

## API 边界
- Crazy UI 不直接依赖 executor 内部对象细节
- Crazy 通过 façade 层消费 executor 能力

## 数据模型
- 不出现新的真相源冲突
- source/tool/credential/provider 与 Runtime/Governance/Collaboration 分离清楚

## UI
- `Operations` 中可见 integrations family
- 左树 / 中栏 / 右栏能承接 integrations object model
- 用户不会误以为 executor 是另一个主产品

---

# 11. 下一步建议

如果继续推进实施前文档，最合理的下一份应该是：

## `Crazy Operations Integrations Delivery Plan`

它要回答：
- 第一阶段先接哪些 executor 包
- Crazy 侧 façade 先提供哪些接口
- UI 先落哪些 object family
- 如何验证不破坏 Crazy 当前主产品逻辑
