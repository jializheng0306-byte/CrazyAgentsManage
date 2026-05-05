# Crazy handoff live 复验收口 — 2026-05-05

> **复验时间**：2026-05-05 12:30 CST  
> **类型**：运营侧 handoffContract 消费面复验  
> **仓库**：`CrazyAgentsManage`  
> **上游**：FlowMind `operator/replay` + `bridge/trace`  
> **上位文档**：`execution-boundary-consumption-status-2026-05-04.md`（本文件为事实更新，覆盖其过期结论）

---

## 1. 复验样本

| Bitable recordId | 状态 | Truth Status | handoffContract.ready |
|---|---|---|---|
| `recviqtP2dj0U3` | blocked | rejected | `false` |
| `recviza1xpm9BI` | 进行中 | approved | `true` |
| `recviBYza3ipt4` | blocked | rejected | `false` |

全部通过 `/api/runtime/handoffs?recordId=<bitable_record_id>` 消费，来源均为 `moduleDetails.handoff`。

---

## 2. 关键结论

### 2.1 接入层

| 检查项 | 结论 |
|---|---|
| `/api/runtime/handoffs?recordId=...` 已可直接使用 | ✅ 是 |
| 无需人工做 ID 映射 | ✅ 是（预生成缓存 `bitable_candidate_cache.json` + lark-cli 回退） |
| 无需人工推导 ready | ✅ 是（`handoffContract.ready` 直接可读） |
| 无需人工解释阻塞 | ✅ 是（`handoffContract.blockingIssues` 结构化列表） |

### 2.2 handoffContract 归一化字段

| 字段 | 是否可消费 | 说明 |
|---|---|---|
| `handoffContract.ready` | ✅ | Truth Status 为 `approved`/`committed` 时为 `true` |
| `handoffContract.blockingIssues` | ✅ | 含 Truth Status、gaps、missingFields 等结构化阻塞 |
| `handoffContract.missingFields` | ✅ | 当前 4 项 Evidence 字段标记缺失（合成 replay 路径限制） |
| `handoffContract.executionBoundaryMissingFields` | ✅ | 当前为空（semanticContext 已提供完整 EB） |

### 2.3 Execution Boundary

| 四块 | 状态 | 来源 |
|---|---|---|
| Canonical Authority | ✅ | `semanticContext.executionBoundary`（bridge trace 回退） |
| Local Writable Targets | ✅ | 同上 |
| Human Gate Actions | ✅ | 同上 |
| Forbidden Mutations | ✅ | 同上 |

> **注**：`bitable_mapped` 路径（Path 2）通过 `semanticContext.executionBoundary` 回退提供完整四块。  
> `operator_replay` 路径（Path 1，FlowMind UUID 直查）通过 `moduleDetails.handoff.Execution Boundary` section 提供。  
> 两条路径均已闭环，不再存在 executionBoundary 为 `null` 的情况（覆盖 `execution-boundary-consumption-status-2026-05-04.md` 的过期结论）。

---

## 3. 结论

### 结论 1：handoffContract 主链路 — ✅ 可切默认

运营已可直接用 Bitable `recordId` 走统一 `handoffContract`：
- 不再需人工做 FlowMind UUID 映射
- 不再需人工从状态推导 ready
- 不再需人工读 gaps 解释阻塞
- `blockingIssues` / `missingFields` / `executionBoundaryMissingFields` 均为结构化输出

### 结论 2：Execution Boundary — ✅ 已闭环

两个消费路径均完整提供四块信息。不再存在 EB 缺失且消费者无法判断的情况。相关过期文档 `execution-boundary-consumption-status-2026-05-04.md` 中的 `executionBoundary = null` 结论已被本文件覆盖。

---

## 4. 仍存缺口（已降级为增强项，不作为默认切换阻塞）

| 缺口 | 影响 | 优先级 |
|---|---|---|
| evidence 类字段在合成 replay 路径缺失 | `Latest Evidence Summary/Class/Source Type/Refs` 四项为空 —— 需 operator record linkage 补齐 | P2 增强 |
| `refresh-bitable-cache.sh` 尚未接入 cron | 新 Bitable 记录需手动刷新缓存后才能通过 recordId 查询 | P2 增强 |

> 以上两项不影响 handoffContract 主链路和 Execution Boundary 的默认消费。

---

## 5. 部署状态

| 组件 | 状态 |
|---|---|
| CrazyAgentsManage WebUI/API | ✅ `cam.service` on `:5002`，nginx proxy `/manage/` |
| recordId 映射缓存 | ✅ `/opt/crazyagentsmanage/src/webui/bitable_candidate_cache.json`（9 条） |
| 缓存刷新脚本 | ✅ `/root/.hermes/scripts/refresh-bitable-cache.sh`（待接入 cron） |
