# Crazy `runtime/handoffs` Context Summary 冻结说明

> 日期：2026-05-08  
> 类型：counterpart 冻结说明 / phase28-34 sync  
> 作用：把 FlowMind `Harness Knowloge` 研究线对 `context-pack` 的下一优先主线裁定同步到 Crazy 侧共享工件

---

## 1. 当前已冻结的事实

1. `feedback`
   - 当前应视为 **脚本级部分消费**
2. `context-pack`
   - 当前仍是 **probe-only**
   - Crazy 还没有 durable 主线消费入口

这两点继续以：

- `feedback-context-consumption-status-2026-05-03.md`
- `hermes-flowmind-compatibility-matrix-2026-04-30.md`

作为状态工件记录。

---

## 2. 下一优先主线

当前冻结的下一优先主线不是：

- 直接让脚本直连 `POST /bridge/context-pack`
- 直接新开 instance-level context 页面

而是：

> **先补强 Crazy `GET /api/runtime/handoffs?recordId=...` 的 page-facing `contextSummary`。**

原因：

1. Crazy 页面当前真正消费的是 `runtime/handoffs`
2. 这条链已经有：
   - 路由
   - 页面
   - handoffContract
   - live acceptance 工件
3. `context-pack` 的摘要结果已经在 FlowMind 上游进入 replay / handoff

---

## 3. `runtime/handoffs` 的角色

当前冻结：

1. `/api/runtime/handoffs?recordId=...`
   - 是 **page-facing canonical surface**
2. `/api/flowmind/records/:recordId/replay`
   - 只是 **upstream replay adapter**
3. `generate_hermes_handoff.py`
   - 只是 **downstream distributor**
   - 不是新的 `context-pack` 主读面

---

## 4. 当前 `Context Summary` 的冻结口径

当前冻结的 page-facing `contextSummary` 四项字段是：

1. `Active Commitments`
2. `Recent Decisions`
3. `Active Constraints`
4. `Consumer Hints`

当前冻结的语义分层是：

1. `Consumer Hints`
   - 与上游现有 authority gate 保持一致
2. 其余三项计数字段
   - 先作为显式展示字段
   - 当前不直接升级成阻塞项

---

## 5. instance-level context surface

当前冻结结论：

> **不立项。**

只有在以下条件同时满足时，才允许重开：

1. `runtime/handoffs` 的 `contextSummary` 已补强完成
2. operator 仍然无法完成 instance 级判断
3. IA / route / 页面 PRD 三锚点齐备

---

## 6. 本文件的作用边界

本文件是 Crazy counterpart 冻结说明。

它：

1. 负责把下一优先主线写死
2. 防止 Crazy 侧继续回到“直打 context-pack / 直接开新面”的旧分叉

它不负责：

1. 修改 FlowMind canonical contract
2. 定义新的 API
3. 宣称 `context-pack` 当前已经被 durable 消费

---

## 7. 一句话结论

> 当前 Crazy 侧对 `context-pack` 的正确推进顺序已经冻结：保持 `probe_only` 状态判断不变，但下一优先补强 lane 固定为 `runtime/handoffs` 的 page-facing `contextSummary`；Hermes handoff 只能继承这条主线，instance-level context surface 当前不立项。
