# Feedback / Context-Pack 消费状态

> 日期: 2026-05-03  
> 类型: 消费证据普查（CrazyAgentsManage 侧视角）  
> 触发: 补收口任务（兼容矩阵条件项 #6）  
> 参照链路: `docs/02-engineering/harness/hermes-flowmind-link-manifest-v1.json` contracts.feedback / contracts.contextPack

---

## 1. 分类定义

| 分类 | 含义 |
|---|---|
| **已消费** | Crazy 侧存在入口脚本/流程，能读取该端点数据并将其用于运营/开发决策 |
| **仅接口存在** | FlowMind 端点可达（HTTP 返回非 404），但 Crazy 侧没有任何消费入口 |
| **未消费** | 端点不可达或 Crazy 侧无任何相关代码/流程引用 |

---

## 2. Feedback 消费状态

### 2.1 问题回答

| 问题 | 回答 |
|---|---|
| Crazy 是否真的在某条主链里读取了 `bridge/feedback/:instanceId`？ | **否** |
| 入口脚本是什么？ | **无主线消费入口**。仓库存在 `scripts/flowmind_handshake_smoke.py` 的探测性调用，但没有持续消费 `bridge/feedback/:instanceId` 的运营/开发流程 |
| 消费到哪个状态面？ | **无消费** |
| 当前缺什么？ | 缺少：① 正确的 x-instance-token；② 消费入口脚本/流程；③ 反馈数据到运营决策面的映射 |
| 属于设计缺口、实现缺口还是运行缺口？ | **实现缺口**。FlowMind manifest 已定义该契约（§1.1 contracts.feedback），Crazy 侧尚未实现消费端 |

### 2.2 端点状态

| 项 | 值 |
|---|---|
| 端点 | `GET /api/bridge/feedback/:instanceId` |
| auth 要求 | `x-instance-token`（manifest contracts.feedback） |
| HTTP 状态 (2026-05-03) | **401 Unauthorized** |
| 路由匹配 | ✅ 是（401 证明路由存在，非 404） |
| Bearer token 可用？ | ❌ 不适用，端点使用 `x-instance-token` 而非 Bearer |

### 2.3 结论

> **仅接口存在**。端点存活但 Crazy 侧无消费入口。待实现。

---

## 3. Context-Pack 消费状态

### 3.1 问题回答

| 问题 | 回答 |
|---|---|
| Crazy 是否真的在某条主链里读取了 `bridge/context-pack`？ | **否** |
| 入口脚本 / 页面 / 流程是什么？ | **无主线消费入口**。仓库存在 `scripts/flowmind_handshake_smoke.py` 的探测性调用，但没有持续消费 `bridge/context-pack` 的页面、脚本或运营流程 |
| 消费到哪个面？ | **无消费** |
| 当前缺什么？ | 缺少：① 正确的 x-instance-token；② 消费入口；③ context-pack 语义定义与 Crazy 运营面的映射 |
| 属于设计缺口、实现缺口还是运行缺口？ | **设计+实现缺口**。契约已定义（manifest contracts.contextPack），但 Crazy 侧未定义"需要什么样的 context"，也未实现消费端 |
| 是否只是"接口存在但无人消费"？ | **是**。精确描述：FlowMind 端点存在且可达，Crazy 侧无任何消费逻辑 |

### 3.2 端点状态

| 项 | 值 |
|---|---|
| 端点 | `POST /api/bridge/context-pack` |
| auth 要求 | `x-instance-token`（manifest contracts.contextPack） |
| HTTP 状态 (2026-05-03) | **401 Unauthorized** |
| 路由匹配 | ✅ 是（401 证明路由存在，非 404） |
| Bearer token 可用？ | ❌ 不适用 |

### 3.3 结论

> **仅接口存在**。端点存活但 Crazy 侧无消费入口。待实现。

---

## 4. 汇总

| 维度 | 状态 | 分类 | 阻塞项 |
|---|---|---|---|
| Feedback | 无人消费 | **仅接口存在** | ① x-instance-token；② 消费脚本；③ 反馈→运营映射 |
| Context-Pack | 无人消费 | **仅接口存在** | ① x-instance-token；② 消费入口；③ context 语义定义 |

---

## 5. 与当前 handoff generator 的关系

> 当前 `generate_hermes_handoff.py` **只消费 `bridge/truth`**，不读取 feedback 或 context-pack。  
> 这是正确的分层——handoff packet 聚焦 truth read surface，feedback/context-pack 属于独立消费链路。  
> 如需增强 handoff packet（例如在 packet 中附带 feedback summary），应在 generator 中增加可选的 feedback/context-pack 读取参数，而非混入 truth read 逻辑。
