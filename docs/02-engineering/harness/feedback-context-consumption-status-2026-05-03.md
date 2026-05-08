# Feedback / Context-Pack 消费状态

> 日期: 2026-05-08（更新自 2026-05-03 初版）
> 类型: 消费证据普查 + 口径纠偏（CrazyAgentsManage 侧视角）
> 触发: 补收口任务（兼容矩阵条件项 #6）  
> 参照链路: `docs/02-engineering/harness/hermes-flowmind-link-manifest-v1.json` contracts.feedback / contracts.contextPack

---

## 1. 分类定义

| 分类 | 含义 |
|---|---|
| **已消费** | Crazy 侧存在入口脚本/流程，能读取该端点数据并将其用于运营/开发决策 |
| **部分消费** | Crazy 侧已有脚本级消费入口和运营字段投影，但尚未形成统一页面/产品化主链 |
| **探测性消费** | Crazy 侧存在 handshake/smoke/probe 调用，但没有 durable 主线消费入口 |
| **仅接口存在** | FlowMind 端点可达（HTTP 返回非 404），但 Crazy 侧没有任何消费入口或探测入口 |
| **未消费** | 端点不可达或 Crazy 侧无任何相关代码/流程引用 |

---

## 2. Feedback 消费状态

### 2.1 问题回答

| 问题 | 回答 |
|---|---|
| Crazy 是否真的在某条主链里读取了 `bridge/feedback/:instanceId`？ | **是，但层级仍停留在脚本级主链。** `scripts/daily-promise-review.py` 已真实读取并汇总 feedback；尚未形成统一页面/产品化消费面 |
| 入口脚本是什么？ | 主入口是 `scripts/daily-promise-review.py`；此外 `scripts/flowmind_handshake_smoke.py` 也会做一次 feedback pull probe |
| 消费到哪个状态面？ | 已进入承诺审查主表 `备注` 文本汇总、Trace 子表 `module=feedback` 事件写回，以及 `latest_feedback_* / notes_text` 这类运营投影 |
| 当前缺什么？ | 缺少：① 统一页面/产品化消费入口；② `feedback pull` / `feedback record` 分离后的契约口径同步；③ 持续运行证据与验收口径补齐 |
| 属于设计缺口、实现缺口还是运行缺口？ | **产品化消费缺口 + 契约文档漂移**。不能再简单归类为“无人消费” |

### 2.2 端点状态

| 项 | 值 |
|---|---|
| pull 端点 | `GET /api/bridge/feedback/:instanceId` |
| record 端点 | `POST /api/bridge/feedback` |
| pull auth（代码口径，2026-05-08） | `ui_bearer` **或** `x-instance-token`。FlowMind `packages/mcp-server/src/api/bridge-routes.ts` 中 `GET /bridge/feedback/:instanceId` 走 `truthReadAuth` |
| record auth（代码口径，2026-05-08） | `x-instance-token` |
| 历史冒烟 (2026-05-03) | **401 Unauthorized**；该次结果只能证明当时鉴权生效，不能再据此推出“feedback 无消费入口” |
| 路由匹配 | ✅ 是 |
| Bearer token 可用？ | ✅ **对 pull 端点可用**；❌ 对 record 端点不适用 |

### 2.3 结论

> **部分消费**。Crazy 已有脚本级 feedback pull、事件归一化与运营字段写回；但还没有统一页面/产品化消费面，也缺持续运行证据面。

---

## 3. Context-Pack 消费状态

### 3.1 问题回答

| 问题 | 回答 |
|---|---|
| Crazy 是否真的在某条主链里读取了 `bridge/context-pack`？ | **否** |
| 入口脚本 / 页面 / 流程是什么？ | **无主线消费入口**。当前只见 `scripts/flowmind_handshake_smoke.py` 的 probe 调用，没有持续消费 `bridge/context-pack` 的页面、脚本或运营流程 |
| 消费到哪个面？ | **无消费** |
| 当前缺什么？ | 缺少：① durable 消费入口；② context-pack 字段到 handoff / 日审 / 运营页面的映射；③ 何时请求、谁负责消费、消费后写到哪里 的治理口径；④ 一个冻结后的 page-facing 主链顺序 |
| 属于设计缺口、实现缺口还是运行缺口？ | **设计+实现缺口**。契约已定义（manifest contracts.contextPack），但 Crazy 侧未定义"需要什么样的 context"，也未实现消费端 |
| 是否只是"接口存在但无人消费"？ | **不完全是**。更准确的说法是：已有 probe 调用，但仍无 durable 主线消费逻辑 |

### 3.2 端点状态

| 项 | 值 |
|---|---|
| 端点 | `POST /api/bridge/context-pack` |
| auth 要求 | `x-instance-token`（FlowMind `packages/mcp-server/src/api/bridge-routes.ts`） |
| 历史冒烟 (2026-05-03) | **401 Unauthorized**；说明当时接口存在但缺有效 token，不构成主线消费证明 |
| 路由匹配 | ✅ 是 |
| Bearer token 可用？ | ❌ 不适用 |

### 3.3 结论

> **探测性消费**。当前只有 handshake smoke 级调用；没有 durable 主线消费入口，也没有稳定运营投影。

---

## 4. 汇总

| 维度 | 状态 | 分类 | 阻塞项 |
|---|---|---|---|
| Feedback | 已有脚本级消费与运营字段投影 | **部分消费** | ① 统一产品化入口；② 契约口径与 manifest 同步；③ 持续运行证据 |
| Context-Pack | 仅有 handshake/probe 调用 | **探测性消费** | ① durable 消费入口；② context 语义定义；③ 消费后写回/展示规则 |

---

## 5. 与当前 handoff generator 的关系

> 当前 `generate_hermes_handoff.py` **只消费 `bridge/truth`**，不读取 feedback 或 context-pack。
> 这是合理分层：handoff packet 主读面仍应聚焦 truth read；feedback 已在日审脚本形成脚本级消费，context-pack 仍缺独立 durable consumer。
> 如需增强 handoff packet（例如在 packet 中附带 feedback summary 或 context-pack 摘要），应在 generator 中增加可选读取参数，而不是回退成混杂 truth/feedback/context-pack 的单一自由文本入口。

---

## 6. 当前冻结的补强顺序

针对 `context-pack`，Crazy 当前冻结的下一优先主线不是：

1. 让 `generate_hermes_handoff.py` 直接直连 `POST /bridge/context-pack`
2. 直接新开 instance-level context 页面

而是：

> **先补强 Crazy `/api/runtime/handoffs?recordId=...` 的 page-facing `contextSummary`。**

冻结点如下：

1. `/api/runtime/handoffs?recordId=...`
   - 作为当前 page-facing canonical surface
2. `/api/flowmind/records/:recordId/replay`
   - 只作为 upstream replay adapter
3. `generate_hermes_handoff.py`
   - 未来只能继承该主链结果，作为 downstream distributor
4. instance-level context surface
   - 当前不立项
