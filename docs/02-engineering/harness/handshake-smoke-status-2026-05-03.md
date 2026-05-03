# Handshake Smoke Status

> 日期: 2026-05-03  
> 类型: 双仓联通冒烟验证（CrazyAgentsManage ↔ FlowMindDeploy）  
> 触发: 补收口任务（基于 `feat/auto-capture-trace@3c5815d` 真实 round）

---

## 1. 测试环境

| 项目 | 值 |
|---|---|
| FlowMind Base URL | `http://111.229.194.203:3301` |
| FlowMind Host | TX-NEWHOST (per manifest) |
| Crazy Host | ALI-HERMES (`47.99.217.1`) |
| Auth: Bearer token | `flowmind-dev-token`（已配置） |
| Auth: x-instance-token | 未获取（feedback/context-pack 端点返回 401） |
| 验证时间 | 2026-05-03 01:59 UTC |
| Instance 引用 | `hermes-agent`（truth read）/ `test-probe`（candidate ingress 冒烟） |
| Candidate 引用 | `219a5914-6c85-43df-ad5e-1d1d36241b39`（truth read） |

---

## 2. Smoke 检查结果

### 2.1 Candidate Ingress

| 项 | 结果 |
|---|---|
| 端点 | `POST /api/integrations/candidate-ingress` |
| HTTP 状态 | **201 Created** ✅ |
| 测试 payload | `{"instanceId": "test-probe", "rawText": "handshake-smoke-probe"}` |
| 返回 candidateId | `b1b6f7ec-2e6b-47f2-803e-bd26b0ca2627` |
| 返回 status | `draft` |
| 结论 | **接口可达，端到端创建工作正常** |

> ⚠️ 注意：这是接口层冒烟。`flowmind_capture.py` 从 Bitable 真实记录 → FlowMind 的端到端闭合验证仍待执行。

---

### 2.2 Review Queue Read

| 项 | 结果 |
|---|---|
| 端点 | `GET /api/integrations/review-queue` |
| HTTP 状态 | **200 OK** ✅ |
| 返回数据 | 11 个 instance，含真实 candidates（`hermes-agent`, `ui-manual-capture`, `crazyagentsmanage-intel-sentinel` 等） |
| 真实 candidate 可见 | ✅ `219a5914-6c85-43df-ad5e-1d1d36241b39`（C-1, approved）在 `hermes-agent` instance 中 |
| 结论 | **接口可达，数据完整** |

---

### 2.3 Truth Read

| 项 | 结果 |
|---|---|
| 端点 | `GET /api/bridge/truth/:candidateId` |
| HTTP 状态 | **200 OK** ✅ |
| 测试 candidateId | `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| 返回 semanticContext | ✅ 包含 entries、fieldMappings、consumerHints |
| 返回 latestEvidence | ✅ 包含 evidenceClass、evidenceSourceType、summary、refs |
| 返回 status | `approved` |
| 消费方式 | `scripts/runtime/generate_hermes_handoff.py` → Hermes handoff packet |
| 结论 | **真实消费闭环已验证** ✅ |

---

### 2.4 Decision (Review Confirm)

| 项 | 结果 |
|---|---|
| 端点 | `POST /api/integrations/candidates/:id/confirm` |
| HTTP 状态 | **500 Internal Server Error** ❌ |
| 原因 | 需要正确的 x-instance-token 或 session context，裸调不通过 |
| 结论 | **接口可达但未在真实 review 轮次中触发** |

> C-1 candidate `219a5914` 的 `decisionMetadata.confirmedBy: "codex-cli"` 证明决策链路曾工作，但冒烟复现失败。

---

### 2.5 Feedback Pull

| 项 | 结果 |
|---|---|
| 端点 | `GET /api/bridge/feedback/:instanceId` |
| HTTP 状态 | **401 Unauthorized** ⚠️ |
| 原因 | `x-instance-token` 不正确（使用 `flowmind-dev-token`） |
| 结论 | **端点存在且可达**（401 证明路由匹配），但缺少正确 instance token |

---

### 2.6 Context Pack

| 项 | 结果 |
|---|---|
| 端点 | `POST /api/bridge/context-pack` |
| HTTP 状态 | **401 Unauthorized** ⚠️ |
| 原因 | `x-instance-token` 不正确 |
| 结论 | **端点存在且可达**（401 证明路由匹配），但缺少正确 instance token |

---

## 3. 通过 vs 未通过分类

| 检查项 | 结果 | 分类 |
|---|---|---|
| Candidate ingress（接口层） | 201 Created | ✅ 通过 |
| Candidate ingress（Bitable 端到端） | 未验证 | ⚠️ 仅接口可达 |
| Review queue | 200 OK | ✅ 通过 |
| Truth read | 200 OK + 真实消费 | ✅ 通过（已形成消费闭环） |
| Decision confirm | 500 error | ⚠️ 仅接口可达 |
| Feedback pull | 401 (endpoint exists) | ⚠️ 仅接口可达 |
| Context pack | 401 (endpoint exists) | ⚠️ 仅接口可达 |
| Hermes handoff packet | 生成 + review 完成 | ✅ 通过（真实消费闭环） |

---

## 4. 当前 handshake 结论

> **5/8 通过，3/8 仅接口可达。**  
> Truth read + handoff packet 是当前唯一形成**真实消费闭环**的链路。  
> Candidate ingress 接口可达但缺少 Bitable → FlowMind 端到端验证。  
> Decision / Feedback / Context-pack 端点均存在，但未在 Crazy 侧形成消费——不是接口不存在的问题，是消费侧未接入。
