# Phase 5 最小闭环回写 — 实施记录

> 日期: 2026-05-03  
> 类型: Hermes promise ← FlowMind truth/trace/feedback 回写  
> 分支: `feat/auto-capture-trace`

---

## 1. 验证对象

| 项目 | C-1 (approved) | AEGIS (draft) |
|---|---|---|
| promise_id | `promise-phase5-c1-approved` | `promise-auto-20260502-79e81600` + `promise-phase5-new-draft` |
| flowmind_candidate_id | `219a5914-6c85-43df-ad5e-1d1d36241b39` | `ce79892d-3578-4538-82ee-9941abf57cff` |
| instance | `hermes-agent` | `hermes-agent` |
| ingress 方式 | 已有（运营侧已确认） | POST `/api/integrations/candidate-ingress` |

---

## 2. 固定读取顺序执行

| 步骤 | C-1 (approved) | AEGIS (draft) |
|---|---|---|
| 1. truth read | ✅ status=approved, evidence=EXTRACTED/OPERATOR_ACCEPTANCE | ✅ status=draft |
| 2. trace read | ✅ 7 events (create→clarify→confirm→approve→update→update) | ✅ 1 event (create) |
| 3. feedback read | ❌ endpoint returns 401 (x-instance-token unavailable) | ❌ same |
| 4. handoff/replay | 跳过（非必要） | 跳过 |

---

## 3. Promise 回写字段

### C-1 (approved)

| 字段 | 值 |
|---|---|
| flowmind_candidate_id | ✅ `219a5914-6c85-43df-ad5e-1d1d36241b39` |
| last_governance_status | ✅ `approved` |
| last_governance_feedback | ⚠️ 空（feedback endpoint unavailable） |
| interactions[] | ✅ 2 条（truth query + trace query） |
| status | ✅ `in_progress`（approved → in_progress） |

### AEGIS (draft)

| 字段 | 值 |
|---|---|
| flowmind_candidate_id | ✅ `ce79892d-3578-4538-82ee-9941abf57cff` |
| last_governance_status | ✅ `draft` |
| last_governance_feedback | ⚠️ 空 |
| interactions[] | ✅ 3 条（ingress create + truth query + trace query） |
| status | ✅ `pending`（draft → pending） |

---

## 4. 状态映射验证

| truth.status | promise.status | 规则 |
|---|---|---|
| `approved` | `in_progress` ✅ | "approved 不能再被当成还不能消费的中间态" |
| `draft` | `pending` | draft → 保持 pending |
| `committed` | 未测试（无真实 committed candidate） | 规则已编码 |
| `rejected` | 未测试 | 规则已编码 |

---

## 5. 剩余缺口

| 缺口 | 分类 |
|---|---|
| feedback endpoint 不可用（x-instance-token 缺失） | 运行缺口 |
| 无真实 `committed` candidate 验证 committed → done 映射 | 数据缺口 |
| feedback 状态映射（blocked/clarified/cancelled）未实测 | 实现缺口 |
| interactions[] 缺少 feedback 方向的事件（因 endpoint 不可用） | 运行缺口 |

---

## 6. 结论

> ✅ **已进入最小闭环。**  
> Hermes promise 现在可以通过 `flowmind_candidate_id` → truth/trace/feedback 固定读取顺序  
> 从 FlowMind 反向获取治理状态。`approved` 已正确驱动 promise 进入 `in_progress` 状态。  
> feedback 链路因 x-instance-token 缺失暂时不可用，不影响 truth/trace 主链路。
